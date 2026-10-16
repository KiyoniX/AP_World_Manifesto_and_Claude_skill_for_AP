# Unreal Engine 4 / 5

## Loader

UE4SS (https://github.com/UE4SS-RE/RE-UE4SS, MIT) supports UE 4.7 to 5.x on Windows. Most AP mods use the stable
3.0.1; the experimental build moves files into a `ue4ss/` subfolder. Install into the folder of the real executable,
`<Game>/Binaries/Win64/` (`detect_engine.py` prints it). Mods live in `Mods/<Name>/Scripts/main.lua` and are listed in
`Mods/mods.txt`. UE4SS is not plug-and-play: recent games may need AOB signatures fixed (see its "fixing
compatibility problems" guide). Docs: https://docs.ue4ss.com.

## Two routes

1. **Lua mod + lua-apclientpp** (https://github.com/black-sliver/lua-apclientpp, MIT). Simplest. The DLL must match
   UE4SS's Lua version.
2. **C++ mod + apclientpp** (header-only, MIT), built against UE4SS in a CMake workspace (`RC::CppUserModBase`,
   `start_mod` / `uninstall_mod` exports). More work, full engine access.

There is no template for either yet: write the client following `client-protocol.md` and the layering of
`quality.md`. Keep the reusable part (connection, item pump, location reporting) in its own module, and the game
part (hooks, item and location tables) in others.

## Threading rule (critical)

lua-apclientpp requires that the client is created and `poll()`ed on the same thread. UE4SS runs `RegisterHook`
callbacks on other threads. So: create the client and do every client call inside a single
`LoopAsync(ms, function() ... return false end)` callback; game hooks only push events into a table that this loop
drains. Use `ExecuteInGameThread` to touch game objects from the loop. Crab Champions' AP client documents and
follows this pattern (its repository has no licence: read, do not copy):
https://github.com/Str8UpWHITE64/CrabChampionsAP.

## Finding hooks

- UE4SS Live View browses live objects and properties; its dumpers produce C++ headers with offsets and `.usmap`
  mappings. Generated dumps are game data: keep them out of the repository.
- FModel (GPL-3.0) explores `.pak` and IoStore (`.utoc`/`.ucas`) archives to find Blueprint names.
- `RegisterHook("/Script/Module.Class:Function", pre, post)` for native functions; for Blueprint functions the second
  argument runs after. The function must already be loaded when you register: register on a later event if needed.
- Typical targets: pickup or chest Blueprint functions, the inventory component's add function, the save game object
  (a `USaveGame` subclass, where the applied item counter can be stored if the game serializes a map or array you can
  extend), the player death event.

## Reference integrations

- Crab Champions (Lua + lua-apclientpp): https://github.com/Str8UpWHITE64/CrabChampionsAP (no licence)
- Pseudoregalia (C++ + apclientpp): https://github.com/pseudoregalia-modding/pseudoregalia-archipelago (no licence)
- Dead as Disco (Lua mod exchanging JSONL files with a Python client): https://github.com/daevien71-cloud/Dead-as-Disco-Archipelago
