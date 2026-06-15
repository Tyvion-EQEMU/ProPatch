# ProPatch — EQProfusion Component Manager

ProPatch is a simple Windows patcher for the **E9 Profusion** EverQuest EMU server. It manages all your Profusion specific EQ files, MacroQuest install, and lua scripts in sync with their GitHub releases — all from a single console.

None of the components automatically included with this patcher are required.  You can opt-out of any of the components and in a future release I will give you the option to put in your own if there is something you'd like to be patched automatically.  All you'll need to provide is its github repo.

---

## What ProPatch Manages

| Component | Description |
|---|---|
| **ProPatch** | The patcher itself — self-updating |
| **MQ Install (Rekkas)** | Rekkas' E3Next + MQNext binary |
| **MQ2RWarp** | RWarp plugin (`plugins/MQ2RWarp.dll`) |
| **RGMercs** | RGMercs lua automation (`lua/rgmercs/`) |
| **ProLoot** | ProLoot (e9loot) lua (`lua/proloot/`) |
| **EQ Server Files** | `spells_us.txt`, `dbstr_us.txt`, `SkillCaps.txt`, `BaseData.txt`, `dinput8.dll` |

---

## Getting Started

1. **Download** `ProPatch.exe` from the [Releases](https://github.com/Tyvion-EQEMU/ProPatch/releases) page.
2. **Run it** The Setup Wizard opens on first launch and walks you through:
   - Where to keep ProPatch (and its settings/logs)
   - Whether you want MacroQuest, or not
   - Where your MQ installation lives
   - Where your EverQuest installation(s) live
3. **Opt-Out** All of the components built-in are optional, simply uncheck anything you do not want.  If you use E3, uncheck RGMercs as an example.
4. **Hit Update** ProPatch checks every component and downloads anything that's out of date.

> See **[docs/getting-started.md](docs/getting-started.md)** for a full walkthrough with screenshots.

---

## Documentation

| Guide | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | First-run setup and typical workflow |
| [GUI Reference](docs/gui.md) | Every panel, button, and column explained |
| [CLI Reference](docs/cli.md) | Command-line usage for power users |
| [Components](docs/components.md) | What each managed component is and where it installs |
| [Configuration](docs/configuration.md) | Settings files, paths, GitHub token, disabling components |

---

## Quick Notes

- **GitHub token** — optional. GitHub limits you to 60 API requests/hour. Adding a token raises that to 5,000. ProPatch will allow for one during setup, or you can add it to `settings.local.toml` later. See [Configuration](docs/configuration.md).
- **MQ is optional** — if you don't use MacroQuest, toggle it off in the Setup Wizard and ProPatch will ignore all MQ components.
- **Your config is never overwritten** — `settings.local.toml` and `gui_settings.json` are yours. ProPatch only touches its own defaults file.
- **Self-updating** — when a new ProPatch release is available, it downloads the new `.exe`, swaps it in, and relaunches automatically.

---

## CLI

ProPatch also ships a command-line interface for scripting or headless use:

```
ProPatch status          # show installed vs. remote versions
ProPatch update          # update everything
ProPatch update rekkas   # update MQ, bundled with Mono/E3
ProPatch update-eq       # update EQ server files only
ProPatch version         # show ProPatch version
ProPatch setup           # reconfigure paths
```

See [docs/cli.md](docs/cli.md) for the full reference.

---

## Support & Community

- **EQ Profusion Discord** — best place for help and discussion
- **Issues** — bug reports and feature requests: [github.com/Tyvion-EQEMU/ProPatch/issues](https://github.com/Tyvion-EQEMU/ProPatch/issues)
