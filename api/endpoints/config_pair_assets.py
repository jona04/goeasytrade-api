from fastapi import APIRouter, HTTPException
from core.config_pair_assets_manager import ConfigPairAssetsManager

router = APIRouter()
manager = ConfigPairAssetsManager()

@router.get("/asset-configs", summary="Lista todas as configurações")
def list_configs():
    configs = manager.list_configs()
    if not configs:
        return {"message": "Nenhuma configuração encontrada."}
    return {"configs": configs}

@router.get("/asset-configs/{symbol}", summary="Consulta a configuração de um ativo")
def get_config(symbol: str):
    config = manager.get_config(symbol)
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuração para {symbol} não encontrada.")
    return config

@router.post("/asset-configs", summary="Adiciona ou atualiza uma configuração")
def add_or_update_config(symbol: str, leverage: int):
    if leverage <= 0:
        raise HTTPException(status_code=400, detail="Leverage devem ser maiores que zero.")
    manager.add_or_update_config(symbol, leverage)
    return {"message": f"Configuração para {symbol} atualizada com sucesso."}

@router.delete("/asset-configs/{symbol}", summary="Remove a configuração de um ativo")
def remove_config(symbol: str):
    config = manager.get_config(symbol)
    if not config:
        raise HTTPException(status_code=404, detail=f"Configuração para {symbol} não encontrada.")
    manager.remove_config(symbol)
    return {"message": f"Configuração para {symbol} removida com sucesso."}
