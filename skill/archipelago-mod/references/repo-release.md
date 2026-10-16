# Repository and release

## Layout

`scripts/new_project.py` creates it:

```
<repo>/
  apworld/<module>/        the world package (built into <module>.apworld)
  client/                  the in-game client (C# solution, Lua mod, plugin...) when it is not inside the apworld
  docs/dev/progress.md     resumable state of the work
  docs/dev/game-map.md     every location, item, gate and hook, with its proof
  tools/check_apworld.py   static checks, run by CI
  .github/workflows/       ci.yml (tests + build on every push), release.yml (publish on tag)
  README.md  .gitignore
```

One project, one repository: never split the world and its client, never put two games in one repository.

## Archipelago is a neighbour, not a fork

Do not fork or vendor ArchipelagoMW/Archipelago. Locally, clone the official repository beside the project at the
version the world targets and symlink the world into its `worlds/` folder (`references/apworld.md`). In CI, the
workflow checks out the official repository at the pinned release (`ARCHIPELAGO_REF`) and copies the world in.
Bumping `ARCHIPELAGO_REF` is a deliberate change, tested like any other.

A fork is only justified for a change to Archipelago core itself; it is then short-lived and proposed upstream.

## Never committed

- Anything from the game: binaries, assets, extracted or decompiled code, dumps, ROMs, saves, generated SDKs
  (Il2CppDumper, UE4SS dumps). Reference them at build time from the local install (`local.props`, environment
  variables), which stays git-ignored.
- Build outputs: `.apworld`, `.dll`, `bin/`, `obj/`, `build/`, archives.
- Machine-specific configuration.

`.gitignore` from the template covers the usual cases; check `git status` before every commit.

## Versioning

- `world_version` in `archipelago.json` follows semantic versioning: a change of an item or location ID, or of slot
  data shape, is a major bump; new content is minor; fixes are patch.
- The client and the world are released together under the same version, so a player never mixes incompatible
  halves. The client should check the world version it receives (put it in slot data) and warn on mismatch.

## Releasing

1. Update `world_version` and the changelog section of the release notes.
2. Commit, then tag that commit `v<world_version>` (annotated tag: `git tag -a v1.2.0 -m "v1.2.0"`).
3. Ask the user before pushing: `git push origin main v1.2.0`. The release workflow refuses a tag that differs from
   `world_version`, reruns CI, builds the `.apworld` and creates the GitHub release with it attached.
4. Build the client locally (it needs the game's files, which CI never has) and attach each file in its native form:
   `gh release upload v1.2.0 client/.../MyGameArchipelago.dll client/.../ArchipelagoBridge.dll ...`.
   Never wrap assets in a `.zip`. If a distribution channel requires an archive (e.g. Thunderstore), that is a
   separate channel the user decides on, not the GitHub release.

## Licence

Ask the user which licence to use before the first public push (MIT is the norm in the Archipelago ecosystem and
matches Archipelago itself). Copy code from other integrations only when their licence allows it and credit them;
a repository without a licence file is read-only inspiration.
