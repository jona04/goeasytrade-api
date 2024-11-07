
import pandas as pd
from data.database import DataDB
from core.strategies import SignalStrategy
from core.signal_manager import SignalManager
from technicals.indicators import EMAShort, EMAPER, ADX, RSI, EMALong


class LongShortTrader:
    def __init__(
        self,
        symbol,
        bar_length,
        units,
        strategy: SignalStrategy,
        signal_manager: SignalManager,
        ema_s,
        ema_l,
        emaper_window,
        emaper_s,
        emaper_force,
        sl_percent,
        rsi_force,
        rsi_window,
        adx_force,
        adx_window,
        trade_id,
        manager
    ):
        # Configuração inicial
        self.symbol = symbol
        self.bar_length = bar_length
        self.units = units
        self.ema_s = ema_s
        self.ema_l = ema_l
        self.emaper_window = emaper_window
        self.emaper_s = emaper_s
        self.emaper_force = emaper_force
        self.sl_percent = sl_percent
        self.rsi_force = rsi_force
        self.rsi_window = rsi_window
        self.adx_force = adx_force
        self.adx_window = adx_window
        self.trades = 0
        self.trade_values = []
        self.strategy = strategy
        self.signal_manager = signal_manager
        self.trade_id = trade_id
        self.manager = manager
        # Conexão com o MongoDB
        self.db = DataDB()

    def save_candle_strategy_to_db(self):
        candle_data = self.prepared_data.iloc[-1].to_dict()
        self.db.add_one(f"bot_{self.symbol}_{self.trade_id}", candle_data)
        # print(
        #     f"Candle salvo para {self.symbol}: {candle_data['Close']} - {candle_data['Time']}"
        # )

    def define_strategy(self):
        # Implementar lógica da estratégia
        self.prepared_data = self.manager.candle_data[self.symbol].copy()[-self.ema_l-1000:]
        
        
        self.prepared_data = EMAShort(self.prepared_data, self.ema_s)
        self.prepared_data = EMALong(self.prepared_data, self.ema_l)
        self.prepared_data = ADX(self.prepared_data, self.adx_window)
        self.prepared_data = RSI(self.prepared_data, self.rsi_window)
        self.prepared_data = EMAPER(
            self.prepared_data, self.emaper_window, self.emaper_s
        )

        self.prepared_data.dropna(inplace=True)
        self.prepared_data.reset_index(drop=True, inplace=True)

        self.prepared_data = self.strategy.detect_signals(
            self.prepared_data.copy(), self.emaper_force, self.rsi_force, self.adx_force
        )

        # print(f"Prepared data for {self.trade_id} - with size {self.prepared_data.shape[0]}")
        pd.set_option("display.max_rows", None)
        
        self.save_candle_strategy_to_db()
        
        # print(
        #     self.prepared_data[
        #         [
        #             "Time",
        #             "Close",
        #             "EMA_long",
        #             "Emaper",
        #             "SIGNAL_UP",
        #             "SIGNAL_UP_FIRST",
        #             "SIGNAL_UP_CONTINUE",
        #             "SIGNAL_UP_EXIT"
        #         ]
        #     ].tail(1)
        # )

        candle_prepared_data = self.prepared_data.iloc[-1]
        # Verifica sinais ao final do candle completo
        if candle_prepared_data.SIGNAL_UP_FIRST != 0 or candle_prepared_data.SIGNAL_DOWN_FIRST != 0:
            signal = {
                "trade_id": self.trade_id,
                "SIGNAL_UP": candle_prepared_data.SIGNAL_UP,
                "SIGNAL_DOWN": candle_prepared_data.SIGNAL_DOWN,
                "timestamp": self.prepared_data.index[-1],
            }
            self.signal_manager.register_signal(self.trade_id, signal)  # Registra o sinal
            print(f"################## Signal registered for {self.trade_id}! #############################")

    def execute_trades(self):
        # Implementar lógica de execução de trades
        pass
