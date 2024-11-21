from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


class SignalStrategy(ABC):
    @abstractmethod
    def detect_signals(
        self, df: pd.DataFrame, emaper_force
    ) -> pd.DataFrame:
        pass


class Strategy1(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force
    ) -> pd.DataFrame:
        """
        Função para detectar sinais de compra e venda com base no cruzamento de
        Average_EMA_percent_ema_short e Average_EMA_percent_ema_long.
        
        Compra ocorre quando Average_EMA_percent_ema_short cruza para cima de Average_EMA_percent_ema_long,
        com Average_EMA_percent_ema_short abaixo de EMA_percent_s_force.
        
        Venda ocorre quando Average_EMA_percent_ema_short cruza para baixo de Average_EMA_percent_ema_long,
        com Average_EMA_percent_ema_short acima de EMA_percent_s_force.
        
        Operação é interrompida quando Average_EMA_percent_ema_short cruza zero no sentido oposto da operação.
        """

        # Obtém os valores das colunas necessárias
        avg_ema_short_values = df['Average_EMA_percent_ema_short'].values
        avg_ema_long_values = df['Average_EMA_percent_ema_long'].values

        # Vetores de sinal de compra e venda
        signal_up = np.zeros(len(df), dtype=int)
        signal_down = np.zeros(len(df), dtype=int)
        signal_up_first = np.zeros(len(df), dtype=int)
        signal_down_first = np.zeros(len(df), dtype=int)

        # Itera sobre o DataFrame a partir do segundo valor
        for i in range(1, len(df)):
            # Valores atuais e anteriores
            avg_ema_short = avg_ema_short_values[i]
            avg_ema_short_prev = avg_ema_short_values[i-1]
            avg_ema_long = avg_ema_long_values[i]
            avg_ema_long_prev = avg_ema_long_values[i-1]
            
            # Detecção de cruzamento para compra
            if (
                avg_ema_short_prev < avg_ema_long_prev and  # short estava abaixo de long
                avg_ema_short > avg_ema_long and  # short cruzou para cima de long
                avg_ema_short < -emaper_force  # short está abaixo do EMA_percent_s_force
            ):
                signal_up[i] = 1  # Marca o ponto de compra
                signal_up_first[i] = 1

            # Detecção de cruzamento para venda
            elif (
                avg_ema_short_prev > avg_ema_long_prev and  # short estava acima de long
                avg_ema_short < avg_ema_long and  # short cruzou para baixo de long
                avg_ema_short > emaper_force  # short está acima do EMA_percent_s_force
            ):
                signal_down[i] = 1  # Marca o ponto de venda
                signal_down_first[i] = 1

        # Adiciona os arrays de sinais ao DataFrame de uma vez
        df["SIGNAL_UP"] = signal_up
        df["SIGNAL_UP_FIRST"] = signal_up_first
        
        df["SIGNAL_DOWN"] = signal_down
        df["SIGNAL_DOWN_FIRST"] = signal_down_first

        return df


def get_strategy(strategy_type: int) -> SignalStrategy:
    if strategy_type == 1:
        return Strategy1()
    # Adicione outras estratégias conforme necessário
    else:
        raise ValueError(f"Strategy type {strategy_type} is not recognized.")
