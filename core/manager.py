import asyncio
import hashlib
from data.collector import stream_data
from models.trader import LongShortTrader
from data.database import DataDB
from binance import BinanceSocketManager, AsyncClient
from datetime import datetime
from core.strategies import get_strategy
from core.signal_manager import SignalManager


class TraderManager:
    def __init__(self):
        self.active_trader_instances = {}
        self.background_tasks = []
        self.client = None
        self.bm = None
        self.db = DataDB()
        self.signal_manager = SignalManager(total_tasks=0)

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

    def _generate_trade_id(self, **params):
        """Gera um identificador único para o conjunto de parâmetros do trade."""
        trade_str = "_".join(f"{key}={value}" for key, value in sorted(params.items()))
        return hashlib.md5(trade_str.encode()).hexdigest()

    async def start_trading(
        self,
        symbol,
        bar_length,
        units,
        historical_days,
        strategy_type,
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
    ):
        """Inicia uma sessão de trading para um conjunto de parâmetros específicos."""
        params = {
            "symbol": symbol,
            "bar_length": bar_length,
            "strategy_type": strategy_type,
            "ema_s": ema_s,
            "ema_l": ema_l,
            "emaper_window": emaper_window,
            "emaper_s": emaper_s,
            "emaper_force": emaper_force,
            "sl_percent": sl_percent,
            "rsi_force": rsi_force,
            "rsi_window": rsi_window,
            "adx_force": adx_force,
            "adx_window": adx_window,
        }
        trade_id = self._generate_trade_id(**params)

        # Verifique se já existe uma sessão ativa
        if trade_id in self.active_trader_instances:
            return {
                "status": "error",
                "message": f"Trading is already running with the same parameters",
            }

        # Define a estratégia com base no tipo especificado
        strategy = get_strategy(strategy_type)

        # Cria uma instância de trader e armazena no dicionário
        trader = LongShortTrader(
            symbol,
            bar_length,
            units,
            strategy,
            self.signal_manager,
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
        )
        trader.get_most_recent(symbol=symbol, interval=bar_length, days=historical_days)
        self.active_trader_instances[symbol] = trader
        self.signal_manager.total_tasks += 1

        # Salva a instância ativa no banco de dados
        self.db.add_one(
            "active_traders",
            {
                "trade_id": trade_id,
                "symbol": symbol,
                "bar_length": bar_length,
                "units": units,
                "historical_days": historical_days,
                "strategy_type": strategy_type,
                "ema_s": ema_s,
                "ema_l": ema_l,
                "emaper_window": emaper_window,
                "emaper_s": emaper_s,
                "emaper_force": emaper_force,
                "sl_percent": sl_percent,
                "rsi_force": rsi_force,
                "rsi_window": rsi_window,
                "adx_force": adx_force,
                "adx_window": adx_window,
                "start_time": datetime.now(),
            },
        )

        # Inicia o stream de dados em segundo plano, garantindo que `bm` esteja pronto
        if self.bm is None:
            raise RuntimeError("BinanceSocketManager (bm) não foi inicializado.")

        task = asyncio.create_task(stream_data(symbol, self.bm, trader, self))
        self.background_tasks.append(task)

        return {"status": "success", "message": f"Trading started for {symbol}"}

    async def stop_trading(self, trade_id):
        """Encerra a sessão de trading para um símbolo específico."""
        if trade_id in self.active_trader_instances:
            self.db.delete_single("active_traders", trade_id=trade_id)
            self.active_trader_instances.pop(trade_id)
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
        active_traders = list(self.db.query_all("active_traders"))
        return {"active_traders": active_traders}
