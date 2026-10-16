from test.bases import WorldTestBase

from ..world import __CLASS__World


class __CLASS__TestBase(WorldTestBase):
    game = "__GAME_NAME__"
    world: __CLASS__World
