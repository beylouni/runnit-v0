#!/usr/bin/env python3
"""
Garmin FIT Workout Creator
==========================

Este módulo fornece funcionalidades para criar arquivos .FIT de treinos de corrida
que podem ser enviados para a Training API da Garmin.

Funcionalidades:
- criar_treino_fit(): Cria arquivos .FIT de treino a partir de estruturas simples
- testar_arquivo_fit(): Valida arquivos .FIT usando o SDK oficial da Garmin
- ler_atividade_fit(): Lê arquivos .FIT de atividades concluídas

Uso:
    from garmin_fit_workout_creator import criar_treino_fit
    
    treino = {
        "nome_do_treino": "Meu Treino 5k",
        "passos": [
            {"tipo": "aquecimento", "duracao_tipo": "tempo", "duracao_valor": 600},
            {"tipo": "corrida", "duracao_tipo": "distancia", "duracao_valor": 5000},
            {"tipo": "desaquecimento", "duracao_tipo": "tempo", "duracao_valor": 300}
        ]
    }
    
    sucesso = criar_treino_fit(treino, "meu_treino.fit")
"""

import os
import datetime
from typing import Dict, List, Any, Optional

# Importações da biblioteca fit_tool
from fit_tool.fit_file import FitFile
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.workout_message import WorkoutMessage
from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
from fit_tool.profile.profile_type import Sport, Intensity, WorkoutStepDuration, WorkoutStepTarget, Manufacturer, FileType

def criar_treino_fit(estrutura_treino: Dict[str, Any], nome_do_arquivo: str = "treino.fit") -> bool:
    """
    Cria um arquivo .FIT de treino a partir de uma estrutura de dados simples.
    
    Esta função é ideal para o fluxo PUSH - criar treinos personalizados que serão
    enviados para o calendário Garmin Connect dos usuários.
    
    Args:
        estrutura_treino: Dicionário com a estrutura do treino
            {
                "nome_do_treino": "Nome do treino",
                "passos": [
                    {
                        "tipo": "aquecimento|corrida|desaquecimento",
                        "duracao_tipo": "tempo|distancia",
                        "duracao_valor": valor_numerico,
                        "nome_passo": "Nome do passo (opcional)"
                    }
                ]
            }
        nome_do_arquivo: Nome do arquivo .FIT a ser criado
    
    Returns:
        bool: True se o arquivo foi criado com sucesso, False caso contrário
    
    Example:
        >>> treino = {
        ...     "nome_do_treino": "Treino Intervalado 5k",
        ...     "passos": [
        ...         {"tipo": "aquecimento", "duracao_tipo": "tempo", "duracao_valor": 600},
        ...         {"tipo": "corrida", "duracao_tipo": "distancia", "duracao_valor": 5000},
        ...         {"tipo": "desaquecimento", "duracao_tipo": "tempo", "duracao_valor": 300}
        ...     ]
        ... }
        >>> criar_treino_fit(treino, "meu_treino.fit")
        True
    """
    try:
        print(f"🏃 Criando arquivo de treino: {nome_do_arquivo}")
        
        # Mapeamento de tipos de treino para as constantes da biblioteca
        tipo_mapping = {
            "aquecimento": Intensity.WARMUP,
            "corrida": Intensity.ACTIVE,
            "desaquecimento": Intensity.COOLDOWN,
            "warmup": Intensity.WARMUP,
            "active": Intensity.ACTIVE,
            "cooldown": Intensity.COOLDOWN
        }
        
        duracao_mapping = {
            "tempo": WorkoutStepDuration.TIME,
            "distancia": WorkoutStepDuration.DISTANCE,
            "time": WorkoutStepDuration.TIME,
            "distance": WorkoutStepDuration.DISTANCE
        }
        
        # Criar o builder
        builder = FitFileBuilder(auto_define=True, min_string_size=30)
        
        # Mensagem File ID (obrigatória)
        msg_file_id = FileIdMessage()
        msg_file_id.type = FileType.WORKOUT
        msg_file_id.manufacturer = Manufacturer.DEVELOPMENT.value
        msg_file_id.product = 0
        # TODO: Adicionar time_created quando resolver o problema do timestamp
        msg_file_id.serial_number = 0x12345678
        builder.add(msg_file_id)
        
        # Mensagem Workout
        msg_workout = WorkoutMessage()
        msg_workout.sport = Sport.RUNNING
        msg_workout.workout_name = estrutura_treino.get("nome_do_treino", "Treino de Corrida")
        msg_workout.num_valid_steps = len(estrutura_treino.get("passos", []))
        builder.add(msg_workout)
        
        # Adicionar passos do treino
        for i, passo in enumerate(estrutura_treino.get("passos", [])):
            msg_step = WorkoutStepMessage()
            msg_step.message_index = i
            msg_step.workout_step_name = passo.get("nome_passo", f"Passo {i+1}")
            
            # Mapear tipo de intensidade
            tipo_str = passo.get("tipo", "corrida").lower()
            msg_step.intensity = tipo_mapping.get(tipo_str, Intensity.ACTIVE)
            
            # Mapear tipo de duração
            duracao_tipo_str = passo.get("duracao_tipo", "tempo").lower()
            msg_step.duration_type = duracao_mapping.get(duracao_tipo_str, WorkoutStepDuration.TIME)
            
            # Definir valor da duração
            duracao_valor = passo.get("duracao_valor", 0)
            if duracao_tipo_str in ["tempo", "time"]:
                duration_time_ms = int(duracao_valor * 1000)  # Converter segundos para milissegundos
                msg_step.duration_time = duration_time_ms
            elif duracao_tipo_str in ["distancia", "distance"]:
                duration_distance_cm = int(duracao_valor / 10)  # Compensar multiplicação automática do fit_tool
                msg_step.duration_distance = duration_distance_cm
            
            # Definir tipo de target (aberto por padrão)
            msg_step.target_type = WorkoutStepTarget.OPEN
            
            builder.add(msg_step)
            print(f"✅ Passo {i+1}: {msg_step.workout_step_name}")
        
        # Construir e salvar o arquivo
        fit_file = builder.build()
        fit_file.to_file(nome_do_arquivo)
        
        tamanho_arquivo = os.path.getsize(nome_do_arquivo)
        print(f"✅ Arquivo '{nome_do_arquivo}' criado com sucesso! ({tamanho_arquivo} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo FIT: {e}")
        return False

def testar_arquivo_fit(nome_do_arquivo: str) -> bool:
    """
    Testa se o arquivo FIT criado é válido usando o SDK oficial da Garmin.
    
    Args:
        nome_do_arquivo: Nome do arquivo .FIT a ser testado
    
    Returns:
        bool: True se o arquivo é válido, False caso contrário
    """
    try:
        from garmin_fit_sdk import Decoder, Stream
        
        stream = Stream.from_file(nome_do_arquivo)
        decoder = Decoder(stream)
        
        if not decoder.is_fit():
            print("❌ O arquivo não é um arquivo FIT válido")
            return False
            
        if not decoder.check_integrity():
            print("❌ O arquivo não passou na verificação de integridade")
            return False
            
        messages, errors = decoder.read()
        
        if errors:
            print(f"⚠️  Avisos durante a leitura: {errors}")
        
        print("✅ Arquivo FIT válido e legível!")
        print(f"📊 Mensagens encontradas: {len(messages)} tipos")
        
        for message_type, message_list in messages.items():
            print(f"  - {message_type}: {len(message_list)} mensagens")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar arquivo: {e}")
        return False

def ler_atividade_fit(caminho_do_arquivo: str) -> Optional[Dict[str, Any]]:
    """
    Lê um arquivo .FIT de uma atividade concluída e extrai dados de resumo.
    
    Esta função é ideal para o fluxo PULL - ler dados de atividades que foram
    sincronizadas do relógio Garmin do usuário.
    
    Args:
        caminho_do_arquivo: Caminho para o arquivo .FIT da atividade
    
    Returns:
        Dict com dados da atividade ou None se houver erro
    """
    try:
        from garmin_fit_sdk import Decoder, Stream
        
        print(f"📖 Lendo arquivo de atividade: {caminho_do_arquivo}")
        
        stream = Stream.from_file(caminho_do_arquivo)
        decoder = Decoder(stream)
        
        if not decoder.is_fit():
            print("❌ O arquivo não é um arquivo FIT válido")
            return None
            
        messages, errors = decoder.read()
        
        if errors:
            print(f"⚠️  Avisos durante a leitura: {errors}")
        
        # Extrair dados da sessão (se houver)
        session_data = {}
        if 'session_mesgs' in messages and messages['session_mesgs']:
            session = messages['session_mesgs'][0]
            session_data = {
                'sport': session.get('sport', 'unknown'),
                'start_time': session.get('start_time', None),
                'total_distance': session.get('total_distance', 0),
                'total_elapsed_time': session.get('total_elapsed_time', 0),
                'avg_speed': session.get('avg_speed', 0),
                'avg_heart_rate': session.get('avg_heart_rate', 0),
                'max_heart_rate': session.get('max_heart_rate', 0),
                'total_calories': session.get('total_calories', 0)
            }
        
        # Extrair dados dos records (pontos GPS, etc.)
        record_data = []
        if 'record_mesgs' in messages:
            for record in messages['record_mesgs']:
                record_data.append({
                    'timestamp': record.get('timestamp', None),
                    'position_lat': record.get('position_lat', None),
                    'position_long': record.get('position_long', None),
                    'distance': record.get('distance', None),
                    'speed': record.get('speed', None),
                    'heart_rate': record.get('heart_rate', None)
                })
        
        resultado = {
            'session': session_data,
            'records': record_data,
            'total_records': len(record_data)
        }
        
        print(f"✅ Atividade lida com sucesso! {len(record_data)} pontos de dados")
        return resultado
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo de atividade: {e}")
        return None

def ler_treino_fit(caminho_do_arquivo: str) -> Optional[Dict[str, Any]]:
    """
    Lê um arquivo .FIT de treino e extrai informações dos passos do treino.
    
    Esta função é específica para arquivos de treino (workout), não de atividade.
    
    Args:
        caminho_do_arquivo: Caminho para o arquivo .FIT do treino
    
    Returns:
        Dict com dados do treino ou None se houver erro
    """
    try:
        from garmin_fit_sdk import Decoder, Stream
        
        print(f"📖 Lendo arquivo de treino: {caminho_do_arquivo}")
        
        stream = Stream.from_file(caminho_do_arquivo)
        decoder = Decoder(stream)
        
        if not decoder.is_fit():
            print("❌ O arquivo não é um arquivo FIT válido")
            return None
            
        messages, errors = decoder.read()
        
        if errors:
            print(f"⚠️  Avisos durante a leitura: {errors}")
        
        resultado = {
            'workout': {},
            'workout_steps': [],
            'file_info': {}
        }
        
        # Extrair informações do arquivo
        if 'file_id_mesgs' in messages and messages['file_id_mesgs']:
            file_info = messages['file_id_mesgs'][0]
            resultado['file_info'] = {
                'type': file_info.get('type', 'unknown'),
                'manufacturer': file_info.get('manufacturer', 'unknown'),
                'product': file_info.get('product', 0),
                'time_created': file_info.get('time_created', None)
            }
        
        # Extrair informações do workout
        if 'workout_mesgs' in messages and messages['workout_mesgs']:
            workout = messages['workout_mesgs'][0]
            resultado['workout'] = {
                'sport': workout.get('sport', 'unknown'),
                'workout_name': workout.get('wkt_name', ''),  # Campo correto
                'num_valid_steps': workout.get('num_valid_steps', 0),
                'capabilities': workout.get('capabilities', 0)
            }
        
        # Extrair informações dos passos do workout
        if 'workout_step_mesgs' in messages:
            for step in messages['workout_step_mesgs']:
                step_info = {
                    'message_index': step.get('message_index', 0),
                    'workout_step_name': step.get('wkt_step_name', ''),  # Campo correto
                    'intensity': step.get('intensity', 'unknown'),
                    'duration_type': step.get('duration_type', 'unknown'),
                    'target_type': step.get('target_type', 'unknown')
                }
                
                # Adicionar valores específicos de duração
                if step.get('duration_type') == 'time':
                    step_info['duration_time'] = step.get('duration_time', 0)  # Já está em segundos
                elif step.get('duration_type') == 'distance':
                    step_info['duration_distance'] = step.get('duration_distance', 0)  # Já está em metros
                
                resultado['workout_steps'].append(step_info)
        
        print(f"✅ Treino lido com sucesso! {len(resultado['workout_steps'])} passos encontrados")
        return resultado
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo de treino: {e}")
        return None

# Exemplo de uso e testes
if __name__ == "__main__":
    print("🏃 Garmin FIT Workout Creator - Teste")
    print("=" * 50)
    
    # Exemplo de estrutura de treino
    treino_exemplo = {
        "nome_do_treino": "Treino Intervalado 5k",
        "passos": [
            {"tipo": "aquecimento", "duracao_tipo": "tempo", "duracao_valor": 600, "nome_passo": "Aquecimento 10 min"},
            {"tipo": "corrida", "duracao_tipo": "distancia", "duracao_valor": 5000, "nome_passo": "Corrida 5km"},
            {"tipo": "desaquecimento", "duracao_tipo": "tempo", "duracao_valor": 300, "nome_passo": "Desaquecimento 5 min"}
        ]
    }
    
    # Criar o arquivo
    print("\n1. Criando arquivo de treino...")
    sucesso = criar_treino_fit(treino_exemplo, "exemplo_treino.fit")
    
    if sucesso:
        # Testar o arquivo criado
        print("\n2. Testando arquivo criado...")
        testar_arquivo_fit("exemplo_treino.fit")
        
        # Testar leitura do arquivo de treino
        print("\n3. Testando leitura do arquivo de treino...")
        dados_treino = ler_treino_fit("exemplo_treino.fit")
        
        if dados_treino:
            print("✅ Dados do treino extraídos com sucesso!")
            print(f"📊 Resumo do treino:")
            print(f"   - Nome: {dados_treino['workout'].get('workout_name', 'N/A')}")
            print(f"   - Esporte: {dados_treino['workout'].get('sport', 'N/A')}")
            print(f"   - Número de passos: {dados_treino['workout'].get('num_valid_steps', 0)}")
            print(f"   - Passos encontrados: {len(dados_treino['workout_steps'])}")
            
            for i, step in enumerate(dados_treino['workout_steps']):
                print(f"   Passo {i+1}: {step.get('workout_step_name', 'N/A')}")
                print(f"     - Intensidade: {step.get('intensity', 'N/A')}")
                print(f"     - Duração: {step.get('duration_type', 'N/A')}")
                if 'duration_time' in step:
                    tempo_segundos = step['duration_time'] / 1000 if step['duration_time'] else 0
                    print(f"     - Tempo: {tempo_segundos} segundos")
                if 'duration_distance' in step:
                    distancia_metros = step['duration_distance'] / 100 if step['duration_distance'] else 0
                    print(f"     - Distância: {distancia_metros} metros")
        
        print("\n✅ Teste concluído com sucesso!")
        print("\n📋 Próximos passos:")
        print("1. Integrar com Training API da Garmin para upload")
        print("2. Implementar OAuth 2.0 com PKCE para autenticação")
        print("3. Configurar webhooks para receber notificações de atividades")
    else:
        print("❌ Falha no teste") 