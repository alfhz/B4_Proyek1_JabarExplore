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


# ------------------- DROPDOWN CUSTOM DENGAN SCROLL TERBATAS -------------------
class DropdownScroll(ctk.CTkToplevel):
    """Popup dropdown custom dengan tinggi terbatas dan bisa di-scroll."""

    def __init__(self, parent, values, callback, lebar=200, tinggi_max=220):
        super().__init__(parent)

        # sembunyikan title bar dan border window
        self.overrideredirect(True)
        self.configure(fg_color="white")

        # simpan callback untuk dipanggil saat item dipilih
        self.callback = callback

        # hitung posisi popup tepat di bawah tombol yang diklik
        x = parent.winfo_rootx()
        y = parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"{lebar}x{tinggi_max}+{x}+{y}")

        # border tipis di sekeliling dropdown
        border = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=8)
        border.pack(fill="both", expand=True, padx=1, pady=1)

        # area scroll untuk item-item dropdown
        scroll = ctk.CTkScrollableFrame(border, fg_color="white", corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # render tiap item sebagai tombol
        for nilai in values:
            ctk.CTkButton(
                scroll,
                text=nilai,
                anchor="w",
                fg_color="transparent",
                text_color="#374151",
                hover_color="#DEF4CA",
                height=30,
                corner_radius=6,
                command=lambda v=nilai: self._pilih(v)
            ).pack(fill="x", padx=4, pady=1)

        # tutup dropdown jika klik di luar area
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set()

    def _pilih(self, nilai):
        """Panggil callback dengan nilai yang dipilih lalu tutup dropdown."""
        self.callback(nilai)
        self.destroy()


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

        # daftar kab/kota Jawa Barat (hardcode lengkap)
        self.list_kab_kota = [
            "Semua Kota / Kabupaten",
            "Kabupaten Bandung", "Kabupaten Bandung Barat", "Kabupaten Bekasi",
            "Kabupaten Bogor", "Kabupaten Ciamis", "Kabupaten Cianjur",
            "Kabupaten Cirebon", "Kabupaten Garut", "Kabupaten Indramayu",
            "Kabupaten Karawang", "Kabupaten Kuningan", "Kabupaten Majalengka",
            "Kabupaten Pangandaran", "Kabupaten Purwakarta", "Kabupaten Subang",
            "Kabupaten Sukabumi", "Kabupaten Sumedang", "Kabupaten Tasikmalaya",
            "Kota Bandung", "Kota Banjar", "Kota Bekasi", "Kota Bogor",
            "Kota Cimahi", "Kota Cirebon", "Kota Depok",
            "Kota Sukabumi", "Kota Tasikmalaya"
        ]

        # daftar kategori wisata (hardcode sesuai kesepakatan tim)
        self.list_kategori = [
            "Semua Kategori",
            "Gunung", "Kawah", "Pantai", "Curug", "Situ", "Taman", "Danau"
        ]

        # daftar rating grouped: 1.0-1.9, 2.0-2.9, 3.0-3.9, 4.0-4.9, 5.0
        self.list_rating = ["Semua Rating"] + [
            f"{r/10:.1f}" for r in range(10, 20)   # 1.0 - 1.9
        ] + [
            f"{r/10:.1f}" for r in range(20, 30)   # 2.0 - 2.9
        ] + [
            f"{r/10:.1f}" for r in range(30, 40)   # 3.0 - 3.9
        ] + [
            f"{r/10:.1f}" for r in range(40, 50)   # 4.0 - 4.9
        ] + ["5.0"]

        # nilai yang sedang terpilih untuk tiap filter
        self.kota_terpilih = "Semua Kota / Kabupaten"
        self.kategori_terpilih = "Semua Kategori"
        self.rating_terpilih = "Semua Rating"

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

        # search bar
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        self.teks_ui_nama_wisata = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Cari destinasi wisata...",
            height=35, fg_color="white", text_color="black"
        )
        self.teks_ui_nama_wisata.pack(fill="x", expand=True)
        self.teks_ui_nama_wisata.bind("<KeyRelease>", self.proses_filter)

        # Baris dropdown filter kota + kategori + tombol tambah
        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")

        # tombol dropdown kota - pakai dropdown custom scroll terbatas
        _, self.lbl_kota = self.buat_tombol_dropdown(
            combo_frame, "Semua Kota / Kabupaten", 210, self._buka_dropdown_kota
        )
        _.pack(side="left", padx=(0, 10))

        # tombol dropdown kategori - pakai dropdown custom scroll terbatas
        _, self.lbl_kategori = self.buat_tombol_dropdown(
            combo_frame, "Semua Kategori", 160, self._buka_dropdown_kategori
        )
        _.pack(side="left", padx=(0, 10))

        # tombol dropdown rating - pakai dropdown custom scroll terbatas
        _, self.lbl_rating = self.buat_tombol_dropdown(
            combo_frame, "Semua Rating", 150, self._buka_dropdown_rating
        )
        _.pack(side="left", padx=(0, 10))

        # redirect ke halaman form 
        ctk.CTkButton(combo_frame, text="+ Tambah Data", font=("Arial", 12, "bold"), fg_color="#10B981", hover_color="#059669", text_color="white", 
                    command=lambda: self.callback_form("Tambah", None)).pack(side="right")

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

    # ------------------- BUKA DROPDOWN MASING-MASING FILTER -------------------
    def _buka_dropdown_kota(self, tombol):
        """Buka dropdown kota/kabupaten dengan scroll terbatas 10 item."""
        def pilih(nilai):
            self.kota_terpilih = nilai
            self.lbl_kota.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_kab_kota, pilih, lebar=220, tinggi_max=220)

    def _buka_dropdown_kategori(self, tombol):
        """Buka dropdown kategori dengan scroll terbatas."""
        def pilih(nilai):
            self.kategori_terpilih = nilai
            self.lbl_kategori.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_kategori, pilih, lebar=170, tinggi_max=220)

    def _buka_dropdown_rating(self, tombol):
        """Buka dropdown rating grouped dengan scroll terbatas."""
        def pilih(nilai):
            self.rating_terpilih = nilai
            self.lbl_rating.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_rating, pilih, lebar=160, tinggi_max=220)

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

        for item in data_master:
            self.render_kartu_wisata(item)

    # ------------------- PROSES FILTER GABUNGAN -------------------
    def proses_filter(self, event=None):
        """Proses filter berdasarkan search, kota, kategori, dan rating sekaligus."""
        keyword = self.teks_ui_nama_wisata.get().strip().lower()
        pilihan_kota = self.kota_terpilih
        pilihan_kategori = self.kategori_terpilih
        pilihan_rating = self.rating_terpilih

        # ambil semua data
        data_master = buka_json()
        if not data_master:
            return

        hasil = []
        for item in data_master:
            identitas = item.get('identitas', {})
            nama = identitas.get('nama', '').lower()
            alamat = identitas.get('alamat', '')
            tipe = identitas.get('tipe', '')

            try:
                rating = float(identitas.get('rating', 0))
            except:
                rating = 0.0

            # filter search - cari di nama wisata
            if keyword and keyword not in nama:
                continue

            # filter kota/kabupaten - cocokkan dengan field tipe (berisi nama kab/kota)
            if pilihan_kota != "Semua Kota / Kabupaten":
                tipe_kota = identitas.get('tipe', '')
                kota_lower = pilihan_kota.lower()
                # normalisasi: bandingkan tanpa "Kabupaten"/"Kota" prefix
                nama_kota_saja = kota_lower.replace("kabupaten ", "kab. ").replace("kota ", "kota ")
                if kota_lower not in tipe_kota.lower() and nama_kota_saja not in tipe_kota.lower():
                    continue

            # filter kategori
            if pilihan_kategori != "Semua Kategori":
                if tipe.lower() != pilihan_kategori.lower():
                    continue

            # filter rating - exact match
            if pilihan_rating != "Semua Rating":
                try:
                    rating_filter = float(pilihan_rating)
                    # toleransi 0.05 untuk floating point agar 4.6 == 4.6
                    if abs(rating - rating_filter) > 0.05:
                        continue
                except:
                    pass

            hasil.append(item)

        # tampilkan hasil filter
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not hasil:
            self.tampil_pesan_error("Tidak ada data wisata yang sesuai filter")
        else:
            for item in hasil:
                self.render_kartu_wisata(item)

    # proses search (alias ke proses_filter untuk backward compatibility)
    def proses_pencarian(self, event=None):
        # ambil teks dari search bar
        input_user = self.teks_ui_nama_wisata.get().strip()
        
        # kalau bar kosong, balikkan ke tampilan awal (semua data)
        if not input_user:
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

        teks_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        teks_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(teks_frame, text=nama, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        # teks di bawah nama wisata = kategori wisata (Pantai, Gunung, dll), bukan alamat
        kategori_wisata = identitas.get('tipe', '-')
        # jika tipe berisi nama kab/kota (format lama), ambil dari list kategori resmi
        list_kategori_resmi = ["Gunung", "Kawah", "Pantai", "Curug", "Situ", "Taman", "Danau"]
        label_bawah = kategori_wisata if kategori_wisata in list_kategori_resmi else identitas.get('alamat', '-').split(',')[0]
        ctk.CTkLabel(teks_frame, text=label_bawah, font=("Arial", 11), text_color="#6B7280", anchor="w").pack(fill="x")

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