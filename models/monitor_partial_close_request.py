from pydantic import BaseModel, Field
from typing import Dict

class MonitorPartialCloseRequest(BaseModel):
    symbol: str = Field(..., description="Símbolo do ativo monitorado, por exemplo, 'BTCUSDT'.")
    candle_data: Dict[str, float] = Field(
        ...,
        description=(
            "Dados do candle atual, um dicionário contendo informações como 'Close', 'High', 'Low', 'Open', e 'Volume'. "
            "Exemplo: {\"Close\": 27300.5, \"High\": 27500.0, \"Low\": 27000.0, \"Open\": 27100.0, \"Volume\": 1200.5}."
        )
    )