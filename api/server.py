from fastapi import APIRouter
from api.endpoints.trading import router as trading_router
from api.endpoints.config_assets import router as config_assets_router
from api.endpoints.config_system import router as config_system_router
from api.endpoints.operations import router as operations_router
from api.endpoints.signals import router as signals_router
from api.endpoints.pair_trading import router as pair_trading_router
from api.endpoints.config_pair_assets import router as config_pair_assets_router
from api.endpoints.config_pair_system import router as config_pair_system_router
from api.endpoints.signals_pair import router as signals_pair_router

app = APIRouter()

# Inclui os endpoints relacionados a trading e indicadores técnicos
app.include_router(trading_router, prefix="/trading", tags=["Trading"])
app.include_router(config_assets_router, prefix="/api", tags=["Assets Configs"])
app.include_router(config_system_router, prefix="/api", tags=["System Configs"])
app.include_router(operations_router, prefix="/operations", tags=["Operations"])
app.include_router(signals_router, prefix="/signals", tags=["Signals"])
app.include_router(pair_trading_router, prefix="/pair-trading", tags=["Pair Trading"])
app.include_router(config_pair_assets_router, prefix="/pair", tags=["Pair Assets Configs"])
app.include_router(config_pair_system_router, prefix="/pair", tags=["Pair System Configs"])
app.include_router(signals_pair_router, prefix="/pair", tags=["Signals Pair"])
