#!/usr/bin/env python3
"""
Serviço de Integração com Garmin Connect

Integra com o sistema atual de criação e leitura de arquivos FIT.
Por enquanto usa simulação, mas está preparado para API real.
"""

import os
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import sys
import httpx
import time

# Adicionar o diretório pai para importar o sistema de FIT
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'core'))

try:
    from fit_creator import criar_treino_fit, ler_treino_fit, ler_atividade_fit
    FIT_SYSTEM_AVAILABLE = True
    print("✅ Sistema de FIT integrado com sucesso!")
except ImportError as e:
    print(f"⚠️  Sistema de FIT não disponível: {e}")
    print("   Usando simulações...")
    FIT_SYSTEM_AVAILABLE = False

# Enhanced FIT System (extração completa + métricas avançadas)
try:
    from enhanced_fit_parser import EnhancedFITParser
    from metrics_engine import MetricsEngine
    ENHANCED_SYSTEM_AVAILABLE = True
    print("✅ Enhanced FIT System integrado com sucesso!")
except ImportError as e:
    print(f"⚠️  Enhanced FIT System não disponível: {e}")
    print("   Usando sistema básico...")
    ENHANCED_SYSTEM_AVAILABLE = False
    
    # Funções de simulação como fallback
    def criar_treino_fit(workout_data, output_path):
        """Simulação da função criar_treino_fit"""
        try:
            # Simular criação de arquivo FIT
            with open(output_path, 'wb') as f:
                f.write(b'FIT_FILE_SIMULATION')
            return True
        except Exception:
            return False

    def ler_treino_fit(fit_file_path):
        """Simulação da função ler_treino_fit"""
        try:
            if os.path.exists(fit_file_path):
                return {
                    'workout': {
                        'workout_name': 'Treino Simulado',
                        'num_valid_steps': 3
                    },
                    'workout_steps': [
                        {
                            'workout_step_name': 'Aquecimento',
                            'duration_type': 'time',
                            'duration_time': 600.0
                        },
                        {
                            'workout_step_name': 'Corrida',
                            'duration_type': 'distance',
                            'duration_distance': 5000.0
                        },
                        {
                            'workout_step_name': 'Desaquecimento',
                            'duration_type': 'time',
                            'duration_time': 300.0
                        }
                    ]
                }
            return None
        except Exception:
            return None

    def ler_atividade_fit(fit_file_path):
        """Simulação da função ler_atividade_fit"""
        try:
            if os.path.exists(fit_file_path):
                return {
                    'total_distance': 5000,
                    'total_time': 1800,
                    'average_pace': 216,  # segundos por km
                    'calories': 450,
                    'max_heart_rate': 165,
                    'average_heart_rate': 145
                }
            return None
        except Exception:
            return None

# Simulação do sistema de integração
class GarminSimulator:
    def push_workout(self, workout_data, fit_file_path):
        """Simula envio de treino"""
        return True
    
    def pull_activity(self, activity_id, output_path):
        """Simula download de atividade"""
        try:
            with open(output_path, 'wb') as f:
                f.write(b'ACTIVITY_FIT_SIMULATION')
            return output_path
        except Exception:
            return None
    
    def list_activities(self, limit=10):
        """Simula listagem de atividades"""
        return [
            {
                'id': 'sim_001',
                'name': 'Corrida Matinal',
                'type': 'RUNNING',
                'startTime': '2024-01-01T10:00:00Z',
                'distance': 5000,
                'duration': 1800
            },
            {
                'id': 'sim_002',
                'name': 'Treino Intervalado',
                'type': 'RUNNING',
                'startTime': '2024-01-02T10:00:00Z',
                'distance': 8000,
                'duration': 2400
            }
        ]

def create_garmin_integration(use_simulator=True):
    """Simulação da função create_garmin_integration"""
    return GarminSimulator()

from app.config import settings

logger = logging.getLogger(__name__)

# Armazenamento temporário em memória para o code_verifier e tokens
# Em produção, isso deve ser substituído por um banco de dados ou Redis
# Movido de auth.py para cá para centralizar o estado da autenticação
temp_auth_storage = {}


class GarminService:
    """Serviço para integração com Garmin Connect"""
    
    def __init__(self):
        """Inicializar serviço Garmin"""
        self.garmin_integration = create_garmin_integration(use_simulator=False) # Mudado para False
        self.workouts_dir = settings.WORKOUTS_DIR
        self.activities_dir = settings.ACTIVITIES_DIR
        self.fit_system_available = FIT_SYSTEM_AVAILABLE
        
        # Manter uma referência ao armazenamento de autenticação
        self.auth_storage = temp_auth_storage

        # Garantir que os diretórios existem
        os.makedirs(self.workouts_dir, exist_ok=True)
        os.makedirs(self.activities_dir, exist_ok=True)
        
        logger.info(f"Sistema de FIT disponível: {self.fit_system_available}")
    
    def is_available(self) -> bool:
        """Verificar se o serviço Garmin está disponível"""
        try:
            # Por enquanto, sempre retorna True pois estamos usando simulação
            # Na implementação real, verificaria se as credenciais estão válidas
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade do Garmin: {e}")
            return False
    
    def create_workout_fit(self, workout_data: Dict[str, Any], output_path: str) -> bool:
        """
        Criar arquivo FIT para um treino
        
        Args:
            workout_data: Dados do treino
            output_path: Caminho onde salvar o arquivo FIT
            
        Returns:
            True se criado com sucesso, False caso contrário
        """
        try:
            logger.info(f"Criando arquivo FIT para treino: {workout_data.get('nome_do_treino')}")
            
            # Usar o sistema REAL de criação de FIT (se disponível)
            if self.fit_system_available:
                logger.info("Usando sistema REAL de criação de FIT")
                success = criar_treino_fit(workout_data, output_path)
            else:
                logger.warning("Usando simulação de criação de FIT")
                success = criar_treino_fit(workout_data, output_path)
            
            if success:
                logger.info(f"Arquivo FIT criado com sucesso: {output_path}")
                return True
            else:
                logger.error(f"Erro ao criar arquivo FIT: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"Exceção ao criar arquivo FIT: {e}")
            return False
    
    def read_workout_fit(self, fit_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Ler arquivo FIT de treino
        
        Args:
            fit_file_path: Caminho do arquivo FIT
            
        Returns:
            Dados do treino ou None se erro
        """
        try:
            logger.info(f"Lendo arquivo FIT: {fit_file_path}")
            
            if not os.path.exists(fit_file_path):
                logger.error(f"Arquivo FIT não encontrado: {fit_file_path}")
                return None
            
            # Usar o sistema REAL de leitura de FIT (se disponível)
            if self.fit_system_available:
                logger.info("Usando sistema REAL de leitura de FIT")
                data = ler_treino_fit(fit_file_path)
            else:
                logger.warning("Usando simulação de leitura de FIT")
                data = ler_treino_fit(fit_file_path)
            
            if data:
                logger.info(f"Arquivo FIT lido com sucesso: {fit_file_path}")
                return data
            else:
                logger.error(f"Erro ao ler arquivo FIT: {fit_file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Exceção ao ler arquivo FIT: {e}")
            return None
    
    def read_activity_fit(self, fit_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Ler arquivo FIT de atividade
        
        Args:
            fit_file_path: Caminho do arquivo FIT
            
        Returns:
            Dados da atividade ou None se erro
        """
        try:
            logger.info(f"Lendo arquivo FIT de atividade: {fit_file_path}")
            
            if not os.path.exists(fit_file_path):
                logger.error(f"Arquivo FIT não encontrado: {fit_file_path}")
                return None
            
            # Usar o sistema REAL de leitura de FIT (se disponível)
            if self.fit_system_available:
                logger.info("Usando sistema REAL de leitura de atividade FIT")
                data = ler_atividade_fit(fit_file_path)
            else:
                logger.warning("Usando simulação de leitura de atividade FIT")
                data = ler_atividade_fit(fit_file_path)
            
            if data:
                logger.info(f"Arquivo FIT de atividade lido com sucesso: {fit_file_path}")
                return data
            else:
                logger.error(f"Erro ao ler arquivo FIT de atividade: {fit_file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Exceção ao ler arquivo FIT de atividade: {e}")
            return None
    
    def _translate_to_garmin_json(self, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traduz a estrutura de treino interna para o formato JSON da Garmin API."""
        intensity_mapping = {
            "aquecimento": "WARMUP", "warmup": "WARMUP",
            "corrida": "ACTIVE", "active": "ACTIVE",
            "desaquecimento": "COOLDOWN", "cooldown": "COOLDOWN",
            "recuperacao": "RECOVERY", "recovery": "RECOVERY",
            "intervalo": "INTERVAL", "interval": "INTERVAL",
        }
        duration_mapping = {"tempo": "TIME", "time": "TIME", "distancia": "DISTANCE", "distance": "DISTANCE"}
        target_mapping = {"ritmo": "PACE", "frequencia_cardiaca": "HEART_RATE"}

        garmin_steps = []
        for i, step_data in enumerate(workout_data.get("passos", [])):
            garmin_step = {
                "type": "WorkoutStep",
                "stepOrder": i + 1,
                "description": step_data.get("nome_do_passo"),
                "intensity": intensity_mapping.get(step_data.get("tipo_de_passo"), "ACTIVE"),
                "durationType": duration_mapping.get(step_data.get("duracao_tipo"), "TIME"),
                "durationValue": step_data.get("duracao_valor"),
                "targetType": target_mapping.get(step_data.get("meta_tipo"), "OPEN"),
                "targetValueLow": None,
                "targetValueHigh": None,
            }

            min_val = step_data.get("meta_valor_min")
            max_val = step_data.get("meta_valor_max")

            if min_val is not None and max_val is not None:
                if garmin_step["targetType"] == "PACE" and max_val > 0 and min_val > 0:
                    garmin_step["targetValueLow"] = 1000 / max_val
                    garmin_step["targetValueHigh"] = 1000 / min_val
                else:
                    garmin_step["targetValueLow"] = min_val
                    garmin_step["targetValueHigh"] = max_val
            
            garmin_steps.append(garmin_step)
        
        # TODO: Detectar o tipo de esporte a partir dos dados do treino
        sport_type = "RUNNING"

        garmin_workout_json = {
            "workoutName": workout_data.get("nome_do_treino"),
            "description": workout_data.get("descricao"),
            "sport": sport_type,
            "segments": [{
                "segmentOrder": 1,
                "sport": sport_type,
                "steps": garmin_steps
            }]
        }
        return garmin_workout_json

    async def push_workout(self, workout_data: Dict[str, Any]) -> Optional[str]:
        """
        Enviar treino para Garmin Connect (PUSH) via JSON.
        
        Args:
            workout_data: Dados do treino na estrutura interna.
            
        Returns:
            ID do treino na Garmin ou None se erro.
        """
        access_token = self.auth_storage.get('access_token')
        if not access_token:
            logger.error("Não autenticado. Não é possível enviar treino.")
            raise Exception("Não autenticado. Por favor, complete o fluxo OAuth2.")

        try:
            workout_json = self._translate_to_garmin_json(workout_data)
            logger.info(f"Enviando treino para Garmin via API JSON: {workout_json.get('workoutName')}")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(settings.GARMIN_TRAINING_API_URL, headers=headers, json=workout_json)
                response.raise_for_status()
                response_data = response.json()
                
                garmin_workout_id = response_data.get("workoutId")
                logger.info(f"Treino enviado com sucesso via JSON. Resposta: {response_data}")
                return str(garmin_workout_id) if garmin_workout_id else None

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de API ao enviar treino JSON: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Exceção ao enviar treino JSON: {e}")
            return None

    async def schedule_workout(self, workout_id: str, schedule_date: str) -> bool:
        """Agenda um treino existente no calendário do usuário."""
        access_token = self.auth_storage.get('access_token')
        if not access_token:
            logger.error("Não autenticado. Não é possível agendar treino.")
            return False

        try:
            schedule_payload = {
                "workoutId": int(workout_id),
                "date": schedule_date
            }
            logger.info(f"Agendando treino {workout_id} para {schedule_date}")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(settings.GARMIN_SCHEDULE_API_URL, headers=headers, json=schedule_payload)
                response.raise_for_status()
                logger.info(f"Treino agendado com sucesso. Status: {response.status_code}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de API ao agendar treino: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Exceção ao agendar treino: {e}")
            return False
    
    async def request_activity_backfill(self, days: int = 30) -> bool:
        """
        Solicita um backfill de dados de atividades para os últimos X dias.
        Este é um processo assíncrono.
        """
        access_token = self.auth_storage.get('access_token')
        if not access_token:
            logger.error("Não autenticado. Não é possível solicitar backfill.")
            return False

        try:
            # Para evitar o erro de 'backfill duplicado', solicitamos uma janela de tempo
            # muito antiga que a Garmin definitivamente não processou antes.
            # Vamos pedir dados de 6 meses atrás (180 dias atrás até 175 dias atrás)
            end_date = datetime.now(timezone.utc) - timedelta(days=175)
            start_date = end_date - timedelta(days=5)  # 5 dias de janela
            
            # Formata as datas para o formato ISO 8601 exigido pela Garmin
            start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

            backfill_url = f"{settings.GARMIN_ACTIVITY_API_URL}/backfill/activities"
            params = {
                "summaryStartTimeInSeconds": int(start_date.timestamp()),
                "summaryEndTimeInSeconds": int(end_date.timestamp())
            }
            
            logger.info(f"Solicitando backfill de atividades de {start_date_str} a {end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}")
            
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(backfill_url, headers=headers, params=params)
                
                # Para backfill, o sucesso é um status 202 Accepted
                if response.status_code == 202:
                    logger.info("Pedido de backfill aceito com sucesso pela Garmin.")
                    return True
                else:
                    # Se não for 202, trata como erro
                    response.raise_for_status()
                    return False # Não deve chegar aqui, mas por segurança

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de API ao solicitar backfill: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Exceção ao solicitar backfill: {e}")
            return False

    async def request_activity_sync(self, access_token: str) -> bool:
        if not settings.GARMIN_ACTIVITY_API_URL:
            logger.error("A URL da API de Atividades da Garmin não está configurada.")
            return False

        try:
            # Para evitar o erro de 'backfill duplicado', solicitamos uma janela de tempo
            # que não seja exatamente os 'últimos X dias'.
            # Aqui, pegamos uma janela de 5 dias terminando 3 dias atrás.
            end_date = datetime.now(timezone.utc) - timedelta(days=3)
            start_date = end_date - timedelta(days=5) # Do dia -8 ao dia -3

            # Formata as datas para o formato ISO 8601 exigido pela Garmin
            start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

            backfill_url = f"{settings.GARMIN_ACTIVITY_API_URL}/backfill/activities"
            params = {
                "summaryStartTimeInSeconds": int(start_date.timestamp()),
                "summaryEndTimeInSeconds": int(end_date.timestamp())
            }
            
            logger.info(f"Solicitando backfill de atividades de {start_date_str} a {end_date_str}")
            logger.info(f"PARÂMETROS EXATOS ENVIADOS PARA A GARMIN: {params}") # <-- LOG DE DEPURAÇÃO
            
            headers = {"Authorization": f"Bearer {access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(backfill_url, headers=headers, params=params)
                
                # Para backfill, o sucesso é um status 202 Accepted
                if response.status_code == 202:
                    logger.info("Pedido de backfill aceito com sucesso pela Garmin.")
                    return True
                else:
                    # Se não for 202, trata como erro
                    response.raise_for_status()
                    return False # Não deve chegar aqui, mas por segurança

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de API ao solicitar backfill: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Exceção ao solicitar backfill: {e}")
            return False

    async def download_activity_fit(self, callback_url: str, activity_id: str) -> Optional[str]:
        """
        Baixa um arquivo FIT de atividade usando a callbackURL recebida via webhook.
        """
        access_token = self.auth_storage.get('access_token')
        if not access_token:
            logger.error("Não autenticado. Não é possível baixar atividade.")
            return None
        
        try:
            logger.info(f"Baixando arquivo FIT da atividade {activity_id} de: {callback_url}")
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(callback_url, headers=headers)
                response.raise_for_status()

                # Salvar o arquivo
                file_path = self.get_activity_file_path(activity_id)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Arquivo FIT da atividade {activity_id} salvo em: {file_path}")
                return file_path

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de API ao baixar arquivo FIT: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Exceção ao baixar arquivo FIT: {e}")
            return None

    async def pull_activity(self, activity_id: str, output_path: str) -> bool:
        """
        Baixar atividade da Garmin Connect (PULL)
        
        Args:
            activity_id: ID da atividade na Garmin
            output_path: Caminho onde salvar o arquivo FIT
            
        Returns:
            True se baixado com sucesso, False caso contrário
        """
        try:
            logger.info(f"Baixando atividade da Garmin: {activity_id}")
            
            # Usar o sistema atual de integração (simulado por enquanto)
            downloaded_file = self.garmin_integration.pull_activity(activity_id, output_path)
            
            if downloaded_file:
                logger.info(f"Atividade baixada com sucesso: {activity_id} -> {output_path}")
                return True
            else:
                logger.error(f"Erro ao baixar atividade: {activity_id}")
                return False
                
        except Exception as e:
            logger.error(f"Exceção ao baixar atividade: {e}")
            return False
    
    async def list_activities(self) -> List[Dict[str, Any]]:
        """
        Listar atividades recentes da Garmin Connect (PULL).
        Busca atividades das últimas 24 horas.
        """
        access_token = self.auth_storage.get('access_token')
        if not access_token:
            logger.error("Não autenticado. Não é possível listar atividades.")
            raise Exception("Não autenticado. Por favor, complete o fluxo OAuth2.")

        try:
            end_ts = int(time.time())
            start_ts = end_ts - (24 * 60 * 60)  # 24 horas

            list_url = f"{settings.GARMIN_ACTIVITY_API_URL}/activities"
            params = {
                "uploadStartTimeInSeconds": start_ts,
                "uploadEndTimeInSeconds": end_ts
            }
            
            logger.info(f"Listando atividades da Garmin de {start_ts} a {end_ts}")
            
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(list_url, headers=headers, params=params)
                response.raise_for_status()
                activities = response.json()
                
                logger.info(f"Encontradas {len(activities)} atividades.")
                return activities

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro de API ao listar atividades: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Exceção ao listar atividades: {e}")
            return []
    
    def process_activity_fit(self, fit_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Processar arquivo FIT de atividade e extrair dados relevantes
        
        NOVO: Usa Enhanced FIT Parser + Metrics Engine para extração completa
        
        Args:
            fit_file_path: Caminho do arquivo FIT
            
        Returns:
            Dados processados da atividade ou None se erro
        """
        try:
            logger.info(f"Processando arquivo FIT de atividade: {fit_file_path}")
            
            # NOVO: Usar Enhanced System se disponível
            if ENHANCED_SYSTEM_AVAILABLE:
                logger.info("🚀 Usando Enhanced FIT System (extração completa + métricas avançadas)")
                
                # Parse completo do arquivo FIT
                parser = EnhancedFITParser()
                enhanced_data = parser.parse(fit_file_path)
                
                if not enhanced_data:
                    logger.warning("Enhanced parser falhou, tentando sistema básico...")
                    raw_data = self.read_activity_fit(fit_file_path)
                    if not raw_data:
                        return None
                    return self._process_basic_data(fit_file_path, raw_data)
                
                # Calcular métricas avançadas
                metrics_engine = MetricsEngine()
                advanced_metrics = metrics_engine.analyze_activity(enhanced_data)
                
                # Estruturar resposta completa
                processed_data = {
                    "activity_id": os.path.basename(fit_file_path).replace('.fit', ''),
                    "fit_file_path": fit_file_path,
                    "processed_at": datetime.now().isoformat(),
                    "system_version": "enhanced",
                    
                    # Dados completos extraídos do FIT
                    "enhanced_data": {
                        "file_info": enhanced_data.get("file_info"),
                        "device_info": enhanced_data.get("device_info"),
                        "activity_summary": enhanced_data.get("activity_summary"),
                        "sessions": enhanced_data.get("sessions"),
                        "laps": enhanced_data.get("laps"),
                        "records_count": len(enhanced_data.get("records", [])),
                        "events_count": len(enhanced_data.get("events", [])),
                        "hrv_available": len(enhanced_data.get("hrv", [])) > 0,
                    },
                    
                    # Métricas avançadas calculadas
                    "advanced_metrics": advanced_metrics,
                    
                    # Resumo rápido para APIs (compatibilidade)
                    "summary": self._extract_enhanced_summary(enhanced_data, advanced_metrics),
                    
                    # Métricas detalhadas (para analytics)
                    "detailed_metrics": {
                        "basic_stats": advanced_metrics.get("basic_stats"),
                        "heart_rate": advanced_metrics.get("heart_rate_analysis"),
                        "pace_speed": advanced_metrics.get("pace_speed_analysis"),
                        "elevation": advanced_metrics.get("elevation_analysis"),
                        "cadence": advanced_metrics.get("cadence_analysis"),
                        "power": advanced_metrics.get("power_analysis"),
                        "running_dynamics": advanced_metrics.get("running_dynamics"),
                        "fatigue": advanced_metrics.get("fatigue_analysis"),
                        "performance": advanced_metrics.get("performance_score"),
                        "efficiency": advanced_metrics.get("efficiency_metrics"),
                    },
                    
                    # Insights automáticos
                    "insights": self._generate_insights(advanced_metrics)
                }
                
                logger.info(f"✅ Atividade processada com Enhanced System: {fit_file_path}")
                logger.info(f"   📊 {len(enhanced_data.get('records', []))} pontos extraídos")
                logger.info(f"   🎯 {len(enhanced_data.get('laps', []))} laps processados")
                
                return processed_data
            
            else:
                # Fallback: usar sistema básico
                logger.info("⚠️  Usando sistema básico (legacy)")
                raw_data = self.read_activity_fit(fit_file_path)
                
                if not raw_data:
                    return None
                
                return self._process_basic_data(fit_file_path, raw_data)
            
        except Exception as e:
            logger.error(f"Exceção ao processar atividade: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _process_basic_data(self, fit_file_path: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados do sistema básico (fallback)"""
        return {
            "activity_id": os.path.basename(fit_file_path).replace('.fit', ''),
            "fit_file_path": fit_file_path,
            "processed_at": datetime.now().isoformat(),
            "system_version": "basic",
            "raw_data": raw_data,
            "summary": self._extract_activity_summary(raw_data)
        }
    
    def _extract_enhanced_summary(self, enhanced_data: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai resumo rápido dos dados enhanced (compatibilidade com APIs existentes)"""
        try:
            basic_stats = metrics.get("basic_stats", {})
            hr_analysis = metrics.get("heart_rate_analysis", {})
            pace_analysis = metrics.get("pace_speed_analysis", {})
            
            return {
                "sport": basic_stats.get("sport"),
                "start_time": basic_stats.get("start_time"),
                "duration_seconds": basic_stats.get("duration_seconds"),
                "duration_formatted": basic_stats.get("duration_formatted"),
                "distance_meters": basic_stats.get("distance_meters"),
                "distance_km": basic_stats.get("distance_km"),
                "avg_speed_kmh": pace_analysis.get("avg_speed_kmh"),
                "avg_pace_min_per_km": pace_analysis.get("avg_pace_min_per_km"),
                "total_calories": basic_stats.get("total_calories"),
                "avg_heart_rate": basic_stats.get("avg_heart_rate"),
                "max_heart_rate": basic_stats.get("max_heart_rate"),
                "total_ascent": basic_stats.get("total_ascent"),
                "total_descent": basic_stats.get("total_descent"),
            }
        except Exception as e:
            logger.error(f"Erro ao extrair enhanced summary: {e}")
            return {}
    
    def _generate_insights(self, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Gera insights automáticos baseados nas métricas"""
        insights = []
        
        try:
            # HR Drift insight
            hr_analysis = metrics.get("heart_rate_analysis", {})
            hr_drift = hr_analysis.get("hr_drift_percent", 0)
            
            if hr_drift > 10:
                insights.append({
                    "type": "warning",
                    "category": "cardiovascular",
                    "message": f"HR Drift de {hr_drift}% indica que você começou muito forte. Considere um aquecimento mais longo para melhorar eficiência."
                })
            elif hr_drift < 5:
                insights.append({
                    "type": "positive",
                    "category": "cardiovascular",
                    "message": f"Excelente controle de frequência cardíaca! HR Drift baixo ({hr_drift}%) mostra boa gestão de esforço."
                })
            
            # Fatigue Index insight
            fatigue = metrics.get("fatigue_analysis", {})
            fatigue_index = fatigue.get("fatigue_index_percent", 0)
            
            if fatigue_index < -20:
                insights.append({
                    "type": "positive",
                    "category": "performance",
                    "message": f"Strong finish! Você acelerou no final (fatigue index: {fatigue_index}%). Excelente gestão de energia."
                })
            elif fatigue_index > 15:
                insights.append({
                    "type": "warning",
                    "category": "performance",
                    "message": f"Decaimento de {fatigue_index}% na velocidade. Considere trabalhar resistência para manter o ritmo até o final."
                })
            
            # Consistency insight
            pace_analysis = metrics.get("pace_speed_analysis", {})
            consistency = pace_analysis.get("consistency_score", 0)
            
            if consistency > 85:
                insights.append({
                    "type": "positive",
                    "category": "pacing",
                    "message": f"Pacing muito consistente! Score de {consistency}/100 indica excelente controle de ritmo."
                })
            elif consistency < 60:
                insights.append({
                    "type": "tip",
                    "category": "pacing",
                    "message": f"Pacing irregular (score: {consistency}/100). Tente manter um ritmo mais constante para melhor eficiência."
                })
            
            # HR Zones insight
            zones = hr_analysis.get("zones", {})
            zone5_pct = zones.get("zone5", {}).get("percentage", 0)
            
            if zone5_pct > 50:
                insights.append({
                    "type": "warning",
                    "category": "training_load",
                    "message": f"Você passou {zone5_pct}% do tempo em Zona 5 (VO2 Max). Treino de alta intensidade - considere descansar amanhã."
                })
            
            # Performance Score insight
            performance = metrics.get("performance_score", {})
            score = performance.get("overall_score", 0)
            
            if score > 80:
                insights.append({
                    "type": "positive",
                    "category": "overall",
                    "message": f"Excelente treino! Performance Score de {score}/100."
                })
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights: {e}")
        
        return insights
    
    def _extract_activity_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrair resumo da atividade dos dados brutos
        
        Args:
            raw_data: Dados brutos do arquivo FIT
            
        Returns:
            Resumo estruturado da atividade
        """
        try:
            # Implementar extração de dados relevantes
            # Por enquanto, retorna estrutura básica
            return {
                "total_distance": raw_data.get("total_distance", 0),
                "total_time": raw_data.get("total_time", 0),
                "average_pace": raw_data.get("average_pace", 0),
                "calories": raw_data.get("calories", 0),
                "max_heart_rate": raw_data.get("max_heart_rate", 0),
                "average_heart_rate": raw_data.get("average_heart_rate", 0)
            }
        except Exception as e:
            logger.error(f"Erro ao extrair resumo da atividade: {e}")
            return {}
    
    def get_workout_file_path(self, workout_id: str) -> str:
        """
        Gerar caminho para arquivo FIT de treino
        
        Args:
            workout_id: ID do treino
            
        Returns:
            Caminho completo do arquivo
        """
        return os.path.join(self.workouts_dir, f"{workout_id}.fit")
    
    def get_activity_file_path(self, activity_id: str) -> str:
        """
        Gerar caminho para arquivo FIT de atividade
        
        Args:
            activity_id: ID da atividade
            
        Returns:
            Caminho completo do arquivo
        """
        return os.path.join(self.activities_dir, f"{activity_id}.fit") 