#!/usr/bin/env python3
"""
Endpoints para Backfill Histórico Completo
===========================================

Permite extrair TODO o histórico de dados de um atleta.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.services.garmin_service import temp_auth_storage
from app.services.historical_backfill import HistoricalBackfillService

router = APIRouter()


class BackfillRequest(BaseModel):
    """Request body para backfill histórico"""
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None    # ISO format
    years_back: Optional[int] = None  # Alternativa: quantos anos buscar


@router.post("/activities/backfill-complete")
async def backfill_complete_activity_history(
    request: BackfillRequest = Body(...)
):
    """
    Faz backfill completo do histórico de atividades
    
    Busca TODO o histórico disponível (múltiplas requisições de 30 dias).
    Os dados serão enviados via webhook quando disponíveis.
    
    Args:
        start_date: Data inicial (ISO format, padrão: 5 anos atrás)
        end_date: Data final (ISO format, padrão: hoje)
        years_back: Alternativa: buscar dados dos últimos X anos
    """
    access_token = temp_auth_storage.get('access_token')
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Faça login primeiro em /auth/garmin/authorize"
        )
    
    # Parse dates
    end_date = datetime.now().replace(tzinfo=datetime.now().astimezone().tzinfo)
    if request.end_date:
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    
    start_date = None
    if request.start_date:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    elif request.years_back:
        start_date = end_date - timedelta(days=request.years_back * 365)
    else:
        # Padrão: 5 anos
        start_date = end_date - timedelta(days=5 * 365)
    
    service = HistoricalBackfillService(access_token)
    result = await service.backfill_complete_activity_history(start_date, end_date)
    
    return {
        "message": "Backfill histórico de atividades iniciado",
        **result
    }


@router.post("/health/backfill-complete/{summary_type}")
async def backfill_complete_health_history(
    summary_type: str,
    request: BackfillRequest = Body(...)
):
    """
    Faz backfill completo de um tipo específico de dados de saúde
    
    Tipos suportados:
    - dailies (resumo diário)
    - epochs (dados a cada 15 minutos)
    - sleeps (sono)
    - stressDetails (estresse)
    - bodyComps (composição corporal)
    - userMetrics (métricas do usuário)
    - pulseOx (oxigenação)
    - respiration (respiração)
    - healthSnapshot (snapshot de saúde)
    - hrv (variabilidade cardíaca)
    - bloodPressures (pressão arterial)
    - skinTemp (temperatura da pele)
    """
    access_token = temp_auth_storage.get('access_token')
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Faça login primeiro em /auth/garmin/authorize"
        )
    
    valid_types = [
        "dailies", "epochs", "sleeps", "stressDetails", "bodyComps",
        "userMetrics", "pulseOx", "respiration", "healthSnapshot",
        "hrv", "bloodPressures", "skinTemp"
    ]
    
    if summary_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo inválido. Use um dos: {', '.join(valid_types)}"
        )
    
    # Parse dates
    end_date = datetime.now().replace(tzinfo=datetime.now().astimezone().tzinfo)
    if request.end_date:
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    
    start_date = None
    if request.start_date:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    elif request.years_back:
        start_date = end_date - timedelta(days=request.years_back * 365)
    else:
        # Padrão: 2 anos para health data
        start_date = end_date - timedelta(days=2 * 365)
    
    service = HistoricalBackfillService(access_token)
    result = await service.backfill_complete_health_history(
        summary_type, start_date, end_date
    )
    
    return {
        "message": f"Backfill histórico de {summary_type} iniciado",
        **result
    }


@router.post("/health/backfill-all")
async def backfill_all_health_data(
    request: BackfillRequest = Body(...)
):
    """
    Faz backfill completo de TODOS os tipos de dados de saúde
    
    Busca todos os 12 tipos de summary de saúde disponíveis.
    """
    access_token = temp_auth_storage.get('access_token')
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Faça login primeiro em /auth/garmin/authorize"
        )
    
    # Parse dates
    end_date = datetime.now().replace(tzinfo=datetime.now().astimezone().tzinfo)
    if request.end_date:
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    
    start_date = None
    if request.start_date:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    elif request.years_back:
        start_date = end_date - timedelta(days=request.years_back * 365)
    else:
        start_date = end_date - timedelta(days=2 * 365)
    
    service = HistoricalBackfillService(access_token)
    result = await service.backfill_all_health_data(start_date, end_date)
    
    return {
        "message": "Backfill histórico completo de todos os dados de saúde iniciado",
        **result
    }


@router.post("/backfill-everything")
async def backfill_everything(
    request: BackfillRequest = Body(...)
):
    """
    🚀 BACKFILL COMPLETO DE TUDO
    
    Faz backfill de:
    - Todas as atividades históricas
    - Todos os tipos de dados de saúde
    
    Isso pode levar algum tempo e fazer muitas requisições.
    Os dados serão recebidos via webhooks.
    """
    access_token = temp_auth_storage.get('access_token')
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado. Faça login primeiro em /auth/garmin/authorize"
        )
    
    # Parse dates
    end_date = datetime.now().replace(tzinfo=datetime.now().astimezone().tzinfo)
    if request.end_date:
        end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
    
    start_date = None
    if request.start_date:
        start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    elif request.years_back:
        start_date = end_date - timedelta(days=request.years_back * 365)
    else:
        # Padrão: 5 anos para atividades, 2 anos para health
        start_date = end_date - timedelta(days=5 * 365)
    
    service = HistoricalBackfillService(access_token)
    
    # Fazer backfill de atividades e health em paralelo
    activity_result = await service.backfill_complete_activity_history(start_date, end_date)
    
    # Para health, usar 2 anos
    health_start = end_date - timedelta(days=2 * 365)
    health_result = await service.backfill_all_health_data(health_start, end_date)
    
    return {
        "message": "Backfill histórico completo iniciado",
        "activities": activity_result,
        "health_data": health_result,
        "note": "Os dados serão recebidos via webhooks conforme ficarem disponíveis. "
                "Pode levar alguns minutos ou horas dependendo do volume de dados."
    }

