from fastapi import FastAPI, Depends
from api.server import app as api_app
from core.instances import trader_manager, pair_trader_manager
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await trader_manager.init_binance_client()
    await pair_trader_manager.init_binance_client()
    yield
    await trader_manager.close_binance_client()
    await pair_trader_manager.close_binance_client()


# Inicialize o FastAPI com o lifespan
app = FastAPI(lifespan=lifespan)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas do API
app.include_router(api_app)
