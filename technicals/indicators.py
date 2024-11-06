import pandas as pd
import numpy as np


def BollingerBands(df: pd.DataFrame, n=20, s=2):
    typical_p = (df.mid_c + df.mid_h + df.mid_l) / 3
    stddev = typical_p.rolling(window=n).std()
    df["BB_MA"] = typical_p.rolling(window=n).mean()
    df["BB_UP"] = df["BB_MA"] + stddev * s
    df["BB_LW"] = df["BB_MA"] - stddev * s
    return df


def ATR(df: pd.DataFrame, n=14):
    prev_c = df.mid_c.shift(1)
    tr1 = df.mid_h - df.mid_l
    tr2 = abs(df.mid_h - prev_c)
    tr3 = abs(prev_c - df.mid_l)
    tr = pd.DataFrame({"tr1": tr1, "tr2": tr2, "tr3": tr3}).max(axis=1)
    df[f"ATR_{n}"] = tr.rolling(window=n).mean()
    return df


def KeltnerChannels(df: pd.DataFrame, n_ema=20, n_atr=10):
    df["EMA"] = df.mid_c.ewm(span=n_ema, min_periods=n_ema).mean()
    df = ATR(df, n=n_atr)
    c_atr = f"ATR_{n_atr}"
    df["KeUp"] = df[c_atr] * 2 + df.EMA
    df["KeLo"] = df.EMA - df[c_atr] * 2
    df.drop(c_atr, axis=1, inplace=True)
    return df


def RSI(df: pd.DataFrame, n=14):
    alpha = 1.0 / n
    gains = df.Close.diff()

    wins = pd.Series([x if x >= 0 else 0.0 for x in gains], name="wins")
    losses = pd.Series([x * -1 if x < 0 else 0.0 for x in gains], name="losses")

    wins_rma = wins.ewm(min_periods=n, alpha=alpha).mean()
    losses_rma = losses.ewm(min_periods=n, alpha=alpha).mean()

    rs = wins_rma / losses_rma

    df[f"RSI_{n}"] = 100.0 - (100.0 / (1.0 + rs))
    return df


def MACD(df: pd.DataFrame, n_slow=26, n_fast=12, n_signal=9):

    ema_long = df.mid_c.ewm(min_periods=n_slow, span=n_slow).mean()
    ema_short = df.mid_c.ewm(min_periods=n_fast, span=n_fast).mean()

    df["MACD"] = ema_short - ema_long
    df["SIGNAL"] = df.MACD.ewm(min_periods=n_signal, span=n_signal).mean()
    df["HIST"] = df.MACD - df.SIGNAL
    return df


def Donchian(df: pd.DataFrame, window=50):
    df["donchian_high"] = df["mid_c"].rolling(window=window).max()
    df["donchian_low"] = df["mid_c"].rolling(window=window).min()
    df["donchian_mid"] = (df["donchian_high"] + df["donchian_low"]) / 2
    df["donchian_75"] = (df["donchian_high"] + df["donchian_mid"]) / 2
    df["donchian_87"] = (df["donchian_high"] + df["donchian_75"]) / 2
    df["donchian_62"] = (df["donchian_75"] + df["donchian_mid"]) / 2
    df["donchian_25"] = (df["donchian_mid"] + df["donchian_low"]) / 2
    df["donchian_37"] = (df["donchian_mid"] + df["donchian_25"]) / 2
    df["donchian_12"] = (df["donchian_25"] + df["donchian_low"]) / 2

    return df


def EMA(df: pd.DataFrame, window: 50):
    df[f"EMA_{window}"] = df.Close.ewm(span=window, min_periods=window).mean()
    return df


def EMAShort(df: pd.DataFrame, window: 50):
    df[f"EMA_short"] = df.Close.ewm(span=window, min_periods=window).mean()
    return df


def EMALong(df: pd.DataFrame, window: 50):
    df[f"EMA_long"] = df.Close.ewm(span=window, min_periods=window).mean()
    return df


# Função para calcular a variação percentual acumulada
def calculate_percent_change(close_prices, window):
    percent_change = np.zeros(len(close_prices))

    for i in range(window, len(close_prices)):
        window_sum = 0.0
        for j in range(i - window + 1, i + 1):
            percent_change[j] = (
                (close_prices[j] - close_prices[j - 1]) / close_prices[j - 1] * 100
            )
            window_sum += percent_change[j]
        percent_change[i] = window_sum

    return percent_change


# Função para calcular a EMA
def calculate_ema(values, period):
    ema = np.zeros(len(values))
    multiplier = 2 / (period + 1)
    ema[period - 1] = values[
        period - 1
    ]  # O primeiro valor da EMA é igual ao valor inicial
    for i in range(period, len(values)):
        ema[i] = (values[i] - ema[i - 1]) * multiplier + ema[i - 1]
    return ema


# Função para calcular os indicadores e adicionar ao DataFrame
def EMAPER(df: pd.DataFrame, window=14, ema_period_1=10):

    # Obtém os preços de fechamento da coluna 'EMA_short/Close'
    close_prices = df["EMA_short"].values

    # Calcula a variação percentual acumulada
    percent_change = calculate_percent_change(close_prices, window)

    # Calcula as EMAs
    ema_1 = calculate_ema(percent_change, ema_period_1)

    # Adiciona os resultados ao DataFrame original
    df["Percent_Change"] = percent_change
    df["Emaper"] = ema_1

    return df


def ADX(df: pd.DataFrame, period=14):
    # Calcula +DM, -DM e TR
    high_diff = df["High"].diff()
    low_diff = df["Low"].diff()
    df["+DM"] = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    df["-DM"] = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
    df["TR"] = np.maximum(
        df["High"] - df["Low"],
        np.maximum(
            abs(df["High"] - df["Close"].shift(1)),
            abs(df["Low"] - df["Close"].shift(1)),
        ),
    )

    # Suaviza TR, +DM e -DM com a média móvel exponencial
    atr = df["TR"].ewm(alpha=1 / period, min_periods=period).mean()
    df["+DI"] = 100 * (df["+DM"].ewm(alpha=1 / period, min_periods=period).mean() / atr)
    df["-DI"] = 100 * (df["-DM"].ewm(alpha=1 / period, min_periods=period).mean() / atr)

    # Calcula o DX e o ADX
    dx = 100 * abs(df["+DI"] - df["-DI"]) / (df["+DI"] + df["-DI"])
    df["ADX"] = dx.ewm(alpha=1 / period, min_periods=period).mean()

    # Remove colunas temporárias
    df.drop(columns=["+DM", "-DM", "TR"], inplace=True)

    return df
