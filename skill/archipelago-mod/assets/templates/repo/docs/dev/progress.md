# Progress

Resumable state of the integration. Update it at the end of every step; a new session starts by reading it.

## Game

- Name: __GAME_NAME__
- Store and build: <!-- e.g. Steam build 12345678 -->
- Executable SHA-256: <!-- from detect_engine.py -->
- Engine and route: <!-- e.g. Unity Mono 2021.3, BepInEx 5 + ArchipelagoBridge -->
- Online features or anti-cheat: <!-- none / what was disabled -->

## Steps

Numbered as in the archipelago-mod skill, so a session can resume at the first unchecked step.

- [ ] 0. Interview: game, platform, install, online features, checks, items and goal
- [ ] 1. Prior art searched (results below)
- [ ] 2. Engine identified and route chosen
- [x] 3. Repository scaffolded
- [ ] 4. Proof of concept: one location detected, one item granted, one server round trip
- [ ] 5. Game map: locations, items, goal and logic gates proven in game-map.md
- [ ] 6. APWorld generates with the real map, tests and checks green
- [ ] 7. Client complete: reconnection, offline resync, save binding, no double grants, goal, DeathLink
- [ ] 8. End-to-end seed played locally from start to goal, adversarial review done, findings fixed
- [ ] 9. Released and tagged

## Prior art

<!-- Every place searched, with links, and the conclusion. -->

## Decisions

<!-- Date: decision, and why. -->

## Open questions

<!-- What only the user can answer, or what is still unproven. -->
