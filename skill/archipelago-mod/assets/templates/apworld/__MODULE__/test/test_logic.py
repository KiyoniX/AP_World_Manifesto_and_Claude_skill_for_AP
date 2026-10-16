from .bases import __CLASS__TestBase


class TestLogic(__CLASS__TestBase):
    # One assertion per real gate of the game map. Replace these with the game's own gates as data.py grows.
    def test_dungeon_needs_key(self) -> None:
        self.assertAccessDependency(["Dungeon Chest"], [["Key"]], only_check_listed=True)

    def test_boss_needs_both_swords(self) -> None:
        first_sword, second_sword = self.get_items_by_name("Progressive Sword")
        self.collect_by_name("Key")
        self.collect(first_sword)
        self.assertFalse(self.can_reach_location("Boss Drop"))
        self.collect(second_sword)
        self.assertTrue(self.can_reach_location("Boss Drop"))
