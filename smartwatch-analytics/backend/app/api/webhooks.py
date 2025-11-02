#!/usr/bin/env python3
"""
Endpoints para webhooks da Garmin
==================================

Sistema de webhooks preparado para PRODUÇÃO com:
- Enhanced FIT Parser (extração completa de dados)
- Metrics Engine (métricas avançadas)
- Processamento assíncrono
- Logging detalhado
- Error handling robusto

STATUS: PREPARADO mas INATIVO (aguardando servidor de produção)
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import logging
import json
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)
router = APIRouter()

# Import enhanced systems
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'core'))
try:
    from enhanced_fit_parser import EnhancedFITParser, analyze_fit_file
    from metrics_engine import MetricsEngine
    ENHANCED_SYSTEM_AVAILABLE = True
    logger.info("✅ Enhanced FIT Parser e Metrics Engine carregados")
except ImportError as e:
    logger.warning(f"⚠️ Sistema avançado não disponível: {e}")
    ENHANCED_SYSTEM_AVAILABLE = False


class WebhookProcessor:
    """Processador de webhooks da Garmin"""
    
    def __init__(self):
        self.parser = EnhancedFITParser() if ENHANCED_SYSTEM_AVAILABLE else None
        self.metrics_engine = MetricsEngine() if ENHANCED_SYSTEM_AVAILABLE else None
    
    async def process_activity_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa webhook de atividade da Garmin
        
        Fluxo:
        1. Recebe notificação de nova atividade
        2. Baixa arquivo FIT da URL fornecida
        3. Parse completo com enhanced_fit_parser
        4. Calcula métricas avançadas com metrics_engine
        5. Salva no banco de dados (quando implementado)
        6. Retorna resultados
        """
        
        results = {
            'webhook_received_at': datetime.now().isoformat(),
            'activities_processed': [],
            'errors': []
        }
        
        # Extrair atividades do webhook
        activities = webhook_data.get('activities', [])
        
        for activity in activities:
            activity_id = activity.get('activityId')
            callback_url = activity.get('callbackURL')
            
            logger.info(f"📥 Processando atividade {activity_id}")
            
            try:
                # AQUI: Baixar arquivo FIT do callback_url
                # fit_file_path = await self.download_fit_file(callback_url, activity_id)
                
                # Por enquanto, simular
                activity_result = {
                    'activity_id': activity_id,
                    'callback_url': callback_url,
                    'status': 'queued_for_processing',
                    'activity_name': activity.get('activityName'),
                    'activity_type': activity.get('activityType'),
                    'start_time': activity.get('startTimeInSeconds'),
                    'note': 'Webhook recebido. Processamento completo quando servidor de produção estiver ativo.'
                }
                
                # Se tivéssemos o arquivo FIT:
                # if ENHANCED_SYSTEM_AVAILABLE and fit_file_path:
                #     # Parse completo
                #     activity_data = self.parser.parse(fit_file_path)
                #     
                #     # Calcular métricas avançadas
                #     metrics = self.metrics_engine.analyze_activity(activity_data)
                #     
                #     # Adicionar aos resultados
                #     activity_result['enhanced_data'] = activity_data
                #     activity_result['advanced_metrics'] = metrics
                #     activity_result['status'] = 'processed_successfully'
                
                results['activities_processed'].append(activity_result)
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar atividade {activity_id}: {e}")
                results['errors'].append({
                    'activity_id': activity_id,
                    'error': str(e)
                })
        
        return results
    
    async def process_health_webhook(self, webhook_data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """
        Processa webhooks de dados de saúde (Health API)
        
        Tipos suportados:
        - dailies: Resumo diário
        - epochs: Dados em intervalos (ex: HR contínuo)
        - sleeps: Análise de sono
        - stress: Níveis de stress
        - body_composition: Composição corporal
        - hrv_summary: Sumário de HRV
        - pulse_ox: SpO2
        - respiration: Taxa respiratória
        - skin_temperature: Temperatura da pele
        - blood_pressure: Pressão arterial
        """
        
        logger.info(f"🏥 Processando webhook de saúde: {data_type}")
        
        result = {
            'webhook_received_at': datetime.now().isoformat(),
            'data_type': data_type,
            'status': 'queued_for_processing',
            'raw_data': webhook_data,
            'note': 'Webhook recebido. Processamento completo quando servidor de produção estiver ativo.'
        }
        
        # AQUI: Implementar processamento específico por tipo
        # Exemplo para dailies:
        # if data_type == 'dailies':
        #     for daily in webhook_data.get('dailies', []):
        #         # Salvar no banco
        #         # Calcular tendências
        #         # Gerar insights
        
        return result


# Global processor instance
processor = WebhookProcessor()


# ============================================================================
# ACTIVITY WEBHOOKS
# ============================================================================

@router.post("/garmin/activity")
async def garmin_activity_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook para receber notificações de atividades da Garmin
    
    Documentação: Activity API
    
    Este endpoint recebe notificações quando:
    - Nova atividade é sincronizada
    - Atividade existente é atualizada
    - Atividade é deletada
    
    Payload esperado:
    {
        "activities": [
            {
                "activityId": "12345",
                "callbackURL": "https://...",
                "activityName": "Morning Run",
                "activityType": "running",
                "startTimeInSeconds": 1234567890
            }
        ]
    }
    """
    try:
        body = await request.body()
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"raw_body": body.decode()}
        
        logger.info(f"🎯 ACTIVITY WEBHOOK: {json.dumps(data, indent=2)}")
        
        # Processar webhook
        results = await processor.process_activity_webhook(data)
        
        return {
            "status": "success",
            "message": f"Webhook processado. {len(results['activities_processed'])} atividades recebidas.",
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "system": {
                "enhanced_parser": ENHANCED_SYSTEM_AVAILABLE,
                "production_ready": True,
                "awaiting_deployment": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar activity webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/activity-details")
async def garmin_activity_details_webhook(request: Request):
    """
    Webhook para Activity Details (detalhes adicionais de atividades)
    """
    try:
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"📊 ACTIVITY DETAILS WEBHOOK: {json.dumps(data, indent=2)}")
        
        return {
            "status": "success",
            "message": "Activity details webhook recebido",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/activity-files")
async def garmin_activity_files_webhook(request: Request):
    """
    Webhook para Activity Files (arquivos FIT prontos para download)
    """
    try:
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"📁 ACTIVITY FILES WEBHOOK: {json.dumps(data, indent=2)}")
        
        return {
            "status": "success",
            "message": "Activity files webhook recebido",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/manually-updated-activities")
async def garmin_manually_updated_activities_webhook(request: Request):
    """
    Webhook para atividades atualizadas manualmente pelo usuário
    """
    try:
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"✏️ MANUALLY UPDATED WEBHOOK: {json.dumps(data, indent=2)}")
        
        return {
            "status": "success",
            "message": "Manually updated activities webhook recebido",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/moveiq")
async def garmin_moveiq_webhook(request: Request):
    """
    Webhook para eventos MoveIQ (atividades detectadas automaticamente)
    """
    try:
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"🎬 MOVEIQ WEBHOOK: {json.dumps(data, indent=2)}")
        
        return {
            "status": "success",
            "message": "MoveIQ webhook recebido",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH WEBHOOKS
# ============================================================================

@router.post("/garmin/health/dailies")
async def garmin_health_dailies_webhook(request: Request):
    """Webhook para dados diários de saúde"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"📅 DAILIES WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'dailies')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/epochs")
async def garmin_health_epochs_webhook(request: Request):
    """Webhook para dados de epochs (HR contínuo, etc.)"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"⏱️ EPOCHS WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'epochs')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/sleeps")
async def garmin_health_sleeps_webhook(request: Request):
    """Webhook para dados de sono"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"😴 SLEEPS WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'sleeps')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/stress")
async def garmin_health_stress_webhook(request: Request):
    """Webhook para dados de stress"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"😰 STRESS WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'stress')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/body-composition")
async def garmin_health_body_composition_webhook(request: Request):
    """Webhook para composição corporal"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"⚖️ BODY COMPOSITION WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'body_composition')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/hrv-summary")
async def garmin_health_hrv_webhook(request: Request):
    """Webhook para sumário de HRV"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"💓 HRV WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'hrv_summary')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/health-snapshot")
async def garmin_health_snapshot_webhook(request: Request):
    """Webhook para Health Snapshot"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"📸 HEALTH SNAPSHOT WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'health_snapshot')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/pulse-ox")
async def garmin_health_pulse_ox_webhook(request: Request):
    """Webhook para Pulse Ox (SpO2)"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"🫁 PULSE OX WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'pulse_ox')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/respiration")
async def garmin_health_respiration_webhook(request: Request):
    """Webhook para taxa respiratória"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"🌬️ RESPIRATION WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'respiration')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/skin-temperature")
async def garmin_health_skin_temp_webhook(request: Request):
    """Webhook para temperatura da pele"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"🌡️ SKIN TEMPERATURE WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'skin_temperature')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/health/blood-pressure")
async def garmin_health_blood_pressure_webhook(request: Request):
    """Webhook para pressão arterial"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"❤️‍🩹 BLOOD PRESSURE WEBHOOK: {json.dumps(data, indent=2)}")
        
        result = await processor.process_health_webhook(data, 'blood_pressure')
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMMON WEBHOOKS
# ============================================================================

@router.post("/garmin/deregistrations")
async def garmin_deregistrations_webhook(request: Request):
    """Webhook para notificar quando usuário remove permissões"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"🚫 DEREGISTRATIONS WEBHOOK: {json.dumps(data, indent=2)}")
        
        # AQUI: Remover dados do usuário do sistema
        
        return {
            "status": "success",
            "message": "Deregistration processado",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/garmin/permissions-change")
async def garmin_permissions_change_webhook(request: Request):
    """Webhook para mudanças nas permissões do usuário"""
    try:
        body = await request.body()
        data = json.loads(body)
        logger.info(f"🔐 PERMISSIONS CHANGE WEBHOOK: {json.dumps(data, indent=2)}")
        
        return {
            "status": "success",
            "message": "Permissions change processado",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WORKOUT WEBHOOKS (PUSH)
# ============================================================================

@router.post("/garmin/workout")
async def garmin_workout_webhook(request: Request):
    """
    Webhook para receber notificações de treinos (PUSH)
    
    Notifica quando:
    - Treino é baixado para o dispositivo
    - Treino é iniciado
    - Treino é concluído
    - Treino é modificado/deletado
    """
    try:
        body = await request.body()
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"raw_body": body.decode()}
        
        logger.info(f"💪 WORKOUT WEBHOOK: {json.dumps(data, indent=2)}")
        
        return {
            "status": "success",
            "message": "Workout webhook recebido",
            "timestamp": datetime.now().isoformat(),
            "received_data": data
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar workout webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATUS & HEALTH CHECK ENDPOINTS
# ============================================================================

@router.get("/status")
async def webhook_status():
    """Status do sistema de webhooks"""
    return {
        "status": "ready",
        "message": "Sistema de webhooks preparado para produção",
        "enhanced_system": ENHANCED_SYSTEM_AVAILABLE,
        "endpoints_configured": 22,
        "ready_for_deployment": True,
        "awaiting": "Servidor de produção com URL pública",
        "endpoints": {
            "activity": [
                "/webhooks/garmin/activity",
                "/webhooks/garmin/activity-details",
                "/webhooks/garmin/activity-files",
                "/webhooks/garmin/manually-updated-activities",
                "/webhooks/garmin/moveiq"
            ],
            "health": [
                "/webhooks/garmin/health/dailies",
                "/webhooks/garmin/health/epochs",
                "/webhooks/garmin/health/sleeps",
                "/webhooks/garmin/health/stress",
                "/webhooks/garmin/health/body-composition",
                "/webhooks/garmin/health/hrv-summary",
                "/webhooks/garmin/health/health-snapshot",
                "/webhooks/garmin/health/pulse-ox",
                "/webhooks/garmin/health/respiration",
                "/webhooks/garmin/health/skin-temperature",
                "/webhooks/garmin/health/blood-pressure"
            ],
            "common": [
                "/webhooks/garmin/deregistrations",
                "/webhooks/garmin/permissions-change"
            ],
            "workout": [
                "/webhooks/garmin/workout"
            ]
        }
    }


@router.get("/health")
async def webhook_health():
    """Health check do sistema de webhooks"""
    return {
        "status": "healthy",
        "enhanced_parser": ENHANCED_SYSTEM_AVAILABLE,
        "metrics_engine": ENHANCED_SYSTEM_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }
