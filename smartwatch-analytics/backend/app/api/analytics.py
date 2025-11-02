#!/usr/bin/env python3
"""
Endpoints para Analytics Agregados
===================================

Fornece estatísticas, totais, progressão e insights agregados
de todas as atividades do usuário.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

from app.services.garmin_service import GarminService

router = APIRouter()

def get_garmin_service() -> GarminService:
    """Dependency para obter instância do serviço Garmin"""
    return GarminService()


@router.get("/summary")
async def get_activity_summary(
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Retorna resumo geral de todas as atividades processadas
    
    Similar ao que aparece na tela inicial do Garmin Connect:
    - Total de atividades
    - Distância total
    - Tempo total
    - Calorias totais
    - Média de pace, FC, etc.
    """
    try:
        activities = _load_all_processed_activities(garmin_service.activities_dir)
        
        if not activities:
            return {
                "message": "Nenhuma atividade processada ainda",
                "total_activities": 0
            }
        
        # Calcular agregados
        summary = _calculate_summary(activities)
        
        return {
            "total_activities": len(activities),
            "summary": summary,
            "period": {
                "first_activity": activities[-1].get("summary", {}).get("start_time"),
                "last_activity": activities[0].get("summary", {}).get("start_time"),
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-sport")
async def get_stats_by_sport(
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Estatísticas agrupadas por tipo de esporte
    """
    try:
        activities = _load_all_processed_activities(garmin_service.activities_dir)
        
        if not activities:
            return {"sports": {}}
        
        # Agrupar por esporte
        by_sport = defaultdict(list)
        for activity in activities:
            sport = activity.get("summary", {}).get("sport", "unknown")
            by_sport[sport].append(activity)
        
        # Calcular stats por esporte
        stats = {}
        for sport, sport_activities in by_sport.items():
            stats[sport] = _calculate_summary(sport_activities)
        
        return {"sports": stats}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def get_timeline(
    days: int = Query(30, description="Número de dias para análise"),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Timeline de atividades com progressão ao longo do tempo
    
    Retorna dados para gráficos de:
    - Distância por dia/semana/mês
    - Tempo de treino
    - Frequência de treinos
    """
    try:
        activities = _load_all_processed_activities(garmin_service.activities_dir)
        
        if not activities:
            return {"timeline": []}
        
        # Filtrar por período
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered = []
        
        for activity in activities:
            start_time_str = activity.get("summary", {}).get("start_time")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    if start_time.replace(tzinfo=None) >= cutoff_date:
                        filtered.append(activity)
                except:
                    continue
        
        # Agrupar por dia
        by_day = defaultdict(list)
        for activity in filtered:
            start_time_str = activity.get("summary", {}).get("start_time")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    day = start_time.date().isoformat()
                    by_day[day].append(activity)
                except:
                    continue
        
        # Criar timeline
        timeline = []
        for day, day_activities in sorted(by_day.items()):
            day_summary = _calculate_summary(day_activities)
            timeline.append({
                "date": day,
                "activities_count": len(day_activities),
                "total_distance_km": day_summary.get("total_distance_km", 0),
                "total_time_seconds": day_summary.get("total_time_seconds", 0),
                "total_calories": day_summary.get("total_calories", 0),
                "activities": [
                    {
                        "id": a.get("activity_id"),
                        "sport": a.get("summary", {}).get("sport"),
                        "distance_km": a.get("summary", {}).get("distance_km"),
                        "duration": a.get("summary", {}).get("duration_formatted"),
                    }
                    for a in day_activities
                ]
            })
        
        return {
            "period_days": days,
            "timeline": timeline,
            "total_days_with_activity": len(timeline),
            "total_activities": len(filtered)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records")
async def get_personal_records(
    sport: Optional[str] = Query(None, description="Filtrar por esporte"),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Recordes pessoais
    
    - Maior distância
    - Melhor pace
    - Mais calorias
    - FC mais alta
    - etc.
    """
    try:
        activities = _load_all_processed_activities(garmin_service.activities_dir)
        
        if not activities:
            return {"records": {}}
        
        # Filtrar por esporte se solicitado
        if sport:
            activities = [a for a in activities if a.get("summary", {}).get("sport") == sport]
        
        records = _calculate_records(activities)
        
        return {
            "sport": sport or "all",
            "records": records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_global_insights(
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Insights globais baseados em todo o histórico
    
    - Tendências
    - Padrões
    - Recomendações
    """
    try:
        activities = _load_all_processed_activities(garmin_service.activities_dir)
        
        if not activities:
            return {"insights": []}
        
        insights = _generate_global_insights(activities)
        
        return {
            "total_activities": len(activities),
            "insights": insights
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-all-history")
async def process_all_history(
    max_activities: int = Query(100, description="Máximo de atividades a processar"),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Processa todo o histórico de atividades localmente armazenadas
    
    Útil após fazer backfill ou baixar múltiplos arquivos FIT
    """
    try:
        activities_dir = garmin_service.activities_dir
        
        # Listar todos os arquivos FIT
        fit_files = [f for f in os.listdir(activities_dir) if f.endswith('.fit')]
        
        if not fit_files:
            return {
                "message": "Nenhum arquivo FIT encontrado",
                "processed": 0
            }
        
        # Limitar quantidade
        fit_files = fit_files[:max_activities]
        
        processed = []
        errors = []
        
        for fit_file in fit_files:
            try:
                fit_path = os.path.join(activities_dir, fit_file)
                activity_id = fit_file.replace('.fit', '')
                
                # Processar com Enhanced System
                activity_data = garmin_service.process_activity_fit(fit_path)
                
                if activity_data:
                    # Salvar dados processados
                    output_path = os.path.join(activities_dir, f"{activity_id}_processed.json")
                    with open(output_path, 'w') as f:
                        json.dump(activity_data, f, indent=2, default=str)
                    
                    processed.append({
                        "activity_id": activity_id,
                        "sport": activity_data.get("summary", {}).get("sport"),
                        "distance_km": activity_data.get("summary", {}).get("distance_km"),
                    })
                else:
                    errors.append({"file": fit_file, "error": "Failed to process"})
                    
            except Exception as e:
                errors.append({"file": fit_file, "error": str(e)})
        
        return {
            "message": f"Processadas {len(processed)} atividades",
            "total_fit_files": len(fit_files),
            "processed": len(processed),
            "errors": len(errors),
            "processed_activities": processed,
            "errors_detail": errors if errors else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

def _load_all_processed_activities(activities_dir: str) -> List[Dict[str, Any]]:
    """Carrega todas as atividades processadas"""
    activities = []
    
    if not os.path.exists(activities_dir):
        return activities
    
    # Procurar arquivos _processed.json
    for filename in os.listdir(activities_dir):
        if filename.endswith('_processed.json'):
            try:
                filepath = os.path.join(activities_dir, filename)
                with open(filepath, 'r') as f:
                    activity_data = json.load(f)
                    activities.append(activity_data)
            except Exception as e:
                continue
    
    # Ordenar por data (mais recente primeiro)
    activities.sort(
        key=lambda x: x.get("summary", {}).get("start_time", ""),
        reverse=True
    )
    
    return activities


def _calculate_summary(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula estatísticas agregadas"""
    if not activities:
        return {}
    
    total_distance = 0
    total_time = 0
    total_calories = 0
    hr_values = []
    pace_values = []
    
    for activity in activities:
        summary = activity.get("summary", {})
        metrics = activity.get("detailed_metrics", {})
        
        total_distance += summary.get("distance_meters", 0)
        total_time += summary.get("duration_seconds", 0)
        total_calories += summary.get("total_calories", 0)
        
        if summary.get("avg_heart_rate"):
            hr_values.append(summary.get("avg_heart_rate"))
        
        pace_speed = metrics.get("pace_speed", {})
        if pace_speed.get("avg_speed_kmh"):
            pace_values.append(pace_speed.get("avg_speed_kmh"))
    
    return {
        "total_activities": len(activities),
        "total_distance_km": round(total_distance / 1000, 2),
        "total_distance_miles": round(total_distance / 1609.34, 2),
        "total_time_seconds": total_time,
        "total_time_formatted": _format_duration(total_time),
        "total_calories": total_calories,
        "avg_heart_rate": round(sum(hr_values) / len(hr_values), 1) if hr_values else None,
        "avg_speed_kmh": round(sum(pace_values) / len(pace_values), 2) if pace_values else None,
        "avg_pace_min_per_km": _format_pace(1000 / (sum(pace_values) / len(pace_values) / 3.6)) if pace_values else None,
    }


def _calculate_records(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula recordes pessoais"""
    records = {
        "longest_distance": None,
        "longest_time": None,
        "fastest_pace": None,
        "most_calories": None,
        "highest_hr": None,
        "best_consistency": None,
    }
    
    for activity in activities:
        summary = activity.get("summary", {})
        metrics = activity.get("detailed_metrics", {})
        
        # Maior distância
        distance = summary.get("distance_km", 0)
        if not records["longest_distance"] or distance > records["longest_distance"]["value"]:
            records["longest_distance"] = {
                "value": distance,
                "unit": "km",
                "activity_id": activity.get("activity_id"),
                "date": summary.get("start_time"),
            }
        
        # Maior tempo
        duration = summary.get("duration_seconds", 0)
        if not records["longest_time"] or duration > records["longest_time"]["value"]:
            records["longest_time"] = {
                "value": duration,
                "value_formatted": summary.get("duration_formatted"),
                "activity_id": activity.get("activity_id"),
                "date": summary.get("start_time"),
            }
        
        # Pace mais rápido (menor valor)
        pace_kmh = metrics.get("pace_speed", {}).get("avg_speed_kmh", 0)
        if pace_kmh > 0:
            if not records["fastest_pace"] or pace_kmh > records["fastest_pace"]["value"]:
                records["fastest_pace"] = {
                    "value": pace_kmh,
                    "pace": summary.get("avg_pace_min_per_km"),
                    "activity_id": activity.get("activity_id"),
                    "date": summary.get("start_time"),
                }
        
        # Mais calorias
        calories = summary.get("total_calories", 0)
        if not records["most_calories"] or calories > records["most_calories"]["value"]:
            records["most_calories"] = {
                "value": calories,
                "activity_id": activity.get("activity_id"),
                "date": summary.get("start_time"),
            }
        
        # FC mais alta
        max_hr = summary.get("max_heart_rate", 0)
        if not records["highest_hr"] or max_hr > records["highest_hr"]["value"]:
            records["highest_hr"] = {
                "value": max_hr,
                "unit": "bpm",
                "activity_id": activity.get("activity_id"),
                "date": summary.get("start_time"),
            }
        
        # Melhor consistency
        consistency = metrics.get("pace_speed", {}).get("consistency_score", 0)
        if not records["best_consistency"] or consistency > records["best_consistency"]["value"]:
            records["best_consistency"] = {
                "value": consistency,
                "activity_id": activity.get("activity_id"),
                "date": summary.get("start_time"),
            }
    
    return records


def _generate_global_insights(activities: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Gera insights globais"""
    insights = []
    
    if len(activities) < 2:
        return insights
    
    # Insight: Total de atividades
    insights.append({
        "type": "info",
        "category": "volume",
        "message": f"Você completou {len(activities)} atividades registradas!"
    })
    
    # Insight: Distância total
    summary = _calculate_summary(activities)
    total_km = summary.get("total_distance_km", 0)
    if total_km > 100:
        insights.append({
            "type": "achievement",
            "category": "distance",
            "message": f"Já percorreu {total_km:.1f} km! Isso é como ir de São Paulo a {'Campinas' if total_km < 100 else 'Rio de Janeiro' if total_km < 500 else 'Curitiba'}!"
        })
    
    # Insight: Frequência
    days_with_activity = len(set([
        a.get("summary", {}).get("start_time", "")[:10]
        for a in activities
    ]))
    avg_per_week = (days_with_activity / (len(activities) / 7)) if len(activities) > 7 else 0
    if avg_per_week > 3:
        insights.append({
            "type": "positive",
            "category": "consistency",
            "message": f"Você treina em média {avg_per_week:.1f} dias por semana. Excelente consistência!"
        })
    
    # Insight: Progressão de pace
    if len(activities) >= 5:
        recent_5 = activities[:5]
        old_5 = activities[-5:]
        
        recent_speeds = [a.get("detailed_metrics", {}).get("pace_speed", {}).get("avg_speed_kmh", 0) for a in recent_5]
        old_speeds = [a.get("detailed_metrics", {}).get("pace_speed", {}).get("avg_speed_kmh", 0) for a in old_5]
        
        recent_speeds = [s for s in recent_speeds if s > 0]
        old_speeds = [s for s in old_speeds if s > 0]
        
        if recent_speeds and old_speeds:
            recent_avg = sum(recent_speeds) / len(recent_speeds)
            old_avg = sum(old_speeds) / len(old_speeds)
            
            improvement = ((recent_avg - old_avg) / old_avg) * 100
            
            if improvement > 5:
                insights.append({
                    "type": "achievement",
                    "category": "performance",
                    "message": f"Seu pace melhorou {improvement:.1f}% nas últimas atividades! 🚀"
                })
            elif improvement < -5:
                insights.append({
                    "type": "warning",
                    "category": "performance",
                    "message": f"Seu pace está {abs(improvement):.1f}% mais lento. Considere descansar ou revisar treinos."
                })
    
    return insights


def _format_duration(seconds: float) -> str:
    """Formata duração em HH:MM:SS"""
    if not seconds:
        return "00:00:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_pace(pace_minutes: float) -> str:
    """Formata pace em MM:SS"""
    minutes = int(pace_minutes)
    seconds = int((pace_minutes - minutes) * 60)
    return f"{minutes:02d}:{seconds:02d}"

