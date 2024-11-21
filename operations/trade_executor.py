from binance.client import Client
from binance.exceptions import BinanceAPIException
from data.database import DataDB
import pandas as pd
from binance.client import Client
from constants.defs import (
    BINANCE_KEY,
    BINANCE_TESTNET_KEY,
    BINANCE_SECRET,
    BINANCE_TESTNET_SECRET,
)

class TradeExecutor:
    def __init__(self):
        """
        Inicializa o TradeExecutor com a API Binance.
        :param binance_client: Instância do cliente da API Binance.
        """
        self.db = DataDB()
        self.client = Client(api_key=BINANCE_KEY, api_secret=BINANCE_SECRET, tld="com")
        
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
            symbol = trade_params["symbol"]
            position_side = "LONG" if signal["SIGNAL_UP"] == 1 else "SHORT"
            
            # Obtém quantidade e alavancagem do banco
            quantity = self.get_quantity(symbol)
            leverage = self.get_leverage(symbol)

            # Configura alavancagem
            self.client.futures_change_leverage(symbol = symbol, leverage = leverage)
        
            # Chama o método open_trade com os parâmetros traduzidos
            order = self.open_trade(
                symbol=symbol,
                side="BUY" if position_side == "LONG" else "SELL",
                quantity=quantity,
                position_side=position_side
            )
            
            if not order:
                print("Erro ao abrir a posição. Operação abortada.")
                return None
            
            # Salva a ordem no banco
            self.log_order(order)
            
            # Verifica detalhes da ordem aberta
            opened_order = self.client.futures_account_trades(symbol = symbol, orderId=order['orderId'])
            if not opened_order or not isinstance(opened_order, list) or len(opened_order) == 0:
                print("Erro com ordem aberta. Não foi possivel adicionar SL e TP.")
                return None
            
            # Calcula SL e TP
            sl_price = self.calculate_stop_loss(opened_order, trade_params, position_side)
            tp_price = self.calculate_take_profit(opened_order, trade_params, position_side)
            
            # Salva os detalhes iniciais do trade (criação ou atualização)
            self.db.update_trade_status(
                open_order_id=order["orderId"],
                trade_id=trade_params["trade_id"],
                symbol=symbol,
                positionSide=position_side,
                quantity=quantity,
                stop_loss_order_id=None,  # Atualizado posteriormente
                take_profit_order_id=None,  # Atualizado posteriormente
                activate=True,
                close_type=None,
                take_profit=tp_price,
                stop_loss=sl_price,
                break_even=False,
                timestamp=pd.Timestamp.now(),
            )

            # Define Stop Loss e atualiza no banco
            if sl_price:
                sl_order = self.set_stop_loss(symbol, quantity, position_side, sl_price)
                if sl_order:
                    self.db.update_trade_status(
                        open_order_id=order["orderId"],
                        stop_loss_order_id=sl_order["orderId"],
                    )

            # Define Take Profit e atualiza no banco
            if tp_price:
                tp_order = self.set_take_profit(symbol, quantity, position_side, tp_price)
                if tp_order:
                    self.db.update_trade_status(
                        open_order_id=order["orderId"],
                        take_profit_order_id=tp_order["orderId"],
                    )

            return order
        except Exception as e:
            print(f"Erro ao executar trade: {e}")
            return None
        
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
            print(f"Posição aberta: {order}")

            return order
        except BinanceAPIException as e:
            print(f"Erro ao abrir posição: {e}")
            return None
    
    def check_and_close_tp_sl_orders(self):
        """
        Verifica as ordens de TP e SL associadas a trades abertos.
        Atualiza o banco de dados caso uma ordem tenha sido executada e cancela as ordens restantes.
        """
        try:
            # Obtém todas as ordens abertas na Binance
            open_orders = self.client.futures_get_open_orders()
            open_order_ids = {order["orderId"] for order in open_orders}

            # Obtém todos os trades ativos do banco
            active_trades = self.db.query_all("trades", activate=True)

            for trade in active_trades:
                open_order_id = trade["_id"]
                take_profit_order_id = trade.get("take_profit_order_id")
                stop_loss_order_id = trade.get("stop_loss_order_id")

                # Verifica se as ordens TP e SL ainda estão na lista de ordens abertas
                tp_active = take_profit_order_id in open_order_ids
                sl_active = stop_loss_order_id in open_order_ids

                # Determina o motivo do fechamento
                if not tp_active or not sl_active:
                    close_type = "TP" if not tp_active else "SL"

                    # Cancela a ordem restante
                    if close_type == "TP" and sl_active:
                        self.cancel_order(trade["symbol"], stop_loss_order_id)
                    elif close_type == "SL" and tp_active:
                        self.cancel_order(trade["symbol"], take_profit_order_id)

                    # Atualiza o banco de dados
                    self.db.update_one(
                        "trades",
                        {"_id": open_order_id},
                        {
                            "activate": False,
                            "close_type": close_type,
                            "stop_loss_order_id": None,
                            "take_profit_order_id": None,
                        }
                    )
                    print(f"Trade {open_order_id} atualizado: fechado por {close_type}.")

        except Exception as e:
            print(f"Erro ao verificar e fechar ordens TP/SL: {e}")

            
    # ------------------
    # CÁLCULOS
    # ------------------

    def calculate_take_profit(self, opened_order, trade_params, position_side):
        """
        Calcula o preço de Take Profit.
        :param entry_price: Preço de entrada.
        :param position_side: 'LONG' ou 'SHORT'.
        :param multiplier: Fator de multiplicação para calcular TP.
        """
        price = float(opened_order[0]['price'])
        sl_percent = abs(float(trade_params['sl_percent']))
        
        if position_side == "LONG":
            return round( price + (price * sl_percent),5)
        else:
            return round( price - (price * sl_percent),5)

    def calculate_stop_loss(self, opened_order, trade_params, position_side):
        """
        Calcula o preço de Stop Loss.
        :param entry_price: Preço de entrada.
        :param position_side: 'LONG' ou 'SHORT'.
        :param multiplier: Fator de multiplicação para calcular SL.
        """
        price = float(opened_order[0]['price'])
        sl_percent = abs(float(trade_params['sl_percent']))
        
        if position_side == "LONG":
            return round( price - (price * sl_percent),5)
        else:
            return round( price + (price * sl_percent),5)
        

    # ------------------
    # PERSISTÊNCIA
    # ------------------

    def log_order(self, order):
        """
        Salva uma ordem na coleção `orders`.
        """
        self.db.add_one("orders", order)

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
            sl_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="STOP_MARKET",
                stopPrice=sl_price,
                quantity=quantity,
                positionSide=position_side
            )
            print(f"Stop Loss definido: {sl_order}")
            
            self.log_order(sl_order)
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
            tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp_price,
                quantity=quantity,
                positionSide=position_side
            )
            print(f"Take Profit definido: {tp_order}")
            
            self.log_order(tp_order)
            return tp_order
        except BinanceAPIException as e:
            print(f"Erro ao definir Take Profit: {e}")
            return None

    
    def activate_break_even(self, trade):
        """
        Ativa o Break Even para um trade.
        :param trade: Dicionário com informações do trade.
        """
        try:
            symbol = trade["symbol"]
            position_side = trade["positionSide"]
            quantity = trade["quantity"]
            entry_price = trade["entry_price"]

            # Remove a ordem de Stop Loss atual, se existir
            stop_loss_order_id = trade.get("stop_loss_order_id")
            if stop_loss_order_id:
                self.cancel_order(symbol, stop_loss_order_id)

            # Define um novo Stop Loss no ponto de entrada
            sl_order = self.set_stop_loss(symbol, quantity, position_side, entry_price)
            if sl_order:
                # Atualiza o banco de dados com o novo Stop Loss
                self.db.update_trade_status(
                    open_order_id=trade["_id"],
                    stop_loss_order_id=sl_order["orderId"],
                    break_even=True
                )
                print(f"Break Even ativado para o trade {trade['_id']}.")
        except Exception as e:
            print(f"Erro ao ativar Break Even para o trade {trade['_id']}: {e}")
        
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
            config = self.db.query_single("config_assets", symbol=symbol)
            if config and "quantity" in config:
                return config["quantity"]
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
            config = self.db.query_single("config_assets", symbol=symbol)
            if config and "leverage" in config:
                return config["leverage"]
            else:
                raise ValueError(f"Configuração de alavancagem não encontrada para {symbol}.")
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
            
            
    def close_partial_position(self, open_order_id, percentage):
        """
        Fecha parcialmente uma posição aberta.
        :param open_order_id: ID único do trade ativo.
        :param percentage: Percentual da posição a ser encerrada.
        """
        try:
            # Recupera os detalhes do trade
            trade = self.db.query_single("trades", _id=open_order_id)
            if not trade:
                print(f"Trade {open_order_id} não encontrado.")
                return

            symbol = trade["symbol"]
            position_side = trade["positionSide"]
            total_quantity = trade["quantity"]
            partial_quantity = total_quantity * (percentage / 100)

            # Fecha a posição parcial
            side = "SELL" if position_side == "LONG" else "BUY"
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=partial_quantity,
                positionSide=position_side
            )

            # Atualiza o banco de dados com os detalhes do encerramento parcial
            remaining_quantity = total_quantity - partial_quantity
            self.db.update_partial_close(
                open_order_id,
                closed_percentage=percentage,
                remaining_quantity=remaining_quantity,
                break_even_price=trade["entry_price"]
            )
            print(f"Parcial de {percentage}% encerrada para trade {open_order_id}.")
        except Exception as e:
            print(f"Erro ao fechar posição parcial para trade {open_order_id}: {e}")

    
    def adjust_stop_loss(self, open_order_id, new_sl_price):
        """
        Ajusta o Stop Loss de uma posição após o encerramento parcial.
        :param open_order_id: ID único do trade ativo.
        :param new_sl_price: Novo preço de Stop Loss (Break Even).
        """
        try:
            # Recupera os detalhes do trade
            trade = self.db.query_single("trades", _id=open_order_id)
            if not trade:
                print(f"Trade {open_order_id} não encontrado.")
                return

            symbol = trade["symbol"]
            position_side = trade["positionSide"]
            remaining_quantity = trade["remaining_quantity"]

            # Cancela o Stop Loss atual, se existir
            stop_loss_order_id = trade.get("stop_loss_order_id")
            if stop_loss_order_id:
                self.cancel_order(symbol, stop_loss_order_id)

            # Define um novo Stop Loss
            sl_order = self.set_stop_loss(symbol, remaining_quantity, position_side, new_sl_price)
            if sl_order:
                # Atualiza o banco de dados com o novo SL
                self.db.update_trade_status(
                    open_order_id=open_order_id,
                    stop_loss_order_id=sl_order["orderId"]
                )
                print(f"Novo Stop Loss ajustado para {new_sl_price} no trade {open_order_id}.")
        except Exception as e:
            print(f"Erro ao ajustar Stop Loss para trade {open_order_id}: {e}")
    
    def monitor_tp_sl_for_remaining_position(self, open_order_id):
        """
        Monitora a posição restante para fechamento no TP ou no novo SL ajustado.
        :param open_order_id: ID único do trade ativo.
        """
        try:
            # Recupera os detalhes do trade
            trade = self.db.query_single("trades", _id=open_order_id)
            if not trade or not trade.get("activate", False):
                print(f"Trade {open_order_id} não está ativo.")
                return

            symbol = trade["symbol"]
            remaining_quantity = trade["remaining_quantity"]
            tp_price = trade.get("take_profit")
            sl_price = trade.get("stop_loss")

            # Recupera o preço atual do mercado
            current_price = float(self.client.futures_mark_price(symbol=symbol)["markPrice"])

            # Verifica se o preço atingiu o TP ou o SL
            if tp_price and current_price >= tp_price:
                print(f"Take Profit atingido para trade {open_order_id}.")
                self.close_remaining_position(open_order_id, reason="TP")
            elif sl_price and current_price <= sl_price:
                print(f"Stop Loss ajustado (Break Even) atingido para trade {open_order_id}.")
                self.close_remaining_position(open_order_id, reason="Break Even")
        except Exception as e:
            print(f"Erro ao monitorar TP/SL para trade {open_order_id}: {e}")

    def close_remaining_position(self, open_order_id, reason):
        """
        Encerra a posição restante de um trade e atualiza o banco de dados.
        :param open_order_id: ID único do trade ativo.
        :param reason: Motivo do encerramento ('TP' ou 'Break Even').
        """
        try:
            # Recupera os detalhes do trade
            trade = self.db.query_single("trades", _id=open_order_id)
            if not trade:
                print(f"Trade {open_order_id} não encontrado.")
                return

            symbol = trade["symbol"]
            position_side = trade["positionSide"]
            remaining_quantity = trade["remaining_quantity"]

            # Fecha a posição restante
            side = "SELL" if position_side == "LONG" else "BUY"
            close_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=remaining_quantity,
                positionSide=position_side
            )

            # Atualiza o banco de dados para refletir o encerramento total
            self.db.update_trade_status(
                open_order_id=open_order_id,
                activate=False,
                close_type=reason,
                stop_loss_order_id=None,
                take_profit_order_id=None,
            )
            print(f"Trade {open_order_id} encerrado por {reason}.")
        except Exception as e:
            print(f"Erro ao encerrar posição restante para trade {open_order_id}: {e}")

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