import asyncio


async def stream_data(symbol, bm, trader, manager):
    """Stream de dados da Binance para um símbolo e instância de trader específica."""
    # Verificação extra para garantir que `bm` não é `None`
    if bm is None:
        raise ValueError("BinanceSocketManager (bm) não foi inicializado corretamente.")

    async with bm.kline_socket(symbol=symbol, interval=trader.bar_length) as tscm:
        print(f"Streaming data for {symbol}")  # Log para confirmar o início do stream
        while True:
            try:
                msg = await tscm.recv()
                trader.stream_candles(msg)
            except Exception as e:
                print(f"Error while streaming data for {symbol}: {e}")
                break  # Quebra o loop em caso de erro para evitar loops infinitos
