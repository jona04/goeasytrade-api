from data.database import DataDB

class ConfigPairSystemManager:
    def __init__(self):
        """
        Gerenciador do collection `config_pair_system`.
        """
        self.db = DataDB()

    def update_system_config(self, 
                            available_balance: float, 
                            percentage_of_total: float, 
                            breakeven_profit_threshold: float):
        """
        Atualiza ou cria as configurações gerais do sistema.
        :param available_balance: Ganhos totais do sistema.
        :param percentage_of_total: Percentual do total usado para operações.
        :param breakeven_profit_threshold: Percentual de lucro para ativar o Break Even.
        :param use_top_signals: Indica se os sinais prioritários devem ser usados.
        """
        try:
            config = {
                "available_balance": available_balance,
                "percentage_of_total": percentage_of_total,
                "breakeven_profit_threshold": breakeven_profit_threshold,
            }
            self.db.update_one("config_pair_system", {}, config, upsert=True)
            print("Configurações gerais atualizadas:", config)
        except Exception as e:
            print(f"Erro ao atualizar configurações gerais: {e}")

    def update_system_available_balance(self, available_balance: float):
        """
        Atualiza apenas o campo available_balance na configuração do sistema.
        :param available_balance: Ganhos totais do sistema.
        """
        try:
            print(f"Atualiza saldo atual de {available_balance} no banco de dados!")
            
            # Atualizar apenas o campo available_balance
            self.db.update_one(
                "config_pair_system",
                {},  # Atualiza o primeiro documento encontrado
                {"$set": {"available_balance": available_balance}},  # Atualiza apenas available_balance
                upsert=True  # Cria o documento se não existir
            )
            print(f"Campo 'available_balance' atualizado para: {available_balance}")
        except Exception as e:
            print(f"Erro ao atualizar 'available_balance': {e}")
            
    def get_system_config(self) -> dict:
        """
        Obtém as configurações gerais do sistema.
        :return: Configurações gerais ou None se não existir.
        """
        try:
            config = self.db.query_single("config_pair_system")
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
            self.db.delete_many("config_pair_system", {})
            print("Configurações gerais removidas.")
        except Exception as e:
            print(f"Erro ao remover configurações gerais: {e}")
