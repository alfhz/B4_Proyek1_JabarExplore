"""
dashboard.py — VERSI OPTIMASI + SESUAI GAMBAR (UPDATED)
Pembaruan:
  - Top Destinasi per Kategori: scroll kanan-kiri dengan tombol panah
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
from src.logic.stats_logic import (
    buat_dataframe, ambil_metrik_data, ambil_data_stats,
    DAFTAR_KAB_KOTA_JABAR, get_official_kabupaten,
)

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
    "Gunung":         "#10B981",
    "Kawah":          "#F97316",
    "Danau":          "#6366F1",
    "Situ":           "#6366F1",
    "Curug":          "#14B8A6",
    "Taman":          "#84CC16",
    "Lainnya":        "#A78BFA",
}

PALETTE = ["#10B981", "#0EA5E9", "#F97316", "#6366F1", "#14B8A6",
           "#22C55E", "#84CC16", "#38BDF8", "#A78BFA", "#F59E0B"]

STAR_COLOR = "#FBBF24"
STAR_EMPTY = "#E5E7EB"

# Kategori resmi untuk top destinasi
KATEGORI_TOP = [
    "Gunung", "Kawah", "Pantai", "Curug", "Situ", "Taman", "Danau"
]

# Mapping alias kategori dari data ke kategori tampilan
KATEGORI_ALIAS = {
    "gunung":          "Gunung",
    "pegunungan":      "Gunung",
    "pantai":          "Pantai",
    "kawah":           "Kawah",
    "danau":           "Danau",
    "situ":            "Situ",
    "telaga":          "Danau",
    "air terjun":      "Curug",
    "curug":           "Curug",
    "taman nasional":  "Taman",
    "taman":           "Taman",
}

_PLACEHOLDER_CACHE: dict = {}
_CARD_IMG_CACHE: dict = {}  # Cache untuk gambar kartu dari file

# Warna thumbnail per kategori
KATEGORI_THUMB_COLOR = {
    "Pantai":            (14,  165, 233),
    "Gunung":            (16,  185, 129),
    "Kawah":             (249, 115,  22),
    "Danau":             (99,  102, 241),
    "Situ":              (99,  102, 241),
    "Curug":             (20,  184, 166),
    "Taman":             (132, 204,  22),
}

# Path root proyek (sama dengan _ROOT di atas)
_UPLOADS_DIR = os.path.join(_ROOT, "assets", "uploads")


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


def _load_card_thumbnail(foto_nama: str, w: int, h: int, fallback_hue: tuple) -> ctk.CTkImage:
    """
    Muat gambar dari assets/uploads/ untuk thumbnail kartu.
    Jika foto_nama == 'default.png' atau file tidak ditemukan, gunakan placeholder warna.
    Gambar di-crop center dan di-resize agar pas di kartu.
    """
    if not foto_nama or foto_nama == "default.png":
        return _make_placeholder(w, h, fallback_hue)

    cache_key = (foto_nama, w, h)
    if cache_key in _CARD_IMG_CACHE:
        return _CARD_IMG_CACHE[cache_key]

    path = os.path.join(_UPLOADS_DIR, foto_nama)
    if not os.path.exists(path):
        return _make_placeholder(w, h, fallback_hue)

    try:
        img = Image.open(path).convert("RGB")
        # Center crop agar rasio pas dengan kartu
        img_w, img_h = img.size
        target_ratio = w / h
        img_ratio = img_w / img_h
        if img_ratio > target_ratio:
            # Gambar lebih lebar — crop horizontal
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, img_h))
        else:
            # Gambar lebih tinggi — crop vertikal
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            img = img.crop((0, top, img_w, top + new_h))
        img = img.resize((w, h), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
        _CARD_IMG_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception:
        return _make_placeholder(w, h, fallback_hue)


def _star_row(parent, rating: float):
    full = int(rating)
    row  = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(anchor="w", pady=(4, 0))
    for i in range(5):
        col = STAR_COLOR if i < full else STAR_EMPTY
        ctk.CTkLabel(row, text="★", font=ctk.CTkFont(size=13), text_color=col).pack(side="left")
    ctk.CTkLabel(row, text=f"  {rating:.1f}", font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=C["txt"]).pack(side="left", padx=(4, 0))


def _get_foto_from_raw(raw_data) -> str:
    """Ambil nama file foto dari data raw wisata."""
    if not raw_data or not isinstance(raw_data, dict):
        return "default.png"
    foto = raw_data.get("identitas", {}).get("foto", "default.png")
    # foto bisa berupa list (multi-foto dari scraping) atau string tunggal
    if isinstance(foto, list):
        return foto[0] if foto else "default.png"
    return foto or "default.png"


def _destination_card(parent, name, rating, category, thumb, ulasan=0, foto_nama=""):
    """Kartu destinasi dengan desain yang lebih rapi. Menampilkan foto jika tersedia."""
    # Jika ada foto asli, gunakan gambar tersebut sebagai thumbnail
    if foto_nama and foto_nama != "default.png":
        kat_key = category.split("/")[0].strip()
        fallback_hue = KATEGORI_THUMB_COLOR.get(kat_key,
                           KATEGORI_THUMB_COLOR.get(category, (100, 100, 100)))
        thumb = _load_card_thumbnail(foto_nama, 195, 115, fallback_hue)

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
    - Kartu per kategori: Gunung, Kawah, Pantai, dll.
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
        return grouped

    def _is_single_category_mode(self) -> bool:
        """Cek apakah semua item di top_list berasal dari kategori tampilan yang sama."""
        if len(self._top_list) <= 1:
            return False
        display_kats = set()
        for item in self._top_list:
            tipe = item.get("kategori", item.get("tipe", ""))
            display_kats.add(self._get_kategori_display(tipe))
        return len(display_kats) == 1

    def _build(self):
        single_mode = self._is_single_category_mode()

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

        if single_mode:
            # ── Mode kategori spesifik: render semua item sebagai kartu individual ──
            sorted_items = sorted(self._top_list,
                                  key=lambda x: float(x.get("rating", 0) or 0),
                                  reverse=True)
            for i, item in enumerate(sorted_items):
                tipe = item.get("kategori", item.get("tipe", ""))
                kat = self._get_kategori_display(tipe)
                hue = KATEGORI_THUMB_COLOR.get(kat, (100, 100, 100))
                thumb = _make_placeholder(195, 115, hue)
                raw_data = item.get("_raw")
                foto = _get_foto_from_raw(raw_data)
                card = _destination_card(
                    self._scroll_frame,
                    name=item.get("nama", "-"),
                    rating=float(item.get("rating", 0) or 0),
                    category=kat,
                    thumb=thumb,
                    ulasan=item.get("jumlah_ulasan", 0),
                    foto_nama=foto,
                )
                if raw_data and self._nav_detail:
                    self._bind_click_recursive(card, raw_data)
                card.pack(side="left", padx=(0 if i == 0 else 10, 0))
        else:
            # ── Mode default: render 1 terbaik per kategori ──
            grouped = self._group_by_kategori()
            for i, kat in enumerate(KATEGORI_TOP):
                items = grouped.get(kat, [])
                hue   = KATEGORI_THUMB_COLOR.get(kat, (100, 100, 100))
                thumb = _make_placeholder(195, 115, hue)

                if items:
                    best = max(items, key=lambda x: float(x.get("rating", 0) or 0))
                    raw_data = best.get("_raw")
                    foto = _get_foto_from_raw(raw_data)
                    card = _destination_card(
                        self._scroll_frame,
                        name=best.get("nama", kat),
                        rating=float(best.get("rating", 0) or 0),
                        category=kat,
                        thumb=thumb,
                        ulasan=best.get("jumlah_ulasan", 0),
                        foto_nama=foto,
                    )
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
            data_stats["_raw_data"] = raw_data
            self._result_queue.put(("ok", metrik_data, data_stats))
        except Exception as exc:
            self._result_queue.put(("err", str(exc)))

    def _poll_result(self):
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

    def _render_all(self, metrik_data, data_stats):
        """Render semua bagian dashboard ke scroll area — bertahap agar UI tidak freeze."""
        # Tahap 1: render bagian ringan dulu (hero + metrik + top destinasi)
        self._render_hero()
        self._render_metrik(metrik_data)
        self._render_top_destinasi_section(metrik_data, data_stats)

        # Update status sementara agar user tahu proses berjalan
        n = metrik_data["total_wisata"]
        self._lbl_status.configure(text=f"Merender grafik… ({n} destinasi)")
        self.update_idletasks()

        # Tahap 2: render chart berat secara bertahap dengan after()
        self.after(50, lambda: self._render_stage2(metrik_data, data_stats))

    def _render_stage2(self, metrik_data, data_stats):
        """Render chart distribusi (bar + donut) — tahap 2."""
        self._render_distribution_charts(metrik_data, data_stats)
        self.update_idletasks()
        self.after(50, lambda: self._render_stage3(metrik_data, data_stats))

    def _render_stage3(self, metrik_data, data_stats):
        """Render chart kabupaten & finalisasi — tahap 3."""
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
        """Header + dropdown filter kategori & kota + kartu scroll horizontal dengan tombol panah."""
        header_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        header_frame.pack(fill="x", padx=28, pady=(20, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header_frame, text="Top Destinasi per Kategori",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=C["txt"], anchor="w").grid(row=0, column=0, sticky="w")

        # Dropdown filter kategori
        kategori_values = ["Semua Kategori"] + list(KATEGORI_TOP)
        self._filter_kategori_var = ctk.StringVar(value="Semua Kategori")
        filter_kategori = ctk.CTkOptionMenu(
            header_frame,
            variable=self._filter_kategori_var,
            values=kategori_values,
            fg_color=C["card"],
            button_color=C["teal"],
            text_color=C["txt"],
            dropdown_fg_color=C["card"],
            width=180,
            command=self._on_filter_changed
        )
        filter_kategori.grid(row=0, column=1, padx=(12, 0), sticky="e")

        # Dropdown filter kota
        raw_data = data_stats.get("_raw_data", [])
        kota_values = ["Semua Kota / Kabupaten"] + sorted(DAFTAR_KAB_KOTA_JABAR)

        self._filter_kota_var = ctk.StringVar(value="Semua Kota / Kabupaten")
        filter_kota = ctk.CTkOptionMenu(
            header_frame,
            variable=self._filter_kota_var,
            values=kota_values,
            fg_color=C["card"],
            button_color=C["teal"],
            text_color=C["txt"],
            dropdown_fg_color=C["card"],
            width=190,
            command=self._on_filter_changed
        )
        filter_kota.grid(row=0, column=2, padx=(12, 0), sticky="e")

        self._cached_metrik = metrik_data
        self._cached_raw    = raw_data

        self._top_container = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._top_container.pack(fill="x", padx=28, pady=(0, 4))

        top_list = metrik_data.get("top_destinasi", [])
        self._render_top_cards(top_list)

    def _on_filter_changed(self, _pilihan: str = ""):
        """Callback gabungan saat dropdown kategori atau kota berubah — filter top destinasi."""
        raw = self._cached_raw
        pilihan_kota = self._filter_kota_var.get()
        pilihan_kategori = self._filter_kategori_var.get()

        def get_rating(item):
            try:
                return float(item.get("identitas", {}).get("rating") or item.get("rating") or 0)
            except (ValueError, TypeError):
                return 0.0

        def get_kategori_display(item):
            idn = item.get("identitas", item)
            tipe = idn.get("tipe") or idn.get("kategori") or "Umum"
            key = tipe.lower().strip()
            return KATEGORI_ALIAS.get(key, tipe)

        # Filter berdasarkan kota
        if pilihan_kota == "Semua Kota / Kabupaten" or not pilihan_kota:
            pool = list(raw)
        else:
            pool = []
            for item in raw:
                alamat = item.get("identitas", {}).get("alamat", "")
                raw_kab = item.get("kabupaten") or alamat
                kota = get_official_kabupaten(raw_kab)
                if kota == pilihan_kota:
                    pool.append(item)

        # Filter berdasarkan kategori
        if pilihan_kategori == "Semua Kategori" or not pilihan_kategori:
            if pilihan_kota == "Semua Kota / Kabupaten" or not pilihan_kota:
                top_list = self._cached_metrik.get("top_destinasi", [])
            else:
                top_list = []
                seen_kat: set = set()
                sorted_pool = sorted(pool, key=get_rating, reverse=True)
                for item in sorted_pool:
                    idn = item.get("identitas", item)
                    kat = idn.get("tipe") or idn.get("kategori") or "Umum"
                    if kat not in seen_kat:
                        seen_kat.add(kat)
                        top_list.append({
                            "nama":         idn.get("nama", "-"),
                            "rating":       get_rating(item),
                            "kategori":     kat,
                            "jumlah_ulasan": int(idn.get("jumlah_ulasan") or 0),
                            "_raw":         item,
                        })
        else:
            kategori_terpilih = pilihan_kategori
            filtered_items = []
            for item in pool:
                kat_display = get_kategori_display(item)
                if kat_display == kategori_terpilih:
                    idn = item.get("identitas", item)
                    filtered_items.append({
                        "nama":         idn.get("nama", "-"),
                        "rating":       get_rating(item),
                        "kategori":     idn.get("tipe") or idn.get("kategori") or "Umum",
                        "jumlah_ulasan": int(idn.get("jumlah_ulasan") or 0),
                        "_raw":         item,
                    })
            top_list = sorted(filtered_items, key=lambda x: float(x.get("rating", 0)), reverse=True)

        for w in self._top_container.winfo_children():
            w.destroy()
        self._render_top_cards(top_list)

    def _render_top_cards(self, top_list: list):
        TopDestinasScroll(self._top_container, top_list=top_list,
                          navigasi_ke_detail=self._nav_detail).pack(fill="x")

    def _render_distribution_charts(self, metrik_data, data_stats):
        """Bar chart rating + Donut chart kategori — berdampingan."""
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(20, 8))
        row.grid_columnconfigure(0, weight=6)
        row.grid_columnconfigure(1, weight=5)

        # Bar chart rating
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

        # Donut chart kategori
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

        ctk.CTkLabel(wrap_donut, text="Sebaran Destinasi Berdasarkan Kategori",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["txt"], anchor="w").pack(anchor="w", padx=14, pady=(12, 0))

        inner = ctk.CTkFrame(wrap_donut, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        fig_donut = _build_donut_fig(c_labels, c_sizes, c_colors, str(total))
        canvas_donut = FigureCanvasTkAgg(fig_donut, master=inner)
        canvas_donut.draw()
        canvas_donut.get_tk_widget().pack(side="left", fill="y")
        self._canvas_list.append(canvas_donut)

        # Legenda
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

        wrap = ctk.CTkFrame(self._scroll, fg_color=C["card"], corner_radius=14,
                            border_width=1, border_color=C["border"])
        wrap.pack(fill="x", padx=28, pady=(0, 20))

        top_bar = ctk.CTkFrame(wrap, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(14, 4))
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_bar, text="Jumlah Wisata per Kabupaten / Kota",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C["txt"], anchor="w").grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(top_bar, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="e")

        self._kab_scroll = ctk.CTkScrollableFrame(
            wrap, orientation="horizontal",
            fg_color="transparent", height=250,
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["teal"]
        )
        self._kab_scroll.pack(fill="x", padx=8, pady=(0, 8))

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
