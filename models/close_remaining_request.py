from pydantic import BaseModel, Field
from typing import Optional

class CloseRemainingRequest(BaseModel):
    id: int = Field(..., alias="_id", description="ID único do trade.")  # Uso de alias
    symbol: str = Field(..., description="Símbolo do ativo (ex: 'BTCUSDT').")
    position_side: str = Field(..., description="'LONG' ou 'SHORT'.")
    remaining_quantity: float = Field(..., description="Quantidade restante da posição.")
    reason: str = Field(..., description="Motivo do encerramento ('TP' ou 'Break Even').")
