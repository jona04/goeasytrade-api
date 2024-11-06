from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


class SignalStrategy(ABC):
    @abstractmethod
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
    ) -> pd.DataFrame:
        pass


class Strategy1(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
    ) -> pd.DataFrame:

        # Extrai os valores como arrays NumPy para maior eficiência
        close_values = df["Close"].values
        ema_long_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values

        # Inicializa os arrays SIGNAL_UP e SIGNAL_DOWN com zeros
        signal_up = np.zeros(len(df), dtype=int)
        signal_up_first = np.zeros(len(df), dtype=int)
        signal_up_continue = np.zeros(len(df), dtype=int)
        signal_up_exit = np.zeros(len(df), dtype=int)
        
        signal_down = np.zeros(len(df), dtype=int)
        signal_down_first = np.zeros(len(df), dtype=int)
        signal_down_continue = np.zeros(len(df), dtype=int)
        signal_down_exit = np.zeros(len(df), dtype=int)

        # Flags para rastrear a continuidade dos sinais
        in_up_first_signal, in_up_continue_signal = False, False
        in_down_first_signal, in_down_continue_signal = False, False

        # Loop otimizado
        for i in range(1, len(df)):
            close = close_values[i]
            ema_long = ema_long_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close > ema_long:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal
                    and (previous_previous_emaper - previous_emaper) > 0
                    and (emaper - previous_emaper) > 0
                    and emaper < -emaper_force
                ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True
                    
            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close < ema_long or (emaper > 0 and (previous_emaper - emaper) > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close < ema_long:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal
                    and (previous_previous_emaper - previous_emaper) < 0
                    and (emaper - previous_emaper) < 0
                    and emaper > emaper_force
                ):
                    signal_down[i] = -1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True
                    
            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close > ema_long or (emaper < 0 and (previous_emaper - emaper) < 0):
                    in_down_first_signal = in_down_continue_signal = False
                    signal_down_exit[i] = 1

            if in_down_continue_signal:
                signal_down[i] = -1
                signal_down_continue[i] = 1

        # Adiciona os arrays de sinais ao DataFrame de uma vez
        df["SIGNAL_UP"] = signal_up
        df["SIGNAL_UP_FIRST"] = signal_up_first
        df["SIGNAL_UP_CONTINUE"] = signal_up_continue
        df["SIGNAL_UP_EXIT"] = signal_up_exit
        
        df["SIGNAL_DOWN"] = signal_down
        df["SIGNAL_DOWN_FIRST"] = signal_down_first
        df["SIGNAL_DOWN_CONTINUE"] = signal_down_continue
        df["SIGNAL_DOWN_EXIT"] = signal_down_exit
        
        return df


class Strategy2(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
    ) -> pd.DataFrame:
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
