import customtkinter as ctk
import os
from PIL import Image
from tkinter import messagebox
from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json 
from src.utils.validators import format_harga_idr


# ------------------- implementasi komponen dropdown custom -------------------
# kelas untuk mengelola jendela popup dropdown dengan fitur scrollbar
class DropdownScroll(ctk.CTkToplevel):
    def __init__(self, parent, values, callback, lebar=200, tinggi_max=220):
        super().__init__(parent)

        self.overrideredirect(True)
        self.configure(fg_color="white")

        # menyimpan referensi fungsi callback untuk pengembalian nilai terpilih
        self.callback = callback

        # kalkulasi koordinat posisi window agar muncul tepat di bawah komponen induk
        x = parent.winfo_rootx()
        y = parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"{lebar}x{tinggi_max}+{x}+{y}")

        # pembuatan kontainer utama untuk memberikan efek border pada dropdown
        border = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=8)
        border.pack(fill="both", expand=True, padx=1, pady=1)

        # inisialisasi area scrollable untuk menampung daftar entri yang banyak
        scroll = ctk.CTkScrollableFrame(border, fg_color="white", corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # proses iterasi untuk merender setiap opsi sebagai komponen tombol
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
                command=lambda v=nilai: self._pilih(v) # eksekusi fungsi pemilihan
            ).pack(fill="x", padx=4, pady=1)

        # pengaturan penutupan otomatis jendela saat kehilangan fokus (klik di luar area)
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set()

    def _pilih(self, nilai):
        self.callback(nilai)
        self.destroy()


# ------------------- modul utama penampilan daftar data wisata -------------------
class DaftarWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form, self.callback_detail = callback_form, callback_detail
        
        # konfigurasi dimensi lebar kolom untuk menjaga standarisasi tampilan tabel
        self.w_kota = 140
        self.w_harga = 120
        self.w_jam = 150
        self.w_rate = 90
        self.w_aksi = 160

        # koleksi data referensi wilayah kabupaten dan kota untuk kebutuhan filtrasi
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

        # koleksi data kategori destinasi berdasarkan parameter teknis aplikasi
        self.list_kategori = [
            "Semua Kategori",
            "Gunung", "Kawah", "Pantai", "Curug", "Situ", "Taman", "Danau"
        ]

        # pembuatan daftar nilai rating secara sistematis dari interval 1.0 hingga 5.0
        self.list_rating = ["Semua Rating"] + [
            f"{r/10:.1f}" for r in range(10, 20)
        ] + [
            f"{r/10:.1f}" for r in range(20, 30)
        ] + [
            f"{r/10:.1f}" for r in range(30, 40)
        ] + [
            f"{r/10:.1f}" for r in range(40, 50)
        ] + ["5.0"]

        # inisialisasi state awal untuk parameter filter yang aktif
        self.kota_terpilih = "Semua Kota / Kabupaten"
        self.kategori_terpilih = "Semua Kategori"
        self.rating_terpilih = "Semua Rating"

        self.setup_ui()
        self.refresh_tabel()

    # ------------------- prosedur pembangunan komponen antarmuka -------------------
    def buat_tombol_dropdown(self, parent, teks_awal, lebar, callback_buka):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=6,
                             border_width=1, border_color="#E5E7EB", width=lebar, height=35)
        frame.pack_propagate(False)

        # label untuk mendisplay status pilihan filter saat ini
        lbl = ctk.CTkLabel(frame, text=teks_awal, text_color="#374151",
                           font=("Arial", 12), anchor="w")
        lbl.pack(side="left", padx=10, fill="x", expand=True)

        # elemen visual indikator dropdown (panah bawah)
        ctk.CTkLabel(frame, text="▾", text_color="#9CA3AF",
                     font=("Arial", 12), width=20).pack(side="right", padx=6)

        # penambahan event binding untuk pembukaan menu dropdown saat diklik
        frame.bind("<Button-1>", lambda e: callback_buka(frame))
        lbl.bind("<Button-1>", lambda e: callback_buka(frame))

        return frame, lbl

    # prosedur penanganan interaksi untuk masing-masing kategori filter
    def _buka_dropdown_kota(self, tombol):
        def pilih(nilai):
            self.kota_terpilih = nilai
            self.lbl_kota.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_kab_kota, pilih, lebar=220, tinggi_max=220)

    def _buka_dropdown_kategori(self, tombol):
        def pilih(nilai):
            self.kategori_terpilih = nilai
            self.lbl_kategori.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_kategori, pilih, lebar=170, tinggi_max=220)

    def _buka_dropdown_rating(self, tombol):
        def pilih(nilai):
            self.rating_terpilih = nilai
            self.lbl_rating.configure(text=nilai)
            self.proses_filter()
        DropdownScroll(tombol, self.list_rating, pilih, lebar=160, tinggi_max=220)

    def setup_ui(self):
        # bagian header: judul halaman aplikasi
        ctk.CTkLabel(self, text="Kelola Data Wisata", font=("Arial", 28, "bold")).pack(anchor="w", pady=(0, 20))
        
        # kontainer filter yang menampung search bar dan tombol dropdown
        f_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        f_frame.pack(fill="x", pady=(0, 15), ipady=10, ipadx=15)

        # baris pertama: field pencarian teks dan tombol aksi penambahan data
        search_frame = ctk.CTkFrame(f_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.teks_cari = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Cari destinasi wisata...",
            height=40,
            fg_color="white"
        )
        self.teks_cari.pack(side="left", fill="x", expand=True, padx=(0, 15))
        # sinkronisasi otomatis penyaringan data saat terdeteksi input keyboard
        self.teks_cari.bind("<KeyRelease>", self.proses_filter)

        ctk.CTkButton(
            search_frame,
            text="+ Tambah Data",
            font=("Arial", 13, "bold"),
            fg_color="#10B981",
            height=40,
            command=lambda: self.callback_form("Tambah", None)
        ).pack(side="right")

        # baris kedua: penempatan kelompok filter dropdown
        combo_frame = ctk.CTkFrame(f_frame, fg_color="transparent")
        combo_frame.pack(fill="x")

        # inisialisasi tombol filter untuk wilayah
        frame_kota, self.lbl_kota = self.buat_tombol_dropdown(
            combo_frame, "Semua Kota / Kabupaten", 210, self._buka_dropdown_kota
        )
        frame_kota.pack(side="left", padx=(0, 10))

        # inisialisasi tombol filter untuk kategori
        frame_kat, self.lbl_kategori = self.buat_tombol_dropdown(
            combo_frame, "Semua Kategori", 160, self._buka_dropdown_kategori
        )
        frame_kat.pack(side="left", padx=(0, 10))

        # inisialisasi tombol filter untuk rating
        frame_rat, self.lbl_rating = self.buat_tombol_dropdown(
            combo_frame, "Semua Rating", 150, self._buka_dropdown_rating
        )
        frame_rat.pack(side="left", padx=(0, 10))

        # header tabel untuk label identitas kolom
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

        # inisialisasi area scroll untuk penampilan baris data
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    # untuk membuat header kolom dengan styling khusus agar membedakan dari baris data biasa
    def buat_sel_header(self, parent, col, text, width):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=30)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        ctk.CTkLabel(box, text=text, font=("Arial", 11, "bold"), text_color="#4B5563").pack(expand=True)

    def refresh_tabel(self):
        for w in self.scroll.winfo_children(): 
            w.destroy()
            
        # proses pengambilan data dari sumber penyimpanan json
        data = buka_json()
        
        # penanganan kondisi saat dataset dalam keadaan kosong
        if not data:
            ctk.CTkLabel(
                self.scroll, 
                text="Belum ada data wisata.", 
                font=("Arial", 14, "italic"),
                text_color="gray",
                pady=50
            ).pack(expand=True)
            return

        # pengurutan data berdasarkan timestamp modifikasi terbaru secara descending
        data_sorted = sorted(
            data,
            key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')),
            reverse=True
        )
        # iterasi pemanggilan prosedur perenderan untuk setiap baris data
        for item in data_sorted: 
            self.render_row(item)

    # ------------------- logika utama pemrosesan filtrasi data -------------------
    def proses_filter(self, event=None):
        # pengambilan nilai filter aktif dari komponen input dan dropdown
        keyword = self.teks_cari.get().strip().lower()
        pilihan_kota = self.kota_terpilih
        pilihan_kategori = self.kategori_terpilih
        pilihan_rating = self.rating_terpilih

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

            # validasi kesesuaian berdasarkan kata kunci pencarian nama
            if keyword and keyword not in nama:
                continue

            # validasi berdasarkan wilayah kabupaten/kota melalui manipulasi string alamat
            if pilihan_kota != "Semua Kota / Kabupaten":
                alamat_lower = alamat.lower()
                kota_normalized = pilihan_kota.lower().replace("kabupaten ", "kab. ").replace("kota ", "kota ")
                if (kota_normalized + ",") not in alamat_lower and not alamat_lower.endswith(kota_normalized):
                    continue

            # validasi kesesuaian kategori destinasi
            if pilihan_kategori != "Semua Kategori":
                if tipe.lower() != pilihan_kategori.lower():
                    continue

            # validasi berdasarkan nilai rating minimal yang ditetapkan
            if pilihan_rating != "Semua Rating":
                try:
                    rating_min = float(pilihan_rating)
                    if rating < rating_min - 0.05:
                        continue
                except:
                    pass

            # pengumpulan data yang lolos seluruh kriteria filtrasi
            hasil.append(item)

        # pembersihan antarmuka sebelum merender hasil filtrasi baru
        for w in self.scroll.winfo_children():
            w.destroy()

        # penanganan kondisi saat tidak ditemukan data yang sesuai dengan kriteria
        if not hasil:
            ctk.CTkLabel(
                self.scroll,
                text="🔍 Tidak ada data wisata yang sesuai filter",
                font=("Arial", 14, "italic"),
                text_color="#9CA3AF"
            ).pack(pady=60)
            return

        # pengurutan ulang hasil filtrasi untuk disajikan kepada pengguna
        hasil_sorted = sorted(
            hasil,
            key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')),
            reverse=True
        )
        for item in hasil_sorted:
            self.render_row(item)

    def render_row(self, item):
        # pembuatan frame untuk setiap baris data
        row = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=8, border_width=1, border_color="#F3F4F6")
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(0, weight=1)

        idnt = item.get('identitas', {})
        oper = item.get('operasional', {})
        
        # --- representasi visual kolom 0: profil gambar dan identitas nama ---
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        f_nama = idnt.get('foto', ["default.png"])
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

        # --- pemrosesan data teks untuk penampilan informasi spesifik ---
        kota = idnt.get('alamat', '-').split(',')[-1].strip()
        harga = format_harga_idr(oper.get('htm', 0))

        # manipulasi data waktu operasional dari format dictionary ke string display
        jam_data = oper.get('jam_operasional', {})
        buka = jam_data.get('buka', '-')
        tutup = jam_data.get('tutup', '-')
        if isinstance(buka, dict):
            buka = f"{str(buka.get('jam','00')).zfill(2)}:{str(buka.get('menit','00')).zfill(2)}"
        if isinstance(tutup, dict):
            tutup = f"{str(tutup.get('jam','00')).zfill(2)}:{str(tutup.get('menit','00')).zfill(2)}"
        jam = f"{buka} - {tutup}" if jam_data else "-"

        rating = f"★ {idnt.get('rating', '0.0')}"

        # pemetaan teks informasi ke sel tabel masing-masing
        self.buat_sel_teks(row, 1, kota, self.w_kota)
        self.buat_sel_teks(row, 2, harga, self.w_harga, text_color="#10B981", is_bold=True)
        self.buat_sel_teks(row, 3, jam, self.w_jam)
        self.buat_sel_teks(row, 4, rating, self.w_rate, text_color="#F59E0B", is_bold=True)

        # --- pembangunan grup tombol aksi untuk kontrol data ---
        box_aksi = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi, height=40)
        box_aksi.grid(row=0, column=5)
        box_aksi.pack_propagate(False) 
        
        btn_wrap = ctk.CTkFrame(box_aksi, fg_color="transparent")
        btn_wrap.pack(expand=True)

        # tombol interaksi untuk penampilan rincian data
        ctk.CTkButton(
            btn_wrap, text="👁️", width=34, height=34,
            fg_color="transparent", text_color="#10B981", hover_color="#D1FAE5",
            command=lambda: self.callback_detail(item)
        ).pack(side="left", padx=2)
        # tombol interaksi untuk modifikasi data
        ctk.CTkButton(
            btn_wrap, text="✏️", width=34, height=34,
            fg_color="transparent", text_color="#3B82F6", hover_color="#DBEAFE",
            command=lambda: self.callback_form("Edit", item)
        ).pack(side="left", padx=2)
        # tombol interaksi untuk penghapusan entri data
        ctk.CTkButton(
            btn_wrap, text="🗑️", width=34, height=34,
            fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2",
            command=lambda: self._del(idnt.get('nama'), item['id'])
        ).pack(side="left", padx=2)

    # prosedur pembuatan elemen teks pada baris data
    def buat_sel_teks(self, parent, col, text, width, text_color="black", is_bold=False):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=40)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        font_style = ("Arial", 12, "bold") if is_bold else ("Arial", 12)
        ctk.CTkLabel(box, text=text, font=font_style, text_color=text_color).pack(expand=True)
        
    # prosedur penanganan penghapusan data dengan konfirmasi pengguna dan pembaruan tampilan tabel
    def _del(self, n, id_w):
        if messagebox.askyesno("Hapus", f"Yakin ingin menghapus {n}?"):
            hapus_data_wisata(id_w)
            self.refresh_tabel() # pembaharuan tampilan tabel pasca penghapusan