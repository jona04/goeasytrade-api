from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreateTrade(BaseModel):
    open_order_id: int = Field(..., description="ID da ordem de abertura.")
    trade_id: int = Field(..., description="ID único do trade.")
    entry_price: float = Field(..., description="Preço de entrada no trade.")
    symbol: str = Field(..., description="Ativo a ser negociado, por exemplo, 'BTCUSDT'.")
    position_side: str = Field(..., description="'LONG' ou 'SHORT'.")
    quantity: float = Field(..., description="Quantidade a ser negociada.")
    stop_loss_order_id: Optional[int] = Field(None, description="ID da ordem de Stop Loss, se houver.")
    take_profit_order_id: Optional[int] = Field(None, description="ID da ordem de Take Profit, se houver.")
    activate: bool = Field(..., description="Se o trade está ativo.")
    remaining_quantity: Optional[float] = Field(None, description="Quantidade restante do trade.")
    close_type: Optional[str] = Field(None, description="Motivo do fechamento (ex: 'TP', 'SL').")
    take_profit: Optional[float] = Field(None, description="Preço de Take Profit.")
    stop_loss: Optional[float] = Field(None, description="Preço de Stop Loss.")
    break_even: bool = Field(..., description="Se o trade ativou o break-even.")
    timestamp: datetime = Field(..., description="Timestamp do trade.")