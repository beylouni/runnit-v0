#!/usr/bin/env python3
"""
Importação de Dados Históricos do Garmin Connect
=================================================

Este script usa a biblioteca garminconnect para:
1. Autenticar com Garmin Connect (username/password)
2. Baixar TODAS as atividades históricas
3. Salvar no PostgreSQL

Uso:
    python garmin_historical_import.py
    
Ou via API:
    POST /historical/import-from-garmin
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tentar importar garminconnect
try:
    from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError
    GARMINCONNECT_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ garminconnect não está instalado. Instale com: pip install garminconnect")
    GARMINCONNECT_AVAILABLE = False
    Garmin = None

# Importar database service
try:
    from app.services.database_service import DatabaseService
    from app.config import settings
except ImportError:
    # Se executado standalone, ajustar path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from app.services.database_service import DatabaseService
    from app.config import settings


class GarminHistoricalImporter:
    """Importador de dados históricos do Garmin Connect"""
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Inicializar importador
        
        Args:
            email: Email do Garmin Connect (opcional, usa env var se não fornecido)
            password: Senha do Garmin Connect (opcional, usa env var se não fornecido)
        """
        if not GARMINCONNECT_AVAILABLE:
            raise ImportError("garminconnect não está instalado")
        
        self.email = email or os.getenv("GARMIN_EMAIL")
        self.password = password or os.getenv("GARMIN_PASSWORD")
        
        if not self.email or not self.password:
            raise ValueError("Email e senha do Garmin Connect são obrigatórios")
        
        self.client: Optional[Garmin] = None
        self.db_service = DatabaseService()
        
        logger.info("✅ GarminHistoricalImporter inicializado")
    
    def authenticate(self) -> bool:
        """
        Autenticar com Garmin Connect
        
        Returns:
            True se autenticação bem-sucedida
        """
        try:
            logger.info("🔐 Autenticando com Garmin Connect...")
            self.client = Garmin(self.email, self.password)
            self.client.login()
            logger.info("✅ Autenticação bem-sucedida!")
            return True
            
        except GarminConnectAuthenticationError as e:
            logger.error(f"❌ Erro de autenticação: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao autenticar: {e}")
            return False
    
    def get_activities(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Buscar atividades do Garmin Connect
        
        Args:
            start_date: Data de início (padrão: 2 anos atrás)
            end_date: Data de fim (padrão: hoje)
            limit: Número máximo de atividades por requisição (padrão: 100)
        
        Returns:
            Lista de atividades
        """
        if not self.client:
            logger.error("❌ Cliente não autenticado. Execute authenticate() primeiro.")
            return []
        
        # Datas padrão
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=730)  # 2 anos
        
        logger.info(f"📥 Buscando atividades de {start_date.date()} até {end_date.date()}")
        
        try:
            all_activities = []
            start = 0
            
            while True:
                logger.info(f"   Buscando atividades {start} - {start + limit}...")
                
                # Buscar atividades
                activities = self.client.get_activities(start, limit)
                
                if not activities:
                    logger.info("   Nenhuma atividade encontrada.")
                    break
                
                # Filtrar por data
                filtered_activities = []
                for activity in activities:
                    activity_date_str = activity.get('startTimeLocal') or activity.get('startTimeGMT')
                    if not activity_date_str:
                        continue
                    
                    try:
                        # Parse date (formato: 2024-10-15 12:30:45 ou ISO)
                        activity_date = datetime.fromisoformat(activity_date_str.replace('Z', '+00:00'))
                        
                        if start_date <= activity_date <= end_date:
                            filtered_activities.append(activity)
                        elif activity_date < start_date:
                            # Já passou do período, parar
                            logger.info(f"   Chegou ao fim do período (atividade de {activity_date.date()})")
                            return all_activities + filtered_activities
                    except:
                        # Se erro no parse, incluir mesmo assim
                        filtered_activities.append(activity)
                
                all_activities.extend(filtered_activities)
                logger.info(f"   ✅ {len(filtered_activities)} atividades no período. Total: {len(all_activities)}")
                
                # Se retornou menos que o limite, não há mais atividades
                if len(activities) < limit:
                    break
                
                start += limit
            
            logger.info(f"✅ Total de {len(all_activities)} atividades encontradas!")
            return all_activities
            
        except GarminConnectConnectionError as e:
            logger.error(f"❌ Erro de conexão: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar atividades: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def import_activity(self, activity: Dict[str, Any]) -> Optional[str]:
        """
        Importar uma atividade para o banco de dados
        
        Args:
            activity: Dados da atividade do Garmin Connect
        
        Returns:
            UUID da atividade salva ou None se erro
        """
        try:
            # Mapear campos do Garmin Connect para nosso formato
            activity_data = {
                'garmin_activity_id': str(activity.get('activityId')),
                'garmin_user_id': str(activity.get('ownerId')) if activity.get('ownerId') else None,
                'activity_name': activity.get('activityName'),
                'sport': activity.get('activityType', {}).get('typeKey') if isinstance(activity.get('activityType'), dict) else activity.get('activityType'),
                'sub_sport': activity.get('activityType', {}).get('subtypeKey') if isinstance(activity.get('activityType'), dict) else None,
                'start_time': activity.get('startTimeLocal') or activity.get('startTimeGMT'),
                'duration_seconds': activity.get('duration'),
                'distance_meters': activity.get('distance'),
                'avg_heart_rate': activity.get('averageHR'),
                'max_heart_rate': activity.get('maxHR'),
                'total_calories': activity.get('calories'),
                'device_name': activity.get('deviceId'),
            }
            
            # Salvar no banco
            activity_uuid = self.db_service.save_activity(activity_data)
            
            if activity_uuid:
                logger.info(f"   ✅ Atividade {activity.get('activityId')} salva: {activity.get('activityName')}")
                return activity_uuid
            else:
                logger.warning(f"   ⚠️ Não foi possível salvar atividade {activity.get('activityId')}")
                return None
                
        except Exception as e:
            logger.error(f"   ❌ Erro ao importar atividade {activity.get('activityId')}: {e}")
            return None
    
    def import_all_activities(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Importar todas as atividades históricas
        
        Args:
            start_date: Data de início (padrão: 2 anos atrás)
            end_date: Data de fim (padrão: hoje)
        
        Returns:
            Estatísticas da importação
        """
        logger.info("🚀 INICIANDO IMPORTAÇÃO HISTÓRICA")
        logger.info("=" * 50)
        
        # Autenticar
        if not self.authenticate():
            return {
                'success': False,
                'error': 'Falha na autenticação',
                'imported': 0,
                'failed': 0
            }
        
        # Buscar atividades
        activities = self.get_activities(start_date, end_date)
        
        if not activities:
            logger.warning("⚠️ Nenhuma atividade encontrada")
            return {
                'success': True,
                'message': 'Nenhuma atividade encontrada no período',
                'imported': 0,
                'failed': 0
            }
        
        # Importar atividades
        logger.info(f"\n💾 Importando {len(activities)} atividades para o banco...")
        imported = 0
        failed = 0
        
        for i, activity in enumerate(activities, 1):
            logger.info(f"\n[{i}/{len(activities)}] Processando atividade {activity.get('activityId')}...")
            
            if self.import_activity(activity):
                imported += 1
            else:
                failed += 1
        
        # Resultado
        logger.info("\n" + "=" * 50)
        logger.info("🎉 IMPORTAÇÃO CONCLUÍDA!")
        logger.info(f"   ✅ Importadas: {imported}")
        logger.info(f"   ❌ Falharam: {failed}")
        logger.info(f"   📊 Total: {len(activities)}")
        logger.info("=" * 50)
        
        return {
            'success': True,
            'total_activities': len(activities),
            'imported': imported,
            'failed': failed,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }


def main():
    """Executar importação via linha de comando"""
    print("🏃 IMPORTADOR DE DADOS HISTÓRICOS DO GARMIN")
    print("=" * 50)
    print()
    
    # Verificar credenciais
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        print("❌ Erro: Defina as variáveis de ambiente:")
        print("   export GARMIN_EMAIL='seu_email@garmin.com'")
        print("   export GARMIN_PASSWORD='sua_senha'")
        print()
        print("Ou adicione ao arquivo .env")
        sys.exit(1)
    
    # Criar importador
    try:
        importer = GarminHistoricalImporter(email, password)
        
        # Importar últimos 2 anos
        result = importer.import_all_activities()
        
        if result['success']:
            print("\n✅ Importação concluída com sucesso!")
            sys.exit(0)
        else:
            print(f"\n❌ Importação falhou: {result.get('error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

