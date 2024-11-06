import asyncio

async def stream_data(symbol, trade_id, bm, manager):
    """Stream de dados da Binance para um símbolo e gerencia candles completos no TraderManager."""
    if bm is None:
        raise ValueError("BinanceSocketManager (bm) não foi inicializado corretamente.")

    async with bm.kline_socket(symbol=symbol, interval=manager.active_trader_instances[trade_id].bar_length) as tscm:
        print(f"Streaming data for {symbol} with interval {manager.active_trader_instances[trade_id].bar_length}")  # Log para confirmar o início do stream
        while True:
            try:
                msg = await tscm.recv()
                manager.process_stream_message(symbol, msg)  # Envia a mensagem para o TraderManager
            except Exception as e:
                print(f"Error while streaming data for {symbol}: {e}")
                break
