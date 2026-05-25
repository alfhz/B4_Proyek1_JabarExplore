
import customtkinter as ctk
import os
from tkinter import filedialog
from PIL import Image

from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT, export_ke_csv, export_log_ke_csv
from src.utils.validators import format_harga_idr
from src.logic.stats_logic import get_official_kabupaten

# ---------------- NOTIFIKASI MODAL - DELETE ------------------
class ModalKonfirmasi(ctk.CTkToplevel):
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


# ------------------- DROPDOWN CUSTOM FILTER -------------------
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
                scroll, text=nilai, anchor="w", fg_color="transparent", text_color="#374151",
                hover_color="#DEF4CA", height=32, font=("Arial", 13), corner_radius=6,
                command=lambda v=nilai: self._pilih(v)
            ).pack(fill="x", padx=4, pady=1)
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.focus_set()

    def _pilih(self, nilai):
        self.callback(nilai)
        self.destroy()


#------------------- FRAME UTAMA DAFTAR WISATA -------------------
class DaftarWisata(ctk.CTkFrame):
    BATCH_SIZE = 15

    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form, self.callback_detail = callback_form, callback_detail
        self.data_master = buka_json() 
        
        # konfigurasi weight kolom (total 10.5) untuk sinkronisasi header-tabel
        self.w_nama, self.w_kota, self.w_harga, self.w_jam, self.w_rate, self.w_aksi = 3.2, 1.5, 1.5, 1.5, 1.0, 1.8

        self.list_kab_kota = [
            "Semua Kota / Kabupaten", "Kabupaten Bandung", "Kabupaten Bandung Barat", "Kabupaten Bekasi",
            "Kabupaten Bogor", "Kabupaten Ciamis", "Kabupaten Cianjur", "Kabupaten Cirebon", "Kabupaten Garut",
            "Kabupaten Indramayu", "Kabupaten Karawang", "Kabupaten Kuningan", "Kabupaten Majalengka",
            "Kabupaten Pangandaran", "Kabupaten Purwakarta", "Kabupaten Subang", "Kabupaten Sukabumi",
            "Kabupaten Sumedang", "Kabupaten Tasikmalaya", "Kota Bandung", "Kota Banjar", "Kota Bekasi",
            "Kota Bogor", "Kota Cimahi", "Kota Cirebon", "Kota Depok", "Kota Sukabumi", "Kota Tasikmalaya"
        ]
        self.list_kategori = ["Semua Kategori", "Gunung", "Kawah", "Pantai", "Curug", "Situ", "Taman", "Danau"]
        self.list_rating = ["Semua Rating"] + [f"{r/10:.1f}" for r in range(10, 50, 10)] + ["5.0"]

        self.kota_terpilih = "Semua Kota / Kabupaten"
        self.kategori_terpilih = "Semua Kategori"
        self.rating_terpilih = "Semua Rating"
        
        self.toast_aktif = None
        self.data_aktif = []

        self.setup_ui()
        self.refresh_tabel()

    # ------------------- SISTEM NOTIFIKASI TOAST -------------------
    def tampilkan_notif(self, pesan, tipe="success"):
        if self.toast_aktif: self.toast_aktif.destroy()

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

    # ------------------- FUNGSI DROPDOWN UNTUK FILTER -------------------
    def buat_tombol_dropdown(self, parent, teks_awal, lebar, callback_buka):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=6, border_width=1, border_color="#E5E7EB", width=lebar, height=40)
        frame.pack_propagate(False)
        lbl = ctk.CTkLabel(frame, text=teks_awal, text_color="#374151", font=("Arial", 13), anchor="w")
        lbl.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(frame, text="▾", text_color="#9CA3AF", font=("Arial", 13), width=20).pack(side="right", padx=6)
        frame.bind("<Button-1>", lambda e: callback_buka(frame)); lbl.bind("<Button-1>", lambda e: callback_buka(frame))
        return frame, lbl

    def _buka_dropdown_kota(self, t): DropdownScroll(t, self.list_kab_kota, self._pilih_kota, 230)
    def _pilih_kota(self, v): self.kota_terpilih = v; self.lbl_kota.configure(text=v); self.proses_filter()
    def _buka_dropdown_kategori(self, t): DropdownScroll(t, self.list_kategori, self._pilih_kat, 180)
    def _pilih_kat(self, v): self.kategori_terpilih = v; self.lbl_kategori.configure(text=v); self.proses_filter()
    def _buka_dropdown_rating(self, t): DropdownScroll(t, self.list_rating, self._pilih_rat, 170)
    def _pilih_rat(self, v): self.rating_terpilih = v; self.lbl_rating.configure(text=v); self.proses_filter()

    # ------------------- TATA LETAK UTAMA KELOLA DATA -------------------
    def setup_ui(self):
        ctk.CTkLabel(self, text="Kelola Data Wisata", font=("Arial", 32, "bold")).pack(anchor="w", pady=(0, 20))
        
        f_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        f_frame.pack(fill="x", pady=(0, 15), ipady=12, ipadx=15)

        # -------------- SECTION PENCARIAN & FILTER --------------
        search_row = ctk.CTkFrame(f_frame, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 10))
        self.teks_cari = ctk.CTkEntry(search_row, placeholder_text="Cari destinasi wisata...", height=45, font=("Arial", 15), fg_color="white")
        self.teks_cari.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.teks_cari.bind("<KeyRelease>", self.proses_filter)
        ctk.CTkButton(search_row, text="+ Tambah Data", font=("Arial", 15, "bold"), fg_color="#10B981", hover_color="#477163", height=45, width=140, command=lambda: self.callback_form("Tambah", None)).pack(side="right")
        ctk.CTkButton(search_row, text="▼ Export", font=("Arial", 15, "bold"), fg_color="#3B82F6", hover_color="#4A5D7A", height=45, width=120, command=self.tampilkan_popup_export).pack(side="right", padx=(0, 10))

        combo_row = ctk.CTkFrame(f_frame, fg_color="transparent")
        combo_row.pack(fill="x")
        f_k, self.lbl_kota = self.buat_tombol_dropdown(combo_row, "Semua Kota / Kabupaten", 230, self._buka_dropdown_kota)
        f_k.pack(side="left", padx=(0, 10))
        f_kt, self.lbl_kategori = self.buat_tombol_dropdown(combo_row, "Semua Kategori", 180, self._buka_dropdown_kategori)
        f_kt.pack(side="left", padx=(0, 10))
        f_rt, self.lbl_rating = self.buat_tombol_dropdown(combo_row, "Semua Rating", 170, self._buka_dropdown_rating)
        f_rt.pack(side="left", padx=(0, 10))

        # -------------- SECTION TABEL DAFTAR WISATA --------------
        self.h_frame = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=5)
        self.h_frame.pack(fill="x", pady=(10, 5), padx=(0, 16)) 
        self.h_frame.grid_columnconfigure(0, weight=int(self.w_nama*10), uniform="tabel")
        self.h_frame.grid_columnconfigure(1, weight=int(self.w_kota*10), uniform="tabel")
        self.h_frame.grid_columnconfigure(2, weight=int(self.w_harga*10), uniform="tabel")
        self.h_frame.grid_columnconfigure(3, weight=int(self.w_jam*10), uniform="tabel")
        self.h_frame.grid_columnconfigure(4, weight=int(self.w_rate*10), uniform="tabel")
        self.h_frame.grid_columnconfigure(5, weight=int(self.w_aksi*10), uniform="tabel")
        self.h_frame.grid_columnconfigure(6, minsize=14) 

        ctk.CTkLabel(self.h_frame, text="NAMA WISATA", font=("Arial", 13, "bold"), text_color="#565656", anchor="w").grid(row=0, column=0, padx=25, pady=12, sticky="w")
        self.buat_sel_header(self.h_frame, 1, "KOTA / KAB")
        self.buat_sel_header(self.h_frame, 2, "HARGA TIKET")
        self.buat_sel_header(self.h_frame, 3, "JAM OPERASIONAL")
        self.buat_sel_header(self.h_frame, 4, "RATING")
        self.buat_sel_header(self.h_frame, 5, "AKSI")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.navigasi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.navigasi_container.pack(fill="x", pady=10)

    def buat_sel_header(self, parent, col, text):
        ctk.CTkFrame(parent, fg_color="#D1D5DB", width=1, height=30).grid(row=0, column=col, sticky="w")
        ctk.CTkLabel(parent, text=text, font=("Arial", 13, "bold"), text_color="#565656", anchor="center").grid(row=0, column=col, sticky="nsew")

    # ------------------- REFRESH & RENDER TABEL -------------------
    def refresh_tabel(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for w in self.navigasi_container.winfo_children(): w.destroy()

        data = buka_json()
        
        if not data:
            self.data_master = []
            self.data_aktif = []
            self.halaman_tabel = 0
            
            lbl_empty = ctk.CTkLabel(
                self.scroll_frame, 
                text="Belum ada data.", 
                font=("Arial", 15, "italic"), 
                text_color="#9CA3AF"
            )
            lbl_empty.pack(pady=100, expand=True)
            return

        data_s = sorted(data, key=lambda x: max(x.get('tanggal_diubah',''), x.get('tanggal_ditambahkan','')), reverse=True)
        self.data_master = data
        self.data_aktif = data_s
        self.halaman_tabel = 0
        self.render_halaman()

    def render_halaman(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for w in self.navigasi_container.winfo_children(): w.destroy()

        if not self.data_aktif:
            ctk.CTkLabel(self.scroll_frame, text="Data tidak ditemukan.", font=("Arial", 14), text_color="#9CA3AF").pack(pady=60)
            return

        start = self.halaman_tabel * self.BATCH_SIZE
        end = min(start + self.BATCH_SIZE, len(self.data_aktif))
        
        for item in self.data_aktif[start:end]:
            self.render_row(item)
            
        total_halaman = max(1, -(-len(self.data_aktif) // self.BATCH_SIZE))
        if total_halaman > 1:
            nav_inner = ctk.CTkFrame(self.navigasi_container, fg_color="transparent")
            nav_inner.pack(anchor="center")
            
            ctk.CTkButton(nav_inner, text="‹ Prev", width=60, height=30, fg_color="#F3F4F6", text_color="#374151", hover_color="#DEF4CA", command=self._halaman_prev).pack(side="left", padx=5)
            
            # Batasi jumlah tombol halaman agar tidak kepanjangan
            start_pg = max(0, self.halaman_tabel - 2)
            end_pg = min(total_halaman, start_pg + 5)
            if end_pg - start_pg < 5:
                start_pg = max(0, end_pg - 5)
                
            if start_pg > 0:
                ctk.CTkLabel(nav_inner, text="...").pack(side="left", padx=2)
                
            for h in range(start_pg, end_pg):
                is_aktif = (h == self.halaman_tabel)
                ctk.CTkButton(nav_inner, text=str(h + 1), width=35, height=35, fg_color="#10B981" if is_aktif else "#F3F4F6", text_color="white" if is_aktif else "#374151", hover_color="#DEF4CA", command=lambda p=h: self._pergi_ke_halaman(p)).pack(side="left", padx=2)
                
            if end_pg < total_halaman:
                ctk.CTkLabel(nav_inner, text="...").pack(side="left", padx=2)
                
            ctk.CTkButton(nav_inner, text="Next ›", width=60, height=30, fg_color="#F3F4F6", text_color="#374151", hover_color="#DEF4CA", command=self._halaman_next).pack(side="left", padx=5)

    def _halaman_prev(self):
        if self.halaman_tabel > 0:
            self.halaman_tabel -= 1
            self.render_halaman()

    def _halaman_next(self):
        total = -(-len(self.data_aktif) // self.BATCH_SIZE)
        if self.halaman_tabel < total - 1:
            self.halaman_tabel += 1
            self.render_halaman()

    def _pergi_ke_halaman(self, hal):
        self.halaman_tabel = hal
        self.render_halaman()

    # ------------------- RENDER BARIS DATA -------------------
    def render_row(self, item):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#F3F4F6")
        row.pack(fill="x", pady=4, padx=2)
        row.grid_columnconfigure(0, weight=int(self.w_nama * 10), uniform="tabel")
        row.grid_columnconfigure(1, weight=int(self.w_kota * 10), uniform="tabel")
        row.grid_columnconfigure(2, weight=int(self.w_harga * 10), uniform="tabel")
        row.grid_columnconfigure(3, weight=int(self.w_jam * 10), uniform="tabel")
        row.grid_columnconfigure(4, weight=int(self.w_rate * 10), uniform="tabel")
        row.grid_columnconfigure(5, weight=int(self.w_aksi * 10), uniform="tabel")

        idnt, oper = item.get('identitas', {}), item.get('operasional', {})
        
        c0 = ctk.CTkFrame(row, fg_color="transparent")
        c0.grid(row=0, column=0, padx=25, pady=12, sticky="w")
        f_n = idnt.get('foto', ["default.png"])
        f_n = f_n[0] if isinstance(f_n, list) else f_n
        path = os.path.join("assets/uploads", f_n)
        if not os.path.exists(path): path = os.path.join("assets", "placeholder.png") 
        img = ctk.CTkImage(light_image=Image.open(path), size=(55, 55))
        ctk.CTkLabel(c0, image=img, text="").pack(side="left")

        txt_f = ctk.CTkFrame(c0, fg_color="transparent")
        txt_f.pack(side="left", padx=15, fill="x", expand=True)
        lbl_n = ctk.CTkLabel(txt_f, text=idnt.get('nama','-'), font=("Arial", 15, "bold"), anchor="w", justify="left", wraplength=180)
        lbl_n.pack(fill="x")
        lbl_n.bind("<Configure>", lambda e: lbl_n.configure(wraplength=e.width))
        ctk.CTkLabel(txt_f, text=f"Update: {item.get('tanggal_diubah','-')}", font=("Arial", 13), text_color="#6B6F76", anchor="w").pack(fill="x")

        alamat_asli = idnt.get('alamat', '-')
        kota_resmi = get_official_kabupaten(alamat_asli)
        
        if kota_resmi == "Lainnya":
            parts = alamat_asli.split(',')
            kota = parts[-1].strip()
            if "Jawa Barat" in kota and len(parts) > 1: kota = parts[-2].strip()
            kota = kota.replace("Kabupaten", "Kab.")
            if kota.lower() == "jawa barat" or kota.strip() == "":
                kota = "-"
        else:
            if not kota_resmi.startswith("Kota "):
                kota = f"Kab. {kota_resmi}"
            else:
                kota = kota_resmi

        self.buat_sel(row, 1, kota, font_size=15)
        self.buat_sel(row, 2, format_harga_idr(oper.get('htm', 0)), "#10B981", True)
        j = oper.get('jam_operasional', {})
        self.buat_sel(row, 3, f"{j.get('buka','08:00')} - {j.get('tutup','17:00')}", font_size=15)
        self.buat_sel(row, 4, f"★ {idnt.get('rating', '0.0')}", "#F59E0B", True)

        action_f = ctk.CTkFrame(row, fg_color="transparent")
        action_f.grid(row=0, column=5, sticky="nsew")
        ctk.CTkFrame(row, fg_color="#F3F4F6", width=1, height=45).grid(row=0, column=5, sticky="w")
        btn_i = ctk.CTkFrame(action_f, fg_color="transparent")
        btn_i.pack(expand=True)
        btn_i.grid_columnconfigure((0, 1, 2), weight=1, uniform="ikon")
        
        ctk.CTkButton(btn_i, text="👁️", width=38, height=40, fg_color="transparent", text_color="#10B981", hover_color="#BEFFE9", command=lambda: self.callback_detail(item)).grid(row=0, column=0, padx=2)
        ctk.CTkButton(btn_i, text="✏️", width=38, height=40, fg_color="transparent", text_color="#3B82F6", hover_color="#ADCCFF", command=lambda: self.callback_form("Edit", item)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(btn_i, text="🗑️", width=38, height=40, fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2", command=lambda: self._del(idnt.get('nama'), item['id'])).grid(row=0, column=2, padx=2)

    def buat_sel(self, parent, col, teks, warna="black", bold=False, font_size=14):
        ctk.CTkFrame(parent, fg_color="#F3F4F6", width=1, height=45).grid(row=0, column=col, sticky="w")
        fnt = ("Arial", font_size, "bold") if bold else ("Arial", font_size)
        lbl = ctk.CTkLabel(parent, text=teks, font=fnt, text_color=warna, anchor="center")
        lbl.grid(row=0, column=col, sticky="nsew")

    # ------------------- HAPUS & FILTER -------------------
    def _del(self, n, id_w):
        def eksekusi_hapus():
            hapus_data_wisata(id_w)
            self.refresh_tabel()
            self.tampilkan_notif(f"'{n}' berhasil dihapus!", "success")

        ModalKonfirmasi(self, "Hapus Destinasi?", f"Apakah kamu yakin ingin menghapus '{n}'? Data akan hilang permanen dari database.", eksekusi_hapus)

    # ------------------- FILTER -------------------
    def proses_filter(self, event=None):
        keyword = self.teks_cari.get().strip().lower()
        p_kota, p_kat, p_rat = self.kota_terpilih, self.kategori_terpilih, self.rating_terpilih
        
        data = buka_json()
        if not data: return
        
        hasil_pencarian = cari_wisata(keyword, data) if keyword else data
        
        hasil_akhir = []
        for i in hasil_pencarian:
            idnt = i.get('identitas', {})
            al, ti, rat = idnt.get('alamat',''), idnt.get('tipe',''), float(idnt.get('rating',0))
            if p_kota != "Semua Kota / Kabupaten":
                k_n = p_kota.lower().replace("kabupaten ","kab. ").replace("kota ","kota ")
                if (k_n+",") not in al.lower() and not al.lower().endswith(k_n): continue
            if p_kat != "Semua Kategori" and ti.lower() != p_kat.lower(): continue
            if p_rat != "Semua Rating":
                try: 
                    if rat < float(p_rat) - 0.05: continue
                except: pass
            hasil_akhir.append(i)
            
        self.data_aktif = sorted(hasil_akhir, key=lambda x: max(x.get('tanggal_diubah',''), x.get('tanggal_ditambahkan','')), reverse=True)
        self.halaman_tabel = 0
        self.render_halaman()

    # ------------------- EXPORT -------------------
    def tampilkan_popup_export(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Export")
        popup.geometry("350x200")
        popup.attributes("-topmost", True)
        ctk.CTkLabel(popup, text="Pilih Format Export:", font=("Arial", 14, "bold")).pack(pady=20)
        ctk.CTkButton(popup, text="Export CSV", command=lambda: [popup.destroy(), self.export_csv_action()], fg_color="#10B981", hover_color="#477163").pack(pady=5, fill="x", padx=30)
        ctk.CTkButton(popup, text="Export Log", command=lambda: [popup.destroy(), self.export_log_action()], fg_color="#3B82F6", hover_color="#4A5D7A").pack(pady=5, fill="x", padx=30)

    def export_csv_action(self):
        if not getattr(self, 'data_aktif', []): return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="Wisata_Jabar.csv")
        if path: 
            export_ke_csv(self.data_aktif, path)
            self.tampilkan_notif("Data berhasil diekspor ke CSV di {}!".format(path))

    def export_log_action(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="Log_Aktivitas.csv")
        if path: 
            export_log_ke_csv(path)
            self.tampilkan_notif("Log berhasil diekspor ke CSV di {}!".format(path))