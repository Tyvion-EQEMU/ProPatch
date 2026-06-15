# ProFetch Roadmap

This document tracks planned features, improvements, and longer-term ideas for ProFetch. It's a living document — priorities shift as the community grows and feedback comes in.

---

## Near-Term (Next 1–2 Releases)

### Custom Components
The UI already has a hidden "+ Add custom component" button. The plan is to let users register their own GitHub repos (or local paths) so ProFetch can track and update them alongside the built-in components.


---

## Medium-Term

### Tray Icon Mode
Run ProFetch minimized to the system tray. It quietly checks for updates in the background and shows a badge when something needs attention — similar to how a lot of launcher tools work.

### Rollback Support
Track the last N installed versions in the local database so you can roll back a component to a previous release if something breaks.

### Multiple MQ Instances
Support for users who run more than one MQ installation (e.g., a separate profile for tanks vs. bots). Each instance would have its own path and can be updated independently.

---

## Longer-Term / Ideas

### Plugin Health Check
Detect common MQ configuration problems (missing `MacroQuest.ini` fields, wrong EQ path set inside MQ, etc.) and surface them as warnings in the GUI.

### MQ Config Options

Autoloads popular aliases, the NavMesh Updater utility, optional settings templates like AutoGroup, AutoAccept, AutoRez and common commands via Buttonmaster for server specific functions like navigating to your DZ, etc.

---

## Recently Shipped

| Version | Feature |
|---|---|
| v0.5.0 | Initial public release — GUI + CLI, self-update, Setup Wizard |
| v0.5.0 | Desktop shortcut creation option in Setup Wizard |
| v0.5.0 | GitHub token field in Setup Wizard |
| v0.5.6 | Self-update relaunch fix (Shell.Application.ShellExecute) |
| v0.5.6 | Launch MQ button (▶) on MQ component row |
| v0.5.6 | "Last checked" timestamp in header |
| v0.5.6 | ProFetch-first update behavior (restarts before updating other components) |
| v0.5.6 | Self-update breadcrumb logging |
| v0.5.6 | GitHub ReadMe, Roadmap and Documentation |
