import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from PIL import Image
from src.logic.crud_engine import tambah_data_wisata, update_data_wisata
from src.utils.file_handler import simpan_gambar_ke_lokal
from src.utils.validators import (
    cek_duplikat_nama, cek_angka, cek_rating, 
    cek_ukuran_foto, cek_input_kosong
)

# modul utama untuk manajemen dan visualisasi formulir input data destinasi wisata
class FormWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_back, mode="Tambah", data=None):
        super().__init__(parent, fg_color="transparent")
        # inisialisasi properti dasar untuk navigasi balik, penentuan mode, dan penampung data
        self.callback_back, self.mode, self.data = callback_back, mode, data
        self.temp_photos = [] # list temporer untuk menyimpan referensi foto sebelum disimpan
        self.dict_widgets = {} # kamus data untuk memetakan label input ke widget masing-masing
        
        # pengecekan mode operasi; jika edit, lakukan ekstraksi data foto yang sudah ada
        if self.mode == "Edit" and self.data:
            f_list = self.data['identitas'].get('foto', [])
            self.temp_photos = [{"type": "remote", "value": f} for f in f_list if f != "default.png"]

        # definisi kumpulan data referensi wilayah kabupaten/kota di jawa barat
        self.wilayah = ["Kab. Bogor", "Kab. Sukabumi", "Kab. Cianjur", "Kab. Bandung", "Kab. Garut", "Kab. Tasikmalaya", "Kab. Ciamis", "Kab. Kuningan", "Kab. Cirebon", "Kab. Majalengka", "Kab. Sumedang", "Kab. Indramayu", "Kab. Subang", "Kab. Purwakarta", "Kab. Karawang", "Kab. Bekasi", "Kab. Bandung Barat", "Kab. Pangandaran", "Kota Bogor", "Kota Sukabumi", "Kota Bandung", "Kota Cirebon", "Kota Bekasi", "Kota Depok", "Kota Cimahi", "Kota Tasikmalaya", "Kota Banjar"]
        
        # definisi kategori destinasi wisata untuk pengelompokan tipe data
        self.kategori = ["Gunung", "Pantai", "Kawah", "Situ", "Curug", "Taman"]
        
        # eksekusi pembangunan elemen antarmuka pengguna
        self.setup_ui()

    def setup_ui(self):
        # pembangunan area header yang mencakup tombol navigasi kembali dan judul modul
        header = ctk.CTkFrame(self, fg_color="transparent"); header.pack(fill="x", pady=20)
        ctk.CTkButton(header, text="← Kembali", width=80, command=self.callback_back).pack(side="left")
        ctk.CTkLabel(header, text=f"{self.mode} Destinasi", font=("Arial", 22, "bold")).pack(side="left", padx=20)

        # inisialisasi kontainer scrollable sebagai area utama pengisian data
        self.container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10); self.container.pack(fill="both", expand=True)
        
        # ekstraksi nilai dari struktur data json jika formulir berada dalam mode edit
        idnt = self.data.get('identitas', {}) if self.data else {}
        oper = self.data.get('operasional', {}) if self.data else {}
        info_t = self.data.get('informasi_tambahan', {}) if self.data else {}

        # --- 1. blok input identitas destinasi ---
        self.create_section("IDENTITAS")
        
        self.en_nama = self.create_input("Nama Wisata *", idnt.get('nama', ''), "misal: Kawah Putih")
        self.dict_widgets["Nama Wisata *"] = self.en_nama
        
        ctk.CTkLabel(self.container, text="Kategori / Tipe *", font=("Arial", 11)).pack(anchor="w", padx=15)
        self.cb_tipe = ctk.CTkComboBox(self.container, values=self.kategori, height=35)
        self.cb_tipe.pack(fill="x", padx=15, pady=5)
        self.cb_tipe.set(idnt.get('tipe', 'Gunung')) 
        self.dict_widgets["Kategori / Tipe *"] = self.cb_tipe

        ctk.CTkLabel(self.container, text="Deskripsi *", font=("Arial", 11)).pack(anchor="w", padx=15)
        self.txt_desk = ctk.CTkTextbox(self.container, height=100, border_width=2)
        self.txt_desk.pack(fill="x", padx=15, pady=5)
        if self.mode == "Edit": self.txt_desk.insert("1.0", idnt.get('deskripsi', ''))
        self.dict_widgets["Deskripsi *"] = self.txt_desk

        alamat = idnt.get('alamat', '')
        det_v = alamat.split(',')[0] if ',' in alamat else alamat
        kot_v = alamat.split(',')[-1].strip() if ',' in alamat else "Kota Bandung"

        ctk.CTkLabel(self.container, text="Kota/Kabupaten *").pack(anchor="w", padx=15)
        self.cb_kota = ctk.CTkComboBox(self.container, values=self.wilayah, height=35)
        self.cb_kota.pack(fill="x", padx=15, pady=5); self.cb_kota.set(kot_v)
        self.dict_widgets["Kota/Kabupaten *"] = self.cb_kota

        self.en_alamat = self.create_input("Alamat Detail *", det_v, "jl. raya ciwidey no. 1...")
        self.dict_widgets["Alamat Detail *"] = self.en_alamat
        
        self.en_maps = self.create_input("Link Google Maps (Opsional)", idnt.get('maps', ''), "https://maps.app.goo.gl/...")
        self.en_rate = self.create_input("Rating (0-5) *", idnt.get('rating', ''), "contoh: 4.5")
        self.dict_widgets["Rating (0-5) *"] = self.en_rate

        # --- 2. blok manajemen galeri foto ---
        self.create_section("GALERI FOTO")
        f_frame = ctk.CTkFrame(self.container, fg_color="transparent"); f_frame.pack(fill="x", padx=15)
        self.btn_add = ctk.CTkButton(f_frame, text="+ Tambah Foto", command=self.pilih_foto); self.btn_add.pack(side="left")
        
        # area tampilan thumbnail foto dengan orientasi horizontal
        self.galeri = ctk.CTkScrollableFrame(self.container, fg_color="#F3F4F6", orientation="horizontal", height=110)
        self.galeri.pack(fill="x", padx=15, pady=10)
        self.render_galeri()

        # --- 3. blok informasi operasional dan fasilitas ---
        self.create_section("OPERASIONAL & FASILITAS")
        self.en_htm = self.create_input("HTM (Angka) *", oper.get('htm', ''), "contoh: 25000")
        self.dict_widgets["HTM (Angka) *"] = self.en_htm
        
        ctk.CTkLabel(self.container, text="Jam Operasional *", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10,0))
        j_frame = ctk.CTkFrame(self.container, fg_color="transparent"); j_frame.pack(fill="x", padx=15, pady=5)
        self.en_buka = ctk.CTkEntry(j_frame, width=100, border_width=2, placeholder_text="08:00")
        self.en_buka.pack(side="left")
        if self.mode == "Edit": self.en_buka.insert(0, oper.get('jam_operasional', {}).get('buka', ''))
        self.dict_widgets["Jam Buka *"] = self.en_buka
        
        ctk.CTkLabel(j_frame, text=" s/d ").pack(side="left")
        self.en_tutup = ctk.CTkEntry(j_frame, width=100, border_width=2, placeholder_text="17:00")
        self.en_tutup.pack(side="left")
        if self.mode == "Edit": self.en_tutup.insert(0, oper.get('jam_operasional', {}).get('tutup', ''))
        self.dict_widgets["Jam Tutup *"] = self.en_tutup

        # manajemen input fasilitas menggunakan komponen checkbox
        ctk.CTkLabel(self.container, text="Fasilitas Utama", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(15,0))
        self.f_frame = ctk.CTkFrame(self.container, fg_color="transparent"); self.f_frame.pack(fill="x", padx=15, pady=5)
        self.f_vars = {}
        for i, f in enumerate(["Toilet", "Parkir", "Mushola", "Warung", "Gazebo", "Camping Ground"]):
            var = ctk.BooleanVar(value=f in info_t.get('fasilitas', []))
            ctk.CTkCheckBox(self.f_frame, text=f, variable=var).grid(row=i//3, column=i%3, padx=10, pady=5, sticky="w"); self.f_vars[f] = var
        
        self.en_lain = self.create_input("Fasilitas Lainnya (Opsional)", "", "misal: lapangan luas")

        # --- 4. blok informasi aksesibilitas jalan ---
        self.create_section("AKSESIBILITAS")
        ctk.CTkLabel(self.container, text="Kondisi Jalan *", font=("Arial", 11)).pack(anchor="w", padx=15)
        self.cb_jalan = ctk.CTkComboBox(self.container, values=["Sangat Baik", "Baik", "Cukup", "Rusak"], height=35)
        self.cb_jalan.pack(fill="x", padx=15, pady=5)
        self.cb_jalan.set(info_t.get('kondisi_jalan', 'Baik'))
        self.dict_widgets["Kondisi Jalan *"] = self.cb_jalan

        # tombol pengiriman dan penyimpanan data
        ctk.CTkButton(self.container, text="SIMPAN DATA", height=50, fg_color="#10B981", command=self.submit).pack(pady=30, padx=100, fill="x")

    def render_galeri(self):
        for w in self.galeri.winfo_children(): w.destroy()
        # limitasi tombol tambah foto jika jumlah file telah mencapai batas maksimal (12)
        self.btn_add.configure(state="disabled" if len(self.temp_photos) >= 12 else "normal")
        for i, p in enumerate(self.temp_photos):
            box = ctk.CTkFrame(self.galeri, fg_color="white", corner_radius=5); box.pack(side="left", padx=5, pady=5)
            try:
                # pemilihan path file berdasarkan asal data (lokal baru atau dari server/uploads)
                path = p['value'] if p['type'] == 'local' else os.path.join("assets/uploads", p['value'])
                img = ctk.CTkImage(Image.open(path), size=(70, 70))
                ctk.CTkLabel(box, image=img, text="").pack(pady=2, padx=5)
            except: ctk.CTkLabel(box, text="Err").pack()
            # penambahan fitur penghapusan item foto dari daftar temporer
            ctk.CTkButton(box, text="hapus", width=60, height=18, fg_color="#EF4444", command=lambda idx=i: self.hapus_f(idx)).pack(pady=2)

    # untuk membuka dialog pemilihan file foto dan menambahkan referensi ke daftar temporer dengan validasi ukuran file
    def pilih_foto(self):
        sisa = 12 - len(self.temp_photos)
        paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.png *.webp")])
        for p in paths[:sisa]:
            if cek_ukuran_foto(p): self.temp_photos.append({"type": "local", "value": p})
            else: messagebox.showwarning("Error", "File kegedean (Maks 2MB)")
        self.render_galeri()

    # untuk menghapus item foto dari daftar temporer berdasarkan indeks dan memperbarui tampilan galeri
    def hapus_f(self, idx): 
        self.temp_photos.pop(idx); self.render_galeri()

    def get_widget_value(self, widget):
        if isinstance(widget, ctk.CTkTextbox):
            return widget.get("1.0", "end-1c").strip()
        return widget.get().strip()

    # prosedur utama untuk validasi input dan penyimpanan data ke dalam dataset json melalui engine crud
    def submit(self):
        data_validasi = {k: self.get_widget_value(v) for k, v in self.dict_widgets.items()}
        kosong = cek_input_kosong(data_validasi) # pengecekan field wajib yang belum terisi
        
        # reset visual warna border widget sebelum melakukan validasi ulang
        for widget in self.dict_widgets.values():
            widget.configure(border_color=["#979797", "#565b5e"])

        if kosong:
            # penandaan visual pada widget yang gagal validasi (kosong)
            for field in kosong:
                self.dict_widgets[field].configure(border_color="#EF4444")
            messagebox.showwarning("Wajib Isi", f"Field wajib diisi:\n- " + "\n- ".join(kosong))
            return

        # pengambilan nilai string untuk field utama yang akan divalidasi lebih lanjut
        nama, htm, rate = self.en_nama.get().strip(), self.en_htm.get().strip(), self.en_rate.get().strip()
        
        # rangkaian pengecekan validitas: duplikasi nama, format numerik, dan rentang rating
        if cek_duplikat_nama(nama, self.data['id'] if self.data else None):
            self.en_nama.configure(border_color="#EF4444")
            messagebox.showerror("Error", "Destinasi wisata sudah terdaftar!"); return
        if not cek_angka(htm):
            self.en_htm.configure(border_color="#EF4444"); messagebox.showerror("Error", "HTM harus berupa angka!"); return
        if not cek_rating(rate):
            self.en_rate.configure(border_color="#EF4444"); messagebox.showerror("Error", "Rating harus angka 0-5!"); return
        if not self.temp_photos:
            messagebox.showwarning("Foto", "Minimal unggah 1 foto!"); return

        # sinkronisasi file foto: konversi path lokal menjadi file permanen di direktori uploads dengan identitas unik
        final_f = [simpan_gambar_ke_lokal(p['value']) if p['type'] == 'local' else p['value'] for p in self.temp_photos]
    
        fas = [f for f, v in self.f_vars.items() if v.get()]
        if self.en_lain.get(): fas.extend([x.strip() for x in self.en_lain.get().split(',')])

        # penyusunan objek dictionary final yang akan dikirim ke engine crud
        input_data = {
            "nama": nama, "deskripsi": self.txt_desk.get("1.0", "end-1c").strip(), "rating": rate,
            "alamat": f"{self.en_alamat.get()}, {self.cb_kota.get()}", 
            "tipe": self.cb_tipe.get(), 
            "htm": htm, "hari_buka": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"],
            "jam_mulai": self.en_buka.get(), "jam_selesai": self.en_tutup.get(), 
            "fasilitas": fas, "kondisi_jalan": self.cb_jalan.get(), "maps": self.en_maps.get().strip()
        }
        
        # pemilihan metode penyimpanan berdasarkan status mode operasi (edit atau tambah baru)
        if self.mode == "Edit": update_data_wisata(self.data['id'], input_data, final_f)
        else: tambah_data_wisata(input_data, final_f)
        
        messagebox.showinfo("Sukses", "Data berhasil diperbarui!"); self.callback_back()

    # fungsi pembantu untuk membuat section header dengan styling khusus agar membedakan dari bagian input biasa
    def create_section(self, t):
        ctk.CTkLabel(self.container, text=t, font=("Arial", 12, "bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(15, 2))
        ctk.CTkFrame(self.container, height=1, fg_color="#E5E7EB").pack(fill="x", padx=10, pady=5)

    # fungsi pembantu untuk membuat input field dengan label dan placeholder, serta memuat data lama jika dalam mode edit
    def create_input(self, l, d, p):
        ctk.CTkLabel(self.container, text=l, font=("Arial", 11)).pack(anchor="w", padx=15)
        e = ctk.CTkEntry(self.container, height=35, border_width=2, placeholder_text=p)
        e.pack(fill="x", padx=15, pady=5)
        if self.mode == "Edit" and d: e.insert(0, str(d))
        return e