# Godot

## Getting code into the game

- If the game ships **Godot Mod Loader** (https://github.com/GodotModding/godot-mod-loader, CC0; Brotato, Dome
  Keeper...), write a regular mod for it: it overrides scripts and scenes without touching game files.
- Otherwise, use **gdre_tools** (https://github.com/GDRETools/gdsdecomp, MIT) to extract the pack and to build a
  patch pack containing only your files:
  ```sh
  gdre_tools --headless --extract=game.pck --output=extracted/          # read-only exploration, never committed
  gdre_tools --headless --pck-patch=game.pck --output=patched.pck --patch-file=mod/ap_client.gd=res://ap_client.gd
  ```
  Distribute your scripts and a patch step, never the game's pack. An autoload added through the patch hosts the
  client; `ProjectSettings.load_resource_pack()` from an early autoload can also load a mod pack.

## Client

- **GodotAP** (https://github.com/EmilyV99/GodotAP, MIT, GDScript): add `godot_ap/autoloads/archipelago.tscn` as an
  autoload and listen to its signals (`connected`, `disconnected`, `printjson`...).
- Brotato's client (https://github.com/SpenserHaddad/Brotato-ArchipelagoClient, MIT) is a clean example of a game
  client layered on a generic GDScript client, packaged as a Mod Loader mod.
- Known limit: Godot's WebSocket does not support compression, and the protocol marks uncompressed connections as
  deprecated (currently a warning only). If that ever becomes an error, fall back to a local Python client
  (CommonClient) talking to the game over a local socket or files.

## Finding hooks

The decompiled GDScript is readable: look for the save singleton (an autoload holding progress dictionaries), item
pickup and chest scripts, the inventory add function and the death signal. The per-frame hook is `_process(delta)` of
your autoload.
