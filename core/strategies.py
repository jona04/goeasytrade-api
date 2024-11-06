from abc import ABC, abstractmethod
import pandas as pd


class SignalStrategy(ABC):
    @abstractmethod
    def detect_signals(self, df: pd.DataFrame, emaper_force, 
                       rsi_force, adx_force) -> pd.DataFrame:
        pass


class Strategy1(SignalStrategy):
    def detect_signals(self, df: pd.DataFrame, emaper_force, 
                       rsi_force, adx_force) -> pd.DataFrame:
        # Implementação da estratégia 1
        # Modifica o DataFrame `df` e retorna
        close_values = df.Close.values
        ema_long_values = df.EMA_long.values
        emaper_values = df.Emaper.values
     
        # Inicializa as colunas SIGNAL_UP e SIGNAL_DOWN com zeros
        df['SIGNAL_UP'] = 0
        df['SIGNAL_DOWN'] = 0
        
        # Flags para rastrear a continuidade dos sinais
        in_up_first_signal, in_up_continue_signal = False, False
        
        in_down_first_signal, in_down_continue_signal = False, False

        for i in range(1, len(df)):
            # Valores atuais e anteriores
            close = close_values[i]
            ema_long = ema_long_values[i]
            emaper = emaper_values[i]
            previous_Emaper = emaper_values[i-1]
            
            # Lógica para iniciar o SIGNAL_UP
            if close > ema_long:
                # Condição para iniciar o SIGNAL_UP
                if previous_Emaper > 0 and emaper < 0:  # EMA_1_medio passa de positivo para negativo
                    in_up_first_signal = True  # Ativa o sinal de subida
                    in_down_first_signal, in_down_continue_signal = False, False # Interrompe qualquer sinal de descida
                    continue
                
                if (
                    in_up_first_signal and 
                    (emaper - previous_Emaper) > 0 and 
                    emaper < -emaper_force
                ): 
                    df.loc[i, 'SIGNAL_UP'] = 1  # Marca o sinal de subida
                    in_up_continue_signal = True
                    
            # Condição para continuar ou interromper o SIGNAL_UP
            if in_up_first_signal:
                if (
                    close < ema_long or 
                    (emaper > 0 and (previous_Emaper - emaper) > 0)
                ):  # Condições de interrupção
                    in_up_first_signal, in_up_continue_signal = False, False
            
            if in_up_continue_signal:
                df.loc[i, 'SIGNAL_UP'] = 1  # Mantém o sinal de subida contínuo

            # Lógica para iniciar o SIGNAL_DOWN (inverso do SIGNAL_UP)
            if close < ema_long:
                # Condição para iniciar o SIGNAL_DOWN
                if previous_Emaper < 0 and emaper > 0:  # EMA_1_medio passa de negativo para positivo
                    in_down_first_signal = True  # Ativa o sinal de descida
                    in_up_first_signal, in_up_continue_signal = False, False  # Interrompe qualquer sinal de subida
                    continue
                
                if (
                    in_down_first_signal and 
                    (emaper - previous_Emaper) < 0 and 
                    emaper > emaper_force
                ):  # EMA_1_medio começa a descer
                    df.loc[i, 'SIGNAL_DOWN'] = -1  # Marca o sinal de descida
                    in_down_continue_signal = True

            # Condição para continuar ou interromper o SIGNAL_DOWN
            if in_down_first_signal:
                if (
                    close > ema_long or 
                    (emaper < 0 and (previous_Emaper - emaper) < 0)
                    ):  # Condições de interrupção
                    in_down_first_signal, in_down_continue_signal = False, False
            if in_down_continue_signal:
                df.loc[i, 'SIGNAL_DOWN'] = -1  # Mantém o sinal de descida contínuo

        return df


class Strategy2(SignalStrategy):
    def detect_signals(self, df: pd.DataFrame, emaper_force, 
                       rsi_force, adx_force) -> pd.DataFrame:
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
