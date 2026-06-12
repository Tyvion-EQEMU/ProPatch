from __future__ import annotations
import tkinter as tk


class Tooltip:
    """Hover tooltip for any tkinter or CTK widget.

    CTK widgets have internal child widgets that cause <Leave> to fire when
    the mouse moves between them. This class binds recursively to all children
    and ignores <Leave> events where the pointer is still within the root widget.
    """

    def __init__(self, widget, text: str, delay: int = 500) -> None:
        self._root     = widget
        self._text     = text
        self._delay    = delay
        self._tip_win  = None
        self._after_id = None
        self._bind_recursive(widget)

    def _bind_recursive(self, widget) -> None:
        widget.bind("<Enter>",       self._on_enter, add="+")
        widget.bind("<Leave>",       self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")
        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _on_enter(self, event=None) -> None:
        if self._after_id:
            return
        self._after_id = self._root.after(self._delay, self._show)

    def _on_leave(self, event=None) -> None:
        # Ignore leave events where the pointer is still inside the root widget
        try:
            rx = self._root.winfo_rootx()
            ry = self._root.winfo_rooty()
            rw = self._root.winfo_width()
            rh = self._root.winfo_height()
            px = self._root.winfo_pointerx()
            py = self._root.winfo_pointery()
            if rx <= px <= rx + rw and ry <= py <= ry + rh:
                return
        except Exception:
            pass
        if self._after_id:
            self._root.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self) -> None:
        self._after_id = None
        if self._tip_win:
            return
        try:
            x = self._root.winfo_rootx() + 10
            y = self._root.winfo_rooty() + self._root.winfo_height() + 6
        except Exception:
            return
        self._tip_win = tw = tk.Toplevel(self._root)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.wm_attributes("-topmost", True)
        tk.Label(
            tw,
            text=self._text,
            justify="left",
            background="#1a1a2e",
            foreground="#cccccc",
            font=("Consolas", 10),
            relief="flat",
            bd=1,
            padx=8,
            pady=5,
            wraplength=320,
        ).pack()

    def _hide(self) -> None:
        if self._tip_win:
            self._tip_win.destroy()
            self._tip_win = None
