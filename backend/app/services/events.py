"""Server-sent events as a change signal, not a data feed.

A channel polls a cheap fingerprint of the relevant state server-side and
emits a `change` event only when it moves; the client refetches through its
normal queries. Payloads stay tiny and the repositories/DTOs are reused
unchanged.
"""

import asyncio
from collections.abc import AsyncGenerator, Callable

POLL_SECONDS = 3.0
KEEPALIVE_EVERY = 5  # cycles → one comment line every ~15s keeps proxies open


async def change_stream(fingerprint: Callable[[], str]) -> AsyncGenerator[str, None]:
    last: str | None = None
    cycles = 0
    while True:
        current = await asyncio.to_thread(fingerprint)
        if current != last:
            last = current
            yield "event: change\ndata: 1\n\n"
        else:
            cycles += 1
            if cycles >= KEEPALIVE_EVERY:
                cycles = 0
                yield ": keepalive\n\n"
        await asyncio.sleep(POLL_SECONDS)
