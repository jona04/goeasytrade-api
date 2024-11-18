from data.database import DataDB
from typing import Optional

class ConfigAssetsManager:
    def __init__(self):
        """
        Gerenciador do collection `config_assets`.
        """
        self.db = DataDB()

    def add_or_update_config(self, symbol: str, quantity: float, leverage: int):
        """
        Adiciona ou atualiza a configuração de um ativo.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :param quantity: Quantidade padrão para o ativo.
        :param leverage: Alavancagem padrão para o ativo.
        """
        try:
            if not symbol or not isinstance(quantity, (int, float)) or not isinstance(leverage, int):
                raise ValueError("Dados inválidos para configuração.")

            self.db.update_one(
                "config_assets",
                {"symbol": symbol},
                {"symbol": symbol, "quantity": quantity, "leverage": leverage},
                upsert=True
            )
            print(f"Configuração atualizada para {symbol}.")
        except Exception as e:
            print(f"Erro ao adicionar/atualizar configuração para {symbol}: {e}")

    def get_config(self, symbol: str) -> Optional[dict]:
        """
        Obtém a configuração de um ativo específico.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :return: Configuração do ativo ou None.
        """
        try:
            return self.db.query_single("config_assets", symbol=symbol)
        except Exception as e:
            print(f"Erro ao obter configuração para {symbol}: {e}")
            return None

    def list_configs(self) -> list:
        """
        Lista todas as configurações.
        :return: Lista de configurações.
        """
        try:
            return self.db.query_all("config_assets")
        except Exception as e:
            print(f"Erro ao listar configurações: {e}")
            return []

    def remove_config(self, symbol: str):
        """
        Remove a configuração de um ativo.
        :param symbol: Ativo (ex: 'ADAUSDT').
        """
        try:
            self.db.delete_single("config_assets", symbol=symbol)
            print(f"Configuração removida para {symbol}.")
        except Exception as e:
            print(f"Erro ao remover configuração para {symbol}: {e}")
