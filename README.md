# AP World Manifesto and Claude skill for AP

Two independent ways to build an [Archipelago](https://archipelago.gg) integration (the APWorld that generates seeds,
plus the client that connects the game) that players can trust and maintainers can keep alive:

| | For | What it is |
| --- | --- | --- |
| [`manifesto/`](manifesto/AP_World_Manifesto.md) | People, with or without AI | A detailed guide: principles, finding the game loop, checks and items, building and testing the world and the client, releasing. Each release attaches it as PDF, DOCX and Markdown. |
| [`skill/archipelago-mod/`](skill/archipelago-mod/SKILL.md) | AI agents that read Claude-style skills | A step-by-step skill with tested templates (data-driven APWorld, sandboxed generation test, C# and BizHawk clients, CI) and helper scripts. |

Both follow the same rules: readable, reusable code; generation that reads no outside file, needs no extra
dependency and makes no network call; no fork of Archipelago; one project per repository; tagged releases with
unzipped assets; nothing from the game ever published.

## Using the skill

Copy or link `skill/archipelago-mod/` into your agent's skills folder, for Claude Code `~/.claude/skills/`:

```sh
git clone <this repository> AP_World_Manifesto_and_Claude_skill_for_AP
ln -s "$(pwd)/AP_World_Manifesto_and_Claude_skill_for_AP/skill/archipelago-mod" ~/.claude/skills/archipelago-mod
# Windows: mklink /J %USERPROFILE%\.claude\skills\archipelago-mod <clone>\skill\archipelago-mod
```

Then ask the agent something like "help me make an Archipelago randomizer for <game>".

## Development

| Task | Command |
| --- | --- |
| Test the skill's scripts | `python skill/archipelago-mod/scripts/test_scripts.py` |
| Build the manifesto (needs pandoc 3 and typst) | `python tools/build_manifesto.py` |
| Verify the templates end to end | see the `templates` job in `.github/workflows/ci.yml` |

Releases are tagged `vX.Y.Z`; pushing a tag builds the manifesto and attaches the PDF, DOCX and Markdown files to the
GitHub release.
