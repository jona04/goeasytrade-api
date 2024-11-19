from fastapi import APIRouter, HTTPException
from core.config_system_manager import ConfigSystemManager

router = APIRouter()
manager = ConfigSystemManager()

@router.get("/system-configs", summary="Obtém as configurações gerais do sistema")
def get_system_config():
    config = manager.get_system_config()
    if not config:
        raise HTTPException(status_code=404, detail="Nenhuma configuração encontrada.")
    return config

@router.post("/system-configs", summary="Atualiza ou cria as configurações gerais")
def update_system_config(total_earnings: float, percentage_of_total: float, breakeven_profit_threshold: float):
    if total_earnings < 0 or percentage_of_total < 0:
        raise HTTPException(status_code=400, detail="Os valores devem ser positivos.")
    manager.update_system_config(total_earnings, percentage_of_total, breakeven_profit_threshold)
    return {
        "message": "Configurações gerais atualizadas com sucesso.",
        "total_earnings": total_earnings,
        "percentage_of_total": percentage_of_total,
    }

@router.delete("/system-configs", summary="Remove as configurações gerais")
def remove_system_config():
    config = manager.get_system_config()
    if not config:
        raise HTTPException(status_code=404, detail="Nenhuma configuração encontrada para remover.")
    manager.remove_system_config()
    return {"message": "Configurações gerais removidas com sucesso."}
