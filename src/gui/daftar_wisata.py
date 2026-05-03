"""
daftar_wisata.py
Halaman Kelola Data Wisata untuk aplikasi JabarExplore.
Fitur: tampil tabel, pencarian teks, filter kota & kategori, tambah/edit/hapus.
Optimasi performa: image cache, lazy batch rendering, dan pencarian dari cache data.
"""

import customtkinter as ctk
import os
from tkinter import messagebox
from PIL import Image

from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT
from src.utils.validators import format_harga_idr

# ── Cache gambar & placeholder ────────────────────────────────────────────────
_IMG_CACHE: dict = {}
_IMG_PLACEHOLDER: "ctk.CTkImage | None" = None


def _get_placeholder() -> ctk.CTkImage:
    """Kembalikan gambar placeholder abu-abu 50×50 (dibuat sekali, disimpan)."""
    global _IMG_PLACEHOLDER
    if _IMG_PLACEHOLDER is None:
        img = Image.new("RGB", (50, 50), (229, 231, 235))
        _IMG_PLACEHOLDER = ctk.CTkImage(light_image=img, size=(50, 50))
    return _IMG_PLACEHOLDER


def _load_image(foto_nama: str) -> ctk.CTkImage:
    """
    Muat gambar dari disk dengan cache modul.
    Jika file tidak ditemukan atau gagal dibuka, kembalikan placeholder.
    """
    if foto_nama in _IMG_CACHE:
        return _IMG_CACHE[foto_nama]
    path = os.path.join(PROJECT_ROOT, "assets", "uploads", foto_nama)
    if not os.path.exists(path):
        path = os.path.join(PROJECT_ROOT, "assets", "placeholder.png")
    try:
        img_obj = Image.open(path).convert("RGB")
        # BILINEAR lebih cepat dari LANCZOS untuk thumbnail kecil
        img_obj.thumbnail((50, 50), Image.BILINEAR)
        ctk_img = ctk.CTkImage(light_image=img_obj, size=(50, 50))
        _IMG_CACHE[foto_nama] = ctk_img
        return ctk_img
    except Exception:
        return _get_placeholder()


# ── Helpers ekstraksi data item ───────────────────────────────────────────────

def _get_kota(item: dict) -> str:
    """Ekstrak nama kota/kabupaten dari field alamat atau kabupaten."""
    alamat = item.get("identitas", {}).get("alamat", "") or item.get("kabupaten", "")
    return alamat.split(",")[0].strip() if "," in alamat else alamat.strip()


def _get_kategori(item: dict) -> str:
    """Ekstrak kategori/tipe wisata dari data item."""
    idn = item.get("identitas", item)
    return (idn.get("tipe") or idn.get("kategori") or "Umum").strip()


# ── Kelas utama ───────────────────────────────────────────────────────────────

class DaftarWisata(ctk.CTkFrame):
    """
    Halaman Kelola Data Wisata.
    Data dibaca sekali dari JSON, lalu disimpan di _data_master untuk
    semua operasi filter & pencarian (tanpa buka file berulang kali).
    """

    # Jumlah item yang dirender per frame untuk mencegah freeze UI
    BATCH_SIZE = 15

    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form   = callback_form
        self.callback_detail = callback_detail
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Lebar kolom tabel
        self.w_kota = 120
        self.w_htm  = 110
        self.w_jam  = 130
        self.w_rate = 80
        self.w_aksi = 120

        # State data
        self._data_master: list = []   # semua data dari JSON (tidak berubah kecuali refresh)
        self._data_tampil: list = []   # data yang sedang ditampilkan (hasil filter)
        self._render_idx:  int  = 0    # pointer batch rendering

        self._tampilkan_layout()
        self._muat_data_awal()

    # ─────────────────────── LAYOUT ──────────────────────────────────────────

    def _tampilkan_layout(self):
        """Bangun struktur UI: header, area filter, header tabel, scroll area."""
        # Header judul halaman
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Kelola Data Wisata",
                     font=("Arial", 28, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(header,
                     text="Tambah, edit, atau hapus data destinasi wisata Jawa Barat",
                     font=("Arial", 14), text_color="#4B5563").pack(anchor="w", pady=(5, 0))

        # Area filter & pencarian
        filter_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), ipady=15, ipadx=15)

        # Baris pencarian teks
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        self.teks_ui_nama_wisata = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Cari destinasi wisata...",
            height=35, fg_color="white", text_color="black"
        )
        self.teks_ui_nama_wisata.pack(fill="x", expand=True)
        # Debounce: pencarian dijadwalkan ulang setiap keystroke agar tidak lag
        self._search_after_id = None
        self.teks_ui_nama_wisata.bind("<KeyRelease>", self._on_search_keyrelease)

        # Baris dropdown filter kota + kategori + tombol tambah
        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")

        self.filter_kota = ctk.CTkComboBox(
            combo_frame,
            values=["Semua Kota / Kabupaten"],   # akan diisi setelah data dimuat
            width=190, fg_color="white", text_color="black",
            command=self._terapkan_filter          # dipanggil saat nilai berubah
        )
        self.filter_kota.set("Semua Kota / Kabupaten")
        self.filter_kota.pack(side="left", padx=(0, 10))

        self.filter_kategori = ctk.CTkComboBox(
            combo_frame,
            values=["Semua Kategori"],            # akan diisi setelah data dimuat
            width=160, fg_color="white", text_color="black",
            command=self._terapkan_filter          # dipanggil saat nilai berubah
        )
        self.filter_kategori.set("Semua Kategori")
        self.filter_kategori.pack(side="left", padx=10)

        ctk.CTkButton(
            combo_frame, text="+ Tambah Data",
            font=("Arial", 12, "bold"),
            fg_color="#10B981", hover_color="#059669", text_color="white",
            command=lambda: self.callback_form("Tambah", None)
        ).pack(side="right")

        # 3. HEADER TABEL
        self.h_frame = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=5)
        self.h_frame.pack(fill="x", pady=(10, 5))
        self.h_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.h_frame, text="NAMA WISATA", font=("Arial", 11, "bold"), text_color="#4B5563", anchor="w").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Header kolom data (Lurus tengah)
        self.buat_sel_header(self.h_frame, 1, "KOTA / KAB", self.w_kota)
        self.buat_sel_header(self.h_frame, 2, "HARGA TIKET", self.w_harga)
        self.buat_sel_header(self.h_frame, 3, "JAM OPERASIONAL", self.w_jam)
        self.buat_sel_header(self.h_frame, 4, "RATING", self.w_rate)
        self.buat_sel_header(self.h_frame, 5, "AKSI", self.w_aksi)

        # 4. Scroll Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def buat_sel_header(self, parent, col, text, width):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=30)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        ctk.CTkLabel(box, text=text, font=("Arial", 11, "bold"), text_color="#4B5563").pack(expand=True)

    def urutkan_data_terbaru(self, data):
        def get_latest_date(x):
            d1 = x.get('tanggal_diubah', '') or '0000-00-00'
            d2 = x.get('tanggal_ditambahkan', '') or '0000-00-00'
            return max(d1, d2)
        
        return sorted(data, key=get_latest_date, reverse=True)

    def refresh_tabel(self):
        for w in self.scroll.winfo_children(): 
            w.destroy()
            
        data = buka_json()
        
        if not data:
            ctk.CTkLabel(
                self.scroll, 
                text="Belum ada data wisata nih. Tambah dulu yuk!", 
                font=("Arial", 14, "italic"),
                text_color="gray",
                pady=50
            ).pack(expand=True)
            return

        data_sorted = sorted(data, key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')), reverse=True)
        for item in data_sorted: 
            self.render_row(item)

    def proses_cari(self, event=None):
        query = self.teks_cari.get().strip()
        
        for w in self.scroll.winfo_children(): 
            w.destroy()

        if not query: 
            self.refresh_tabel()
            return

        from src.logic.search_engine import cari_wisata
        hasil = cari_wisata(query, buka_json())

        if not hasil:
            ctk.CTkLabel(
                self.scroll, 
                text="Data yang dicari tidak ditemukan!", 
                font=("Arial", 14, "italic"),
                text_color="gray",
                pady=50
            ).pack(expand=True)
            return

        hasil_sorted = sorted(hasil, key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')), reverse=True)
        
        for item in hasil_sorted: 
            self.render_row(item)
    
    def render_row(self, item):
        row = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=8, border_width=1, border_color="#F3F4F6")
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(0, weight=1)

        idnt = item.get('identitas', {})
        oper = item.get('operasional', {})
        
        # --- KOLOM 0: FOTO & NAMA (Sejajar Kiri) ---
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        f_nama = idnt.get('foto', ["default.png"])[0]
        path = os.path.join("assets/uploads", f_nama)
        if not os.path.exists(path): path = os.path.join("assets", "placeholder.png") 
        try:
            img = ctk.CTkImage(light_image=Image.open(path), size=(50, 50))
            ctk.CTkLabel(c0, image=img, text="").pack(side="left")
        except:
            ctk.CTkFrame(c0, width=50, height=50, fg_color="#E5E7EB").pack(side="left")

        txt_f = ctk.CTkFrame(c0, fg_color="transparent")
        txt_f.pack(side="left", padx=15)
        ctk.CTkLabel(txt_f, text=idnt.get('nama', '-'), font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(txt_f, text=f"Update: {item.get('tanggal_diubah', '-')}", font=("Arial", 9), text_color="#9CA3AF", anchor="w").pack(fill="x")

        # --- KOLOM 1 SAMPAI 4: DATA (Lurus Center) ---
        kota = idnt.get('alamat', '-').split(',')[-1].strip()
        harga = format_harga_idr(oper.get('htm', 0))
        jam = f"{oper.get('jam_operasional', {}).get('buka', '-')} - {oper.get('jam_operasional', {}).get('tutup', '-')}"
        rating = f"★ {idnt.get('rating', '0.0')}"

        self.buat_sel_teks(row, 1, kota, self.w_kota)
        self.buat_sel_teks(row, 2, harga, self.w_harga, text_color="#10B981", is_bold=True)
        self.buat_sel_teks(row, 3, jam, self.w_jam)
        self.buat_sel_teks(row, 4, rating, self.w_rate, text_color="#F59E0B", is_bold=True)

        # --- KOLOM 5: AKSI (Center & Ga Kepotong) ---
        box_aksi = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi, height=40)
        box_aksi.grid(row=0, column=5)
        box_aksi.pack_propagate(False) 
        
        btn_wrap = ctk.CTkFrame(box_aksi, fg_color="transparent")
        btn_wrap.pack(expand=True)

        ctk.CTkButton(btn_wrap, text="👁️", width=34, height=34, fg_color="transparent", text_color="#10B981", 
                      hover_color="#D1FAE5", command=lambda: self.callback_detail(item)).pack(side="left", padx=2)
        ctk.CTkButton(btn_wrap, text="✏️", width=34, height=34, fg_color="transparent", text_color="#3B82F6", 
                      hover_color="#DBEAFE", command=lambda: self.callback_form("Edit", item)).pack(side="left", padx=2)
        ctk.CTkButton(btn_wrap, text="🗑️", width=34, height=34, fg_color="transparent", text_color="#EF4444", 
                      hover_color="#FEE2E2", command=lambda: self._del(idnt.get('nama'), item['id'])).pack(side="left", padx=2)

    def buat_sel_teks(self, parent, col, text, width, text_color="black", is_bold=False):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=40)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        font_style = ("Arial", 12, "bold") if is_bold else ("Arial", 12)
        ctk.CTkLabel(box, text=text, font=font_style, text_color=text_color).pack(expand=True)

    def _del(self, n, id_w):
        if messagebox.askyesno("Hapus", f"Yakin ingin menghapus {n}?"):
            hapus_data_wisata(id_w); self.refresh_tabel()