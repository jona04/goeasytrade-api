from datetime import datetime, timedelta
import pandas as pd
from data.database import DataDB
from pytz import UTC
from binance.client import Client
from core.strategies import SignalStrategy
from core.signal_manager import SignalManager
from constants.defs import (
    BINANCE_KEY,
    BINANCE_TESTNET_KEY,
    BINANCE_SECRET,
    BINANCE_TESTNET_SECRET,
)
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
        trade_id
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
        self.data = pd.DataFrame()
        self.strategy = strategy
        self.signal_manager = signal_manager
        self.trade_id = trade_id

        # Conexão com o MongoDB
        self.db = DataDB()

    def get_most_recent(self, symbol, interval, days):
        now = datetime.now(UTC)
        past = str(now - timedelta(days=days))

        client = Client(api_key=BINANCE_KEY, api_secret=BINANCE_SECRET, tld="com")
        bars = client.get_historical_klines(
            symbol=symbol, interval=interval, start_str=past, end_str=None
        )

        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
        df.columns = [
            "Open Time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Close Time",
            "Quote Asset Volume",
            "Number of Trades",
            "Taker Buy Base Asset Volume",
            "Taker Buy Quote Asset Volume",
            "Ignore",
            "Date",
        ]
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

        # Converte todos os candles para uma lista de dicionários
        candles = self.data.to_dict("records")
        self.db.delete_many(f"bot_{self.symbol}")
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
        self.data.loc[start_time] = [
            first,
            high,
            low,
            close,
            volume,
            start_time,
            complete,
        ]

        # Salvar no MongoDB e processar estratégia ao final do candle
        if complete:
            self.save_candle_to_db()
            self.define_strategy()
            self.signal_manager.register_task_completion(
                start_time
            )  # Notifica o SignalManager sobre a conclusão
            self.execute_trades()

    def save_candle_to_db(self):
        candle_data = self.data.iloc[-1].to_dict()
        self.db.add_one(f"bot_{self.symbol}", candle_data)
        print(
            f"Candle salvo para {self.symbol}: {candle_data['Close']} - {candle_data['Time']}"
        )

    def define_strategy(self):
        # Implementar lógica da estratégia
        self.prepared_data = self.data.copy()

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

        pd.set_option("display.max_rows", None)
        print(
            self.prepared_data[
                [
                    "Time",
                    "Close",
                    "EMA_long",
                    "Emaper",
                    "SIGNAL_UP",
                    "SIGNAL_UP_FIRST",
                    "SIGNAL_UP_CONTINUE",
                    "SIGNAL_UP_EXIT"
                ]
            ].tail(1)
        )

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

    def execute_trades(self):
        # Implementar lógica de execução de trades
        pass
