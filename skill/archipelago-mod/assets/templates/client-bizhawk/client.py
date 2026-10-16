"""BizHawk client for __GAME_NAME__: reads progress flags from emulated memory and writes received items into it.

Lives inside the apworld and only imports Archipelago core. It must be imported from __init__.py so it registers.
Every address below is game-specific and must come from docs/dev/game-map.md with its proof.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import worlds._bizhawk as bizhawk
from NetUtils import ClientStatus
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

# BizHawk system id (emu.getsystemid()), e.g. "GBA", "NES", ("GB", "SGB"), "N64".
SYSTEM = "__SYSTEM__"

# Written into the ROM by the world's patch. The magic identifies a patched ROM; seed and slot bind it to one
# multiworld, so CommonClient refuses a server running another seed and logs in to the right slot.
ROM_DOMAIN = "ROM"
ROM_MAGIC_ADDRESS = 0x0
ROM_MAGIC = b"__ROM_NAME__"
ROM_SEED_NAME_ADDRESS = 0x0
ROM_SLOT_NAME_ADDRESS = 0x0
ROM_NAME_FIELD_SIZE = 32

# The game's save data as it lives in RAM: the game copies it to the save file when the player saves. The applied
# item counter belongs there (in bytes the patch reserves) so it is saved together with the items it counts: a reset
# without saving rolls both back, and the items are granted again.
RAM_DOMAIN = "System Bus"
FLAGS_ADDRESS = 0x0
FLAGS_SIZE = 0x1
RECEIVED_COUNT_ADDRESS = 0x0
# A byte that holds IN_GAMEPLAY_VALUE only during normal gameplay: nothing is read or written on the title screen,
# during loads or in cutscenes.
GAME_STATE_ADDRESS = 0x0
IN_GAMEPLAY_VALUE = 0x0
PLAYER_HEALTH_ADDRESS = 0x0
PLAYER_HEALTH_SIZE = 1

# location_id -> (byte offset into the flags block, bit mask). IDs match data.LOCATIONS.
LOCATION_FLAGS: dict[int, tuple[int, int]] = {}
GOAL_FLAG: tuple[int, int] = (0, 0)


def item_writes(item_id: int) -> list[tuple[int, list[int], str]]:
    """Memory writes that give one received item, e.g. an inventory slot or a mailbox the patch consumes."""
    raise NotImplementedError(f"No write known for item {item_id}")


def kill_player_writes() -> list[tuple[int, list[int], str]]:
    """Memory writes that kill the player, applied for a received DeathLink."""
    return [(PLAYER_HEALTH_ADDRESS, [0] * PLAYER_HEALTH_SIZE, RAM_DOMAIN)]


def is_flag_set(flags: bytes, flag: tuple[int, int]) -> bool:
    offset, mask = flag
    return bool(flags[offset] & mask)


def decode_name(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("utf-8")


class __CLASS__Client(BizHawkClient):
    game = "__GAME_NAME__"
    system = SYSTEM

    def __init__(self) -> None:
        super().__init__()
        self.slot_name = ""
        self.death_link_enabled = False
        self.death_pending = False
        self.player_dead = False
        # Set when we kill the player for a received DeathLink: that one death must not be sent back.
        self.own_kill = False

    async def validate_rom(self, ctx: BizHawkClientContext) -> bool:
        try:
            magic, seed_name, slot_name = await bizhawk.read(ctx.bizhawk_ctx, [
                (ROM_MAGIC_ADDRESS, len(ROM_MAGIC), ROM_DOMAIN),
                (ROM_SEED_NAME_ADDRESS, ROM_NAME_FIELD_SIZE, ROM_DOMAIN),
                (ROM_SLOT_NAME_ADDRESS, ROM_NAME_FIELD_SIZE, ROM_DOMAIN),
            ])
        except bizhawk.RequestFailedError:
            return False
        if magic != ROM_MAGIC:
            return False

        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        ctx.seed_name = decode_name(seed_name)
        self.slot_name = decode_name(slot_name)
        return True

    async def set_auth(self, ctx: BizHawkClientContext) -> None:
        ctx.auth = self.slot_name

    def on_package(self, ctx: BizHawkClientContext, cmd: str, args: dict[str, Any]) -> None:
        if cmd == "Connected":
            self.death_link_enabled = bool(args.get("slot_data", {}).get("death_link"))
        elif cmd == "Bounced" and "DeathLink" in args.get("tags", []) and ctx.slot is not None:
            if args["data"].get("source") != ctx.player_names.get(ctx.slot):
                self.death_pending = True

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        if ctx.server is None or ctx.slot is None:
            return

        try:
            # One request bundle, so every value comes from the same frame.
            game_state, flags, count_bytes, health = await bizhawk.read(ctx.bizhawk_ctx, [
                (GAME_STATE_ADDRESS, 1, RAM_DOMAIN),
                (FLAGS_ADDRESS, FLAGS_SIZE, RAM_DOMAIN),
                (RECEIVED_COUNT_ADDRESS, 2, RAM_DOMAIN),
                (PLAYER_HEALTH_ADDRESS, PLAYER_HEALTH_SIZE, RAM_DOMAIN),
            ])
            if game_state[0] != IN_GAMEPLAY_VALUE:
                self.death_pending = False  # A death received outside gameplay must not kill on the next load.
                return

            checked = {location_id for location_id, flag in LOCATION_FLAGS.items() if is_flag_set(flags, flag)}
            await ctx.check_locations(checked)

            if not ctx.finished_game and is_flag_set(flags, GOAL_FLAG):
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True

            await self._update_death_link(ctx, game_state, health)
            await self._grant_next_item(ctx, game_state, count_bytes)
        except bizhawk.RequestFailedError:
            pass  # The connector dropped; BizHawkClient reconnects and calls the watcher again.

    async def _update_death_link(self, ctx: BizHawkClientContext, game_state: bytes, health: bytes) -> None:
        if not self.death_link_enabled or ctx.slot is None:
            return
        if "DeathLink" not in ctx.tags:
            await ctx.update_death_link(True)

        is_dead = not any(health)
        if is_dead and not self.player_dead:
            if self.own_kill:
                self.own_kill = False
            else:
                await ctx.send_death(f"{ctx.player_names[ctx.slot]} died")
        self.player_dead = is_dead

        if self.death_pending and not is_dead:
            killed = await bizhawk.guarded_write(
                ctx.bizhawk_ctx, kill_player_writes(), [(GAME_STATE_ADDRESS, game_state, RAM_DOMAIN)]
            )
            self.death_pending = not killed
            self.own_kill = killed

    async def _grant_next_item(self, ctx: BizHawkClientContext, game_state: bytes, count_bytes: bytes) -> None:
        applied = int.from_bytes(count_bytes, "little")
        if applied >= len(ctx.items_received):
            return
        item = ctx.items_received[applied]
        new_count = list((applied + 1).to_bytes(2, "little"))
        # The guards make the write a no-op if the game left gameplay or touched the counter since the read, so an
        # item is never granted twice or written into a loading screen; the next pass simply retries.
        await bizhawk.guarded_write(
            ctx.bizhawk_ctx,
            [*item_writes(item.item), (RECEIVED_COUNT_ADDRESS, new_count, RAM_DOMAIN)],
            [(RECEIVED_COUNT_ADDRESS, count_bytes, RAM_DOMAIN), (GAME_STATE_ADDRESS, game_state, RAM_DOMAIN)],
        )
