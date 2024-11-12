
import pandas as pd
from data.database import DataDB
from core.strategies import SignalStrategy
from core.signal_manager import SignalManager
from core.telegram_bot import run_bot
from technicals.indicators import EMAShort, EMAPER, calculate_ema, PAV, ADX, RSI, EMALong
from constants.defs import (CHAT_TELEGRAM_ID)
import asyncio

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
        emaper_l,
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
        self.emaper_l = emaper_l
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
        self.prepared_data = self.manager.candle_data[self.symbol].copy()[-1000:]
        
        
        self.prepared_data = EMAShort(self.prepared_data, self.ema_s)
        # self.prepared_data = EMALong(self.prepared_data, self.ema_l)
        # self.prepared_data = ADX(self.prepared_data, self.adx_window)
        # self.prepared_data = RSI(self.prepared_data, self.rsi_window)
        
        # self.prepared_data = EMAPER(
        #     self.prepared_data, self.emaper_window, 10
        # )
        
        self.prepared_data['Percent_Change_10'] = PAV(self.prepared_data['EMA_short'].values, 10)
        self.prepared_data['EMA_percent_s_10'] = calculate_ema(self.prepared_data['Percent_Change_10'].values, 10)

        self.prepared_data['Percent_Change_50'] = PAV(self.prepared_data['EMA_short'].values, 50)
        self.prepared_data['EMA_percent_s_50'] = calculate_ema(self.prepared_data['Percent_Change_50'].values, 10)
        
        self.prepared_data['Percent_Change_150'] = PAV(self.prepared_data['EMA_short'].values, 150)
        self.prepared_data['EMA_percent_s_150'] = calculate_ema(self.prepared_data['Percent_Change_150'].values, 10)

        self.prepared_data['Percent_Change_200'] = PAV(self.prepared_data['EMA_short'].values, 200)
        self.prepared_data['EMA_percent_s_200'] = calculate_ema(self.prepared_data['Percent_Change_200'].values, 10)
        
        self.prepared_data['Average_EMA_percent'] = self.prepared_data[['EMA_percent_s_10', 'EMA_percent_s_50', 'EMA_percent_s_150','EMA_percent_s_200']].mean(axis=1)
        self.prepared_data['Average_EMA_percent_ema_short'] = calculate_ema(self.prepared_data['Average_EMA_percent'].values, self.emaper_s)
        self.prepared_data['Average_EMA_percent_ema_long'] = calculate_ema(self.prepared_data['Average_EMA_percent'].values, self.emaper_l)
    
        self.prepared_data.dropna(inplace=True)
        self.prepared_data.reset_index(drop=True, inplace=True)

        self.prepared_data = self.strategy.detect_signals(
            self.prepared_data.copy(), self.emaper_force, self.rsi_force, self.adx_force
        )

        # print(f"Prepared data for {self.trade_id} - with size {self.prepared_data.shape[0]}")
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        
        self.save_candle_strategy_to_db()
        
        # print(
        #     self.prepared_data[
        #         [
        #             "Time",
        #             "Close",
        #             "Average_EMA_percent_ema_short",
        #             "Average_EMA_percent_ema_long"
        #         ]
        #     ].tail(1)
        # )

        candle_prepared_data = self.prepared_data.iloc[-1]
        # Verifica sinais ao final do candle completo
        if candle_prepared_data.SIGNAL_UP_FIRST != 0 or candle_prepared_data.SIGNAL_DOWN_FIRST != 0:
            signal = {
                "trade_id": self.trade_id,
                "Time": candle_prepared_data.Time
            }
            self.signal_manager.register_signal(self.trade_id, signal)  # Registra o sinal
            message = "################## Signal registered for "+self.trade_id+"! #############################"
            print(message)
            print(f"Time = {candle_prepared_data.Time}")
            print("")
            asyncio.create_task(run_bot([message], CHAT_TELEGRAM_ID))
            
    def execute_trades(self):
        # Implementar lógica de execução de trades
        pass
