# Source snapshot: fastapi/fastapi
# Upstream: https://github.com/fastapi/fastapi/blob/481660275ca94e9cece101831de5e47aaaf99860/fastapi/routing.py
send_keepalive, receive_keepalive = anyio.create_memory_object_stream[bytes](max_buffer_size=1)
async def _keepalive_inserter() -> None:
    """Read from the producer and forward to the output,
    inserting keepalive comments on timeout."""
    try:
        with anyio.fail_after(_PING_INTERVAL):
            data = await receive_stream.receive()
        await send_keepalive.send(data)
    except TimeoutError:
        await send_keepalive.send(KEEPALIVE_COMMENT)
