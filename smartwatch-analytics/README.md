# 🏃 Smartwatch Analytics Platform

Advanced analytics platform for smartwatch data (Garmin, Strava, etc.) with AI-powered insights.

## 🚀 Features

- **Enhanced FIT Parser**: Extract 100% of data from FIT files (16x more data than basic integrations)
- **Advanced Metrics**: HR Drift, Consistency Score, Fatigue Index, and 12+ categories
- **GPS Maps**: Full GPS tracking with heatmaps and route comparison
- **Auto Insights**: AI-generated personalized recommendations
- **REST API**: 40+ endpoints for complete integration
- **Multi-Provider**: Garmin (active), Strava (coming soon)

## 📊 Tech Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (schema included)
- **Parser**: Garmin FIT SDK + Custom Enhanced Parser
- **Deploy**: Railway / Render / Docker

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Garmin API credentials
```

### 3. Run Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Test API

Open http://localhost:8000/docs for Swagger UI

## 📁 Project Structure

```
smartwatch-analytics/
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── database/     # PostgreSQL schema
│   │   ├── models/       # Pydantic models
│   │   └── services/     # Business logic
│   └── requirements.txt
├── core/
│   ├── enhanced_fit_parser.py  # FIT file parser
│   ├── metrics_engine.py        # Metrics calculation
│   └── fit_creator.py           # Workout creation
└── uploads/              # Temporary FIT files
```

## 🔧 Configuration

Required environment variables:

```bash
# Garmin API
GARMIN_CONSUMER_KEY=your_key
GARMIN_CONSUMER_SECRET=your_secret

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Server
PORT=8000
ENVIRONMENT=development
```

## 📡 API Endpoints

### Activities
- `POST /activities/process-activity` - Process activity from webhook
- `GET /activities/request-sync` - Request backfill from Garmin

### Analytics
- `GET /analytics/summary` - Overall summary
- `GET /analytics/records` - Personal records
- `GET /analytics/timeline` - Historical progression

### Maps
- `GET /maps/{id}/geojson` - GPS route (GeoJSON)
- `GET /maps/{id}/heatmap-data` - Metric heatmap

### Auth
- `GET /auth/garmin/authorize` - OAuth flow
- `GET /auth/garmin/callback` - OAuth callback

## 🐳 Docker Deploy

```bash
docker-compose up -d
```

## 📝 License

MIT License - see LICENSE file

## 🤝 Contributing

Pull requests welcome! Please read CONTRIBUTING.md first.

## 📧 Contact

For questions: [your-email]

