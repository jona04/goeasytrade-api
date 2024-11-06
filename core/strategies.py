from abc import ABC, abstractmethod
import pandas as pd

class SignalStrategy(ABC):
    @abstractmethod
    def detect_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        pass

class Strategy1(SignalStrategy):
    def detect_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Implementação da estratégia 1
        # Modifica o DataFrame `df` e retorna
        return df

class Strategy2(SignalStrategy):
    def detect_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Implementação da estratégia 2
        # Modifica o DataFrame `df` e retorna
        return df

# Adicione outras classes de estratégia conforme necessário...

def get_strategy(strategy_type: int) -> SignalStrategy:
    if strategy_type == 1:
        return Strategy1()
    elif strategy_type == 2:
        return Strategy2()
    # Adicione outras estratégias conforme necessário
    else:
        raise ValueError(f"Strategy type {strategy_type} is not recognized.")
