from pydantic import BaseModel
from typing import Any, Dict, Optional

class MonitorTpSlRequest(BaseModel):
    _id: int  # ID único do trade
    symbol: str  # Símbolo do ativo (ex: 'BTCUSDT')
    remaining_quantity: float  # Quantidade restante do trade
    take_profit: Optional[float] = None  # Preço do Take Profit (opcional)
    stop_loss: Optional[float] = None  # Preço do Stop Loss (opcional)
    activate: bool  # Status do trade (ativo ou inativo)