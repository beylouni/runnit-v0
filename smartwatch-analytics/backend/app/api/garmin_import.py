"""
API Endpoint para Importação Histórica do Garmin Connect
=========================================================

Endpoint para importar dados históricos diretamente do Garmin Connect
usando credenciais de usuário (username/password).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Verificar se garminconnect está disponível
try:
    from app.services.garmin_historical_import import GarminHistoricalImporter, GARMINCONNECT_AVAILABLE
except ImportError:
    GARMINCONNECT_AVAILABLE = False
    logger.warning("⚠️ garminconnect não disponível")


class ImportRequest(BaseModel):
    """Request para importação histórica"""
    email: str = Field(..., description="Email do Garmin Connect")
    password: str = Field(..., description="Senha do Garmin Connect")
    start_date: Optional[str] = Field(None, description="Data de início (ISO 8601, ex: 2023-01-01)")
    end_date: Optional[str] = Field(None, description="Data de fim (ISO 8601, ex: 2024-12-31)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "seu_email@example.com",
                "password": "sua_senha",
                "start_date": "2023-01-01",
                "end_date": "2024-12-31"
            }
        }


@router.post("/import-from-garmin")
async def import_historical_data(request: ImportRequest, background_tasks: BackgroundTasks):
    """
    Importar dados históricos do Garmin Connect
    
    Este endpoint:
    1. Autentica com Garmin Connect usando email/senha
    2. Busca todas as atividades no período especificado
    3. Salva no banco de dados PostgreSQL
    
    **Atenção:** Este processo pode demorar vários minutos dependendo
    da quantidade de atividades. A importação roda em background.
    
    **Segurança:** As credenciais NÃO são armazenadas, apenas usadas
    para autenticação durante a importação.
    """
    if not GARMINCONNECT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Serviço de importação não disponível. "
                   "Instale: pip install garminconnect"
        )
    
    try:
        # Parse dates
        start_date = None
        end_date = None
        
        if request.start_date:
            try:
                start_date = datetime.fromisoformat(request.start_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Data de início inválida: {request.start_date}. Use formato ISO 8601 (YYYY-MM-DD)"
                )
        
        if request.end_date:
            try:
                end_date = datetime.fromisoformat(request.end_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Data de fim inválida: {request.end_date}. Use formato ISO 8601 (YYYY-MM-DD)"
                )
        
        # Criar importador
        importer = GarminHistoricalImporter(
            email=request.email,
            password=request.password
        )
        
        # Executar importação em background
        def run_import():
            try:
                result = importer.import_all_activities(start_date, end_date)
                logger.info(f"✅ Importação concluída: {result}")
            except Exception as e:
                logger.error(f"❌ Erro na importação em background: {e}")
        
        background_tasks.add_task(run_import)
        
        return {
            "status": "started",
            "message": "Importação iniciada em background",
            "note": "A importação pode demorar vários minutos. "
                   "Acompanhe os logs do servidor para ver o progresso.",
            "start_date": request.start_date or "2 anos atrás",
            "end_date": request.end_date or "hoje"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar importação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar importação: {str(e)}"
        )


@router.post("/import-from-garmin-sync")
async def import_historical_data_sync(request: ImportRequest):
    """
    Importar dados históricos do Garmin Connect (SÍNCRONO)
    
    **Atenção:** Este endpoint é SÍNCRONO e pode demorar vários minutos.
    Use apenas para pequenos períodos ou quando precisar do resultado imediato.
    
    Para grandes importações, use o endpoint /import-from-garmin (async).
    """
    if not GARMINCONNECT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Serviço de importação não disponível. "
                   "Instale: pip install garminconnect"
        )
    
    try:
        # Parse dates
        start_date = None
        end_date = None
        
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date)
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
        
        # Criar importador
        importer = GarminHistoricalImporter(
            email=request.email,
            password=request.password
        )
        
        # Executar importação
        result = importer.import_all_activities(start_date, end_date)
        
        if result['success']:
            return {
                "status": "completed",
                "message": "Importação concluída com sucesso",
                **result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Erro desconhecido na importação')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na importação: {str(e)}"
        )


@router.get("/import-status")
async def get_import_status():
    """
    Verificar status do serviço de importação
    """
    return {
        "service": "Garmin Historical Import",
        "available": GARMINCONNECT_AVAILABLE,
        "version": "1.0.0",
        "endpoints": {
            "async": "/historical/import-from-garmin",
            "sync": "/historical/import-from-garmin-sync",
            "status": "/historical/import-status"
        },
        "note": "Use o endpoint async para grandes importações (recomendado)" if GARMINCONNECT_AVAILABLE else 
                "Serviço não disponível. Instale: pip install garminconnect"
    }

