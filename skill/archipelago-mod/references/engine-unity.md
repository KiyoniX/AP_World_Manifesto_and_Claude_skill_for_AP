# Unity

## Mono or IL2CPP

| Files | Backend | Loader |
| --- | --- | --- |
| `<Game>_Data/Managed/Assembly-CSharp.dll`, no `GameAssembly.dll` | Mono | BepInEx 5 (stable, 5.4.23.x) |
| `GameAssembly.dll` + `global-metadata.dat` | IL2CPP | BepInEx 6 Bleeding Edge builds (https://builds.bepinex.dev), or MelonLoader 0.7.x |

`detect_engine.py` reports which, plus the Unity version read from `globalgamemanagers`. BepInEx 5 does not support
IL2CPP; BepInEx 6 is still pre-release, and its first IL2CPP launch generates interop assemblies (slow, once).
MelonLoader (Apache-2.0) supports both; some existing AP mods pin a specific MelonLoader version, so check the game's
modding community first.

## Template

`--client dotnet` gives:

- `client/ArchipelagoBridge/`: game-agnostic client on Archipelago.MultiClient.Net 6.7.1 (connection, back-off
  reconnection, item pump with save-stored counter, offline resync, goal, DeathLink). Do not edit it per game.
- `client/ArchipelagoBridge.Tests/`: xUnit tests of the pure logic. `dotnet test client/ArchipelagoBridge.Tests`.
- `client/<Class>Archipelago/`: the BepInEx 5 plugin. `Plugin.cs` creates the connection and calls `Update()` every
  frame; `GameAdapter.cs` is the game-specific glue, each member throwing until implemented.

Copy `local.props.example` to `local.props` and set `GameDir`, then `dotnet build`. Pass
`--token UNITY_VERSION=<x.y.z> --token GAME_DATA_DIR=<Game>_Data` to `new_project.py`, from `detect_engine.py`'s
output (`UnityEngine.Modules` versions exist for most releases; use the closest one that restores).

`dotnet build -c Release` puts everything to deploy in the plugin's `bin/Release/netstandard2.0/`: the plugin DLL,
`ArchipelagoBridge.dll`, `Archipelago.MultiClient.Net.dll` and `Newtonsoft.Json.dll` (BepInEx itself is excluded).
Copy those four into `<game>/BepInEx/plugins/<Class>Archipelago/`, and attach them to the release one by one.

### IL2CPP variant

BepInEx 6: the plugin derives from `BasePlugin` and overrides `Load()`. There is no `Update()` on it: register a
`MonoBehaviour` with `ClassInjector.RegisterTypeInIl2Cpp<T>()` and add it to a `DontDestroyOnLoad` object; its
`Update()` calls `Connection.Update()`. TUNIC's randomizer is the reference (MIT):
https://github.com/silent-destroyer/tunic-randomizer (`src/TunicRandomizer.cs`, `src/Archipelago/Archipelago.cs`).
Templates: `dotnet new bep6plugin_unity_il2cpp` (package `BepInEx.Templates`, feed `https://nuget.bepinex.dev`).

## Finding hooks

- Decompile `Assembly-CSharp.dll` with ILSpy (MIT) or dnSpyEx (GPL-3.0, has a debugger). For IL2CPP, recover names
  with Cpp2IL (MIT, maintained) or Il2CppDumper (Unity up to 2022.2, no longer maintained).
- Search for the inventory API (`AddItem`, `Inventory`, `GiveItem`), the save model (`SaveData`, `GameState`,
  `Progress`, flags or dictionaries of booleans), chest and pickup classes (`Chest.Open`, `Pickup.Collect`), death
  (`Die`, `OnDeath`, `Respawn`) and the end of the game (credits, final boss).
- Patch with Harmony (bundled with BepInEx): a postfix on `Chest.Open` calls `Plugin.Connection.ReportLocationChecked`.
  Map game objects to location IDs with a stable key from the game (an ID field, scene name plus object name), never
  a runtime instance ID.
- To give items, call the game's own method so UI, save and events stay consistent; never write fields directly
  unless the game does the same.
- The applied item counter goes into the save: add a key to the game's save dictionary if it has one, or store a
  side file next to the save, keyed by the save slot, written in the same moment as the game saves.
- An in-game object inspector speeds this up: UnityExplorer's original repository is archived (2023); look for a
  maintained fork compatible with the game's Unity version.

## Reference integrations (MIT)

- La-Mulana 2 (BepInEx 5, Harmony, thread-safe queue, persisted index): https://github.com/Crownmuri/LaMulana2Archipelago
- TUNIC (BepInEx 6 IL2CPP): https://github.com/silent-destroyer/tunic-randomizer
- Neon White (MelonLoader): https://github.com/Hyreon/NWArchipelagoMod
- Hollow Knight (game mod API + ItemChanger): https://github.com/ArchipelagoMW-HollowKnight/Archipelago.HollowKnight
- Outer Wilds (OWML, main-thread dispatcher, DeathLink): https://github.com/Ixrec/OuterWildsArchipelagoRandomizer
- Subnautica (BepInEx): https://github.com/Berserker66/ArchipelagoSubnauticaModSrc
