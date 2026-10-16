---
name: archipelago-mod
description: Guides a user, step by step, from "I own this game" to a released Archipelago (multiworld randomizer) integration - the APWorld that generates seeds plus the in-game client or mod - for any game on any engine or emulator. It asks which game, checks whether an integration already exists, detects the engine from the install folder, picks the right hooking route (BepInEx, UE4SS, Godot, BizHawk, memory client, Manual...), helps find the game loop, checks, items and goal, scaffolds a tested repository, and releases it. Use this whenever someone wants to make, start, continue, fix or release an Archipelago / AP randomizer, apworld, AP client or "multiworld mod" for a game, even if they only say "add my game to Archipelago", "randomizer for X" or "is X moddable for AP".
---

# Archipelago integration, guided

You are guiding someone who owns a game and wants it playable in an [Archipelago](https://archipelago.gg) multiworld.
An integration always has two halves that talk through the Archipelago server:

- the **APWorld** (Python, runs at generation): items, locations, regions, logic, options;
- the **client** (runs while playing): detects checks, grants received items, reports the goal, reconnects.

Speak with the user in their language. Everything that ends up in the repository (identifiers, comments, docs, commit
messages) is in English, because the Archipelago community works in English.

Most of the work is generic and this skill makes it fast. The hard part is game-specific: finding where the game
stores progress and how to give it an item. Be honest about that from the start, and keep the user involved where
their knowledge of the game matters (what counts as a check, what blocks what, what the goal is).

## Absolute rules

These are not trade-offs. If a request conflicts with one, say so and propose the compliant way.

### 1. Code quality, readability and reuse

Read `references/quality.md` before writing code, and hold every change to it. In short: the simplest design that
works, no duplicated logic, strict typing, small single-purpose functions, names that make comments about *what*
unnecessary, comments only for *why*, tests for everything that can break, and a strict separation between the
reusable layer (protocol, connection, item pump, data-driven world) and the game-specific layer (adapter, data, game
map). No code is "done" before its tests pass and it has survived an adversarial review (step 8).

### 2. Generation is self-contained

During generation the APWorld:

- reads no file outside its own package: no game install, no ROM, no save, no `host.yaml`, no user folder;
- depends on nothing but the Python standard library and Archipelago core: no `requirements.txt`, no vendored or
  downloaded code;
- makes no network call.

All game knowledge is static data shipped inside the apworld (`data.py`, or files read with `pkgutil.get_data`).
A ROM-based game produces a patch in the output directory; the client applies it to the player's own ROM.
`scripts/check_apworld.py` enforces this statically and `test/test_generation_is_self_contained.py` at runtime.

### 3. Repository and release

- Never fork ArchipelagoMW/Archipelago to develop a world. Clone the official repository next to the project and
  link the world into it (`references/repo-release.md`). A fork is a last resort, only for a change to Archipelago
  core itself, and is then proposed upstream.
- One project, one repository: APWorld, client, docs and tests live together.
- Nothing built is committed. A release is a git tag `vX.Y.Z` equal to `world_version` in `archipelago.json`;
  its assets are the `.apworld` file itself and the client in its native form (`.dll`, `.lua`...). Never wrap release
  assets in a `.zip`.

### 4. Legitimate use only

The user plays their own copy, offline or on their own multiworld server. Never help bypass anti-cheat, DRM or
online protections, never touch a game whose online mode could be affected, and never commit or publish anything
taken from the game (assets, binaries, decompiled code, dumps, ROMs, saves). Mention that some store terms (e.g.
Steam's) restrict reverse engineering, without giving legal advice.

## Workflow

Keep `docs/dev/progress.md` in the project repository up to date at the end of every step: it is how a later
session resumes, and its steps carry the same numbers as below. Steps 0 to 2 happen before the repository exists:
keep their results and write them into `progress.md` right after scaffolding. If the user already has a project,
read it first and continue from the first unchecked step.
Each step ends with a short summary to the user and, where marked, a question only they can answer.

### Step 0. Interview

Ask, in one message: the game's exact name; platform and store (Steam, GOG, emulator and ROM, console); where it is
installed; whether it has online features or anti-cheat; the user's comfort with code (none, some, developer); and,
if they know already, what they imagine as checks, as items and as the goal. Adapt how much you explain to their
answer, never what quality you deliver.

### Step 1. Prior art

Before anything else, look for an existing integration, because joining or continuing one beats starting over:

- the official list: https://archipelago.gg/games, and the guide for unofficial games:
  https://archipelago.gg/tutorial/Archipelago/other_en;
- GitHub search for `"<game>" archipelago` and `<game> apworld`;
- the community wiki https://archipelago.miraheze.org/;
- the `#apworld-index` channels of the Archipelago Discord (https://discord.gg/8Z65BR2) and of Archipelago After Dark
  (https://discord.gg/fqvNCCRsu4). You cannot read Discord: ask the user to search there and report back.

Record every place searched and the result in `progress.md`. If something exists, show it and **ask** whether to use
it, contribute to it, or still build a new one.

### Step 2. Engine and route

Run `python scripts/detect_engine.py "<install folder or ROM>"`. It prints engine guesses with their evidence, and
SHA-256 hashes of the executables: record the hash, because addresses and hooks are only valid for that build.
Then pick the route and read **only** the matching reference:

| Detected | Route | Reference |
| --- | --- | --- |
| Unity Mono / IL2CPP | BepInEx plugin + Archipelago.MultiClient.Net, `client-dotnet` template | `references/engine-unity.md` |
| Unreal Engine 4/5 | UE4SS Lua mod + lua-apclientpp, or C++ mod + apclientpp | `references/engine-unreal.md` |
| Godot | Autoload script injected via PCK patch or Godot Mod Loader | `references/engine-godot.md` |
| ROM / disc image | BizHawkClient, SNI, Dolphin Memory Engine, PCSX2 PINE, `client-bizhawk` template | `references/engine-emulators.md` |
| GameMaker, RPG Maker, XNA/FNA/MonoGame, Java, Ren'Py, Source, Lua | per-engine notes | `references/engine-others.md` |
| Nothing detected (native or custom engine) | External memory client, or injected DLL | `references/engine-native.md` |
| The game cannot be modded at all | **Manual** for Archipelago (checks ticked by hand) | below |

If the game cannot be modded (closed console, no tooling, protected), propose
[Manual for Archipelago](https://github.com/ManualForArchipelago/Manual): an APWorld described in JSON where the
player ticks checks in a client by hand. It still needs a proper game map, and works poorly for very linear games.

Explain the chosen route and its risks to the user, and **ask** them to confirm before scaffolding.

### Step 3. Scaffold the repository

```sh
python scripts/new_project.py <repo folder> --game "<exact name>" --author "<name>" \
    --ap-version <latest Archipelago release> --client dotnet|bizhawk|none [--token NAME=VALUE ...]
```

Look up the latest Archipelago release (https://github.com/ArchipelagoMW/Archipelago/releases/latest) rather than
assuming it. The script prints every placeholder it could not fill: fill them as the game map is proven, never with
guesses. Then `git init`, and set up the local development loop from `references/repo-release.md`.

### Step 4. Proof of concept (feasibility first)

Before mapping the whole game, prove the three risky links, as Archipelago's own FAQ recommends:

1. a per-frame hook (or polling loop) runs inside or alongside the game;
2. one location of each major kind is detected, and one item is granted, in the real game;
3. the client connects to a local server, sends that check and receives that item.

`references/reverse.md` explains how to find hooks, flags and inventory for each kind of game. The template world
generates out of the box, so an end-to-end round trip is possible from day one. If a link cannot be made to work,
stop and discuss alternatives (another route, Manual) before investing more.

### Step 5. Game map

With the user, list every location, item, logic gate and the goal. Each one goes into `docs/dev/game-map.md` with its
proof (address or hook, how it was found, value before and after), then into `apworld/<module>/data.py`.
Ask the user to settle the design questions: which checks to include, which items are progression, what the goal
is, which options are worth offering. Read `references/apworld.md` for IDs, classifications, rules and options.

### Step 6. APWorld

Fill `data.py`, extend `options.py` only for options the user wants, keep `world.py` generic. Add one logic test per
real gate. Then run, and fix until clean:

```sh
python tools/check_apworld.py apworld/<module>
AP_TEST_WORLDS=<module> python -m pytest      # from the Archipelago clone
```

### Step 7. Client

Implement the game-specific side behind the template's adapter, and nothing game-specific anywhere else. The client
must meet every requirement in `references/client-protocol.md`: reconnection, offline resync, a save bound to its
seed and slot, an applied-item counter saved together with the items, no double grants, goal report, DeathLink only
when the player enabled it. Unit-test the logic that does not need
the game.

### Step 8. End-to-end test and adversarial review

Generate a seed locally, host it, and play from a fresh save to the goal, including a disconnect, a game restart and
reloading an older save. Then have the work reviewed adversarially by a fresh subagent that did not write it, with the
checklist in `references/quality.md`. Fix every confirmed finding; report anything left open to the user.

### Step 9. Release

Follow `references/repo-release.md`: bump `world_version`, tag `vX.Y.Z`, push the tag (CI tests, builds and publishes
the `.apworld`), attach the client in its native form. Pushing and publishing are outward-facing: **ask** before
doing either.

## Bundled resources

| Path | Use |
| --- | --- |
| `scripts/detect_engine.py` | Engine detection and executable hashes (step 2) |
| `scripts/new_project.py` | Repository scaffold from the templates (step 3) |
| `scripts/check_apworld.py` | Static rule checks; also copied into each project's `tools/` for CI |
| `scripts/test_scripts.py` | Tests of the three scripts above |
| `assets/templates/repo/` | README, `.gitignore`, CI and release workflows, `docs/dev/` progress and game map |
| `assets/templates/apworld/` | Data-driven world, logic tests, and an audit-hook sandbox test of the whole generation |
| `assets/templates/client-dotnet/` | `ArchipelagoBridge` (game-agnostic C# client: reconnection, save binding, item pump, DeathLink; unit tested) and a BepInEx 5 plugin |
| `assets/templates/client-bizhawk/` | BizHawkClient: flag table, counter saved with the items, gameplay-guarded writes, ROM-bound seed and slot, DeathLink |
| `references/*.md` | Read on demand, as each step says |
