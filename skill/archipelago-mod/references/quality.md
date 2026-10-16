# Code quality, readability and reuse

The bar: a stranger who knows the language but not the game can read any file, understand why it exists, and change
it without breaking something elsewhere. Every rule below serves that.

## Contents

- Design
- Naming and comments
- Python (APWorld, Python clients)
- C# (.NET clients)
- Lua, C++, GDScript, JavaScript
- Tests
- Adversarial review

## Design

- **Simplest thing that works.** No abstraction with a single user, no option nobody asked for, no framework for a
  problem that has one case. Three similar lines beat a premature helper; a third copy of a block is a helper.
- **Search before writing.** Archipelago core, the client library and the templates already solve connection,
  reconnection, data package caching, location sending, item indexing and DeathLink. Reuse them; never reimplement the
  protocol by hand when a maintained library exists for the language.
- **Two layers, never mixed.**
  - *Reusable layer*: protocol and connection handling, item pump, location reporting, data-driven world code
    (`world.py`, `ArchipelagoBridge`, the BizHawk client skeleton). It never mentions the game.
  - *Game layer*: `data.py`, the game adapter, the address table, Harmony patches or hooks. It never talks to the
    network directly.
  A new game should only ever need a new game layer.
- **Data over code.** Items, locations, regions, entrances and rules are tables (`data.py`); behaviour is generic code
  iterating over them. A new location is one line of data, not a new function.
- **Fail loudly.** Unknown item IDs, unimplemented adapter members and impossible states raise or log clearly. Never
  swallow an exception without saying why in a comment; never return a fake default that hides a missing piece.
- **Threads.** Network callbacks never touch game state. They enqueue under a lock; the game thread drains.
- **Determinism.** Generation uses only `self.random` (or `world.random`). Iteration order over dicts is insertion
  order; never iterate over a `set` where order affects output.
- **IDs are a contract.** Once released, an item or location ID never changes meaning. Add, never renumber.

## Naming and comments

- English everywhere in the repository.
- Names say what a thing is, in the domain's words: `applied_item_count`, `LOCATION_FLAGS`, `TryGrantItem`. No
  abbreviations except universal ones (`id`, `ui`). No `data2`, `tmp`, `helper`, `manager` without a noun.
- A comment explains **why**: a constraint, a game quirk, a protocol rule, a proof reference
  (`# Flag set by Chest.Open (game-map.md#locations)`). Never paraphrase the next line.
- Docstrings on public classes and non-obvious functions: what it guarantees, not how it works.
- No commented-out code, no TODO without an owner and a reason; open work goes in `docs/dev/progress.md`.

## Python (APWorld, Python clients)

- Follow Archipelago's `docs/style.md`: PEP 8, 120 columns, double quotes, f-strings, type annotations on every
  signature and on class members, modern syntax (`dict[str, int | None]`, not `Dict`/`Optional`).
- Imports: absolute for Archipelago core (`from BaseClasses import Item`), relative inside the world
  (`from .data import ITEMS`). `from __future__ import annotations` where it helps with type-only imports.
- Never `eval`, never `yaml.load` (use `Utils.parse_yaml`), never assign to `multiworld.itempool` or
  `multiworld.regions` (always `+=`), never the global `random`.
- `options: MyOptions` with a colon, never `=`.
- Lint with Archipelago's own `ruff.toml` (run `ruff check` from the Archipelago clone against the world folder) and
  keep it clean. `mypy --strict` on the world is a good extra gate when the core types allow it.

## C# (.NET clients)

- Microsoft .NET naming conventions: `PascalCase` types and members, `camelCase` locals and parameters, interfaces
  prefixed `I`. One public type per file, file named after it.
- `TreatWarningsAsErrors` on every project. Enable nullable reference types where the target framework allows it.
- Target the lowest framework the game supports (`netstandard2.0` for Unity 2018+ Mono, `net35` for old Unity) and
  check the client library offers that target (Archipelago.MultiClient.Net ships net35 to net6.0).
- Harmony patches: one class per patched game method, named after it (`ChestOpenPatch`), each calling a single
  method on the bridge. Prefer postfixes; use prefixes that skip the original only when the game must not run it.
- No game types in `ArchipelagoBridge`. The plugin project references the game; the bridge never does.

## Lua, C++, GDScript, JavaScript

- Lua (UE4SS): one module per concern (`client.lua`, `locations.lua`, `items.lua`), `local` everything, no globals
  except what UE4SS requires. All lua-apclientpp calls on the single thread that created the client.
- C++: C++17 or later, RAII, no raw `new`/`delete`, `const` by default, warnings as errors. Pin `apclientpp` to a
  commit as a git submodule.
- GDScript: static typing (`var count: int`), signals for events, one autoload for the client.
- JavaScript (RPG Maker): strict mode, no prototype patching without calling the original, one plugin file per
  concern.

## Tests

- **APWorld**: Archipelago's generic tests (run automatically with `AP_TEST_WORLDS`), the template's
  `test_generation_is_self_contained.py`, and one access test per real logic gate in `data.py`. Each test under one
  second.
- **Client**: unit tests for everything that does not need the game (item pump, flag decoding, ID mapping,
  reconnection back-off). Code that needs the game is kept thin enough that the end-to-end test covers it.
- **End to end** (manual, recorded in `progress.md`): fresh save to goal; disconnect and reconnect mid-game; game
  restart; reload an older save (items must be re-granted exactly once); checks done offline are sent on reconnect;
  DeathLink both ways when enabled.
- A failing test is reported as is, with its output. Never weaken a test to make it pass.

## Adversarial review

Before step 9, spawn a fresh subagent that did not write the code (use a reviewer agent type if the project defines
one) with this brief, and fix every confirmed finding:

> Review this Archipelago integration as an adversary. Assume it is wrong and look for proof. Check:
> 1. Generation: any file read outside the apworld, any network call, any third-party import, any use of the global
>    `random`, any item/location count mismatch, any rule using a non-progression item, any ID reused or renumbered.
> 2. Client: can an item be granted twice (reconnect, resync with index 0, reloading an older save, crash between
>    grant and counter write, a save from another seed)? Can one be lost? Are checks made offline resent? Is the goal sent once? Do network
>    callbacks touch game state off the game thread? Does DeathLink echo its own deaths?
> 3. Claims: does every row of game-map.md have a proof? Is anything stated as fact actually a guess?
> 4. Quality: duplicated logic, game-specific code in the reusable layer, dead code, misleading names, comments that
>    say what instead of why, missing tests.
> 5. Repository: anything from the game committed, build outputs committed, release assets zipped, tag not equal to
>    world_version.
> Report each finding with file:line, a concrete failure scenario, and whether it is confirmed or plausible.
