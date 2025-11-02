#!/usr/bin/env python3
"""
Metrics Engine - Cálculo de Métricas Avançadas
==============================================

Engine para calcular métricas avançadas a partir de dados FIT.
Ideal para analytics B2C de smartwatch.

Métricas implementadas:
- Training Load & Recovery
- Performance Metrics
- Heart Rate Zones & Efficiency
- Pace/Speed Analysis
- Running/Cycling Dynamics
- Trends & Comparisons
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from collections import defaultdict


class MetricsEngine:
    """Engine para cálculo de métricas avançadas"""
    
    def __init__(self):
        self.activity_data = None
        
    def analyze_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise completa de uma atividade com métricas avançadas
        
        Args:
            activity_data: Dados parseados do EnhancedFITParser
            
        Returns:
            Dict com métricas avançadas calculadas
        """
        self.activity_data = activity_data
        
        metrics = {
            'basic_stats': self._calculate_basic_stats(),
            'heart_rate_analysis': self._analyze_heart_rate(),
            'pace_speed_analysis': self._analyze_pace_speed(),
            'elevation_analysis': self._analyze_elevation(),
            'cadence_analysis': self._analyze_cadence(),
            'power_analysis': self._analyze_power(),
            'running_dynamics': self._analyze_running_dynamics(),
            'splits': self._calculate_splits(),
            'zones': self._calculate_zones(),
            'efficiency_metrics': self._calculate_efficiency(),
            'fatigue_analysis': self._analyze_fatigue(),
            'performance_score': self._calculate_performance_score(),
        }
        
        return metrics
    
    def _calculate_basic_stats(self) -> Dict[str, Any]:
        """Estatísticas básicas da atividade"""
        sessions = self.activity_data.get('sessions', [])
        if not sessions:
            return {}
        
        session = sessions[0]
        
        total_distance = session.get('total_distance', 0)
        total_time = session.get('total_timer_time', 0)
        
        return {
            'sport': session.get('sport'),
            'sub_sport': session.get('sub_sport'),
            'start_time': session.get('start_time'),
            'duration_seconds': total_time,
            'duration_formatted': self._format_duration(total_time),
            'distance_meters': total_distance,
            'distance_km': round(total_distance / 1000, 2) if total_distance else 0,
            'distance_miles': round(total_distance / 1609.34, 2) if total_distance else 0,
            'total_calories': session.get('total_calories', 0),
            'avg_heart_rate': session.get('avg_heart_rate'),
            'max_heart_rate': session.get('max_heart_rate'),
            'total_ascent': session.get('total_ascent'),
            'total_descent': session.get('total_descent'),
        }
    
    def _analyze_heart_rate(self) -> Dict[str, Any]:
        """Análise avançada de frequência cardíaca"""
        sessions = self.activity_data.get('sessions', [])
        records = self.activity_data.get('records', [])
        
        if not sessions or not records:
            return {}
        
        session = sessions[0]
        
        # Extrair HR de todos os records
        hr_values = [r.get('heart_rate') for r in records if r.get('heart_rate')]
        
        if not hr_values:
            return {
                'avg': session.get('avg_heart_rate'),
                'max': session.get('max_heart_rate'),
                'min': session.get('min_heart_rate'),
            }
        
        # Calcular variabilidade
        hr_variability = statistics.stdev(hr_values) if len(hr_values) > 1 else 0
        
        # Zonas de FC (simplificado - pode usar HR max do usuário)
        max_hr = session.get('max_heart_rate', max(hr_values))
        zones = self._calculate_hr_zones(hr_values, max_hr)
        
        # Análise de tendência
        hr_drift = self._calculate_hr_drift(hr_values)
        
        return {
            'avg': round(statistics.mean(hr_values), 1),
            'max': max(hr_values),
            'min': min(hr_values),
            'median': statistics.median(hr_values),
            'std_dev': round(hr_variability, 2),
            'zones': zones,
            'hr_drift_percent': hr_drift,
            'time_in_zones': self._time_in_hr_zones(hr_values),
        }
    
    def _calculate_hr_zones(self, hr_values: List[int], max_hr: int) -> Dict[str, Any]:
        """Calcula distribuição em zonas de FC"""
        zones = {
            'zone1': {'name': 'Recovery', 'range': (0, 0.6 * max_hr), 'count': 0},
            'zone2': {'name': 'Endurance', 'range': (0.6 * max_hr, 0.7 * max_hr), 'count': 0},
            'zone3': {'name': 'Tempo', 'range': (0.7 * max_hr, 0.8 * max_hr), 'count': 0},
            'zone4': {'name': 'Threshold', 'range': (0.8 * max_hr, 0.9 * max_hr), 'count': 0},
            'zone5': {'name': 'VO2 Max', 'range': (0.9 * max_hr, max_hr), 'count': 0},
        }
        
        for hr in hr_values:
            for zone_key, zone_data in zones.items():
                if zone_data['range'][0] <= hr < zone_data['range'][1]:
                    zone_data['count'] += 1
                    break
        
        total = len(hr_values)
        for zone_data in zones.values():
            zone_data['percentage'] = round((zone_data['count'] / total * 100), 1) if total > 0 else 0
        
        return zones
    
    def _time_in_hr_zones(self, hr_values: List[int]) -> Dict[str, int]:
        """Tempo gasto em cada zona (assumindo 1 record/segundo)"""
        max_hr = max(hr_values) if hr_values else 180
        
        zone_times = {
            'zone1_seconds': 0,
            'zone2_seconds': 0,
            'zone3_seconds': 0,
            'zone4_seconds': 0,
            'zone5_seconds': 0,
        }
        
        for hr in hr_values:
            if hr < 0.6 * max_hr:
                zone_times['zone1_seconds'] += 1
            elif hr < 0.7 * max_hr:
                zone_times['zone2_seconds'] += 1
            elif hr < 0.8 * max_hr:
                zone_times['zone3_seconds'] += 1
            elif hr < 0.9 * max_hr:
                zone_times['zone4_seconds'] += 1
            else:
                zone_times['zone5_seconds'] += 1
        
        return zone_times
    
    def _calculate_hr_drift(self, hr_values: List[int]) -> float:
        """Calcula drift de FC (primeira vs segunda metade)"""
        if len(hr_values) < 20:
            return 0.0
        
        mid = len(hr_values) // 2
        first_half = hr_values[:mid]
        second_half = hr_values[mid:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        drift = ((avg_second - avg_first) / avg_first) * 100
        return round(drift, 2)
    
    def _analyze_pace_speed(self) -> Dict[str, Any]:
        """Análise de pace/velocidade"""
        sessions = self.activity_data.get('sessions', [])
        records = self.activity_data.get('records', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        # Usar enhanced_avg_speed se disponível, senão avg_speed
        avg_speed_ms = session.get('enhanced_avg_speed') or session.get('avg_speed', 0)
        max_speed_ms = session.get('enhanced_max_speed') or session.get('max_speed', 0)
        
        result = {
            'avg_speed_ms': avg_speed_ms,
            'avg_speed_kmh': round(avg_speed_ms * 3.6, 2) if avg_speed_ms else 0,
            'avg_speed_mph': round(avg_speed_ms * 2.237, 2) if avg_speed_ms else 0,
            'max_speed_ms': max_speed_ms,
            'max_speed_kmh': round(max_speed_ms * 3.6, 2) if max_speed_ms else 0,
            'max_speed_mph': round(max_speed_ms * 2.237, 2) if max_speed_ms else 0,
        }
        
        # Calcular pace (min/km e min/mile) para corrida
        if avg_speed_ms > 0:
            pace_min_per_km = 1000 / (avg_speed_ms * 60)
            pace_min_per_mile = 1609.34 / (avg_speed_ms * 60)
            
            result['avg_pace_min_per_km'] = self._format_pace(pace_min_per_km)
            result['avg_pace_min_per_mile'] = self._format_pace(pace_min_per_mile)
        
        # Análise de variabilidade de speed nos records
        if records:
            speeds = [r.get('enhanced_speed') or r.get('speed', 0) for r in records if r.get('speed') or r.get('enhanced_speed')]
            if speeds:
                result['speed_variability'] = round(statistics.stdev(speeds), 3) if len(speeds) > 1 else 0
                result['consistency_score'] = self._calculate_consistency(speeds)
        
        return result
    
    def _analyze_elevation(self) -> Dict[str, Any]:
        """Análise de elevação"""
        sessions = self.activity_data.get('sessions', [])
        records = self.activity_data.get('records', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        result = {
            'total_ascent': session.get('total_ascent', 0),
            'total_descent': session.get('total_descent', 0),
            'avg_altitude': session.get('enhanced_avg_altitude') or session.get('avg_altitude'),
            'max_altitude': session.get('enhanced_max_altitude') or session.get('max_altitude'),
            'min_altitude': session.get('enhanced_min_altitude') or session.get('min_altitude'),
            'avg_grade': session.get('avg_grade'),
            'max_pos_grade': session.get('max_pos_grade'),
            'max_neg_grade': session.get('max_neg_grade'),
        }
        
        # Análise de elevação ao longo do tempo
        if records:
            altitudes = [r.get('enhanced_altitude') or r.get('altitude') for r in records if r.get('altitude') or r.get('enhanced_altitude')]
            if altitudes:
                result['altitude_variability'] = round(statistics.stdev(altitudes), 2) if len(altitudes) > 1 else 0
        
        return result
    
    def _analyze_cadence(self) -> Dict[str, Any]:
        """Análise de cadência"""
        sessions = self.activity_data.get('sessions', [])
        records = self.activity_data.get('records', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        result = {
            'avg_cadence': session.get('avg_cadence') or session.get('avg_running_cadence'),
            'max_cadence': session.get('max_cadence') or session.get('max_running_cadence'),
        }
        
        # Análise detalhada de cadência
        if records:
            cadences = [r.get('cadence') for r in records if r.get('cadence')]
            if cadences:
                result['cadence_std_dev'] = round(statistics.stdev(cadences), 2) if len(cadences) > 1 else 0
                result['cadence_consistency'] = self._calculate_consistency(cadences)
        
        return result
    
    def _analyze_power(self) -> Dict[str, Any]:
        """Análise de potência (ciclismo/corrida)"""
        sessions = self.activity_data.get('sessions', [])
        records = self.activity_data.get('records', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        result = {
            'avg_power': session.get('avg_power'),
            'max_power': session.get('max_power'),
            'normalized_power': session.get('normalized_power'),
            'training_stress_score': session.get('training_stress_score'),
            'intensity_factor': session.get('intensity_factor'),
            'total_work': session.get('total_work'),
        }
        
        # Power zones
        if records:
            powers = [r.get('power') for r in records if r.get('power')]
            if powers:
                result['power_variability'] = round(statistics.stdev(powers), 2) if len(powers) > 1 else 0
        
        return result
    
    def _analyze_running_dynamics(self) -> Dict[str, Any]:
        """Análise de running dynamics"""
        sessions = self.activity_data.get('sessions', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        return {
            'vertical_oscillation': session.get('avg_vertical_oscillation'),
            'vertical_ratio': session.get('avg_vertical_ratio'),
            'stance_time': session.get('avg_stance_time'),
            'stance_time_percent': session.get('avg_stance_time_percent'),
            'stance_time_balance': session.get('avg_stance_time_balance'),
            'step_length': session.get('avg_step_length'),
            'total_steps': session.get('total_steps'),
        }
    
    def _calculate_splits(self) -> List[Dict[str, Any]]:
        """Calcula splits por km ou milha"""
        laps = self.activity_data.get('laps', [])
        
        splits = []
        for i, lap in enumerate(laps):
            split = {
                'lap_number': i + 1,
                'distance': lap.get('total_distance'),
                'time': lap.get('total_timer_time'),
                'avg_heart_rate': lap.get('avg_heart_rate'),
                'avg_speed': lap.get('enhanced_avg_speed') or lap.get('avg_speed'),
                'avg_cadence': lap.get('avg_cadence'),
                'total_ascent': lap.get('total_ascent'),
                'total_calories': lap.get('total_calories'),
            }
            
            # Calcular pace se tiver speed
            if split['avg_speed'] and split['avg_speed'] > 0:
                pace_min_per_km = 1000 / (split['avg_speed'] * 60)
                split['pace_min_per_km'] = self._format_pace(pace_min_per_km)
            
            splits.append(split)
        
        return splits
    
    def _calculate_zones(self) -> Dict[str, Any]:
        """Calcula tempo em diferentes zonas de treinamento"""
        records = self.activity_data.get('records', [])
        
        if not records:
            return {}
        
        # Zonas baseadas em HR (já calculado em heart_rate_analysis)
        # Adicionar zonas de power se disponível
        powers = [r.get('power') for r in records if r.get('power')]
        
        zones = {}
        
        if powers:
            zones['power_zones'] = self._calculate_power_zones(powers)
        
        return zones
    
    def _calculate_power_zones(self, powers: List[int]) -> Dict[str, Any]:
        """Calcula zonas de potência"""
        if not powers:
            return {}
        
        avg_power = statistics.mean(powers)
        
        # Zonas simplificadas (idealmente usar FTP do usuário)
        zones = {
            'zone1': {'name': 'Active Recovery', 'range': (0, 0.55 * avg_power), 'count': 0},
            'zone2': {'name': 'Endurance', 'range': (0.55 * avg_power, 0.75 * avg_power), 'count': 0},
            'zone3': {'name': 'Tempo', 'range': (0.75 * avg_power, 0.9 * avg_power), 'count': 0},
            'zone4': {'name': 'Threshold', 'range': (0.9 * avg_power, 1.05 * avg_power), 'count': 0},
            'zone5': {'name': 'VO2 Max', 'range': (1.05 * avg_power, float('inf')), 'count': 0},
        }
        
        for power in powers:
            for zone_data in zones.values():
                if zone_data['range'][0] <= power < zone_data['range'][1]:
                    zone_data['count'] += 1
                    break
        
        total = len(powers)
        for zone_data in zones.values():
            zone_data['percentage'] = round((zone_data['count'] / total * 100), 1) if total > 0 else 0
        
        return zones
    
    def _calculate_efficiency(self) -> Dict[str, Any]:
        """Calcula métricas de eficiência"""
        sessions = self.activity_data.get('sessions', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        # Efficiency metrics
        result = {}
        
        # Aerobic Efficiency (pace vs HR)
        avg_speed = session.get('enhanced_avg_speed') or session.get('avg_speed')
        avg_hr = session.get('avg_heart_rate')
        
        if avg_speed and avg_hr and avg_speed > 0 and avg_hr > 0:
            # Quanto mais rápido com menor HR, melhor
            result['aerobic_efficiency'] = round((avg_speed * 3.6) / avg_hr, 4)
        
        # Caloric Efficiency (calorias por km)
        total_distance = session.get('total_distance', 0)
        total_calories = session.get('total_calories', 0)
        
        if total_distance > 0 and total_calories > 0:
            result['calories_per_km'] = round(total_calories / (total_distance / 1000), 2)
        
        return result
    
    def _analyze_fatigue(self) -> Dict[str, Any]:
        """Análise de fadiga durante atividade"""
        records = self.activity_data.get('records', [])
        
        if not records or len(records) < 10:
            return {}
        
        # Dividir em quartis
        quartile_size = len(records) // 4
        quartiles = [
            records[:quartile_size],
            records[quartile_size:2*quartile_size],
            records[2*quartile_size:3*quartile_size],
            records[3*quartile_size:],
        ]
        
        fatigue_indicators = {}
        
        # Análise de HR por quartil
        hr_by_quartile = []
        for i, q in enumerate(quartiles):
            hrs = [r.get('heart_rate') for r in q if r.get('heart_rate')]
            if hrs:
                hr_by_quartile.append({
                    'quartile': i + 1,
                    'avg_hr': round(statistics.mean(hrs), 1)
                })
        
        fatigue_indicators['hr_progression'] = hr_by_quartile
        
        # Análise de speed por quartil
        speed_by_quartile = []
        for i, q in enumerate(quartiles):
            speeds = [r.get('enhanced_speed') or r.get('speed', 0) for r in q if r.get('speed') or r.get('enhanced_speed')]
            if speeds:
                speed_by_quartile.append({
                    'quartile': i + 1,
                    'avg_speed_kmh': round(statistics.mean(speeds) * 3.6, 2)
                })
        
        fatigue_indicators['speed_progression'] = speed_by_quartile
        
        # Calcular índice de fadiga (decaimento de performance)
        if len(speed_by_quartile) >= 2:
            first_speed = speed_by_quartile[0]['avg_speed_kmh']
            last_speed = speed_by_quartile[-1]['avg_speed_kmh']
            
            if first_speed > 0:
                fatigue_index = ((first_speed - last_speed) / first_speed) * 100
                fatigue_indicators['fatigue_index_percent'] = round(fatigue_index, 2)
        
        return fatigue_indicators
    
    def _calculate_performance_score(self) -> Dict[str, Any]:
        """Calcula score de performance geral"""
        sessions = self.activity_data.get('sessions', [])
        
        if not sessions:
            return {}
        
        session = sessions[0]
        
        # Score baseado em training effect, TSS, etc.
        score = {
            'training_effect': session.get('total_training_effect'),
            'anaerobic_training_effect': session.get('total_anaerobic_training_effect'),
            'training_stress_score': session.get('training_stress_score'),
        }
        
        # Calcular score agregado (0-100)
        # Simplificado - pode ser mais sofisticado
        factors = []
        
        te = session.get('total_training_effect', 0)
        if te:
            factors.append(min(te / 5.0 * 100, 100))  # TE máx ~5.0
        
        tss = session.get('training_stress_score', 0)
        if tss:
            factors.append(min(tss / 200 * 100, 100))  # TSS 200 = muito alto
        
        if factors:
            score['overall_score'] = round(statistics.mean(factors), 1)
        
        return score
    
    # Utility methods
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em HH:MM:SS"""
        if not seconds:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _format_pace(self, pace_minutes: float) -> str:
        """Formata pace em MM:SS"""
        minutes = int(pace_minutes)
        seconds = int((pace_minutes - minutes) * 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _calculate_consistency(self, values: List[float]) -> float:
        """Calcula score de consistência (0-100)"""
        if not values or len(values) < 2:
            return 100.0
        
        avg = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        if avg == 0:
            return 0.0
        
        # Coefficient of variation invertido
        cv = (std_dev / avg) * 100
        consistency = max(0, 100 - cv)
        
        return round(consistency, 2)


if __name__ == "__main__":
    print("✅ Metrics Engine carregado com sucesso!")
    print("\nUso:")
    print("  from metrics_engine import MetricsEngine")
    print("  engine = MetricsEngine()")
    print("  metrics = engine.analyze_activity(activity_data)")

