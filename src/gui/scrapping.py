# src/gui/scrapping.py
import customtkinter as ctk

class HalamanScrapping(ctk.CTkFrame):
    def __init__(self, parent, callback_back):
        super().__init__(parent, fg_color="transparent")
        self.callback_back = callback_back
        self.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(self, text="Halaman Scrapping Data", font=("Arial", 24, "bold")).pack(pady=50)
        ctk.CTkButton(self, text="← Kembali", command=self.callback_back).pack()