#!/usr/bin/env python3
"""
Endpoint para Inicializar Banco de Dados
========================================

Útil para executar o schema.sql uma vez após criar o banco.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import subprocess
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/init-database")
async def init_database():
    """
    Inicializa o banco de dados executando schema.sql
    
    ⚠️ ATENÇÃO: Execute apenas UMA VEZ após criar o banco!
    """
    try:
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'database',
            'schema.sql'
        )
        
        schema_path = os.path.abspath(schema_path)
        
        if not os.path.exists(schema_path):
            raise HTTPException(
                status_code=404,
                detail=f"Schema file not found: {schema_path}"
            )
        
        # Pegar DATABASE_URL do ambiente
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(
                status_code=500,
                detail="DATABASE_URL environment variable not set"
            )
        
        # Executar psql
        # Formato: postgresql://user:pass@host:port/dbname
        result = subprocess.run(
            ['psql', database_url, '-f', schema_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Database schema initialized successfully",
                "output": result.stdout
            }
        else:
            # Verificar se é erro de "already exists" (ok)
            if "already exists" in result.stderr.lower() or "duplicate" in result.stderr.lower():
                return {
                    "status": "warning",
                    "message": "Schema already initialized (tables may already exist)",
                    "output": result.stderr
                }
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize database: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Database initialization timed out"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="psql not found. Install PostgreSQL client tools."
        )
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/database-status")
async def database_status():
    """
    Verifica status da conexão com banco de dados
    """
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return {
                "status": "not_configured",
                "message": "DATABASE_URL not set"
            }
        
        # Tentar conectar
        result = subprocess.run(
            ['psql', database_url, '-c', 'SELECT version();'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return {
                "status": "connected",
                "message": "Database connection successful"
            }
        else:
            return {
                "status": "error",
                "message": f"Database connection failed: {result.stderr}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking database: {str(e)}"
        }

