import customtkinter as ctk

class ScrapperUI(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            header, 
            text="Scrapping Data Wisata", 
            font=("Arial", 28, "bold"), 
            text_color="black"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header, 
            text="Ambil data destinasi wisata secara otomatis dari internet (Fitur Segera Datang)", 
            font=("Arial", 14), 
            text_color="#4B5563"
        ).pack(anchor="w", pady=(5, 0))
        
        # Content
        content = ctk.CTkFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#E5E7EB")
        content.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        ctk.CTkLabel(
            content,
            text="Fitur Scrapping sedang dalam pengembangan.",
            font=("Arial", 16),
            text_color="#6B7280"
        ).place(relx=0.5, rely=0.4, anchor="center")
        
        # We assume parent.master is the JabarExploreApp instance based on main.py
        def back_to_dashboard():
            try:
                # Depending on how it's packed, we might need to find the app instance
                # In main.py: halaman_scrapper = ScrapperUI(self.main_frame)
                # self.main_frame is a child of self (JabarExploreApp)
                parent.master.tampilkan_dashboard()
            except:
                pass

        ctk.CTkButton(
            content,
            text="Kembali ke Dashboard",
            fg_color="#10B981",
            hover_color="#059669",
            command=back_to_dashboard
        ).place(relx=0.5, rely=0.5, anchor="center")
