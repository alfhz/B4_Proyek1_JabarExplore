import customtkinter as ctk
import os
import threading
from PIL import Image
from tkinter import messagebox
from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import load_data_wisata, cari_wisata
from src.utils.file_handler import buka_json 
from src.utils.validators import format_harga_idr

class DaftarWisata(ctk.CTkFrame):
    """Menampilkan daftar destinasi dalam bentuk kartu dengan aksi edit/hapus/detail."""

    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form = callback_form
        self.callback_detail = callback_detail
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        # konfigurasi responsif
        self.w_kota = 120
        self.w_htm = 110
        self.w_jam = 130
        self.w_rate = 80
        self.w_aksi = 120

        self.tampilkan_halaman_daftar_wisata()
        
        # load data awal langsung dari file handler
        self.refresh_tabel()

    # ------------------- LOAD GAMBAR ASYNC -------------------
    def load_image_async(self, path, label, size=(50, 50)):
        """Memuat gambar dari disk di thread terpisah, update UI setelah selesai."""
        if path in self.image_cache:
            label.configure(image=self.image_cache[path], text="")
            return

        def task():
            try:
                img = Image.open(path)
                # Buat thumbnail agar lebih ringan
                img.thumbnail((size[0]*2, size[1]*2), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                self.image_cache[path] = ctk_img
                self.after(0, lambda: label.configure(image=ctk_img, text=""))
            except Exception:
                self.after(0, lambda: label.configure(text="❌", image=None))

        threading.Thread(target=task, daemon=True).start()

    # ------------------- UI HEADER & FILTER -------------------
    def tampilkan_halaman_daftar_wisata(self):
        # header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Kelola Data Wisata", font=("Arial", 28, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(header, text="Tambah, edit, atau hapus data destinasi wisata Jawa Barat", font=("Arial", 14), text_color="#4B5563").pack(anchor="w", pady=(5,0))

        # filter dan search
        filter_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), ipady=15, ipadx=15)

        # search bar - belum jalan
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        self.teks_ui_nama_wisata = ctk.CTkEntry(search_frame, placeholder_text="🔍 Cari destinasi wisata...", height=35, fg_color="white", text_color="black")
        self.teks_ui_nama_wisata.pack(fill="x", expand=True)
        self.teks_ui_nama_wisata.bind("<KeyRelease>", self.proses_pencarian)

        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")
        
        ctk.CTkComboBox(combo_frame, values=["Semua Kota / Kabupaten"], width=180, fg_color="white", text_color="black").pack(side="left", padx=(0, 10))
        ctk.CTkComboBox(combo_frame, values=["Semua Kategori"], width=150, fg_color="white", text_color="black").pack(side="left", padx=10)

        # redirect ke halaman form 
        ctk.CTkButton(combo_frame, text="+ Tambah Data", font=("Arial", 12, "bold"), fg_color="#10B981", hover_color="#059669", text_color="white", 
                    command=lambda: self.callback_form("Tambah", None)).pack(side="right")

        # header tabel
        table_header = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=5)
        table_header.pack(fill="x", pady=(0, 5), ipady=8)
        
        # grid wight
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

    def refresh_tabel(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        data_master = buka_json()
        if not data_master:
            ctk.CTkLabel(self.scroll_frame, text="Belum ada data wisata.", text_color="gray").pack(pady=20)
            return

        for item in data_master:
            self.render_kartu_wisata(item)

    # proses search
    def proses_pencarian(self, event=None):
        # ambil teks dari search bar
        input_user = self.teks_ui_nama_wisata.get().strip()
        
        # kalau bar kosong, balikkan ke tampilan awal (semua data)
        if not input_user:
            self.refresh_tabel()
            return
            
        # kalau user ngetik sesuatu, baru proses pencariannya
        data_master = buka_json() 
        
        # jalankan pencari
        hasil_pencarian = cari_wisata(input_user, data_master)
        
        # tentukan output
        if not hasil_pencarian:
            self.tampil_pesan_error(f"Wisata '{input_user}' tidak ditemukan")
        else:
            self.render_hasil_pencarian(hasil_pencarian)

    def render_hasil_pencarian(self, daftar_wisata):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        for item in daftar_wisata:
            self.render_kartu_wisata(item)

    def tampil_pesan_error(self, pesan_teks):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.scroll_frame, 
            text=f"🔍 {pesan_teks}", 
            font=("Arial", 14, "italic"),
            text_color="#9CA3AF"
        ).pack(pady=60)
    
    def render_kartu_wisata(self, item):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=5)
        row.pack(fill="x", pady=4, ipady=10)
        row.grid_columnconfigure(0, weight=1)

        identitas = item.get('identitas', {})
        operasional = item.get('operasional', {})
        jam_data = operasional.get('jam_operasional', {})
        
        buka = jam_data.get('buka', {})
        tutup = jam_data.get('tutup', {})
        
        if isinstance(buka, dict):
            j_buka = str(buka.get('jam', '00')).zfill(2)
            m_buka = str(buka.get('menit', '00')).zfill(2)
            waktu_buka = f"{j_buka}:{m_buka}"
        else:
            waktu_buka = str(buka)

        if isinstance(tutup, dict):
            j_tutup = str(tutup.get('jam', '00')).zfill(2)
            m_tutup = str(tutup.get('menit', '00')).zfill(2)
            waktu_tutup = f"{j_tutup}:{m_tutup}"
        else:
            waktu_tutup = str(tutup)
            
        jam_tampil = f"{waktu_buka} - {waktu_tutup}"
        
        if not jam_data or jam_tampil == "{} - {}":
            jam_tampil = "-"

        nama = identitas.get('nama', '-')
        tipe = identitas.get('tipe', 'Umum')
        foto_nama = identitas.get('foto', 'default.png')
        if isinstance(foto_nama, list):
            foto_nama = foto_nama[0] if foto_nama else 'default.png'
        kota = identitas.get('alamat', 'Jawa Barat').split(',')[0]
        rating = identitas.get('rating', '0.0')
        htm = format_harga_idr(operasional.get('htm', 0))

        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20)
        
        # Foto
        path_foto = os.path.join("assets/uploads", foto_nama)
        if not os.path.exists(path_foto):
            path_foto = os.path.join("assets", "placeholder.png") 

        try:
            img_obj = Image.open(path_foto)
            img_render = ctk.CTkImage(light_image=img_obj, size=(50, 50))
            ctk.CTkLabel(info_frame, image=img_render, text="").pack(side="left", padx=(0, 10))
        except:
            ctk.CTkFrame(info_frame, width=50, height=50, fg_color="#E5E7EB").pack(side="left", padx=(0, 10))

        teks_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        teks_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(teks_frame, text=nama, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(teks_frame, text=tipe, font=("Arial", 11), text_color="#6B7280", anchor="w").pack(fill="x")

        # Kolom Data
        ctk.CTkLabel(row, text=kota, width=self.w_kota, anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row, text=htm, width=self.w_htm, anchor="w").grid(row=0, column=2, sticky="w")
        
        # Jam operasional
        ctk.CTkLabel(row, text=jam_tampil, width=self.w_jam, anchor="w").grid(row=0, column=3, sticky="w")
        
        ctk.CTkLabel(row, text=f"★ {rating}", width=self.w_rate, font=("Arial", 12, "bold"), text_color="#F59E0B", anchor="w").grid(row=0, column=4, sticky="w")

        # Tombol Aksi
        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi)
        action_frame.grid(row=0, column=5, sticky="e", padx=20)
        
        ctk.CTkButton(action_frame, text="👁️", width=30, fg_color="transparent", 
                        text_color="#10B981", 
                        command=lambda: self.callback_detail(item)).pack(side="left", padx=2)
        
        ctk.CTkButton(action_frame, text="✏️", width=30, fg_color="transparent", 
                        text_color="#3B82F6", 
                        command=lambda: self.callback_form("Edit", item)).pack(side="left", padx=2)
        
        ctk.CTkButton(action_frame, text="🗑️", width=30, fg_color="transparent", 
                        text_color="#EF4444", 
                        command=lambda: self.notif_konfirmasi(f"Hapus {nama}?", item['id'])).pack(side="left", padx=2)

    def notif_konfirmasi(self, pesan, id_w):
        if messagebox.askyesno("Konfirmasi", pesan):
            hapus_data_wisata(id_w)
            self.refresh_tabel()