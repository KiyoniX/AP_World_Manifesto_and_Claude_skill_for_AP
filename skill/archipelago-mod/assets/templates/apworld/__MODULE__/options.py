from dataclasses import dataclass

from Options import DeathLink, PerGameCommonOptions


@dataclass
class __CLASS__Options(PerGameCommonOptions):
    death_link: DeathLink
