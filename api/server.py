from fastapi import APIRouter
from api.endpoints.trading import router as trading_router
from api.endpoints.technicals import router as technicals_router
from endpoints.configs import router as configs_router

app = APIRouter()

# Inclui os endpoints relacionados a trading e indicadores técnicos
app.include_router(trading_router, prefix="/trading")
app.include_router(technicals_router, prefix="/technicals")
app.include_router(configs_router, prefix="/api")