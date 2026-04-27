# file untuk gui detail wisata - task alfina
import customtkinter as ctk

class DetailWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_kembali, data_wisata):
        super().__init__(parent, fg_color="transparent")
        self.callback_kembali = callback_kembali
        self.data_wisata = data_wisata
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        # konfigurasi responsif
        self.w_kota = 120
        self.w_htm = 110
        self.w_jam = 130
        self.w_rate = 80
        self.w_aksi = 120 

        self.halaman_detail_wisata()

    def halaman_detail_wisata(self):
        # header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        # Tombol Kembali (Biar nggak terjebak di halaman detail)
        ctk.CTkButton(header, text="← Kembali", width=80, 
                        command=self.callback_kembali).pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(header, text="Detail Wisata", font=("Arial", 28, "bold"), 
                        text_color="black").pack(side="left")

        # Tampilkan Nama Wisatanya buat ngetes data masuk
        nama_wisata = self.data_wisata.get('identitas', {}).get('nama', 'Tanpa Nama')
        ctk.CTkLabel(self, text=f"Menampilkan detail untuk: {nama_wisata}", 
                        font=("Arial", 16)).pack(pady=20)