#!/usr/bin/env python3
"""
Endpoints para gerenciamento de atividades

Inclui listagem e download de atividades da Garmin Connect.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional

from app.services.garmin_service import GarminService

router = APIRouter()

def get_garmin_service() -> GarminService:
    """Dependency para obter instância do serviço Garmin"""
    return GarminService()

@router.get("/", response_model=List[dict])
async def list_garmin_activities(
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    (LEGADO - PODE NÃO FUNCIONAR COM TOKENS DE USUÁRIO)
    Tenta listar as atividades recentes da Garmin (últimas 24 horas).
    """
    try:
        activities = await garmin_service.list_activities()
        return activities
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/request-sync", status_code=202)
async def request_activity_sync(
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Solicita à Garmin um backfill dos dados de atividades dos últimos 30 dias.
    Este é um processo assíncrono. A Garmin enviará os dados para o webhook configurado.
    """
    try:
        success = await garmin_service.request_activity_backfill(days=30)
        if success:
            return {"message": "Pedido de sincronização de atividades aceito pela Garmin. Os dados serão enviados para o webhook configurado."}
        else:
            raise HTTPException(status_code=500, detail="A Garmin rejeitou o pedido de sincronização.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/process-activity")
async def process_single_activity(
    callback_url: str = Body(..., embed=True),
    activity_id: str = Body(..., embed=True),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Recebe uma callbackURL de um webhook, baixa o arquivo .fit e o processa.
    """
    try:
        # Etapa 2: Baixar o arquivo .fit
        fit_file_path = await garmin_service.download_activity_fit(callback_url, activity_id)
        if not fit_file_path:
            raise HTTPException(status_code=500, detail="Falha ao baixar o arquivo FIT da Garmin.")

        # Etapa 3: Processar com Enhanced System
        activity_data = garmin_service.process_activity_fit(fit_file_path)
        if not activity_data:
            raise HTTPException(status_code=500, detail="Falha ao processar o arquivo FIT baixado.")

        return {
            "message": "Atividade baixada e processada com sucesso!",
            "fit_file_path": fit_file_path,
            "system_version": activity_data.get("system_version"),
            "summary": activity_data.get("summary"),
            "detailed_metrics": activity_data.get("detailed_metrics"),
            "insights": activity_data.get("insights"),
            "enhanced_data_preview": {
                "records_count": activity_data.get("enhanced_data", {}).get("records_count", 0),
                "laps_count": len(activity_data.get("enhanced_data", {}).get("laps", [])),
                "hrv_available": activity_data.get("enhanced_data", {}).get("hrv_available", False),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{activity_id}/process-local")
async def process_local_activity(
    activity_id: str,
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Processa um arquivo FIT que já existe localmente (para testes).
    Útil quando o arquivo já foi baixado antes.
    """
    import os
    try:
        # Verificar se o arquivo existe
        fit_file_path = os.path.join(garmin_service.activities_dir, f"{activity_id}.fit")
        
        if not os.path.exists(fit_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Arquivo FIT não encontrado: {activity_id}.fit. Faça o download primeiro via /activities/process-activity"
            )

        # Processar com Enhanced System
        activity_data = garmin_service.process_activity_fit(fit_file_path)
        
        if not activity_data:
            raise HTTPException(status_code=500, detail="Falha ao processar o arquivo FIT.")

        return {
            "message": "✅ Atividade processada com Enhanced System!",
            "activity_id": activity_id,
            "fit_file_path": fit_file_path,
            "system_version": activity_data.get("system_version"),
            "summary": activity_data.get("summary"),
            "detailed_metrics": activity_data.get("detailed_metrics"),
            "insights": activity_data.get("insights"),
            "enhanced_data_preview": {
                "records_count": activity_data.get("enhanced_data", {}).get("records_count", 0),
                "laps_count": len(activity_data.get("enhanced_data", {}).get("laps", [])),
                "sessions_count": len(activity_data.get("enhanced_data", {}).get("sessions", [])),
                "hrv_available": activity_data.get("enhanced_data", {}).get("hrv_available", False),
                "device_info": activity_data.get("enhanced_data", {}).get("device_info", []),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 