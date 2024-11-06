# core/signal_manager.py

from collections import defaultdict
from typing import Dict, List

class SignalManager:
    def __init__(self, total_tasks):
        # Armazena sinais como um dicionário onde as chaves são os símbolos e o valor é uma lista de sinais
        self.signals = defaultdict(list)
        self.last_processed_timestamp = None
        self.total_tasks = total_tasks
        self.completed_tasks_count = 0
        
    def register_signal(self, symbol: str, signal: Dict):
        """Registra um sinal para um símbolo específico."""
        self.signals[symbol].append(signal)

    def register_task_completion(self, timestamp):
        """Registra a conclusão de uma task e processa sinais quando todas as tasks completaram."""
        self.completed_tasks_count += 1
        if self.completed_tasks_count == self.total_tasks and (self.last_processed_timestamp is None or self.last_processed_timestamp != timestamp):
            self.last_processed_timestamp = timestamp
            self.completed_tasks_count = 0
            self.process_signals()
            
    def process_signals(self):
        """Processa sinais coletados e decide qual operação abrir, se houver."""
        # Verifica se o timestamp é novo em relação ao último processado
        print("Processa sinal!")
        signals = self.get_signals()
        
        # Lógica de decisão: aqui vamos verificar qual sinal é o mais forte ou atende aos critérios
        chosen_signal = None
        for symbol, signal_list in signals.items():
            for signal in signal_list:
                if signal['SIGNAL_UP'] != 0 or signal['SIGNAL_DOWN'] != 0:
                    # Exemplo: selecione o primeiro sinal encontrado. Aqui pode-se aplicar lógica mais complexa
                    chosen_signal = signal
                    break
            if chosen_signal:
                break

        if chosen_signal:
            # A lógica para abrir a posição com base no `chosen_signal`
            print("")
            print("#"*20)
            print(f"Abrindo operação para o símbolo: {chosen_signal['symbol']} com sinal {chosen_signal}")
            print("#"*20)
            print("")
            # Aqui você chamaria a função que executa a ordem real (abrir posição)
    
    
    def get_signals(self):
        """Retorna todos os sinais registrados e limpa o registro para o próximo candle."""
        signals = dict(self.signals)
        self.signals.clear()  # Limpa os sinais após a consulta
        return signals
