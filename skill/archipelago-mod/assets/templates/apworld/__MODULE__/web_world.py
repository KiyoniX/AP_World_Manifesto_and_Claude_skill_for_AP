from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld


class __CLASS__WebWorld(WebWorld):
    game = "__GAME_NAME__"
    tutorials = [  # noqa: RUF012 - WebWorld declares tutorials as a plain class attribute, as APQuest does
        Tutorial(
            "Multiworld Setup Guide",
            "How to set up __GAME_NAME__ for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["__AUTHOR__"],
        )
    ]
