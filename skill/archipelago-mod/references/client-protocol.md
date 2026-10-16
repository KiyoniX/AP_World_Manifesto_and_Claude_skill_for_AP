# What every client must do

Sources: `docs/adding games.md` (hard requirements) and `docs/network protocol.md` in the Archipelago repository,
plus patterns verified in maintained clients (La-Mulana 2, TUNIC, Dark Souls III, NeoForgeAP).

## Hard requirements (from `docs/adding games.md`)

1. Connect over WebSocket, both `ws://` and `wss://`; let the player change host and port.
2. Reconnect automatically when the connection drops.
3. Send `LocationChecks` when a location is done, **and** on every connection resend all locations already done in
   the save: actions done offline cannot be replayed. Duplicates are harmless.
4. Accept any item any number of times, including items with no sender or location (start inventory, admin
   commands, item links).
5. Keep an index of received items to resynchronize with the server.
6. Send `StatusUpdate` with status 30 (`CLIENT_GOAL`) when the goal is reached.

## Choices this skill makes on top

These are not written in Archipelago's documents; they are how the maintained clients avoid the classic bugs:

- the received-item index is a count of applied items stored **in the save**, written together with the items;
- the save is **bound to its seed and slot**, so a save from another multiworld is never synced;
- the goal is sent **once** per connection;
- DeathLink is enabled only when the player's option is on, and the death the client causes is not echoed.

## Item indexing, the part that goes wrong

The server sends `ReceivedItems` with an `index` and an ordered list. The full list is the same on every connection,
so the right state to persist is "how many items of that list this save has applied".

- On each update, apply items from `applied_count` onwards, and increase `applied_count` only **after** the game
  accepted the item. Store it in the save so that reloading an older save re-applies exactly what it lacks.
- `index == 0` means a full resync: the list replaces everything. With the persisted count, nothing special is needed.
- An `index` other than expected: send `Sync` (then `LocationChecks`); client libraries do this for you.
- Spread a large backlog over frames (one or a few items per frame).
- If the game refuses an item now (cutscene, menu), retry later without skipping it, so order is preserved.

`ArchipelagoBridge` (C# template) and the BizHawk template implement exactly this; reuse them.

## Threads

Library callbacks run on the network thread. They must only enqueue (under a lock, or with a concurrent queue). The
game thread drains the queue once per frame. lua-apclientpp requires creation and `poll()` on the same thread: do all
calls inside one `LoopAsync` callback in UE4SS.

## items_handling

Bit flags sent in `Connect`: `0b001` items from other worlds, `0b010` items from your own world, `0b100` starting
inventory. A client that lets the server send everything (the usual choice, because the game does not place its own
items) uses `0b111` (`ItemsHandlingFlags.AllItems` in .NET).

## DeathLink

Optional, controlled by the player's `death_link` option sent in slot data. Enable the `DeathLink` tag only when it
is on, and never send a death otherwise: the server forwards any DeathLink bounce, it does not check the sender's
tags, so a client that sends while disabled kills everyone who enabled it. Send a `Bounce` with tags `["DeathLink"]` and `{time, source, cause}` when the player dies; on receiving one,
kill the player at the next safe moment, and do not send back the death you just caused (ignore deaths for a short
window after applying one, as the bridge does).

## Messages and UI

Show at least: connection state and errors, items received (with sender), and the goal. Use the library's message
log (`PrintJSON` parts carry colours and item flags). Let the player edit server, slot and password without editing
code (config file, in-game menu).

## Data storage and hints

`Get` / `Set` / `SetNotify` on server-side keys store shared state (e.g. a tracker's map position). `LocationScouts`
tells the client which item sits at a location, to show it in game; prefer it over putting placements in slot data.

## Client libraries (maintained, October 2026)

| Language | Library | Notes |
| --- | --- | --- |
| C# / .NET | Archipelago.MultiClient.Net 6.7.1 (NuGet, MIT) | net35 to net6.0; standard for Unity, XNA, FNA |
| Python | Archipelago `CommonClient` | For external clients; BizHawkClient and SNIClient build on it |
| C++ | apclientpp (header-only, MIT) | No releases: pin a commit as a submodule |
| Lua | lua-apclientpp (MIT) | Native DLL; Lua version and C runtime must match the host |
| JavaScript / TS | archipelago.js 2.1.0 (npm, MIT) | Browser and NW.js (RPG Maker) |
| Rust | archipelago_rs 3.0.1 (crates.io, MIT) | Safe to drive from the game loop |
| Java | Archipelago.MultiClient.Java 0.2.1 (Maven, MIT) | Minecraft-style mods |
| GameMaker | gm-apclientpp (MIT, work in progress) | GM 8 and later through the DLL API |
| C++ (CMake) | APCpp (LGPL-2.1) | Licence is more restrictive |
