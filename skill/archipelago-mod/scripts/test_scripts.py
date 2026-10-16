"""Tests for the skill's scripts. Standard library only: python scripts/test_scripts.py"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_apworld
import detect_engine
import new_project


def write(path: Path, content: bytes | str = b"") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path


class TemporaryDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)


class TestDetectEngine(TemporaryDirTestCase):
    def engines(self, target: Path | None = None) -> list[str]:
        return [finding.engine for finding in detect_engine.detect(target or self.root)]

    def test_unity_mono_with_version(self) -> None:
        write(self.root / "Game_Data/Managed/Assembly-CSharp.dll")
        write(self.root / "Game_Data/globalgamemanagers", b"\x00\x00header 2021.3.16f1\x00")
        findings = detect_engine.detect(self.root)
        self.assertEqual(["Unity Mono"], [finding.engine for finding in findings])
        self.assertIn("Unity 2021.3.16f1", findings[0].evidence)

    def test_unity_il2cpp_wins_over_stub_assembly(self) -> None:
        write(self.root / "GameAssembly.dll")
        write(self.root / "Game_Data/Managed/Assembly-CSharp.dll")
        self.assertEqual(["Unity IL2CPP"], self.engines())

    def test_unreal_with_io_store(self) -> None:
        write(self.root / "Game/Content/Paks/Game-Windows.pak")
        write(self.root / "Game/Content/Paks/Game-Windows.utoc")
        findings = detect_engine.detect(self.root)
        self.assertEqual("Unreal Engine", findings[0].engine)
        self.assertIn("IoStore", findings[0].evidence)

    def test_godot_pck_and_embedded_pack(self) -> None:
        write(self.root / "game.pck", b"GDPC\x02\x00\x00\x00")
        self.assertEqual(["Godot"], self.engines())
        (self.root / "game.pck").unlink()
        write(self.root / "game.exe", b"MZ" + b"\x00" * 64 + b"\x00" * 8 + b"GDPC")
        self.assertEqual(["Godot"], self.engines())

    def test_gamemaker_bytecode(self) -> None:
        write(self.root / "data.win", b"FORM\x10\x00\x00\x00GEN8")
        self.assertEqual(["GameMaker (VM bytecode)"], self.engines())

    def test_rom_file(self) -> None:
        self.assertEqual(["ROM or disc image"], self.engines(write(self.root / "game.gba", b"\x00")))

    def test_unknown_folder(self) -> None:
        write(self.root / "game.exe", b"MZ")
        self.assertEqual([], self.engines())


def scaffold(destination: Path, *extra: str) -> None:
    args = [str(destination), "--game", "Test Quest", "--author", "Tester", "--ap-version", "0.6.8", *extra]
    new_project.main(args)


class TestNewProject(TemporaryDirTestCase):
    def test_replaces_tokens_in_names_and_contents(self) -> None:
        scaffold(self.root / "repo")
        world = self.root / "repo/apworld/test_quest"
        manifest = json.loads((world / "archipelago.json").read_text(encoding="utf-8"))
        self.assertEqual({"game": "Test Quest", "minimum_ap_version": "0.6.8", "world_version": "0.1.0",
                          "authors": ["Tester"]}, manifest)
        self.assertTrue((world / "docs/en_Test Quest.md").is_file())
        self.assertIn("class TestQuestWorld(World)", (world / "world.py").read_text(encoding="utf-8"))
        self.assertEqual({}, new_project.leftover_tokens(self.root / "repo"))

    def test_bizhawk_client_is_registered_from_init(self) -> None:
        scaffold(self.root / "repo", "--client", "bizhawk")
        init = (self.root / "repo/apworld/test_quest/__init__.py").read_text(encoding="utf-8")
        self.assertIn("from .client import TestQuestClient as TestQuestClient", init)

    def test_dotnet_client_with_extra_tokens(self) -> None:
        scaffold(self.root / "repo", "--client", "dotnet", "--token", "UNITY_VERSION=2021.3.16",
                 "--token", "GAME_DATA_DIR=TestQuest_Data")
        self.assertTrue((self.root / "repo/client/TestQuestArchipelago/TestQuestArchipelago.csproj").is_file())
        self.assertEqual({}, new_project.leftover_tokens(self.root / "repo"))

    def test_refuses_non_empty_destination(self) -> None:
        write(self.root / "repo/file.txt", "x")
        with self.assertRaises(SystemExit):
            scaffold(self.root / "repo")

    def test_refuses_names_that_would_need_escaping(self) -> None:
        with self.assertRaises(SystemExit):
            new_project.main([str(self.root / "repo"), "--game", 'Bad "Name"', "--author", "T",
                              "--ap-version", "0.6.8"])

    def test_folds_accents_in_derived_names(self) -> None:
        self.assertEqual("pokemon_x", new_project.default_module("Pokémon X"))
        self.assertEqual("PokemonX", new_project.default_class_name("Pokémon X"))


class TestCheckApworld(TemporaryDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        scaffold(self.root / "repo")
        self.world = self.root / "repo/apworld/test_quest"

    def messages(self) -> list[str]:
        return [problem.message for problem in check_apworld.check_world(self.world)]

    def test_template_world_is_clean(self) -> None:
        self.assertEqual([], self.messages())

    def test_rejects_third_party_dependencies(self) -> None:
        write(self.world / "requirements.txt", "requests\n")
        write(self.world / "extra.py", "import requests\n")
        messages = self.messages()
        self.assertIn("third-party dependencies are not allowed", messages)
        self.assertIn("imports 'requests': only stdlib, Archipelago and its own requirements", messages)

    def test_rejects_network_file_and_random_in_generation(self) -> None:
        write(self.world / "extra.py", "import socket\nimport random\nopen('x')\n")
        messages = self.messages()
        self.assertTrue(any(message.startswith("imports 'socket' in generation code") for message in messages))
        self.assertTrue(any(message.startswith("imports 'random' in generation code") for message in messages))
        self.assertTrue(any(message.startswith("calls open() in generation code") for message in messages))

    def test_allows_network_in_client_modules(self) -> None:
        write(self.world / "client.py", "import asyncio\n")
        self.assertEqual([], self.messages())

    def test_rejects_build_keys_and_leftover_tokens(self) -> None:
        manifest_path = self.world / "archipelago.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["compatible_version"] = 7
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        write(self.world / "extra.py", "NAME = '__SYSTEM__'\n")
        messages = self.messages()
        self.assertIn("must not define 'compatible_version' (added by the build)", messages)
        self.assertIn("unreplaced template token __SYSTEM__", messages)

    def test_package_data_only_from_own_package(self) -> None:
        write(self.world / "extra.py", "import pkgutil\n"
                                       "A = pkgutil.get_data(__name__, 'data/a.json')\n"
                                       "B = pkgutil.get_data('Utils', 'LICENSE')\n"
                                       "C = pkgutil.get_data(__name__, '../x')\n")
        problems = [p for p in check_apworld.check_world(self.world) if "another package" in p.message]
        self.assertEqual([3, 4], [problem.line for problem in problems])

    def test_open_is_allowed_only_in_generate_output(self) -> None:
        write(self.world / "extra.py", "def generate_output(d):\n    open(d)\n\n\ndef create_items():\n    open('x')\n")
        lines = [p.line for p in check_apworld.check_world(self.world) if p.message.startswith("calls open()")]
        self.assertEqual([6], lines)

    def test_client_modules_must_not_run_code_at_import(self) -> None:
        write(self.world / "client.py", "import asyncio\nasyncio.get_event_loop()\n")
        self.assertIn("client module runs code at import time", self.messages())

    def test_allow_marker_silences_a_reviewed_exception(self) -> None:
        write(self.world / "extra.py", "import socket  # check_apworld: allow probe documented in game-map.md\n")
        self.assertEqual([], self.messages())

    def test_archipelago_requirements_are_allowed_where_archipelago_uses_them(self) -> None:
        write(self.world / "extra.py", "import settings\nfrom schema import Schema\n")
        write(self.world / "client.py", "import pymem\nimport websockets\n")
        self.assertEqual([], self.messages())

    def test_rejects_package_without_init(self) -> None:
        write(self.world / "logic/rules.py", "")
        self.assertIn("contains Python files but no __init__.py", self.messages())


if __name__ == "__main__":
    unittest.main()
