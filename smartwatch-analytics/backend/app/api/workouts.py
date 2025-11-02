#!/usr/bin/env python3
"""
Endpoints para gerenciamento de treinos

Inclui criação, listagem, visualização e envio de treinos para Garmin Connect.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import uuid
import logging
from datetime import datetime, date
import os

from app.models.workout import (
    WorkoutCreate, 
    WorkoutResponse, 
    WorkoutListResponse,
    WorkoutUpdate,
    WorkoutStatus
)
from app.services.garmin_service import GarminService

logger = logging.getLogger(__name__)
router = APIRouter()

# Armazenamento temporário em memória (será substituído por banco de dados na Fase 3)
workouts_storage = {}

def get_garmin_service() -> GarminService:
    """Dependency para obter instância do serviço Garmin"""
    return GarminService()

@router.post("/", response_model=WorkoutResponse, status_code=201)
async def create_workout(
    workout: WorkoutCreate,
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Criar um novo treino
    
    - **nome_do_treino**: Nome do treino
    - **descricao**: Descrição opcional
    - **passos**: Lista de passos do treino
    """
    try:
        workout_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Passo 1: Enviar o treino para a Garmin para criá-lo
        garmin_workout_id = await garmin_service.push_workout(workout.dict())
        
        # Determinar status baseado no resultado do envio
        status = WorkoutStatus.SENT if garmin_workout_id else WorkoutStatus.FAILED
        
        # Passo 2: Se o treino foi criado com sucesso, agendá-lo no calendário
        if status == WorkoutStatus.SENT:
            today_str = date.today().isoformat()
            scheduled_ok = await garmin_service.schedule_workout(garmin_workout_id, today_str)
            if not scheduled_ok:
                # Não é um erro fatal, o treino foi criado mas não agendado.
                # Poderíamos definir um status diferente aqui se quiséssemos, ex: "created_not_scheduled"
                logger.warning(f"Treino {garmin_workout_id} criado, mas falhou ao agendar no calendário.")

        # Passo 3: Criar arquivo FIT local para referência (opcional)
        fit_file_path = None
        if status == WorkoutStatus.SENT:
            fit_file_path = garmin_service.get_workout_file_path(workout_id)
            if not garmin_service.create_workout_fit(workout.dict(), fit_file_path):
                logger.warning(f"Treino enviado para Garmin, mas falhou ao criar arquivo .fit local: {workout_id}")
                fit_file_path = None
        
        # Criar resposta
        workout_response = WorkoutResponse(
            id=workout_id,
            nome_do_treino=workout.nome_do_treino,
            descricao=workout.descricao,
            status=status,
            created_at=now,
            updated_at=now,
            garmin_workout_id=garmin_workout_id,
            fit_file_path=fit_file_path,
            passos=workout.passos
        )
        
        # Armazenar no storage temporário
        workouts_storage[workout_id] = workout_response.dict()
        
        logger.info(f"Treino criado com sucesso: {workout_id}")
        return workout_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar treino: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao criar treino"
        )

@router.get("/", response_model=WorkoutListResponse)
async def list_workouts(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(10, ge=1, le=100, description="Itens por página"),
    status: Optional[WorkoutStatus] = Query(None, description="Filtrar por status")
):
    """
    Listar treinos com paginação
    
    - **page**: Número da página (começa em 1)
    - **per_page**: Itens por página (máximo 100)
    - **status**: Filtrar por status (opcional)
    """
    try:
        # Filtrar treinos por status se especificado
        filtered_workouts = list(workouts_storage.values())
        if status:
            filtered_workouts = [w for w in filtered_workouts if w["status"] == status]
        
        # Calcular paginação
        total = len(filtered_workouts)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Aplicar paginação
        paginated_workouts = filtered_workouts[start_idx:end_idx]
        
        # Converter para WorkoutResponse
        workout_responses = [WorkoutResponse(**workout) for workout in paginated_workouts]
        
        return WorkoutListResponse(
            workouts=workout_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar treinos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao listar treinos"
        )

@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(workout_id: str):
    """
    Obter treino específico por ID
    
    - **workout_id**: ID único do treino
    """
    try:
        if workout_id not in workouts_storage:
            raise HTTPException(
                status_code=404,
                detail="Treino não encontrado"
            )
        
        workout_data = workouts_storage[workout_id]
        return WorkoutResponse(**workout_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter treino {workout_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao obter treino"
        )

@router.put("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: str,
    workout_update: WorkoutUpdate,
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Atualizar treino existente
    
    - **workout_id**: ID único do treino
    - **workout_update**: Dados para atualização
    """
    try:
        if workout_id not in workouts_storage:
            raise HTTPException(
                status_code=404,
                detail="Treino não encontrado"
            )
        
        # Obter treino atual
        current_workout = workouts_storage[workout_id]
        
        # Aplicar atualizações
        update_data = workout_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            current_workout[field] = value
        
        # Atualizar timestamp
        current_workout["updated_at"] = datetime.now().isoformat()
        
        # Se os passos foram atualizados, recriar arquivo FIT
        if "passos" in update_data:
            fit_file_path = garmin_service.get_workout_file_path(workout_id)
            success = garmin_service.create_workout_fit(current_workout, fit_file_path)
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao recriar arquivo FIT do treino"
                )
            
            # Reenviar para Garmin
            garmin_workout_id = await garmin_service.push_workout(current_workout)
            current_workout["garmin_workout_id"] = garmin_workout_id
            current_workout["status"] = WorkoutStatus.SENT if garmin_workout_id else WorkoutStatus.FAILED
        
        # Atualizar storage
        workouts_storage[workout_id] = current_workout
        
        logger.info(f"Treino atualizado com sucesso: {workout_id}")
        return WorkoutResponse(**current_workout)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar treino {workout_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao atualizar treino"
        )

@router.delete("/{workout_id}", status_code=204)
async def delete_workout(workout_id: str):
    """
    Deletar treino
    
    - **workout_id**: ID único do treino
    """
    try:
        if workout_id not in workouts_storage:
            raise HTTPException(
                status_code=404,
                detail="Treino não encontrado"
            )
        
        # Remover do storage
        del workouts_storage[workout_id]
        
        logger.info(f"Treino deletado com sucesso: {workout_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar treino {workout_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao deletar treino"
        )

@router.post("/{workout_id}/send", response_model=WorkoutResponse)
async def send_workout_to_garmin(
    workout_id: str,
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Reenviar treino para Garmin Connect
    
    - **workout_id**: ID único do treino
    """
    try:
        if workout_id not in workouts_storage:
            raise HTTPException(
                status_code=404,
                detail="Treino não encontrado"
            )
        
        workout_data = workouts_storage[workout_id]
        
        # Enviar para Garmin
        garmin_workout_id = await garmin_service.push_workout(workout_data)
        
        # Atualizar status
        workout_data["garmin_workout_id"] = garmin_workout_id
        workout_data["status"] = WorkoutStatus.SENT if garmin_workout_id else WorkoutStatus.FAILED
        workout_data["updated_at"] = datetime.now().isoformat()
        
        # Atualizar storage
        workouts_storage[workout_id] = workout_data
        
        logger.info(f"Treino reenviado para Garmin: {workout_id}")
        return WorkoutResponse(**workout_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reenviar treino {workout_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao reenviar treino"
        )

@router.get("/{workout_id}/fit")
async def download_workout_fit(workout_id: str):
    """
    Download do arquivo FIT do treino
    
    - **workout_id**: ID único do treino
    """
    try:
        if workout_id not in workouts_storage:
            raise HTTPException(
                status_code=404,
                detail="Treino não encontrado"
            )
        
        garmin_service = GarminService()
        fit_file_path = garmin_service.get_workout_file_path(workout_id)
        
        if not os.path.exists(fit_file_path):
            raise HTTPException(
                status_code=404,
                detail="Arquivo FIT não encontrado"
            )
        
        # Retornar arquivo FIT
        from fastapi.responses import FileResponse
        return FileResponse(
            fit_file_path,
            media_type="application/octet-stream",
            filename=f"workout_{workout_id}.fit"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo FIT do treino {workout_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor ao baixar arquivo FIT"
        ) 