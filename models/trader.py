from datetime import datetime, timedelta
from collections import deque
import pandas as pd
from data.database import DataDB
from pytz import UTC
from binance.client import Client
from constants.defs import BINANCE_KEY, BINANCE_TESTNET_KEY, BINANCE_SECRET, BINANCE_TESTNET_SECRET

class LongShortTrader:
    def __init__(self, symbol, bar_length, ema_s, units, quote_units, position=0):
        # Configuração inicial
        self.symbol = symbol
        self.bar_length = bar_length
        self.units = units
        self.quote_units = quote_units
        self.position = position
        self.trades = 0
        self.trade_values = []
        self.opened_trades = deque()
        self.closed_trades = deque()
        self.data = pd.DataFrame()
        self.strategy = None
        
        # Conexão com o MongoDB
        self.db = DataDB()
    
    def get_most_recent(self, symbol, interval, days):
        now = datetime.now(UTC)
        past = str(now - timedelta(days=days))

        client = Client(api_key = BINANCE_KEY, api_secret = BINANCE_SECRET, tld = "com")
        bars = client.get_historical_klines(
            symbol=symbol, interval=interval, start_str=past, end_str=None
        )
        print("bars",len(bars))
        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
        df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume", "Close Time",
                      "Quote Asset Volume", "Number of Trades", "Taker Buy Base Asset Volume",
                      "Taker Buy Quote Asset Volume", "Ignore", "Date"]
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        
        df["Time"] = df["Date"].copy()
        
        df.set_index("Date", inplace=True)
        for column in df.columns:
            if column != "Time":
                df[column] = pd.to_numeric(df[column], errors="coerce")
        df["Complete"] = [True for _ in range(len(df) - 1)] + [False]
        
        self.data = df.iloc[:-1]

        # Salva todos os candles históricos no banco de dados
        self.save_candles_to_db()
    
    def save_candles_to_db(self):
        """Salva todos os candles no banco de dados."""
        
        print(self.data.head())
        print(self.data.tail())
        print(self.data.shape)
        # Converte todos os candles para uma lista de dicionários
        candles = self.data.to_dict("records")

        self.db.delete_many(f"bot_{self.symbol}")
        
        # Insere todos os candles de uma vez no MongoDB
        self.db.add_many(f"bot_{self.symbol}", candles)
        print(f"Todos os candles históricos foram salvos para {self.symbol}.")
        
    def stream_candles(self, msg):
        event_time = pd.to_datetime(msg["E"], unit="ms")
        start_time = pd.to_datetime(msg["k"]["t"], unit="ms")
        first = float(msg["k"]["o"])
        high = float(msg["k"]["h"])
        low = float(msg["k"]["l"])
        close = float(msg["k"]["c"])
        volume = float(msg["k"]["v"])
        complete = msg["k"]["x"]

        # Atualizar o DataFrame com o novo candle
        self.data.loc[start_time] = [first, high, low, close, volume, start_time, complete]

        
        # Salvar no MongoDB e processar estratégia ao final do candle
        if complete:
            self.save_candle_to_db()
            self.define_strategy()
            self.execute_trades()

    def save_candle_to_db(self):
        candle_data = self.data.iloc[-1].to_dict()
        self.db.add_one(f"bot_{self.symbol}",candle_data)
        print(f"Candle salvo para {self.symbol}: {candle_data}")

    def define_strategy(self):
        # Implementar lógica da estratégia
        pass

    def execute_trades(self):
        # Implementar lógica de execução de trades
        pass
