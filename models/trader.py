
import pandas as pd
from data.database import DataDB
from core.strategies import SignalStrategy
from core.signal_manager import SignalManager
from core.telegram_bot import run_bot
from technicals.indicators import EMAShort, calculate_ema, PAV
from constants.defs import (CHAT_TELEGRAM_ID)
import asyncio
import mplfinance as mpf
import matplotlib.pyplot as plt

class LongShortTrader:
    def __init__(
        self,
        symbol,
        bar_length,
        strategy: SignalStrategy,
        signal_manager: SignalManager,
        ema_s,
        emaper_s,
        emaper_l,
        emaper_force,
        sl_percent,
        trade_id,
        manager
    ):
        # Configuração inicial
        self.symbol = symbol
        self.bar_length = bar_length
        self.ema_s = ema_s
        self.emaper_s = emaper_s
        self.emaper_l = emaper_l
        self.emaper_force = emaper_force
        self.sl_percent = sl_percent
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

    def define_strategy(self, start_time):
        # Implementar lógica da estratégia
        self.prepared_data = self.manager.candle_data[self.symbol].copy()[-500:]
        
        self.prepared_data = EMAShort(self.prepared_data, self.ema_s)
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
        self.prepared_data = self.strategy.detect_signals(self.prepared_data.copy(), self.emaper_force)

        self.save_candle_strategy_to_db()
      
        
        candle_prepared_data = self.prepared_data.iloc[-1]
        # Verifica sinais ao final do candle completo
        if candle_prepared_data.SIGNAL_UP_FIRST != 0 or candle_prepared_data.SIGNAL_DOWN_FIRST != 0:
            # Gera o gráfico de candlestick e salva como imagem
            img_path = "candle_chart.png"
            fig, ax = plt.subplots(figsize=(10, 6))
            mpf.plot(self.prepared_data.set_index("Time").tail(100), type="candle", ax=ax)
            plt.savefig(img_path)
            plt.close(fig)
            
            signal = {
                "trade_id": self.trade_id,
                "Time": candle_prepared_data.Time,
                "Close": candle_prepared_data.Close,
                "SIGNAL_UP": candle_prepared_data.SIGNAL_UP_FIRST,
                "SIGNAL_DOWN": candle_prepared_data.SIGNAL_DOWN_FIRST
            }
            self.signal_manager.register_signal(self.trade_id, signal)
            
            # Estrutura a mensagem para envio no Telegram
            title = f"################## \nSinal registrado para: \n{self.trade_id}"
            message = f"""
            *{title}*
            
            - ID da Trade: `{signal['trade_id']}`
            - Hora: `{signal['Time']}`
            - Fechamento: `{signal['Close']}`
            - Sinal de Alta: `{signal['SIGNAL_UP']}`
            - Sinal de Baixa: `{signal['SIGNAL_DOWN']}`
            - Ativo: '{self.symbol}'
            - Emaper short: '{self.emaper_s}'
            - Emaper long: '{self.emaper_l}'
            - Emaper force: '{self.emaper_force}'
            - SL percent: '{self.sl_percent}'
            """

            # Envia a mensagem usando o bot do Telegram
            print("")
            print(message)
            print("")
            
            asyncio.create_task(run_bot([message, ("photo", img_path)], CHAT_TELEGRAM_ID))
        
        # Notifica o SignalManager sobre a conclusão conclusão da stratégia para um trader strategy
        self.signal_manager.register_task_completion(start_time)
        
        
    def execute_trades(self):
        # Implementar lógica de execução de trades
        pass
