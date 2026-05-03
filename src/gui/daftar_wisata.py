import customtkinter as ctk
import os
from PIL import Image
from tkinter import messagebox
from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json 
from src.utils.validators import format_harga_idr

class DaftarWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form, self.callback_detail = callback_form, callback_detail
        
        # Lebar kolom (diperbesar untuk tampilan lebih lega dan icon ga kepotong)
        self.w_kota = 140
        self.w_harga = 120
        self.w_jam = 150
        self.w_rate = 90
        self.w_aksi = 160 

        self.setup_ui()
        self.refresh_tabel()

    def setup_ui(self):
        # 1. Judul Halaman
        ctk.CTkLabel(self, text="Kelola Data Wisata", font=("Arial", 28, "bold")).pack(anchor="w", pady=(0, 20))
        
        # 2. Filter Bar
        f_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        f_frame.pack(fill="x", pady=(0, 15), ipady=10, ipadx=15)
        
        self.teks_cari = ctk.CTkEntry(f_frame, placeholder_text="🔍 Cari destinasi wisata...", height=40, fg_color="white")
        self.teks_cari.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.teks_cari.bind("<KeyRelease>", self.proses_cari)

        ctk.CTkButton(f_frame, text="+ Tambah Data", font=("Arial", 13, "bold"), fg_color="#10B981", 
                      height=40, command=lambda: self.callback_form("Tambah", None)).pack(side="right")

        # 3. HEADER TABEL
        self.h_frame = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=5)
        self.h_frame.pack(fill="x", pady=(10, 5))
        self.h_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.h_frame, text="NAMA WISATA", font=("Arial", 11, "bold"), text_color="#4B5563", anchor="w").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Header kolom data (Lurus tengah)
        self.buat_sel_header(self.h_frame, 1, "KOTA / KAB", self.w_kota)
        self.buat_sel_header(self.h_frame, 2, "HARGA TIKET", self.w_harga)
        self.buat_sel_header(self.h_frame, 3, "JAM OPERASIONAL", self.w_jam)
        self.buat_sel_header(self.h_frame, 4, "RATING", self.w_rate)
        self.buat_sel_header(self.h_frame, 5, "AKSI", self.w_aksi)

        # 4. Scroll Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def buat_sel_header(self, parent, col, text, width):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=30)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        ctk.CTkLabel(box, text=text, font=("Arial", 11, "bold"), text_color="#4B5563").pack(expand=True)

    def urutkan_data_terbaru(self, data):
        def get_latest_date(x):
            d1 = x.get('tanggal_diubah', '') or '0000-00-00'
            d2 = x.get('tanggal_ditambahkan', '') or '0000-00-00'
            return max(d1, d2)
        
        return sorted(data, key=get_latest_date, reverse=True)

    def refresh_tabel(self):
        for w in self.scroll.winfo_children(): 
            w.destroy()
            
        data = buka_json()
        
        if not data:
            ctk.CTkLabel(
                self.scroll, 
                text="Belum ada data wisata nih. Tambah dulu yuk!", 
                font=("Arial", 14, "italic"),
                text_color="gray",
                pady=50
            ).pack(expand=True)
            return

        data_sorted = sorted(data, key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')), reverse=True)
        for item in data_sorted: 
            self.render_row(item)

    def proses_cari(self, event=None):
        query = self.teks_cari.get().strip()
        
        for w in self.scroll.winfo_children(): 
            w.destroy()

        if not query: 
            self.refresh_tabel()
            return

        from src.logic.search_engine import cari_wisata
        hasil = cari_wisata(query, buka_json())

        if not hasil:
            ctk.CTkLabel(
                self.scroll, 
                text="Data yang dicari tidak ditemukan!", 
                font=("Arial", 14, "italic"),
                text_color="gray",
                pady=50
            ).pack(expand=True)
            return

        hasil_sorted = sorted(hasil, key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')), reverse=True)
        
        for item in hasil_sorted: 
            self.render_row(item)
    
    def render_row(self, item):
        row = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=8, border_width=1, border_color="#F3F4F6")
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(0, weight=1)

        idnt = item.get('identitas', {})
        oper = item.get('operasional', {})
        
        # --- KOLOM 0: FOTO & NAMA (Sejajar Kiri) ---
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        f_nama = idnt.get('foto', ["default.png"])[0]
        path = os.path.join("assets/uploads", f_nama)
        if not os.path.exists(path): path = os.path.join("assets", "placeholder.png") 
        try:
            img = ctk.CTkImage(light_image=Image.open(path), size=(50, 50))
            ctk.CTkLabel(c0, image=img, text="").pack(side="left")
        except:
            ctk.CTkFrame(c0, width=50, height=50, fg_color="#E5E7EB").pack(side="left")

        txt_f = ctk.CTkFrame(c0, fg_color="transparent")
        txt_f.pack(side="left", padx=15)
        ctk.CTkLabel(txt_f, text=idnt.get('nama', '-'), font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(txt_f, text=f"Update: {item.get('tanggal_diubah', '-')}", font=("Arial", 9), text_color="#9CA3AF", anchor="w").pack(fill="x")

        # --- KOLOM 1 SAMPAI 4: DATA (Lurus Center) ---
        kota = idnt.get('alamat', '-').split(',')[-1].strip()
        harga = format_harga_idr(oper.get('htm', 0))
        jam = f"{oper.get('jam_operasional', {}).get('buka', '-')} - {oper.get('jam_operasional', {}).get('tutup', '-')}"
        rating = f"★ {idnt.get('rating', '0.0')}"

        self.buat_sel_teks(row, 1, kota, self.w_kota)
        self.buat_sel_teks(row, 2, harga, self.w_harga, text_color="#10B981", is_bold=True)
        self.buat_sel_teks(row, 3, jam, self.w_jam)
        self.buat_sel_teks(row, 4, rating, self.w_rate, text_color="#F59E0B", is_bold=True)

        # --- KOLOM 5: AKSI (Center & Ga Kepotong) ---
        box_aksi = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi, height=40)
        box_aksi.grid(row=0, column=5)
        box_aksi.pack_propagate(False) 
        
        btn_wrap = ctk.CTkFrame(box_aksi, fg_color="transparent")
        btn_wrap.pack(expand=True)

        ctk.CTkButton(btn_wrap, text="👁️", width=34, height=34, fg_color="transparent", text_color="#10B981", 
                      hover_color="#D1FAE5", command=lambda: self.callback_detail(item)).pack(side="left", padx=2)
        ctk.CTkButton(btn_wrap, text="✏️", width=34, height=34, fg_color="transparent", text_color="#3B82F6", 
                      hover_color="#DBEAFE", command=lambda: self.callback_form("Edit", item)).pack(side="left", padx=2)
        ctk.CTkButton(btn_wrap, text="🗑️", width=34, height=34, fg_color="transparent", text_color="#EF4444", 
                      hover_color="#FEE2E2", command=lambda: self._del(idnt.get('nama'), item['id'])).pack(side="left", padx=2)

    def buat_sel_teks(self, parent, col, text, width, text_color="black", is_bold=False):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=40)
        box.grid(row=0, column=col)
        box.pack_propagate(False) 
        font_style = ("Arial", 12, "bold") if is_bold else ("Arial", 12)
        ctk.CTkLabel(box, text=text, font=font_style, text_color=text_color).pack(expand=True)

    def _del(self, n, id_w):
        if messagebox.askyesno("Hapus", f"Yakin ingin menghapus {n}?"):
            hapus_data_wisata(id_w); self.refresh_tabel()