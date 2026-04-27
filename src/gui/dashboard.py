"""
dashboard.py  — VERSI OPTIMASI
Perbaikan performa:
  1. buka_json() + buat_dataframe() + ambil_metrik/stats dijalankan di thread
     terpisah → UI tidak freeze saat data besar dibaca.
  2. Setelah thread selesai, hasil dikirim kembali ke main thread via queue
     + after() polling agar aman (Tkinter tidak thread-safe).
  3. Matplotlib figure tetap dibuat di main thread (aman).
  4. DPI grafik 72 (sudah cukup) + figsize ringkas.
  5. _PLACEHOLDER_CACHE mencegah pembuatan ulang placeholder.
"""

from __future__ import annotations
import sys
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import queue
import threading
import numpy as np
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageDraw

from src.utils.file_handler import buka_json
from src.logic.stats_logic import buat_dataframe, ambil_metrik_data, ambil_data_stats

# ── Palet warna ──────────────────────────────────────────────────────────────
C = {
    "bg":      "#F8FAFC",
    "card":    "#FFFFFF",
    "sidebar": "#F9FAFB",
    "border":  "#E2E8F0",
    "teal":    "#10B981",
    "blue":    "#3B82F6",
    "amber":   "#F59E0B",
    "red":     "#EF4444",
    "purple":  "#8B5CF6",
    "yellow":  "#EAB308",
    "txt":     "#0F172A",
    "muted":   "#64748B",
}
PALETTE     = ["#10B981","#34D399","#6EE7B7","#059669","#14B8A6","#0D9488","#047857"]
STAR_COLOR  = "#FBBF24"
STAR_EMPTY  = "#E5E7EB"

_PLACEHOLDER_CACHE: dict = {}


def _make_placeholder(w: int, h: int, hue: tuple) -> ctk.CTkImage:
    key = (w, h, tuple(hue))
    if key in _PLACEHOLDER_CACHE:
        return _PLACEHOLDER_CACHE[key]
    img  = Image.new("RGB", (w, h), hue)
    draw = ImageDraw.Draw(img)
    for i in range(0, w, 24):
        draw.rectangle(
            (i, h // 2, i + 12, h),
            fill=(max(0, hue[0] - 15), max(0, hue[1] - 10), max(0, hue[2] - 5))
        )
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
    _PLACEHOLDER_CACHE[key] = ctk_img
    return ctk_img


def _star_row(parent, rating):
    full = int(rating)
    row  = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(anchor="w", pady=(4, 0))
    for i in range(5):
        col = STAR_COLOR if i < full else STAR_EMPTY
        ctk.CTkLabel(row, text="★", font=ctk.CTkFont(size=13), text_color=col).pack(side="left")
    ctk.CTkLabel(row, text=f"  {rating}", font=ctk.CTkFont(size=11, weight="bold"), text_color=C["txt"]).pack(side="left", padx=(4, 0))


def _destination_card(parent, name, rating, category, thumb, ulasan=0):
    card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=12,
                        border_width=1, border_color=C["border"], width=200)
    card.pack_propagate(False)
    ctk.CTkLabel(card, text="", image=thumb).pack(fill="x", padx=8, pady=(8, 4))
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=12, pady=(0, 10))
    ctk.CTkLabel(body, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=C["txt"], anchor="w", wraplength=160).pack(fill="x")
    _star_row(body, rating)
    tag = ctk.CTkFrame(body, fg_color=C["border"], corner_radius=20)
    tag.pack(anchor="w", pady=(6, 0))
    ctk.CTkLabel(tag, text=f"  {category}  ",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color=C["teal"]).pack()
    if ulasan:
        ctk.CTkLabel(body, text=f"💬 {ulasan:,} ulasan".replace(",", "."),
                     font=ctk.CTkFont(size=10), text_color=C["muted"]).pack(anchor="w", pady=(4, 0))
    return card


def _build_donut_fig(title, labels, sizes, colors, center_text):
    fig = Figure(figsize=(3.4, 3.2), dpi=72)
    fig.patch.set_facecolor(C["card"])
    fig.subplots_adjust(left=0.06, right=0.94, top=0.88, bottom=0.10)
    ax = fig.add_subplot(111)
    ax.set_facecolor(C["card"])
    ax.set_title(title, fontsize=10, fontweight="bold", color=C["txt"], pad=8)
    ax.pie(sizes, colors=colors, startangle=90,
           wedgeprops=dict(width=0.42, edgecolor="#FFFFFF", linewidth=2))
    ax.text(0, 0, center_text, ha="center", va="center",
            fontsize=15, fontweight="bold", color=C["teal"])
    ax.axis("equal")
    return fig


def _build_line_fig(labels, values):
    fig = Figure(figsize=(8.5, 3.0), dpi=72)
    fig.patch.set_facecolor(C["card"])
    ax  = fig.add_subplot(111)
    ax.set_facecolor(C["card"])
    fig.subplots_adjust(left=0.05, right=0.98, top=0.84, bottom=0.24)
    ax.set_title("Jumlah Wisata per Kabupaten/Kota", fontsize=11,
                 fontweight="bold", color=C["txt"], loc="left", pad=10)
    n = len(labels)
    y = np.asarray(values, dtype=float)
    x = np.arange(n, dtype=float)
    if n == 0:
        ymax = 10
    elif n == 1:
        ax.plot(x, y, color=C["purple"], linewidth=2.5, marker="o", markersize=7,
                markerfacecolor="white", markeredgewidth=2, markeredgecolor=C["purple"])
        ymax = max(float(y[0]) * 1.28, 1.0)
    else:
        deg  = min(3, n - 1)
        xi   = np.linspace(x.min(), x.max(), max(n * 12, 48))
        coeff = np.polyfit(x, y, deg)
        yi   = np.polyval(coeff, xi)
        line, = ax.plot(xi, yi, color=C["purple"], linewidth=2.5,
                        antialiased=True, label="Jumlah Wisata")
        ax.plot(x, y, linestyle="none", marker="o", markersize=7,
                markerfacecolor="white", markeredgewidth=2, markeredgecolor=C["purple"])
        ymax = max(float(y.max()) * 1.28, 1.0)
        ax.legend(handles=[line], loc="upper right", fontsize=8,
                  facecolor=C["card"], edgecolor=C["border"], labelcolor=C["txt"])
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, fontsize=8, color=C["muted"])
    ax.tick_params(colors=C["muted"], labelsize=8)
    ax.set_ylim(0, ymax)
    ax.grid(True, linestyle="--", alpha=0.25, color=C["border"])
    for sp in ax.spines.values():
        sp.set_edgecolor(C["border"])
    return fig


class KartuMetrikDashboard(ctk.CTkFrame):
    def __init__(self, master, metrik_data, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        cards = [
            ("Total Destinasi Wisata", str(metrik_data["total_wisata"]), "✈", "#6EE7B7"),
            ("Rata - rata Rating",     str(metrik_data["rata_rating"]),  "★", "#6EE7B7"),
        ]
        for i, (label, nilai, ikon, _) in enumerate(cards):
            self.grid_columnconfigure(i, weight=1)
            kartu = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                 border_width=1, border_color=C["border"])
            kartu.grid(row=0, column=i, padx=(0 if i == 0 else 14, 0), sticky="ew")
            kartu.grid_columnconfigure(0, weight=1)
            top = ctk.CTkFrame(kartu, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 4))
            top.grid_columnconfigure(0, weight=1)
            badge = ctk.CTkFrame(top, fg_color="#D1FAE5", corner_radius=10, width=40, height=40)
            badge.grid(row=0, column=1, sticky="e")
            badge.grid_propagate(False)
            ctk.CTkLabel(badge, text=ikon, font=ctk.CTkFont(size=18),
                         text_color=C["teal"]).place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(kartu, text=nilai, font=ctk.CTkFont(size=28, weight="bold"),
                         text_color=C["txt"]).grid(row=1, column=0, padx=20, sticky="w")
            ctk.CTkLabel(kartu, text=label, font=ctk.CTkFont(size=12),
                         text_color=C["muted"]).grid(row=2, column=0, padx=20, pady=(0, 18), sticky="w")


class HalamanDashboard(ctk.CTkFrame):
    _THUMB_HUES = [(0,90,80),(20,60,110),(90,70,20),(70,20,80),(10,80,50)]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self._canvas_list    = []
        self._widget_metrik  = None
        self._result_queue: queue.Queue = queue.Queue()

        self._build_header()
        self._build_scroll_area()
        self._build_footer()
        self.after(120, self._jalankan_dashboard)

    # ─────────────────────── LAYOUT ─────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=52)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="Ringkasan data wisata",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["muted"]).grid(row=0, column=0, padx=22, pady=8, sticky="w")
        self._btn_refresh = ctk.CTkButton(
            hdr, text="⟳  Refresh Data",
            width=130, height=32, corner_radius=8,
            fg_color=C["teal"], hover_color="#059669", text_color="#FFFFFF",
            font=ctk.CTkFont(weight="bold", size=12),
            command=self._jalankan_dashboard
        )
        self._btn_refresh.grid(row=0, column=2, padx=22, pady=8, sticky="e")

    def _build_scroll_area(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)

    def _build_footer(self):
        ftr = ctk.CTkFrame(self, fg_color=C["sidebar"], corner_radius=0, height=30)
        ftr.grid(row=2, column=0, sticky="ew")
        ftr.grid_propagate(False)
        self._lbl_status = ctk.CTkLabel(
            ftr, text="Menginisialisasi dashboard…",
            font=ctk.CTkFont(size=11), text_color=C["muted"]
        )
        self._lbl_status.grid(row=0, column=0, padx=16, pady=4, sticky="w")

    # ─────────────────────── LOAD DATA (THREAD) ─────────────────────────────

    def _jalankan_dashboard(self):
        """Mulai load data di background thread; UI tidak freeze."""
        self._btn_refresh.configure(state="disabled", text="⟳  Memuat…")
        self._lbl_status.configure(text="Memuat data dari file JSON…")
        self.update_idletasks()

        # Bersihkan konten lama
        for w in self._scroll.winfo_children():
            w.destroy()
        self._canvas_list.clear()

        threading.Thread(target=self._load_data_worker, daemon=True).start()
        self.after(100, self._poll_result)

    def _load_data_worker(self):
        """Berjalan di thread terpisah: baca file + hitung statistik."""
        try:
            raw_data   = buka_json()
            df         = buat_dataframe(raw_data)
            metrik_data = ambil_metrik_data(df)
            data_stats  = ambil_data_stats(df)
            data_stats["_top_destinasi"] = metrik_data["top_destinasi"]
            self._result_queue.put(("ok", metrik_data, data_stats))
        except Exception as exc:
            self._result_queue.put(("err", str(exc)))

    def _poll_result(self):
        """Cek antrian hasil; jika belum siap, coba lagi 100 ms lagi."""
        try:
            payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_result)
            return

        if payload[0] == "err":
            self._lbl_status.configure(text=f"❌ Gagal memuat data: {payload[1]}")
            self._btn_refresh.configure(state="normal", text="⟳  Refresh Data")
            return

        _, metrik_data, data_stats = payload
        self._render_all(metrik_data, data_stats)

    # ─────────────────────── RENDER (MAIN THREAD) ───────────────────────────

    def _render_all(self, metrik_data, data_stats):
        self._render_hero()
        self._render_metrik(metrik_data)
        self._render_top_destinasi(metrik_data["top_destinasi"])
        self._render_donut_row(metrik_data, data_stats)
        self._render_line_chart(data_stats)

        n = metrik_data["total_wisata"]
        self._lbl_status.configure(
            text=f"✓  Dashboard siap — {n} destinasi wisata termuat  |  data/data_wisata.json"
        )
        self._btn_refresh.configure(state="normal", text="⟳  Refresh Data")

    def _render_hero(self):
        hero = ctk.CTkFrame(self._scroll, fg_color="transparent")
        hero.pack(fill="x", padx=28, pady=(22, 6))
        ctk.CTkLabel(
            hero, text="Welcome To Jabar Explore",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=C["txt"], anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            hero,
            text="Jelajahi keindahan wisata Jawa Barat dan temukan destinasi terbaik untuk pengalaman tak terlupakan.",
            font=ctk.CTkFont(size=13), text_color=C["muted"], anchor="w", justify="left"
        ).pack(fill="x", pady=(4, 0))

    def _render_metrik(self, metrik_data):
        self._widget_metrik = KartuMetrikDashboard(self._scroll, metrik_data=metrik_data)
        self._widget_metrik.pack(fill="x", padx=28, pady=(12, 0))

    def _render_top_destinasi(self, top_list):
        if not top_list:
            return
        ctk.CTkLabel(self._scroll, text="Top Destinasi per Kategori",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=C["txt"], anchor="w").pack(fill="x", padx=28, pady=(18, 8))
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=28)
        n = min(len(top_list), 5)
        for i in range(n):
            row.grid_columnconfigure(i, weight=1)
        for i, dest in enumerate(top_list[:5]):
            hue   = self._THUMB_HUES[i % len(self._THUMB_HUES)]
            thumb = _make_placeholder(200, 110, hue)
            card  = _destination_card(
                row,
                name=dest.get("nama", "-"),
                rating=dest.get("rating", 0.0),
                category=dest.get("kategori", "-"),
                thumb=thumb,
                ulasan=dest.get("jumlah_ulasan", 0),
            )
            card.grid(row=0, column=i, padx=(0 if i == 0 else 8, 0), sticky="nsew")

    def _render_donut_row(self, metrik_data, data_stats):
        ctk.CTkLabel(self._scroll, text="Distribusi Data Wisata",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=C["txt"], anchor="w").pack(fill="x", padx=28, pady=(20, 8))
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=28)
        row.grid_columnconfigure((0, 1), weight=1)

        total      = metrik_data["total_wisata"]
        star_labels = ["5★","4★","3★","2★","1★"]
        star_colors = [C["teal"], C["blue"], C["amber"], C["red"], C["purple"]]

        dist_r = data_stats.get("distribusi_rating")
        if dist_r is not None and hasattr(dist_r, "reindex"):
            dr      = dist_r.reindex(range(1, 6), fill_value=0).astype(int)
            r_counts = [int(dr.loc[i]) for i in range(5, 0, -1)]
        else:
            r_counts = [0, 0, 0, 0, 0]

        if sum(r_counts) == 0:
            r_pie_labels, r_pie_sizes, r_pie_colors = ["—"], [1], [C["muted"]]
            r_center      = "0"
            r_legend_rows = [("—", C["muted"], 0)]
        else:
            r_pie_labels, r_pie_sizes, r_pie_colors = star_labels, r_counts, star_colors
            r_center      = str(sum(r_counts))
            r_legend_rows = list(zip(star_labels, star_colors, r_counts))

        kat = data_stats.get("sebaran_kategori")
        if kat is not None and not kat.empty:
            c_labels = list(kat.index)
            c_sizes  = [int(v) for v in kat.values]
            c_colors = PALETTE[:len(c_labels)]
        else:
            c_labels, c_sizes, c_colors = ["-"], [1], [C["muted"]]

        datasets = [
            ("Distribusi Rating Wisata",  r_pie_labels, r_pie_sizes, r_pie_colors,
             r_center, r_legend_rows),
            ("Sebaran Kategori Wisata",   c_labels,     c_sizes,     c_colors,
             str(total), list(zip(c_labels, c_colors, c_sizes))),
        ]

        for col_idx, (title, labels, sizes, colors, center_txt, legend_rows) in enumerate(datasets):
            fig  = _build_donut_fig(title, labels, sizes, colors, center_txt)
            wrap = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=12,
                                border_width=1, border_color=C["border"])
            wrap.grid(row=0, column=col_idx, padx=(0 if col_idx == 0 else 12, 0), sticky="ew")
            inner = ctk.CTkFrame(wrap, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=8, pady=8)
            canvas = FigureCanvasTkAgg(fig, master=inner)
            canvas.draw()
            canvas.get_tk_widget().pack(side="left")
            self._canvas_list.append(canvas)

            leg = ctk.CTkFrame(inner, fg_color="transparent", width=130)
            leg.pack(side="right", fill="y", padx=(0, 12), pady=20)

            if col_idx == 0:
                legend_iter = (
                    [("Tidak ada data", C["muted"], 0)]
                    if r_center == "0"
                    else [(a, b, c) for a, b, c in legend_rows if c > 0]
                )
            else:
                legend_iter = [(a, b, c) for a, b, c in legend_rows if c > 0]

            for lab, col, cnt in legend_iter:
                lrow = ctk.CTkFrame(leg, fg_color="transparent")
                lrow.pack(fill="x", pady=2)
                ctk.CTkLabel(lrow, text="●", font=ctk.CTkFont(size=12), text_color=col, width=18).pack(side="left")
                ctk.CTkLabel(lrow, text=lab, font=ctk.CTkFont(size=11), text_color=C["muted"]).pack(side="left")
                ctk.CTkLabel(lrow, text=str(cnt), font=ctk.CTkFont(size=11, weight="bold"), text_color=C["txt"]).pack(side="right")

    def _render_line_chart(self, data_stats):
        kab = data_stats.get("total_per_kabupaten")
        if kab is None or kab.empty:
            return
        labels = list(kab.index)
        values = [int(v) for v in kab.values]
        wrap   = ctk.CTkFrame(self._scroll, fg_color=C["card"], corner_radius=12,
                              border_width=1, border_color=C["border"])
        wrap.pack(fill="x", padx=28, pady=(16, 0))
        fig    = _build_line_fig(labels, values)
        canvas = FigureCanvasTkAgg(fig, master=wrap)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._canvas_list.append(canvas)