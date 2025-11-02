#!/usr/bin/env python3
"""
Endpoints para consultar dados salvos no banco de dados
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging

from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/activities")
async def get_saved_activities(
    limit: int = Query(10, description="Número máximo de atividades"),
    offset: int = Query(0, description="Offset para paginação")
):
    """
    Lista atividades salvas no banco de dados
    """
    try:
        db_service = DatabaseService()
        
        if not db_service.pool:
            return {
                "status": "database_not_available",
                "message": "Database não disponível. Verifique DATABASE_URL e se psycopg2 está instalado.",
                "activities": []
            }
        
        from app.services.database_service import get_db_connection
        
        activities = []
        with get_db_connection() as conn:
            if not conn:
                return {
                    "status": "database_not_available",
                    "message": "Database não disponível",
                    "activities": []
                }
            
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id,
                    garmin_activity_id,
                    activity_name,
                    sport,
                    start_time,
                    duration_seconds,
                    distance_meters,
                    avg_heart_rate,
                    max_heart_rate,
                    total_calories,
                    created_at
                FROM activities
                ORDER BY start_time DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM activities")
            total = cur.fetchone()[0]
            
            for row in rows:
                activities.append({
                    "id": str(row[0]),
                    "garmin_activity_id": row[1],
                    "activity_name": row[2],
                    "sport": row[3],
                    "start_time": row[4].isoformat() if row[4] else None,
                    "duration_seconds": row[5],
                    "distance_meters": row[6],
                    "distance_km": round(row[6] / 1000.0, 2) if row[6] else None,
                    "avg_heart_rate": row[7],
                    "max_heart_rate": row[8],
                    "total_calories": row[9],
                    "created_at": row[10].isoformat() if row[10] else None
                })
        
        return {
            "status": "success",
            "total": total,
            "returned": len(activities),
            "limit": limit,
            "offset": offset,
            "activities": activities
        }
        
    except Exception as e:
        logger.error(f"Erro ao consultar atividades: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities/stats")
async def get_activities_stats():
    """
    Estatísticas das atividades salvas
    """
    try:
        db_service = DatabaseService()
        
        if not db_service.pool:
            return {
                "status": "database_not_available",
                "message": "Database não disponível"
            }
        
        from app.services.database_service import get_db_connection
        
        with get_db_connection() as conn:
            if not conn:
                return {"status": "database_not_available"}
            
            cur = conn.cursor()
            
            # Total de atividades
            cur.execute("SELECT COUNT(*) FROM activities")
            total = cur.fetchone()[0]
            
            # Por esporte
            cur.execute("""
                SELECT sport, COUNT(*) 
                FROM activities 
                GROUP BY sport 
                ORDER BY COUNT(*) DESC
            """)
            by_sport = {row[0]: row[1] for row in cur.fetchall()}
            
            # Data mais antiga e mais recente
            cur.execute("""
                SELECT 
                    MIN(start_time) as oldest,
                    MAX(start_time) as newest
                FROM activities
                WHERE start_time IS NOT NULL
            """)
            dates = cur.fetchone()
            oldest = dates[0].isoformat() if dates and dates[0] else None
            newest = dates[1].isoformat() if dates and dates[1] else None
            
            # Total de distância
            cur.execute("SELECT SUM(distance_meters) FROM activities WHERE distance_meters IS NOT NULL")
            total_distance = cur.fetchone()[0] or 0
            
            return {
                    "status": "success",
                    "total_activities": total,
                    "by_sport": by_sport,
                    "oldest_activity": oldest,
                    "newest_activity": newest,
                "total_distance_km": round(total_distance / 1000.0, 2),
                "total_distance_miles": round(total_distance / 1609.34, 2)
            }
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_users():
    """
    Lista usuários salvos no banco
    """
    try:
        db_service = DatabaseService()
        
        if not db_service.pool:
            return {
                "status": "database_not_available",
                "users": []
            }
        
        from app.services.database_service import get_db_connection
        
        users = []
        with get_db_connection() as conn:
            if not conn:
                return {"status": "database_not_available", "users": []}
            
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id,
                    garmin_user_id,
                    email,
                    name,
                    created_at,
                    last_sync_at
                FROM users
                ORDER BY created_at DESC
            """)
            
            rows = cur.fetchall()
            for row in rows:
                users.append({
                    "id": str(row[0]),
                    "garmin_user_id": row[1],
                    "email": row[2],
                    "name": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "last_sync_at": row[5].isoformat() if row[5] else None
                })
        
        return {
            "status": "success",
            "count": len(users),
            "users": users
        }
        
    except Exception as e:
        logger.error(f"Erro ao consultar usuários: {e}")
        raise HTTPException(status_code=500, detail=str(e))

