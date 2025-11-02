#!/usr/bin/env python3
"""
Endpoints para dados de Mapa (GPS)
===================================

Fornece dados geográficos em formato GeoJSON para renderizar
mapas das atividades (como Garmin Connect).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import json
import os

from app.services.garmin_service import GarminService

router = APIRouter()

def get_garmin_service() -> GarminService:
    """Dependency para obter instância do serviço Garmin"""
    return GarminService()


@router.get("/{activity_id}/geojson")
async def get_activity_geojson(
    activity_id: str,
    simplified: bool = Query(False, description="Simplificar rota para melhor performance"),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Retorna dados GPS da atividade em formato GeoJSON
    
    Formato padrão para mapas web (Leaflet, Mapbox, Google Maps, etc.)
    
    Args:
        activity_id: ID da atividade
        simplified: Se True, reduz número de pontos para melhor performance
    
    Returns:
        GeoJSON Feature Collection com LineString da rota
    """
    try:
        # Carregar dados processados
        activities_dir = garmin_service.activities_dir
        enhanced_file = os.path.join(activities_dir, f"{activity_id}_enhanced_data.json")
        
        if not os.path.exists(enhanced_file):
            raise HTTPException(
                status_code=404,
                detail=f"Atividade {activity_id} não encontrada. Processe primeiro."
            )
        
        with open(enhanced_file, 'r') as f:
            data = json.load(f)
        
        records = data.get('records', [])
        
        if not records:
            raise HTTPException(
                status_code=404,
                detail="Atividade não tem dados GPS"
            )
        
        # Extrair coordenadas
        coordinates = []
        for record in records:
            lat = record.get('position_lat')
            long = record.get('position_long')
            
            if lat and long:
                # Converter de semicircles para graus
                lat_deg = lat * (180 / 2**31)
                long_deg = long * (180 / 2**31)
                
                # GeoJSON usa [longitude, latitude] (invertido!)
                coordinates.append([long_deg, lat_deg])
        
        # Simplificar se solicitado
        if simplified and len(coordinates) > 100:
            # Pegar 1 a cada N pontos
            step = max(1, len(coordinates) // 100)
            coordinates = coordinates[::step]
        
        # Criar GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates
                    },
                    "properties": {
                        "activity_id": activity_id,
                        "sport": data.get('sessions', [{}])[0].get('sport'),
                        "start_time": data.get('sessions', [{}])[0].get('start_time'),
                        "distance_km": data.get('sessions', [{}])[0].get('total_distance', 0) / 1000,
                        "total_points": len(coordinates),
                        "simplified": simplified
                    }
                }
            ]
        }
        
        return geojson
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{activity_id}/gps-points")
async def get_activity_gps_points(
    activity_id: str,
    include_metrics: bool = Query(True, description="Incluir FC, velocidade, etc."),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Retorna todos os pontos GPS da atividade com métricas
    
    Útil para:
    - Renderizar mapa com gradiente de velocidade/FC
    - Heatmaps
    - Análise detalhada de pontos
    """
    try:
        # Carregar dados
        activities_dir = garmin_service.activities_dir
        enhanced_file = os.path.join(activities_dir, f"{activity_id}_enhanced_data.json")
        
        if not os.path.exists(enhanced_file):
            raise HTTPException(
                status_code=404,
                detail=f"Atividade {activity_id} não encontrada"
            )
        
        with open(enhanced_file, 'r') as f:
            data = json.load(f)
        
        records = data.get('records', [])
        
        # Processar pontos
        points = []
        for i, record in enumerate(records):
            lat = record.get('position_lat')
            long = record.get('position_long')
            
            if lat and long:
                # Converter coordenadas
                lat_deg = lat * (180 / 2**31)
                long_deg = long * (180 / 2**31)
                
                point = {
                    "index": i,
                    "timestamp": record.get('timestamp'),
                    "latitude": lat_deg,
                    "longitude": long_deg,
                }
                
                if include_metrics:
                    point.update({
                        "distance": record.get('distance'),
                        "speed": record.get('enhanced_speed') or record.get('speed'),
                        "altitude": record.get('enhanced_altitude') or record.get('altitude'),
                        "heart_rate": record.get('heart_rate'),
                        "cadence": record.get('cadence'),
                        "power": record.get('power'),
                    })
                
                points.append(point)
        
        return {
            "activity_id": activity_id,
            "total_points": len(points),
            "has_gps": len(points) > 0,
            "points": points
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{activity_id}/heatmap-data")
async def get_activity_heatmap_data(
    activity_id: str,
    metric: str = Query("speed", description="Métrica para heatmap: speed, heart_rate, altitude, cadence"),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Retorna dados formatados para criar heatmap de métricas
    
    Exemplo: Mapa com cores por velocidade (azul=lento, vermelho=rápido)
    """
    try:
        # Carregar dados
        activities_dir = garmin_service.activities_dir
        enhanced_file = os.path.join(activities_dir, f"{activity_id}_enhanced_data.json")
        
        if not os.path.exists(enhanced_file):
            raise HTTPException(status_code=404, detail="Atividade não encontrada")
        
        with open(enhanced_file, 'r') as f:
            data = json.load(f)
        
        records = data.get('records', [])
        
        # Mapear nome da métrica para campo
        metric_field_map = {
            "speed": "enhanced_speed",
            "heart_rate": "heart_rate",
            "altitude": "enhanced_altitude",
            "cadence": "cadence",
            "power": "power"
        }
        
        field = metric_field_map.get(metric, "enhanced_speed")
        
        # Coletar valores
        values = []
        for record in records:
            if record.get('position_lat') and record.get(field):
                values.append(record.get(field))
        
        if not values:
            raise HTTPException(status_code=404, detail=f"Métrica {metric} não disponível")
        
        # Calcular min/max para normalização
        min_value = min(values)
        max_value = max(values)
        
        # Criar pontos com valor normalizado (0-1)
        heatmap_points = []
        for record in records:
            lat = record.get('position_lat')
            long = record.get('position_long')
            value = record.get(field)
            
            if lat and long and value is not None:
                lat_deg = lat * (180 / 2**31)
                long_deg = long * (180 / 2**31)
                
                # Normalizar valor (0-1)
                normalized = (value - min_value) / (max_value - min_value) if max_value > min_value else 0.5
                
                heatmap_points.append({
                    "latitude": lat_deg,
                    "longitude": long_deg,
                    "value": value,
                    "normalized": round(normalized, 3),
                    "timestamp": record.get('timestamp')
                })
        
        return {
            "activity_id": activity_id,
            "metric": metric,
            "unit": _get_metric_unit(metric),
            "total_points": len(heatmap_points),
            "min_value": min_value,
            "max_value": max_value,
            "points": heatmap_points
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/route-comparison")
async def compare_routes(
    activity_ids: List[str] = Query(..., description="IDs das atividades para comparar"),
    garmin_service: GarminService = Depends(get_garmin_service)
):
    """
    Compara rotas de múltiplas atividades
    
    Útil para:
    - Ver todas as corridas/pedaladas na mesma região
    - Comparar performance em mesma rota
    """
    try:
        routes = []
        
        for activity_id in activity_ids[:10]:  # Limitar a 10
            try:
                activities_dir = garmin_service.activities_dir
                enhanced_file = os.path.join(activities_dir, f"{activity_id}_enhanced_data.json")
                
                if not os.path.exists(enhanced_file):
                    continue
                
                with open(enhanced_file, 'r') as f:
                    data = json.load(f)
                
                records = data.get('records', [])
                coordinates = []
                
                for record in records:
                    lat = record.get('position_lat')
                    long = record.get('position_long')
                    
                    if lat and long:
                        lat_deg = lat * (180 / 2**31)
                        long_deg = long * (180 / 2**31)
                        coordinates.append([long_deg, lat_deg])
                
                if coordinates:
                    session = data.get('sessions', [{}])[0]
                    routes.append({
                        "activity_id": activity_id,
                        "coordinates": coordinates,
                        "sport": session.get('sport'),
                        "start_time": session.get('start_time'),
                        "distance_km": session.get('total_distance', 0) / 1000,
                        "avg_speed_ms": session.get('enhanced_avg_speed') or session.get('avg_speed'),
                        "total_points": len(coordinates)
                    })
            except:
                continue
        
        # Criar GeoJSON com múltiplas rotas
        features = []
        for route in routes:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": route["coordinates"]
                },
                "properties": {
                    "activity_id": route["activity_id"],
                    "sport": route["sport"],
                    "start_time": route["start_time"],
                    "distance_km": route["distance_km"],
                    "avg_speed_kmh": route["avg_speed_ms"] * 3.6 if route["avg_speed_ms"] else None
                }
            })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return {
            "total_routes": len(routes),
            "geojson": geojson,
            "routes_summary": [
                {
                    "activity_id": r["activity_id"],
                    "sport": r["sport"],
                    "distance_km": r["distance_km"],
                    "start_time": r["start_time"]
                }
                for r in routes
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_metric_unit(metric: str) -> str:
    """Retorna unidade da métrica"""
    units = {
        "speed": "m/s",
        "heart_rate": "bpm",
        "altitude": "m",
        "cadence": "spm",
        "power": "W"
    }
    return units.get(metric, "")

