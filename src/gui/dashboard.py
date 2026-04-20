# src/gui/dashboard.py
"""
src/gui/dashboard.py - lengkap dengan perbaikan
"""
from __future__ import annotations
import sys
import os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageDraw

from src.utils.file_handler import buka_json
from src.logic.stats_logic import buat_dataframe, ambil_metrik_data, ambil_data_stats

C = {
    "bg": "#F3F4F6", "card": "#FFFFFF", "sidebar": "#F9FAFB", "border": "#E5E7EB",
    "teal": "#10B981", "blue": "#3B82F6", "amber": "#F59E0B", "red": "#EF4444",
    "purple": "#8B5CF6", "yellow": "#EAB308", "txt": "#111827", "muted": "#6B7280",
}
PALETTE = ["#10B981", "#34D399", "#6EE7B7", "#059669", "#14B8A6", "#0D9488", "#047857"]
STAR_COLOR = "#FBBF24"
STAR_EMPTY = "#E5E7EB"

def _make_placeholder(w, h, hue):
    img = Image.new("RGB", (w, h), hue)
    draw = ImageDraw.Draw(img)
    for i in range(0, w, 24):
        draw.rectangle((i, h//2, i+12, h), fill=(max(0,hue[0]-15), max(0,hue[1]-10), max(0,hue[2]-5)))
    return ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))

def _star_row(parent, rating):
    full = int(rating)
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(anchor="w", pady=(4,0))
    for i in range(5):
        col = STAR_COLOR if i < full else STAR_EMPTY
        ctk.CTkLabel(row, text="★", font=ctk.CTkFont(size=13), text_color=col).pack(side="left", padx=0)
    ctk.CTkLabel(row, text=f"  {rating}", font=ctk.CTkFont(size=11, weight="bold"), text_color=C["txt"]).pack(side="left", padx=(4,0))

def _destination_card(parent, name, rating, category, thumb, ulasan=0):
    card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"], width=200)
    card.pack_propagate(False)
    ctk.CTkLabel(card, text="", image=thumb).pack(fill="x", padx=8, pady=(8,4))
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=12, pady=(0,10))
    ctk.CTkLabel(body, text=name, font=ctk.CTkFont(size=13, weight="bold"), text_color=C["txt"], anchor="w", wraplength=160).pack(fill="x")
    _star_row(body, rating)
    tag = ctk.CTkFrame(body, fg_color=C["border"], corner_radius=20)
    tag.pack(anchor="w", pady=(6,0))
    ctk.CTkLabel(tag, text=f"  {category}  ", font=ctk.CTkFont(size=10, weight="bold"), text_color=C["teal"]).pack()
    if ulasan:
        ctk.CTkLabel(body, text=f"💬 {ulasan:,} ulasan".replace(",", "."), font=ctk.CTkFont(size=10), text_color=C["muted"]).pack(anchor="w", pady=(4,0))
    return card

def _build_donut_fig(title, labels, sizes, colors, center_text):
    fig = Figure(figsize=(3.4,3.2), dpi=96)
    fig.patch.set_facecolor(C["card"])
    fig.subplots_adjust(left=0.06, right=0.94, top=0.88, bottom=0.10)
    ax = fig.add_subplot(111)
    ax.set_facecolor(C["card"])
    ax.set_title(title, fontsize=10, fontweight="bold", color=C["txt"], pad=8)
    ax.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.42, edgecolor="#FFFFFF", linewidth=2))
    ax.text(0,0, center_text, ha="center", va="center", fontsize=15, fontweight="bold", color=C["teal"])
    ax.axis("equal")
    return fig

def _build_line_fig(labels, values):
    fig = Figure(figsize=(8.5,3.0), dpi=96)
    fig.patch.set_facecolor(C["card"])
    ax = fig.add_subplot(111)
    ax.set_facecolor(C["card"])
    fig.subplots_adjust(left=0.05, right=0.98, top=0.84, bottom=0.24)
    ax.set_title("Jumlah Wisata per Kabupaten/Kota", fontsize=11, fontweight="bold", color=C["txt"], loc="left", pad=10)
    n = len(labels)
    y = np.asarray(values, dtype=float)
    x = np.arange(n, dtype=float)
    if n == 0:
        ymax = 10
    elif n == 1:
        ax.plot(x, y, color=C["purple"], linewidth=2.5, marker="o", markersize=7, markerfacecolor="white", markeredgewidth=2, markeredgecolor=C["purple"])
        ymax = max(float(y[0])*1.28, 1.0)
    else:
        deg = min(3, n-1)
        xi = np.linspace(x.min(), x.max(), max(n*12, 48))
        coeff = np.polyfit(x, y, deg)
        yi = np.polyval(coeff, xi)
        line, = ax.plot(xi, yi, color=C["purple"], linewidth=2.5, antialiased=True, label="Jumlah Wisata")
        ax.plot(x, y, linestyle="none", marker="o", markersize=7, markerfacecolor="white", markeredgewidth=2, markeredgecolor=C["purple"])
        ymax = max(float(y.max())*1.28, 1.0)
        ax.legend(handles=[line], loc="upper right", fontsize=8, facecolor=C["card"], edgecolor=C["border"], labelcolor=C["txt"])
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
        cards = [("Total Destinasi Wisata", str(metrik_data["total_wisata"]), "✈", "#6EE7B7"),
                 ("Rata - rata Rating", str(metrik_data["rata_rating"]), "★", "#6EE7B7")]
        for i, (label, nilai, ikon, _) in enumerate(cards):
            self.grid_columnconfigure(i, weight=1)
            kartu = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["border"])
            kartu.grid(row=0, column=i, padx=(0 if i==0 else 14, 0), sticky="ew")
            kartu.grid_columnconfigure(0, weight=1)
            top = ctk.CTkFrame(kartu, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=20, pady=(18,4))
            top.grid_columnconfigure(0, weight=1)
            badge = ctk.CTkFrame(top, fg_color="#D1FAE5", corner_radius=10, width=40, height=40)
            badge.grid(row=0, column=1, sticky="e")
            badge.grid_propagate(False)
            ctk.CTkLabel(badge, text=ikon, font=ctk.CTkFont(size=18), text_color=C["teal"]).place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(kartu, text=nilai, font=ctk.CTkFont(size=32, weight="bold"), text_color=C["teal"]).grid(row=1, column=0, padx=20, pady=(0,4), sticky="w")
            ctk.CTkLabel(kartu, text=label, font=ctk.CTkFont(size=12), text_color=C["muted"]).grid(row=2, column=0, padx=20, pady=(0,18), sticky="w")

class GrafikSebaranWisata(ctk.CTkFrame):
    def __init__(self, master, data_stats, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._stats = data_stats
        self._canvas_list = []  # PERBAIKAN: ganti dari _canvas
        for c in range(3):
            self.grid_columnconfigure(c, weight=3 if c==0 else 2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._chart_tren_bulanan(0,0)
        self._chart_sebaran_kategori(0,1)
        self._chart_top_rating(0,2)
        self._chart_total_per_kabupaten(1,0)
        self._chart_distribusi_harga(1,1)
        self._chart_total_rating_wisata(1,2)

    def _kartu(self, row, col, title, padtop=0):
        frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        frame.grid(row=row, column=col, padx=(0 if col==0 else 10, 0), pady=(padtop,0) if row>0 else (0,0), sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=C["txt"]).pack(anchor="w", padx=12, pady=(10,2))
        return frame
    def _embed(self, fig, frame):
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=(0,6))
        self._canvas_list.append(canvas)
    def _base_fig(self, w=5, h=3.0):
        fig = Figure(figsize=(w,h), dpi=88)
        fig.patch.set_facecolor(C["card"])
        return fig
    def _style_ax(self, ax):
        ax.set_facecolor(C["card"])
        ax.tick_params(colors=C["muted"], labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor(C["border"])
        ax.grid(axis="y", color=C["border"], linestyle="--", alpha=0.5)
    def _chart_tren_bulanan(self, row, col):
        frame = self._kartu(row, col, "📅  Tren Penambahan Wisata per Bulan")
        tren = self._stats["tren_bulanan"]
        fig = self._base_fig(w=6.2, h=3.0)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.08, right=0.97, top=0.96, bottom=0.20)
        if not tren.empty:
            x = [str(p) for p in tren.index]
            y = tren.values
            ax.fill_between(x, y, alpha=0.18, color=C["teal"])
            ax.plot(x, y, color=C["teal"], lw=2.5, marker="o", ms=6, markerfacecolor=C["teal"], markeredgecolor=C["bg"], markeredgewidth=1.5)
            for xi, yi in zip(x, y):
                ax.annotate(str(yi), (xi, yi), textcoords="offset points", xytext=(0,7), ha="center", fontsize=8, color=C["txt"])
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=28, ha="right")
        self._style_ax(ax)
        ax.set_ylabel("Jumlah", color=C["muted"], fontsize=8)
        ax.grid(axis="x", color=C["border"], linestyle="--", alpha=0.3)
        self._embed(fig, frame)
    def _chart_sebaran_kategori(self, row, col):
        frame = self._kartu(row, col, "🗂  Sebaran Kategori Wisata")
        kat = self._stats["sebaran_kategori"]
        fig = self._base_fig(w=4, h=3.0)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.06)
        if not kat.empty:
            _, texts, autotexts = ax.pie(kat.values, labels=kat.index, colors=PALETTE[:len(kat)], autopct="%1.0f%%", startangle=90, wedgeprops=dict(width=0.54, edgecolor=C["card"], linewidth=2), pctdistance=0.78)
            for t in texts:
                t.set_color(C["txt"]); t.set_fontsize(8)
            for a in autotexts:
                a.set_color("#FFFFFF"); a.set_fontsize(7); a.set_fontweight("bold")
        ax.set_facecolor(C["card"])
        self._embed(fig, frame)
    def _chart_top_rating(self, row, col):
        frame = self._kartu(row, col, "🏆  Top 5 Destinasi Rating Tertinggi")
        top_list = self._stats.get("_top_destinasi", [])
        fig = self._base_fig(w=4, h=3.0)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.32, right=0.94, top=0.96, bottom=0.12)
        if top_list:
            names = [d["nama"][:16]+("…" if len(d["nama"])>16 else "") for d in top_list]
            ratings = [d["rating"] for d in top_list]
            bars = ax.barh(names[::-1], ratings[::-1], color=PALETTE[:len(names)][::-1], height=0.55, edgecolor="none")
            for bar, val in zip(bars, ratings[::-1]):
                ax.text(bar.get_width()+0.02, bar.get_y()+bar.get_height()/2, f"{val:.1f} ⭐", va="center", ha="left", fontsize=8, color=C["txt"])
            ax.set_xlim(0,5.4)
            ax.grid(axis="x", color=C["border"], linestyle="--", alpha=0.4)
        self._style_ax(ax)
        ax.set_xlabel("Rating", color=C["muted"], fontsize=8)
        self._embed(fig, frame)
    def _chart_total_per_kabupaten(self, row, col):
        frame = self._kartu(row, col, "🏙  Total Wisata per Kabupaten/Kota", padtop=10)
        kab = self._stats["total_per_kabupaten"]
        fig = self._base_fig(w=6.2, h=3.0)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.07, right=0.97, top=0.96, bottom=0.24)
        if not kab.empty:
            bars = ax.bar(kab.index, kab.values, color=PALETTE[:len(kab)], width=0.55, edgecolor="none")
            for bar, val in zip(bars, kab.values):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.08, str(val), ha="center", va="bottom", fontsize=9, color=C["txt"], fontweight="bold")
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=25, ha="right", fontsize=8)
        self._style_ax(ax)
        ax.set_ylabel("Jumlah", color=C["muted"], fontsize=8)
        self._embed(fig, frame)
    def _chart_distribusi_harga(self, row, col):
        frame = self._kartu(row, col, "💰  Distribusi Harga Tiket (HTM)", padtop=10)
        harga = self._stats["distribusi_harga"]
        fig = self._base_fig(w=4, h=3.0)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.10, right=0.97, top=0.96, bottom=0.26)
        if not harga.empty:
            bucket_colors = [C["teal"], C["blue"], C["amber"], C["red"]]
            bars = ax.bar(harga.index, harga.values, color=bucket_colors[:len(harga)], width=0.5, edgecolor="none")
            for bar, val in zip(bars, harga.values):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05, str(int(val)), ha="center", va="bottom", fontsize=9, color=C["txt"], fontweight="bold")
            plt.setp(ax.xaxis.get_majorticklabels(), fontsize=7, rotation=8)
        self._style_ax(ax)
        ax.set_ylabel("Jumlah", color=C["muted"], fontsize=8)
        self._embed(fig, frame)
    def _chart_total_rating_wisata(self, row, col):
        frame = self._kartu(row, col, "📈  Total Rating Wisata per Kategori", padtop=10)
        scatter = self._stats["scatter_data"]
        fig = self._base_fig(w=4, h=3.0)
        ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.14, right=0.97, top=0.96, bottom=0.16)
        if scatter:
            cat_list = list({d["kategori"] for d in scatter})
            color_map = {k: PALETTE[i%len(PALETTE)] for i,k in enumerate(cat_list)}
            for cat in cat_list:
                pts = [d for d in scatter if d["kategori"]==cat]
                ax.scatter([d["rating"] for d in pts], [d["ulasan"] for d in pts], c=color_map[cat], s=72, alpha=0.85, edgecolors="#FFFFFF", linewidths=0.9)
            patches = [mpatches.Patch(color=color_map[k], label=k) for k in cat_list]
            ax.legend(handles=patches, fontsize=6, loc="upper left", facecolor=C["card"], edgecolor=C["border"], labelcolor=C["txt"])
            ax.set_xlabel("Rating", color=C["muted"], fontsize=8)
            ax.set_ylabel("Jumlah Ulasan", color=C["muted"], fontsize=8)
        self._style_ax(ax)
        ax.grid(axis="both", color=C["border"], linestyle="--", alpha=0.4)
        self._embed(fig, frame)

class HalamanDashboard(ctk.CTkFrame):
    _THUMB_HUES = [(0,90,80), (20,60,110), (90,70,20), (70,20,80), (10,80,50)]
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self._canvas_list = []
        self._widget_metrik = None
        self._widget_grafik = None
        self._build_header()
        self._build_scroll_area()
        self._build_footer()
        self.after(120, self._jalankan_dashboard)
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=52)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr, text="Ringkasan data wisata", font=ctk.CTkFont(size=13, weight="bold"), text_color=C["muted"]).grid(row=0, column=0, padx=22, pady=8, sticky="w")
        self._btn_refresh = ctk.CTkButton(hdr, text="⟳  Refresh Data", width=130, height=32, corner_radius=8, fg_color=C["teal"], hover_color="#059669", text_color="#FFFFFF", font=ctk.CTkFont(weight="bold", size=12), command=self._jalankan_dashboard)
        self._btn_refresh.grid(row=0, column=2, padx=22, pady=8, sticky="e")
    def _build_scroll_area(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)
    def _build_footer(self):
        ftr = ctk.CTkFrame(self, fg_color=C["sidebar"], corner_radius=0, height=30)
        ftr.grid(row=2, column=0, sticky="ew")
        ftr.grid_propagate(False)
        self._lbl_status = ctk.CTkLabel(ftr, text="Menginisialisasi dashboard…", font=ctk.CTkFont(size=11), text_color=C["muted"])
        self._lbl_status.grid(row=0, column=0, padx=16, pady=4, sticky="w")
    def _jalankan_dashboard(self):
        self._btn_refresh.configure(state="disabled", text="⟳  Memuat…")
        self._lbl_status.configure(text="Memuat data dari file JSON…")
        self.update_idletasks()
        raw_data = buka_json()
        df = buat_dataframe(raw_data)
        metrik_data = ambil_metrik_data(df)
        data_stats = ambil_data_stats(df)
        data_stats["_top_destinasi"] = metrik_data["top_destinasi"]
        for w in self._scroll.winfo_children():
            w.destroy()
        self._canvas_list.clear()
        self._render_hero()
        self._render_metrik(metrik_data)
        self._render_top_destinasi(metrik_data["top_destinasi"])
        self._render_donut_row(metrik_data, data_stats)
        self._render_line_chart(data_stats)
        self._render_grafik_sebaran(data_stats)
        n = metrik_data["total_wisata"]
        self._lbl_status.configure(text=f"✓  Dashboard siap — {n} destinasi wisata termuat  |  data/data_wisata.json")
        self._btn_refresh.configure(state="normal", text="⟳  Refresh Data")
    def _render_hero(self):
        hero = ctk.CTkFrame(self._scroll, fg_color="transparent")
        hero.pack(fill="x", padx=28, pady=(22,6))
        ctk.CTkLabel(hero, text="Welcome To Jabar Explore", font=ctk.CTkFont(size=28, weight="bold"), text_color=C["txt"], anchor="w").pack(fill="x")
        ctk.CTkLabel(hero, text="Jelajahi keindahan wisata Jawa Barat dan temukan destinasi terbaik untuk pengalaman tak terlupakan.", font=ctk.CTkFont(size=13), text_color=C["muted"], anchor="w", justify="left").pack(fill="x", pady=(4,0))
    def _render_metrik(self, metrik_data):
        self._widget_metrik = KartuMetrikDashboard(self._scroll, metrik_data=metrik_data)
        self._widget_metrik.pack(fill="x", padx=28, pady=(12,0))
    def _render_top_destinasi(self, top_list):
        if not top_list:
            return
        ctk.CTkLabel(self._scroll, text="Top Destinasi per Kategori", font=ctk.CTkFont(size=15, weight="bold"), text_color=C["txt"], anchor="w").pack(fill="x", padx=28, pady=(18,8))
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=28)
        n = min(len(top_list),5)
        for i in range(n):
            row.grid_columnconfigure(i, weight=1)
        for i, dest in enumerate(top_list[:5]):
            hue = self._THUMB_HUES[i%len(self._THUMB_HUES)]
            thumb = _make_placeholder(200,110, hue)
            card = _destination_card(row, name=dest.get("nama","-"), rating=dest.get("rating",0.0), category=dest.get("kategori","-"), thumb=thumb, ulasan=dest.get("jumlah_ulasan",0))
            card.grid(row=0, column=i, padx=(0 if i==0 else 8,0), sticky="nsew")
    def _render_donut_row(self, metrik_data, data_stats):
        ctk.CTkLabel(self._scroll, text="Distribusi Data Wisata", font=ctk.CTkFont(size=15, weight="bold"), text_color=C["txt"], anchor="w").pack(fill="x", padx=28, pady=(20,8))
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=28)
        row.grid_columnconfigure((0,1), weight=1)
        total = metrik_data["total_wisata"]
        star_labels = ["5★","4★","3★","2★","1★"]
        star_colors = [C["teal"], C["blue"], C["amber"], C["red"], C["purple"]]
        dist_r = data_stats.get("distribusi_rating")
        if dist_r is not None and hasattr(dist_r, "reindex"):
            dr = dist_r.reindex(range(1,6), fill_value=0).astype(int)
            r_counts = [int(dr.loc[i]) for i in range(5,0,-1)]
        else:
            r_counts = [0,0,0,0,0]
        if sum(r_counts)==0:
            r_pie_labels, r_pie_sizes, r_pie_colors = ["—"], [1], [C["muted"]]
            r_center = "0"
            r_legend_rows = [("—", C["muted"], 0)]
        else:
            r_pie_labels, r_pie_sizes, r_pie_colors = star_labels, r_counts, star_colors
            r_center = str(sum(r_counts))
            r_legend_rows = list(zip(star_labels, star_colors, r_counts))
        kat = data_stats.get("sebaran_kategori")
        if kat is not None and not kat.empty:
            c_labels = list(kat.index)
            c_sizes = [int(v) for v in kat.values]
            c_colors = PALETTE[:len(c_labels)]
        else:
            c_labels, c_sizes, c_colors = ["-"], [1], [C["muted"]]
        datasets = [("Distribusi Rating Wisata", r_pie_labels, r_pie_sizes, r_pie_colors, r_center, r_legend_rows),
                    ("Sebaran Kategori Wisata", c_labels, c_sizes, c_colors, str(total), list(zip(c_labels, c_colors, c_sizes)))]
        for col_idx, (title, labels, sizes, colors, center_txt, legend_rows) in enumerate(datasets):
            fig = _build_donut_fig(title, labels, sizes, colors, center_txt)
            wrap = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
            wrap.grid(row=0, column=col_idx, padx=(0 if col_idx==0 else 12,0), sticky="ew")
            inner = ctk.CTkFrame(wrap, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=8, pady=8)
            canvas = FigureCanvasTkAgg(fig, master=inner)
            canvas.draw()
            canvas.get_tk_widget().pack(side="left")
            self._canvas_list.append(canvas)
            leg = ctk.CTkFrame(inner, fg_color="transparent", width=130)
            leg.pack(side="right", fill="y", padx=(0,12), pady=20)
            if col_idx==0:
                legend_iter = [("Tidak ada data", C["muted"], 0)] if r_center=="0" else [(a,b,c) for a,b,c in legend_rows if c>0]
            else:
                legend_iter = [(a,b,c) for a,b,c in legend_rows if c>0]
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
        wrap = ctk.CTkFrame(self._scroll, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        wrap.pack(fill="x", padx=28, pady=(16,0))
        fig = _build_line_fig(labels, values)
        canvas = FigureCanvasTkAgg(fig, master=wrap)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._canvas_list.append(canvas)

kartu_metrik_dashboard = KartuMetrikDashboard
grafik_sebaran_wisata = GrafikSebaranWisata
dashboard = HalamanDashboard