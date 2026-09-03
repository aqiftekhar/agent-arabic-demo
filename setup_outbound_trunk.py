"""
Creates the outbound SIP trunk LiveKit uses to send REFER/transfer traffic
back to FreePBX (e.g. the "press 0 for operator" cold transfer).

Run once, after setup_sip.py. Safe to re-run against a clean state
(reset_sip.py first) if you need to change the address or numbers.
"""

import asyncio
import logging

from livekit import api

from config import Settings
from sip_client import lk_client

logger = logging.getLogger("setup-outbound-trunk")


async def main():
    settings = Settings.load()

    async with lk_client(settings) as lk_api:
        outbound_trunk = api.SIPOutboundTrunkInfo(
            name="FreePBX-Outbound-Trunk",
            address=f"{settings.freepbx_host}:5060",
            transport=api.SIPTransport.SIP_TRANSPORT_UDP,
            numbers=[settings.sip_transfer_extension],
        )
        try:
            resp = await lk_api.sip.create_sip_outbound_trunk(
                api.CreateSIPOutboundTrunkRequest(trunk=outbound_trunk)
            )
        except Exception as e:
            logger.error(f"Failed to create outbound trunk: {e}")
            logger.error(
                "If this says a conflicting trunk exists, run reset_sip.py first."
            )
            raise
        logger.info(f"Outbound trunk created: {resp.sip_trunk_id}")


if __name__ == "__main__":
    asyncio.run(main())