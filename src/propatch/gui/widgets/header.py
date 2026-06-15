from __future__ import annotations
import tkinter as tk
import webbrowser
from pathlib import Path
import customtkinter as ctk

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

from propatch.__about__ import __version__

_ASSETS_DIR = Path(__file__).parent.parent / "assets"
_WARM_GOLD  = "#FFB833"
_STRIP_BG   = "#07070f"
_MARGIN     = 48
_WIN_W      = 680


def build_header(parent: ctk.CTkFrame) -> tuple[ctk.CTkFrame, int]:
    """Build the shared banner + info strip header.

    Returns (header_frame, banner_height_px).
    banner_height_px is 0 when the image is absent/unloadable (fallback bar shown).
    """
    header = ctk.CTkFrame(parent, corner_radius=0, fg_color=("#1a1a2e", "#0d0d1a"))
    header.grid_columnconfigure(0, weight=1)

    # ── Banner image ──────────────────────────────────────────────────────────
    banner_h = 0
    if _PIL_AVAILABLE:
        banner_path = _ASSETS_DIR / "hero-banner.webp"
        if banner_path.exists():
            try:
                img = Image.open(banner_path)
                orig_w, orig_h = img.size
                banner_h = int(_WIN_W * orig_h / orig_w)
                img = img.resize((_WIN_W, banner_h), Image.LANCZOS)
                banner_ctk = ctk.CTkImage(img, size=(_WIN_W, banner_h))
                ctk.CTkLabel(header, image=banner_ctk, text="").grid(
                    row=0, column=0, sticky="ew"
                )
            except Exception:
                banner_h = 0

    if banner_h == 0:
        fb = ctk.CTkFrame(header, height=80, corner_radius=0, fg_color=("#1a1a2e", "#0d0d1a"))
        fb.grid(row=0, column=0, sticky="ew")
        fb.grid_propagate(False)
        ctk.CTkFrame(fb, width=6, fg_color="#4a9eff", corner_radius=0).place(
            x=0, y=0, relheight=1
        )

    # ── Info strip ────────────────────────────────────────────────────────────
    strip = ctk.CTkFrame(header, height=60, corner_radius=0, fg_color=(_STRIP_BG, _STRIP_BG))
    strip.grid(row=1, column=0, sticky="ew")
    strip.grid_propagate(False)

    left_group = tk.Frame(strip, bg=_STRIP_BG)
    left_group.place(relx=0, rely=0.5, anchor="w", x=_MARGIN)

    line1 = tk.Frame(left_group, bg=_STRIP_BG)
    line1.pack(side="top", anchor="w")
    tk.Label(line1, text="ProPatch",
             font=("Consolas", 14, "bold"), fg=_WARM_GOLD, bg=_STRIP_BG,
             padx=0, pady=0).pack(side="left")
    tk.Label(line1, text=f"  v{__version__}",
             font=("Consolas", 10), fg=_WARM_GOLD, bg=_STRIP_BG,
             padx=0, pady=0).pack(side="left")
    tk.Label(line1, text="  [BETA]",
             font=("Consolas", 10, "bold"), fg="#ff8c00", bg=_STRIP_BG,
             padx=0, pady=0).pack(side="left")

    line2 = tk.Frame(left_group, bg=_STRIP_BG)
    line2.pack(side="top", anchor="w")
    tk.Label(line2, text="by ",
             font=("Consolas", 10), fg="#888888", bg=_STRIP_BG,
             padx=0, pady=0).pack(side="left")
    lbl_author = tk.Label(line2, text="Tyvion",
                          font=("Consolas", 10, "bold"), fg=_WARM_GOLD, bg=_STRIP_BG,
                          padx=0, pady=0, cursor="hand2")
    lbl_author.pack(side="left")
    lbl_author.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Tyvion-EQEMU"))

    return header, banner_h
