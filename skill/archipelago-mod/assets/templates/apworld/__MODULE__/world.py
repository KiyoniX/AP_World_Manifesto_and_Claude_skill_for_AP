from collections.abc import Mapping
from typing import Any, ClassVar

from BaseClasses import Item, Location, Region
from rule_builder.rules import Has
from worlds.AutoWorld import World

from . import data
from .options import __CLASS__Options
from .web_world import __CLASS__WebWorld

VICTORY_EVENT = "Victory"


class __CLASS__Item(Item):
    game = "__GAME_NAME__"


class __CLASS__Location(Location):
    game = "__GAME_NAME__"


class __CLASS__World(World):
    """__GAME_NAME__ randomizer for Archipelago."""

    game = "__GAME_NAME__"
    web = __CLASS__WebWorld()
    options_dataclass = __CLASS__Options
    options: __CLASS__Options
    origin_region_name = data.ORIGIN_REGION

    item_name_to_id: ClassVar[dict[str, int]] = {name: item.id for name, item in data.ITEMS.items()}
    location_name_to_id: ClassVar[dict[str, int]] = {name: loc.id for name, loc in data.LOCATIONS.items()}

    def create_regions(self) -> None:
        regions = {name: Region(name, self.player, self.multiworld) for name in data.REGIONS}
        self.multiworld.regions += regions.values()

        for entrance in data.ENTRANCES:
            self.create_entrance(regions[entrance.source], regions[entrance.target], entrance.rule)

        for name, location in data.LOCATIONS.items():
            region = regions[location.region]
            region.locations.append(__CLASS__Location(self.player, name, location.id, region))

        regions[data.GOAL_REGION].add_event(
            "Goal Reached", VICTORY_EVENT, location_type=__CLASS__Location, item_type=__CLASS__Item
        )

    def create_items(self) -> None:
        pool: list[Item] = [self.create_item(name) for name, item in data.ITEMS.items() for _ in range(item.pool_count)]
        free_slots = len(self.multiworld.get_unfilled_locations(self.player)) - len(pool)
        pool += [self.create_filler() for _ in range(free_slots)]
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        for name, location in data.LOCATIONS.items():
            self.set_rule(self.get_location(name), location.rule)
        self.set_completion_rule(Has(VICTORY_EVENT))

    def create_item(self, name: str) -> __CLASS__Item:
        item = data.ITEMS[name]
        return __CLASS__Item(name, item.classification, item.id, self.player)

    def get_filler_item_name(self) -> str:
        return data.FILLER_ITEM

    def fill_slot_data(self) -> Mapping[str, Any]:
        # Everything the client needs to adapt the game to this seed. Keep it small and JSON-serializable.
        return self.options.as_dict("death_link")
