import asyncio
import hashlib
from data.collector import stream_data
from models.trader import LongShortTrader
from data.database import DataDB
from binance import BinanceSocketManager, AsyncClient
from datetime import datetime
from core.strategies import get_strategy
from core.signal_manager import SignalManager
from datetime import datetime, timedelta
from pytz import UTC
from binance.client import Client
import pandas as pd
from constants.defs import (
    BINANCE_KEY,
    BINANCE_TESTNET_KEY,
    BINANCE_SECRET,
    BINANCE_TESTNET_SECRET,
)

class TraderManager:
    def __init__(self):
        self.active_trader_instances = {}
        self.background_tasks = []
        self.client = None
        self.bm = None
        self.db = DataDB()
        self.signal_manager = SignalManager(total_tasks=0)
        self.candle_data = {}
        self.active_streams = set()
        
    async def init_binance_client(self):
        """Inicializa o cliente Binance e o Socket Manager."""
        self.client = await AsyncClient.create()
        self.bm = BinanceSocketManager(self.client)

    async def close_binance_client(self):
        """Fecha o cliente Binance e cancela as tarefas em segundo plano."""
        # Atualiza todos os traders no banco de dados para inativos
        try:
            self.db.update_many("active_traders", {}, {"active": False})
            print("Todos os active_traders foram marcados como inativos no banco de dados.")
        except Exception as e:
            print(f"Erro ao atualizar active_traders no banco de dados: {e}")

        # Cancela todas as instâncias de traders ativos em memória
        for trade_id, trader in self.active_trader_instances.items():
            try:
                # Remove o símbolo de streams ativos, se aplicável
                if trader.symbol in self.active_streams:
                    self.active_streams.remove(trader.symbol)
            except Exception as e:
                print(f"Erro ao cancelar stream para trade_id {trade_id}: {e}")
        self.active_trader_instances.clear()  # Limpa todas as instâncias locais

        # Cancela todas as tarefas em segundo plano
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Fecha a conexão com o cliente Binance
        if self.client:
            try:
                await self.client.close_connection()
                print("Conexão com o cliente Binance encerrada com sucesso.")
            except Exception as e:
                print(f"Erro ao fechar a conexão com o cliente Binance: {e}")


    def _generate_trade_id(self, **params):
        """Gera um identificador único para o conjunto de parâmetros do trade."""
        trade_str = "_".join(f"{key}={value}" for key, value in sorted(params.items()))
        return hashlib.md5(trade_str.encode()).hexdigest()

    async def start_trading(
        self,
        symbol,
        bar_length,
        strategy_type,
        ema_s,
        emaper_s,
        emaper_l,
        emaper_force,
        sl_percent,
    ):
        """Inicia uma sessão de trading para um conjunto de parâmetros específicos."""
        params = {
            "symbol": symbol,
            "bar_length": bar_length,
            "strategy_type": strategy_type,
            "ema_s": ema_s,
            "emaper_s": emaper_s,
            "emaper_l": emaper_l,
            "emaper_force": emaper_force,
            "sl_percent": sl_percent,
        }
        trade_id = self._generate_trade_id(**params)

        # Verifique se já existe um trade no banco de dados
        existing_trade = self.db.query_single("active_traders", trade_id=trade_id)
        if existing_trade:
            if existing_trade["active"]:
                return {
                    "status": "error",
                    "message": f"Trading is already running with the same parameters - {trade_id}",
                }
            else:
                # Atualiza o registro existente para ativo
                self.db.update_one("active_traders", {"trade_id": trade_id}, {"active": True, "start_time": datetime.now()})
                # Reinstancia o objeto `LongShortTrader`
                strategy = get_strategy(strategy_type)
                trader = LongShortTrader(
                    symbol,
                    bar_length,
                    strategy,
                    self.signal_manager,
                    ema_s,
                    emaper_s,
                    emaper_l,
                    emaper_force,
                    sl_percent,
                    trade_id,
                    self
                )
                self.active_trader_instances[trade_id] = trader
                return {"status": "success", "message": f"Trading restarted for {symbol}"}

            
        # Cria ou recupera o DataFrame centralizado para o símbolo
        if symbol not in self.candle_data:
            self.candle_data[symbol] = self.get_historical_data(symbol, bar_length)

        # Define a estratégia com base no tipo especificado
        strategy = get_strategy(strategy_type)

        # Cria uma instância de trader e armazena no dicionário
        trader = LongShortTrader(
            symbol,
            bar_length,
            strategy,
            self.signal_manager,
            ema_s,
            emaper_s,
            emaper_l,
            emaper_force,
            sl_percent,
            trade_id,
            self
        )
        self.active_trader_instances[trade_id] = trader
        self.signal_manager.total_tasks += 1

        # Salva a instância ativa no banco de dados com o status ativo
        self.db.add_one(
            "active_traders",
            {
                "trade_id": trade_id,
                "symbol": symbol,
                "bar_length": bar_length,
                "strategy_type": strategy_type,
                "ema_s": ema_s,
                "emaper_s": emaper_s,
                "emaper_l": emaper_l,
                "emaper_force": emaper_force,
                "sl_percent": sl_percent,
                "active": True,
                "start_time": datetime.now(),
            },
        )

        # Inicia o stream de dados em segundo plano, garantindo que `bm` esteja pronto
        if self.bm is None:
            raise RuntimeError("BinanceSocketManager (bm) não foi inicializado.")
       
        # Inicia o stream de dados em segundo plano, se ainda não estiver ativo para o símbolo
        if symbol not in self.active_streams:
            self.active_streams.add(symbol)  # Marcar o stream como ativo
            task = asyncio.create_task(stream_data(symbol, trade_id, self.bm, self))
            self.background_tasks.append(task)
            
        return {"status": "success", "message": f"Trading started for {symbol}"}

    def process_stream_message(self, symbol, msg):
        """Processa a mensagem de stream e verifica se o candle está completo."""
        start_time = pd.to_datetime(msg["k"]["t"], unit="ms")
        first = float(msg["k"]["o"])
        high = float(msg["k"]["h"])
        low = float(msg["k"]["l"])
        close = float(msg["k"]["c"])
        volume = float(msg["k"]["v"])
        complete = msg["k"]["x"]

        candle_data = [
            first,
            high,
            low,
            close,
            volume,
            start_time,
            complete
        ]

        # Atualiza o DataFrame centralizado apenas quando o candle está completo
        if complete:
            self.update_candle_data(symbol, candle_data, start_time)

    def get_historical_data(self, symbol, interval):
        """Obtem dados históricos de candle para um símbolo específico."""
        print(f"Adicionando dados historicos para {symbol}......")
        now = datetime.now(UTC)
        past = str(now - timedelta(days=8)) # 8 dias para ficar algo proximo de 10000 candles

        client = Client(api_key=BINANCE_KEY, api_secret=BINANCE_SECRET, tld="com")
        bars = client.get_historical_klines(symbol=symbol, interval=interval, start_str=past, end_str=None)

        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
        df.columns = [
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date",
        ]
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
        
        df["Time"] = df["Date"].copy()
        
        df.set_index("Date", inplace=True)
        for column in df.columns:
            if column != "Time":
                df[column] = pd.to_numeric(df[column], errors="coerce")
        df["Complete"] = [True for _ in range(len(df) - 1)] + [False]
        
        print(f"Dados historicos para {symbol} adicionados!")
        return df
    
    async def stop_trading(self, trade_id):
        """Encerra a sessão de trading para um símbolo específico."""
        # Verifica se o trade_id existe em active_trader_instances
        trader = self.active_trader_instances.get(trade_id)

        if trader:
            # Remove a instância do dicionário ativo
            self.active_trader_instances.pop(trade_id)

        # Verifica o banco de dados
        existing_trade = self.db.query_single("active_traders", trade_id=trade_id, active=True)
        if existing_trade:
            # Atualiza o banco de dados para marcar o trade como inativo
            self.db.update_one("active_traders", {"trade_id": trade_id}, {"active": False})
            return {
                "status": "success",
                "message": f"Trading stopped for trade_id {trade_id}",
            }

        return {
            "status": "error",
            "message": f"No active trading session for trade_id {trade_id}",
        }


    def get_active_traders(self):
        """Retorna a lista de traders ativos."""
        active_traders = self.db.query_all("active_traders", active=True)
        return {"active_traders": active_traders}

    def update_candle_data(self, symbol, candle_data, start_time):
        """Atualiza os dados de candle centralizados e notifica traders ativos."""
        # Adiciona o novo candle ao DataFrame centralizado
        df = self.candle_data[symbol]
        df.loc[start_time] = candle_data
        self.candle_data[symbol] = df
        
        # Notifica todas as instâncias de LongShortTrader para o símbolo quando um candle estiver completo
        for trade_id, trader in self.active_trader_instances.items():
            if trader.symbol == symbol:
                trader.define_strategy(start_time)
