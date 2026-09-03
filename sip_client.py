"""
Shared LiveKit API client factory used by every setup/reset/verify script.

Keeps connection handling (and future retry/backoff logic) in one place
instead of duplicated across four scripts.
"""

from contextlib import asynccontextmanager

from livekit import api

from config import Settings


@asynccontextmanager
async def lk_client(settings: Settings):
    """
    Usage:
        async with lk_client(settings) as lk_api:
            await lk_api.sip.list_inbound_trunk(...)
    """
    client = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        yield client
    finally:
        await client.aclose()