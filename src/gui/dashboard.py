"""
dashboard.py — VERSI OPTIMASI + SESUAI GAMBAR (UPDATED)
Pembaruan:
  - Top Destinasi per Kategori: scroll kanan-kiri dengan tombol panah,
    kategori diperluas: Pantai, Pegunungan, Kawah, Danau/Situ/Telaga,
    Air Terjun, Hutan, Taman Nasional, Sungai
  - Grafik Rating: bar chart yang rapi dengan warna gradient hijau
  - Grafik Sebaran Kategori: donut chart dengan legenda yang lebih baik
  - Grafik Kabupaten/Kota: scrollable horizontal dengan tombol panah kanan-kiri
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

# ── Palet warna ─────────────────────────────────────────────────────────────
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

# Palet untuk kategori wisata
KATEGORI_PALETTE = {
    "Pantai":         "#0EA5E9",
    "Pegunungan":     "#10B981",
    "Gunung":         "#10B981",
    "Kawah":          "#F97316",
    "Danau":          "#6366F1",
    "Situ":           "#6366F1",
    "Telaga":         "#6366F1",
    "Air Terjun":     "#14B8A6",
    "Curug":          "#14B8A6",
    "Hutan":          "#22C55E",
    "Taman Nasional": "#84CC16",
    "Taman":          "#84CC16",
    "Sungai":         "#38BDF8",
    "Lainnya":        "#A78BFA",
}

PALETTE = ["#10B981", "#0EA5E9", "#F97316", "#6366F1", "#14B8A6",
           "#22C55E", "#84CC16", "#38BDF8", "#A78BFA", "#F59E0B"]

STAR_COLOR = "#FBBF24"
STAR_EMPTY = "#E5E7EB"

# Kategori resmi untuk top destinasi
KATEGORI_TOP = [
    "Pantai", "Pegunungan", "Kawah", "Danau/Situ/Telaga",
    "Air Terjun", "Hutan", "Taman Nasional", "Sungai"
]

# Mapping alias kategori dari data ke kategori tampilan
KATEGORI_ALIAS = {
    "gunung":          "Pegunungan",
    "pegunungan":      "Pegunungan",
    "pantai":          "Pantai",
    "kawah":           "Kawah",
    "danau":           "Danau/Situ/Telaga",
    "situ":            "Danau/Situ/Telaga",
    "telaga":          "Danau/Situ/Telaga",
    "air terjun":      "Air Terjun",
    "curug":           "Air Terjun",
    "hutan":           "Hutan",
    "taman nasional":  "Taman Nasional",
    "taman":           "Taman Nasional",
    "sungai":          "Sungai",
}

_PLACEHOLDER_CACHE: dict = {}

# Warna thumbnail per kategori
KATEGORI_THUMB_COLOR = {
    "Pantai":            (14,  165, 233),
    "Pegunungan":        (16,  185, 129),
    "Kawah":             (249, 115,  22),
    "Danau/Situ/Telaga": (99,  102, 241),
    "Air Terjun":        (20,  184, 166),
    "Hutan":             (34,  197,  94),
    "Taman Nasional":    (132, 204,  22),
    "Sungai":            (56,  189, 248),
}


def _make_placeholder(w: int, h: int, hue: tuple) -> ctk.CTkImage:
    key = (w, h, tuple(hue))
    if key in _PLACEHOLDER_CACHE:
        return _PLACEHOLDER_CACHE[key]
    img  = Image.new("RGB", (w, h), hue)
    draw = ImageDraw.Draw(img)
    # Buat pattern diagonal yang lebih menarik
    darker = (max(0, hue[0] - 30), max(0, hue[1] - 25), max(0, hue[2] - 20))
    for i in range(0, w + h, 20):
        draw.line([(max(0, i - h), min(h, i)), (min(w, i), max(0, i - w))],
                  fill=darker, width=3)
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
    _PLACEHOLDER_CACHE[key] = ctk_img
    return ctk_img


def _star_row(parent, rating: float):
    full = int(rating)
    row  = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(anchor="w", pady=(4, 0))
    for i in range(5):
        col = STAR_COLOR if i < full else STAR_EMPTY
        ctk.CTkLabel(row, text="★", font=ctk.CTkFont(size=13), text_color=col).pack(side="left")
    ctk.CTkLabel(row, text=f"  {rating:.1f}", font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=C["txt"]).pack(side="left", padx=(4, 0))


def _destination_card(parent, name, rating, category, thumb, ulasan=0):
    """Kartu destinasi dengan desain yang lebih rapi."""
    card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=14,
                        border_width=1, border_color=C["border"], width=195)
    card.pack_propagate(False)

    # Gambar thumbnail
    img_lbl = ctk.CTkLabel(card, text="", image=thumb)
    img_lbl.pack(fill="x", padx=0, pady=0)

    # Kategori badge di atas gambar (overlay-style via body)
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=12, pady=(8, 12))

    ctk.CTkLabel(body, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=C["txt"], anchor="w", wraplength=160).pack(fill="x")
    _star_row(body, rating)

    # Tag kategori berwarna sesuai tipe
    kat_key = category.split("/")[0].strip()
    tag_color = KATEGORI_PALETTE.get(kat_key, C["border"])
    tag_frame = ctk.CTkFrame(body, fg_color=tag_color, corner_radius=20)
    tag_frame.pack(anchor="w", pady=(6, 0))
    ctk.CTkLabel(tag_frame, text=f"  {category}  ",
                 font=ctk.CTkFont(size=10, weight="bold"), text_color="white").pack()

    if ulasan:
        ctk.CTkLabel(body, text=f"💬 {ulasan:,} ulasan".replace(",", "."),
                     font=ctk.CTkFont(size=10), text_color=C["muted"]).pack(anchor="w", pady=(4, 0))
    return card


def _build_donut_fig(labels, sizes, colors, center_text):
    """Donut chart lebih besar dan rapi tanpa legenda internal."""
    fig = Figure(figsize=(3.2, 3.2), dpi=80)
    fig.patch.set_facecolor(C["card"])
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    ax = fig.add_subplot(111)
    ax.set_facecolor(C["card"])

    wedge_props = dict(width=0.45, edgecolor="#FFFFFF", linewidth=2.5)
    ax.pie(sizes, colors=colors, startangle=90, wedgeprops=wedge_props)
    ax.text(0, 0, center_text, ha="center", va="center",
            fontsize=18, fontweight="bold", color=C["teal"])
    ax.axis("equal")
    return fig


def _build_rating_bar_fig(labels, values):
    """Bar chart rating dengan gradient warna hijau."""
    fig = Figure(figsize=(4.2, 3.2), dpi=80)
    fig.patch.set_facecolor(C["card"])
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.18)
    ax = fig.add_subplot(111)
    ax.set_facecolor(C["card"])
    ax.set_title("Jumlah Wisata Berdasarkan Rating", fontsize=10,
                 fontweight="bold", color=C["txt"], loc="left", pad=10)

    # Warna gradient dari muda ke tua (makin tinggi bintang makin gelap hijau)
    bar_colors = ["#A7F3D0", "#6EE7B7", "#34D399", "#10B981", "#059669"]
    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=bar_colors, width=0.58, zorder=3,
                  edgecolor="white", linewidth=1.5)

    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f'{int(h)}',
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9, fontweight="bold", color=C["muted"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, color=C["muted"])
    ax.tick_params(axis='y', colors=C["muted"], labelsize=8)
    ax.tick_params(axis='x', length=0)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3, color=C["border"], zorder=0)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_edgecolor(C["border"])
    ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 10)
    return fig


def _build_kabupaten_bar_fig(labels, values):
    """Bar chart scrollable untuk kabupaten/kota."""
    n = len(labels)
    bar_w = 0.85
    fig_w = max(6.0, n * 0.95)
    fig = Figure(figsize=(fig_w, 3.0), dpi=80)
    fig.patch.set_facecolor(C["card"])
    fig.subplots_adjust(left=max(0.02, 0.6 / fig_w), right=0.99,
                        top=0.88, bottom=0.32)
    ax = fig.add_subplot(111)
    ax.set_facecolor(C["card"])
    ax.set_title("Jumlah Wisata per Kabupaten / Kota", fontsize=10,
                 fontweight="bold", color=C["txt"], loc="left", pad=10)

    x = np.arange(n)
    bars = ax.bar(x, values, color="#A78BFA", width=bar_w, zorder=3,
                  edgecolor="white", linewidth=1.5)

    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.annotate(f'{int(h)}',
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 4), textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, fontweight="bold", color=C["muted"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, color=C["muted"],
                       rotation=40, ha="right")
    ax.tick_params(axis='y', colors=C["muted"], labelsize=8)
    ax.tick_params(axis='x', length=0)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3, color=C["border"], zorder=0)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_edgecolor(C["border"])
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 10)
    return fig


class KartuMetrikDashboard(ctk.CTkFrame):
    """Dua kartu metrik: Total Destinasi Wisata dan Rata-rata Rating."""
    def __init__(self, master, metrik_data, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        tgl = metrik_data.get("tanggal_terakhir", "-")
        cards = [
            ("Total Destinasi Wisata", str(metrik_data["total_wisata"]), "✈", "#D1FAE5"),
            ("Rata - rata Rating",     f"{metrik_data['rata_rating']:.1f}", "★", "#D1FAE5"),
        ]
        for i, (label, nilai, ikon, badge_color) in enumerate(cards):
            self.grid_columnconfigure(i, weight=1)
            kartu = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                 border_width=1, border_color=C["border"])
            kartu.grid(row=0, column=i, padx=(0 if i == 0 else 14, 0), sticky="ew")
            kartu.grid_columnconfigure(0, weight=1)
            top = ctk.CTkFrame(kartu, fg_color="transparent")
            top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(18, 4))
            top.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(top, text=label, font=ctk.CTkFont(size=12),
                         text_color=C["muted"], anchor="w").grid(row=0, column=0, sticky="w")
            badge = ctk.CTkFrame(top, fg_color=badge_color, corner_radius=10, width=40, height=40)
            badge.grid(row=0, column=1, sticky="e")
            badge.grid_propagate(False)
            ctk.CTkLabel(badge, text=ikon, font=ctk.CTkFont(size=18),
                         text_color=C["teal"]).place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(kartu, text=nilai, font=ctk.CTkFont(size=28, weight="bold"),
                         text_color=C["txt"]).grid(row=1, column=0, padx=20, sticky="w")
            # Tanggal terakhir update data
            ctk.CTkLabel(kartu, text=f"📅 Update terakhir: {tgl}",
                         font=ctk.CTkFont(size=10), text_color="#9CA3AF").grid(
                row=2, column=0, padx=20, pady=(2, 14), sticky="w")


class TopDestinasScroll(ctk.CTkFrame):
    """
    Widget Top Destinasi per Kategori dengan:
    - Tombol panah kiri/kanan untuk scroll
    - Kartu per kategori: Pantai, Pegunungan, Kawah, dll.
    - Klik kartu untuk navigasi ke detail wisata
    """
    SCROLL_STEP = 210  # pixel per klik

    def __init__(self, master, top_list: list, navigasi_ke_detail=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._top_list = top_list
        self._nav_detail = navigasi_ke_detail
        self._build()

    def _get_kategori_display(self, tipe_raw: str) -> str:
        """Normalkan tipe wisata ke kategori tampilan."""
        key = tipe_raw.lower().strip()
        return KATEGORI_ALIAS.get(key, tipe_raw)

    def _group_by_kategori(self) -> dict:
        """Kelompokkan data per kategori & ambil 1 terbaik per kategori."""
        grouped: dict[str, list] = {k: [] for k in KATEGORI_TOP}
        for item in self._top_list:
            tipe = item.get("kategori", item.get("tipe", ""))
            kat  = self._get_kategori_display(tipe)
            if kat in grouped:
                grouped[kat].append(item)
        # Ambil top 1 per kategori (sudah diurutkan rating desc dari stats_logic)
        return grouped

    def _build(self):
        grouped = self._group_by_kategori()

        # ── wrapper dengan tombol panah ──
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x")
        nav.grid_columnconfigure(1, weight=1)

        btn_left = ctk.CTkButton(nav, text="❮", width=36, height=36,
                                 fg_color=C["card"], text_color=C["txt"],
                                 border_width=1, border_color=C["border"],
                                 hover_color="#F1F5F9", corner_radius=18,
                                 font=ctk.CTkFont(size=16),
                                 command=self._scroll_left)
        btn_left.grid(row=0, column=0, padx=(0, 8))

        # Canvas + scrollbar tersembunyi
        canvas_wrap = ctk.CTkFrame(nav, fg_color="transparent")
        canvas_wrap.grid(row=0, column=1, sticky="ew")

        self._scroll_frame = ctk.CTkScrollableFrame(
            canvas_wrap, orientation="horizontal",
            fg_color="transparent", height=230,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["border"]
        )
        self._scroll_frame.pack(fill="x", expand=True)

        btn_right = ctk.CTkButton(nav, text="❯", width=36, height=36,
                                  fg_color=C["card"], text_color=C["txt"],
                                  border_width=1, border_color=C["border"],
                                  hover_color="#F1F5F9", corner_radius=18,
                                  font=ctk.CTkFont(size=16),
                                  command=self._scroll_right)
        btn_right.grid(row=0, column=2, padx=(8, 0))

        # Render kartu per kategori
        for i, kat in enumerate(KATEGORI_TOP):
            items = grouped.get(kat, [])
            hue   = KATEGORI_THUMB_COLOR.get(kat, (100, 100, 100))
            thumb = _make_placeholder(195, 115, hue)

            if items:
                best = max(items, key=lambda x: float(x.get("rating", 0) or 0))
                card = _destination_card(
                    self._scroll_frame,
                    name=best.get("nama", kat),
                    rating=float(best.get("rating", 0) or 0),
                    category=kat,
                    thumb=thumb,
                    ulasan=best.get("jumlah_ulasan", 0),
                )
                # Bind klik card → navigasi ke detail wisata
                raw_data = best.get("_raw")
                if raw_data and self._nav_detail:
                    self._bind_click_recursive(card, raw_data)
            else:
                # Kartu placeholder jika tidak ada data
                card = ctk.CTkFrame(self._scroll_frame, fg_color=C["card"],
                                    corner_radius=14, border_width=1,
                                    border_color=C["border"], width=195)
                card.pack_propagate(False)
                ctk.CTkLabel(card, text="", image=thumb).pack(fill="x")
                body = ctk.CTkFrame(card, fg_color="transparent")
                body.pack(fill="both", expand=True, padx=12, pady=(8, 12))
                ctk.CTkLabel(body, text=kat, font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=C["muted"], anchor="w").pack(fill="x")
                ctk.CTkLabel(body, text="Belum ada data",
                             font=ctk.CTkFont(size=11), text_color=C["muted"],
                             anchor="w").pack(fill="x")
                kat_key = kat.split("/")[0].strip()
                tag_color = KATEGORI_PALETTE.get(kat_key, C["border"])
                tag_f = ctk.CTkFrame(body, fg_color=tag_color, corner_radius=20)
                tag_f.pack(anchor="w", pady=(6, 0))
                ctk.CTkLabel(tag_f, text=f"  {kat}  ",
                             font=ctk.CTkFont(size=10, weight="bold"),
                             text_color="white").pack()

            card.pack(side="left", padx=(0 if i == 0 else 10, 0))

    def _bind_click_recursive(self, widget, raw_data):
        """Bind klik ke semua child widget agar seluruh area card bisa diklik."""
        widget.configure(cursor="hand2") if hasattr(widget, 'configure') else None
        widget.bind("<Button-1>", lambda e: self._nav_detail(raw_data))
        for child in widget.winfo_children():
            self._bind_click_recursive(child, raw_data)

    def _scroll_left(self):
        sf = self._scroll_frame
        sf._parent_canvas.xview_scroll(-3, "units")

    def _scroll_right(self):
        sf = self._scroll_frame
        sf._parent_canvas.xview_scroll(3, "units")


class HalamanDashboard(ctk.CTkFrame):

    def __init__(self, master, navigasi_ke_detail=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._nav_detail = navigasi_ke_detail
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self._canvas_list   = []
        self._widget_metrik = None
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
        """Mulai load data di background thread agar UI tidak freeze."""
        self._btn_refresh.configure(state="disabled", text="⟳  Memuat…")
        self._lbl_status.configure(text="Memuat data dari file JSON…")
        self.update_idletasks()

        for w in self._scroll.winfo_children():
            w.destroy()
        self._canvas_list.clear()

        threading.Thread(target=self._load_data_worker, daemon=True).start()
        self.after(100, self._poll_result)

    def _load_data_worker(self):
        """Berjalan di thread terpisah: baca JSON + hitung statistik."""
        try:
            raw_data    = buka_json()
            df          = buat_dataframe(raw_data)
            metrik_data = ambil_metrik_data(df, raw_data=raw_data)
            data_stats  = ambil_data_stats(df)
            data_stats["_top_destinasi"] = metrik_data["top_destinasi"]
            # Simpan raw_data untuk dropdown filter kota (tanpa buka file lagi)
            data_stats["_raw_data"] = raw_data
            self._result_queue.put(("ok", metrik_data, data_stats))
        except Exception as exc:
            self._result_queue.put(("err", str(exc)))

    def _poll_result(self):
        """Cek antrian hasil; jika belum siap, polling ulang 100 ms."""
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

    # ─────────────────────── RENDER (MAIN THREAD) ────────────────────────────
    def _render_all(self, metrik_data, data_stats):
        """Render semua bagian dashboard ke scroll area."""
        self._render_hero()
        self._render_metrik(metrik_data)
        self._render_top_destinasi_section(metrik_data, data_stats)
        self._render_distribution_charts(metrik_data, data_stats)
        self._render_kabupaten_chart(data_stats)

        n = metrik_data["total_wisata"]
        self._lbl_status.configure(
            text=f"✓  Dashboard siap — {n} destinasi wisata termuat  |  data/data_wisata.json"
        )
        self._btn_refresh.configure(state="normal", text="⟳  Refresh Data")

    def _render_hero(self):
        hero = ctk.CTkFrame(self._scroll, fg_color="transparent")
        hero.pack(fill="x", padx=28, pady=(22, 6))
        ctk.CTkLabel(hero, text="Welcome To Jabar Explore",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=C["txt"], anchor="w").pack(fill="x")
        ctk.CTkLabel(hero,
                     text="Jelajahi keindahan wisata Jawa Barat dan temukan destinasi terbaik untuk pengalaman tak terlupakan.",
                     font=ctk.CTkFont(size=13), text_color=C["muted"],
                     anchor="w", justify="left").pack(fill="x", pady=(4, 0))

    def _render_metrik(self, metrik_data):
        self._widget_metrik = KartuMetrikDashboard(self._scroll, metrik_data=metrik_data)
        self._widget_metrik.pack(fill="x", padx=28, pady=(12, 0))

    def _render_top_destinasi_section(self, metrik_data, data_stats):
        """Header + dropdown filter kota + kartu scroll horizontal dengan tombol panah."""
        header_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        header_frame.pack(fill="x", padx=28, pady=(20, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header_frame, text="Top Destinasi per Kategori",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=C["txt"], anchor="w").grid(row=0, column=0, sticky="w")

        # Bangun daftar kota dari raw_data yang sudah ada (tidak buka JSON lagi)
        raw_data = data_stats.get("_raw_data", [])
        kota_set = set()
        for item in raw_data:
            alamat = item.get("identitas", {}).get("alamat", "")
            if not alamat:
                alamat = item.get("kabupaten", "")
            if "," in alamat:
                kota_set.add(alamat.split(",")[0].strip())
            elif alamat:
                kota_set.add(alamat.strip())
        kota_values = ["Semua Kota / Kabupaten"] + sorted(kota_set)

        self._filter_kota_var = ctk.StringVar(value="Semua Kota / Kabupaten")
        filter_combo = ctk.CTkOptionMenu(
            header_frame,
            variable=self._filter_kota_var,
            values=kota_values,
            fg_color=C["card"],
            button_color=C["teal"],
            text_color=C["txt"],
            dropdown_fg_color=C["card"],
            width=190,
            command=self._on_filter_kota_changed
        )
        filter_combo.grid(row=0, column=1, padx=(12, 0), sticky="e")

        # Simpan data_stats untuk dipakai ulang saat filter berubah
        self._cached_metrik = metrik_data
        self._cached_raw    = raw_data

        # Container untuk kartu top destinasi (agar bisa di-replace saat filter berubah)
        self._top_container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._top_container.pack(fill="x", padx=28, pady=(0, 4))

        top_list = metrik_data.get("top_destinasi", [])
        self._render_top_cards(top_list)

    def _on_filter_kota_changed(self, pilihan: str):
        """Callback saat dropdown kota berubah — filter top destinasi."""
        raw = self._cached_raw
        if pilihan == "Semua Kota / Kabupaten" or not pilihan:
            # Gunakan top destinasi global yang sudah dihitung
            top_list = self._cached_metrik.get("top_destinasi", [])
        else:
            # Filter raw_data berdasarkan kota yang dipilih, lalu hitung ulang top
            filtered = []
            for item in raw:
                alamat = item.get("identitas", {}).get("alamat", "") or item.get("kabupaten", "")
                kota = alamat.split(",")[0].strip() if "," in alamat else alamat.strip()
                if kota == pilihan:
                    filtered.append(item)
            # Bentuk top_list dari data yang sudah difilter
            top_list = []
            seen_kat: set = set()
            # Urutkan berdasarkan rating
            def get_rating(item):
                try:
                    return float(item.get("identitas", {}).get("rating") or item.get("rating") or 0)
                except (ValueError, TypeError):
                    return 0.0
            sorted_filtered = sorted(filtered, key=get_rating, reverse=True)
            for item in sorted_filtered:
                idn = item.get("identitas", item)
                kat = idn.get("tipe") or idn.get("kategori") or "Umum"
                if kat not in seen_kat:
                    seen_kat.add(kat)
                    top_list.append({
                        "nama":         idn.get("nama", "-"),
                        "rating":       get_rating(item),
                        "kategori":     kat,
                        "jumlah_ulasan": int(idn.get("jumlah_ulasan") or 0),
                    })

        # Hapus kartu lama dan render ulang
        for w in self._top_container.winfo_children():
            w.destroy()
        self._render_top_cards(top_list)

    def _render_top_cards(self, top_list: list):
        """Render widget TopDestinasScroll ke dalam _top_container."""
        TopDestinasScroll(self._top_container, top_list=top_list,
                          navigasi_ke_detail=self._nav_detail).pack(fill="x")

    def _render_distribution_charts(self, metrik_data, data_stats):
        """Bar chart rating + Donut chart kategori — berdampingan."""
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(20, 8))
        row.grid_columnconfigure(0, weight=6)
        row.grid_columnconfigure(1, weight=5)

        # ── Bar chart: Jumlah Wisata Berdasarkan Rating ──────────────────────
        dist_r = data_stats.get("distribusi_rating")
        if dist_r is not None and hasattr(dist_r, "reindex"):
            dr = dist_r.reindex(range(1, 6), fill_value=0).astype(int)
            r_counts = [int(dr.loc[i]) for i in range(1, 6)]
        else:
            r_counts = [0, 0, 0, 0, 0]
        r_labels = ["Bintang 1", "Bintang 2", "Bintang 3", "Bintang 4", "Bintang 5"]

        wrap_bar = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=14,
                                border_width=1, border_color=C["border"])
        wrap_bar.grid(row=0, column=0, padx=(0, 10), sticky="nsew", ipady=4)

        fig_bar = _build_rating_bar_fig(r_labels, r_counts)
        canvas_bar = FigureCanvasTkAgg(fig_bar, master=wrap_bar)
        canvas_bar.draw()
        canvas_bar.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._canvas_list.append(canvas_bar)

        # ── Donut chart: Sebaran Destinasi Berdasarkan Kategori ──────────────
        kat = data_stats.get("sebaran_kategori")
        if kat is not None and not kat.empty:
            c_labels = list(kat.index)
            c_sizes  = [int(v) for v in kat.values]
            c_colors = [PALETTE[i % len(PALETTE)] for i in range(len(c_labels))]
        else:
            c_labels, c_sizes, c_colors = ["-"], [1], [C["muted"]]

        total = metrik_data["total_wisata"]

        wrap_donut = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=14,
                                  border_width=1, border_color=C["border"])
        wrap_donut.grid(row=0, column=1, padx=(10, 0), sticky="nsew", ipady=4)

        # Judul section
        ctk.CTkLabel(wrap_donut, text="Sebaran Destinasi Berdasarkan Kategori",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["txt"], anchor="w").pack(anchor="w", padx=14, pady=(12, 0))

        inner = ctk.CTkFrame(wrap_donut, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Donut di kiri
        fig_donut = _build_donut_fig(c_labels, c_sizes, c_colors, str(total))
        canvas_donut = FigureCanvasTkAgg(fig_donut, master=inner)
        canvas_donut.draw()
        canvas_donut.get_tk_widget().pack(side="left", fill="y")
        self._canvas_list.append(canvas_donut)

        # Legenda di kanan
        leg = ctk.CTkFrame(inner, fg_color="transparent")
        leg.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=10)

        for lab, col, cnt in zip(c_labels, c_colors, c_sizes):
            if cnt == 0:
                continue
            lrow = ctk.CTkFrame(leg, fg_color="transparent")
            lrow.pack(fill="x", pady=3)
            ctk.CTkLabel(lrow, text="●", font=ctk.CTkFont(size=14),
                         text_color=col, width=20).pack(side="left")
            ctk.CTkLabel(lrow, text=lab, font=ctk.CTkFont(size=11),
                         text_color=C["muted"], anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(lrow, text=str(cnt), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["txt"]).pack(side="right")

    def _render_kabupaten_chart(self, data_stats):
        """Bar chart kabupaten/kota — scrollable horizontal dengan tombol panah."""
        kab = data_stats.get("total_per_kabupaten")
        if kab is None or kab.empty:
            return
        labels = list(kab.index)
        values = [int(v) for v in kab.values]

        # Wrapper card
        wrap = ctk.CTkFrame(self._scroll, fg_color=C["card"], corner_radius=14,
                            border_width=1, border_color=C["border"])
        wrap.pack(fill="x", padx=28, pady=(0, 20))

        # Judul + tombol panah dalam satu baris
        top_bar = ctk.CTkFrame(wrap, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(14, 4))
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_bar, text="Jumlah Wisata per Kabupaten / Kota",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["txt"], anchor="w").grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(top_bar, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="e")

        # Scrollable frame untuk chart
        self._kab_scroll = ctk.CTkScrollableFrame(
            wrap, orientation="horizontal",
            fg_color="transparent", height=250,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["teal"]
        )
        self._kab_scroll.pack(fill="x", padx=8, pady=(0, 8))

        # Tombol panah — setelah scroll frame dibuat
        btn_kiri = ctk.CTkButton(nav, text="❮", width=30, height=30,
                                 fg_color=C["sidebar"], text_color=C["txt"],
                                 border_width=1, border_color=C["border"],
                                 hover_color="#E2E8F0", corner_radius=6,
                                 font=ctk.CTkFont(size=13),
                                 command=self._kab_scroll_left)
        btn_kiri.pack(side="left", padx=(0, 4))

        btn_kanan = ctk.CTkButton(nav, text="❯", width=30, height=30,
                                  fg_color=C["sidebar"], text_color=C["txt"],
                                  border_width=1, border_color=C["border"],
                                  hover_color="#E2E8F0", corner_radius=6,
                                  font=ctk.CTkFont(size=13),
                                  command=self._kab_scroll_right)
        btn_kanan.pack(side="left")

        # Build figure
        fig = _build_kabupaten_bar_fig(labels, values)
        canvas = FigureCanvasTkAgg(fig, master=self._kab_scroll)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas_list.append(canvas)

    def _kab_scroll_left(self):
        try:
            self._kab_scroll._parent_canvas.xview_scroll(-4, "units")
        except Exception:
            pass

    def _kab_scroll_right(self):
        try:
            self._kab_scroll._parent_canvas.xview_scroll(4, "units")
        except Exception:
            pass


# Ekspor kelas
kartu_metrik_dashboard = KartuMetrikDashboard
dashboard = HalamanDashboard