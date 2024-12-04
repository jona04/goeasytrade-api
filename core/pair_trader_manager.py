from binance.client import Client
from binance import BinanceSocketManager, AsyncClient
from datetime import datetime, timedelta
from pytz import UTC
import pandas as pd
import asyncio
import hashlib
from data.collector import stream_data_pair
from data.database import DataDB
from core.pair_trader import PairTrader
from operations.pair_trade_executor import PairTradeExecutor
from core.config_pair_system_manager import ConfigPairSystemManager

from constants.defs import (
    BINANCE_KEY,
    BINANCE_TESTNET_KEY,
    BINANCE_SECRET,
    BINANCE_TESTNET_SECRET,
)

class PairTraderManager:
    def __init__(self):
        self.active_pair_traders = {}
        self.background_tasks = []
        self.client = None
        self.bm = None
        self.db = DataDB()
        self.candle_data = {}  # Armazena os candles históricos para cada ativo
        self.candle_sync = {}  # Controle de sincronização de candles
        self.active_streams = set()
        self.pair_trade_executor = PairTradeExecutor()
        
    async def init_binance_client(self):
        """Inicializa o cliente Binance e o Socket Manager."""
        self.client = await AsyncClient.create()
        self.bm = BinanceSocketManager(self.client)

    async def close_binance_client(self):
        """Fecha o cliente Binance e cancela as tarefas em segundo plano."""
        # Atualiza todos os traders no banco de dados para inativos
        try:
            self.db.update_many("active_pair_traders", {}, {"active": False})
            print("Todos os active_pair_traders foram marcados como inativos no banco de dados.")
        except Exception as e:
            print(f"Erro ao atualizar active_pair_traders no banco de dados: {e}")
        
        # Cancela todas as instâncias de traders ativos em memória
        for pair_trader_id, trader in self.active_pair_traders.items():
            try:
                # Remove o símbolo de streams ativos, se aplicável
                if trader.target_asset in self.active_streams:
                    self.active_streams.remove(trader.target_asset)
            except Exception as e:
                print(f"Erro ao cancelar stream para trade_id {pair_trader_id}: {e}")
        self.active_pair_traders.clear()  # Limpa todas as instâncias locais
        self.candle_data.clear()
        self.candle_sync.clear()

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



    def get_historical_data(self, symbol, interval):
        """Obtem dados históricos de candle para um símbolo específico."""
        print(f"Adicionando dados historicos para {symbol}......")
        now = datetime.now(UTC)
        past = str(now - timedelta(days=20)) # 20 dias para ficar algo proximo de 10000 candles

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
    

    def _generate_trade_id(self, **params):
        """Gera um identificador único para o conjunto de parâmetros do trade."""
        trade_str = "_".join(f"{key}={value}" for key, value in sorted(params.items()))
        return hashlib.md5(trade_str.encode()).hexdigest()

    async def start_pair_trading(self, target_symbol, cluster_symbols, 
                                 entry_threshold, exit_threshold, window,
                                 stop_loss,trailing_stop_target,
                                 trailing_stop_loss):
        """Inicia um par de trading."""
        params = {
            "target_symbol": target_symbol,
            "cluster_symbols": cluster_symbols,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
            "window": window,
            "sl_percent": stop_loss,
            "trailing_stop_target": trailing_stop_target,
            "trailing_stop_loss": trailing_stop_loss 
        }
        pair_trader_id = self._generate_trade_id(**params)
        
        # 1. Verificar se já existe um trade ativo no banco de dados
        existing_trade = self.db.query_single("active_pair_traders", pair_trader_id=pair_trader_id)
        if existing_trade:
            if existing_trade["active"]:
                return {
                    "status": "error",
                    "message": f"Trading is already running with the same parameters - {pair_trader_id}",
                }
            
            # Reativar trade existente
            return await self._reactivate_trade(existing_trade)


        # 2. Criar e configurar novo trader
        await self._setup_new_trader(pair_trader_id, target_symbol, cluster_symbols, 
                                     entry_threshold, exit_threshold, window, params)
        

        return {"status": "success", "message": f"Pair trading started for {pair_trader_id}"}
       
    async def _reactivate_trade(self, existing_trade):
        """Reativa um trade existente."""
        # Atualiza o banco de dados
        self.db.update_one(
            "active_pair_traders",
            {"pair_trader_id": existing_trade['pair_trader_id']},
            {"active": True, "start_time": datetime.now()}
        )

        symbols = [existing_trade['target_symbol']] + existing_trade['cluster_symbols']
        
        for symbol in symbols:
            # Obter dados históricos
            if symbol not in self.candle_data:
                self.candle_data[symbol] = self.get_historical_data(symbol, '1m')

        pair_trader = PairTrader(existing_trade['pair_trader_id'], 
                                 existing_trade['target_symbol'], 
                                 existing_trade['cluster_symbols'], 
                                 existing_trade['entry_threshold'], 
                                 existing_trade['exit_threshold'], 
                                 existing_trade['window'], 
                                 interval='1m',
                                 pair_trade_executor=self.pair_trade_executor)
        self.active_pair_traders[existing_trade['pair_trader_id']] = pair_trader
        
        # Configurar stream
        for symbol in symbols:
            await self._initialize_data_stream(symbol, existing_trade['pair_trader_id'])
        
        return {"status": "success", "message": f"Trading restarted for {existing_trade['target_symbol']}"}


    async def _setup_new_trader(self, pair_trader_id, target_symbol, cluster_symbols, 
                                entry_threshold, exit_threshold, window, params):
        """Configura um novo trader e inicia o stream de dados."""

        symbols = [target_symbol] + cluster_symbols
        
        for symbol in symbols:
            # Obter dados históricos
            if symbol not in self.candle_data:
                self.candle_data[symbol] = self.get_historical_data(symbol, '1m')
            
        pair_trader = PairTrader(pair_trader_id, target_symbol, cluster_symbols, 
                                 entry_threshold, exit_threshold, window, interval='1m',
                                 pair_trade_executor=self.pair_trade_executor)
        self.active_pair_traders[pair_trader_id] = pair_trader

        # Salvar informações no banco de dados
        self.db.add_one(
            "active_pair_traders",
            {
                "pair_trader_id": pair_trader_id,
                **params,
                "active": True,
                "start_time": datetime.now(),
            }
        )
        
        # Configurar stream
        for symbol in symbols:
            await self._initialize_data_stream(symbol, pair_trader_id)
            
            
    async def _initialize_data_stream(self, symbol, trade_id):
        """Inicia o stream de dados para um símbolo específico."""
        if self.bm is None:
            raise RuntimeError("BinanceSocketManager (bm) não foi inicializado.")

        if symbol not in self.active_streams:
            self.active_streams.add(symbol)
            task = asyncio.create_task(stream_data_pair(symbol, trade_id, self.bm, self))
            self.background_tasks.append(task)
            
    def process_stream_message_pair(self, symbol, msg):
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

    def update_candle_data(self, symbol, candle_data, start_time):
        """Atualiza os dados de candle centralizados e notifica traders ativos."""
        # Adiciona o novo candle ao DataFrame centralizado
        if symbol in self.candle_data:
            df = self.candle_data[symbol]
            df.loc[start_time] = candle_data
            self.candle_data[symbol] = df
        
        # Notifica todas as instâncias de PairTrader para o símbolo quando um candle estiver completo
        for pair_trader_id, trader in self.active_pair_traders.items():
            
            # Filtrar trades apenas para o símbolo atualizado
            trades_for_symbol = [
                trade for trade in self.pair_trade_executor.get_opened_trades(activate=True)
                if trade['symbol'] == symbol
            ]
            
            for opened_pair_trade in trades_for_symbol:
                if trader.target_asset == symbol:
                    current_price = float(candle_data[3])  # Preço de fechamento
                    print(f"Check tralings do ativo {symbol} e preço atual em {current_price}.")

                    # Verifica e fecha ordens de SL, se necessário
                    self.pair_trade_executor.check_sl_orders(symbol)
                    self.pair_trade_executor.check_trailing_stop_target(symbol, current_price)
                    self.pair_trade_executor.check_trailing_stop_loss(symbol, current_price)
                    
            # Se o ativo faz parte do par, marque como atualizado
            if symbol in [trader.target_asset] + trader.cluster_assets:
                if pair_trader_id not in self.candle_sync:
                    self.candle_sync[pair_trader_id] = {}
                self.candle_sync[pair_trader_id][symbol] = start_time

                # Verifica se todos os ativos necessários já têm o mesmo timestamp
                required_assets = [trader.target_asset] + trader.cluster_assets
                timestamps = [
                    self.candle_sync[pair_trader_id].get(asset) for asset in required_assets
                ]
                if len(set(timestamps)) == 1 and timestamps[0] == start_time:
                    # Todos os ativos têm o mesmo timestamp
                    self._notify_pair_trader(trader, symbol)
                    
    def _notify_pair_trader(self, trader, symbol):
        """
        Notifica o PairTrader que um novo candle foi recebido para um dos ativos monitorados.
        """
        try:
            # Atualiza os dados necessários para o PairTrader e executa a estratégia
            dfs = [self.candle_data[asset] for asset in trader.cluster_assets]
            df_target = self.candle_data[trader.target_asset]
            trader.define_strategy(dfs, df_target)
        except Exception as e:
            print(f"Erro ao notificar PairTrader {trader.pair_trader_id}: {e}")
