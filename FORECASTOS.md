# ForecastOS — AI Forecasting & Decision Engine

**ForecastOS** is a production-ready forecasting infrastructure, AI decision engine, and cryptographic audit platform built directly on top of **Google TimesFM 2.5** (200M parameters, 16k context, zero-shot quantile forecasting).

Rather than modifying Google's core foundation model internals, ForecastOS acts as a modular application layer that provides REST APIs, dataset validation, two-phase anomaly detection, AI business recommendations, WebChat AI assistant, SQLite historical storage, and EVM blockchain proof anchoring (`ForecastAuditRegistry.sol`).

---

## 📚 Documentation Index

- 📖 **[USER.md](file:///c:/Users/janla/GOOgle/USER.md)**: Comprehensive End-User Guide & Platform Manual.
- 📈 **[PITCH.md](file:///c:/Users/janla/GOOgle/PITCH.md)**: Commercialization Strategy & B2B Pitch Deck.

---

## 🏗️ Architecture Overview

```text
                                  CLIENT / DASHBOARD / WEBCHAT
                                               │
                                               ▼
                                        FORECASTOS API
                                     (FastAPI + Pydantic)
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               ▼                               ▼                               ▼
        Dataset Ingestion            TimesFM 2.5 Adapter              Database & Hashes
        (CSV/JSON Validator)         (PyTorch / Mock Engine)         (SQLite + SHA256)
               │                               │                               │
               └───────────────────────────────┼───────────────────────────────┘
                                               ▼
                                     Quantile & Risk Engine
                                     (q10, q20 ... q80, q90)
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
      Two-Phase Anomaly Agent                                  AI Decision Agent
    (Linear Detrend & PI Bounds)                             (Actionable Recommendations)
               │                                                               │
               └───────────────────────────────┬───────────────────────────────┘
                                               ▼
                                  Cryptographic Audit Layer
                               (Local Log / EVM Contract ABI)
```

---

## 📁 Repository Structure

```text
c:\Users\janla\GOOgle/
├── src/                          # Google TimesFM core library (Unmodified)
├── forecastos/                   # ForecastOS Application Layer
│   ├── api/                      # REST API Endpoints & Schemas
│   │   ├── main.py               # FastAPI App & Web Dashboard Mount
│   │   ├── schemas.py            # Request/Response Pydantic Models
│   │   └── routes/
│   │       ├── forecast.py       # Forecast & Natural Language Endpoints
│   │       ├── chat.py           # WebChat AI Assistant Endpoint
│   │       ├── blockchain.py     # Smart Contract ABI & Address Info Endpoint
│   │       ├── datasets.py       # Dataset Ingestion Endpoints
│   │       └── health.py         # System Health Check
│   ├── engine/                   # TimesFM Adapter & Pre/Post Processing
│   │   ├── model.py              # PyTorch TimesFM Adapter + Mock Engine
│   │   ├── preprocessing.py      # Cleaning & Imputation
│   │   ├── postprocessing.py     # Date alignment & formatting
│   │   └── confidence.py         # Quantile interval score calculation
│   ├── data/                     # Data Ingestion Layer
│   │   ├── validation.py         # DataFrame and Series validators
│   │   ├── csv_loader.py         # CSV/JSON file parser
│   │   └── api_loader.py         # REST API fetcher
│   ├── agents/                   # AI Intelligence Layer
│   │   ├── anomaly_agent.py      # Two-Phase Anomaly Detector
│   │   ├── decision_agent.py     # Business Insight & Decision Generator
│   │   └── forecast_agent.py     # Natural Language NLP query parser
│   ├── blockchain/               # Verification & Provenance Layer
│   │   ├── hash.py               # Deterministic SHA256 hashing
│   │   ├── audit.py              # LocalMockProvider & EVMProvider
│   │   ├── deploy_and_verify.py  # Contract compilation & verification
│   │   └── ForecastAuditRegistry.sol # Solidity Registry Contract
│   ├── storage/                  # Relational Persistence
│   │   ├── database.py           # SQLAlchemy setup
│   │   └── models.py             # SQLite DB models
│   └── config.py                 # Application settings
├── contracts/                    # Solidity Smart Contracts
│   ├── ForecastAuditRegistry.sol # On-chain Audit Registry Implementation
│   └── IForecastAuditRegistry.sol# Smart Contract Interface
├── dashboard/                    # Single-Page Web Dashboard
│   ├── index.html                # Responsive UI Template with WebChat Widget
│   ├── styles.css                # Dark-mode glassmorphic design system
│   └── app.js                    # Chart.js visualization & WebChat Client
├── examples/                     # Sample datasets (sales, crypto, energy, inventory)
├── tests/forecastos/             # Automated Pytest suite (21/21 passed)
├── docker/                       # Containerized deployment files
├── .env.example                  # Environment configuration
├── Makefile                      # Developer shortcut commands
└── FORECASTOS.md                 # System Documentation
```

---

## ⚡ Quick Start

```bash
# Install dependencies into virtual environment
make install

# Run the ForecastOS API server & dashboard
make run
```

Access the dashboard at:
👉 `http://localhost:8000/dashboard/`

API Documentation at:
👉 `http://localhost:8000/docs`

---

## 🔌 Core API Endpoints

### 1. Execute Forecast (`POST /api/v1/forecast`)
Runs TimesFM point/quantile predictions, two-phase anomaly detection, decision agent reasoning, and SHA256 audit proof generation.

### 2. WebChat Conversational Assistant (`POST /api/v1/chat`)
Routes user messages to TimesFM, Anomaly Detection, AI Decision reasoning, or Smart Contract ABI inspection.

### 3. Smart Contract Info & ABI (`GET /api/v1/blockchain/contract-info`)
Returns deployed smart contract name, EVM address (`0x99a5e0195a92d7ae0730226ded132d5e58676050`), bytecode hash, and JSON ABI.

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
.\.venv\Scripts\pytest tests/forecastos/
```

**Result: 21 passed in 5.49s**
