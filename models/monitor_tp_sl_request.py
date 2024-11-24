from pydantic import BaseModel, Field
from typing import Optional

class MonitorTpSlRequest(BaseModel):
    id: int = Field(..., alias="_id", description="ID único do trade.")  # Uso de alias
    symbol: str = Field(..., description="Símbolo do ativo (ex: 'BTCUSDT').")
    remaining_quantity: float = Field(..., description="Quantidade restante do trade.")
    take_profit: Optional[float] = Field(None, description="Preço do Take Profit (opcional).")
    stop_loss: Optional[float] = Field(None, description="Preço do Stop Loss (opcional).")
    activate: bool = Field(..., description="Indica se o trade está ativo ou inativo.")
