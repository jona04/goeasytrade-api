from pydantic import BaseModel
from typing import Any, Dict

class ClosePartialRequest(BaseModel):
    opened_trade: Dict[str, Any]  # Informações do trade aberto
    percentage: float             # Percentual da posição a ser encerrada