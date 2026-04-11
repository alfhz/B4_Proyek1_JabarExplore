import customtkinter as ctk
from src.logic.crud_engine import tambah_data_wisata, update_data_wisata

class FormWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_back, mode="Tambah", data=None):
        super().__init__(parent, fg_color="transparent")
        self.callback_back = callback_back
        self.mode = mode
        self.data = data
        self.pack(fill="both", expand=True, padx=30, pady=20)

        self.setup_ui()

    def setup_ui(self):
        # Header & Tombol Kembali
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(header_frame, text="← Kembali", width=80, fg_color="#6B7280", command=self.callback_back).pack(side="left")
        ctk.CTkLabel(header_frame, text=f"{self.mode} Destinasi Wisata", font=("Arial", 24, "bold"), text_color="black").pack(side="left", padx=20)

        # Scrollable area untuk form
        container = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # Data lama jika mode Edit
        idnt = self.data.get('identitas', {}) if self.data else {}
        oper = self.data.get('operasional', {}) if self.data else {}
        addn = self.data.get('informasi_tambahan', {}) if self.data else {}

        # --- SEKSI 1: IDENTITAS ---
        self.create_section(container, "IDENTITAS")
        self.en_nama = self.create_input(container, "Nama Wisata", idnt.get('nama', ''))
        self.en_tipe = self.create_input(container, "Tipe (Gunung/Pantai/dll)", idnt.get('tipe', ''))
        self.en_alamat = self.create_input(container, "Alamat / Lokasi", idnt.get('alamat', ''))
        self.en_rate = self.create_input(container, "Rating (Angka)", idnt.get('rating', ''))

        # --- SEKSI 2: OPERASIONAL ---
        self.create_section(container, "OPERASIONAL")
        self.en_htm = self.create_input(container, "Harga Tiket (Angka)", oper.get('htm', ''))
        self.en_hari = self.create_input(container, "Hari Buka", oper.get('hari_buka', 'Senin - Minggu'))
        self.en_jam = self.create_input(container, "Jam Operasional", oper.get('jam_buka', '08:00 - 17:00'))

        # --- SEKSI 3: INFORMASI TAMBAHAN ---
        self.create_section(container, "INFORMASI TAMBAHAN")
        self.en_jalan = self.create_input(container, "Kondisi Jalan", addn.get('kondisi_jalan', ''))
        self.en_jarak = self.create_input(container, "Jarak dari Kota", addn.get('jarak_dari_kab_kota', ''))
        
        # Simpan Button
        ctk.CTkButton(container, text="SIMPAN PERUBAHAN", height=45, font=("Arial", 14, "bold"), 
                      fg_color="#10B981", hover_color="#059669", command=self.submit_data).pack(pady=30, padx=100, fill="x")

    def create_section(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=("Arial", 12, "bold"), text_color="#10B981").pack(anchor="w", padx=10, pady=(20, 5))
        ctk.CTkFrame(parent, height=2, fg_color="#E5E7EB").pack(fill="x", padx=10, pady=(0, 10))

    def create_input(self, parent, label, value):
        ctk.CTkLabel(parent, text=label, font=("Arial", 12), text_color="#374151").pack(anchor="w", padx=15)
        entry = ctk.CTkEntry(parent, height=35, fg_color="#F9FAFB", border_color="#E5E7EB")
        entry.pack(fill="x", padx=15, pady=(2, 12))
        entry.insert(0, str(value))
        return entry

    def submit_data(self):
        # Konstruksi JSON sesuai bentuk yang kamu mau
        d_form = {
            "identitas": {
                "nama": self.en_nama.get(),
                "rating": float(self.en_rate.get() or 0),
                "alamat": self.en_alamat.get(),
                "tipe": self.en_tipe.get()
            },
            "operasional": {
                "htm": self.en_htm.get(),
                "hari_buka": self.en_hari.get(),
                "jam_buka": self.en_jam.get()
            },
            "informasi_tambahan": {
                "fasilitas": self.data.get('informasi_tambahan', {}).get('fasilitas', []) if self.data else [],
                "kondisi_jalan": self.en_jalan.get(),
                "jarak_dari_kab_kota": self.en_jarak.get()
            }
        }

        if self.mode == "Edit":
            update_data_wisata(self.data['id'], d_form)
        else:
            tambah_data_wisata(d_form)
        
        self.callback_back() # Balik ke halaman daftar