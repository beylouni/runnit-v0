# API Documentation

Documentação completa da API REST do sistema de integração Garmin.

## 🏠 Base URL

```
http://localhost:8002
```

## 📋 Endpoints

### Health & Status

#### GET `/health`
Health check da aplicação.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00.000000",
  "service": "garmin-integration-api"
}
```

#### GET `/status`
Status detalhado da aplicação.

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2024-01-01T10:00:00.000000",
  "services": {
    "api": "running",
    "garmin_integration": "connected",
    "database": "not_implemented",
    "redis": "not_implemented"
  },
  "environment": "development"
}
```

### Workouts (Treinos)

#### POST `/workouts/`
Criar um novo treino.

**Request Body:**
```json
{
  "nome_do_treino": "Meu Treino 5k",
  "descricao": "Treino para melhorar pace",
  "passos": [
    {
      "nome_passo": "Aquecimento 10 min",
      "tipo": "aquecimento",
      "duracao_tipo": "tempo",
      "duracao_valor": 600
    },
    {
      "nome_passo": "Corrida 5km",
      "tipo": "corrida",
      "duracao_tipo": "distancia",
      "duracao_valor": 5000
    },
    {
      "nome_passo": "Desaquecimento 5 min",
      "tipo": "desaquecimento",
      "duracao_tipo": "tempo",
      "duracao_valor": 300
    }
  ]
}
```

**Response:**
```json
{
  "id": "uuid-do-treino",
  "nome_do_treino": "Meu Treino 5k",
  "descricao": "Treino para melhorar pace",
  "status": "created",
  "created_at": "2024-01-01T10:00:00.000000",
  "updated_at": "2024-01-01T10:00:00.000000"
}
```

#### GET `/workouts/`
Listar todos os treinos.

**Response:**
```json
{
  "total": 1,
  "workouts": [
    {
      "id": "uuid-do-treino",
      "nome_do_treino": "Meu Treino 5k",
      "status": "created",
      "created_at": "2024-01-01T10:00:00.000000"
    }
  ]
}
```

#### GET `/workouts/{id}`
Obter detalhes de um treino específico.

**Response:**
```json
{
  "id": "uuid-do-treino",
  "nome_do_treino": "Meu Treino 5k",
  "descricao": "Treino para melhorar pace",
  "passos": [...],
  "status": "created",
  "created_at": "2024-01-01T10:00:00.000000",
  "updated_at": "2024-01-01T10:00:00.000000"
}
```

#### POST `/workouts/{id}/send`
Enviar treino para Garmin Connect.

**Response:**
```json
{
  "id": "uuid-do-treino",
  "status": "sent",
  "garmin_id": "garmin_workout_id",
  "sent_at": "2024-01-01T10:00:00.000000"
}
```

#### GET `/workouts/{id}/fit`
Download do arquivo FIT do treino.

**Response:** Arquivo .FIT

### Activities (Atividades)

#### GET `/activities/`
Listar atividades disponíveis.

**Response:**
```json
{
  "total": 2,
  "activities": [
    {
      "id": "sim_001",
      "name": "Corrida Matinal",
      "type": "RUNNING",
      "startTime": "2024-01-01T10:00:00Z",
      "distance": 5000,
      "duration": 1800
    }
  ]
}
```

#### GET `/activities/{id}`
Obter detalhes de uma atividade.

**Response:**
```json
{
  "id": "sim_001",
  "name": "Corrida Matinal",
  "type": "RUNNING",
  "startTime": "2024-01-01T10:00:00Z",
  "distance": 5000,
  "duration": 1800,
  "processed": false
}
```

#### POST `/activities/{id}/download`
Baixar arquivo FIT da atividade.

**Response:**
```json
{
  "id": "sim_001",
  "status": "downloaded",
  "file_path": "/path/to/activity.fit",
  "downloaded_at": "2024-01-01T10:00:00.000000"
}
```

#### GET `/activities/{id}/fit`
Download do arquivo FIT da atividade.

**Response:** Arquivo .FIT

#### POST `/activities/{id}/process`
Processar dados da atividade.

**Response:**
```json
{
  "id": "sim_001",
  "status": "processed",
  "data": {
    "total_distance": 5000,
    "total_time": 1800,
    "average_pace": 216,
    "calories": 450,
    "max_heart_rate": 165,
    "average_heart_rate": 145
  },
  "processed_at": "2024-01-01T10:00:00.000000"
}
```

### Authentication

#### GET `/auth/status`
Status da autenticação.

**Response:**
```json
{
  "status": "simulated",
  "message": "Sistema de autenticação em desenvolvimento",
  "phase": "1",
  "features": [
    "Simulação de autenticação",
    "Sistema de usuários - Fase 2",
    "JWT tokens - Fase 2",
    "OAuth 2.0 com Garmin - Fase 2"
  ]
}
```

### Webhooks

#### POST `/webhooks/garmin/activity`
Webhook para notificações de atividades (futuro).

#### POST `/webhooks/garmin/workout`
Webhook para notificações de treinos (futuro).

## 🔐 Autenticação

Atualmente o sistema usa simulação de autenticação. Na implementação real, será usado OAuth 2.0 com PKCE.

## 📝 Códigos de Status

- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Bad Request
- `404` - Não encontrado
- `500` - Erro interno do servidor

## 🚀 Swagger UI

Documentação interativa disponível em:
```
http://localhost:8002/docs
```

## 📄 Licença

MIT License 