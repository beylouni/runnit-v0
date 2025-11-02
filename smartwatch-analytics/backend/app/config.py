#!/usr/bin/env python3
"""
Configurações do Backend Garmin Integration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Configurações básicas
    APP_NAME: str = "Garmin Integration API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Configurações de segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Configurações da Garmin
    GARMIN_CLIENT_ID: Optional[str] = os.getenv("GARMIN_CLIENT_ID")
    GARMIN_CLIENT_SECRET: Optional[str] = os.getenv("GARMIN_CLIENT_SECRET")
    GARMIN_REDIRECT_URI: str = os.getenv("GARMIN_REDIRECT_URI", "http://localhost:8002/auth/garmin/callback")
    
    # URLs da API Garmin
    GARMIN_AUTH_URL: str = "https://connect.garmin.com/oauth2Confirm"
    GARMIN_TOKEN_URL: str = "https://diauth.garmin.com/di-oauth2-service/oauth/token"
    # ATENÇÃO: A URL de treino foi atualizada para o endpoint de criação de workout via JSON
    GARMIN_TRAINING_API_URL: str = "https://apis.garmin.com/workoutportal/workout/v2"
    GARMIN_SCHEDULE_API_URL: str = "https://apis.garmin.com/training-api/schedule/"
    GARMIN_ACTIVITY_API_URL: str = "https://apis.garmin.com/wellness-api/rest"
    
    # Escopos para permissões
    GARMIN_SCOPES: str = "WORKOUT_WRITE ACTIVITY_READ"
    
    # Configurações de arquivos
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    WORKOUTS_DIR: str = os.getenv("WORKOUTS_DIR", "uploads/workouts")
    ACTIVITIES_DIR: str = os.getenv("ACTIVITIES_DIR", "uploads/activities")
    
    # Configurações de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Configurações de CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Configurações de rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    
    # Configurações de banco de dados (serão implementadas na Fase 3)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Configurações de Redis (serão implementadas na Fase 5)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    class Config:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
        case_sensitive = True

# Instância global das configurações
settings = Settings()

# Criar diretórios necessários
def create_directories():
    """Criar diretórios necessários para a aplicação"""
    directories = [
        settings.UPLOAD_DIR,
        settings.WORKOUTS_DIR,
        settings.ACTIVITIES_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Criar diretórios na inicialização
create_directories() 