"""Static description of __GAME_NAME__: every item, location, region and entrance the world can create.

This is the only file that should change when the game map grows. Everything here is plain data checked into the
apworld: generation never reads the game, a ROM, a user file or the network to build it.
Each entry should be backed by a row in docs/dev/game-map.md (address, flag, or save field, plus how it was proven).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from BaseClasses import ItemClassification
from rule_builder.rules import Has, Rule, True_

# IDs are part of the network contract with the client: once released, an ID never changes meaning.
# Keep them in [1, 2**31 - 1]. Items and locations may share numbers, they live in separate namespaces.


@dataclass(frozen=True)
class ItemData:
    id: int
    classification: ItemClassification
    pool_count: int = 1
    """Copies placed in the item pool. 0 means the item exists (e.g. as filler) but is not pre-placed."""


@dataclass(frozen=True)
class LocationData:
    id: int
    region: str
    rule: Rule = field(default_factory=True_)


@dataclass(frozen=True)
class EntranceData:
    source: str
    target: str
    rule: Rule = field(default_factory=True_)


ORIGIN_REGION = "Menu"

# Placeholder content, shaped like a real game, so the template generates and its tests pass from day one.
# Replace it with the game's real map; keep the shapes.
ITEMS: dict[str, ItemData] = {
    "Progressive Sword": ItemData(1, ItemClassification.progression, pool_count=2),
    "Key": ItemData(2, ItemClassification.progression),
    "Health Upgrade": ItemData(3, ItemClassification.useful),
    "Coin": ItemData(4, ItemClassification.filler, pool_count=0),
}

FILLER_ITEM = "Coin"

REGIONS: tuple[str, ...] = (ORIGIN_REGION, "Village", "Dungeon", "Boss Room")

ENTRANCES: tuple[EntranceData, ...] = (
    EntranceData(ORIGIN_REGION, "Village"),
    EntranceData("Village", "Dungeon", Has("Key")),
    EntranceData("Dungeon", "Boss Room", Has("Progressive Sword", count=2)),
)

LOCATIONS: dict[str, LocationData] = {
    "Village Chest": LocationData(1, "Village"),
    "Village Quest Reward": LocationData(2, "Village"),
    "Dungeon Chest": LocationData(3, "Dungeon"),
    "Dungeon Hidden Chest": LocationData(4, "Dungeon", Has("Progressive Sword")),
    "Boss Drop": LocationData(5, "Boss Room"),
}

GOAL_REGION = "Boss Room"
"""Region holding the victory event; the client reports the goal with StatusUpdate when the game is beaten."""
