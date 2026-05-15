import customtkinter as ctk
import os
from tkinter import filedialog
from PIL import Image
from src.logic.crud_engine import tambah_data_wisata, update_data_wisata
from src.utils.file_handler import simpan_gambar_ke_lokal
from src.utils.validators import (
    cek_duplikat_nama, cek_angka, cek_rating, 
    cek_ukuran_foto, cek_input_kosong
)

class FormWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_back, mode="Tambah", data=None):
        super().__init__(parent, fg_color="transparent")
        self.callback_back, self.mode, self.data = callback_back, mode, data
        self.temp_photos = []
        self.dict_widgets = {} 
        
        # penampung notifikasi toast aktif
        self.toast_aktif = None

        if (self.mode == "Edit" or self.mode == "Edit Scrape") and self.data:
            f_list = self.data['identitas'].get('foto', [])
            if isinstance(f_list, str):
                f_list = [f_list]
            self.temp_photos = [{"type": "remote", "value": f} for f in f_list if f != "default.png"]

        self.wilayah = ["Kab. Bogor", "Kab. Sukabumi", "Kab. Cianjur", "Kab. Bandung", "Kab. Garut", "Kab. Tasikmalaya", "Kab. Ciamis", "Kab. Kuningan", "Kab. Cirebon", "Kab. Majalengka", "Kab. Sumedang", "Kab. Indramayu", "Kab. Subang", "Kab. Purwakarta", "Kab. Karawang", "Kab. Bekasi", "Kab. Bandung Barat", "Kab. Pangandaran", "Kota Bogor", "Kota Sukabumi", "Kota Bandung", "Kota Cirebon", "Kota Bekasi", "Kota Depok", "Kota Cimahi", "Kota Tasikmalaya", "Kota Banjar"]
        self.kategori = ["Gunung", "Pantai", "Kawah", "Situ", "Curug", "Taman", "Danau"]
        
        self.setup_ui()

    # ------------------- SISTEM NOTIFIKASI TOAST -------------------
    def tampilkan_notif(self, pesan, tipe="success"):
        """nampilin notifikasi melayang di pojok kanan atas ala scraping page."""
        if self.toast_aktif:
            self.toast_aktif.destroy()

        # styling warna pastel sesuai request
        warna_bg = "#D1FAE5" if tipe == "success" else "#FEE2E2"
        warna_txt = "#065F46" if tipe == "success" else "#B91C1C"
        ikon = "✅" if tipe == "success" else "⚠"

        self.toast_aktif = ctk.CTkLabel(
            self, text=f"{ikon}  {pesan}", font=("Arial", 13, "bold"),
            text_color=warna_txt, fg_color=warna_bg, corner_radius=10,
            padx=20, pady=10
        )
        
        self.toast_aktif.place(relx=0.98, rely=0.02, anchor="ne")
        self.after(3000, lambda: self.toast_aktif.destroy() if self.toast_aktif else None)

    def setup_ui(self):
        # header
        header = ctk.CTkFrame(self, fg_color="transparent"); header.pack(fill="x", pady=20)
        ctk.CTkButton(header, text="← Kembali", width=100,
                      font=("Arial", 13, "bold"),
                      fg_color="#DEF4CA", text_color="#3A6B1A", hover_color="#c8ebb0",
                      command=self.callback_back).pack(side="left")
        ctk.CTkLabel(header, text=f"{self.mode} Destinasi", font=("Arial", 24, "bold")).pack(side="left", padx=20)

        # scroll container
        self.container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10); self.container.pack(fill="both", expand=True)
        idnt = self.data.get('identitas', {}) if self.data else {}
        oper = self.data.get('operasional', {}) if self.data else {}
        info_t = self.data.get('informasi_tambahan', {}) if self.data else {}

        # --- 1. section identitas ---
        self.create_section("IDENTITAS")
        
        self.en_nama = self.create_input("Nama Wisata *", idnt.get('nama', ''), "misal: Kawah Putih")
        self.dict_widgets["Nama Wisata *"] = self.en_nama
        
        ctk.CTkLabel(self.container, text="Kategori / Tipe *", font=("Arial", 13)).pack(anchor="w", padx=15)
        self.cb_tipe = ctk.CTkComboBox(self.container, values=self.kategori, height=38, font=("Arial", 13))
        self.cb_tipe.pack(fill="x", padx=15, pady=5)
        self.cb_tipe.set(idnt.get('tipe', 'Gunung')) 
        self.dict_widgets["Kategori / Tipe *"] = self.cb_tipe

        ctk.CTkLabel(self.container, text="Deskripsi *", font=("Arial", 13)).pack(anchor="w", padx=15)
        self.txt_desk = ctk.CTkTextbox(self.container, height=120, border_width=2, font=("Arial", 13))
        self.txt_desk.pack(fill="x", padx=15, pady=5)
        if self.mode == "Edit" or self.mode == "Edit Scrape": 
            self.txt_desk.insert("1.0", idnt.get('deskripsi', ''))
        self.dict_widgets["Deskripsi *"] = self.txt_desk

        alamat = idnt.get('alamat', '')
        parts_alamat = [p.strip() for p in alamat.split(',')] if ',' in alamat else [alamat]
        
        if len(parts_alamat) >= 2:
            if "Jawa Barat" in parts_alamat[-1]:
                kot_v = parts_alamat[-2] if len(parts_alamat) >= 2 else "Kota Bandung"
                det_v = ", ".join(parts_alamat[:-2]) if len(parts_alamat) > 2 else parts_alamat[0]
            else:
                kot_v = parts_alamat[-1]
                det_v = ", ".join(parts_alamat[:-1])
        else:
            kot_v = "Kota Bandung"
            det_v = alamat

        ctk.CTkLabel(self.container, text="Kota/Kabupaten *", font=("Arial", 13)).pack(anchor="w", padx=15)
        self.cb_kota = ctk.CTkComboBox(self.container, values=self.wilayah, height=38, font=("Arial", 13))
        self.cb_kota.pack(fill="x", padx=15, pady=5); self.cb_kota.set(kot_v)
        self.dict_widgets["Kota/Kabupaten *"] = self.cb_kota

        self.en_alamat = self.create_input("Alamat Detail *", det_v, "jl. raya ciwidey no. 1...")
        self.dict_widgets["Alamat Detail *"] = self.en_alamat
        
        self.en_maps = self.create_input("Link Google Maps (Opsional)", idnt.get('maps', ''), "http://maps.google.com/...")
        self.en_rate = self.create_input("Rating (0-5) *", idnt.get('rating', ''), "contoh: 4.5")
        self.dict_widgets["Rating (0-5) *"] = self.en_rate

        # --- 2. section foto ---
        self.create_section("GALERI FOTO")
        f_frame = ctk.CTkFrame(self.container, fg_color="transparent"); f_frame.pack(fill="x", padx=15)
        self.btn_add = ctk.CTkButton(f_frame, text="+ Tambah Foto", font=("Arial", 13, "bold"), command=self.pilih_foto)
        self.btn_add.pack(side="left")
        
        self.galeri = ctk.CTkScrollableFrame(self.container, fg_color="#F3F4F6", orientation="horizontal", height=120)
        self.galeri.pack(fill="x", padx=15, pady=10)
        self.render_galeri()

        # --- 3. section operasional ---
        self.create_section("OPERASIONAL & FASILITAS")
        self.en_htm = self.create_input("HTM (Angka) *", oper.get('htm', ''), "contoh: 25000")
        self.dict_widgets["HTM (Angka) *"] = self.en_htm
        
        ctk.CTkLabel(self.container, text="Jam Operasional *", font=("Arial", 13)).pack(anchor="w", padx=15, pady=(10,0))
        j_frame = ctk.CTkFrame(self.container, fg_color="transparent"); j_frame.pack(fill="x", padx=15, pady=5)
        self.en_buka = ctk.CTkEntry(j_frame, width=110, height=38, border_width=2, font=("Arial", 13), placeholder_text="08:00")
        self.en_buka.pack(side="left")
        if self.mode == "Edit": self.en_buka.insert(0, oper.get('jam_operasional', {}).get('buka', ''))
        self.dict_widgets["Jam Buka *"] = self.en_buka
        
        ctk.CTkLabel(j_frame, text=" s/d ", font=("Arial", 13)).pack(side="left")
        self.en_tutup = ctk.CTkEntry(j_frame, width=110, height=38, border_width=2, font=("Arial", 13), placeholder_text="17:00")
        self.en_tutup.pack(side="left")
        if self.mode == "Edit": self.en_tutup.insert(0, oper.get('jam_operasional', {}).get('tutup', ''))
        self.dict_widgets["Jam Tutup *"] = self.en_tutup

        # fasilitas
        ctk.CTkLabel(self.container, text="Fasilitas Utama", font=("Arial", 13)).pack(anchor="w", padx=15, pady=(15,0))
        self.f_frame = ctk.CTkFrame(self.container, fg_color="transparent"); self.f_frame.pack(fill="x", padx=15, pady=5)
        self.f_vars = {}
        for i, f in enumerate(["Toilet", "Parkir", "Mushola", "Warung", "Gazebo", "Camping Ground"]):
            var = ctk.BooleanVar(value=f in info_t.get('fasilitas', []))
            ctk.CTkCheckBox(self.f_frame, text=f, variable=var, font=("Arial", 13)).grid(row=i//3, column=i%3, padx=10, pady=8, sticky="w")
            self.f_vars[f] = var
        
        self.en_lain = self.create_input("Fasilitas Lainnya (Opsional)", "", "misal: lapangan luas")

        # --- 4. section aksesibilitas ---
        self.create_section("AKSESIBILITAS")
        ctk.CTkLabel(self.container, text="Kondisi Jalan *", font=("Arial", 13)).pack(anchor="w", padx=15)
        self.cb_jalan = ctk.CTkComboBox(self.container, values=["Sangat Baik", "Baik", "Cukup", "Rusak"], height=38, font=("Arial", 13))
        self.cb_jalan.pack(fill="x", padx=15, pady=5)
        self.cb_jalan.set(info_t.get('kondisi_jalan', 'Baik'))
        self.dict_widgets["Kondisi Jalan *"] = self.cb_jalan

        # tombol simpan dengan font besar
        ctk.CTkButton(self.container, text="SIMPAN DATA", height=55, font=("Arial", 15, "bold"), fg_color="#10B981", command=self.submit).pack(pady=40, padx=100, fill="x")

    def render_galeri(self):
        for w in self.galeri.winfo_children(): w.destroy()
        self.btn_add.configure(state="disabled" if len(self.temp_photos) >= 12 else "normal")
        for i, p in enumerate(self.temp_photos):
            box = ctk.CTkFrame(self.galeri, fg_color="white", corner_radius=5); box.pack(side="left", padx=5, pady=5)
            try:
                path = p['value'] if p['type'] == 'local' else os.path.join("assets/uploads", p['value'])
                img = ctk.CTkImage(Image.open(path), size=(75, 75))
                ctk.CTkLabel(box, image=img, text="").pack(pady=2, padx=5)
            except: ctk.CTkLabel(box, text="Err", font=("Arial", 11)).pack()
            ctk.CTkButton(box, text="hapus", width=65, height=22, font=("Arial", 12), fg_color="#EF4444", command=lambda idx=i: self.hapus_f(idx)).pack(pady=2)

    def pilih_foto(self):
        sisa = 12 - len(self.temp_photos)
        paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.png *.webp")])
        for p in paths[:sisa]:
            if cek_ukuran_foto(p): self.temp_photos.append({"type": "local", "value": p})
            else: self.tampilkan_notif("File terlalu besar (Maks 2MB)", "error")
        self.render_galeri()

    def hapus_f(self, idx): self.temp_photos.pop(idx); self.render_galeri()

    def get_widget_value(self, widget):
        if isinstance(widget, ctk.CTkTextbox):
            return widget.get("1.0", "end-1c").strip()
        return widget.get().strip()

    def submit(self):
        data_validasi = {k: self.get_widget_value(v) for k, v in self.dict_widgets.items()}
        kosong = cek_input_kosong(data_validasi)
        
        for widget in self.dict_widgets.values():
            widget.configure(border_color=["#979797", "#565b5e"])

        if kosong:
            for field in kosong:
                self.dict_widgets[field].configure(border_color="#EF4444")
            self.tampilkan_notif(f"Ada {len(kosong)} kolom wajib yang belum diisi!", "error")
            return

        nama, htm, rate = self.en_nama.get().strip(), self.en_htm.get().strip(), self.en_rate.get().strip()
        
        if cek_duplikat_nama(nama, self.data['id'] if self.data else None):
            self.en_nama.configure(border_color="#EF4444")
            self.tampilkan_notif("Nama destinasi wisata sudah terdaftar!", "error"); return
        if not cek_angka(htm):
            self.en_htm.configure(border_color="#EF4444")
            self.tampilkan_notif("HTM harus berupa angka valid!", "error"); return
        if not cek_rating(rate):
            self.en_rate.configure(border_color="#EF4444")
            self.tampilkan_notif("Rating harus berada di angka 0-5!", "error"); return
        if not self.temp_photos:
            self.tampilkan_notif("Minimal unggah 1 foto destinasi!", "error"); return

        final_f = [simpan_gambar_ke_lokal(p['value']) if p['type'] == 'local' else p['value'] for p in self.temp_photos]
        fas = [f for f, v in self.f_vars.items() if v.get()]
        if self.en_lain.get(): fas.extend([x.strip() for x in self.en_lain.get().split(',')])

        input_data = {
            "nama": nama, "deskripsi": self.txt_desk.get("1.0", "end-1c").strip(), "rating": rate,
            "alamat": f"{self.en_alamat.get()}, {self.cb_kota.get()}", 
            "tipe": self.cb_tipe.get(), 
            "htm": htm, "hari_buka": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"],
            "jam_mulai": self.en_buka.get(), "jam_selesai": self.en_tutup.get(), 
            "fasilitas": fas, "kondisi_jalan": self.cb_jalan.get(), "maps": self.en_maps.get().strip()
        }
        
        if self.mode == "Edit":
            update_data_wisata(self.data['id'], input_data, final_f)
            msg = f"Data wisata '{nama}' berhasil diperbarui!"
        elif self.mode == "Edit Scrape":
            if 'identitas' not in self.data: self.data['identitas'] = {}
            if 'operasional' not in self.data: self.data['operasional'] = {}
            if 'informasi_tambahan' not in self.data: self.data['informasi_tambahan'] = {}
            self.data['identitas']['nama'] = input_data['nama']
            self.data['identitas']['deskripsi'] = input_data.get('deskripsi', '')
            self.data['identitas']['rating'] = float(input_data['rating'] or 0)
            self.data['identitas']['alamat'] = input_data['alamat']
            self.data['identitas']['tipe'] = input_data['tipe']
            self.data['identitas']['maps'] = input_data.get('maps', '')
            self.data['identitas']['foto'] = final_f
            self.data['operasional']['htm'] = input_data['htm']
            self.data['operasional']['hari_buka'] = input_data.get('hari_buka', [])
            self.data['operasional']['jam_operasional'] = {"buka": input_data['jam_mulai'], "tutup": input_data['jam_selesai']}
            self.data['informasi_tambahan']['fasilitas'] = input_data.get('fasilitas', [])
            self.data['informasi_tambahan']['kondisi_jalan'] = input_data.get('kondisi_jalan', '')
            msg = f"Hasil scraping '{nama}' berhasil disesuaikan!"
        else:
            tambah_data_wisata(input_data, final_f)
            msg = f"Destinasi '{nama}' berhasil ditambahkan!"
        
        self.tampilkan_notif(msg, "success")
        self.after(500, self.callback_back)

    def create_section(self, t):
        """buat pemisah section dengan font lebih tegas (14)."""
        ctk.CTkLabel(self.container, text=t, font=("Arial", 14, "bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(15, 2))
        ctk.CTkFrame(self.container, height=1, fg_color="#E5E7EB").pack(fill="x", padx=10, pady=5)

    def create_input(self, l, d, p):
        """helper buat input field dengan font label dan entry minimal 13."""
        ctk.CTkLabel(self.container, text=l, font=("Arial", 13)).pack(anchor="w", padx=15)
        e = ctk.CTkEntry(self.container, height=38, border_width=2, font=("Arial", 13), placeholder_text=p)
        e.pack(fill="x", padx=15, pady=5)
        if (self.mode == "Edit" or self.mode == "Edit Scrape") and d: e.insert(0, str(d))
        return e

# backward compatibility alias
form_input_wisata = FormWisata