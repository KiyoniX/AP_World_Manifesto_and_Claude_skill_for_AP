# Finding the game loop, checks, items and goal

What the integration needs from the game, in order of discovery:

1. a **per-frame hook** or a polling loop, plus a way to know a save is loaded and gameplay is running;
2. for each kind of **location**: the event or the persistent flag that says it is done;
3. for each **item**: the game's own way to give it;
4. the **goal** condition;
5. a place **in the save** to store the applied-item counter;
6. the **death** event and a way to kill the player (for DeathLink).

## Method

- **Start from what the engine gives you.** Managed engines (Unity Mono, .NET, Java, GDScript, JavaScript, GML VM)
  decompile to readable code with names: search by name first (`Inventory`, `AddItem`, `Save`, `Flag`, `Chest`,
  `Pickup`, `Boss`, `Death`, `Credits`). Native code needs the next tools.
- **Value scanning** (Cheat Engine for PC, BizHawk RAM Search, Dolphin Memory Engine): change one thing in game (open
  a chest, pick up an item), scan for changed values, repeat until a few candidates remain, then confirm by watching
  them across a save and reload.
- **Who writes it**: once a flag or counter is found, Cheat Engine's "find out what writes to this address" gives the
  instruction, and Ghidra or x64dbg give the function around it: that function is the hook.
- **Save diffing**: copy the save before and after one event and diff the files (binary diff or a hex editor). Flags
  that persist in the save are exactly what offline resync needs.
- **Prove each finding** before it enters `data.py`: change it by hand and watch the game react, or trigger it in
  game and watch the value change, twice, including after a reload.

## Recording proofs

Each row of `docs/dev/game-map.md` holds: the name, what it is (flag, counter, method, Blueprint function), where
(module-relative offset or pointer chain, class and method, memory domain and address), the game build it was found
on (executable SHA-256 from `detect_engine.py`), how it was found, and the observation that proves it. A row without
proof is marked "hypothesis" and is not shipped as fact.

## Pitfalls

- **ASLR**: a module's base moves each launch; record `module+offset`, never an absolute address.
- **Moving objects**: data reached through pointers moves on level loads; re-resolve every time, guard writes.
- **Builds differ**: Steam, GOG, Epic and each patch have different binaries and offsets. Pin the supported build by
  hash and refuse others with a clear message.
- **Work RAM vs save**: a value in work RAM may be a copy; the authoritative one is what gets saved.
- **One-shot events**: a check detected only by an event (not a flag) cannot be resent after an offline session;
  prefer persistent flags for location detection, or persist the event yourself.

## Tools (state checked October 2026)

| Tool | For | Licence | Status |
| --- | --- | --- | --- |
| ILSpy | .NET decompiler | MIT | Active |
| dnSpyEx | .NET decompiler and debugger | GPL-3.0 | Active (the original dnSpy is archived) |
| Cpp2IL | Unity IL2CPP names and signatures | MIT | Active |
| Il2CppDumper | Unity IL2CPP (up to 2022.2) | MIT | Unmaintained since 2024 |
| AssetRipper | Unity assets (exploration only) | GPL-3.0 | Active |
| UE4SS | Unreal live view, dumps, Lua and C++ mods | MIT | Active |
| FModel | Unreal pak / IoStore explorer | GPL-3.0 | Active |
| gdre_tools | Godot pack extraction and GDScript decompiler | MIT | Active |
| UndertaleModTool | GameMaker data.win | GPL-3.0 | Active |
| Detect It Easy | Packers, compilers, DRM, some engines | MIT | Active |
| Cheat Engine | Value scans, pointer scans, "what writes" | Not determined, read its terms | Active |
| Ghidra | Disassembler and decompiler | Apache-2.0 | Active |
| x64dbg | Windows debugger | GPL-3.0 | Active |
| BizHawk | Emulator with RAM search and Lua | MIT (mixed for cores) | Active |
| Dolphin Memory Engine | GameCube / Wii RAM search | MIT | Active |

Using a GPL tool is fine; copying its code into the project makes that part GPL. Output of these tools (dumps,
extracted assets, decompiled code) is game material and never enters the repository.

## Boundaries

Own copy, offline or own server, no anti-cheat interaction, no DRM bypass, nothing from the game redistributed.
If finding something requires crossing one of these lines, stop and tell the user why.
