---
title: "The AP World Manifesto"
subtitle: "How to build an Archipelago integration that people can trust, play and maintain"
lang: en
---

# Preface

Archipelago lets players shuffle the items of many different games into one shared multiworld: the sword you need
in your game may sit in a chest of someone else's game, and you get it when they open that chest. Every game that
joins this network needs an *integration*, and this manifesto is about building one well.

It is written for people who want to add a game they love, with or without prior modding experience, and without
needing any AI assistant. Each chapter explains **what** to do, **why** it matters, and **how to know you did it
right**. A companion agent skill in the same repository walks an AI assistant through the same process; the two are
independent, and you never need one to use the other.

Facts about Archipelago in this text were checked against its repository in October 2026 (release 0.6.8). The
project moves: whenever a detail here disagrees with the official documentation, the official documentation wins.

## How to read this

- Chapters 1 to 3 are for everyone: what an integration is, the principles, and the questions to answer first.
- Chapters 4 to 6 are the technical journey: reach the game, prove it is feasible, map it.
- Chapters 7 to 9 build, test and ship it.
- Chapter 10 is a checklist to review your work, or someone else's.

# 1. What an integration is

An Archipelago integration has two halves that never talk to each other directly:

| Half | Language | Runs | Job |
| --- | --- | --- | --- |
| **APWorld** | Python | Once, when a multiworld is *generated* | Describe the game: its items, its locations, which items unlock which locations, the goal, the options |
| **Client** | Whatever the game allows | During play, alongside or inside the game | Tell the server which locations the player completed, give the player the items the server sends, report the goal |

Between them sits the **Archipelago server**. At generation, every player's APWorld contributes its items and
locations to one big pool, and the generator places items so that every player can finish. During play, each
client sends *location checks* to the server and receives *items* from it.

Some vocabulary you will meet everywhere:

- **Location** (or *check*): somewhere an item can be found: a chest, a quest reward, a boss drop, a shop slot.
- **Item**: something a player can receive: a key, a weapon, an upgrade, a pile of money, a trap.
- **Progression item**: an item that some rule needs to reach a location. The generator guarantees it is reachable.
- **Region** and **entrance**: the map of the game as a graph, used to express access rules.
- **Sphere**: the set of locations reachable with what you have; sphere 1 is what you can do from the start.
- **Slot data**: per-player data the APWorld hands to the client at connection (options, randomized layout).
- **Goal**: the in-game condition that completes a player's game.

# 2. The principles

These principles are not style preferences. Each one prevents a class of failures that players have actually met:
lost items, broken seeds, worlds that stop loading after an update, repositories taken down. Follow all of them.

## 2.1 Quality you can read

Write code a stranger can read. Somebody else will maintain your integration one day, maybe you in two years.

- **Keep it simple.** The simplest design that works is the right one. Do not add an abstraction for one use, or an
  option nobody asked for.
- **Do not repeat yourself.** If two pieces of code do the same thing, keep one. Before writing a helper, check
  whether Archipelago or your client library already has it: they solve connection, reconnection, item indexing and
  DeathLink already.
- **Separate what is reusable from what is game-specific.** Connection handling, item granting and location
  reporting do not depend on your game: keep them in one layer that never mentions the game. Hooks, addresses and
  item tables are game-specific: keep them in another layer that never talks to the network. The next game then only
  needs a new game layer.
- **Prefer data to code.** Items, locations, regions and rules belong in tables. Adding a location should be one new
  line, not a new function.
- **Name things for what they are**, in English, and comment only *why* something is done, never *what* the next line
  does.
- **Fail loudly.** An unknown item, an unimplemented hook, an impossible state: raise or log clearly. A silent
  default hides a bug until a player loses an item.
- **Test what can break**, and never weaken a test to make it pass.

## 2.2 Generation is self-contained

When a multiworld is generated, your APWorld runs on someone else's computer, often on a server, next to dozens of
other worlds. So, during generation, it must:

- **read no file outside its own package**: not the game, not a ROM, not a save, not the user's settings;
- **depend on nothing but Python's standard library and Archipelago itself**: no extra packages to install;
- **make no network call.**

Everything the APWorld knows about the game is data shipped inside it. If the game needs patching (a ROM, a data
file), the APWorld writes a patch into the output folder and the client applies it to the player's own copy.

Why so strict? A world that reads the user's files cannot be generated on a server. A world that pulls packages
breaks when they change or are unavailable, and runs code nobody reviewed. A world that calls the network makes
generation slow, fragile and non-reproducible. A self-contained world generates anywhere, forever, with the same
result for the same seed.

## 2.3 One project, one repository, clean releases

- **Do not fork Archipelago** to develop your world. Clone the official repository next to yours and link your world
  into it (chapter 7). A fork drifts from upstream, hides your work among thousands of unrelated files and makes
  updates painful. The only reason to fork is a change to Archipelago itself, proposed back upstream.
- **One project, one repository**: your APWorld, your client, their documentation and tests live together. Players
  and contributors find everything in one place, and the two halves are versioned together.
- **Nothing built is committed.** The `.apworld` file and the client binaries are build outputs: they are produced
  from the sources and attached to releases.
- **Releases are tagged** `vX.Y.Z`, the same number as `world_version` in the APWorld's manifest, so the tag, the
  manifest and the published files always agree.
- **Release assets are attached as they are**: the `.apworld` itself (it is already a zip archive), the client in
  its native form. No extra `.zip` around them: players can see exactly what they install.

## 2.4 Legitimate use only

- You play your own, legally obtained copy, offline or on your own multiworld.
- Never bypass anti-cheat, DRM or online protections, and never mod a game whose online mode could be affected.
- Never publish anything taken from the game: no assets, binaries, decompiled code, dumps, ROMs or saves. Your
  repository contains your own code and your own findings (names, IDs, offsets), nothing else.
- Some store agreements restrict reverse engineering and modding (Steam's subscriber agreement does). Read the terms
  that apply to you; this manifesto is not legal advice.

# 3. Before you write anything

## 3.1 Does it already exist?

Joining or continuing an existing integration is almost always better than starting another one. Search:

- the official list of supported games: <https://archipelago.gg/games>;
- the guide to unofficial games and tools: <https://archipelago.gg/tutorial/Archipelago/other_en>;
- GitHub, for `"<game name>" archipelago` and `<game name> apworld`;
- the community wiki: <https://archipelago.miraheze.org/>;
- the `#apworld-index` channels of the Archipelago Discord (<https://discord.gg/8Z65BR2>) and of the
  Archipelago After Dark Discord (<https://discord.gg/fqvNCCRsu4>).

If you find something, talk to its authors before starting over.

## 3.2 Is the game a good candidate?

Good candidates have many distinct pickups, a progression gated by items (keys, abilities, upgrades), a clear goal,
and a way to be modified. Games that are hard to randomize well: purely linear games with few pickups, games whose
progression is skill-based rather than item-based, and games with online-only modes or active anti-cheat.

## 3.3 What will checks, items and the goal be?

Write down, in plain words, before any code:

- what counts as a location (and roughly how many there are);
- what can be sent as an item, and which items gate progress;
- what the goal is;
- what should *not* be randomized (story items that would soft-lock the game, for instance).

You know the game; this list is where that knowledge matters most. It will change, and that is fine.

## 3.4 Can the game not be modded at all?

Then consider **Manual for Archipelago** (<https://github.com/ManualForArchipelago/Manual>): you describe items and
locations in JSON, and players tick checks by hand in a client while honouring the items they received. It needs no
mod, works for any game, and still benefits from everything in chapters 3, 6 and 7 about designing a good map.

# 4. Reaching the game

The client must do four things inside or beside the game: run regularly (every frame, or a few times per second),
know when a save is loaded, see progress, and change the inventory. *How* depends on the engine.

## 4.1 Identify the engine

Look at the game's installation folder:

| You see | Engine |
| --- | --- |
| `<Game>_Data/Managed/Assembly-CSharp.dll`, no `GameAssembly.dll` | Unity, Mono scripting backend |
| `GameAssembly.dll` and `global-metadata.dat` | Unity, IL2CPP scripting backend |
| `<Game>/Content/Paks/*.pak` (and `.utoc`/`.ucas` since UE 4.26), exe in `<Game>/Binaries/Win64/` | Unreal Engine |
| A `.pck` file starting with `GDPC`, or a pack appended to the exe | Godot |
| `data.win` (or `game.unx`, `game.ios`) starting with `FORM` ... `GEN8` | GameMaker (bytecode) |
| `js/rpg_core.js` | RPG Maker MV |
| `game/*.rpy`, `.rpyc` or `.rpa` | Ren'Py |
| `FNA.dll`, `MonoGame.Framework.dll` or XNA assemblies | .NET game frameworks |
| A ROM or disc image | Emulated console game |
| None of the above | Native or custom engine |

Note the store and exact build too (Steam, GOG, version number), and hash the executable: offsets and hooks are
only valid for the build you found them on.

## 4.2 Choose the route

| Engine | Usual route | Client library |
| --- | --- | --- |
| Unity Mono | BepInEx 5 plugin, Harmony patches | Archipelago.MultiClient.Net (C#) |
| Unity IL2CPP | BepInEx 6 (bleeding edge) or MelonLoader | Archipelago.MultiClient.Net |
| Unreal | UE4SS Lua mod, or UE4SS C++ mod | lua-apclientpp / apclientpp |
| Godot | Godot Mod Loader, or an autoload added through a pack patch | GodotAP (GDScript) |
| GameMaker | Patched `data.win`, extension calls | gm-apclientpp, or a Python client exchanging files |
| RPG Maker MV/MZ | JavaScript plugin | archipelago.js, or a local bridge to a Python client |
| .NET frameworks | The game's mod loader (SMAPI, tModLoader, Everest) or Harmony | Archipelago.MultiClient.Net |
| Java | The game's mod loader | Archipelago.MultiClient.Java |
| Emulated | Archipelago's BizHawkClient, SNIClient, Dolphin or PCSX2 clients | Built into Archipelago (Python) |
| Native, no mod support | External program reading memory, or a DLL loaded by the game | Archipelago's CommonClient, apclientpp, archipelago_rs |

Prefer, in this order: the game's own mod support, an established mod loader for the engine, an emulator framework
that Archipelago already ships, and only then raw memory access. The higher in this list, the more your client
survives game updates.

## 4.3 Learn from existing integrations

Reading a maintained integration on the same engine teaches more than any document. A few with permissive licences:
La-Mulana 2 and TUNIC (Unity), Hollow Knight (Unity, through the game's mod API), Stardew Valley (SMAPI), the Dark
Souls III and Sekiro clients (a Rust DLL), Brotato (Godot), Lost Chapter (RPG Maker MZ), and inside the Archipelago
repository itself the BizHawk-based worlds such as Pokémon Emerald or Mega Man 2. Respect licences: a repository
without one is something you can learn from, not copy from.

# 5. Prove it is feasible first

Before mapping a whole game, prove the three risky links. Archipelago's own developer FAQ recommends the same order:

1. **A hook runs.** Your code executes regularly inside or beside the game, and can tell a save is loaded.
2. **One check and one item work.** You can detect one location of each major kind (a chest, a quest, a boss) and
   give one item, in the real game.
3. **A round trip works.** A minimal APWorld generates, a local server hosts it, your client connects, sends that
   check, and receives an item.

The APWorld part of this step is the easy one: a world with a handful of fixed items and locations is a few dozen
lines. If one of the three links cannot be made to work, stop here and reconsider the route, or Manual, before
investing weeks.

# 6. Mapping the game

## 6.1 What you are looking for

1. a **per-frame hook** (or a polling loop) and a way to know a save is loaded;
2. for each kind of **location**, the persistent flag or the event that says it is done;
3. for each **item**, the game's own way of giving it;
4. the **goal** condition;
5. a place **in the save** to store how many received items were already applied;
6. the **death** event and a way to kill the player, if you offer DeathLink.

## 6.2 How to find it

- **Managed engines first.** Unity Mono, .NET, Java, GDScript, JavaScript and GameMaker bytecode decompile into
  readable code with names. Search for words like `Inventory`, `AddItem`, `Save`, `Flag`, `Chest`, `Pickup`, `Boss`,
  `Death`, `Credits`. Tools: ILSpy or dnSpyEx (.NET), Cpp2IL (Unity IL2CPP), UE4SS and FModel (Unreal), gdre_tools
  (Godot), UndertaleModTool (GameMaker).
- **Value scanning.** Change one thing in the game (open a chest, pick up a coin), scan memory for values that
  changed, repeat until few candidates remain, then confirm across a save and a reload. Tools: Cheat Engine on PC,
  BizHawk's RAM Search for emulated games, Dolphin Memory Engine for GameCube and Wii.
- **Who writes it.** Once you have a flag, find the instruction that writes it (Cheat Engine's "find out what writes
  to this address") and read the function around it in Ghidra or x64dbg. That function is usually the best hook.
- **Save diffing.** Copy the save before and after one event and compare the files. Flags that live in the save are
  exactly what you need to recover checks made while offline.
- **Existing knowledge.** RAM maps on Data Crystal (<https://datacrystal.tcrf.net>), decompilation projects, speedrun
  notes and older randomizers. Credit them.

## 6.3 Prove every finding

Keep a *game map*: a document with one row per location, item, gate and hook, recording what it is, where it lives
(class and method, module-relative offset, memory domain and address), the build it was found on, how it was found,
and the observation that proves it ("set to 1 when the chest opens, survives a reload"). Prove each finding twice,
including after a reload, before you rely on it. A row without proof is a hypothesis and must be labelled as one.

## 6.4 Traps

- **Addresses move.** Executables are loaded at a different base each launch (ASLR): record `module + offset`.
  Objects reached through pointers move on level loads: resolve the pointer chain every time.
- **Builds differ.** Steam, GOG, Epic and every patch have different binaries. Support named builds, detect them by
  hash, and refuse unknown ones with a clear message.
- **Work memory is not the save.** A value in memory may be a temporary copy; trust what gets saved.
- **One-shot events cannot be replayed.** If a check is only visible as an event, a player who completes it while
  disconnected loses it unless you persist it. Prefer persistent flags.

## 6.5 Design the randomizer

With the map in hand, decide:

- **Which locations count.** Include what is fun to find and reliable to detect. Avoid locations that can be missed
  forever, or mark them clearly.
- **Which items are progression.** Every item that a rule mentions must be progression. Keep progression items
  meaningful: too many trivial ones make the logic opaque.
- **Sphere 1.** The start must offer enough reachable locations, or generation fails and seeds feel stuck. Give a
  few starting items or early locations if needed.
- **Filler and traps.** You need at least one item that can be created any number of times (money, ammunition) to
  fill the pool. Traps are optional fun; make them opt-in.
- **Options.** Offer only options you will test and the client honours. Each option multiplies the cases to check.
- **The goal.** One clear condition, reported reliably by the client.

# 7. Building the APWorld

## 7.1 Set up the workshop

Do not fork Archipelago. Clone the official repository next to your project at the release you target, then link
your world into its `worlds` folder:

```sh
git clone --branch 0.6.8 https://github.com/ArchipelagoMW/Archipelago ../Archipelago
ln -s "$(pwd)/apworld/my_game" ../Archipelago/worlds/my_game   # on Windows: mklink /D, with developer mode
cd ../Archipelago
python ModuleUpdate.py --yes          # installs Archipelago's own dependencies
python Launcher.py --update_settings  # creates host.yaml
```

Archipelago needs Python 3.11.9 to 3.13 on Windows. Read the official teaching world, **APQuest**
(`worlds/apquest/` in the repository): every step is commented. The documents in the repository's `docs/` folder are
the reference: `world api.md`, `apworld_dev_faq.md`, `rule builder.md`, `options api.md`, `tests.md` and
`adding games.md`.

## 7.2 The shape of a world

```
apworld/my_game/
  archipelago.json   the manifest: game, minimum_ap_version, world_version, authors
  __init__.py        imports the World class
  data.py            the game map as data: items, locations, regions, entrances, goal
  world.py           generic code that builds the world from data.py
  options.py         player options
  web_world.py       website metadata and tutorial
  docs/              en_<Game>.md (game page) and setup_en.md (setup guide)
  test/              tests
```

The manifest is required from Archipelago 0.7.0. Do not write `version` or `compatible_version` in it: the build adds
them.

## 7.3 Describe the game as data

```python
@dataclass(frozen=True)
class LocationData:
    id: int
    region: str
    rule: Rule = field(default_factory=True_)

ITEMS = {
    "Progressive Sword": ItemData(1, ItemClassification.progression, pool_count=2),
    "Key": ItemData(2, ItemClassification.progression),
    "Coin": ItemData(4, ItemClassification.filler, pool_count=0),
}
ENTRANCES = (
    EntranceData("Menu", "Village"),
    EntranceData("Village", "Dungeon", Has("Key")),
)
LOCATIONS = {
    "Village Chest": LocationData(1, "Village"),
    "Dungeon Chest": LocationData(3, "Dungeon"),
}
```

Rules use Archipelago's rule builder (`Has`, `HasAll`, `Has(..., count=2)`, combined with `&` and `|`). They are
readable, serializable, and Archipelago can explain them to players.

Rules for IDs: unique integers between 1 and 2^31 - 1, separately for items and locations. Every item and location
that can ever exist must be listed, even if an option removes it. Once released, an ID never changes meaning: add
new ones, never renumber.

## 7.4 Build the world from the data

The world class then stays generic: create one region per name, one entrance per row with its rule, one location
per row; add the goal as an event in the goal region; create the item pool from the item table, and fill the
remaining slots with the filler item, so the number of items always equals the number of locations. Always use
`self.random` for randomness, never Python's global `random` module, so the same seed gives the same result.
`fill_slot_data` returns the small set of values the client needs (options, randomized layout).

## 7.5 Test it

- Archipelago runs generic tests on every world: everything is reachable with all items, something is reachable
  with none, a full fill succeeds. Run them with `AP_TEST_WORLDS=my_game python -m pytest` from the Archipelago
  folder.
- Add one test per real gate in your map ("the dungeon chest needs the key").
- Add a test that proves generation is self-contained: run every generation step while network access is blocked
  and file opens outside the world folder fail, and check the guard itself rejects such accesses.
- Generate a real seed: create a template YAML with the Launcher's "Generate Template Options", put a filled copy in
  `Players/`, run `python Generate.py`, and host the result with `python MultiServer.py output/AP_<seed>.zip`.

## 7.6 Package it

`python Launcher.py "Build APWorlds" -- "My Game"` writes `build/apworlds/my_game.apworld`. Players install it with
the Launcher's "Install APWorld" or by double-clicking it.

# 8. Building the client

## 8.1 What every client must do

From Archipelago's requirements:

1. connect over WebSocket, both secure (`wss://`) and not (`ws://`), with a changeable host and port;
2. reconnect automatically when the connection drops;
3. send location checks when they happen, and on every connection resend all locations already completed in the
   save, because actions done while disconnected cannot be replayed;
4. accept any item any number of times, including items with no sender (starting inventory, admin commands);
5. remember how many received items were already applied, and apply only the newer ones;
6. report the goal once.

## 8.2 The item counter, where most bugs live

The server sends received items as an ordered list that is the same on every connection. So the state to keep is
*how many items of that list this save has applied*, and it belongs **in the save itself**:

- apply items starting from that count, and increase it only *after* the game accepted the item;
- if the game cannot take an item right now (cutscene, menu), retry later without skipping it;
- spread a large backlog over several frames;
- because the count lives in the save, reloading an older save re-applies exactly what that save is missing, and a
  new save starts from zero.

Storing the count anywhere else (a global file, memory only) leads either to duplicated items or to lost ones.

## 8.3 Threads

Client libraries call you back on their network thread. Never touch game state from there: put events in a queue
protected by a lock, and drain it from the game's own update loop. Some libraries (lua-apclientpp) require that the
client is created and polled on one single thread.

## 8.4 DeathLink

DeathLink is optional and controlled by a player option passed in slot data. When enabled, send a death when the
player dies, and kill the player when a death arrives, at a safe moment. Do not send back the death you just caused.

## 8.5 Player experience

Show the connection state and errors, the items received and who sent them, and the goal. Let players set server,
slot name and password without editing code. Check the world version you receive in slot data and warn on a
mismatch with the client.

## 8.6 Keep the game layer thin

All the above is identical for every game. Write it once, as a reusable layer with no reference to the game, and
put everything game-specific behind a small interface: "is a save loaded", "read completed locations", "is the goal
reached", "give this item", "kill the player", "show a message", "read and write the applied item count". A new game
is then a new implementation of that interface, and the reusable layer can be unit-tested without the game.

# 9. Testing and shipping

## 9.1 The end-to-end test

Automated tests cover generation and the client's logic. Before each release, also play a seed locally and check, by
hand:

- a fresh save reaches the goal;
- disconnecting and reconnecting in the middle of play loses nothing and duplicates nothing;
- restarting the game keeps everything;
- reloading an older save re-grants exactly the missing items, once;
- checks completed while disconnected are sent on reconnection;
- DeathLink works in both directions when enabled, and is silent when disabled.

## 9.2 Repository layout

```
<repo>/
  apworld/<module>/        the world package
  client/                  the in-game client, if it is not inside the world
  docs/dev/progress.md     what is done, what is open, decisions taken
  docs/dev/game-map.md     every finding with its proof
  tools/                   project checks run by CI
  .github/workflows/       tests and builds on every push; publishes on tags
```

Never commit build outputs, local configuration, or anything from the game. Reference game files at build time from
the developer's own installation, through a git-ignored local setting.

## 9.3 Continuous integration

On every push, CI checks out your repository and the official Archipelago repository at the pinned release (never a
fork, never `main`), runs the static checks, the world's tests and Archipelago's generic tests, and builds the
`.apworld`. Bumping the pinned Archipelago release is a deliberate change, tested like any other.

## 9.4 Releasing

1. Bump `world_version` (semantic versioning: changing an ID or the slot data shape is a major version).
2. Commit, tag the commit `v<world_version>`, push the tag.
3. CI verifies the tag matches the manifest, tests, builds and creates the release with the `.apworld` attached.
4. Build the client and attach its files in their native form. No zip around them.
5. Release the world and the client together, under the same version.

Choose a licence before your first public push. MIT is common in the Archipelago ecosystem and is Archipelago's own.

# 10. The review checklist

Use it on your own work before each release, ideally with a second pair of eyes that did not write the code.

**Generation**

- [ ] No file read outside the world, no network call, no dependency beyond the standard library and Archipelago.
- [ ] Only `self.random` is used for randomness.
- [ ] Item count equals location count with every combination of options.
- [ ] Every item used in a rule is progression.
- [ ] No ID was reused or renumbered since the last release.
- [ ] Archipelago's generic tests, the gate tests and the self-contained test pass.

**Client**

- [ ] An item can never be granted twice: reconnection, full resync, older save, crash between grant and save.
- [ ] An item can never be lost: refused items are retried, order is kept.
- [ ] Checks done offline are sent on reconnection.
- [ ] The goal is reported once.
- [ ] Network callbacks never touch game state off the game thread.
- [ ] DeathLink does not echo its own deaths.

**Claims**

- [ ] Every row of the game map has a proof; hypotheses are labelled.
- [ ] Documentation matches the code.

**Code quality**

- [ ] No duplicated logic, no dead code, no game-specific code in the reusable layer.
- [ ] Names are clear, comments explain why.
- [ ] Tests cover what can break.

**Repository**

- [ ] Nothing from the game is committed, and no build output.
- [ ] Release assets are attached unzipped, and the tag equals `world_version`.

# Appendix A. Tools

| Tool | For | Licence |
| --- | --- | --- |
| ILSpy, dnSpyEx | .NET decompiling (dnSpyEx also debugs) | MIT, GPL-3.0 |
| Cpp2IL | Unity IL2CPP names and signatures | MIT |
| BepInEx, MelonLoader, Harmony | Unity mod loading and patching | LGPL-2.1, Apache-2.0, MIT |
| UE4SS, FModel | Unreal live inspection, mods, archives | MIT, GPL-3.0 |
| gdre_tools | Godot packs and GDScript | MIT |
| UndertaleModTool | GameMaker data files | GPL-3.0 |
| Cheat Engine | Memory scanning on PC | Read its terms |
| Ghidra, x64dbg | Disassembly and debugging | Apache-2.0, GPL-3.0 |
| BizHawk, Dolphin Memory Engine | Emulated memory search | MIT |
| Detect It Easy | Identify packers, compilers, engines | MIT |

Using a GPL tool is fine. Copying its code into your project makes that part GPL. What these tools extract from the
game stays on your machine.

# Appendix B. Client libraries

| Language | Library |
| --- | --- |
| C# / .NET | Archipelago.MultiClient.Net (NuGet) |
| Python | Archipelago's CommonClient, BizHawkClient, SNIClient |
| C++ | apclientpp (header-only), APCpp |
| Lua | lua-apclientpp |
| JavaScript / TypeScript | archipelago.js (npm) |
| Rust | archipelago_rs (crates.io) |
| Java | Archipelago.MultiClient.Java (Maven) |
| GameMaker | gm-apclientpp |
| GDScript | GodotAP |

# Appendix C. Where to get help

- Archipelago's documentation: <https://github.com/ArchipelagoMW/Archipelago/tree/main/docs>
- The Archipelago Discord (<https://archipelago.gg/discord>): `#ap-world-dev` for worlds, `#ap-modding-help` for
  engines and mods.
- Universal Tracker and PopTracker, to test that your logic is understandable from the player's side.
