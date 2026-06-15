# CLI Reference

ProFetch includes a command-line interface for power users, scripting, or headless environments. Running `profetch` with no arguments opens the GUI. Any subcommand skips the GUI entirely.

---

## Commands

### `profetch status`

Shows installed vs. remote versions for all enabled components, plus your current path configuration.

```
profetch status
```

**Example output:**
```
  ProFetch         v0.5.6     current
  MQ Install       v3.1.0     current
  MQ2RWarp         v1.2.0     update available  →  v1.3.0
  RGMercs          v2.4.1     current
  ProLoot          —          not installed
  spells_us        current
  dbstr_us         current
```

---

### `profetch update`

Updates all enabled components that are out of date. Shows a pre-flight summary and asks for confirmation before downloading anything.

```
profetch update
```

To update a **single component**, pass its name or alias:

```
profetch update rekkas      # MQ binary
profetch update mq2rwarp    # or: rwarp
profetch update rgmercs     # or: mercs
profetch update proloot     # or: loot, e9loot
```

**Component aliases:**

| Alias(es) | Component |
|---|---|
| `rekkas`, `rekkas_mq` | MQ Install (Rekkas) |
| `mq2rwarp`, `rwarp` | MQ2RWarp |
| `rgmercs`, `mercs` | RGMercs |
| `proloot`, `loot`, `e9loot` | ProLoot |

---

### `profetch update-eq`

Updates EQ server-specific files only (`spells_us.txt`, `dbstr_us.txt`, etc.) across all configured EQ directories. Useful if you only want to sync server files without touching MQ.

```
profetch update-eq
```

Requires at least one `eq_dirs` entry in `settings.local.toml`. See [Configuration](configuration.md).

---

### `profetch version`

Prints the running ProFetch version.

```
profetch version
# → ProFetch v0.5.6
```

---

### `profetch setup`

Re-runs path configuration (CLI version). Prompts for your MQ install path and EQ directories, then writes `settings.local.toml`. Equivalent to **Re-run Setup** in the GUI, but text-based.

```
profetch setup
```

---

## Global Behavior

- **No args** → launches the GUI
- **GitHub token** — if configured, used automatically for all API calls. See [Configuration](configuration.md).
- **Disabled components** — components set to `false` in `[components]` are skipped in `update` and `status`
- **Logs** — all CLI runs write to `profetch.log` in the data directory alongside the exe

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Error (bad component name, network failure, etc.) |
