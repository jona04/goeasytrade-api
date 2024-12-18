from binance.client import Client
from binance.exceptions import BinanceAPIException
from data.database import DataDB
from core.config_pair_system_manager import ConfigPairSystemManager
import pandas as pd
from typing import Optional, Dict, Any
import math
from constants.defs import (
    BINANCE_KEY,
    BINANCE_TESTNET_KEY,
    BINANCE_SECRET,
    BINANCE_TESTNET_SECRET,
)

class PairTradeExecutor:
    def __init__(self):
        """
        Inicializa o TradeExecutor com a API Binance.
        :param binance_client: Instância do cliente da API Binance.
        """
        self.db = DataDB()
        self.client = Client(api_key=BINANCE_KEY, api_secret=BINANCE_SECRET, tld="com")
        self.config_pair_system_manager = ConfigPairSystemManager()
    # ------------------
    # MÉTODOS PRINCIPAIS
    # ------------------

    def execute_trade(self, trade_params, signal):
        """
        Método intermediário que recebe trade_params e signal,
        traduzindo-os para parâmetros necessários e executando o trade.
        :param trade_params: Parâmetros da operação (e.g., símbolo, estratégia).
        :param signal: Dados do sinal que disparou a operação.
        """
        try:
            symbol = trade_params["target_symbol"]
            position_side = "LONG" if signal["signal_up_pair1"] == 1 else "SHORT"
            
            # Obtém quantidade e alavancagem do banco
            quantity, balance = self.get_quantity(symbol)
            leverage = self.get_leverage(symbol)

            # Configura alavancagem
            self.client.futures_change_leverage(symbol = symbol, leverage = leverage)
        
            # Chama o método open_trade com os parâmetros traduzidos
            side = "BUY" if position_side == "LONG" else "SELL"
            print(f"Abrindo trade {symbol} | {side} | qtt = {quantity} | {position_side} | balance = {balance}!")
            order = self.open_trade(
                symbol=symbol,
                side = side,
                quantity=quantity,
                position_side=position_side
            )
            
            if not order:
                print("Erro ao abrir a posição. Operação abortada.")
                return None
            
            # Salva a ordem no banco
            self.log_pair_order(order)

            entry_price = float(signal['close'])
            
            # Calcula SL e TP
            sl_price = self.calculate_stop_loss(entry_price, trade_params, position_side)
            trailing_stop_target_price = self.calculate_trailing_stop_target(entry_price, trade_params, position_side)
            trailing_stop_loss_price = self.calculate_trailing_stop_loss(entry_price, trade_params, position_side)

            # Salva os detalhes iniciais do trade (criação ou atualização)
            self.edit_opened_trades(
                opened_pair_trader_id=order["orderId"],
                updates={
                    "pair_trader_id": trade_params["pair_trader_id"],
                    "entry_price": entry_price,
                    "symbol": symbol,
                    "position_side": position_side,
                    "quantity": quantity,
                    "stop_loss_order_id": None,  # Atualizado posteriormente
                    "take_profit_order_id": None,  # Atualizado posteriormente
                    "activate": True,
                    "close_type": None,
                    "trailing_stop_target_price": trailing_stop_target_price,
                    "trailing_stop_loss_price": trailing_stop_loss_price,
                    "trailing_stop_target_price": trailing_stop_target_price,
                    "trailing_stop_loss_price": trailing_stop_loss_price,
                    "stop_loss_price": sl_price,
                    "break_even": False,
                    "trailing_stop_target": trade_params['trailing_stop_target'],
                    "trailing_stop_loss": trade_params['trailing_stop_loss'],
                    "stop_loss": trade_params['sl_percent'],
                    "timestamp": pd.Timestamp.now(),
                },
                upsert=True
            )
            print(f"Ordem {order["orderId"]} salva no banco")
            
            # Define Stop Loss e atualiza no banco
            if sl_price:
                sl_order = self.set_stop_loss(symbol, quantity, position_side, sl_price)
                if sl_order:
                    self.edit_opened_trades(
                        opened_pair_trader_id=order["orderId"],
                        updates={"stop_loss_order_id": sl_order["orderId"]}
                    )
 
            return order
        except Exception as e:
            print(f"Erro ao executar trade: {e}")
            return None
    
    def get_opened_trades(self, activate: Optional[bool] = None, break_even: Optional[bool] = None):
        """
        Retorna trades abertos da coleção `opened_trades` com base nos filtros fornecidos.
        :param activate: True para trades ativos, False para inativos.
        :param break_even: True para trades com parcial ativada, False para sem parcial.
        :return: Lista de trades filtrados.
        """
        try:
            query = {}
            if activate is not None:
                query["activate"] = activate
            if break_even is not None:
                query["break_even"] = break_even

            trades = list(self.db.query_all("opened_pair_trades", **query))
            return trades
        except Exception as e:
            print(f"Erro ao buscar opened_trades: {e}")
            return []
    
    def edit_opened_trades(self, opened_pair_trader_id: int, updates: Dict[str, Any], upsert: bool = False):
        """
        Edita ou cria um trade específico na coleção `opened_trades`.
        :param opened_pair_trader_id: ID do trade a ser atualizado.
        :param updates: Dicionário contendo os campos a serem atualizados.
        :param upsert: Se True, cria o documento caso ele não exista.
        """
        try:
            filter_criteria = {"_id": opened_pair_trader_id}
            result = self.db.update_one(
                collection="opened_pair_trades",
                filter_criteria=filter_criteria,
                update_values=updates,
                upsert=upsert
            )
            
            print(f"Trade aberto {opened_pair_trader_id} atualizado!")
            
            if result.matched_count == 0 and not upsert:
                return {"status": "error", "message": f"Trade {opened_pair_trader_id} não encontrado."}
            if result.modified_count == 0 and not upsert:
                return {"status": "warning", "message": f"Nenhuma modificação foi feita para o trade {opened_pair_trader_id}."}
            
            return {"status": "success", "message": f"Trade aberto {opened_pair_trader_id} atualizado com sucesso."}
        except Exception as e:
            print(f"Erro ao atualizar trade {opened_pair_trader_id}: {e}")
            return {"status": "error", "message": str(e)}


        
    def open_trade(self, symbol, side, quantity, position_side):
        """
        Abre uma posição no mercado futuro.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :param side: 'BUY' para abrir Long, 'SELL' para abrir Short.
        :param quantity: Quantidade a negociar.
        :param position_side: 'LONG' ou 'SHORT'.
        :param sl_price: (Opcional) Preço para Stop Loss.
        :param tp_price: (Opcional) Preço para Take Profit.
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
                positionSide=position_side
            )
            print(f"Posição aberta: {order['orderId']}")

            return order
        except BinanceAPIException as e:
            print(f"Erro ao abrir posição: {e}")
            return None
    
    
    def check_sl_orders(self, symbol):
        """
        Verifica as ordens de TP e SL associadas a opened_trades abertos.
        Atualiza o banco de dados caso uma ordem tenha sido executada e cancela as ordens restantes.
        """
        try:
            # Obtém todas as ordens abertas na Binance
            open_orders = self.client.futures_get_open_orders()
            open_order_ids = {order["orderId"] for order in open_orders}

            # Obtém todos os opened_trades ativos do banco
            active_trades = self.db.query_all("opened_pair_trades", activate=True)

            for trade in active_trades:
                if trade["symbol"] == symbol:
                    open_order_id = trade["_id"]
                    stop_loss_order_id = trade.get("stop_loss_order_id")

                    # Verifica se as ordens SL ainda estão na lista de ordens abertas
                    sl_active = stop_loss_order_id in open_order_ids

                    if not sl_active:
                        close_type = "SL"

                        self.cancel_order(trade["symbol"], stop_loss_order_id)
                        
                        # Atualiza o banco de dados
                        self.edit_opened_trades(
                            opened_pair_trader_id=int(open_order_id),
                            updates={
                                "activate": False,
                                "close_type": close_type,
                                "stop_loss_order_id": None,
                                "take_profit_order_id": None,
                            }
                        )
                        print(f"[{symbol}] Trade {open_order_id} atualizado: fechado por {close_type}.")
                    
        except Exception as e:
            print(f"Erro ao verificar e fechar ordens TP/SL: {e}")



    def check_trailing_stop_target(self, symbol, current_price):
        """
        Verifica as ordens de TP e SL associadas a opened_trades abertos.
        Atualiza o banco de dados caso uma ordem tenha sido executada e cancela as ordens restantes.
        """
        try:
            # Obtém todos os opened_trades ativos do banco
            active_trades = self.db.query_all("opened_pair_trades", activate=True)

            for opened_pair_trade in active_trades:
                if opened_pair_trade["symbol"] == symbol:
                    symbol = opened_pair_trade["symbol"]
                    entry_price = opened_pair_trade["entry_price"]
                    position_side = opened_pair_trade["position_side"]
                    trailing_stop_target = opened_pair_trade["trailing_stop_target"]
                    quantity = opened_pair_trade["quantity"]
                    stop_loss_order_id = opened_pair_trade["stop_loss_order_id"]
                    
                    # Calcula o lucro percentual
                    profit_percent = self.calculate_profit_percent(entry_price, current_price, position_side)
                    
                    # Verifica se o lucro ultrapassou o limiar
                    if profit_percent >= trailing_stop_target:
                        print(f"[{symbol}] Fechando trade aberto {opened_pair_trade['_id']}. Side = {position_side} | Profit = {profit_percent} | trailing_stop_target = {trailing_stop_target}")
                        
                        order = self.close_operation(opened_pair_trade, position_side, symbol, quantity, "trailing_stop_target")
                        
                        self.log_pair_order(order)
                        
                        # Cancel SL
                        self.cancel_order(symbol, stop_loss_order_id)
                    
        except Exception as e:
            print(f"Erro ao verificar e fechar ordens TP/SL: {e}")
            
            
    def check_trailing_stop_loss(self, symbol, current_price):
        """
        Verifica as ordens de TP e SL associadas a opened_trades abertos.
        Atualiza o banco de dados caso uma ordem tenha sido executada e cancela as ordens restantes.
        """
        try:
            # Obtém todos os opened_trades ativos do banco
            active_trades = self.db.query_all("opened_pair_trades", activate=True)

            for opened_pair_trade in active_trades:
                if opened_pair_trade["symbol"] == symbol:
                    symbol = opened_pair_trade["symbol"]
                    entry_price = opened_pair_trade["entry_price"]
                    position_side = opened_pair_trade["position_side"]
                    trailing_stop_loss = opened_pair_trade["trailing_stop_loss"]
                    quantity = opened_pair_trade["quantity"]
                    stop_loss_order_id = opened_pair_trade["stop_loss_order_id"]
                    
                    # Calcula o lucro percentual
                    profit_percent = self.calculate_profit_percent(entry_price, current_price, position_side)
                    
                    # Verifica se o lucro ultrapassou o limiar
                    if profit_percent <= trailing_stop_loss:
                        print(f"[{symbol}] Fechando trade aberto {opened_pair_trade['_id']}. Side = {position_side} | Profit = {profit_percent} | trailing_stop_loss = {trailing_stop_loss}")
                        
                        order = self.close_operation(opened_pair_trade, position_side, symbol, quantity, "trailing_stop_loss")
                        
                        self.log_pair_order(order)
                        
                        # Cancel SL
                        self.cancel_order(symbol, stop_loss_order_id)
                    
        except Exception as e:
            print(f"Erro ao verificar e fechar ordens TP/SL: {e}")

    def close_operation(self, opened_pair_trade, position_side, symbol, quantity, close_type):
        # Fecha a posição
        side = "SELL" if position_side == "LONG" else "BUY"
        order = self.client.futures_create_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
            positionSide=position_side
        )
        
        # Atualiza o banco de dados
        self.edit_opened_trades(
            opened_pair_trader_id=int(opened_pair_trade['_id']),
            updates={
                "activate": False,
                "close_type": close_type,
                "stop_loss_order_id": None,
            }
        )
        
        # Retorna saldo atual e atualiza available_balance
        balance = self.get_available_balance()
        if balance:
            self.config_pair_system_manager.update_system_available_balance(balance)
            
        return order
    
    def check_zscore_change(self, opened_pair_trade, z_score):
        """
        Verifica se o z score mudou de sinal. Caso sim entao encerra operação
        :param opened_pair_trade: Trade aberto ativo.
        :param current_price: Preço atual do mercado.
        """
        try:
            if not opened_pair_trade:
                print(f"Trade aberto {opened_pair_trade['_id']} não encontrado.")
                return

            print(f"[{opened_pair_trade["symbol"]}] Analisando Z-Score para {opened_pair_trade['_id']}: {z_score}.")
            
            position_side = opened_pair_trade["position_side"]
            trailing_stop_loss = opened_pair_trade["trailing_stop_loss"]
            symbol = opened_pair_trade["symbol"]
            quantity = opened_pair_trade["quantity"]
            stop_loss_order_id = opened_pair_trade["stop_loss_order_id"]
            
            close_operation = False
            
            if z_score > -1 and position_side == "LONG":
                close_operation = True
            elif z_score < 1 and position_side == "SHORT":
                close_operation = True
            
            if close_operation:
                
                print(f"[{symbol}]Fechando trade aberto {opened_pair_trade['_id']}. Side = {position_side} | z_score = {z_score}")
                    
                # Fecha a posição
                order = self.close_operation(opened_pair_trade, position_side, symbol, quantity, "z_score")

                self.log_pair_order(order)
                    
                # Cancel SL
                self.cancel_order(symbol, stop_loss_order_id)
                
        except Exception as e:
            print(f"[{opened_pair_trade["symbol"]}] Erro ao verificar Break Even para trade {opened_pair_trade['_id']}: {e}")
            
    # ------------------
    # CÁLCULOS
    # ------------------

    def calculate_take_profit(self, entry_price, trade_params, position_side):
        """
        Calcula o preço de Take Profit.
        :param entry_price: Preço de entrada.
        :param position_side: 'LONG' ou 'SHORT'.
        :param multiplier: Fator de multiplicação para calcular TP.
        """
        sl_percent = abs(float(trade_params['sl_percent']))
        
        if position_side == "LONG":
            return round( entry_price + (entry_price * sl_percent),7)
        else:
            return round( entry_price - (entry_price * sl_percent),7)

    def calculate_stop_loss(self, entry_price, trade_params, position_side):
        """
        Calcula o preço de Stop Loss.
        :param entry_price: Preço de entrada.
        :param position_side: 'LONG' ou 'SHORT'.
        :param multiplier: Fator de multiplicação para calcular SL.
        """
        sl_percent = abs(float(trade_params['sl_percent']))
        
        precision = 3
        if trade_params["target_symbol"] == 'ALPHAUSDT':
            precision = 5
        elif trade_params["target_symbol"] == 'VIDTUSDT':
            precision = 7
        elif trade_params["target_symbol"] == 'VIDTUSDT':
            precision = 5
            
        if position_side == "LONG":
            return round( entry_price - (entry_price * sl_percent),precision)
        else:
            return round( entry_price + (entry_price * sl_percent),precision)
        
    def calculate_trailing_stop_loss(self, entry_price, trade_params, position_side):
        """
        Calcula o preço de Stop Loss.
        :param entry_price: Preço de entrada.
        :param position_side: 'LONG' ou 'SHORT'.
        :param trade_params: Parâmetros do trade (incluindo trailing_stop_loss).
        """
        trailing_stop_loss = abs(float(trade_params['trailing_stop_loss']))

        precision = 3
        if trade_params["target_symbol"] == 'ALPHAUSDT':
            precision = 5
        elif trade_params["target_symbol"] == 'VIDTUSDT':
            precision = 7
        elif trade_params["target_symbol"] == 'VIDTUSDT':
            precision = 5
            
        if position_side == "LONG":
            # Stop Loss para LONG deve ser abaixo do preço de entrada.
            return round(entry_price * (1 - trailing_stop_loss), precision)
        else:
            # Stop Loss para SHORT deve ser acima do preço de entrada.
            return round(entry_price * (1 + trailing_stop_loss), precision)


    def calculate_trailing_stop_target(self, entry_price, trade_params, position_side):
        """
        Calcula o preço de Stop Target.
        :param entry_price: Preço de entrada.
        :param position_side: 'LONG' ou 'SHORT'.
        :param trade_params: Parâmetros do trade (incluindo trailing_stop_target).
        """
        trailing_stop_target = abs(float(trade_params['trailing_stop_target']))

        precision = 3
        if trade_params["target_symbol"] == 'ALPHAUSDT':
            precision = 5
        elif trade_params["target_symbol"] == 'VIDTUSDT':
            precision = 7
        elif trade_params["target_symbol"] == 'VIDTUSDT':
            precision = 5
            
        if position_side == "LONG":
            # Stop Target para LONG deve ser acima do preço de entrada.
            return round(entry_price * (1 + trailing_stop_target), precision)
        else:
            # Stop Target para SHORT deve ser abaixo do preço de entrada.
            return round(entry_price * (1 - trailing_stop_target), precision)
        
    # ------------------
    # PERSISTÊNCIA
    # ------------------

    def log_pair_order(self, order):
        """
        Salva uma ordem na coleção `orders`.
        """
        self.db.add_one("orders", order)
        print(f"Ordem {order['orderId']} salva no banco!")

    # -------------------
    # GESTÃO DE RISCOS
    # -------------------

    def set_stop_loss(self, symbol, quantity, position_side, sl_price):
        """
        Define uma ordem de Stop Loss para proteger a posição.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :param quantity: Quantidade a proteger.
        :param position_side: 'LONG' ou 'SHORT'.
        :param sl_price: Preço de disparo do Stop Loss.
        """
        try:
            # Cria o novo SL
            side = "SELL" if position_side == "LONG" else "BUY"
            print(f"Abrindo SL {symbol} | {side} | {sl_price} | {quantity} | {position_side}")
            sl_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="STOP_MARKET",
                stopPrice=sl_price,
                quantity=quantity,
                positionSide=position_side
            )
            print(f"Stop Loss definido: {sl_order['orderId']}")
            
            self.log_pair_order(sl_order)
            return sl_order
        except BinanceAPIException as e:
            print(f"Erro ao definir Stop Loss: {e}")
            return None

    def set_take_profit(self, symbol, quantity, position_side, tp_price):
        """
        Define uma ordem de Take Profit para a posição.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :param quantity: Quantidade alvo.
        :param position_side: 'LONG' ou 'SHORT'.
        :param tp_price: Preço alvo para encerrar a posição.
        """
        try:
            side = "SELL" if position_side == "LONG" else "BUY"
            print(f"Abrindo TP {symbol} | {side} | {tp_price} | {quantity} | {position_side}")
            tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp_price,
                quantity=quantity,
                positionSide=position_side
            )
            print(f"Take Profit definido: {tp_order['orderId']}")
            
            self.log_pair_order(tp_order)
            return tp_order
        except BinanceAPIException as e:
            print(f"Erro ao definir Take Profit: {e}")
            return None

    def get_available_balance(self, asset='USDT'):
        """
        Obtém o saldo disponível em USDT na conta de Futuros.

        :param client: Instância autenticada do cliente da Binance API.
        """
        try:
            # Consulta informações da conta de Futuros
            account_info = self.client.futures_account()
            
            # Itera sobre a lista de ativos para encontrar o saldo disponível
            for item in account_info['assets']:
                if item['asset'] == asset:
                    available_balance = float(item['walletBalance'])
                    return available_balance
            
            # Se o ativo não for encontrado, levanta uma exceção
            raise ValueError(f"Ativo {asset} não encontrado na conta de Futuros.")

        except Exception as e:
            print(f"Erro ao obter o saldo disponível: {e}")
            return None

    # ------------------
    # MÉTODOS AUXILIARES
    # ------------------

    def get_quantity(self, symbol):
        """
        Obtém a quantidade configurada para um símbolo específico do banco de dados.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :return: Quantidade configurada para o símbolo.
        """
        try:
            config_pair_system = self.db.query_single("config_pair_system")
            balance = (config_pair_system['available_balance']-5)
            percentage_of_total = config_pair_system['percentage_of_total']
            quantity_in_dolar = balance / percentage_of_total
            
            price_data = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(price_data['price'])
        
            quantity = math.floor(quantity_in_dolar / current_price)
            
            if quantity:
                return quantity, balance
            else:
                raise ValueError(f"Configuração de quantidade não encontrada para {symbol}.")
        except Exception as e:
            print(f"Erro ao obter quantidade para {symbol}: {e}")
            return None

    def get_leverage(self, symbol):
        """
        Obtém a alavancagem configurada para um símbolo específico do banco de dados.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :return: Alavancagem configurada para o símbolo.
        """
        try:
            config_pair_assets = self.db.query_single("config_pair_assets", symbol=symbol)
            if config_pair_assets and "leverage" in config_pair_assets:
                return config_pair_assets["leverage"]
            else:
                print(f"Configuração de alavancagem não encontrada para {symbol}.")
                return 1
        except Exception as e:
            print(f"Erro ao obter alavancagem para {symbol}: {e}")
            return None
        
        
    def get_entry_price(self, order_id):
        try:
            order = self.client.futures_account_trades(orderId = order_id)
            if order:
                return order['price']
        except Exception as e:
            print(f"Erro ao obter entry price para {order_id}: {e}")
            return None
        
    
    def cancel_order(self, symbol, order_id):
        """
        Cancela uma ordem específica.
        :param symbol: Ativo (ex: 'ADAUSDT').
        :param order_id: ID da ordem a ser cancelada.
        """
        try:
            self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            print(f"Ordem {order_id} cancelada para o símbolo {symbol}.")
        except BinanceAPIException as e:
            print(f"Erro ao cancelar a ordem {order_id} para {symbol}: {e}")
            
    
    def adjust_stop_loss(self, opened_pair_trade, new_sl_price):
        """
        Ajusta o Stop Loss de uma posição após o encerramento parcial.
        :param opened_trade: Trade aberto ativo.
        :param new_sl_price: Novo preço de Stop Loss (Break Even).
        """
        try:
            # Recupera os detalhes do trade
            opened_pair_trade = self.db.query_single("opened_pair_trades", _id=opened_pair_trade['_id'])
            if not opened_pair_trade:
                print(f"Trade aberto {opened_pair_trade['_id']} não encontrado.")
                return

            symbol = opened_pair_trade["symbol"]
            position_side = opened_pair_trade["position_side"]
            quantity, _ = self.get_quantity(symbol)

            # Cancela o Stop Loss atual, se existir
            stop_loss_order_id = opened_pair_trade.get("stop_loss_order_id")
            if stop_loss_order_id:
                self.cancel_order(symbol, stop_loss_order_id)

            # Define um novo Stop Loss
            sl_order = self.set_stop_loss(symbol, quantity, position_side, new_sl_price)
            if sl_order:
                # Atualiza o banco de dados com o novo SL
                self.edit_opened_trades(
                    opened_pair_trader_id=opened_pair_trade['_id'],
                    updates={
                        "stop_loss_order_id": sl_order["orderId"],
                        "stop_loss": new_sl_price
                        }
                )
                print(f"Novo Stop Loss ajustado para {new_sl_price} no trade {opened_pair_trade['_id']}.")
        except Exception as e:
            print(f"Erro ao ajustar Stop Loss para trade {opened_pair_trade['_id']}: {e}")
         
    def calculate_profit_percent(self, entry_price, current_price, position_side):
        """
        Calcula o lucro percentual para um trade.
        :param entry_price: Preço de entrada.
        :param current_price: Preço atual.
        :param position_side: 'LONG' ou 'SHORT'.
        :return: Lucro percentual.
        """
        if position_side == "LONG":
            return (current_price - entry_price) / entry_price
        else:
            return (entry_price - current_price) / entry_price
