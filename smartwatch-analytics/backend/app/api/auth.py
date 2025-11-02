#!/usr/bin/env python3
"""
Endpoints para Autenticação OAuth 2.0 com Garmin Connect
"""

import logging
import secrets
import hashlib
import base64
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.config import settings
from app.services.garmin_service import temp_auth_storage

logger = logging.getLogger(__name__)
router = APIRouter()

# O armazenamento foi movido para garmin_service.py para ser centralizado
# temp_storage = {}

def generate_pkce_codes():
    """Gera o code_verifier e o code_challenge para o fluxo PKCE."""
    code_verifier = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(hashed).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

@router.get("/garmin/authorize")
async def authorize_garmin():
    """
    Inicia o fluxo de autorização OAuth 2.0 com a Garmin.
    Redireciona o usuário para a página de autorização da Garmin.
    """
    if not settings.GARMIN_CLIENT_ID or not settings.GARMIN_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GARMIN_CLIENT_ID não está configurado.")

    # Criando o cliente OAuth2 para a sessão
    client = AsyncOAuth2Client(
        client_id=settings.GARMIN_CLIENT_ID,
        client_secret=settings.GARMIN_CLIENT_SECRET,
        redirect_uri=settings.GARMIN_REDIRECT_URI,
        scope=settings.GARMIN_SCOPES,
        authorize_url=settings.GARMIN_AUTH_URL,
        access_token_url=settings.GARMIN_TOKEN_URL,
    )

    code_verifier, code_challenge = generate_pkce_codes()
    
    state = secrets.token_urlsafe(32)
    temp_auth_storage["state"] = state
    temp_auth_storage["code_verifier"] = code_verifier

    authorization_url, _ = client.create_authorization_url(
        settings.GARMIN_AUTH_URL,
        code_challenge=code_challenge,
        code_challenge_method="S256",
        state=state,
        # redirect_uri is already in the client
    )

    # Adicionando um print para depuração
    print("--- URL DE AUTORIZAÇÃO GERADA ---")
    print(authorization_url)
    print("---------------------------------")
    print(f"VERIFIQUE SE ESTA REDIRECT_URI: '{settings.GARMIN_REDIRECT_URI}' É IDÊNTICA À CONFIGURADA NO PORTAL DA GARMIN.")


    return RedirectResponse(url=authorization_url, status_code=302)

@router.get("/garmin/callback")
async def garmin_callback(request: Request):
    """
    Callback do fluxo OAuth 2.0. A Garmin redireciona para cá após a autorização.
    Troca o código de autorização por um access token.
    """
    code = request.query_params.get('code')
    if not code:
        logger.error("Callback recebido sem um 'code'. Query params: %s", request.query_params)
        raise HTTPException(
            status_code=400, 
            detail=f"Código de autorização não recebido. Query Params: {request.query_params}"
        )

    # O state retornado pela Garmin para verificação
    returned_state = request.query_params.get('state')
    original_state = temp_auth_storage.get('state')

    if not returned_state or returned_state != original_state:
        logger.error("State inválido. Recebido: %s, Esperado: %s", returned_state, original_state)
        raise HTTPException(status_code=400, detail="State CSRF inválido.")

    code_verifier = temp_auth_storage.get('code_verifier')
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Code verifier não encontrado. Inicie o fluxo novamente.")

    # Dados para a requisição do token
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.GARMIN_REDIRECT_URI,
        'client_id': settings.GARMIN_CLIENT_ID,
        'client_secret': settings.GARMIN_CLIENT_SECRET,
        'code_verifier': code_verifier
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.GARMIN_TOKEN_URL, data=token_data)
            response.raise_for_status()  # Lança exceção para status 4xx/5xx
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro ao obter token da Garmin: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro na API da Garmin: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão ao obter token da Garmin: {e}")
            raise HTTPException(status_code=500, detail="Erro de conexão com a API da Garmin.")

    token_data = response.json()
    
    # Armazena os tokens temporariamente
    # Em produção, salve-os de forma segura associados a um usuário
    temp_auth_storage['access_token'] = token_data.get('access_token')
    temp_auth_storage['refresh_token'] = token_data.get('refresh_token')
    temp_auth_storage['expires_in'] = token_data.get('expires_in')
    
    logger.info("Access token recebido e armazenado com sucesso.")
    
    # Limpa o code_verifier após o uso
    del temp_auth_storage['code_verifier']
    del temp_auth_storage['state']

    return {
        "status": "success",
        "message": "Autenticação com a Garmin realizada com sucesso!",
        "access_token": "********", # Não exponha o token diretamente
        "scope": token_data.get('scope')
    }

@router.get("/status")
async def auth_status():
    """Verifica o status da autenticação com a Garmin."""
    if temp_auth_storage.get('access_token'):
        return {
            "status": "authenticated",
            "message": "A aplicação está autenticada com a Garmin."
        }
    else:
        return {
            "status": "not_authenticated",
            "message": "A aplicação não está autenticada. Inicie o fluxo em /auth/garmin/authorize"
        } 