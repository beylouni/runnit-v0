#!/usr/bin/env python3
"""
Serviço de persistência no banco de dados PostgreSQL
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from contextlib import contextmanager

# Tentar importar psycopg2, mas não falhar se não estiver disponível
try:
    import psycopg2
    from psycopg2.extras import execute_values, Json
    from psycopg2.pool import SimpleConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    SimpleConnectionPool = None  # type: ignore

from app.config import settings

logger = logging.getLogger(__name__)

# Connection pool para melhor performance
_pool: Optional[SimpleConnectionPool] = None


def get_connection_pool():
    """Cria ou retorna o pool de conexões"""
    global _pool
    
    if not PSYCOPG2_AVAILABLE:
        logger.warning("⚠️ psycopg2 não está instalado. Persistência desabilitada. "
                      "Instale com: pip install psycopg2-binary")
        return None
    
    if _pool is None:
        if not settings.DATABASE_URL:
            logger.warning("⚠️ DATABASE_URL não configurada. Persistência desabilitada.")
            return None
        
        try:
            # Render requer SSL, então vamos garantir que está configurado
            # Se DATABASE_URL já incluir ?sslmode=require, usar diretamente
            # Caso contrário, adicionar parâmetros SSL
            db_url = settings.DATABASE_URL
            if '?' not in db_url:
                # Adicionar parâmetros SSL para Render
                db_url = f"{db_url}?sslmode=require"
            elif 'sslmode' not in db_url:
                db_url = f"{db_url}&sslmode=require"
            
            _pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=db_url
            )
            
            # Testar conexão imediatamente para detectar erros
            test_conn = _pool.getconn()
            test_conn.close()
            _pool.putconn(test_conn)
            
            logger.info("✅ Pool de conexões PostgreSQL criado e testado")
        except Exception as e:
            logger.error(f"❌ Erro ao criar pool de conexões: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    return _pool


@contextmanager
def get_db_connection():
    """Context manager para obter conexão do pool"""
    pool = get_connection_pool()
    if not pool:
        yield None
        return
    
    conn = None
    try:
        conn = pool.getconn()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Erro na conexão do banco: {e}")
        raise
    finally:
        if conn:
            pool.putconn(conn)


class DatabaseService:
    """Serviço para persistir dados no PostgreSQL"""
    
    def __init__(self):
        self.pool = get_connection_pool()
    
    def _ensure_user_exists(self, garmin_user_id: str) -> Optional[str]:
        """
        Garante que o usuário existe no banco.
        Retorna o UUID do usuário.
        """
        if not self.pool:
            return None
        
        with get_db_connection() as conn:
            if not conn:
                return None
            
            try:
                cur = conn.cursor()
                # Verificar se usuário existe
                cur.execute("""
                    SELECT id FROM users 
                    WHERE garmin_user_id = %s
                """, (garmin_user_id,))
                
                result = cur.fetchone()
                
                if result:
                    return str(result[0])
                else:
                    # Criar usuário se não existir
                    cur.execute("""
                        INSERT INTO users (garmin_user_id, created_at)
                        VALUES (%s, CURRENT_TIMESTAMP)
                        RETURNING id
                    """, (garmin_user_id,))
                    
                    user_uuid = str(cur.fetchone()[0])
                    logger.info(f"✅ Usuário criado: {garmin_user_id} -> {user_uuid}")
                    return user_uuid
                    
            except Exception as e:
                logger.error(f"❌ Erro ao garantir usuário: {e}")
                return None
    
    def save_activity(self, activity_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[str]:
        """
        Salva uma atividade no banco de dados.
        
        activity_data deve conter:
        - garmin_activity_id (obrigatório)
        - user_id ou garmin_user_id
        - Dados básicos da atividade
        """
        if not self.pool:
            logger.warning("⚠️ Pool de conexão não disponível")
            return None
        
        # Obter user_id se necessário
        if not user_id:
            garmin_user_id = activity_data.get('garmin_user_id') or activity_data.get('userId')
            if garmin_user_id:
                user_id = self._ensure_user_exists(garmin_user_id)
            else:
                # Se não houver userId, usar um usuário padrão
                # Isso permite receber webhooks de teste ou webhooks que não incluem userId
                default_garmin_user_id = "default-user"
                logger.warning(f"⚠️ userId não fornecido. Usando usuário padrão: {default_garmin_user_id}")
                user_id = self._ensure_user_exists(default_garmin_user_id)
        
        if not user_id:
            logger.warning("⚠️ Não foi possível determinar user_id")
            return None
        
        with get_db_connection() as conn:
            if not conn:
                return None
            
            try:
                cur = conn.cursor()
                
                # Verificar se atividade já existe
                garmin_activity_id = str(activity_data.get('garmin_activity_id') or activity_data.get('activityId', ''))
                
                cur.execute("""
                    SELECT id FROM activities 
                    WHERE garmin_activity_id = %s
                """, (garmin_activity_id,))
                
                existing = cur.fetchone()
                
                if existing:
                    activity_uuid = str(existing[0])
                    logger.info(f"📝 Atividade já existe: {garmin_activity_id} -> {activity_uuid}")
                    # TODO: Atualizar dados se necessário
                    return activity_uuid
                
                # Converter timestamps
                start_time = None
                if 'start_time' in activity_data:
                    start_time = activity_data['start_time']
                elif 'startTimeInSeconds' in activity_data:
                    start_time = datetime.fromtimestamp(activity_data['startTimeInSeconds'])
                elif 'startTimeGMT' in activity_data:
                    try:
                        start_time = datetime.fromisoformat(activity_data['startTimeGMT'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Extrair e converter valores numéricos
                # Garmin envia: durationInSeconds, distanceInMeters, activeKilocalories, averageHeartRateInBeatsPerMinute
                duration_seconds = activity_data.get('duration_seconds') or activity_data.get('durationInSeconds')
                distance_meters = activity_data.get('distance_meters') or activity_data.get('distanceInMeters')
                avg_hr = activity_data.get('avg_heart_rate') or activity_data.get('averageHeartRateInBeatsPerMinute')
                max_hr = activity_data.get('max_heart_rate') or activity_data.get('maxHeartRateInBeatsPerMinute')
                calories = (activity_data.get('total_calories') or 
                           activity_data.get('activeKilocalories') or 
                           activity_data.get('calories'))
                
                # Garantir que são números ou None (0 é válido!)
                try:
                    duration_seconds = float(duration_seconds) if duration_seconds not in (None, '') else None
                    distance_meters = float(distance_meters) if distance_meters not in (None, '') else None
                    avg_hr = int(float(avg_hr)) if avg_hr not in (None, '') else None
                    max_hr = int(float(max_hr)) if max_hr not in (None, '') else None
                    calories = int(float(calories)) if calories not in (None, '') else None
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Erro ao converter valores numéricos: {e}")
                    # Manter None para valores que falharem
                
                # Inserir atividade
                cur.execute("""
                    INSERT INTO activities (
                        user_id,
                        garmin_activity_id,
                        garmin_summary_id,
                        activity_name,
                        sport,
                        sub_sport,
                        start_time,
                        duration_seconds,
                        distance_meters,
                        avg_heart_rate,
                        max_heart_rate,
                        total_calories,
                        device_name,
                        has_gps,
                        has_heart_rate,
                        created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                    )
                    RETURNING id
                """, (
                    user_id,
                    garmin_activity_id,
                    activity_data.get('garmin_summary_id') or activity_data.get('summaryId'),
                    activity_data.get('activity_name') or activity_data.get('activityName'),
                    activity_data.get('sport') or activity_data.get('activityType') or 'running',
                    activity_data.get('sub_sport') or activity_data.get('subActivityType'),
                    start_time,
                    duration_seconds,
                    distance_meters,
                    avg_hr,
                    max_hr,
                    calories,
                    activity_data.get('device_name') or activity_data.get('deviceName'),
                    activity_data.get('has_gps', True),
                    activity_data.get('has_heart_rate', avg_hr is not None)
                ))
                
                activity_uuid = str(cur.fetchone()[0])
                logger.info(f"✅ Atividade salva: {garmin_activity_id} -> {activity_uuid}")
                
                return activity_uuid
                
            except Exception as e:
                logger.error(f"❌ Erro ao salvar atividade: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None
    
    def save_health_dailies(self, dailies_data: List[Dict[str, Any]], user_id: Optional[str] = None) -> int:
        """
        Salva dados de dailies (resumo diário de saúde) no banco.
        
        Por enquanto, apenas loga os dados recebidos.
        TODO: Criar tabela específica para health_dailies no schema.sql
        """
        if not self.pool:
            logger.warning("⚠️ Pool de conexão não disponível")
            return 0
        
        if not dailies_data:
            return 0
        
        # Por enquanto, apenas logar os dados recebidos
        # Quando criarmos a tabela health_dailies no schema, implementaremos a persistência
        logger.info(f"📝 {len(dailies_data)} registros de dailies recebidos (persistência a ser implementada)")
        
        # Log do primeiro registro como exemplo
        if dailies_data:
            first_daily = dailies_data[0]
            logger.info(f"📊 Exemplo de daily: {json.dumps(first_daily, default=str)[:200]}...")
        
        # TODO: Implementar quando tivermos tabela health_dailies
        # Obter user_id se necessário
        # for daily in dailies_data:
        #     if not user_id:
        #         garmin_user_id = daily.get('userId')
        #         if garmin_user_id:
        #             user_id = self._ensure_user_exists(garmin_user_id)
        #     ...
        
        return len(dailies_data)  # Retornar count para manter compatibilidade
    
    def test_connection(self) -> bool:
        """Testa a conexão com o banco"""
        if not self.pool:
            return False
        
        try:
            with get_db_connection() as conn:
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1")
                    cur.fetchone()
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao testar conexão: {e}")
            return False

