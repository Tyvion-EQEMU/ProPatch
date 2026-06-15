# Managed Components

ProPatch tracks and updates the following components. Each one can be individually enabled/disabled in the GUI or in `settings.local.toml`.

---

## ProPatch Patcher

| | |
|---|---|
| **ID** | `propatch` |
| **Source** | [Tyvion-EQEMU/ProPatch](https://github.com/Tyvion-EQEMU/ProPatch) |
| **Tracking** | GitHub release tag |
| **Installs to** | Replaces itself (self-update) |

ProPatch tracks its own releases. When a newer version is available, it downloads the new `.exe`, waits for the current process to exit, swaps the file, and relaunches automatically. You don't need to do anything — just click Update.

---

## MQ Install (Rekkas)

| | |
|---|---|
| **ID** | `rekkas_mq` |
| **Source** | [RekkasGit/E3NextAndMQNextBinary](https://github.com/RekkasGit/E3NextAndMQNextBinary) |
| **Tracking** | GitHub release tag |
| **Installs to** | MQ root (`C:\Games\MQ-Profusion\` by default) |

The core MacroQuest binary built for EQProfusion by Rekkas. Includes E3Next and MQNext. ProPatch extracts the release zip into your MQ root directory.

**Protected files** — ProPatch will never overwrite:
- `config/*` — all files inside the config folder
- `MacroQuest.ini` — your MQ configuration

> **Important:** If you have an existing MQ install directory, it would be recommended to rename or put this new install in a new directory to test.  You can easily copy your config across this way without potentially disrupting your existing install directory.

---

## MQ2RWarp

| | |
|---|---|
| **ID** | `mq2rwarp` |
| **Source** | [Tyvion-EQEMU/MQ2RWarp](https://github.com/Tyvion-EQEMU/MQ2RWarp) |
| **Tracking** | GitHub release tag |
| **Installs to** | `plugins\MQ2RWarp.dll` inside your MQ root |

A MQ plugin that provides Warp functionality for EQ Profusion. ProPatch downloads `MQ2RWarp.dll` from the release and drops it into the `plugins/` subfolder of your MQ installation.

This repo is forked from [TheDroidYourLookingFor/MQ2RWarp](https://github.com/TheDroidYourLookingFor/MQ2RWarp)

Please review Enine's rules and stance on Warp in the Profusion Discord.

---

## RGMercs

| | |
|---|---|
| **ID** | `rgmercs` |
| **Source** | [DerpleDude/rgmercs](https://github.com/DerpleDude/rgmercs) |
| **Tracking** | GitHub release tag |
| **Installs to** | `lua\rgmercs\` inside your MQ root |

RGMercs is a lua-based automation system for MacroQuest. ProPatch downloads and extracts `rgmercs.zip` from the release into `lua/rgmercs/` inside your MQ directory.

---

## ProLoot

| | |
|---|---|
| **ID** | `proloot` |
| **Source** | [Tyvion-EQEMU/proLoot](https://github.com/Tyvion-EQEMU/proLoot) |
| **Tracking** | GitHub release tag |
| **Installs to** | `lua\proloot\` inside your MQ root |

ProLoot is a lua-based loot automation script built from the e9loot2.mac provided in Discord for Profusion players. ProPatch downloads the release zip and extracts it into `lua/proloot/` inside your MQ directory.

---

## EQ Server Files

These are EverQuest data files specific to and provided directly by the Profusion game server. ProPatch downloads them from the game server live and places them into all of your Profusion EQ directories that you configured during the Setup Wizard.

| Component | File | Location |
|---|---|---|
| `spells_us` | `spells_us.txt` | EQ root |
| `dbstr_us` | `dbstr_us.txt` | EQ root |
| `skillcaps` | `SkillCaps.txt` | `Resources/` |
| `basedata` | `BaseData.txt` | `Resources/` |
| `dinput8` | `dinput8.dll` | EQ root |

ProPatch tracks these by content hash — it only re-downloads a file if its content has actually changed on the server. If you run multiple EQ instances (e.g., separate folders for tanks and bots), ProPatch updates each one.

---

## Disabling a Component

Any component can be disabled individually. Disabled components are skipped during scans and updates.

**In the GUI:** Uncheck the checkbox next to the component name in the main panel.

**In `settings.local.toml`:**
```toml
[components]
proloot = false
rgmercs = false
```

See [Configuration](configuration.md) for details.
