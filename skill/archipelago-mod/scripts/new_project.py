"""Create a new integration repository from the skill templates.

Usage:
  python new_project.py <destination> --game "My Game" --author "Name" --ap-version 0.6.8
                        [--module my_game] [--class-name MyGame] [--client none|dotnet|bizhawk]
                        [--token NAME=VALUE ...]

The destination must be empty or not exist. Tokens such as __MODULE__ are replaced in file names and contents;
any token left unreplaced (e.g. __UNITY_VERSION__ when not passed with --token) is listed at the end, to be filled
from docs/dev/game-map.md. Nothing is fetched from the network.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from check_apworld import TEMPLATE_TOKEN, VERSION

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "assets" / "templates"
TEXT_SUFFIXES = {".py", ".json", ".md", ".yml", ".cs", ".csproj", ".example", ".gitignore", ""}
MODULE_NAME = re.compile(r"[a-z][a-z0-9_]*")
CLASS_NAME = re.compile(r"[A-Z][A-Za-z0-9]*")
# The game name is pasted into JSON and Python string literals: characters that would need escaping are refused.
UNSAFE_GAME_NAME_CHARACTERS = {'"', "\\"} | {chr(code) for code in range(32)}


def ascii_words(game: str) -> list[str]:
    # "Pokémon X" -> ["Pokemon", "X"]: accents are folded instead of splitting words.
    folded = unicodedata.normalize("NFKD", game).encode("ascii", "ignore").decode("ascii")
    return re.findall(r"[A-Za-z0-9]+", folded)


def default_module(game: str) -> str:
    return "_".join(ascii_words(game)).lower()


def default_class_name(game: str) -> str:
    return "".join(word[0].upper() + word[1:] for word in ascii_words(game))


def substitute(text: str, tokens: dict[str, str]) -> str:
    return TEMPLATE_TOKEN.sub(lambda match: tokens.get(match.group(), match.group()), text)


def copy_tree(source: Path, destination: Path, tokens: dict[str, str]) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        target = destination / substitute(str(path.relative_to(source)), tokens)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in TEXT_SUFFIXES:
            target.write_text(substitute(path.read_text(encoding="utf-8"), tokens), encoding="utf-8")
        else:
            shutil.copyfile(path, target)


def leftover_tokens(root: Path) -> dict[str, set[Path]]:
    found: dict[str, set[Path]] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and ".git" not in path.parts:
            for token in TEMPLATE_TOKEN.findall(path.read_text(encoding="utf-8")):
                found.setdefault(token, set()).add(path.relative_to(root))
    return found


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--game", required=True, help="exact game name, as the world's `game` field")
    parser.add_argument("--author", required=True)
    parser.add_argument("--ap-version", required=True, help="Archipelago release the world targets, e.g. 0.6.8")
    parser.add_argument("--module", help="Python package name (default: derived from the game name)")
    parser.add_argument("--class-name", help="Class name prefix (default: derived from the game name)")
    parser.add_argument("--client", choices=("none", "dotnet", "bizhawk"), default="none")
    parser.add_argument("--token", action="append", default=[], metavar="NAME=VALUE",
                        help="extra template value, e.g. --token UNITY_VERSION=2021.3.16")
    args = parser.parse_args(argv)
    if UNSAFE_GAME_NAME_CHARACTERS & set(args.game):
        parser.error("--game must not contain quotes, backslashes or control characters")
    args.module = args.module or default_module(args.game)
    args.class_name = args.class_name or default_class_name(args.game)
    if not MODULE_NAME.fullmatch(args.module):
        parser.error(f"--module {args.module!r} must be lowercase snake_case")
    if not CLASS_NAME.fullmatch(args.class_name):
        parser.error(f"--class-name {args.class_name!r} must be PascalCase")
    if not VERSION.fullmatch(args.ap_version):
        parser.error("--ap-version must look like 0.6.8")
    if args.destination.exists() and any(p.name != ".git" for p in args.destination.iterdir()):
        parser.error(f"{args.destination} is not empty")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    tokens = {
        "__GAME_NAME__": args.game,
        "__MODULE__": args.module,
        "__CLASS__": args.class_name,
        "__AUTHOR__": args.author,
        "__AP_VERSION__": args.ap_version,
    }
    for pair in args.token:
        name, _, value = pair.partition("=")
        tokens[f"__{name.strip('_').upper()}__"] = value

    destination: Path = args.destination
    world = destination / "apworld" / args.module
    copy_tree(TEMPLATES / "repo", destination, tokens)
    copy_tree(TEMPLATES / "apworld" / "__MODULE__", world, tokens)
    (destination / "tools").mkdir(exist_ok=True)
    shutil.copyfile(SKILL_DIR / "scripts" / "check_apworld.py", destination / "tools" / "check_apworld.py")

    if args.client == "dotnet":
        copy_tree(TEMPLATES / "client-dotnet", destination / "client", tokens)
    elif args.client == "bizhawk":
        copy_tree(TEMPLATES / "client-bizhawk", world, tokens)
        init = world / "__init__.py"
        # Importing the client registers it with BizHawkClient; the import itself only pulls Archipelago core.
        client_import = f"from .client import {args.class_name}Client as {args.class_name}Client\n"
        init.write_text(client_import + init.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Created {destination.resolve()}")
    for token, paths in sorted(leftover_tokens(destination).items()):
        print(f"To fill: {token} in {', '.join(sorted(str(p) for p in paths))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
