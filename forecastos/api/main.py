import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from forecastos import __version__
from forecastos.api.routes import datasets, forecast, health, blockchain, chat
from forecastos.storage.database import init_db

# Initialize DB tables on startup
init_db()

app = FastAPI(
    title="ForecastOS API",
    description="AI Forecasting & Decision Engine built on Google TimesFM 2.5 foundation model.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local dashboard development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(forecast.router)
app.include_router(blockchain.router)
app.include_router(chat.router)

# Mount Dashboard static files if dashboard directory exists
dashboard_dir = Path(__file__).resolve().parent.parent.parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")


@app.get("/")
def root():
    return {
        "app": "ForecastOS",
        "version": __version__,
        "engine": "TimesFM 2.5",
        "docs": "/docs",
        "dashboard": "/dashboard/",
    }


if __name__ == "__main__":
    import uvicorn
    from forecastos.config import settings

    uvicorn.run(
        "forecastos.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
