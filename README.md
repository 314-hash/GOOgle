# Google TimesFM & ForecastOS — AI Forecasting & Decision Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Pytest Passed](https://img.shields.io/badge/tests-21%2F21%20passed-success.svg)](tests/forecastos/)

**ForecastOS** is a production-ready time-series forecasting platform, AI decision engine, and cryptographic provenance network built on top of **Google TimesFM 2.5** (200M parameter pretrained foundation model).

---

## 📚 Documentation Index

- 📖 **[USER.md](USER.md)**: End-User Manual & Step-by-Step Dashboard Guide.
- 📈 **[PITCH.md](PITCH.md)**: Commercialization Strategy, Pricing & B2B Pitch Deck.
- ⚙️ **[FORECASTOS.md](FORECASTOS.md)**: Full System Architecture & API Specification.

---

## ✨ Features

- **Pretrained Time-Series Foundation Model**: Zero-shot forecasting via Google TimesFM 2.5 PyTorch core.
- **Quantile Prediction Intervals**: 10 quantiles ($q_{10}$ to $q_{90}$) for uncertainty modeling.
- **WebChat AI Assistant**: Floating interactive web chat widget for conversational forecasting & queries.
- **Two-Phase Anomaly Detection**: Context Z-score detrending + Forecast Prediction Interval breach alerts.
- **AI Decision Agent**: Automatically translates numeric forecasts into business recommendations.
- **Cryptographic Provenance**: Deterministic SHA256 hashes anchored to EVM Smart Contracts (`ForecastAuditRegistry.sol`).
- **Interactive Dashboard**: Modern glassmorphic dark-mode web application with Chart.js charts and ABI inspection.

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv
.\.venv\Scripts\pip install fastapi uvicorn[standard] pydantic pandas numpy matplotlib sqlalchemy pytest httpx python-multipart
.\.venv\Scripts\pip install -e .
```

### 2. Launch Server & Dashboard

```bash
python -m forecastos.api.main
```

Access the dashboard at:  
👉 **Web Dashboard**: `http://localhost:8000/dashboard/`  
👉 **API Docs**: `http://localhost:8000/docs`  
👉 **Health Check**: `http://localhost:8000/health`

### 3. Run Test Suite

```bash
.\.venv\Scripts\pytest tests/forecastos/
```

---

## 📜 Smart Contract Architecture

ForecastOS includes `contracts/ForecastAuditRegistry.sol` for EVM provenance anchoring:

* **Contract Address**: `0x99a5e0195a92d7ae0730226ded132d5e58676050`
* **Bytecode Hash**: `0x7a6d4005c07dfd310334969358add2c0e3ee8353e0b3994317d7dd8551fd4fe7`
* **Smart Contract Verification Script**: `python forecastos/blockchain/deploy_and_verify.py`

---

## 📄 License

This repository is dual-structured: Google TimesFM core and ForecastOS application layer are released under the [Apache-2.0 License](LICENSE).
