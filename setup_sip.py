"""
Creates the inbound SIP trunk + dispatch rule that let FreePBX hand calls
off to LiveKit and dispatch them to the agent.

Safe to run once. Re-running while a trunk/rule already exists with the
same number will raise a clear error from the LiveKit API rather than
silently duplicating config — run reset_sip.py first if you need a clean
slate.
"""

import asyncio
import logging

from livekit import api

from config import Settings
from sip_client import lk_client

logger = logging.getLogger("setup-sip")


async def main():
    settings = Settings.load()

    async with lk_client(settings) as lk_api:
        trunk = api.SIPInboundTrunkInfo(
            name="FreePBX-Inbound-Trunk",
            allowed_addresses=[f"{settings.freepbx_host}/32"],
            numbers=[settings.sip_did_number],
        )
        try:
            trunk_resp = await lk_api.sip.create_sip_inbound_trunk(
                api.CreateSIPInboundTrunkRequest(trunk=trunk)
            )
        except Exception as e:
            logger.error(f"Failed to create inbound trunk: {e}")
            logger.error(
                "If this says a conflicting trunk exists, run reset_sip.py first."
            )
            raise
        logger.info(f"Inbound trunk created: {trunk_resp.sip_trunk_id}")

        rule = api.SIPDispatchRuleInfo(
            name="inbound-dispatch",
            rule=api.SIPDispatchRule(
                dispatch_rule_individual=api.SIPDispatchRuleIndividual(room_prefix="call-")
            ),
            room_config=api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name=settings.agent_name)]
            ),
        )
        try:
            rule_resp = await lk_api.sip.create_sip_dispatch_rule(
                api.CreateSIPDispatchRuleRequest(dispatch_rule=rule)
            )
        except Exception as e:
            logger.error(f"Failed to create dispatch rule: {e}")
            raise
        logger.info(f"Dispatch rule created: {rule_resp.sip_dispatch_rule_id}")


if __name__ == "__main__":
    asyncio.run(main())