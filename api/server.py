from fastapi import APIRouter
from api.endpoints.trading import router as trading_router
from api.endpoints.technicals import router as technicals_router

app = APIRouter()

# Inclui os endpoints relacionados a trading e indicadores técnicos
app.include_router(trading_router, prefix="/trading")
app.include_router(technicals_router, prefix="/technicals")