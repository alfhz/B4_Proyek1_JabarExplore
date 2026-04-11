import customtkinter as ctk
from src.gui.daftar_wisata import DaftarWisata

ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("green")

class JabarExploreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JabarExplore")
        self.geometry("1100x700")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1) 

        self.setup_sidebar()
        self.setup_main_frame()

        self.tampilkan_daftar_wisata() # nanti ganti jadi dashboard

    def setup_sidebar(self):
        # create sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#F9FAFB")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        # Judul Aplikasi
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="JabarExplore", font=("Arial", 24, "bold"), text_color="#10B981")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        # Tombol Navigasi
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="📊 Dashboard", fg_color="transparent", text_color="black", hover_color="#E5E7EB", anchor="w", command=self.tampilkan_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_daftar_wisata = ctk.CTkButton(self.sidebar_frame, text="📋 Kelola Data Wisata", fg_color="transparent", text_color="black", hover_color="#E5E7EB", anchor="w", command=self.tampilkan_daftar_wisata)
        self.btn_daftar_wisata.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_scrapping = ctk.CTkButton(self.sidebar_frame, text="🌐 Scrapping Data", fg_color="transparent", text_color="black", hover_color="#E5E7EB", anchor="w", command=self.tampilkan_scrapping)
        self.btn_scrapping.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

    def setup_main_frame(self):
        # create frame konten
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#FFFFFF")
        self.main_frame.grid(row=0, column=1, sticky="nsew")

    def bersihkan_main_frame(self):
        # clean frame konten
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.btn_dashboard.configure(fg_color="transparent", text_color="black")
        self.btn_daftar_wisata.configure(fg_color="transparent", text_color="black")
        self.btn_scrapping.configure(fg_color="transparent", text_color="black")

    def tampilkan_dashboard(self):
        self.bersihkan_main_frame()
        self.btn_dashboard.configure(fg_color="#86EFAC", text_color="#064E3B")
        
        # Placeholder sementara karena belum dibikin
        ctk.CTkLabel(self.main_frame, text="Halaman Dashboard Belum Dibuat", font=("Arial", 20)).pack(expand=True)
    
    def tampilkan_daftar_wisata(self):
        self.bersihkan_main_frame()
        self.btn_daftar_wisata.configure(fg_color="#86EFAC", text_color="#064E3B") 
        
        # PASTIKAN ADA self.navigasi_ke_form DI SINI!
        halaman_daftar = DaftarWisata(self.main_frame, self.navigasi_ke_form) 
        halaman_daftar.pack(fill="both", expand=True)

    def navigasi_ke_form(self, mode="Tambah", data=None):
        # Fungsi ini yang bakal dipanggil pas button dipencet
        from src.gui.form_wisata import FormWisata
        self.bersihkan_main_frame()
        halaman_form = FormWisata(self.main_frame, self.tampilkan_daftar_wisata, mode, data)
        halaman_form.pack(fill="both", expand=True)


    def tampilkan_scrapping(self):
        self.bersihkan_main_frame()
        self.btn_scrapping.configure(fg_color="#86EFAC", text_color="#064E3B")
        
        # Placeholder sementara karena belum dibikin
        ctk.CTkLabel(self.main_frame, text="Halaman Scrapping Belum Dibuat", font=("Arial", 20)).pack(expand=True)

if __name__ == "__main__":
    app = JabarExploreApp()
    app.mainloop()