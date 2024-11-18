from fastapi import APIRouter
from api.endpoints.trading import router as trading_router
from api.endpoints.technicals import router as technicals_router
from api.endpoints.config_assets import router as config_assets_router
from api.endpoints.config_system import router as config_system_router


app = APIRouter()

# Inclui os endpoints relacionados a trading e indicadores técnicos
app.include_router(trading_router, prefix="/trading", tags=["Trading"])
app.include_router(technicals_router, prefix="/technicals", tags=["Technicals"])
app.include_router(config_assets_router, prefix="/api", tags=["Assets Configs"])
app.include_router(config_system_router, prefix="/api", tags=["System Configs"])
