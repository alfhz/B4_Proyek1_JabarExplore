"""
daftar_wisata.py
Halaman daftar destinasi wisata dengan fitur pencarian, filter, dan aksi CRUD.
Optimasi: async image loading, batch rendering, debounce search, cache filter.
"""
import customtkinter as ctk
import os
import threading
from PIL import Image
from tkinter import messagebox
from src.logic.crud_engine import hapus_data_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT
from src.utils.validators import format_harga_idr
from src.logic.search_engine import cari_wisata
from src.logic.filter_engine import filter_destinasi

class DaftarWisata(ctk.CTkFrame):
    """Menampilkan daftar destinasi dalam bentuk kartu dengan aksi edit/hapus/detail."""

    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form = callback_form
        self.callback_detail = callback_detail
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Cache gambar global
        self.image_cache = {}

        # Cache hasil filter
        self.filter_cache = {"key": None, "result": None}
        self.search_timer = None
        self._pending_data = []
        self._render_timer = None

        # Lebar kolom
        self.w_kota = 120
        self.w_htm = 110
        self.w_jam = 130
        self.w_rate = 80
        self.w_aksi = 120

        self.tampilkan_halaman_daftar_wisata()
        self.refresh_tabel()

    # ------------------- LOAD GAMBAR ASYNC -------------------
    def load_image_async(self, path, label, size=(50, 50)):
        """Memuat gambar dari disk di thread terpisah, update UI setelah selesai."""
        if path in self.image_cache:
            label.configure(image=self.image_cache[path], text="")
            return

        def task():
            try:
                img = Image.open(path)
                # Buat thumbnail agar lebih ringan
                img.thumbnail((size[0]*2, size[1]*2), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                self.image_cache[path] = ctk_img
                self.after(0, lambda: label.configure(image=ctk_img, text=""))
            except Exception:
                self.after(0, lambda: label.configure(text="❌", image=None))

        threading.Thread(target=task, daemon=True).start()

    # ------------------- UI HEADER & FILTER -------------------
    def tampilkan_halaman_daftar_wisata(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0,15))
        ctk.CTkLabel(header, text="Kelola Data Wisata", font=("Arial",28,"bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(header, text="Tambah, edit, atau hapus data destinasi wisata Jawa Barat", font=("Arial",14), text_color="#4B5563").pack(anchor="w", pady=(5,0))

        filter_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0,15), ipady=15, ipadx=15)

        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0,10))
        self.teks_ui_nama_wisata = ctk.CTkEntry(search_frame, placeholder_text="🔍 Cari destinasi wisata...", height=35, fg_color="white", text_color="black")
        self.teks_ui_nama_wisata.pack(fill="x", expand=True)
        self.teks_ui_nama_wisata.bind("<KeyRelease>", self.proses_pencarian)

        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")

        self.combo_kota = ctk.CTkComboBox(combo_frame, values=["Semua Kota / Kabupaten"], width=180, fg_color="white", text_color="black")
        self.combo_kota.pack(side="left", padx=(0,10))
        self.combo_kota.bind("<<ComboboxSelected>>", self.proses_pencarian)

        self.combo_kategori = ctk.CTkComboBox(combo_frame, values=["Semua Kategori"], width=150, fg_color="white", text_color="black")
        self.combo_kategori.pack(side="left", padx=10)
        self.combo_kategori.bind("<<ComboboxSelected>>", self.proses_pencarian)

        self.filter_rating_min = ctk.CTkEntry(combo_frame, placeholder_text="Min Rating", width=80, fg_color="white")
        self.filter_rating_min.pack(side="left", padx=10)
        self.filter_rating_min.bind("<KeyRelease>", self.proses_pencarian)
        self.filter_rating_max = ctk.CTkEntry(combo_frame, placeholder_text="Max Rating", width=80, fg_color="white")
        self.filter_rating_max.pack(side="left", padx=10)
        self.filter_rating_max.bind("<KeyRelease>", self.proses_pencarian)
        self.filter_harga_max = ctk.CTkEntry(combo_frame, placeholder_text="Max Harga (Rp)", width=100, fg_color="white")
        self.filter_harga_max.pack(side="left", padx=10)
        self.filter_harga_max.bind("<KeyRelease>", self.proses_pencarian)

        ctk.CTkButton(combo_frame, text="+ Tambah Data", font=("Arial",12,"bold"), fg_color="#10B981", hover_color="#059669", text_color="white",
                    command=lambda: self.callback_form("Tambah", None)).pack(side="right")

        # Header tabel
        table_header = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=5)
        table_header.pack(fill="x", pady=(0,5), ipady=8)
        table_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(table_header, text="NAMA WISATA", font=("Arial",11,"bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=0, sticky="ew", padx=20)
        ctk.CTkLabel(table_header, text="KOTA", width=self.w_kota, font=("Arial",11,"bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(table_header, text="HARGA", width=self.w_htm, font=("Arial",11,"bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(table_header, text="OPERASIONAL", width=self.w_jam, font=("Arial",11,"bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(table_header, text="RATING", width=self.w_rate, font=("Arial",11,"bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=4, sticky="w")
        ctk.CTkLabel(table_header, text="AKSI", width=self.w_aksi).grid(row=0, column=5, sticky="e", padx=20)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

    # ------------------- FILTER & PENCARIAN DENGAN DEBOUNCE -------------------
    def proses_pencarian(self, event=None):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self._do_search)

    def _do_search(self):
        keyword = self.teks_ui_nama_wisata.get().strip()
        kota = self.combo_kota.get()
        kategori = self.combo_kategori.get()
        try:
            rating_min = float(self.filter_rating_min.get()) if self.filter_rating_min.get() else None
        except:
            rating_min = None
        try:
            rating_max = float(self.filter_rating_max.get()) if self.filter_rating_max.get() else None
        except:
            rating_max = None
        try:
            harga_max_str = self.filter_harga_max.get().replace('.','').replace(',','')
            harga_max = int(harga_max_str) if harga_max_str else None
        except:
            harga_max = None

        # Cek cache
        cache_key = (keyword, kota, kategori, rating_min, rating_max, harga_max)
        if self.filter_cache["key"] == cache_key:
            self.refresh_ui(self.filter_cache["result"])
            return

        data_master = buka_json()
        if not data_master:
            self.refresh_ui([])
            return

        self.update_filter_options(data_master)

        filtered = cari_wisata(keyword, data_master)
        filtered = filter_destinasi(filtered, rating_min=rating_min, rating_max=rating_max,
                                    harga_max=harga_max, lokasi=None if kota=="Semua Kota / Kabupaten" else kota)
        if kategori != "Semua Kategori":
            filtered = [item for item in filtered if item.get('identitas',{}).get('tipe','') == kategori]

        # Simpan cache
        self.filter_cache["key"] = cache_key
        self.filter_cache["result"] = filtered
        self.refresh_ui(filtered)

    def update_filter_options(self, data_master):
        kota_set = set()
        kategori_set = set()
        for item in data_master:
            identitas = item.get('identitas', {})
            alamat = identitas.get('alamat', '')
            kota = alamat.split(',')[0] if ',' in alamat else alamat
            if kota:
                kota_set.add(kota)
            tipe = identitas.get('tipe', 'Umum')
            if tipe:
                kategori_set.add(tipe)
        kota_list = sorted(list(kota_set))
        kategori_list = sorted(list(kategori_set))
        current_kota = self.combo_kota.get()
        current_kategori = self.combo_kategori.get()
        self.combo_kota.configure(values=["Semua Kota / Kabupaten"] + kota_list)
        self.combo_kategori.configure(values=["Semua Kategori"] + kategori_list)
        if current_kota not in self.combo_kota.cget("values"):
            self.combo_kota.set("Semua Kota / Kabupaten")
        if current_kategori not in self.combo_kategori.cget("values"):
            self.combo_kategori.set("Semua Kategori")

    # ------------------- BATCH RENDERING (LAZY LOADING) -------------------
    def refresh_ui(self, data_list):
        """Hapus semua widget lalu render bertahap."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        if not data_list:
            ctk.CTkLabel(self.scroll_frame, text="Tidak ada data wisata yang cocok.", text_color="gray").pack(pady=20)
            return
        self._pending_data = data_list.copy()
        self._render_batch(0, 15)  # mulai render 15 item pertama

    def _render_batch(self, start, batch_size):
        """Render item dari start hingga start+batch_size, lalu schedule batch berikutnya."""
        end = min(start + batch_size, len(self._pending_data))
        for i in range(start, end):
            self.render_kartu_wisata(self._pending_data[i])
        if end < len(self._pending_data):
            self.after(50, lambda: self._render_batch(end, batch_size))

    def refresh_tabel(self):
        self.proses_pencarian()

    # ------------------- RENDER SATU KARTU -------------------
    def render_kartu_wisata(self, item):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=5)
        row.pack(fill="x", pady=4, ipady=10)
        row.grid_columnconfigure(0, weight=1)

        identitas = item.get('identitas', {})
        operasional = item.get('operasional', {})

        nama = identitas.get('nama', '-')
        tipe = identitas.get('tipe', 'Umum')
        foto_nama = identitas.get('foto', 'default.png')
        kota = identitas.get('alamat', 'Jawa Barat').split(',')[0]
        jam = operasional.get('jam_buka', '-')
        rating = identitas.get('rating', '0.0')
        htm = format_harga_idr(operasional.get('htm', 0))

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20)

        # Path foto
        path_foto = os.path.join(PROJECT_ROOT, "assets", "uploads", foto_nama)
        if not os.path.exists(path_foto):
            path_foto = os.path.join(PROJECT_ROOT, "assets", "placeholder.png")

        # Label foto dengan placeholder
        lbl_foto = ctk.CTkLabel(info_frame, text="🖼️", width=50, height=50, fg_color="#E5E7EB", corner_radius=5)
        lbl_foto.pack(side="left", padx=(0,10))

        # Load gambar async
        self.load_image_async(path_foto, lbl_foto, size=(50, 50))

        teks_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        teks_frame.pack(side="left", fill="both", expand=True)

        lbl_nama = ctk.CTkLabel(teks_frame, text=nama, font=("Arial",13,"bold"), text_color="#1F2937", wraplength=250, justify="left", anchor="w")
        lbl_nama.pack(fill="x", anchor="w")
        ctk.CTkLabel(teks_frame, text=tipe, font=("Arial",11), text_color="#6B7280", anchor="w").pack(fill="x", anchor="w")

        ctk.CTkLabel(row, text=kota, width=self.w_kota, font=("Arial",12), text_color="#374151", anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row, text=htm, width=self.w_htm, font=("Arial",12), text_color="#374151", anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(row, text=jam, width=self.w_jam, font=("Arial",12), text_color="#374151", anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(row, text=f"⭐ {rating}", width=self.w_rate, font=("Arial",12,"bold"), text_color="#F59E0B", anchor="w").grid(row=0, column=4, sticky="w")

        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi)
        action_frame.grid(row=0, column=5, sticky="e", padx=20)

        ctk.CTkButton(action_frame, text="👁️", width=30, fg_color="transparent", text_color="#10B981", hover_color="#E5E7EB",
                    command=lambda: self.callback_detail(item)).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="✏️", width=30, fg_color="transparent", text_color="#3B82F6", hover_color="#E5E7EB",
                    command=lambda: self.callback_form("Edit", item)).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="🗑️", width=30, fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2",
                    command=lambda: self.notif_konfirmasi(f"Hapus permanen {nama}?", item['id'])).pack(side="left", padx=2)

    def notif_konfirmasi(self, pesan, id_w):
        if messagebox.askyesno("Konfirmasi", pesan):
            hapus_data_wisata(id_w)
            self.refresh_tabel()