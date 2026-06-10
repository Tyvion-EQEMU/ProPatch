# proFetch

EQProfusion component patcher and updater for MQ-Rekka.

Keeps Rekkas' MQ binary, MQ2RWarp, RGMercs, and e9loot (proLoot) up to date
by tracking GitHub commit SHAs and release tags.

## Install

```
pip install -e .
```

## Usage

```
profetch status      # show installed vs. remote versions
profetch version     # show proFetch version
```

## Configuration

Settings live in `C:\Users\Public\proFetch\`:

| File | Purpose |
|---|---|
| `settings.toml` | Shipped defaults (overwritten on proFetch self-update) |
| `settings.local.toml` | Your overrides — never overwritten |
| `profetch.db` | SQLite version tracking database |

Override `mq_rekkas` path in `settings.local.toml`:

```toml
[paths]
mq_rekkas = "D:\\Games\\MQ-Rekka"
```

Disable a component:

```toml
[components]
rgmercs = false
```
