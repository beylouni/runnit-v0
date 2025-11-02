-- Schema para Banco de Dados - Sistema de Analytics de Smartwatch
-- PostgreSQL

-- ============================================================================
-- TABELA: users
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    garmin_user_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    
    -- OAuth tokens
    garmin_access_token TEXT,
    garmin_refresh_token TEXT,
    garmin_token_expires_at TIMESTAMP,
    
    -- Preferências
    timezone VARCHAR(50) DEFAULT 'UTC',
    unit_system VARCHAR(10) DEFAULT 'metric', -- metric ou imperial
    
    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_garmin_user_id ON users(garmin_user_id);
CREATE INDEX idx_users_email ON users(email);


-- ============================================================================
-- TABELA: activities
-- ============================================================================
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- IDs externos
    garmin_activity_id VARCHAR(255) UNIQUE NOT NULL,
    garmin_summary_id VARCHAR(255),
    
    -- Dados básicos
    activity_name VARCHAR(255),
    sport VARCHAR(50) NOT NULL, -- running, cycling, swimming, etc.
    sub_sport VARCHAR(50),
    
    -- Tempo e data
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    moving_time_seconds INTEGER,
    
    -- Distância
    distance_meters FLOAT,
    distance_km FLOAT GENERATED ALWAYS AS (distance_meters / 1000.0) STORED,
    
    -- Velocidade e Pace
    avg_speed_ms FLOAT,
    max_speed_ms FLOAT,
    avg_pace_min_per_km FLOAT,
    
    -- Frequência Cardíaca
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    min_heart_rate INTEGER,
    
    -- Calorias
    total_calories INTEGER,
    
    -- Elevação
    total_ascent FLOAT,
    total_descent FLOAT,
    avg_altitude FLOAT,
    max_altitude FLOAT,
    min_altitude FLOAT,
    
    -- Cadência
    avg_cadence INTEGER,
    max_cadence INTEGER,
    
    -- Potência (cycling/running power)
    avg_power INTEGER,
    max_power INTEGER,
    normalized_power INTEGER,
    training_stress_score FLOAT,
    
    -- Coordenadas de início/fim
    start_latitude FLOAT,
    start_longitude FLOAT,
    end_latitude FLOAT,
    end_longitude FLOAT,
    
    -- Dispositivo
    device_name VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    -- Flags
    is_manual BOOLEAN DEFAULT FALSE,
    has_gps BOOLEAN DEFAULT TRUE,
    has_heart_rate BOOLEAN DEFAULT FALSE,
    has_power BOOLEAN DEFAULT FALSE,
    has_cadence BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT activities_duration_check CHECK (duration_seconds >= 0),
    CONSTRAINT activities_distance_check CHECK (distance_meters >= 0),
    CONSTRAINT activities_calories_check CHECK (total_calories >= 0)
);

CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_garmin_activity_id ON activities(garmin_activity_id);
CREATE INDEX idx_activities_start_time ON activities(start_time DESC);
CREATE INDEX idx_activities_sport ON activities(sport);
CREATE INDEX idx_activities_user_sport ON activities(user_id, sport);
CREATE INDEX idx_activities_user_start_time ON activities(user_id, start_time DESC);


-- ============================================================================
-- TABELA: activity_metrics
-- ============================================================================
CREATE TABLE activity_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    
    -- Métricas Avançadas
    hr_drift_percent FLOAT,
    consistency_score FLOAT,
    fatigue_index_percent FLOAT,
    aerobic_efficiency FLOAT,
    calories_per_km FLOAT,
    
    -- Zonas de HR (percentuais)
    zone1_recovery_percent FLOAT,
    zone2_endurance_percent FLOAT,
    zone3_tempo_percent FLOAT,
    zone4_threshold_percent FLOAT,
    zone5_vo2max_percent FLOAT,
    
    -- Tempo em zonas (segundos)
    zone1_time_seconds INTEGER,
    zone2_time_seconds INTEGER,
    zone3_time_seconds INTEGER,
    zone4_time_seconds INTEGER,
    zone5_time_seconds INTEGER,
    
    -- Running Dynamics
    avg_vertical_oscillation FLOAT,
    avg_stance_time FLOAT,
    avg_step_length FLOAT,
    total_steps INTEGER,
    
    -- Training Effect (Firstbeat)
    training_effect FLOAT,
    anaerobic_training_effect FLOAT,
    
    -- Variabilidade
    hr_std_dev FLOAT,
    speed_variability FLOAT,
    cadence_std_dev FLOAT,
    cadence_consistency FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_metrics_activity_id ON activity_metrics(activity_id);


-- ============================================================================
-- TABELA: activity_records (Pontos GPS)
-- ============================================================================
CREATE TABLE activity_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    
    -- Tempo
    timestamp TIMESTAMP NOT NULL,
    elapsed_time_seconds INTEGER,
    
    -- GPS
    latitude FLOAT,
    longitude FLOAT,
    altitude FLOAT,
    
    -- Movimento
    distance_meters FLOAT,
    speed_ms FLOAT,
    
    -- Fisiológico
    heart_rate INTEGER,
    cadence INTEGER,
    power INTEGER,
    
    -- Running Dynamics
    vertical_oscillation FLOAT,
    stance_time FLOAT,
    
    -- Temperatura
    temperature FLOAT,
    
    -- Índice sequencial para ordenação
    record_index INTEGER NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT activity_records_record_index_check CHECK (record_index >= 0)
);

CREATE INDEX idx_activity_records_activity_id ON activity_records(activity_id);
CREATE INDEX idx_activity_records_timestamp ON activity_records(timestamp);
CREATE INDEX idx_activity_records_activity_index ON activity_records(activity_id, record_index);
-- Índice geográfico para consultas de mapa
CREATE INDEX idx_activity_records_location ON activity_records(latitude, longitude) WHERE latitude IS NOT NULL AND longitude IS NOT NULL;


-- ============================================================================
-- TABELA: activity_laps
-- ============================================================================
CREATE TABLE activity_laps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    
    -- Identificação
    lap_number INTEGER NOT NULL,
    
    -- Tempo
    start_time TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Distância
    distance_meters FLOAT,
    
    -- Velocidade e Pace
    avg_speed_ms FLOAT,
    max_speed_ms FLOAT,
    
    -- Frequência Cardíaca
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    
    -- Cadência
    avg_cadence INTEGER,
    max_cadence INTEGER,
    
    -- Potência
    avg_power INTEGER,
    max_power INTEGER,
    
    -- Elevação
    total_ascent FLOAT,
    total_descent FLOAT,
    
    -- Calorias
    total_calories INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT activity_laps_lap_number_check CHECK (lap_number > 0)
);

CREATE INDEX idx_activity_laps_activity_id ON activity_laps(activity_id);
CREATE INDEX idx_activity_laps_activity_lap_number ON activity_laps(activity_id, lap_number);


-- ============================================================================
-- TABELA: activity_insights
-- ============================================================================
CREATE TABLE activity_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    
    -- Insight
    insight_type VARCHAR(50) NOT NULL, -- warning, positive, tip, achievement
    category VARCHAR(50) NOT NULL, -- cardiovascular, pacing, performance, etc.
    message TEXT NOT NULL,
    
    -- Dados estruturados (para ML futuro)
    data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_insights_activity_id ON activity_insights(activity_id);
CREATE INDEX idx_activity_insights_type ON activity_insights(insight_type);


-- ============================================================================
-- TABELA: user_records
-- ============================================================================
CREATE TABLE user_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tipo de recorde
    record_type VARCHAR(50) NOT NULL, -- fastest_pace, longest_distance, etc.
    sport VARCHAR(50),
    
    -- Valor
    value FLOAT NOT NULL,
    unit VARCHAR(20),
    
    -- Atividade que estabeleceu o recorde
    activity_id UUID REFERENCES activities(id) ON DELETE SET NULL,
    achieved_at TIMESTAMP NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Garantir um recorde por tipo/esporte por usuário
    CONSTRAINT user_records_unique UNIQUE (user_id, record_type, sport)
);

CREATE INDEX idx_user_records_user_id ON user_records(user_id);
CREATE INDEX idx_user_records_sport ON user_records(sport);


-- ============================================================================
-- TABELA: user_stats_daily
-- ============================================================================
CREATE TABLE user_stats_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Data
    date DATE NOT NULL,
    
    -- Totais do dia
    total_activities INTEGER DEFAULT 0,
    total_distance_km FLOAT DEFAULT 0,
    total_time_seconds INTEGER DEFAULT 0,
    total_calories INTEGER DEFAULT 0,
    
    -- Médias do dia
    avg_heart_rate INTEGER,
    avg_pace_min_per_km FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Um registro por usuário por dia
    CONSTRAINT user_stats_daily_unique UNIQUE (user_id, date)
);

CREATE INDEX idx_user_stats_daily_user_id ON user_stats_daily(user_id);
CREATE INDEX idx_user_stats_daily_date ON user_stats_daily(date DESC);
CREATE INDEX idx_user_stats_daily_user_date ON user_stats_daily(user_id, date DESC);


-- ============================================================================
-- VIEWS ÚTEIS
-- ============================================================================

-- View: Atividades com métricas
CREATE VIEW activities_with_metrics AS
SELECT 
    a.*,
    m.hr_drift_percent,
    m.consistency_score,
    m.fatigue_index_percent,
    m.aerobic_efficiency,
    m.training_effect
FROM activities a
LEFT JOIN activity_metrics m ON a.id = m.activity_id;

-- View: Resumo por esporte
CREATE VIEW user_stats_by_sport AS
SELECT 
    user_id,
    sport,
    COUNT(*) as total_activities,
    SUM(distance_km) as total_distance_km,
    SUM(duration_seconds) as total_time_seconds,
    SUM(total_calories) as total_calories,
    AVG(avg_heart_rate) as avg_heart_rate,
    AVG(avg_speed_ms) as avg_speed_ms
FROM activities
GROUP BY user_id, sport;


-- ============================================================================
-- FUNÇÕES ÚTEIS
-- ============================================================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_activities_updated_at BEFORE UPDATE ON activities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_records_updated_at BEFORE UPDATE ON user_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

-- Para queries de analytics agregados
CREATE INDEX idx_activities_user_sport_date ON activities(user_id, sport, start_time DESC);

-- Para timeline
CREATE INDEX idx_activities_date ON activities(DATE(start_time));

-- Para busca geográfica (se usar PostGIS)
-- CREATE INDEX idx_activity_records_geography ON activity_records USING GIST(ST_MakePoint(longitude, latitude));


-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON TABLE activities IS 'Atividades físicas registradas por smartwatch';
COMMENT ON TABLE activity_records IS 'Pontos GPS e métricas por segundo/ponto da atividade';
COMMENT ON TABLE activity_metrics IS 'Métricas avançadas calculadas para cada atividade';
COMMENT ON TABLE activity_insights IS 'Insights automáticos gerados para cada atividade';
COMMENT ON TABLE user_records IS 'Recordes pessoais do usuário';
COMMENT ON COLUMN activity_records.latitude IS 'Latitude em graus decimais';
COMMENT ON COLUMN activity_records.longitude IS 'Longitude em graus decimais';

