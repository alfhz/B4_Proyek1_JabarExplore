"""
smooth_scroll.py — Perbaikan scroll CTkScrollableFrame di Windows.

Masalah asal: CTkScrollableFrame scroll 3 unit sekaligus (terlalu kasar),
dan di Windows tanpa DPI fix menyebabkan visual glitch (teks/widget patah).

Solusi: ganti dengan scroll 1 unit per event, scroll dipicu via canvas
langsung (bukan bind_all yang bisa bertabrakan).

Cara pakai:
    from src.utils.smooth_scroll import apply_smooth_scroll
    apply_smooth_scroll(scroll_frame)   # scroll_frame = CTkScrollableFrame
"""

from __future__ import annotations

# ── Konstanta ─────────────────────────────────────────────────────────────────
_SCROLL_SPEED = 2   # jumlah unit scroll per notch roda mouse (default CTk = 3, kita turunkan)


def _make_scroll_handler(canvas):
    """Buat handler scroll yang memakai 1 unit agar lebih halus."""
    def _on_wheel(event):
        try:
            # Pastikan canvas masih ada
            if not canvas.winfo_exists():
                return
            # Jika konten tidak perlu di-scroll, skip
            if canvas.yview() == (0.0, 1.0):
                return

            # Windows: event.delta = ±120 per notch
            # macOS : event.delta = ±1
            # Linux : event.num = 4 (up) / 5 (down)
            if hasattr(event, "num") and event.num == 4:
                direction = -1
            elif hasattr(event, "num") and event.num == 5:
                direction = 1
            elif hasattr(event, "delta"):
                direction = -1 if event.delta > 0 else 1
            else:
                return

            canvas.yview_scroll(direction * _SCROLL_SPEED, "units")
        except Exception:
            pass

    return _on_wheel


# ── Tracking frame yang sudah di-patch ────────────────────────────────────────
_patched: set = set()


def apply_smooth_scroll(ctk_scrollable_frame) -> None:
    """
    Ganti scroll handler default CTkScrollableFrame dengan versi yang lebih halus.

    Parameter
    ---------
    ctk_scrollable_frame : customtkinter.CTkScrollableFrame
        Frame yang ingin diperbaiki scroll-nya.
    """
    frame_id = id(ctk_scrollable_frame)

    try:
        canvas = ctk_scrollable_frame._parent_canvas
    except AttributeError:
        return

    handler = _make_scroll_handler(canvas)

    if frame_id not in _patched:
        # Timpa binding default CustomTkinter dengan milik kita
        canvas.bind("<MouseWheel>", handler, add=False)
        canvas.bind("<Button-4>",   handler, add=False)
        canvas.bind("<Button-5>",   handler, add=False)
        _patched.add(frame_id)

        # Simpan handler agar bisa dipakai ulang untuk rebind children
        ctk_scrollable_frame._smooth_handler = handler

    # Selalu bind ulang children (setelah render baru)
    _bind_children(ctk_scrollable_frame, handler)


def rebind_scroll_children(ctk_scrollable_frame) -> None:
    """
    Panggil setelah menambahkan row/widget baru ke dalam scrollable frame
    agar widget baru juga terdaftar ke scroll handler.
    """
    handler = getattr(ctk_scrollable_frame, "_smooth_handler", None)
    if handler:
        _bind_children(ctk_scrollable_frame, handler)


def _bind_children(widget, handler) -> None:
    """Rekursif bind semua child widget agar scroll diteruskan ke canvas."""
    try:
        widget.bind("<MouseWheel>", handler, add=False)
        widget.bind("<Button-4>",   handler, add=False)
        widget.bind("<Button-5>",   handler, add=False)
        for child in widget.winfo_children():
            _bind_children(child, handler)
    except Exception:
        pass
