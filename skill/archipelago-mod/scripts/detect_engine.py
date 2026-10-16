"""Guess a game's engine from its install folder, with the evidence for each guess.

Usage: python detect_engine.py <game folder or ROM file>

Reads only file names and a few header bytes; never modifies anything. Signatures marked "unverified" come from
general knowledge and were not confirmed against a primary source: treat a match on them as a lead, not a fact.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

ROM_EXTENSIONS = {
    ".nes", ".sfc", ".smc", ".gb", ".gbc", ".gba", ".nds", ".3ds", ".cia", ".n64", ".z64", ".v64",
    ".iso", ".gcm", ".wbfs", ".rvz", ".cue", ".chd", ".pbp", ".cso", ".md", ".gen", ".sms", ".pce",
}
UNITY_VERSION = re.compile(rb"20\d\d\.\d+\.\d+[abfp]\d+|[56]\.\d\.\d+[abfp]\d+|6000\.\d+\.\d+[abfp]\d+")
GODOT_MAGIC = b"GDPC"


@dataclass(frozen=True)
class Finding:
    engine: str
    evidence: str
    verified: bool


def files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def read_head(path: Path, size: int) -> bytes:
    with path.open("rb") as stream:
        return stream.read(size)


def read_tail(path: Path, size: int) -> bytes:
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - size))
        return stream.read(size)


def unity_version(root: Path) -> str | None:
    for manager in files(root, "*_Data/globalgamemanagers") + files(root, "*_Data/data.unity3d"):
        match = UNITY_VERSION.search(read_head(manager, 4096))
        if match:
            return match.group().decode()
    return None


def detect_unity(root: Path) -> Iterator[Finding]:
    il2cpp = files(root, "GameAssembly.dll") + files(root, "*_Data/il2cpp_data")
    mono = files(root, "*_Data/Managed/Assembly-CSharp.dll")
    version = unity_version(root)
    suffix = f", Unity {version} (from globalgamemanagers header)" if version else ""
    if il2cpp:
        yield Finding("Unity IL2CPP", f"{il2cpp[0].name} present{suffix}", True)
    elif mono:
        data_dir = mono[0].parent.parent.name
        yield Finding("Unity Mono", f"{data_dir}/Managed/Assembly-CSharp.dll, no GameAssembly.dll{suffix}", True)
    elif files(root, "UnityPlayer.dll"):
        yield Finding("Unity (scripting backend unknown)", f"UnityPlayer.dll present{suffix}", True)


def detect_unreal(root: Path) -> Iterator[Finding]:
    paks = files(root, "*/Content/Paks/*.pak")
    if not paks:
        return
    io_store = " with IoStore (.utoc/.ucas): UE 4.26 or later" if files(root, "*/Content/Paks/*.utoc") else ""
    exe = files(root, "*/Binaries/Win64/*.exe")
    where = f", game executable {exe[0].relative_to(root)}" if exe else ""
    yield Finding("Unreal Engine", f"{paks[0].relative_to(root)}{io_store}{where}", True)


def detect_godot(root: Path) -> Iterator[Finding]:
    for pck in files(root, "*.pck"):
        if read_head(pck, 4) == GODOT_MAGIC:
            yield Finding("Godot", f"{pck.name} starts with GDPC", True)
            return
    for exe in files(root, "*.exe"):
        if GODOT_MAGIC in read_tail(exe, 12):
            yield Finding("Godot", f"pack embedded at the end of {exe.name}", True)
            return


def detect_gamemaker(root: Path) -> Iterator[Finding]:
    for name in ("data.win", "game.unx", "game.ios", "game.droid"):
        for data in files(root, name):
            head = read_head(data, 12)
            if head[:4] == b"FORM" and head[8:12] == b"GEN8":
                yield Finding("GameMaker (VM bytecode)", f"{name} has FORM/GEN8 header", True)
                return
            yield Finding("GameMaker (YYC: code compiled into the exe)", f"{name} without bytecode header", False)
            return


def detect_rpg_maker(root: Path) -> Iterator[Finding]:
    if files(root, "js/rpg_core.js") or files(root, "www/js/rpg_core.js"):
        yield Finding("RPG Maker MV (NW.js)", "js/rpg_core.js present", True)
    elif files(root, "js/rmmz_core.js"):
        yield Finding("RPG Maker MZ (NW.js)", "js/rmmz_core.js present", False)


def detect_renpy(root: Path) -> Iterator[Finding]:
    scripts = files(root, "game/*.rpa") + files(root, "game/*.rpyc")
    if scripts:
        yield Finding("Ren'Py", f"game/{scripts[0].name}", True)


def detect_source(root: Path) -> Iterator[Finding]:
    info = files(root, "*/gameinfo.txt")
    if info:
        yield Finding("Source engine", f"{info[0].relative_to(root)}", True)


def detect_dotnet(root: Path) -> Iterator[Finding]:
    for dll, engine, verified in (
        ("FNA.dll", "FNA (.NET)", True),
        ("MonoGame.Framework.dll", "MonoGame (.NET)", False),
        ("Microsoft.Xna.Framework*.dll", "XNA (.NET Framework)", False),
    ):
        found = files(root, dll)
        if found:
            yield Finding(engine, f"{found[0].name} present", verified)
            return


def detect_other(root: Path) -> Iterator[Finding]:
    if files(root, "*.jar") or files(root, "jre") or files(root, "runtime/bin/java*"):
        yield Finding("Java", "jar or bundled Java runtime present", False)
    if files(root, "love.dll"):
        yield Finding("LOVE (Lua)", "love.dll present", False)


DETECTORS: tuple[Callable[[Path], Iterator[Finding]], ...] = (
    detect_unity, detect_unreal, detect_godot, detect_gamemaker, detect_rpg_maker,
    detect_renpy, detect_source, detect_dotnet, detect_other,
)


def detect(target: Path) -> list[Finding]:
    if target.is_file():
        if target.suffix.lower() in ROM_EXTENSIONS:
            return [Finding("ROM or disc image", f"{target.suffix} file: emulator route", True)]
        target = target.parent
    return [finding for detector in DETECTORS for finding in detector(target)]


def executables(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return files(root, "*.exe") + files(root, "*/Binaries/Win64/*.exe")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    target = Path(argv[1])
    if not target.exists():
        print(f"Not found: {target}", file=sys.stderr)
        return 2

    findings = detect(target)
    if not findings:
        print("No known engine signature: native or custom engine. Route: references/engine-native.md")
    for finding in findings:
        status = "verified signature" if finding.verified else "unverified signature"
        print(f"{finding.engine}: {finding.evidence} [{status}]")

    for exe in executables(target):
        print(f"sha256 {sha256(exe)}  {exe.relative_to(target.parent if target.is_file() else target)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
