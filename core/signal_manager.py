from collections import defaultdict
from typing import Dict
import pandas as pd
from data.database import DataDB

class SignalManager:
    def __init__(self, total_tasks, db):
        # Armazena sinais como um dicionário onde as chaves são os símbolos e o valor é uma lista de sinais
        self.signals = defaultdict(list)
        self.last_processed_timestamp = None
        self.total_tasks = total_tasks
        self.completed_tasks_count = 0
        self.db = DataDB()

    def register_signal(self, trade_id: str, signal: Dict):
        """Registra um sinal para um símbolo específico."""
        self.signals[trade_id].append(signal)

    def register_task_completion(self, timestamp):
        """Registra a conclusão de uma task e processa sinais quando todas as tasks completaram."""
        self.completed_tasks_count += 1
        if self.completed_tasks_count == self.total_tasks and (
            self.last_processed_timestamp is None
            or self.last_processed_timestamp != timestamp
        ):
            self.last_processed_timestamp = timestamp
            self.completed_tasks_count = 0
            self.process_signals()

    def add_priority_in_db(self):
        """
        Adiciona a tabela de prioridades ao banco de dados.
        A coleção será chamada de 'priority_criteria'.
        """
        priority_data = [
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.04},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.03},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.04},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.02},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.02},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.01},
            {"emaper_s": 20, "emaper_l": 50, "emaper_force": 5, "sl_percent": -0.04},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.01},
            {"emaper_s": 50, "emaper_l": 100, "emaper_force": 3, "sl_percent": -0.03},
            {"emaper_s": 10, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.04},
            {"emaper_s": 5, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.04},
            {"emaper_s": 5, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.04},
            {"emaper_s": 10, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.04},
            {"emaper_s": 10, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.03},
            {"emaper_s": 20, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.04},
            {"emaper_s": 20, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.03},
            {"emaper_s": 5, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.03},
            {"emaper_s": 5, "emaper_l": 100, "emaper_force": 2, "sl_percent": -0.04},
        ]

        self.db.delete_many("priority_criteria")  # Limpa a coleção antes de adicionar os novos dados
        self.db.add_many("priority_criteria", priority_data)
        print("Tabela de prioridades adicionada ao banco de dados.")


    def get_trade_params(self, trade_id: str) -> dict:
        """Recupera os parâmetros de trade do banco de dados com base no trade_id."""
        trade_params = self.db.query_single("active_traders", trade_id=trade_id)
        if not trade_params:
            return {}
        return trade_params

    def get_priority_table(self):
        """Recupera a tabela de prioridades do banco de dados."""
        priority_data = self.db.query_all("priority_criteria")
        return pd.DataFrame(priority_data)

    def select_top_signals(self, signals: dict, top_n=10):
        """
        Seleciona os 10 melhores sinais com base nos critérios do banco de dados.
        Se houver menos de 10 sinais, retorna todos.
        """
        decoded_signals = []
        priority_table = self.get_priority_table()

        # Recupera os parâmetros do banco de dados e emparelha com os sinais
        for trade_id, signal_list in signals.items():
            trade_params = self.get_trade_params(trade_id)
            for signal in signal_list:
                decoded_signals.append((trade_params, signal))

        # Se o número de sinais for menor ou igual a `top_n`, retorna todos
        if len(decoded_signals) <= top_n:
            return decoded_signals

        # Prioriza com base na tabela
        ranked_signals = []
        for trade_params, signal in decoded_signals:
            for index, row in priority_table.iterrows():
                # Verifica se os parâmetros coincidem com a tabela
                if (
                    trade_params.get("emaper_s") == row["emaper_s"]
                    and trade_params.get("emaper_l") == row["emaper_l"]
                    and trade_params.get("emaper_force") == row["emaper_force"]
                    and trade_params.get("sl_percent") == row["sl_percent"]
                ):
                    # Inclui a prioridade com base na posição na tabela
                    ranked_signals.append((index, trade_params, signal))
                    break

        # Ordena por prioridade (índice da tabela)
        ranked_signals.sort(key=lambda x: x[0])

        # Seleciona os top_n sinais
        top_signals = ranked_signals[:top_n]

        # Retorna apenas os parâmetros e sinais
        return [(trade_params, signal) for _, trade_params, signal in top_signals]

    def process_signals(self):
        """Processa sinais coletados e decide qual operação abrir, se houver."""
        print("Processa sinal!")
        signals = self.get_signals()

        # Seleciona os 10 melhores sinais com base nos critérios do banco de dados
        top_signals = self.select_top_signals(signals, top_n=10)

        # A lógica de decisão com os sinais selecionados
        if top_signals:
            for trade_params, signal in top_signals:
                print("")
                print("#" * 20)
                print(f"Abrindo operação para o sinal {signal}")
                print("#" * 20)
                print("")
                # Aqui você chamaria a função que executa a ordem real (abrir posição)

    def get_signals(self):
        """Retorna todos os sinais registrados e limpa o registro para o próximo candle."""
        signals = dict(self.signals)
        self.signals.clear()  # Limpa os sinais após a consulta
        return signals
