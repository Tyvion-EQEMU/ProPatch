# proFetch GUI

`customtkinter`-based GUI mockup for the proFetch EQ Profusion component patcher.

## Setup

```
pip install customtkinter pillow
```

## Run

```
cd profetch_gui
python main.py
```

## First-run behavior

On first launch `data/settings.json` does not exist, so the setup wizard appears.
Click **Finish Setup** to write the file and proceed to the components view.
Deleting `data/settings.json` and relaunching shows the wizard again.

## Banner image

Drop `hero-banner.webp` into the `assets/` folder (~1200×400 px recommended).
If the file is absent the header falls back to a plain dark bar — no crash.

## Directory layout

```
profetch_gui/
├── main.py               Entry point
├── app.py                CTk window, view switcher, shared state
├── views/
│   ├── components_view.py  Main panel + Add-component dialog
│   ├── log_view.py         Log panel with level filter
│   └── setup_wizard.py     First-run wizard stub
├── widgets/
│   └── component_row.py    Reusable row: checkbox / name / status badge
├── core/
│   ├── logger.py           File logger + seed helper
│   ├── manifest.py         Load component list (static for now)
│   ├── settings.py         Load/save data/settings.json
│   └── update_worker.py    Simulated check + update worker (background thread)
├── assets/
│   └── hero-banner.webp    (you provide this)
├── data/
│   └── manifest.json       Curated component list
└── logs/
    └── profetch.log        Written at runtime
```
