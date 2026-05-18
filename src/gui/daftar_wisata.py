import customtkinter as ctk
import os
from PIL import Image
from tkinter import messagebox
from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json
from src.utils.validators import format_harga_idr


# ------------------- DROPDOWN CUSTOM DENGAN SCROLL TERBATAS -------------------
class DropdownScroll(ctk.CTkToplevel):
    # Popup dropdown
    def __init__(self, parent, values, callback, lebar=200, tinggi_max=220):
        super().__init__(parent)

        self.overrideredirect(True)
        self.configure(fg_color="white")

        self.callback = callback

        # hitung posisi popup tepat di bawah tombol yang diklik
        x = parent.winfo_rootx()
        y = parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"{lebar}x{tinggi_max}+{x}+{y}")

        border = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=8)
        border.pack(fill="both", expand=True, padx=1, pady=1)

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

        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set()

    def _pilih(self, nilai):
        # Panggil callback dengan nilai yang dipilih lalu tutup dropdown
        self.callback(nilai)
        self.destroy()


class DaftarWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form, self.callback_detail = callback_form, callback_detail
        
        # Lebar kolom 
        self.w_kota = 140
        self.w_harga = 120
        self.w_jam = 150
        self.w_rate = 90
        self.w_aksi = 160

        # daftar kab/kota Jawa Barat
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
            "Gunung", "Kawah", "Pantai", "Curug", "Taman", "Danau"
        ]

        # daftar rating per rentang bintang
        self.list_rating = [
            "Semua Rating",
            "  1.0 – 1.9",
            "  2.0 – 2.9",
            "  3.0 – 3.9",
            "  4.0 – 4.9",
            "  5.0",
        ]

        # nilai yang sedang terpilih untuk tiap filter
        self.kota_terpilih = "Semua Kota / Kabupaten"
        self.kategori_terpilih = "Semua Kategori"
        self.rating_terpilih = "Semua Rating"

        # pagination
        self.halaman_aktif = 0
        self.item_per_halaman = 10

        self.setup_ui()
        self.refresh_tabel()

    # ------------------- BUAT TOMBOL DROPDOWN CUSTOM -------------------
    def buat_tombol_dropdown(self, parent, teks_awal, lebar, callback_buka):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=6,
                             border_width=1, border_color="#E5E7EB", width=lebar, height=35)
        frame.grid_propagate(False)
        frame.pack_propagate(False)

        # label teks nilai terpilih
        lbl = ctk.CTkLabel(frame, text=teks_awal, text_color="#374151",
                           font=("Arial", 12), anchor="w")
        lbl.pack(side="left", padx=10, fill="x", expand=True)

        # ikon panah bawah
        ctk.CTkLabel(frame, text="▾", text_color="#9CA3AF",
                     font=("Arial", 12), width=20).pack(side="right", padx=6)

        # klik tombol → buka dropdown
        frame.bind("<Button-1>", lambda e: callback_buka(frame))
        lbl.bind("<Button-1>", lambda e: callback_buka(frame))

        return frame, lbl

    # ------------------- BUKA DROPDOWN MASING-MASING FILTER -------------------
    def _buka_dropdown_kota(self, tombol):
        # dropdown kota/kabupaten dengan scroll terbatas 
        def pilih(nilai):
            self.kota_terpilih = nilai
            self.lbl_kota.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_kab_kota, pilih, lebar=220, tinggi_max=220)

    def _buka_dropdown_kategori(self, tombol):
        # dropdown kategori dengan scroll terbatas
        def pilih(nilai):
            self.kategori_terpilih = nilai
            self.lbl_kategori.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_kategori, pilih, lebar=170, tinggi_max=220)

    def _buka_dropdown_rating(self, tombol):
        # dropdown rating grouped dengan scroll terbatas
        def pilih(nilai):
            self.rating_terpilih = nilai
            self.lbl_rating.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_rating, pilih, lebar=160, tinggi_max=220)

    def setup_ui(self):
        # Judul Halaman
        ctk.CTkLabel(self, text="Kelola Data Wisata", font=("Arial", 28, "bold")).pack(anchor="w", pady=(0, 20))
        
        # Filter Bar
        f_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        f_frame.pack(fill="x", pady=(0, 15), ipady=10, ipadx=15)

        # baris atas: search bar
        search_frame = ctk.CTkFrame(f_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.teks_cari = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Cari destinasi wisata...",
            height=40,
            fg_color="white"
        )
        self.teks_cari.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.teks_cari.bind("<KeyRelease>", self.proses_filter)

        ctk.CTkButton(
            search_frame,
            text="+ Tambah Data",
            font=("Arial", 13, "bold"),
            fg_color="#10B981",
            height=40,
            command=lambda: self.callback_form("Tambah", None)
        ).pack(side="right")

        # baris bawah: dropdown filter kota, kategori, rating 
        combo_frame = ctk.CTkFrame(f_frame, fg_color="transparent")
        combo_frame.pack(fill="x")
        combo_frame.grid_columnconfigure(0, weight=1)
        combo_frame.grid_columnconfigure(1, weight=1)
        combo_frame.grid_columnconfigure(2, weight=1)

        # tombol dropdown kota
        frame_kota, self.lbl_kota = self.buat_tombol_dropdown(
            combo_frame, "Semua Kota / Kabupaten", 100, self._buka_dropdown_kota
        )
        frame_kota.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # tombol dropdown kategori
        frame_kat, self.lbl_kategori = self.buat_tombol_dropdown(
            combo_frame, "Semua Kategori", 100, self._buka_dropdown_kategori
        )
        frame_kat.grid(row=0, column=1, sticky="ew", padx=5)

        # tombol dropdown rating
        frame_rat, self.lbl_rating = self.buat_tombol_dropdown(
            combo_frame, "Semua Rating", 100, self._buka_dropdown_rating
        )
        frame_rat.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        # HEADER TABEL
        self.h_frame = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=5)
        self.h_frame.pack(fill="x", pady=(10, 5))
        self.h_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            self.h_frame, text="NAMA WISATA",
            font=("Arial", 11, "bold"), text_color="#4B5563", anchor="w"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.buat_sel_header(self.h_frame, 1, "KOTA / KAB", self.w_kota)
        self.buat_sel_header(self.h_frame, 2, "HARGA TIKET", self.w_harga)
        self.buat_sel_header(self.h_frame, 3, "JAM OPERASIONAL", self.w_jam)
        self.buat_sel_header(self.h_frame, 4, "RATING", self.w_rate)
        self.buat_sel_header(self.h_frame, 5, "AKSI", self.w_aksi)

        # Scroll Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Pagination Area
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", pady=(8, 0))

    def buat_sel_header(self, parent, col, text, width):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=30)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        ctk.CTkLabel(box, text=text, font=("Arial", 11, "bold"), text_color="#4B5563").pack(expand=True)

    def refresh_tabel(self):
        # reset ke halaman pertama setiap refresh
        self.halaman_aktif = 0
        data = buka_json()
        
        if not data:
            self._tampilkan_data([])
            return

        data_sorted = sorted(
            data,
            key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')),
            reverse=True
        )
        self._tampilkan_data(data_sorted)

    # ------------------- PROSES FILTER GABUNGAN -------------------
    def proses_filter(self, event=None):
        # Proses filter berdasarkan search, kota, kategori, dan rating sekaligus
        keyword = self.teks_cari.get().strip().lower()
        pilihan_kota = self.kota_terpilih
        pilihan_kategori = self.kategori_terpilih
        pilihan_rating = self.rating_terpilih

        # ambil semua data
        data_master = buka_json()
        if not data_master:
            return

        # --- Search berdasarkan Keyword---
        if keyword:
            # Memanggil fungsi cari_wisata dari modul src.logic.search_engine
            hasil_tahap_1 = cari_wisata(keyword, data_master)
        else:
            hasil_tahap_1 = data_master

        # --- Filter berdasarkan Parameter Dropdown ---
        # Melakukan penyaringan lanjutan terhadap hasil pencarian teks
        hasil = []
        for item in hasil_tahap_1:
            identitas = item.get('identitas', {})
            alamat = identitas.get('alamat', '')
            tipe = identitas.get('tipe', '')

            try:
                rating = float(identitas.get('rating', 0))
            except:
                rating = 0.0

            # filter kota/kabupaten - cocokkan dengan bagian alamat
            if pilihan_kota != "Semua Kota / Kabupaten":
                alamat_lower = alamat.lower()
                kota_normalized = pilihan_kota.lower().replace("kabupaten ", "kab. ").replace("kota ", "kota ")
                # tambah koma atau akhir string sebagai batas kanan
                # agar "kab. bandung" tidak cocok dengan "kab. bandung barat"
                if (kota_normalized + ",") not in alamat_lower and not alamat_lower.endswith(kota_normalized):
                    continue

            # filter kategori
            if pilihan_kategori != "Semua Kategori":
                mapping_kategori = {
                    "Taman": ["taman", "kebun", "kampung"],
                    "Danau": ["danau", "situ"],
                }
                tipe_lower = tipe.lower()
                kategori_lower = pilihan_kategori.lower()
                grup = mapping_kategori.get(pilihan_kategori, [kategori_lower])
                if tipe_lower not in grup:
                    continue

            # filter rating per rentang bintang
            if pilihan_rating != "Semua Rating":
                rentang = {
                    "1.0 – 1.9": (1.0, 1.9),
                    "2.0 – 2.9": (2.0, 2.9),
                    "3.0 – 3.9": (3.0, 3.9),
                    "4.0 – 4.9": (4.0, 4.9),
                    "5.0": (5.0, 5.0),
                }
                batas = rentang.get(pilihan_rating)
                if batas and not (batas[0] <= rating <= batas[1]):
                    continue

            hasil.append(item)

        # tampilkan hasil filter
        if not hasil:
            self._tampilkan_data([])
            return

        hasil_sorted = sorted(
            hasil,
            key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')),
            reverse=True
        )
        # reset ke halaman pertama saat filter berubah
        self.halaman_aktif = 0
        self._tampilkan_data(hasil_sorted)

    # ------------------- PAGINATION -------------------
    def _tampilkan_data(self, data):
        # Tampilkan data sesuai halaman aktif dengan pagination
        self._data_terakhir = data
        self._total_data_terakhir = len(data)

        for w in self.scroll.winfo_children():
            w.destroy()

        if not data:
            ctk.CTkLabel(
                self.scroll,
                text="🔍 Tidak ada data wisata yang sesuai filter",
                font=("Arial", 14, "italic"),
                text_color="#9CA3AF"
            ).pack(pady=60)
            self._render_pagination(0)
            return

        # slice data sesuai halaman aktif
        start = self.halaman_aktif * self.item_per_halaman
        end = min(start + self.item_per_halaman, len(data))
        for item in data[start:end]:
            self.render_row(item)

        self._render_pagination(len(data))

    def _render_pagination(self, total_data):
        # Render tombol navigasi halaman di bawah tabel
        for w in self.pagination_frame.winfo_children():
            w.destroy()

        total_halaman = max(1, -(-total_data // self.item_per_halaman))
        if total_halaman <= 1:
            return

        nav = ctk.CTkFrame(self.pagination_frame, fg_color="transparent")
        nav.pack(anchor="e")

        # tombol prev ‹
        ctk.CTkButton(
            nav, text="‹", width=30, height=30,
            fg_color="#F3F4F6", text_color="#374151", hover_color="#DEF4CA",
            command=lambda: self._ganti_halaman(self.halaman_aktif - 1)
        ).pack(side="left", padx=2)

        # tombol nomor halaman
        for h in range(total_halaman):
            is_aktif = (h == self.halaman_aktif)
            ctk.CTkButton(
                nav, text=str(h + 1), width=30, height=30,
                fg_color="#70A059" if is_aktif else "#F3F4F6",
                text_color="white" if is_aktif else "#374151",
                hover_color="#DEF4CA",
                command=lambda p=h: self._ganti_halaman(p)
            ).pack(side="left", padx=2)

        # tombol next ›
        ctk.CTkButton(
            nav, text="›", width=30, height=30,
            fg_color="#F3F4F6", text_color="#374151", hover_color="#DEF4CA",
            command=lambda: self._ganti_halaman(self.halaman_aktif + 1)
        ).pack(side="left", padx=2)

    def _ganti_halaman(self, halaman):
        # Pindah ke halaman tertentu.
        total_halaman = max(1, -(-self._total_data_terakhir // self.item_per_halaman))
        if 0 <= halaman < total_halaman:
            self.halaman_aktif = halaman
            self._tampilkan_data(self._data_terakhir)

    def render_row(self, item):
        row = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=8, border_width=1, border_color="#F3F4F6")
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(0, weight=1)

        idnt = item.get('identitas', {})
        oper = item.get('operasional', {})
        
        # --- KOLOM 0: FOTO & NAMA (Sejajar Kiri) ---
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        f_nama = idnt.get('foto', ["default.png"])
        # foto bisa berupa list atau string 
        f_nama = f_nama[0] if isinstance(f_nama, list) else f_nama
        path = os.path.join("assets/uploads", f_nama)
        if not os.path.exists(path): 
            path = os.path.join("assets", "placeholder.png") 
        try:
            img = ctk.CTkImage(light_image=Image.open(path), size=(50, 50))
            ctk.CTkLabel(c0, image=img, text="").pack(side="left")
        except:
            ctk.CTkFrame(c0, width=50, height=50, fg_color="#E5E7EB").pack(side="left")

        txt_f = ctk.CTkFrame(c0, fg_color="transparent")
        txt_f.pack(side="left", padx=15)
        ctk.CTkLabel(txt_f, text=idnt.get('nama', '-'), font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(
            txt_f,
            text=f"Update: {item.get('tanggal_diubah', '-')}",
            font=("Arial", 9), text_color="#9CA3AF", anchor="w"
        ).pack(fill="x")

        # --- KOLOM 1 SAMPAI 4: DATA (Lurus Center) ---
        kota = idnt.get('alamat', '-').split(',')[-1].strip()
        harga = format_harga_idr(oper.get('htm', 0))

        # parsing jam operasional (support format dict dan string)
        jam_data = oper.get('jam_operasional', {})
        buka = jam_data.get('buka', '-')
        tutup = jam_data.get('tutup', '-')
        if isinstance(buka, dict):
            buka = f"{str(buka.get('jam','00')).zfill(2)}:{str(buka.get('menit','00')).zfill(2)}"
        if isinstance(tutup, dict):
            tutup = f"{str(tutup.get('jam','00')).zfill(2)}:{str(tutup.get('menit','00')).zfill(2)}"
        jam = f"{buka} - {tutup}" if jam_data else "-"

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

        ctk.CTkButton(
            btn_wrap, text="👁️", width=34, height=34,
            fg_color="transparent", text_color="#10B981", hover_color="#D1FAE5",
            command=lambda: self.callback_detail(item)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_wrap, text="✏️", width=34, height=34,
            fg_color="transparent", text_color="#3B82F6", hover_color="#DBEAFE",
            command=lambda: self.callback_form("Edit", item)
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_wrap, text="🗑️", width=34, height=34,
            fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2",
            command=lambda: self._del(idnt.get('nama'), item['id'])
        ).pack(side="left", padx=2)

    def buat_sel_teks(self, parent, col, text, width, text_color="black", is_bold=False):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=40)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        font_style = ("Arial", 12, "bold") if is_bold else ("Arial", 12)
        ctk.CTkLabel(box, text=text, font=font_style, text_color=text_color).pack(expand=True)

    def _del(self, n, id_w):
        # Menggunakan messagebox standar bawaan kodingan awal
        if messagebox.askyesno("Hapus", f"Yakin ingin menghapus {n}?"):
            hapus_data_wisata(id_w)
            self.refresh_tabel()