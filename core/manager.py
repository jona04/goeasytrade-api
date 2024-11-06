import asyncio
from data.collector import stream_data
from models.trader import LongShortTrader
from data.database import DataDB
from binance import BinanceSocketManager, AsyncClient
from datetime import datetime

class TraderManager:
    def __init__(self):
        self.active_trader_instances = {}
        self.background_tasks = []
        self.client = None
        self.bm = None
        self.db = DataDB()

    async def init_binance_client(self):
        """Inicializa o cliente Binance e o Socket Manager."""
        self.client = await AsyncClient.create()
        self.bm = BinanceSocketManager(self.client)

    async def close_binance_client(self):
        """Fecha o cliente Binance e cancela as tarefas em segundo plano."""
        # Limpa a tabela 'active_traders' no MongoDB
        try:
            self.db.delete_many("active_traders")
            print("Tabela 'active_traders' limpa com sucesso.")
        except Exception as e:
            print(f"Erro ao limpar a tabela 'active_traders': {e}")
        
        # Cancela todas as tarefas em segundo plano
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Fecha a conexão com o cliente Binance
        if self.client:
            await self.client.close_connection()

    async def start_trading(self, symbol, bar_length, ema_s, units, quote_units, historical_days):
        """Inicia uma sessão de trading para um símbolo específico."""
        # Verifique se já existe uma sessão ativa
        if symbol in self.active_trader_instances:
            return {"status": "error", "message": f"Trading is already running for {symbol}"}
        
        # Cria uma instância de trader e armazena no dicionário
        trader = LongShortTrader(symbol, bar_length, ema_s, units, quote_units)
        trader.get_most_recent(symbol=symbol, interval=bar_length, days=historical_days)
        self.active_trader_instances[symbol] = trader

        # Salva a instância ativa no banco de dados
        self.db.add_one("active_traders", {
            "symbol": symbol,
            "bar_length": bar_length,
            "units": units,
            "quote_units": quote_units,
            "start_time": datetime.now()
        })

        # Inicia o stream de dados em segundo plano, garantindo que `bm` esteja pronto
        if self.bm is None:
            raise RuntimeError("BinanceSocketManager (bm) não foi inicializado.")

        task = asyncio.create_task(stream_data(symbol, self.bm, trader))
        self.background_tasks.append(task)
        return {"status": "success", "message": f"Trading started for {symbol}"}

    async def stop_trading(self, symbol):
        """Encerra a sessão de trading para um símbolo específico."""
        if symbol in self.active_trader_instances:
            self.db.delete_single("active_traders", symbol=symbol)
            self.active_trader_instances.pop(symbol)
            return {"status": "success", "message": f"Trading stopped for {symbol}"}
        
        return {"status": "error", "message": f"No active trading session for {symbol}"}

    def get_active_traders(self):
        """Retorna a lista de traders ativos."""
        active_traders = list(self.db.query_all("active_traders"))
        return {"active_traders": active_traders}
