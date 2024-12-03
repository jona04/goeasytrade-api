from core.pair_trading_strategy import detect_signals_strategy_1
from data.database import DataDB
from core.signal_pair_manager import SignalPairManager
class PairTrader:
    def __init__(self, pair_trader_id, target_asset, cluster_assets, entry_threshold, 
                 exit_threshold, window, interval,
                 pair_trade_executor):
        self.pair_trader_id = pair_trader_id
        self.target_asset = target_asset
        self.cluster_assets = cluster_assets
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.window = window
        self.interval = interval
        self.pair_trade_executor = pair_trade_executor
        self.db = DataDB()
        self.signal_pair_manager = SignalPairManager()
        
    def prepare_data(self, dfs, df_target):
        """
        Sincroniza e processa dados históricos para o par.
        """
        # Aqui usaremos os métodos de sincronização e cálculo da estratégia de pair-trading
        from core.pair_trading_strategy import synchronize_dataframes, apply_regression, calculate_zscore

        df = synchronize_dataframes(dfs, df_target, target_name=self.target_asset)
        df = apply_regression(df, self.target_asset)
        df['Spread'] = df['Close'] - df['Regression_Index']
        df = calculate_zscore(df, spread_column='Spread', window=self.window)

        return df

    def define_strategy(self, dfs, df_target):
        """
        Define a estratégia a ser executada após a sincronização dos dados.
        """
        # Sincronizar e calcular dados atualizados
        self.df = self.prepare_data(dfs, df_target)
        
        for opened_pair_trade in self.pair_trade_executor.get_opened_trades(activate=True):
            if self.pair_trader_id == opened_pair_trade['pair_trader_id']:
                self.pair_trade_executor.check_zscore_change(opened_pair_trade, self.df['Z-Score'].values[-1])
        
        # Processar sinais e executar ações baseadas neles
        if not self.df.empty:
            
            self.df = detect_signals_strategy_1(self.df, self.entry_threshold, self.exit_threshold)
            self.process_signals()

    def process_signals(self):
        """
        Processa sinais gerados pela estratégia e realiza ações (ex.: registrar ou executar).
        """
        last_signal = self.df.iloc[-1]
        print(self.target_asset, str(last_signal["Time"]), last_signal['Close'], last_signal["Z-Score"])
        if last_signal["SIGNAL_UP_PAIR1"] or last_signal["SIGNAL_DOWN_PAIR1"]:
            
            # Gera um sinal no banco ou integra com o executor de trades
            signal = {
                "pair_trader_id": self.pair_trader_id,
                "target_asset": str(self.target_asset),
                "time": str(last_signal["Time"]),
                "close": float(last_signal["Close"]),
                "z_score": float(last_signal["Z-Score"]),
                "signal_up_pair1": int(last_signal["SIGNAL_UP_PAIR1"]),
                "signal_down_pair1": int(last_signal["SIGNAL_DOWN_PAIR1"]),
                # Outros dados relevantes
            }
            self.db.add_one("pair_signals", signal)
            self.signal_pair_manager.register_signal(self.pair_trader_id, signal, self)
            