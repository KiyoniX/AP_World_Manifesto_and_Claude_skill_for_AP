# __GAME_NAME__ Archipelago

An [Archipelago](https://archipelago.gg) multiworld integration for __GAME_NAME__: the apworld that generates seeds,
and the client that connects the game to the multiworld server.

This project contains only original code. It ships no game files: you need your own legally obtained copy.

## Install

Download the latest release, then follow [the setup guide](apworld/__MODULE__/docs/setup_en.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `apworld/__MODULE__/` | The world package built into `__MODULE__.apworld` |
| `client/` | The in-game client |
| `docs/dev/` | Development notes: progress and the proven game map |
| `tools/` | Project checks run by CI |

## Development

Archipelago is never forked or copied here. Clone the official repository next to this one at the release CI pins
(`ARCHIPELAGO_REF` in `.github/workflows/ci.yml`), then link the world into it:

```sh
git clone --branch __AP_VERSION__ https://github.com/ArchipelagoMW/Archipelago ../Archipelago
# Windows (administrator or developer mode): mklink /D ..\Archipelago\worlds\__MODULE__ <this repo>\apworld\__MODULE__
ln -s "$(pwd)/apworld/__MODULE__" ../Archipelago/worlds/__MODULE__
cd ../Archipelago && python ModuleUpdate.py --yes --append "WebHostLib/requirements.txt"
AP_TEST_WORLDS=__MODULE__ python -m pytest
```

## Releasing

1. Bump `world_version` in `apworld/__MODULE__/archipelago.json`.
2. Tag the commit `v<world_version>` and push the tag: CI tests, builds and publishes the `.apworld`.
3. Attach the client build to that release with `gh release upload v<world_version> <file>`.
