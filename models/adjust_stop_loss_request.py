from pydantic import BaseModel
from typing import Any, Dict

class AdjustStopLossRequest(BaseModel):
    opened_trade: Dict[str, Any]  # Informações do trade aberto
    new_sl_price: float           # Novo preço de Stop Loss