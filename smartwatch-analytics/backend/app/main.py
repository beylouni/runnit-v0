#!/usr/bin/env python3
"""
Garmin Integration Backend - FastAPI Application

Backend principal para integração com Garmin Connect API.
Inclui endpoints para PUSH de treinos e PULL de atividades.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime

# Importar configurações e garantir que o .env seja carregado
from app.config import settings

# Importar routers
from app.api import workouts, activities, auth, webhooks, analytics, maps, historical, database_init, data_query
from app.services.garmin_service import GarminService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Garmin Integration API",
    description="API para integração com Garmin Connect - PUSH de treinos e PULL de atividades",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, configurar para domínio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(workouts.router, prefix="/workouts", tags=["Treinos"])
app.include_router(activities.router, prefix="/activities", tags=["Atividades"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(maps.router, prefix="/maps", tags=["Mapas e GPS"])
app.include_router(historical.router, prefix="/historical", tags=["Backfill Histórico"])
app.include_router(database_init.router, prefix="/db", tags=["Database"])
app.include_router(data_query.router, prefix="/data", tags=["Consulta de Dados"])

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "Garmin Integration API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check da aplicação"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "garmin-integration-api"
    }

@app.get("/status")
async def status():
    """Status detalhado da aplicação"""
    try:
        # Verificar se o serviço Garmin está funcionando
        garmin_service = GarminService()
        garmin_status = "connected" if garmin_service.is_available() else "disconnected"
        
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "garmin_integration": garmin_status,
                "database": "not_implemented",  # Será implementado na Fase 3
                "redis": "not_implemented"      # Será implementado na Fase 5
            },
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 