# Native games without mod support

Check first that the game has no anti-cheat and no online mode that could be affected. If it has, stop: propose
Manual for Archipelago instead.

## Route A: external memory client (Python)

A program beside the game reads and writes its memory. The protocol comes for free from Archipelago's
`CommonClient` (subclass `CommonContext`, add a watcher task).

- Memory access: `pymem` (MIT; Archipelago core already depends on it for legacy worlds) or `ctypes` with
  `ReadProcessMemory` / `WriteProcessMemory`.
- Addresses are `module base + offset` or pointer chains from a module base (ASLR moves the base each launch).
  Re-resolve pointer chains on every read: objects move on level loads.
- Identify the game build by hashing the executable before touching memory; refuse unknown builds with a clear
  message.
- Writing items into memory is fragile: prefer writing a value the game itself consumes (an inventory count, a
  pending-reward slot) and check it was taken.
- Reference: Kingdom Hearts II's client in the Archipelago repository (`worlds/kh2/ClientStuff/Client.py`); note it
  needs administrator rights and antivirus software may flag memory clients.

## Route B: DLL inside the game process

A proxy DLL (`dinput8.dll`, `version.dll`, `winmm.dll`) loaded by the game installs function hooks and runs the
client in process. Robust and fast, more work.

- Rust: `archipelago_rs` (MIT) + `ilhook` for x64 hooks + `hudhook` for an overlay. Reference, with the item counter
  stored in the save: https://github.com/fswap/from-software-archipelago-clients (MIT, Dark Souls III and Sekiro).
- C++: `apclientpp` + a hooking library such as MinHook (check its licence). Reference: the older DS3 client
  https://github.com/Marechal-L/Dark-Souls-III-Archipelago-client (MIT).

## Finding what to hook

See `reverse.md`: Cheat Engine to find values and the code that writes them, Ghidra to understand that code, x64dbg
to confirm it live. Hook the function that grants a reward or sets a flag, not the value itself, when you can.
