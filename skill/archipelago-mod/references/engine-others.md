# Other engines

Signatures marked unverified by `detect_engine.py` are leads only: confirm by inspecting the files.

## GameMaker

- VM builds keep bytecode in `data.win` (`FORM` + `GEN8` header); YYC builds compile code into the exe (then treat
  as native, `engine-native.md`).
- UndertaleModTool (GPL-3.0) decompiles and edits GML; distribute changes as a bsdiff patch of `data.win` applied on
  the user's copy (Undertale's world in the Archipelago repository does this), or as UndertaleModTool `.csx` scripts.
- Client options: `gm-apclientpp` (MIT, work in progress) called from GML each step, or a Python client exchanging
  files with the game (Undertale uses files under `%LOCALAPPDATA%`).

## RPG Maker MV / MZ (NW.js)

- Plugins are plain JavaScript in `js/plugins/`, registered in `js/plugins.js`: a mod is a plugin.
- Hook by wrapping prototype methods and calling the original (`Scene_Map.prototype.update`,
  `Game_Party.prototype.gainItem`); progress lives in `$gameSwitches`, `$gameVariables`, `$gameParty`.
- Client: `archipelago.js` (MIT) can run in NW.js directly; the verified pattern (Lost Chapter, MIT:
  https://github.com/Crownmuri/LostChapterAP) is a plugin talking over a local WebSocket to a Python client.
- MV detection is verified (`js/rpg_core.js`); MZ (`js/rmmz_core.js`) is not.

## XNA / FNA / MonoGame (.NET)

Use the C# template's `ArchipelagoBridge` unchanged. Hook through the game's own mod loader when one exists (SMAPI
for Stardew Valley, tModLoader for Terraria, Everest for Celeste), otherwise through Harmony loaded by a launcher.
References: Stardew Valley (SMAPI, BSD-3): https://github.com/agilbert1412/StardewArchipelago; Terraria (tModLoader):
https://github.com/Seldom-SE/archipelago_terraria_client.

## Java

Archipelago.MultiClient.Java (MIT, Maven `io.github.archipelagomw:Java-Client`). Reference with the item index
stored in world data: NeoForgeAP (MIT) https://github.com/qixils/NeoForgeAP. Switch back to the server thread before
touching game state.

## Ren'Py

Scripts are Python (`game/*.rpy`, compiled `.rpyc`, archives `.rpa`). No AP integration was found to learn from.
A small `.rpy` file dropped into `game/` can hook labels and the store; the client can run in a thread inside the
game or as an external CommonClient talking over a local socket. Treat this route as unproven and prototype first.

## Source / Source 2

No AP integration was found. Source mods (`gameinfo.txt`, VPK) can add game logic in VScript for some branches;
otherwise use the native routes. Unproven: prototype the feasibility test (step 4) before committing to it.

## LÖVE and other Lua games

`lua-apclientpp` is a native module for Lua 5.1 to 5.4; LÖVE uses LuaJIT, which needs checking. A pure Lua
WebSocket client is an alternative. Unproven.
