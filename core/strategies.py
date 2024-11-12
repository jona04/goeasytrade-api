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
        for i in range(2, len(df)):
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
        self, df: pd.DataFrame, EMA_percent_s_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
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

        for i in range(2, len(df)):
            # Valores atuais e anteriores
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]
            
            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0
                    and (emaper - previous_emaper) > 0 
                    and emaper < -EMA_percent_s_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0
                    and (emaper - previous_emaper) < 0 
                    and emaper > EMA_percent_s_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


class Strategy3(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, EMA_percent_s_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0
                    and (emaper - previous_emaper) > 0 
                    and emaper < -EMA_percent_s_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0
                    and (emaper - previous_emaper) < 0 
                    and emaper > EMA_percent_s_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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

# essa é a estratégia 1 + rsi
class Strategy4(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        RSI_values = df["RSI"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and RSI_values[i] < rsi_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (emaper > 0 and (previous_emaper - emaper) > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and RSI_values[i] > (100 - rsi_force)
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (emaper < 0 and (previous_emaper - emaper) < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 1 + adx
class Strategy5(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, adx_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        ADX_values = df["ADX"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (emaper > 0 and (previous_emaper - emaper) > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (emaper < 0 and (previous_emaper - emaper) < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 2 + rsi
class Strategy6(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        RSI_values = df["RSI"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and RSI_values[i] < rsi_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and RSI_values[i] > (100 - rsi_force)
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 2 + adx
class Strategy7(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, adx_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        ADX_values = df["ADX"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 3 + rsi
class Strategy8(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        RSI_values = df["RSI"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and RSI_values[i] < rsi_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and RSI_values[i] > (100 - rsi_force)
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 3 + adx
class Strategy9(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, adx_force, *args
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        ADX_values = df["ADX"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 1 + rsi + adx
class Strategy10(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        RSI_values = df["RSI"].values
        ADX_values = df["ADX"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and RSI_values[i] < rsi_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (emaper > 0 and (previous_emaper - emaper) > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and RSI_values[i] > (100 - rsi_force) 
                    and ADX_values[i] < adx_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (emaper < 0 and (previous_emaper - emaper) < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 2 + rsi + adx
class Strategy11(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        RSI_values = df["RSI"].values
        ADX_values = df["ADX"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and RSI_values[i] < rsi_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and RSI_values[i] > (100 - rsi_force) 
                    and ADX_values[i] < adx_force
                    ):
                    signal_down[i] = 1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

            if in_down_continue_signal:
                signal_down[i] = 1
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


# essa é a estratégia 3 + rsi + adx
class Strategy12(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
    ) -> pd.DataFrame:
        
        close1_values = df["Close"].values
        ema_long1_values = df["EMA_long"].values
        emaper_values = df["Emaper"].values
        RSI_values = df["RSI"].values
        ADX_values = df["ADX"].values

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

        for i in range(2, len(df)):
            close1 = close1_values[i]
            ema_long1 = ema_long1_values[i]
            emaper = emaper_values[i]
            previous_emaper = emaper_values[i - 1]
            previous_previous_emaper = emaper_values[i - 2]

            # Lógica para iniciar o SIGNAL_UP
            if close1 > ema_long1:
                if previous_emaper > 0 and emaper < 0:
                    in_up_first_signal = True
                    in_down_first_signal = in_down_continue_signal = False
                    continue

                if (
                    in_up_first_signal 
                    and (previous_previous_emaper - previous_emaper) > 0 
                    and (emaper - previous_emaper) > 0 
                    and emaper < -emaper_force 
                    and RSI_values[i] < rsi_force 
                    and ADX_values[i] < adx_force
                    ):
                    signal_up[i] = 1
                    signal_up_first[i] = 1
                    in_up_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if close1 < ema_long1 or (previous_emaper < 0 and emaper > 0):
                    signal_up_exit[i] = 1
                    in_up_first_signal = in_up_continue_signal = False

            if in_up_continue_signal:
                signal_up[i] = 1
                signal_up_continue[i] = 1

            # Lógica para iniciar o SIGNAL_DOWN
            if close1 < ema_long1:
                if previous_emaper < 0 and emaper > 0:
                    in_down_first_signal = True
                    in_up_first_signal = in_up_continue_signal = False
                    continue

                if (
                    in_down_first_signal 
                    and (previous_previous_emaper - previous_emaper) < 0 
                    and (emaper - previous_emaper) < 0 
                    and emaper > emaper_force 
                    and RSI_values[i] > (100 - rsi_force) 
                    and ADX_values[i] < adx_force
                    ):
                    signal_down[i] = -1
                    signal_down_first[i] = 1
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if close1 > ema_long1 or (previous_emaper > 0 and emaper < 0):
                    signal_down_exit[i] = 1
                    in_down_first_signal = in_down_continue_signal = False

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



class Strategy13(SignalStrategy):
    def detect_signals(
        self, df: pd.DataFrame, emaper_force, rsi_force, adx_force
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
        
        # Variáveis para rastrear o estado de compra e venda
        in_up_position = False  # Indica se estamos em uma operação de compra
        in_down_position = False  # Indica se estamos em uma operação de venda

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
                in_up_position = True  # Ativa sinal de compra
                signal_up[i] = 1  # Marca o ponto de compra
                signal_up_first[i] = 1
                in_down_position = False  # Interrompe possível sinal de venda

            # Detecção de cruzamento para venda
            elif (
                avg_ema_short_prev > avg_ema_long_prev and  # short estava acima de long
                avg_ema_short < avg_ema_long and  # short cruzou para baixo de long
                avg_ema_short > emaper_force  # short está acima do EMA_percent_s_force
            ):
                in_down_position = True  # Ativa sinal de venda
                signal_down[i] = 1  # Marca o ponto de venda
                signal_down_first[i] = 1
                in_up_position = False  # Interrompe possível sinal de compra

            # Critério para encerramento de operações
            if in_up_position and avg_ema_long > 0:  # Fecha compra ao cruzar para cima de zero
                in_up_position = False
            elif in_down_position and avg_ema_long < 0:  # Fecha venda ao cruzar para baixo de zero
                in_down_position = False

            # # Manter o sinal ativo enquanto não há cruzamento contrário
            # if in_up_position:
            #     signal_up[i] = 1  # Mantém o sinal de compra ativo

            # if in_down_position:
            #     signal_down[i] = 1  # Mantém o sinal de venda ativo

        # Adiciona os arrays de sinais ao DataFrame de uma vez
        df["SIGNAL_UP"] = signal_up
        df["SIGNAL_UP_FIRST"] = signal_up_first
        # df["SIGNAL_UP_CONTINUE"] = signal_up_continue
        # df["SIGNAL_UP_EXIT"] = signal_up_exit
        
        df["SIGNAL_DOWN"] = signal_down
        df["SIGNAL_DOWN_FIRST"] = signal_down_first
        # df["SIGNAL_DOWN_CONTINUE"] = signal_down_continue
        # df["SIGNAL_DOWN_EXIT"] = signal_down_exit

        return df


def get_strategy(strategy_type: int) -> SignalStrategy:
    if strategy_type == 1:
        return Strategy1()
    elif strategy_type == 2:
        return Strategy2()
    elif strategy_type == 3:
        return Strategy3()
    elif strategy_type == 4:
        return Strategy4()
    elif strategy_type == 5:
        return Strategy5()
    elif strategy_type == 6:
        return Strategy6()
    elif strategy_type == 7:
        return Strategy7()
    elif strategy_type == 8:
        return Strategy8()
    elif strategy_type == 9:
        return Strategy9()
    elif strategy_type == 10:
        return Strategy10()
    elif strategy_type == 11:
        return Strategy11()
    elif strategy_type == 12:
        return Strategy12()
    elif strategy_type == 13:
        return Strategy13()
    # Adicione outras estratégias conforme necessário
    else:
        raise ValueError(f"Strategy type {strategy_type} is not recognized.")
