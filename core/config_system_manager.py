from data.database import DataDB

class ConfigSystemManager:
    def __init__(self):
        """
        Gerenciador do collection `config_system`.
        """
        self.db = DataDB()

    def update_system_config(self, total_earnings: float, percentage_of_total: float, breakeven_profit_threshold: float):
        """
        Atualiza ou cria as configurações gerais do sistema.
        :param total_earnings: Ganhos totais do sistema.
        :param percentage_of_total: Percentual do total usado para operações.
        :param breakeven_profit_threshold: Percentual de lucro para ativar o Break Even.
        """
        try:
            config = {
                "total_earnings": total_earnings,
                "percentage_of_total": percentage_of_total,
                "breakeven_profit_threshold": breakeven_profit_threshold,
            }
            self.db.update_one("config_system", {}, {"$set": config}, upsert=True)
            print("Configurações gerais atualizadas:", config)
        except Exception as e:
            print(f"Erro ao atualizar configurações gerais: {e}")

    def get_system_config(self) -> dict:
        """
        Obtém as configurações gerais do sistema.
        :return: Configurações gerais ou None se não existir.
        """
        try:
            config = self.db.query_single("config_system")
            if not config:
                raise ValueError("Nenhuma configuração geral encontrada.")
            return config
        except Exception as e:
            print(f"Erro ao obter configurações gerais: {e}")
            return {}

    def remove_system_config(self):
        """
        Remove as configurações gerais do sistema.
        """
        try:
            self.db.delete_many("config_system", {})
            print("Configurações gerais removidas.")
        except Exception as e:
            print(f"Erro ao remover configurações gerais: {e}")
