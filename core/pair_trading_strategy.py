import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

def synchronize_dataframes(dfs, df_target, target_name='Target'):
    df = df_target[['Time', 'Close', 'High', 'Low', 'Open']]
    for i, df_pair in enumerate(dfs):
        df = pd.merge(df, df_pair[['Time', 'Close']].rename(columns={'Close': f'Asset_{i}'}), 
                      on='Time', how='inner')
    return df

def apply_regression(df, target_name):
    asset_columns = [col for col in df.columns if col.startswith('Asset_')]
    X = df[asset_columns].values
    y = df['Close'].values

    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(X)
    y_normalized = scaler.fit_transform(y.reshape(-1, 1)).flatten()

    model = LinearRegression().fit(X_normalized, y_normalized)
    y_pred_normalized = model.predict(X_normalized)

    y_pred = scaler.inverse_transform(y_pred_normalized.reshape(-1, 1)).flatten()
    df['Regression_Index'] = y_pred
    return df

def calculate_zscore(df, spread_column='Spread', window=50):
    df['Spread_Mean'] = df[spread_column].rolling(window=window).mean()
    df['Spread_Std'] = df[spread_column].rolling(window=window).std()
    df['Z-Score'] = (df[spread_column] - df['Spread_Mean']) / df['Spread_Std']
    return df

def detect_signals_strategy_1(df, entry_threshold, exit_threshold):
    """
    Gera sinais de entrada e saída com base no Z-Score.
    Mantém o sinal ativo até que o Z-Score cruze zero (se exit_threshold = 0)
    ou atinja a faixa de saída definida por exit_threshold.

    :param df: DataFrame com a coluna 'Z-Score'.
    :param entry_threshold: Limiar para entrada (ex.: ±2).
    :param exit_threshold: Limiar para saída (ex.: 0).
    :return: DataFrame atualizado com sinais específicos para cada par.
    """
    # Inicializando vetores para sinais
    signal_up_pair1 = np.zeros(len(df), dtype=int)  # Long Pair1
    signal_down_pair1 = np.zeros(len(df), dtype=int)  # Short Pair1
    signal_up_pair2 = np.zeros(len(df), dtype=int)  # Long Pair2
    signal_down_pair2 = np.zeros(len(df), dtype=int)  # Short Pair2

    z_score_values = df['Z-Score'].values  # Extraindo Z-Score como array

    # Iterar sobre os índices do DataFrame
    for i in range(1, len(z_score_values)):  # Começa no índice 1 para verificar o cruzamento
        if z_score_values[i] > entry_threshold:
            # Z > entry_threshold: Short Pair1, Long Pair2
            signal_down_pair1[i] = 1  # Short Pair1
            signal_up_pair2[i] = 1  # Long Pair2
        elif z_score_values[i] < -entry_threshold:
            # Z < -entry_threshold: Long Pair1, Short Pair2
            signal_up_pair1[i] = 1  # Long Pair1
            signal_down_pair2[i] = 1  # Short Pair2

    # Adicionando os vetores de sinal ao DataFrame
    df["SIGNAL_UP_PAIR1"] = signal_up_pair1
    df["SIGNAL_DOWN_PAIR1"] = signal_down_pair1
    df["SIGNAL_UP_PAIR2"] = signal_up_pair2
    df["SIGNAL_DOWN_PAIR2"] = signal_down_pair2

    return df