# GUI Reference

ProPatch opens to the **Components View** after first-time setup. Here's what everything does.

---

## Header

The top of the window shows the ProPatch banner and a **Last checked** timestamp in the top-right corner. The timestamp updates after every scan or update run.

---

## Component List

The main panel shows all managed components grouped into three sections:

| Section | Components |
|---|---|
| **ProPatch Patcher** | ProPatch itself |
| **MQ Components** | MQ Install, MQ2RWarp, RGMercs, ProLoot |
| **Server Components** | spells_us, dbstr_us, SkillCaps, BaseData, dinput8 |

### Columns

| Column | Description |
|---|---|
| **Checkbox** | Select/deselect this component for Update and Rescan operations |
| **Name** | Component display name |
| **▶** | (MQ row only) Launch `MacroQuest.exe` from your configured MQ path |
| **Installed** | Version currently on disk, as tracked in ProPatch's local database |
| **Remote** | Latest version available on GitHub |
| **Status** | Current state (see below) |

---

## Action Bar

Buttons at the bottom of the window:

| Button | What it does |
|---|---|
| **Update** | Downloads and installs updates for all checked components that have a newer remote version |
| **Rescan** | Re-checks all checked components against GitHub without installing anything |
| **Re-run Setup** | Opens the Setup Wizard so you can change paths, token, or MQ settings |
| **Log** | Switches to the Log view (tails `ProPatch.log`) |
| **Exit** | Closes ProPatch |

---

## Launch MQ Button (▶)

The green play button on the MQ Install row launches `MacroQuest.exe` from your configured MQ path. It's always clickable — you don't have to wait for an update to finish or have MQ checked in the list. Click it whenever you're ready to start playing.

If `MacroQuest.exe` is not found at the configured path, ProPatch logs a warning but does nothing else.

---

## Log View

Click **Log** to tail `ProPatch.log` in real time. Every scan and update is logged here with component names, version transitions, and GitHub URLs. Useful for diagnosing errors or confirming what changed.

Click **Back** to return to the component list.

---

## Setup Wizard

Accessible via **Re-run Setup**. See [getting-started.md](getting-started.md) for a full walkthrough of each section.
