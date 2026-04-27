import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from PIL import Image
from src.logic.crud_engine import tambah_data_wisata, update_data_wisata
from src.utils.file_handler import simpan_gambar_ke_lokal

class FormWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_back, mode="Tambah", data=None):
        super().__init__(parent, fg_color="transparent")
        self.callback_back = callback_back
        self.mode = mode
        self.data = data
        self.path_gambar_dipilih = "" 
        
        self.pack(fill="both", expand=True, padx=30, pady=20)
        self.setup_ui()

    def setup_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(header_frame, text="← Kembali", width=80, fg_color="#6B7280", 
                      hover_color="#4B5563", command=self.callback_back).pack(side="left")
        
        ctk.CTkLabel(header_frame, text=f"{self.mode} Destinasi Wisata", font=("Arial", 24, "bold"), text_color="black").pack(side="left", padx=20)

        self.container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        self.container.pack(fill="both", expand=True, padx=5, pady=5)

        idnt = self.data.get('identitas', {}) if self.data else {}
        oper = self.data.get('operasional', {}) if self.data else {}
        jam_data = oper.get('jam_operasional', {})
        addn = self.data.get('informasi_tambahan', {}) if self.data else {}

        self.create_section("IDENTITAS WISATA")

        self.en_nama, self.err_nama = self.create_input("Nama Wisata", idnt.get('nama', ''))
        
        ctk.CTkLabel(self.container, text="Tipe Wisata", font=("Arial", 12), text_color="#4B5563").pack(anchor="w", padx=15)
        self.list_tipe = ["Gunung", "Pantai", "Curug", "Hutan", "Taman", "Lainnya"] 
        self.combo_tipe = ctk.CTkComboBox(self.container, values=self.list_tipe, height=38, command=self.cek_tipe_lainnya)
        self.combo_tipe.pack(fill="x", padx=15, pady=(2, 10))
        
        self.en_tipe_manual = ctk.CTkEntry(self.container, placeholder_text="Masukkan tipe lainnya...", height=38)
        tipe_lama = idnt.get('tipe', 'Gunung')
        if tipe_lama in self.list_tipe:
            self.combo_tipe.set(tipe_lama)
        else:
            self.combo_tipe.set("Lainnya")
            self.en_tipe_manual.pack(fill="x", padx=15, pady=(0, 10))
            self.en_tipe_manual.insert(0, tipe_lama)

        self.en_alamat, self.err_alamat = self.create_input("Alamat Lengkap", idnt.get('alamat', ''))
        self.en_maps, self.err_maps = self.create_input("Link Google Maps (Opsional)", idnt.get('maps', ''))
        self.en_rate, self.err_rate = self.create_input("Rating (0.0 - 5.0)", idnt.get('rating', ''))

        self.create_section("MEDIA VISUAL")
        foto_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        foto_frame.pack(fill="x", padx=15, pady=5)
        
        foto_saat_ini = idnt.get('foto', '')
        if self.mode == "Edit" and foto_saat_ini and foto_saat_ini != "default.png":
            teks_status = f"Terpilih: {foto_saat_ini}"
            warna_teks = "#10B981"
        else:
            teks_status = "Belum ada foto dipilih"
            warna_teks = "gray"
            
        self.lbl_status_foto = ctk.CTkLabel(foto_frame, text=teks_status, text_color=warna_teks)
        self.lbl_status_foto.pack(side="left")
        ctk.CTkButton(foto_frame, text="📁 Pilih Foto", width=100, command=self.pilih_foto).pack(side="right")

        self.create_section("OPERASIONAL & FASILITAS")
        
        self.en_htm, self.err_htm = self.create_input("Harga Tiket Masuk", oper.get('htm', ''))
        
        ctk.CTkLabel(self.container, text="Hari Operasional", font=("Arial", 12, "bold")).pack(anchor="w", padx=15)
        self.hari_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.hari_frame.pack(fill="x", padx=15, pady=(5,0))
        
        self.hari_vars = {}
        daftar_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        hari_lama = oper.get('hari_buka', [])
        
        for i, hari in enumerate(daftar_hari):
            var = ctk.BooleanVar(value=True if hari in hari_lama else False)
            cb = ctk.CTkCheckBox(self.hari_frame, text=hari, variable=var, width=100)
            cb.grid(row=i//4, column=i%4, pady=5, sticky="w")
            self.hari_vars[hari] = var
            
        self.err_hari = ctk.CTkLabel(self.container, text="", font=("Arial", 10), text_color="red")
        self.err_hari.pack(anchor="w", padx=15, pady=(0, 5))

        ctk.CTkLabel(self.container, text="Jam Operasional", font=("Arial", 12), text_color="#4B5563").pack(anchor="w", padx=15)
        jam_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        jam_frame.pack(fill="x", padx=15, pady=(2, 0))
        
        self.en_jam_buka = ctk.CTkEntry(jam_frame, placeholder_text="Mulai (08:00)", height=38, width=140, border_color="#E5E7EB", border_width=1)
        self.en_jam_buka.pack(side="left", padx=(0, 10))
        self.en_jam_buka.insert(0, jam_data.get('buka', ''))

        ctk.CTkLabel(jam_frame, text="s/d").pack(side="left", padx=5)

        self.en_jam_tutup = ctk.CTkEntry(jam_frame, placeholder_text="Tutup (17:00)", height=38, width=140, border_color="#E5E7EB", border_width=1)
        self.en_jam_tutup.pack(side="left", padx=10)
        self.en_jam_tutup.insert(0, jam_data.get('tutup', ''))
        
        self.err_jam = ctk.CTkLabel(self.container, text="", font=("Arial", 10), text_color="red")
        self.err_jam.pack(anchor="w", padx=15, pady=(0, 5))
        
        ctk.CTkLabel(self.container, text="Fasilitas Tersedia (Opsional)", font=("Arial", 12), text_color="#4B5563").pack(anchor="w", padx=15)
        self.fasilitas_frame = ctk.CTkFrame(self.container, fg_color="#F9FAFB")
        self.fasilitas_frame.pack(fill="x", padx=15, pady=5)
        
        self.check_vars = {}
        opsi_fasilitas = ["Toilet", "Parkir", "Mushola", "Warung", "Gazebo", "Camping Ground"]
        fasilitas_lama = addn.get('fasilitas', [])
        
        for i, f in enumerate(opsi_fasilitas):
            var = ctk.BooleanVar(value=True if f in fasilitas_lama else False)
            cb = ctk.CTkCheckBox(self.fasilitas_frame, text=f, variable=var, font=("Arial", 11))
            cb.grid(row=i//3, column=i%3, padx=20, pady=10, sticky="w")
            self.check_vars[f] = var

        self.create_section("INFORMASI TAMBAHAN")
        ctk.CTkLabel(self.container, text="Kondisi Jalan", font=("Arial", 12), text_color="#4B5563").pack(anchor="w", padx=15)
        self.combo_jalan = ctk.CTkComboBox(self.container, 
                                        values=["Sangat Baik", "Baik", "Cukup", "Rusak Ringan", "Rusak Berat"], 
                                        height=38)
        self.combo_jalan.pack(fill="x", padx=15, pady=(2, 15))
        
        if self.mode == "Edit":
            self.combo_jalan.set(addn.get('kondisi_jalan', 'Baik'))
        else:
            self.combo_jalan.set("Baik")
            
        self.en_jarak, self.err_jarak = self.create_input("Jarak dari Pusat Kota", addn.get('jarak_dari_kab_kota', ''))
        
        ctk.CTkButton(self.container, text="SIMPAN DATA WISATA", height=50, font=("Arial", 16, "bold"), 
                      fg_color="#10B981", hover_color="#059669", command=self.submit_data).pack(pady=40, padx=100, fill="x")

    def cek_tipe_lainnya(self, choice):
        if choice == "Lainnya":
            self.en_tipe_manual.pack(fill="x", padx=15, pady=(0, 10))
        else:
            self.en_tipe_manual.pack_forget()

    def create_section(self, title):
        ctk.CTkLabel(self.container, text=title, font=("Arial", 13, "bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(25, 5))
        ctk.CTkFrame(self.container, height=2, fg_color="#F3F4F6").pack(fill="x", padx=10, pady=(0, 15))

    def create_input(self, label_text, default_value):
        ctk.CTkLabel(self.container, text=label_text, font=("Arial", 12), text_color="#4B5563").pack(anchor="w", padx=15)
        entry = ctk.CTkEntry(self.container, height=38, fg_color="#F9FAFB", border_color="#E5E7EB", border_width=1)
        entry.pack(fill="x", padx=15, pady=(2, 0)) 
        entry.insert(0, str(default_value))

        # Label error 
        lbl_error = ctk.CTkLabel(self.container, text="", font=("Arial", 10), text_color="red")
        lbl_error.pack(anchor="w", padx=15, pady=(0, 10)) 
        return entry, lbl_error 

    def pilih_foto(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if file_path:
            self.path_gambar_dipilih = file_path
            self.lbl_status_foto.configure(text=f"Terpilih: {os.path.basename(file_path)}", text_color="#10B981")

    def submit_data(self):
        is_valid = True

        # Helper internal untuk cek entry yang kosong
        def cek_wajib(entry, label_err):
            nonlocal is_valid
            if not entry.get().strip():
                entry.configure(border_color="red")
                label_err.configure(text="* Wajib diisi")
                is_valid = False
            else:
                entry.configure(border_color="#E5E7EB")
                label_err.configure(text="")

        # Eksekusi pengecekan tiap field
        cek_wajib(self.en_nama, self.err_nama)
        cek_wajib(self.en_alamat, self.err_alamat)
        cek_wajib(self.en_rate, self.err_rate)
        cek_wajib(self.en_htm, self.err_htm)
        cek_wajib(self.en_jarak, self.err_jarak)

        # Cek Jam
        if not self.en_jam_buka.get().strip() or not self.en_jam_tutup.get().strip():
            self.en_jam_buka.configure(border_color="red")
            self.en_jam_tutup.configure(border_color="red")
            self.err_jam.configure(text="* Jam buka dan tutup wajib diisi")
            is_valid = False
        else:
            self.en_jam_buka.configure(border_color="#E5E7EB")
            self.en_jam_tutup.configure(border_color="#E5E7EB")
            self.err_jam.configure(text="")

        # Cek Hari Operasional
        hari_final = [hari for hari, var in self.hari_vars.items() if var.get()]
        if not hari_final:
            self.err_hari.configure(text="* Minimal pilih 1 hari operasional")
            is_valid = False
        else:
            self.err_hari.configure(text="")

        # Ambil data yang nggak butuh validasi merah (Opsional/Combo)
        tipe_final = self.en_tipe_manual.get() if self.combo_tipe.get() == "Lainnya" else self.combo_tipe.get()
        fasilitas_final = [f for f, var in self.check_vars.items() if var.get()]

        # Kalau ada yang nggak valid, hentikan fungsi (jangan simpan)
        if not is_valid:
            messagebox.showwarning("Peringatan", "Masih ada data yang kosong. Silakan periksa kotak berwarna merah!")
            return

        # Jika lolos validasi, buat dict untuk disimpan
        input_mentah = {
            "nama": self.en_nama.get(),
            "rating": self.en_rate.get(),
            "alamat": self.en_alamat.get(),
            "maps": self.en_maps.get(),
            "tipe": tipe_final,
            "htm": self.en_htm.get(),
            "hari_buka": hari_final,
            "jam_mulai": self.en_jam_buka.get(),
            "jam_selesai": self.en_jam_tutup.get(),
            "fasilitas": fasilitas_final, 
            "kondisi_jalan": self.combo_jalan.get(),
            "jarak_dari_kab_kota": self.en_jarak.get()
        }

        try:
            if self.mode == "Edit":
                foto_lama = self.data['identitas'].get('foto', 'default.png')
                update_data_wisata(self.data['id'], input_mentah, self.path_gambar_dipilih, foto_lama)
                messagebox.showinfo("Berhasil", "Data wisata berhasil diupdate!")
            else:
                tambah_data_wisata(input_mentah, self.path_gambar_dipilih)
                messagebox.showinfo("Berhasil", "Data wisata baru berhasil ditambah!")
            
            self.callback_back()
            
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")