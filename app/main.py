from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.api import auth, strategies, market_data, schwab, indicators
from app.core.config import settings
from app.services.polygon_service import initialize_polygon_websocket, run_polygon_websocket, shutdown_polygon_websocket
import asyncio

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

security = HTTPBearer()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(strategies.router, prefix="/api/v1", tags=["strategies"])
app.include_router(market_data.router, prefix="/api/v1", tags=["market_data"])
app.include_router(schwab.router, prefix="/api/v1", tags=["schwab"])
app.include_router(indicators.router, prefix="/api/v1", tags=["indicators"])

def lifespan(app: FastAPI):
    async def startup_event():
        await initialize_polygon_websocket()
        asyncio.create_task(run_polygon_websocket())

    async def shutdown_event():
        await shutdown_polygon_websocket()

    return startup_event, shutdown_event

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)