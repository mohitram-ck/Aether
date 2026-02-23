# ⚡ Aether — High-Frequency Financial Transaction Engine

A production-grade, event-driven financial transaction engine built for high concurrency, real-time fraud detection, and predictive load forecasting.

## 🏗️ Architecture
```
Client → FastAPI Gateway → Redis Stream → PostgreSQL Worker
                      ↓
              Analytics Engine (ARIMA Fraud Detection)
```

## 🚀 Tech Stack

| Layer | Technology |
|-------|------------|
| API Gateway | FastAPI, Python |
| Auth | JWT, OAuth 2.0, RBAC |
| Caching & Queue | Redis, Redis Streams |
| Database | PostgreSQL, SQLAlchemy |
| Analytics | ARIMA, Z-Score Anomaly Detection |
| Frontend | React, Recharts, Vite |
| Infrastructure | Docker, Alembic |

## ✨ Key Features

- **High-Throughput API Gateway** — Async FastAPI ingestion layer capable of processing 1,000+ mock transactions per second using asynchronous request handling and connection pooling
- **Identity Fortress** — JWT-based authentication with Redis token blacklisting, token caching for microsecond validation, and role-based access control (RBAC) to protect sensitive financial endpoints
- **Event-Driven Pipeline** — Every transaction is pushed into a Redis Stream immediately after ingestion, decoupling the API from the database and absorbing traffic spikes with zero lag to the user
- **ACID-Compliant Worker** — A background consumer pulls transactions from the Redis Stream in configurable batches and safely inserts them into PostgreSQL with full rollback support on failure
- **Fraud-Sensing Engine** — Time-series analysis using ARIMA forecasting and Z-score statistical detection to flag velocity spikes and unusual transaction amounts in real time
- **Live React Dashboard** — Full-stack frontend with login/register flow, transaction submission form, live transaction history table, fraud alert panel, and a load forecast chart

## 🖥️ Screenshots

> Dashboard with transaction history, fraud analysis panel, and ARIMA load forecast chart

## 🛠️ Running Locally

### Prerequisites
- Docker Desktop
- Python 3.11 (via Miniconda)
- Node.js 18+

### 1. Start Infrastructure
```bash
docker-compose up -d
```

### 2. Backend Setup
```bash
cd backend
conda activate aether
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Start Background Worker
```bash
cd backend
conda activate aether
python -m app.workers.transaction_worker
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 5. Open in Browser
| Service | URL |
|---------|-----|
| React Dashboard | http://localhost:5173 |
| API Docs (Swagger) | http://127.0.0.1:8000/docs |

## 📁 Project Structure
```
aether/
├── backend/
│   ├── app/
│   │   ├── api/              # Route handlers (auth, transactions, analytics)
│   │   ├── core/             # Config, Database, Security, Redis client
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic (auth, fraud, cache, analytics)
│   │   ├── workers/          # Redis Stream consumer worker
│   │   └── main.py           # FastAPI app entry point
│   ├── migrations/           # Alembic database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       └── App.jsx           # React dashboard
├── docker-compose.yml
└── README.md
```

## 🔐 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /auth/register | Register a new user | ❌ |
| POST | /auth/login | Login and receive JWT | ❌ |
| POST | /auth/logout | Blacklist token in Redis | ✅ |
| POST | /transactions/ | Submit a transaction | ✅ |
| GET | /transactions/ | List all transactions | ✅ |
| GET | /transactions/{id} | Get single transaction | ✅ |
| GET | /transactions/stream/length | Redis queue depth | ✅ |
| GET | /analytics/forecast | ARIMA forecast + fraud flags | ✅ |
| GET | /health | Health check | ❌ |

## 👤 Author
**Mohit** — [github.com/mohitram-ck](https://github.com/mohitram-ck)
