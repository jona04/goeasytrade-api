from fastapi import APIRouter, HTTPException
from core.config_assets_manager import ConfigAssetsManager

router = APIRouter()
manager = ConfigAssetsManager()

@router.get("/configs", summary="Lista todas as configurações")
def list_configs():
    configs = manager.list_configs()
    if not configs:
        return {"message": "Nenhuma configuração encontrada."}
    return {"configs": configs}

@router.get("/configs/{symbol}", summary="Consulta a configuração de um ativo")
def get_config(symbol: str):
    config = manager.get_config(symbol)
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuração para {symbol} não encontrada.")
    return config

@router.post("/configs", summary="Adiciona ou atualiza uma configuração")
def add_or_update_config(symbol: str, quantity: float, leverage: int):
    if quantity <= 0 or leverage <= 0:
        raise HTTPException(status_code=400, detail="Quantity e leverage devem ser maiores que zero.")
    manager.add_or_update_config(symbol, quantity, leverage)
    return {"message": f"Configuração para {symbol} atualizada com sucesso."}

@router.delete("/configs/{symbol}", summary="Remove a configuração de um ativo")
def remove_config(symbol: str):
    config = manager.get_config(symbol)
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuração para {symbol} não encontrada.")
    manager.remove_config(symbol)
    return {"message": f"Configuração para {symbol} removida com sucesso."}
