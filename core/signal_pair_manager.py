from collections import defaultdict
from typing import Dict
from data.database import DataDB
from operations.pair_trade_executor import PairTradeExecutor

import mplfinance as mpf
import matplotlib.pyplot as plt
import os
import asyncio
from constants.defs import (CHAT_TELEGRAM_ID)
from core.telegram_bot import run_bot


class SignalPairManager:
    def __init__(self):
        # Armazena sinais como um dicionário onde as chaves são os símbolos e o valor é uma lista de sinais
        self.signals = defaultdict(list)
        self.last_processed_timestamp = None
        self.completed_tasks_count = 0
        self.db = DataDB()
        self.pair_trade_executor = PairTradeExecutor()
        
    def register_signal(self, pair_trader_id: str, signal: Dict, pair_trader=None):
        """Registra um sinal para um símbolo específico."""
        self.signals[pair_trader_id].append(signal)
        
        # Verifica se não há ordens abertas para o par de trading
        opened_trades = self.pair_trade_executor.get_opened_trades(activate=True)
        trades_for_pair = [trade for trade in opened_trades if trade["pair_trader_id"] == pair_trader_id]
        
        if not trades_for_pair:
            # Não há ordens em aberto, processa os sinais
            self.process_signals()
            
            if pair_trader:
                self.send_bot_message(signal, pair_trader)
            
        else:
            print(f"[{signal["target_asset"]}] Ordens abertas encontradas para {pair_trader_id}. Sinal registrado, mas não processado.")
            self.signals.clear()  # Limpa os sinais após a consulta
            
    def get_trade_params(self, pair_trader_id: str) -> dict:
        """Recupera os parâmetros de trade do banco de dados com base no trade_id."""
        trade_params = self.db.query_single("active_pair_traders", pair_trader_id=pair_trader_id)
        if not trade_params:
            return {}
        return trade_params

    def process_signals(self):
        """Processa sinais coletados e decide qual operação abrir, se houver."""
        signals = self.get_signals()
        print("verifica sinais", signals)

        # Processa todos os sinais

        # Inicializa uma lista para armazenar os sinais processados
        processed_signals = []

        # Itera sobre cada par (pair_trader_id, lista_de_sinais) no dicionário de sinais
        for pair_trader_id, signal_list in signals.items():
            # Obtém os parâmetros de trading para o trader atual
            trade_params = self.get_trade_params(pair_trader_id)
            
            # Cria uma tupla para cada sinal na lista de sinais e adiciona à lista processada
            for signal in signal_list:
                processed_signals.append((trade_params, signal))

        # A lógica de decisão com os sinais selecionados
        if len(processed_signals) > 0:
            for trade_params, signal in processed_signals:
                print(f"Abrindo operação para o sinal: {signal}")
                
                self.pair_trade_executor.execute_trade(trade_params, signal)



    def get_signals(self):
        """Retorna todos os sinais registrados e limpa o registro para o próximo candle."""
        signals = dict(self.signals)
        self.signals.clear()  # Limpa os sinais após a consulta
        return signals

    def check_signals(self):
        """
        Retorna os sinais atuais sem limpá-los.
        """
        return dict(self.signals)

    def send_bot_message(self, signal, pair_trader):
        # Gera o gráfico de candlestick e salva como imagem
        temp_images_dir = os.path.join(os.getcwd(), "temp_images")
        os.makedirs(temp_images_dir, exist_ok=True)
        img_path = os.path.join(temp_images_dir, "candle_chart.png")
    
        fig, ax = plt.subplots(figsize=(10, 6))
        mpf.plot(pair_trader.df.set_index("Time").tail(100), type="candle", ax=ax)
        plt.savefig(img_path)
        plt.close(fig)
        
        # Estrutura a mensagem para envio no Telegram
        title = f"################## \nSinal registrado para: \n{signal['pair_trader_id']}"
        message = f"""
        *{title}*
        
        - ID da Trade: `{signal['pair_trader_id']}`
        - Hora: `{signal['time']}`
        - Close: `{signal['close']}`
        - z_score: `{signal['z_score']}`
        - Sinal de Alta: `{signal['signal_up_pair1']}`
        - Sinal de Baixa: `{signal['signal_down_pair1']}`
        - Ativo: '{signal['target_asset']}'
        """

        # Envia a mensagem usando o bot do Telegram
        print("")
        print(message)
        print("")
        
        asyncio.create_task(run_bot([message, ("photo", img_path)], CHAT_TELEGRAM_ID))