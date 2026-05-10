import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

import customtkinter as ctk

from src.gui.daftar_wisata import DaftarWisata
from src.gui.dashboard import dashboard

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class main_windows(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("JabarExplore — Wisata Jawa Barat")
        self.geometry("1280x860")
        self.minsize(1100, 720)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_main_frame()

        self.tampilkan_dashboard()

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#F9FAFB")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        self.sidebar_frame.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Jabar Explore",
            font=("Segoe UI", 22, "bold"),
            text_color="#059669",
        ).grid(row=0, column=0, padx=20, pady=(28, 8), sticky="w")

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color="#E5E7EB").grid(
            row=1, column=0, sticky="ew", padx=14, pady=(0, 12)
        )

        self.btn_dashboard = ctk.CTkButton(
            self.sidebar_frame,
            text="  ▦   Dashboard",
            fg_color="transparent",
            text_color="#374151",
            hover_color="#E5E7EB",
            anchor="w",
            height=42,
            font=("Segoe UI", 13),
            command=self.tampilkan_dashboard,
        )
        self.btn_dashboard.grid(row=2, column=0, padx=12, pady=4, sticky="ew")

        self.btn_daftar_wisata = ctk.CTkButton(
            self.sidebar_frame,
            text="  ⚙   Kelola Data Wisata",
            fg_color="transparent",
            text_color="#374151",
            hover_color="#E5E7EB",
            anchor="w",
            height=42,
            font=("Segoe UI", 13),
            command=self.tampilkan_daftar_wisata,
        )
        self.btn_daftar_wisata.grid(row=3, column=0, padx=12, pady=4, sticky="ew")

        self.btn_scrapping = ctk.CTkButton(
            self.sidebar_frame,
            text="  ▤   Scrapping Data",
            fg_color="transparent",
            text_color="#374151",
            hover_color="#E5E7EB",
            anchor="w",
            height=42,
            font=("Segoe UI", 13),
            command=self.tampilkan_scrapping,
        )
        self.btn_scrapping.grid(row=4, column=0, padx=12, pady=4, sticky="ew")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="v1.0 — Tim B4",
            font=("Segoe UI", 10),
            text_color="#9CA3AF",
        ).grid(row=7, column=0, pady=16)

    def setup_main_frame(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#FFFFFF")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def bersihkan_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.btn_dashboard.configure(fg_color="transparent", text_color="#374151")
        self.btn_daftar_wisata.configure(fg_color="transparent", text_color="#374151")
        self.btn_scrapping.configure(fg_color="transparent", text_color="#374151")

    def _set_active_nav(self, active: str) -> None:
        style_active = {"fg_color": "#86EFAC", "text_color": "#064E3B", "hover_color": "#6EE7B7"}
        style_idle = {"fg_color": "transparent", "text_color": "#374151", "hover_color": "#E5E7EB"}
        for key, btn in (
            ("dashboard", self.btn_dashboard),
            ("daftar", self.btn_daftar_wisata),
            ("scrape", self.btn_scrapping),
        ):
            btn.configure(**(style_active if key == active else style_idle))

    def tampilkan_dashboard(self):
        self.bersihkan_main_frame()
        self._set_active_nav("dashboard")
        halaman = dashboard(self.main_frame)
        halaman.grid(row=0, column=0, sticky="nsew")

    def tampilkan_daftar_wisata(self):
        self.bersihkan_main_frame()
        self._set_active_nav("daftar")
        halaman_daftar = DaftarWisata(self.main_frame, self.navigasi_ke_form, self.navigasi_ke_detail)
        halaman_daftar.pack(fill="both", expand=True, padx=20, pady=20)

    def navigasi_ke_form(self, mode="Tambah", data=None):
        try:
            from src.gui.form_wisata import form_input_wisata
        except ImportError:
            import tkinter.messagebox as mb

            mb.showinfo("Form", "Modul form wisata belum tersedia.")
            return
        self.bersihkan_main_frame()
        halaman_form = form_input_wisata(self.main_frame, self.tampilkan_daftar_wisata, mode, data)
        halaman_form.pack(fill="both", expand=True, padx=30, pady=20)

    def navigasi_ke_detail(self, data=None):
        try:
            from src.gui.detail_wisata import DetailWisata
        except ImportError:
            import tkinter.messagebox as mb
            mb.showinfo("Detail", "Modul detail wisata belum tersedia.")
            return
        self.bersihkan_main_frame()
        halaman_detail = DetailWisata(self.main_frame, self.tampilkan_daftar_wisata, data)
        halaman_detail.pack(fill="both", expand=True)

    def tampilkan_scrapping(self):
        from src.gui.scrapping import HalamanScrapping
        self.bersihkan_main_frame()
        self._set_active_nav("scrape")
        halaman_scrapper = HalamanScrapping(self.main_frame, callback_back=self.tampilkan_dashboard)
        halaman_scrapper.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = main_windows()
    app.mainloop()
