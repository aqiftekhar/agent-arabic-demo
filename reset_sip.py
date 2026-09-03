"""
Deletes ALL SIP dispatch rules, inbound trunks, and outbound trunks from
the LiveKit server. This is a destructive, scoped reset — it does NOT
touch the Redis volume, room state, or anything else. Use this instead of
`docker compose down -v`, which would wipe far more than you want.

Requires interactive confirmation unless run with --yes (for scripted use,
e.g. a CI pipeline or a Makefile target — use with care).
"""

import argparse
import asyncio
import logging

from livekit import api

from config import Settings
from sip_client import lk_client

logger = logging.getLogger("reset-sip")


async def _delete_all_dispatch_rules(lk_api) -> int:
    rules = await lk_api.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
    count = 0
    for rule in rules.items:
        try:
            await lk_api.sip.delete_sip_dispatch_rule(
                api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=rule.sip_dispatch_rule_id)
            )
            logger.info(f"Deleted dispatch rule: {rule.sip_dispatch_rule_id}")
            count += 1
        except Exception as e:
            logger.warning(f"Failed to delete dispatch rule {rule.sip_dispatch_rule_id}: {e}")
    return count


async def _delete_all_trunks(lk_api, list_fn, list_req_cls, kind: str) -> int:
    resp = await list_fn(list_req_cls())
    count = 0
    for trunk in resp.items:
        try:
            await lk_api.sip.delete_sip_trunk(
                api.DeleteSIPTrunkRequest(sip_trunk_id=trunk.sip_trunk_id)
            )
            logger.info(f"Deleted {kind} trunk: {trunk.sip_trunk_id}")
            count += 1
        except Exception as e:
            logger.warning(f"Failed to delete {kind} trunk {trunk.sip_trunk_id}: {e}")
    return count


async def main(skip_confirm: bool):
    settings = Settings.load()

    if not skip_confirm:
        answer = input(
            "This will delete ALL SIP dispatch rules and trunks (inbound + "
            "outbound) on this LiveKit server. Continue? (yes/no): "
        )
        if answer.strip().lower() != "yes":
            logger.info("Aborted — no changes made.")
            return

    async with lk_client(settings) as lk_api:
        rules_deleted = await _delete_all_dispatch_rules(lk_api)
        inbound_deleted = await _delete_all_trunks(
            lk_api, lk_api.sip.list_sip_inbound_trunk, api.ListSIPInboundTrunkRequest, "inbound"
        )
        outbound_deleted = await _delete_all_trunks(
            lk_api, lk_api.sip.list_sip_outbound_trunk, api.ListSIPOutboundTrunkRequest, "outbound"
        )

    logger.info(
        f"Reset complete: {rules_deleted} dispatch rule(s), "
        f"{inbound_deleted} inbound trunk(s), {outbound_deleted} outbound trunk(s) removed."
    )
    logger.info("Run setup_sip.py and setup_outbound_trunk.py to recreate a clean config.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes", action="store_true", help="Skip the interactive confirmation prompt."
    )
    args = parser.parse_args()
    asyncio.run(main(skip_confirm=args.yes))