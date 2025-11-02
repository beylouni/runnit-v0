#!/usr/bin/env python3
"""
Modelos Pydantic para Treinos
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class WorkoutStepType(str, Enum):
    """Tipos de passos de treino"""
    AQUECIMENTO = "aquecimento"
    CORRIDA = "corrida"
    DESAQUECIMENTO = "desaquecimento"
    WARMUP = "warmup"
    ACTIVE = "active"
    COOLDOWN = "cooldown"

class DurationType(str, Enum):
    """Tipos de duração"""
    TEMPO = "tempo"
    DISTANCIA = "distancia"
    TIME = "time"
    DISTANCE = "distance"

class WorkoutStep(BaseModel):
    """Modelo para um passo de treino"""
    nome_do_passo: str = Field(..., description="Nome do passo do treino")
    tipo_de_passo: WorkoutStepType = Field(..., description="Tipo do passo")
    duracao_tipo: DurationType = Field(..., description="Tipo de duração (tempo ou distância)")
    duracao_valor: int = Field(..., gt=0, description="Valor da duração em segundos ou metros")
    meta_tipo: Optional[str] = Field(None, description="Tipo de meta (ritmo, frequencia_cardiaca, etc.)")
    meta_valor_min: Optional[int] = Field(None, description="Valor mínimo da meta")
    meta_valor_max: Optional[int] = Field(None, description="Valor máximo da meta")
    
    @validator('duracao_valor')
    def validate_duration_value(cls, v, values):
        """Validar valor da duração baseado no tipo"""
        duracao_tipo = values.get('duracao_tipo')
        
        if duracao_tipo in [DurationType.TEMPO, DurationType.TIME]:
            if v > 36000:  # 10 horas em segundos
                raise ValueError("Duração em tempo muito longa (máximo 10 horas)")
        elif duracao_tipo in [DurationType.DISTANCIA, DurationType.DISTANCE]:
            if v > 100000:  # 100km em metros
                raise ValueError("Distância muito longa (máximo 100km)")
        
        return v

class WorkoutStatus(str, Enum):
    """Status do treino"""
    CREATED = "created"
    SENT = "sent"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkoutCreate(BaseModel):
    """Modelo para criação de treino"""
    nome_do_treino: str = Field(..., min_length=1, max_length=100, description="Nome do treino")
    descricao: Optional[str] = Field(None, max_length=500, description="Descrição opcional do treino")
    passos: List[WorkoutStep] = Field(..., min_items=1, max_items=50, description="Lista de passos do treino")
    
    # @validator('passos')
    # def validate_steps(cls, v):
    #     """Validar que há pelo menos um passo de aquecimento e desaquecimento"""
    #     step_types = [step.tipo_de_passo for step in v]
        
    #     if WorkoutStepType.AQUECIMENTO not in step_types and WorkoutStepType.WARMUP not in step_types:
    #         raise ValueError("Treino deve ter pelo menos um passo de aquecimento")
        
    #     if WorkoutStepType.DESAQUECIMENTO not in step_types and WorkoutStepType.COOLDOWN not in step_types:
    #         raise ValueError("Treino deve ter pelo menos um passo de desaquecimento")
        
    #     return v

class WorkoutResponse(BaseModel):
    """Modelo para resposta de treino"""
    id: str = Field(..., description="ID único do treino")
    nome_do_treino: str = Field(..., description="Nome do treino")
    descricao: Optional[str] = Field(None, description="Descrição do treino")
    status: WorkoutStatus = Field(..., description="Status atual do treino")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")
    garmin_workout_id: Optional[str] = Field(None, description="ID do treino na Garmin")
    fit_file_path: Optional[str] = Field(None, description="Caminho do arquivo FIT")
    passos: List[WorkoutStep] = Field(..., description="Lista de passos do treino")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class WorkoutListResponse(BaseModel):
    """Modelo para lista de treinos"""
    workouts: List[WorkoutResponse] = Field(..., description="Lista de treinos")
    total: int = Field(..., description="Total de treinos")
    page: int = Field(..., description="Página atual")
    per_page: int = Field(..., description="Itens por página")

class WorkoutUpdate(BaseModel):
    """Modelo para atualização de treino"""
    nome_do_treino: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = Field(None, max_length=500)
    passos: Optional[List[WorkoutStep]] = Field(None, min_items=1, max_items=50) 