import customtkinter as ctk
import os
from PIL import Image
from tkinter import messagebox
from src.logic.crud_engine import hapus_data_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT
from src.utils.validators import format_harga_idr

class DaftarWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_form):
        super().__init__(parent, fg_color="transparent")
        self.callback_form = callback_form
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        # konfigurasi responsif
        self.w_kota = 120
        self.w_htm = 110
        self.w_jam = 130
        self.w_rate = 80
        self.w_aksi = 120 

        self.tampilkan_halaman_daftar_wisata()
        self.refresh_tabel()

    def tampilkan_halaman_daftar_wisata(self):
        # header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Kelola Data Wisata", font=("Arial", 28, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(header, text="Tambah, edit, atau hapus data destinasi wisata Jawa Barat", font=("Arial", 14), text_color="#4B5563").pack(anchor="w", pady=(5,0))

        # filter dan search
        filter_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), ipady=15, ipadx=15)

        # search bar
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        self.teks_ui_nama_wisata = ctk.CTkEntry(search_frame, placeholder_text="🔍 Cari destinasi wisata...", height=35, fg_color="white", text_color="black")
        self.teks_ui_nama_wisata.pack(fill="x", expand=True)
        self.teks_ui_nama_wisata.bind("<KeyRelease>", self.proses_pencarian)

        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")
        
        # Combobox untuk filter kota dan kategori (akan diisi nanti)
        self.combo_kota = ctk.CTkComboBox(combo_frame, values=["Semua Kota / Kabupaten"], width=180, fg_color="white", text_color="black")
        self.combo_kota.pack(side="left", padx=(0, 10))
        self.combo_kota.bind("<<ComboboxSelected>>", self.proses_pencarian)
        
        self.combo_kategori = ctk.CTkComboBox(combo_frame, values=["Semua Kategori"], width=150, fg_color="white", text_color="black")
        self.combo_kategori.pack(side="left", padx=10)
        self.combo_kategori.bind("<<ComboboxSelected>>", self.proses_pencarian)

        # redirect ke halaman form 
        ctk.CTkButton(combo_frame, text="+ Tambah Data", font=("Arial", 12, "bold"), fg_color="#10B981", hover_color="#059669", text_color="white", 
                    command=lambda: self.callback_form("Tambah", None)).pack(side="right")

        # header tabel
        table_header = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=5)
        table_header.pack(fill="x", pady=(0, 5), ipady=8)
        
        table_header.grid_columnconfigure(0, weight=1) 
        
        ctk.CTkLabel(table_header, text="NAMA WISATA", font=("Arial", 11, "bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=0, sticky="ew", padx=20)
        ctk.CTkLabel(table_header, text="KOTA", width=self.w_kota, font=("Arial", 11, "bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(table_header, text="HARGA", width=self.w_htm, font=("Arial", 11, "bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(table_header, text="OPERASIONAL", width=self.w_jam, font=("Arial", 11, "bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(table_header, text="RATING", width=self.w_rate, font=("Arial", 11, "bold"), text_color="#9CA3AF", anchor="w").grid(row=0, column=4, sticky="w")
        ctk.CTkLabel(table_header, text="AKSI", width=self.w_aksi).grid(row=0, column=5, sticky="e", padx=20)

        # area scroll data
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

    def proses_pencarian(self, event=None):
        keyword = self.teks_ui_nama_wisata.get().lower().strip()
        kota_filter = self.combo_kota.get()
        kategori_filter = self.combo_kategori.get()
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        data_master = buka_json()
        if not data_master:
            ctk.CTkLabel(self.scroll_frame, text="Belum ada data wisata.", text_color="gray").pack(pady=20)
            return
        
        # Update filter combobox values
        self.update_filter_options(data_master)
        
        # Filter data
        filtered = []
        for item in data_master:
            identitas = item.get('identitas', {})
            nama = identitas.get('nama', '').lower()
            kota = identitas.get('alamat', '').split(',')[0]
            tipe = identitas.get('tipe', 'Umum')
            
            if keyword and keyword not in nama:
                continue
            if kota_filter != "Semua Kota / Kabupaten" and kota != kota_filter:
                continue
            if kategori_filter != "Semua Kategori" and tipe != kategori_filter:
                continue
            filtered.append(item)
        
        for item in filtered:
            self.render_kartu_wisata(item)
        
        if not filtered:
            ctk.CTkLabel(self.scroll_frame, text="Tidak ada data yang cocok.", text_color="gray").pack(pady=20)

    def update_filter_options(self, data_master):
        kota_set = set()
        kategori_set = set()
        for item in data_master:
            identitas = item.get('identitas', {})
            alamat = identitas.get('alamat', '')
            kota = alamat.split(',')[0] if ',' in alamat else alamat
            if kota:
                kota_set.add(kota)
            tipe = identitas.get('tipe', 'Umum')
            if tipe:
                kategori_set.add(tipe)
        
        kota_list = sorted(list(kota_set))
        kategori_list = sorted(list(kategori_set))
        
        current_kota = self.combo_kota.get()
        current_kategori = self.combo_kategori.get()
        
        self.combo_kota.configure(values=["Semua Kota / Kabupaten"] + kota_list)
        self.combo_kategori.configure(values=["Semua Kategori"] + kategori_list)
        
        if current_kota not in self.combo_kota.cget("values"):
            self.combo_kota.set("Semua Kota / Kabupaten")
        if current_kategori not in self.combo_kategori.cget("values"):
            self.combo_kategori.set("Semua Kategori")

    def refresh_tabel(self):
        self.proses_pencarian()

    def render_kartu_wisata(self, item):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=5)
        row.pack(fill="x", pady=4, ipady=10)
        row.grid_columnconfigure(0, weight=1) 
        
        identitas = item.get('identitas', {})
        operasional = item.get('operasional', {})
        
        nama = identitas.get('nama', '-')
        tipe = identitas.get('tipe', 'Umum')
        foto_nama = identitas.get('foto', 'default.png') 
        kota = identitas.get('alamat', 'Jawa Barat').split(',')[0]
        jam = operasional.get('jam_buka', '-')
        rating = identitas.get('rating', '0.0')
        htm = format_harga_idr(operasional.get('htm', 0))

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20)
        
        # tampil foto
        path_foto = os.path.join(PROJECT_ROOT, "assets", "uploads", foto_nama)
        if not os.path.exists(path_foto):
            path_foto = os.path.join(PROJECT_ROOT, "assets", "placeholder.png") 

        try:
            img_obj = Image.open(path_foto)
            img_render = ctk.CTkImage(light_image=img_obj, dark_image=img_obj, size=(50, 50))
            lbl_foto = ctk.CTkLabel(info_frame, image=img_render, text="")
            lbl_foto.pack(side="left", padx=(0, 10))
        except Exception:
            ctk.CTkFrame(info_frame, width=50, height=50, fg_color="#E5E7EB").pack(side="left", padx=(0, 10))

        teks_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        teks_frame.pack(side="left", fill="both", expand=True)

        lbl_nama = ctk.CTkLabel(teks_frame, text=nama, font=("Arial", 13, "bold"), 
                                text_color="#1F2937", wraplength=250, justify="left", anchor="w")
        lbl_nama.pack(fill="x", anchor="w")
        
        ctk.CTkLabel(teks_frame, text=tipe, font=("Arial", 11), 
                    text_color="#6B7280", anchor="w").pack(fill="x", anchor="w")

        ctk.CTkLabel(row, text=kota, width=self.w_kota, font=("Arial", 12), text_color="#374151", anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row, text=htm, width=self.w_htm, font=("Arial", 12), text_color="#374151", anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(row, text=jam, width=self.w_jam, font=("Arial", 12), text_color="#374151", anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(row, text=f"⭐ {rating}", width=self.w_rate, font=("Arial", 12, "bold"), text_color="#F59E0B", anchor="w").grid(row=0, column=4, sticky="w")

        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi)
        action_frame.grid(row=0, column=5, sticky="e", padx=20)
        
        # view detail
        ctk.CTkButton(action_frame, text="👁️", width=30, fg_color="transparent", 
                    text_color="#10B981", hover_color="#E5E7EB",
                    command=lambda: self.callback_form("View", item)).pack(side="left", padx=2)
        
        # edit
        ctk.CTkButton(action_frame, text="✏️", width=30, fg_color="transparent", 
                    text_color="#3B82F6", hover_color="#E5E7EB", 
                    command=lambda: self.callback_form("Edit", item)).pack(side="left", padx=2)
        
        # delete
        ctk.CTkButton(action_frame, text="🗑️", width=30, fg_color="transparent", 
                    text_color="#EF4444", hover_color="#FEE2E2", 
                    command=lambda: self.notif_konfirmasi(f"Hapus permanen {nama}?", item['id'])).pack(side="left", padx=2)

    def notif_konfirmasi(self, pesan, id_w):
        if messagebox.askyesno("Konfirmasi", pesan):
            hapus_data_wisata(id_w)
            self.refresh_tabel()