#!/usr/bin/env python3
"""
Serviço de Backfill Histórico Completo
========================================

⚠️ IMPORTANTE - Rate Limiting da Garmin:
- Free tier: 100 requisições/minuto
- Garmin recomenda: NÃO fazer polling, apenas receber via webhooks
- Se usuário não sincronizar por dias, Garmin faz PUSH automático via webhooks
- Após backfill inicial, dados virão automaticamente via webhooks

Este serviço faz backfill inicial com delays conservadores para evitar rate limit.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class HistoricalBackfillService:
    """Serviço para fazer backfill completo do histórico de dados"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    async def backfill_complete_activity_history(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Faz backfill completo do histórico de atividades
        
        Args:
            start_date: Data inicial (padrão: 5 anos atrás)
            end_date: Data final (padrão: hoje)
        
        Returns:
            Dict com estatísticas do backfill
        """
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        if not start_date:
            # Por padrão, buscar 2 anos de histórico (reduzido de 5 para evitar rate limit)
            # Após backfill inicial, dados futuros virão automaticamente via webhooks
            start_date = end_date - timedelta(days=2*365)
        
        # Limite da API: 30 dias por requisição
        chunk_days = 30
        
        requests_made = []
        current_start = start_date
        
        logger.info(f"Iniciando backfill de atividades de {start_date.date()} a {end_date.date()}")
        logger.info("⚠️ Usando delays conservadores (10s) para respeitar rate limit da Garmin (100 req/min)")
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)
            
            success = await self._request_activity_backfill_chunk(current_start, current_end)
            
            requests_made.append({
                "start": current_start.isoformat(),
                "end": current_end.isoformat(),
                "success": success
            })
            
            # Avançar para o próximo chunk
            current_start = current_end
            
            # Rate limit: aguardar 10 segundos entre requisições para evitar 429
            # Free tier: 100 req/min = mínimo 0.6s entre requisições
            # Usando 10s para ser muito conservador (máximo 6 req/min)
            # Garmin recomenda não fazer polling excessivo - dados virão via webhooks
            await asyncio.sleep(10)
        
        total_requests = len(requests_made)
        successful = sum(1 for r in requests_made if r["success"])
        
        return {
            "type": "activities",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_requests": total_requests,
            "successful_requests": successful,
            "failed_requests": total_requests - successful,
            "requests_detail": requests_made,
            "message": f"Backfill de atividades iniciado. {successful}/{total_requests} requisições aceitas."
        }
    
    async def backfill_complete_health_history(
        self,
        summary_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Faz backfill completo do histórico de dados de saúde
        
        Args:
            summary_type: Tipo de summary (dailies, epochs, sleeps, stressDetails, etc.)
            start_date: Data inicial (padrão: 2 anos atrás)
            end_date: Data final (padrão: hoje)
        
        Returns:
            Dict com estatísticas do backfill
        """
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        if not start_date:
            # Por padrão, buscar 1 ano de histórico (reduzido para evitar rate limit)
            # Após backfill inicial, dados futuros virão automaticamente via webhooks
            start_date = end_date - timedelta(days=1*365)
        
        # Limite da API: 90 dias por requisição
        chunk_days = 90
        
        requests_made = []
        current_start = start_date
        
        logger.info(f"Iniciando backfill de {summary_type} de {start_date.date()} a {end_date.date()}")
        logger.info("⚠️ Usando delays conservadores (10s) para respeitar rate limit da Garmin")
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)
            
            success = await self._request_health_backfill_chunk(
                summary_type, current_start, current_end
            )
            
            requests_made.append({
                "start": current_start.isoformat(),
                "end": current_end.isoformat(),
                "success": success
            })
            
            # Avançar para o próximo chunk
            current_start = current_end
            
            # Rate limit: aguardar 10 segundos entre requisições para evitar 429
            # Free tier: 100 req/min = mínimo 0.6s entre requisições
            # Usando 10s para ser muito conservador (máximo 6 req/min)
            # Health API tem rate limit mais restritivo - Garmin envia dados via webhooks
            await asyncio.sleep(10)
        
        total_requests = len(requests_made)
        successful = sum(1 for r in requests_made if r["success"])
        
        return {
            "type": summary_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_requests": total_requests,
            "successful_requests": successful,
            "failed_requests": total_requests - successful,
            "requests_detail": requests_made,
            "message": f"Backfill de {summary_type} iniciado. {successful}/{total_requests} requisições aceitas."
        }
    
    async def backfill_all_health_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Faz backfill completo de TODOS os tipos de dados de saúde
        
        Tipos suportados:
        - dailies
        - epochs
        - sleeps
        - stressDetails
        - bodyComps
        - userMetrics
        - pulseOx
        - respiration
        - healthSnapshot
        - hrv
        - bloodPressures
        - skinTemp
        """
        health_summary_types = [
            "dailies",
            "epochs",
            "sleeps",
            "stressDetails",
            "bodyComps",
            "userMetrics",
            "pulseOx",
            "respiration",
            "healthSnapshot",
            "hrv",
            "bloodPressures",
            "skinTemp"
        ]
        
        results = {}
        
        for summary_type in health_summary_types:
            try:
                result = await self.backfill_complete_health_history(
                    summary_type, start_date, end_date
                )
                results[summary_type] = result
                
                # Aguardar entre diferentes tipos para evitar rate limit
                # Health API tem rate limit mais restritivo - usar 20s entre tipos
                # São 12 tipos diferentes, então precisa ser muito conservador
                # Garmin recomenda: não fazer polling - dados virão via webhooks automaticamente
                await asyncio.sleep(20)
                
            except Exception as e:
                logger.error(f"Erro ao fazer backfill de {summary_type}: {e}")
                results[summary_type] = {
                    "error": str(e),
                    "success": False
                }
        
        return {
            "status": "completed",
            "summary_types": results,
            "total_types": len(health_summary_types),
            "successful_types": sum(1 for r in results.values() if r.get("successful_requests", 0) > 0)
        }
    
    async def _request_activity_backfill_chunk(
        self,
        start_date: datetime,
        end_date: datetime,
        max_retries: int = 3
    ) -> bool:
        """Faz uma requisição de backfill de atividades para um período de 30 dias"""
        backfill_url = f"{settings.GARMIN_ACTIVITY_API_URL}/backfill/activities"
        params = {
            "summaryStartTimeInSeconds": int(start_date.timestamp()),
            "summaryEndTimeInSeconds": int(end_date.timestamp())
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Solicitando backfill de atividades: {start_date.date()} a {end_date.date()}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        backfill_url,
                        headers=self.headers,
                        params=params,
                        timeout=30.0
                    )
                    
                    if response.status_code == 202:
                        logger.info(f"✅ Backfill aceito: {start_date.date()} a {end_date.date()}")
                        return True
                    elif response.status_code == 409:
                        logger.warning(f"⚠️ Backfill duplicado (já foi solicitado): {start_date.date()} a {end_date.date()}")
                        return True  # Consideramos sucesso pois o backfill já foi feito
                    elif response.status_code == 429:
                        # Rate limit - aguardar e tentar novamente
                        wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                        logger.warning(f"⏳ Rate limit atingido. Aguardando {wait_time}s antes de tentar novamente (tentativa {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Erro no backfill: {response.status_code} - {response.text}")
                        if attempt == max_retries - 1:
                            return False
                        await asyncio.sleep(2)
                        continue
                        
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = (2 ** attempt) * 5
                    logger.warning(f"⏳ Rate limit (HTTP). Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Erro HTTP ao solicitar backfill: {e.response.status_code} - {e.response.text}")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Exceção ao solicitar backfill: {e}")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(2)
        
        return False
    
    async def _request_health_backfill_chunk(
        self,
        summary_type: str,
        start_date: datetime,
        end_date: datetime,
        max_retries: int = 3
    ) -> bool:
        """Faz uma requisição de backfill de health data para um período de 90 dias"""
        backfill_url = f"https://apis.garmin.com/wellness-api/rest/backfill/{summary_type}"
        params = {
            "summaryStartTimeInSeconds": int(start_date.timestamp()),
            "summaryEndTimeInSeconds": int(end_date.timestamp())
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Solicitando backfill de {summary_type}: {start_date.date()} a {end_date.date()}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        backfill_url,
                        headers=self.headers,
                        params=params,
                        timeout=30.0
                    )
                    
                    if response.status_code == 202:
                        logger.info(f"✅ Backfill de {summary_type} aceito: {start_date.date()} a {end_date.date()}")
                        return True
                    elif response.status_code == 409:
                        logger.warning(f"⚠️ Backfill duplicado de {summary_type}: {start_date.date()} a {end_date.date()}")
                        return True
                    elif response.status_code == 429:
                        # Rate limit - aguardar e tentar novamente
                        wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                        logger.warning(f"⏳ Rate limit atingido para {summary_type}. Aguardando {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Erro no backfill de {summary_type}: {response.status_code} - {response.text}")
                        if attempt == max_retries - 1:
                            return False
                        await asyncio.sleep(2)
                        continue
                        
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = (2 ** attempt) * 5
                    logger.warning(f"⏳ Rate limit (HTTP) para {summary_type}. Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Erro HTTP ao solicitar backfill de {summary_type}: {e.response.status_code} - {e.response.text}")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Exceção ao solicitar backfill de {summary_type}: {e}")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(2)
        
        return False

