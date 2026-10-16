# The APWorld

Facts below were read from Archipelago `main` (October 2026, release 0.6.8). Re-check the official docs when the
version changes: https://github.com/ArchipelagoMW/Archipelago/tree/main/docs.

## Contents

- Official sources to read
- The template's shape
- Items, locations, regions, rules
- Options and slot data
- Local development loop
- Packaging
- Common fill problems

## Official sources to read

| Source | Why |
| --- | --- |
| `worlds/apquest/` | The official teaching world: every step commented, read in the order `world.py` gives |
| `docs/apworld_dev_faq.md` | Recommended order of work, fill errors, item/location counts |
| `docs/world api.md` | Full generation API and the order of generation steps |
| `docs/rule builder.md` | The rule API the template uses (`Has`, `HasAll`, `&`, `|`, `OptionFilter`) |
| `docs/options api.md` | Option types, groups, presets |
| `docs/apworld specification.md` | `.apworld` format and `archipelago.json` |
| `docs/tests.md` | `WorldTestBase` and how tests are discovered |
| `docs/adding games.md` | Hard requirements for a world and a client |
| `docs/style.md` | Code style |

## The template's shape

```
apworld/<module>/
  archipelago.json   game, minimum_ap_version, world_version, authors (never version/compatible_version)
  __init__.py        imports the World class (and the BizHawk client, if any, so it registers)
  data.py            the game map: ITEMS, LOCATIONS, REGIONS, ENTRANCES, GOAL_REGION, FILLER_ITEM
  world.py           generic: builds regions, locations, items and rules from data.py
  options.py         player options (DeathLink by default)
  web_world.py       tutorial metadata for the website
  docs/              en_<Game>.md (game page) and setup_en.md (setup guide), both required
  test/              bases.py, logic tests, self-contained generation test
```

`world.py` should rarely change: new content goes into `data.py`. Extend `world.py` only for behaviour driven by
options (e.g. a location that only exists with an option on), and keep that logic data-driven too
(e.g. an `option` field on `LocationData` checked in `create_regions`).

## Items, locations, regions, rules

- **IDs**: unique integers per game in `[1, 2**31 - 1]`; items and locations have separate namespaces. Every item and
  location that can ever exist must be in `item_name_to_id` / `location_name_to_id`, even if an option removes it.
  Names must not be numeric. Event locations and items have ID `None` and exist only during generation.
- **Classification**: `progression` (needed by any rule: mandatory if a rule mentions it), `useful`, `filler`,
  `trap`, plus combinations (`progression | useful`, `progression_skip_balancing`...).
- **Counts**: the pool must contain exactly one item per unfilled location. The template computes the free slots and
  fills them with `create_filler()`; `get_filler_item_name()` must return an infinitely repeatable item.
- **Regions**: the origin region (default `"Menu"`) is always reachable. Rules go on entrances and locations, not on
  regions. `create_entrance` skips an entrance whose rule is always false.
- **Rules**: rule-builder objects (`Has("Key")`, `HasAll("Sword", "Shield")`, `Has("Sword", count=2)`,
  `CanReachRegion(...)`), combined with `&` and `|`, never `and`/`or`. They are serializable and give readable logic
  explanations. If an entrance rule depends on reaching another region, Archipelago needs an indirect condition: the
  rule builder registers it for you.
- **Goal**: the template puts a `Victory` event in `GOAL_REGION` and sets the completion rule to `Has("Victory")`.
  The client reports the goal with `StatusUpdate` status 30 (`CLIENT_GOAL`).
- **Starting items**: `push_precollected`. **Early items**: `multiworld.local_early_items[player][name] = 1`.

## Options and slot data

- One class per option with a docstring (shown to players) and `display_name`, collected in the options dataclass.
  Offer only options the user wants and the client actually honours.
- Static game data shipped as files inside the world is read with `pkgutil.get_data(__name__, "data/file.json")`,
  which also works when the world is zipped. Never `open()` a path, never read another package.
- `fill_slot_data` returns what the client needs to adapt the game to the seed (options, randomized layout). Keep it
  small, JSON-serializable, and versioned if its shape may change.
- Randomization that the YAML and items alone do not determine (entrance order, starting area) must be in slot data,
  so trackers such as Universal Tracker can rebuild the logic (`interpret_slot_data`).

## Local development loop

Never fork Archipelago. Clone it beside the project and link the world into its `worlds/` folder:

```sh
git clone --branch <ap-version> https://github.com/ArchipelagoMW/Archipelago ../Archipelago
ln -s "$(pwd)/apworld/<module>" ../Archipelago/worlds/<module>     # Windows: mklink /D (developer mode)
cd ../Archipelago
python ModuleUpdate.py --yes --append "WebHostLib/requirements.txt"   # Python 3.11.9 to 3.13 on Windows
python Launcher.py --update_settings            # creates host.yaml
AP_TEST_WORLDS=<module> python -m pytest        # the world's tests plus Archipelago's generic tests
```

Generate and host a seed:

```sh
python Launcher.py "Generate Template Options"  # writes Players/Templates/<Game>.yaml
# copy it to Players/, set name and options
python Generate.py                              # output/AP_<seed>.zip
python MultiServer.py output/AP_<seed>.zip      # or the Launcher's "Host"; default port 38281
```

The Launcher's "Text Client" connects to a slot without the game: useful to send `!getitem` style admin commands,
watch messages, or test the server side before the game client exists.

## Packaging

`python Launcher.py "Build APWorlds" -- "<Game Name>" --skip_open_folder` writes `build/apworlds/<module>.apworld`
and adds `version` and `compatible_version` to the manifest. The CI template does this on every push and attaches the
file to tagged releases. `.apignore` in the world folder excludes files (gitignore syntax).

## Common fill problems

- *Restrictive start* (few sphere-1 locations): add early items, more sphere-1 locations, or starting inventory.
- *More items than locations*: count `get_unfilled_locations`, never hardcode; options that add items must add
  locations or replace filler.
- *Rule mentions a non-progression item*: classify it progression.
- *Unreachable locations with all items* (the generic test catches it): a typo in a region name or a missing
  entrance; the data-driven template fails fast on unknown region names.
