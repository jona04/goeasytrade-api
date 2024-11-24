from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any
from core.signal_manager import SignalManager
from datetime import datetime

router = APIRouter()
signal_manager = SignalManager(total_tasks=10)  # Atualize o total_tasks conforme necessário

class RegisterSignalRequest(BaseModel):
    trade_id: str = Field(..., description="ID único do trade relacionado ao sinal.")
    signal: Dict[str, Any] = Field(
        ...,
        description="Dados do sinal que devem ser registrados, como preços e direção do mercado."
    )

@router.post("/register_signal")
def register_signal(request: RegisterSignalRequest):
    """
    Registra um novo sinal para o trade especificado.
    """
    try:
        signal_manager.register_signal(trade_id=request.trade_id, signal=request.signal)
        return {
            "status": "success",
            "message": f"Sinal registrado para o trade {request.trade_id}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process_signals")
def process_signals():
    """
    Processa os sinais coletados e decide quais operações abrir, se houver.
    """
    try:
        signal_manager.process_signals()
        return {
            "status": "success",
            "message": "Sinais processados com sucesso. Operações iniciadas conforme necessário."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))