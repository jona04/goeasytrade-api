from pydantic import BaseModel
from typing import Any, Dict

class BreakEvenRequest(BaseModel):
    opened_trade: Dict[str, Any]  # Informações do trade aberto
    current_price: float          # Preço atual do mercado