"""
Prints the current inbound trunks, dispatch rules, and outbound trunks
configured on the LiveKit server. Read-only — safe to run anytime.
"""

import asyncio
import logging

from livekit import api

from config import Settings
from sip_client import lk_client

logger = logging.getLogger("verify-sip")


async def main():
    settings = Settings.load()

    async with lk_client(settings) as lk_api:
        inbound = await lk_api.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
        rules = await lk_api.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
        outbound = await lk_api.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())

    print("\n--- Inbound Trunks ---")
    if not inbound.items:
        print("  (none)")
    for t in inbound.items:
        print(f"  {t.sip_trunk_id}  name={t.name}  numbers={list(t.numbers)}  "
              f"allowed_addresses={list(t.allowed_addresses)}")

    print("\n--- Dispatch Rules ---")
    if not rules.items:
        print("  (none)")
    for r in rules.items:
        agent_names = [a.agent_name for a in r.room_config.agents]
        print(f"  {r.sip_dispatch_rule_id}  name={r.name}  agents={agent_names}")

    print("\n--- Outbound Trunks ---")
    if not outbound.items:
        print("  (none)")
    for t in outbound.items:
        print(f"  {t.sip_trunk_id}  name={t.name}  address={t.address}  "
              f"numbers={list(t.numbers)}")
    print()


if __name__ == "__main__":
    asyncio.run(main())