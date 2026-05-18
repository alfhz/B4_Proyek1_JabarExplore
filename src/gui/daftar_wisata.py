"""
daftar_wisata.py
Halaman Kelola Data Wisata untuk aplikasi JabarExplore.
Gabungan Fitur: Paginasi (Alfina), Export CSV (Nadhief), Scrapping & Smart Location (Fawwaz).
"""

import customtkinter as ctk
import os
from tkinter import filedialog
from PIL import Image

from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT, export_ke_csv, export_log_ke_csv
from src.utils.validators import format_harga_idr

# ---------------- NOTIFIKASI ------------------
class ModalKonfirmasi(ctk.CTkToplevel):
    """jendela popup kustom rata tengah tanpa ikon untuk konfirmasi hapus."""
    def __init__(self, parent, judul, pesan, callback_setuju):
        super().__init__(parent)
        self.title("")
        self.geometry("400x230")
        self.overrideredirect(True) 
        self.attributes("-topmost", True) 
        self.configure(fg_color="white")

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (230 // 2)
        self.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15, border_width=2, border_color="#F3F4F6")
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        text_container = ctk.CTkFrame(frame, fg_color="transparent")
        text_container.pack(fill="both", expand=True, pady=(35, 0))
        
        ctk.CTkLabel(
            text_container, text=judul, font=("Arial", 18, "bold"), 
            text_color="#111827", anchor="center"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            text_container, text=pesan, font=("Arial", 13), 
            text_color="#6B7280", wraplength=320, justify="center"
        ).pack(pady=(15, 0), padx=40)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(0, 30))

        ctk.CTkButton(
            btn_row, text="Batal", fg_color="#F3F4F6", text_color="#374151", 
            hover_color="#E5E7EB", height=42, font=("Arial", 13, "bold"),
            command=self.destroy
        ).pack(side="left", expand=True, padx=8)
        
        ctk.CTkButton(
            btn_row, text="Ya, Hapus", fg_color="#EF4444", text_color="white", 
            hover_color="#DC2626", height=42, font=("Arial", 13, "bold"),
            command=lambda: [callback_setuju(), self.destroy()]
        ).pack(side="left", expand=True, padx=8)

# ------------------- DROPDOWN CUSTOM DENGAN SCROLL TERBATAS -------------------
class DropdownScroll(ctk.CTkToplevel):
    def __init__(self, parent, values, callback, lebar=200, tinggi_max=220):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color="white")
        self.callback = callback

        x = parent.winfo_rootx()
        y = parent.winfo_rooty() + parent.winfo_height()
        self.geometry(f"{lebar}x{tinggi_max}+{x}+{y}")

        border = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=8)
        border.pack(fill="both", expand=True, padx=1, pady=1)

        scroll = ctk.CTkScrollableFrame(border, fg_color="white", corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        for nilai in values:
            ctk.CTkButton(
                scroll, text=nilai, anchor="w", fg_color="transparent",
                text_color="#374151", hover_color="#DEF4CA", height=30,
                corner_radius=6, command=lambda v=nilai: self._pilih(v)
            ).pack(fill="x", padx=4, pady=1)

        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set()

    def _pilih(self, nilai):
        self.callback(nilai)
        self.destroy()


class DaftarWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form, self.callback_detail = callback_form, callback_detail

        # Lebar kolom
        self.w_kota, self.w_harga, self.w_jam, self.w_rate, self.w_aksi = 140, 120, 150, 90, 160

        self.list_kab_kota = [
            "Semua Kota / Kabupaten", "Kabupaten Bandung", "Kabupaten Bandung Barat", "Kabupaten Bekasi",
            "Kabupaten Bogor", "Kabupaten Ciamis", "Kabupaten Cianjur", "Kabupaten Cirebon", "Kabupaten Garut",
            "Kabupaten Indramayu", "Kabupaten Karawang", "Kabupaten Kuningan", "Kabupaten Majalengka",
            "Kabupaten Pangandaran", "Kabupaten Purwakarta", "Kabupaten Subang", "Kabupaten Sukabumi",
            "Kabupaten Sumedang", "Kabupaten Tasikmalaya", "Kota Bandung", "Kota Banjar", "Kota Bekasi",
            "Kota Bogor", "Kota Cimahi", "Kota Cirebon", "Kota Depok", "Kota Sukabumi", "Kota Tasikmalaya"
        ]
        self.list_kategori = ["Semua Kategori", "Gunung", "Kawah", "Pantai", "Curug", "Situ", "Taman", "Danau"]
        
        # daftar rating per rentang bintang (Fix dari Alfina)
        self.list_rating = [
            "Semua Rating",
            "1.0 - 1.9",
            "2.0 - 2.9",
            "3.0 - 3.9",
            "4.0 - 4.9",
            "5.0",
        ]

        self.kota_terpilih = "Semua Kota / Kabupaten"
        self.kategori_terpilih = "Semua Kategori"
        self.rating_terpilih = "Semua Rating"
        
        # Pagination state
        self.halaman_aktif = 0
        self.item_per_halaman = 10
        self.data_aktif = []
        self._total_data_terakhir = 0
        
        # Penampung notifikasi toast aktif
        self.toast_aktif = None

        self.setup_ui()
        self.refresh_tabel()

    # ------------------- SISTEM NOTIFIKASI TOAST -------------------
    def tampilkan_notif(self, pesan, tipe="success"):
        """nampilin notifikasi melayang di pojok kanan atas."""
        if self.toast_aktif:
            self.toast_aktif.destroy()

        # styling warna pastel
        warna_bg = "#D1FAE5" if tipe == "success" else "#FEE2E2"
        warna_txt = "#065F46" if tipe == "success" else "#B91C1C"
        ikon = "✅" if tipe == "success" else "⚠"

        self.toast_aktif = ctk.CTkLabel(
            self, text=f"{ikon}  {pesan}", font=("Arial", 12, "bold"),
            text_color=warna_txt, fg_color=warna_bg, corner_radius=10,
            padx=20, pady=10
        )
        
        self.toast_aktif.place(relx=0.98, rely=0.02, anchor="ne")
        self.after(3000, lambda: self.toast_aktif.destroy() if self.toast_aktif else None)


    def buat_tombol_dropdown(self, parent, teks_awal, lebar, callback_buka):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=6, border_width=1, border_color="#E5E7EB", width=lebar, height=35)
        frame.pack_propagate(False)
        lbl = ctk.CTkLabel(frame, text=teks_awal, text_color="#374151", font=("Arial", 12), anchor="w")
        lbl.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(frame, text="▼", text_color="#9CA3AF", font=("Arial", 12), width=20).pack(side="right", padx=6)
        frame.bind("<Button-1>", lambda e: callback_buka(frame))
        lbl.bind("<Button-1>", lambda e: callback_buka(frame))
        return frame, lbl

    def _buka_dropdown_kota(self, tombol):
        DropdownScroll(tombol, self.list_kab_kota, lambda v: [setattr(self, 'kota_terpilih', v), self.lbl_kota.configure(text=v), self.proses_filter()], lebar=220)
    def _buka_dropdown_kategori(self, tombol):
        DropdownScroll(tombol, self.list_kategori, lambda v: [setattr(self, 'kategori_terpilih', v), self.lbl_kategori.configure(text=v), self.proses_filter()], lebar=170)
    def _buka_dropdown_rating(self, tombol):
        DropdownScroll(tombol, self.list_rating, lambda v: [setattr(self, 'rating_terpilih', v), self.lbl_rating.configure(text=v), self.proses_filter()], lebar=160)

    def setup_ui(self):
        ctk.CTkLabel(self, text="Kelola Data Wisata", font=("Arial", 28, "bold")).pack(anchor="w", pady=(0, 20))
        f_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        f_frame.pack(fill="x", pady=(0, 15), ipady=10, ipadx=15)

        search_frame = ctk.CTkFrame(f_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        self.teks_cari = ctk.CTkEntry(search_frame, placeholder_text="🔍 Cari destinasi wisata...", height=40, fg_color="white")
        self.teks_cari.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.teks_cari.bind("<KeyRelease>", self.proses_filter)

        ctk.CTkButton(search_frame, text="+ Tambah Data", font=("Arial", 13, "bold"), fg_color="#10B981", height=40, command=lambda: self.callback_form("Tambah", None)).pack(side="right")
        ctk.CTkButton(search_frame, text="📥 Export Data", font=("Arial", 13, "bold"), fg_color="#3B82F6", height=40, command=self.tampilkan_popup_export).pack(side="right", padx=10)

        combo_frame = ctk.CTkFrame(f_frame, fg_color="transparent")
        combo_frame.pack(fill="x")
        self.frame_kota, self.lbl_kota = self.buat_tombol_dropdown(combo_frame, self.kota_terpilih, 210, self._buka_dropdown_kota)
        self.frame_kota.pack(side="left", padx=(0, 10))
        self.frame_kat, self.lbl_kategori = self.buat_tombol_dropdown(combo_frame, self.kategori_terpilih, 160, self._buka_dropdown_kategori)
        self.frame_kat.pack(side="left", padx=(0, 10))
        self.frame_rat, self.lbl_rating = self.buat_tombol_dropdown(combo_frame, self.rating_terpilih, 150, self._buka_dropdown_rating)
        self.frame_rat.pack(side="left")

        self.h_frame = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=5)
        self.h_frame.pack(fill="x", pady=(10, 5))
        self.h_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.h_frame, text="NAMA WISATA", font=("Arial", 11, "bold"), text_color="#4B5563", anchor="w").grid(row=0, column=0, padx=20, pady=10, sticky="w")
        for i, (txt, w) in enumerate([("KOTA / KAB", self.w_kota), ("HARGA TIKET", self.w_harga), ("JAM OPERASIONAL", self.w_jam), ("RATING", self.w_rate), ("AKSI", self.w_aksi)], 1):
            box = ctk.CTkFrame(self.h_frame, fg_color="transparent", width=w, height=30)
            box.grid(row=0, column=i); box.pack_propagate(False)
            ctk.CTkLabel(box, text=txt, font=("Arial", 11, "bold"), text_color="#4B5563").pack(expand=True)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", pady=(8, 0))

    def refresh_tabel(self):
        self.halaman_aktif = 0
        data = buka_json()
        self.data_aktif = sorted(data, key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')), reverse=True) if data else []
        self._tampilkan_halaman()

    def proses_filter(self, e=None):
        keyword, pk, pkat, prat = self.teks_cari.get().lower(), self.kota_terpilih, self.kategori_terpilih, self.rating_terpilih
        data_master = buka_json()
        hasil = []
        for item in data_master:
            idnt = item.get('identitas', {})
            nama, alamat, tipe = idnt.get('nama', '').lower(), idnt.get('alamat', '').lower(), idnt.get('tipe', '').lower()
            try: rating = float(idnt.get('rating', 0))
            except: rating = 0.0
            
            if keyword and keyword not in nama: continue
            if pk != "Semua Kota / Kabupaten":
                pk_n = pk.lower().replace("kabupaten ", "kab. ").replace("kota ", "kota ")
                if pk_n not in alamat: continue
            if pkat != "Semua Kategori" and tipe != pkat.lower(): continue
            if prat != "Semua Rating":
                rentang = {
                    "1.0 - 1.9": (1.0, 1.9),
                    "2.0 - 2.9": (2.0, 2.9),
                    "3.0 - 3.9": (3.0, 3.9),
                    "4.0 - 4.9": (4.0, 4.9),
                    "5.0": (5.0, 5.0),
                }
                batas = rentang.get(prat)
                if batas and not (batas[0] <= rating <= batas[1]): continue
            hasil.append(item)
        
        self.data_aktif = sorted(hasil, key=lambda x: max(x.get('tanggal_diubah', ''), x.get('tanggal_ditambahkan', '')), reverse=True)
        self.halaman_aktif = 0
        self._tampilkan_halaman()

    def _tampilkan_halaman(self):
        for w in self.scroll.winfo_children(): w.destroy()
        if not self.data_aktif:
            ctk.CTkLabel(self.scroll, text="🔍 Tidak ada data", font=("Arial", 14, "italic"), text_color="gray").pack(pady=60)
            self._render_pagination(0); return

        start = self.halaman_aktif * self.item_per_halaman
        end = start + self.item_per_halaman
        for item in self.data_aktif[start:end]: self.render_row(item)
        self._render_pagination(len(self.data_aktif))

    def _render_pagination(self, total):
        for w in self.pagination_frame.winfo_children(): w.destroy()
        total_h = max(1, -(-total // self.item_per_halaman))
        if total_h <= 1: return
        nav = ctk.CTkFrame(self.pagination_frame, fg_color="transparent")
        nav.pack(anchor="e")
        ctk.CTkButton(nav, text="‹", width=30, height=30, fg_color="#F3F4F6", text_color="black", command=lambda: self._ganti_h(self.halaman_aktif-1)).pack(side="left", padx=2)
        for h in range(total_h):
            if abs(h - self.halaman_aktif) < 3:
                ctk.CTkButton(nav, text=str(h+1), width=30, height=30, fg_color="#10B981" if h==self.halaman_aktif else "#F3F4F6", text_color="white" if h==self.halaman_aktif else "black", command=lambda p=h: self._ganti_h(p)).pack(side="left", padx=2)
        ctk.CTkButton(nav, text="›", width=30, height=30, fg_color="#F3F4F6", text_color="black", command=lambda: self._ganti_h(self.halaman_aktif+1)).pack(side="left", padx=2)

    def _ganti_h(self, h):
        if 0 <= h < max(1, -(-len(self.data_aktif) // self.item_per_halaman)):
            self.halaman_aktif = h; self._tampilkan_halaman()

    def render_row(self, item):
        row = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=8, border_width=1, border_color="#F3F4F6")
        row.pack(fill="x", pady=4); row.grid_columnconfigure(0, weight=1)
        idnt, oper = item.get('identitas', {}), item.get('operasional', {})
        
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        f_list = idnt.get('foto', ["default.png"])
        f_nama = f_list[0] if isinstance(f_list, list) else f_list
        path = os.path.join("assets/uploads", f_nama)
        if not os.path.exists(path): path = "assets/placeholder.png"
        try:
            img = ctk.CTkImage(Image.open(path), size=(50, 50))
            ctk.CTkLabel(c0, image=img, text="").pack(side="left")
        except: ctk.CTkFrame(c0, width=50, height=50, fg_color="#E5E7EB").pack(side="left")

        txt_f = ctk.CTkFrame(c0, fg_color="transparent")
        txt_f.pack(side="left", padx=15)
        ctk.CTkLabel(txt_f, text=idnt.get('nama', '-'), font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(txt_f, text=f"Update: {item.get('tanggal_diubah', '-')}", font=("Arial", 9), text_color="gray", anchor="w").pack(fill="x")

        # Smart Location Fawwaz
        parts = idnt.get('alamat', '-').split(',')
        kota = parts[-1].strip()
        if "Jawa Barat" in kota and len(parts) > 1: kota = parts[-2].strip()

        jam_d = oper.get('jam_operasional', {})
        jam = f"{jam_d.get('buka','-')} - {jam_d.get('tutup','-')}" if isinstance(jam_d, dict) else "-"

        self.buat_sel_teks(row, 1, kota, self.w_kota)
        self.buat_sel_teks(row, 2, format_harga_idr(oper.get('htm', 0)), self.w_harga, "#10B981", True)
        self.buat_sel_teks(row, 3, jam, self.w_jam)
        self.buat_sel_teks(row, 4, f"★ {idnt.get('rating', '0.0')}", self.w_rate, "#F59E0B", True)

        box_aksi = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi, height=40)
        box_aksi.grid(row=0, column=5); box_aksi.pack_propagate(False) 
        btn_w = ctk.CTkFrame(box_aksi, fg_color="transparent"); btn_w.pack(expand=True)
        ctk.CTkButton(btn_w, text="👁️", width=34, height=34, fg_color="transparent", text_color="#10B981", command=lambda: self.callback_detail(item)).pack(side="left", padx=2)
        ctk.CTkButton(btn_w, text="✏️", width=34, height=34, fg_color="transparent", text_color="#3B82F6", command=lambda: self.callback_form("Edit", item)).pack(side="left", padx=2)
        ctk.CTkButton(btn_w, text="🗑️", width=34, height=34, fg_color="transparent", text_color="#EF4444", command=lambda: self._del(idnt.get('nama'), item['id'])).pack(side="left", padx=2)

    def buat_sel_teks(self, parent, col, text, width, color="black", bold=False):
        box = ctk.CTkFrame(parent, fg_color="transparent", width=width, height=40)
        box.grid(row=0, column=col); box.pack_propagate(False)
        ctk.CTkLabel(box, text=text, font=("Arial", 12, "bold" if bold else "normal"), text_color=color).pack(expand=True)

    def _del(self, n, id_w):
        def eksekusi_hapus():
            hapus_data_wisata(id_w)
            self.refresh_tabel()
            self.tampilkan_notif(f"'{n}' berhasil dihapus!", "success")

        ModalKonfirmasi(self, "Hapus Destinasi?", f"Apakah kamu yakin ingin menghapus '{n}'? Data akan hilang permanen dari database.", eksekusi_hapus)

    def tampilkan_popup_export(self):
        popup = ctk.CTkToplevel(self); popup.title("Ekspor Data"); popup.geometry("350x200"); popup.attributes("-topmost", True)
        ctk.CTkLabel(popup, text="Pilih Data Eksport:", font=("Arial", 14, "bold")).pack(pady=20)
        ctk.CTkButton(popup, text="Export CSV Wisata", fg_color="#10B981", command=lambda: [popup.destroy(), self.export_csv_action()]).pack(pady=5, fill="x", padx=20)
        ctk.CTkButton(popup, text="Export CSV Log", fg_color="#3B82F6", command=lambda: [popup.destroy(), self.export_log_action()]).pack(pady=5, fill="x", padx=20)

    def export_csv_action(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="Laporan_Wisata.csv")
        if path: 
            export_ke_csv(self.data_aktif, path)
            self.tampilkan_notif("Data berhasil diekspor ke CSV di {}!".format(path))

    def export_log_action(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="Audit_Log.csv")
        if path: 
            if export_log_ke_csv(path): 
                self.tampilkan_notif("Log berhasil diekspor ke CSV di {}!".format(path))
            else: 
                self.tampilkan_notif("Log kosong, tidak ada yang diexport!", "error")
