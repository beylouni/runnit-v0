#!/usr/bin/env python3
"""
Enhanced FIT Parser - Extração COMPLETA de Dados
=================================================

Este módulo extrai 100% dos dados disponíveis em arquivos FIT,
sem cherry-picking. Ideal para analytics avançados.

Suporta:
- Activities (corrida, ciclismo, natação, etc.)
- Health data (HR contínuo, stress, sono, etc.)
- Advanced metrics (HRV, power, cadence, etc.)
"""

import sys
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
import json

# Add parent directory to path for garmin_fit_sdk
parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

try:
    from garmin_fit_sdk import Decoder, Stream
    FIT_SDK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Garmin FIT SDK não disponível: {e}")
    FIT_SDK_AVAILABLE = False


class EnhancedFITParser:
    """Parser avançado de arquivos FIT com extração completa"""
    
    def __init__(self):
        self.file_path = None
        self.messages = {}
        self.errors = []
        
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse completo do arquivo FIT
        
        Returns:
            Dict com todas as mensagens e dados estruturados
        """
        self.file_path = file_path
        
        if not FIT_SDK_AVAILABLE:
            raise Exception("Garmin FIT SDK não disponível")
        
        stream = Stream.from_file(file_path)
        decoder = Decoder(stream)
        
        if not decoder.is_fit():
            raise Exception("Arquivo não é um FIT válido")
        
        self.messages, self.errors = decoder.read()
        
        # Estruturar dados
        structured_data = {
            'file_info': self._extract_file_info(),
            'device_info': self._extract_device_info(),
            'activity_summary': self._extract_activity_summary(),
            'laps': self._extract_laps(),
            'records': self._extract_records(),
            'sessions': self._extract_sessions(),
            'events': self._extract_events(),
            'hrv': self._extract_hrv(),
            'developer_fields': self._extract_developer_fields(),
            'raw_messages': self._get_all_raw_messages(),
            'metadata': {
                'parsed_at': datetime.now().isoformat(),
                'file_path': file_path,
                'file_size_bytes': os.path.getsize(file_path),
                'errors': self.errors,
                'message_types_count': {k: len(v) for k, v in self.messages.items()}
            }
        }
        
        return structured_data
    
    def _extract_file_info(self) -> Dict:
        """Extrai informações do arquivo"""
        if 'file_id_mesgs' not in self.messages:
            return {}
        
        file_id = self.messages['file_id_mesgs'][0] if self.messages['file_id_mesgs'] else {}
        return {
            'type': file_id.get('type'),
            'manufacturer': file_id.get('manufacturer'),
            'product': file_id.get('product'),
            'product_name': file_id.get('product_name'),
            'serial_number': file_id.get('serial_number'),
            'time_created': file_id.get('time_created'),
            'number': file_id.get('number'),
        }
    
    def _extract_device_info(self) -> List[Dict]:
        """Extrai informações dos dispositivos"""
        if 'device_info_mesgs' not in self.messages:
            return []
        
        devices = []
        for device in self.messages['device_info_mesgs']:
            devices.append({
                'device_index': device.get('device_index'),
                'device_type': device.get('device_type'),
                'manufacturer': device.get('manufacturer'),
                'product': device.get('product'),
                'product_name': device.get('product_name'),
                'serial_number': device.get('serial_number'),
                'software_version': device.get('software_version'),
                'hardware_version': device.get('hardware_version'),
                'cum_operating_time': device.get('cum_operating_time'),
                'battery_status': device.get('battery_status'),
                'battery_voltage': device.get('battery_voltage'),
                'ant_device_number': device.get('ant_device_number'),
                'source_type': device.get('source_type'),
                'timestamp': device.get('timestamp'),
            })
        
        return devices
    
    def _extract_activity_summary(self) -> Dict:
        """Extrai resumo da atividade (mais completo)"""
        if 'activity_mesgs' not in self.messages:
            return {}
        
        activity = self.messages['activity_mesgs'][0] if self.messages['activity_mesgs'] else {}
        
        return {
            'timestamp': activity.get('timestamp'),
            'total_timer_time': activity.get('total_timer_time'),
            'num_sessions': activity.get('num_sessions'),
            'type': activity.get('type'),
            'event': activity.get('event'),
            'event_type': activity.get('event_type'),
            'local_timestamp': activity.get('local_timestamp'),
            'event_group': activity.get('event_group'),
        }
    
    def _extract_sessions(self) -> List[Dict]:
        """Extrai TODAS as sessões com TODOS os campos"""
        if 'session_mesgs' not in self.messages:
            return []
        
        sessions = []
        for session in self.messages['session_mesgs']:
            # Não fazer cherry-picking - pegar TUDO
            session_data = dict(session)
            sessions.append(session_data)
        
        return sessions
    
    def _extract_laps(self) -> List[Dict]:
        """Extrai TODAS as voltas com TODOS os campos"""
        if 'lap_mesgs' not in self.messages:
            return []
        
        laps = []
        for lap in self.messages['lap_mesgs']:
            lap_data = dict(lap)  # Pegar TUDO sem filtro
            laps.append(lap_data)
        
        return laps
    
    def _extract_records(self) -> List[Dict]:
        """Extrai TODOS os records (pontos) com TODOS os campos"""
        if 'record_mesgs' not in self.messages:
            return []
        
        records = []
        for record in self.messages['record_mesgs']:
            # Não filtrar - pegar TUDO
            record_data = dict(record)
            records.append(record_data)
        
        return records
    
    def _extract_events(self) -> List[Dict]:
        """Extrai eventos da atividade"""
        if 'event_mesgs' not in self.messages:
            return []
        
        events = []
        for event in self.messages['event_mesgs']:
            events.append(dict(event))
        
        return events
    
    def _extract_hrv(self) -> List[Dict]:
        """Extrai dados de HRV (Heart Rate Variability)"""
        if 'hrv_mesgs' not in self.messages:
            return []
        
        hrv_data = []
        for hrv in self.messages['hrv_mesgs']:
            hrv_data.append(dict(hrv))
        
        return hrv_data
    
    def _extract_developer_fields(self) -> Dict:
        """Extrai campos de desenvolvedor (ConnectIQ, etc.)"""
        developer_data = {}
        
        if 'developer_data_id_mesgs' in self.messages:
            developer_data['definitions'] = [dict(d) for d in self.messages['developer_data_id_mesgs']]
        
        if 'field_description_mesgs' in self.messages:
            developer_data['field_descriptions'] = [dict(f) for f in self.messages['field_description_mesgs']]
        
        return developer_data
    
    def _get_all_raw_messages(self) -> Dict:
        """Retorna TODAS as mensagens sem processamento"""
        raw = {}
        for msg_type, msg_list in self.messages.items():
            raw[msg_type] = [dict(msg) for msg in msg_list]
        
        return raw
    
    def get_available_fields_report(self) -> Dict[str, List[str]]:
        """
        Gera relatório de campos disponíveis por tipo de mensagem
        Útil para descobrir quais campos seu dispositivo fornece
        """
        report = {}
        
        for msg_type, msg_list in self.messages.items():
            if not msg_list:
                continue
            
            # Coletar todos os campos únicos deste tipo
            all_fields = set()
            for msg in msg_list:
                all_fields.update(msg.keys())
            
            # Converter para strings para garantir que são sortáveis
            report[msg_type] = sorted([str(f) for f in all_fields])
        
        return report
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Gera resumo de métricas disponíveis
        Útil para analytics e dashboards
        """
        summary = {
            'has_gps': False,
            'has_heart_rate': False,
            'has_power': False,
            'has_cadence': False,
            'has_temperature': False,
            'has_running_dynamics': False,
            'has_cycling_dynamics': False,
            'has_hrv': False,
            'total_records': 0,
            'total_laps': 0,
            'sport_type': None,
            'device_name': None,
        }
        
        # Check records
        if 'record_mesgs' in self.messages and self.messages['record_mesgs']:
            summary['total_records'] = len(self.messages['record_mesgs'])
            
            # Verificar campos em todos os records
            all_fields = set()
            for record in self.messages['record_mesgs']:
                all_fields.update(record.keys())
            
            summary['has_gps'] = 'position_lat' in all_fields or 'position_long' in all_fields
            summary['has_heart_rate'] = 'heart_rate' in all_fields
            summary['has_power'] = 'power' in all_fields
            summary['has_cadence'] = 'cadence' in all_fields or 'fractional_cadence' in all_fields
            summary['has_temperature'] = 'temperature' in all_fields
            summary['has_running_dynamics'] = 'vertical_oscillation' in all_fields or 'stance_time' in all_fields
            summary['has_cycling_dynamics'] = 'left_torque_effectiveness' in all_fields
        
        # Check HRV
        summary['has_hrv'] = 'hrv_mesgs' in self.messages and len(self.messages.get('hrv_mesgs', [])) > 0
        
        # Check laps
        summary['total_laps'] = len(self.messages.get('lap_mesgs', []))
        
        # Sport type
        if 'session_mesgs' in self.messages and self.messages['session_mesgs']:
            summary['sport_type'] = self.messages['session_mesgs'][0].get('sport')
        
        # Device
        if 'device_info_mesgs' in self.messages and self.messages['device_info_mesgs']:
            summary['device_name'] = self.messages['device_info_mesgs'][0].get('product_name')
        
        return summary
    
    def save_to_json(self, output_path: str, data: Dict[str, Any]) -> None:
        """Salva dados parseados em JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def analyze_fit_file(file_path: str, verbose: bool = True) -> Optional[Dict[str, Any]]:
    """Análise completa de um arquivo FIT com report detalhado"""
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"📊 ANÁLISE COMPLETA DO ARQUIVO FIT")
        print(f"{'='*80}")
        print(f"Arquivo: {file_path}\n")
    
    parser = EnhancedFITParser()
    
    try:
        # Parse completo
        data = parser.parse(file_path)
        
        if verbose:
            # Relatório de campos disponíveis
            print("📋 CAMPOS DISPONÍVEIS POR TIPO DE MENSAGEM:")
            print("="*80)
            
            fields_report = parser.get_available_fields_report()
            for msg_type, fields in sorted(fields_report.items()):
                print(f"\n🔹 {msg_type} ({len(fields)} campos):")
                for field in fields[:10]:  # Mostrar primeiros 10
                    print(f"   • {field}")
                if len(fields) > 10:
                    print(f"   ... e mais {len(fields) - 10} campos")
            
            # Resumo de métricas
            print(f"\n{'='*80}")
            print("🎯 RESUMO DE MÉTRICAS DISPONÍVEIS:")
            print("="*80)
            
            metrics_summary = parser.get_metrics_summary()
            for key, value in metrics_summary.items():
                icon = "✅" if value else "❌"
                if isinstance(value, bool):
                    print(f"{icon} {key}: {value}")
                else:
                    print(f"📊 {key}: {value}")
            
            # Estatísticas
            print(f"\n{'='*80}")
            print("📈 ESTATÍSTICAS:")
            print("="*80)
            print(f"Total de tipos de mensagem: {len(data['raw_messages'])}")
            print(f"Total de records (pontos): {len(data['records'])}")
            print(f"Total de laps (voltas): {len(data['laps'])}")
            print(f"Total de sessions: {len(data['sessions'])}")
            print(f"Total de events: {len(data['events'])}")
            print(f"Total de HRV records: {len(data['hrv'])}")
        
        return data
        
    except Exception as e:
        if verbose:
            print(f"❌ Erro ao analisar arquivo: {e}")
            import traceback
            traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    
    # Teste com arquivo passado como argumento ou arquivo padrão
    if len(sys.argv) > 1:
        fit_file = sys.argv[1]
    else:
        fit_file = "../backend/uploads/activities/18584456659.fit"
    
    if os.path.exists(fit_file):
        data = analyze_fit_file(fit_file)
        
        if data:
            # Salvar dados completos
            output_file = fit_file.replace('.fit', '_complete_data.json')
            parser = EnhancedFITParser()
            parser.save_to_json(output_file, data)
            print(f"\n✅ Dados completos salvos em: {output_file}")
    else:
        print(f"❌ Arquivo não encontrado: {fit_file}")
        print(f"\nUso: python {sys.argv[0]} <caminho_para_arquivo.fit>")

