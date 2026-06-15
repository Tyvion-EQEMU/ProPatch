# Getting Started with ProPatch

ProPatch is a single `.exe` — no installer, no Python, no dependencies. Download it, run it, and the Setup Wizard takes you through everything.

---

## 1. Download

Go to the [Releases page](https://github.com/Tyvion-EQEMU/ProPatch/releases) and download the latest `ProPatch.exe`. Put it anywhere — the Setup Wizard will move it to a permanent home.

---

## 2. First Run — Setup Wizard

When ProPatch launches for the first time, the Setup Wizard opens automatically. It has five sections:

### ProPatch Install Path
Where ProPatch will live on your machine. This is also where all settings files and logs are kept. The default (`C:\Games\ProPatch`) works for most people.

### GitHub Token *(optional - useful if you are a dev/tester)*
Without a token, GitHub limits API requests to 60/hour — enough for normal use, but you may hit it if you rescan frequently. A token raises the limit to 5,000/hour.  This option will eventually be hidden with v1 release.

To get a token:
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Give it any name (e.g., "ProPatch")
4. **No scopes needed** — leave all checkboxes unchecked
5. Click **Generate token** and paste it into ProPatch

### Desktop Shortcut
Creates a shortcut on your Windows Desktop so you can open ProPatch without hunting for the exe.

### MacroQuest
Toggle MQ management on or off. If you don't use MacroQuest, flip the toggle off and ProPatch will ignore all MQ components entirely.

If MQ is enabled, set **MQ Install Path** to the root of your MQ installation — the folder that contains `MacroQuest.exe`. Default is `C:\Games\MQ-Profusion`.

> **Note:** ProPatch leverages Rekkas' MQ build. If you use RedGuides' Very Vanilla (redfetch), or any other MQ compile, make sure you're pointing at a *different* folder else ProPatch will overwrite it.

### EQ Install Path
The root of your EverQuest EMU installation — the folder that contains `eqgame.exe`. This is needed so ProPatch can drop in updated EMU specific server files (spells, DB strings, etc.).  This is NOT your LIVE EQ instance, if you play on LIVE too.

If you run multiple EQ instances for ProFusion (e.g., separate installs for tanks and boxes), use **+ Add EQ Instance** to add each one. ProPatch will update server files in all of them.

---

## 3. Finish Setup

Click **Finish Setup**. ProPatch saves your config and switches to the main panel.

---

## 4. Normal Workflow

1. Open ProPatch.
2. It auto-scans on launch — the **Status** column updates within a few seconds.
3. If anything shows **Update Available**, click **Update**.
4. When all components show **Up to Date**, you're done.
5. Use the **▶** button on the MQ row to launch MacroQuest directly from ProPatch.

---

## Changing Settings Later

Click **Re-run Setup** in the action bar at any time to revisit any of the wizard settings. Your existing config is pre-filled so you only need to change what's different.
