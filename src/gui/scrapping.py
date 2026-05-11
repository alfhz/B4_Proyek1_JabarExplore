"""
src/ui/scrapping.py
────────────────────────────────────────────────────────────────────
Halaman GUI Scrapping Data — Jabar Explore
(Desain Card Baru + Paginasi)
────────────────────────────────────────────────────────────────────
"""

import threading
import math
import customtkinter as ctk
from tkinter import messagebox

# Import FormWisata - sesuaikan path jika perlu
try:
    from src.gui.form_wisata import FormWisata
except ImportError:
    FormWisata = None

try:
    from src.logic.scrap_logic import ScrapLogic
except ImportError:
    ScrapLogic = None

try:
    from src.utils.file_handler import buka_json, tambah_data
except ImportError:
    def buka_json(): return []
    def tambah_data(d): pass

try:
    from src.logic.crud_engine import tambah_data_wisata
except ImportError:
    tambah_data_wisata = None


# ═══════════════════════════════════════════════════════════════════
#  KONSTANTA WARNA BADGE (Desain Pastel)
# ═══════════════════════════════════════════════════════════════════
TIPE_WARNA = {
    "Kawah":  {"bg": "#ECFDF5", "txt": "#10B981"}, 
    "Situ":   {"bg": "#ECFDF5", "txt": "#10B981"}, 
    "Pantai": {"bg": "#ECFDF5", "txt": "#10B981"}, 
    "Curug":  {"bg": "#ECFDF5", "txt": "#10B981"}, 
    "Gunung": {"bg": "#ECFDF5", "txt": "#10B981"},
    "Lainnya":{"bg": "#ECFDF5", "txt": "#10B981"},
}

def _bintang(rating: float) -> str:
    penuh = int(rating)
    setengah = 1 if (rating - penuh) >= 0.5 else 0
    return "★" * penuh + ("½" if setengah else "") + "☆" * (5 - penuh - setengah)

def _cek_duplikat_db(nama: str, data_db: list) -> bool:
    nama_lower = nama.strip().lower()
    for item in data_db:
        if item.get("identitas", {}).get("nama", "").strip().lower() == nama_lower:
            return True
    return False

def _konversi_scrap_ke_card(item_scrap: dict) -> dict:
    if "identitas" in item_scrap: return item_scrap
    return {
        "id": item_scrap.get("id", ""),
        "identitas": {
            "nama": item_scrap.get("judul", "-"), 
            "tipe": "Lainnya",
            "alamat": item_scrap.get("lokasi", "Jawa Barat"), 
            "rating": 0.0,
            "foto": item_scrap.get("gambar", ""),
            "deskripsi": item_scrap.get("deskripsi", ""),
        },
        "operasional": {"htm": "-"},
    }

# ═══════════════════════════════════════════════════════════════════
#  CARD DESTINASI (DESAIN BARU DIPERBAIKI)
# ═══════════════════════════════════════════════════════════════════
class CardDestinasi(ctk.CTkFrame):
    def __init__(self, parent, data: dict, on_edit, on_hapus, is_duplikat: bool = False):
        border_color = "#EF4444" if is_duplikat else "#E5E7EB"
        bg_color     = "#FFF5F5" if is_duplikat else "#FFFFFF"

        super().__init__(
            parent,
            fg_color=bg_color,
            corner_radius=8,
            border_width=1,
            border_color=border_color,
            height=200 
        )
        self.pack_propagate(False)
        self.data        = data
        self.on_edit     = on_edit
        self.on_hapus    = on_hapus
        self.is_duplikat = is_duplikat
        self._build()

    def _build(self):
        idnt = self.data.get("identitas", {})
        oper = self.data.get("operasional", {})
        nama = idnt.get("nama", "-")
        kota = idnt.get("alamat", "-").split(",")[0] 
        rating = float(idnt.get("rating", 0))
        tipe = idnt.get("tipe", "Lainnya")
        htm  = oper.get("htm", "-")
        
        warna = TIPE_WARNA.get(tipe, TIPE_WARNA.get("Lainnya", {"bg": "#F3F4F6", "txt": "#6B7280"}))

        if self.is_duplikat:
            banner = ctk.CTkFrame(self, fg_color="#FEE2E2", corner_radius=0, height=20)
            banner.pack(fill="x")
            ctk.CTkLabel(banner, text="⚠ Sudah ada di database", font=("Arial", 10, "bold"), text_color="#B91C1C").pack()

        # ── ROW 1: Judul & Tombol Aksi ──
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(15, 5))

        # KUNCI: Pack tombol ke KANAN lebih dulu agar tidak terdorong oleh teks
        btn_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        btn_frame.pack(side="right", anchor="ne")
        
        ctk.CTkButton(
            btn_frame, text="✏", width=28, height=28, fg_color="#F3F4F6", 
            text_color="#374151", hover_color="#E5E7EB", font=("Arial", 12), 
            command=lambda: self.on_edit(self.data)
        ).pack(side="left", padx=(0, 4))
        
        ctk.CTkButton(
            btn_frame, text="🗑", width=28, height=28, fg_color="#FEE2E2", 
            text_color="#EF4444", hover_color="#FECACA", font=("Arial", 12), 
            command=lambda: self.on_hapus(self.data)
        ).pack(side="left")

        # Label nama di KIRI, ditambahkan 'wraplength' agar teks turun kalau kepanjangan
        lbl_nama = ctk.CTkLabel(
            top_row, text=nama, font=("Georgia", 14, "bold"), text_color="#111827", 
            anchor="nw", justify="left", wraplength=140
        )
        lbl_nama.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # ── ROW 2: Lokasi ──
        loc_row = ctk.CTkFrame(self, fg_color="transparent")
        loc_row.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(loc_row, text="📍", font=("Arial", 12), text_color="#10B981").pack(side="left")
        ctk.CTkLabel(loc_row, text=f" {kota}", font=("Arial", 12), text_color="#374151").pack(side="left")

        # ── ROW 3: Rating ──
        rat_row = ctk.CTkFrame(self, fg_color="transparent")
        rat_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(rat_row, text=_bintang(rating), font=("Arial", 14), text_color="#FBBF24").pack(side="left")
        ctk.CTkLabel(rat_row, text=f"  {rating}", font=("Arial", 12), text_color="#111827").pack(side="left")

        # ── ROW 4: Badge & Harga (Sekarang aman tidak terpotong) ──
        bot_row = ctk.CTkFrame(self, fg_color="transparent")
        bot_row.pack(fill="x", side="bottom", padx=15, pady=15)
        
        ctk.CTkLabel(
            bot_row, text=tipe, font=("Arial", 11, "bold"),
            text_color=warna["txt"], fg_color=warna["bg"],
            corner_radius=6, padx=10, pady=2
        ).pack(side="left")

        ctk.CTkLabel(bot_row, text=htm, font=("Arial", 13, "bold"), text_color="#10B981").pack(side="right")
        
# ═══════════════════════════════════════════════════════════════════
#  HALAMAN SCRAPPING UTAMA
# ═══════════════════════════════════════════════════════════════════
class HalamanScrapping(ctk.CTkFrame):
    def __init__(self, parent, callback_back):
        super().__init__(parent, fg_color="transparent")
        self.callback_back = callback_back
        
        self.hasil_scrapping = []   
        self.status_duplikat = {}   
        self._scrap_engine   = None
        
        # Pengaturan Paginasi
        self.current_page = 1
        self.items_per_page = 12 

        self._build_ui()

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        self._outer = outer

        # ── Header ──
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(20, 10))

        ctk.CTkLabel(header, text="Scrapping Data", font=("Arial", 28, "bold"), text_color="#111827").pack(side="left")

        self.lbl_notif = ctk.CTkLabel(
            header, text="✅  Scrapping berhasil!", font=("Arial", 12),
            text_color="#065F46", fg_color="#D1FAE5", corner_radius=8, padx=12, pady=6
        )

        # ── Panel Input ──
        panel_input = ctk.CTkFrame(outer, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E7EB")
        panel_input.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(panel_input, text="Input Data", font=("Arial", 14, "bold"), text_color="#111827").pack(anchor="w", padx=20, pady=(15, 5))

        ctk.CTkLabel(panel_input, text="URL Website", font=("Arial", 12), text_color="#6B7280").pack(anchor="w", padx=20)
        self.en_url = ctk.CTkEntry(panel_input, placeholder_text="http://...", height=38, fg_color="#F9FAFB", border_color="#E5E7EB")
        self.en_url.pack(fill="x", padx=20, pady=(2, 10))

        ctk.CTkLabel(panel_input, text="Limit Data", font=("Arial", 12), text_color="#6B7280").pack(anchor="w", padx=20)
        self.en_limit = ctk.CTkEntry(panel_input, placeholder_text="50", height=38, fg_color="#F9FAFB", border_color="#E5E7EB")
        self.en_limit.insert(0, "50")
        self.en_limit.pack(anchor="w", padx=20, pady=(2, 10))

        btn_row = ctk.CTkFrame(panel_input, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 20))

        self.btn_mulai = ctk.CTkButton(btn_row, text="▶  Mulai Scrapping", height=44, font=("Arial", 14, "bold"), fg_color="#10B981", hover_color="#059669", command=self._mulai_scrapping)
        self.btn_mulai.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_stop = ctk.CTkButton(btn_row, text="⏹  Stop", height=44, font=("Arial", 13), fg_color="#EF4444", hover_color="#DC2626", state="disabled", command=self._stop_scrapping)
        self.btn_stop.pack(side="left", fill="x", expand=True)

        # ── Panel Progress ──
        self.panel_progress = ctk.CTkFrame(outer, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E7EB")
        self.panel_progress.pack(fill="x", padx=30, pady=5)

        prog_top = ctk.CTkFrame(self.panel_progress, fg_color="transparent")
        prog_top.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(prog_top, text="Progress", font=("Arial", 13, "bold"), text_color="#111827").pack(side="left")
        self.lbl_persen = ctk.CTkLabel(prog_top, text="0%", font=("Arial", 12), text_color="#6B7280")
        self.lbl_persen.pack(side="right")

        self.progressbar = ctk.CTkProgressBar(self.panel_progress, height=12, fg_color="#E5E7EB", progress_color="#10B981", corner_radius=6)
        self.progressbar.set(0)
        self.progressbar.pack(fill="x", padx=20, pady=5)

        status_row = ctk.CTkFrame(self.panel_progress, fg_color="transparent")
        status_row.pack(fill="x", padx=20, pady=(2, 8))
        ctk.CTkLabel(status_row, text="Status:", font=("Arial", 11), text_color="#6B7280").pack(side="left")
        self.lbl_status = ctk.CTkLabel(status_row, text="Menunggu", font=("Arial", 11, "bold"), text_color="#6B7280")
        self.lbl_status.pack(side="left", padx=4)
        
        self.txt_log = ctk.CTkTextbox(self.panel_progress, height=80, font=("Courier", 10), fg_color="#F9FAFB", border_width=0)
        self.txt_log.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_log.configure(state="disabled")

        # ── Panel Hasil Scrapping (Desain Baru dgn Paginasi) ──
        self.panel_hasil = ctk.CTkFrame(outer, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        
        hasil_head = ctk.CTkFrame(self.panel_hasil, fg_color="transparent")
        hasil_head.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(hasil_head, text="Hasil Scrapping", font=("Arial", 18, "bold"), text_color="#111827").pack(anchor="w")
        self.lbl_jumlah = ctk.CTkLabel(hasil_head, text="", font=("Arial", 13), text_color="#6B7280")
        self.lbl_jumlah.pack(anchor="w", pady=(2,0))

        self.btn_hapus_duplikat = ctk.CTkButton(
            hasil_head, text="🗑 Hapus Semua Duplikat", width=190, height=30,
            font=("Arial", 11), fg_color="#FEE2E2", hover_color="#FECACA",
            text_color="#B91C1C", corner_radius=6, command=self._hapus_semua_duplikat
        )

        self.lbl_stat_duplikat = ctk.CTkLabel(self.panel_hasil, text="", font=("Arial", 12), text_color="#B91C1C")

        # Container Grid Cards
        self.grid_cards = ctk.CTkFrame(self.panel_hasil, fg_color="transparent")
        self.grid_cards.pack(fill="both", expand=True, padx=20, pady=10)
        for c in range(4):
            self.grid_cards.grid_columnconfigure(c, weight=1, uniform="card")

        # Container Paginasi
        self.frame_paginasi = ctk.CTkFrame(self.panel_hasil, fg_color="transparent")
        self.frame_paginasi.pack(fill="x", side="bottom", padx=25, pady=(10, 20))

        # ── Panel Aksi Bawah ──
        self.panel_aksi = ctk.CTkFrame(outer, fg_color="transparent")
        self.btn_simpan = ctk.CTkButton(
            self.panel_aksi, text="⬇ Simpan ke Database", height=44, font=("Arial", 13, "bold"),
            fg_color="#10B981", hover_color="#059669", command=self._simpan_database
        )
        self.btn_simpan.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            self.panel_aksi, text="Batal", height=44, font=("Arial", 13),
            fg_color="white", text_color="#374151", border_width=1, border_color="#D1D5DB",
            hover_color="#F3F4F6", command=self.callback_back
        ).pack(side="left", fill="x", expand=True)

    # ── LOGIKA SCRAPPING ──
    def _mulai_scrapping(self):
        url = self.en_url.get().strip()
        limit = int(self.en_limit.get().strip() or "50")
        if not url: return messagebox.showwarning("Peringatan", "URL tidak boleh kosong!")

        self.hasil_scrapping = []
        self.status_duplikat = {}
        self.current_page = 1
        self.progressbar.set(0)
        self.lbl_persen.configure(text="0%")
        self.lbl_status.configure(text="Status: Memulai...", text_color="#F59E0B")
        self.btn_mulai.configure(state="disabled", text="⏳ Scrapping...")
        self.btn_stop.configure(state="normal")
        self.lbl_notif.pack_forget()
        self._log_reset()
        self.panel_hasil.pack_forget()
        self.panel_aksi.pack_forget()

        if ScrapLogic is not None:
            self._scrap_engine = ScrapLogic(log_callback=self._cb_log, progress_callback=self._cb_progress)
            threading.Thread(target=self._worker, args=(url, limit), daemon=True).start()
        else:
            self._log("⚠ ScrapLogic tidak ditemukan — mode demo aktif.")
            self._animasi_demo(0)

    def _worker(self, url: str, limit: int):
        try: hasil_raw = self._scrap_engine.scrape(url, limit=limit)
        except Exception as e:
            self._log(f"[ERROR] {e}")
            hasil_raw = []
        hasil_card = [_konversi_scrap_ke_card(i) for i in hasil_raw]
        self.after(0, lambda: self._selesai(hasil_card))

    def _selesai(self, hasil_card: list):
        self.progressbar.set(1.0)
        self.lbl_persen.configure(text="100%")
        self.lbl_status.configure(text="Selesai", text_color="#10B981")
        self.btn_mulai.configure(state="normal", text="▶ Mulai Scrapping")
        self.btn_stop.configure(state="disabled")
        self.lbl_notif.pack(side="right")

        self.hasil_scrapping = hasil_card
        self.current_page = 1
        
        data_db = buka_json()
        for item in self.hasil_scrapping:
            self.status_duplikat[item.get("id")] = _cek_duplikat_db(item.get("identitas", {}).get("nama", ""), data_db)
            
        self._tampilkan_halaman()

    def _stop_scrapping(self):
        if self._scrap_engine: self._scrap_engine.stop()
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text="Dihentikan", text_color="#EF4444")

    # ── LOGIKA RENDER & PAGINASI ──
    def _tampilkan_halaman(self):
        for w in self.grid_cards.winfo_children(): w.destroy()
        for w in self.frame_paginasi.winfo_children(): w.destroy()

        if not self.hasil_scrapping:
            self.panel_hasil.pack_forget()
            self.panel_aksi.pack_forget()
            return

        jml_dup  = sum(1 for v in self.status_duplikat.values() if v)
        self.lbl_jumlah.configure(text=f"Ditemukan {len(self.hasil_scrapping)} destinasi wisata")

        if jml_dup > 0:
            self.btn_hapus_duplikat.place(relx=1.0, rely=0.0, anchor="ne")
            self.lbl_stat_duplikat.configure(text=f"⚠ {jml_dup} item sudah ada di database dan akan di-skip.")
            self.lbl_stat_duplikat.pack(anchor="w", padx=25, pady=(0, 10))
        else:
            self.btn_hapus_duplikat.place_forget()
            self.lbl_stat_duplikat.pack_forget()

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        data_halaman = self.hasil_scrapping[start_idx:end_idx]

        for i, data in enumerate(data_halaman):
            item_id  = data.get("id", "")
            is_dup   = self.status_duplikat.get(item_id, False)
            row, col = divmod(i, 4)

            card = CardDestinasi(self.grid_cards, data=data, on_edit=self._buka_form_edit, on_hapus=self._hapus_item, is_duplikat=is_dup)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        self._render_paginasi()

        self.panel_hasil.pack(fill="both", expand=True, padx=30, pady=5)
        self.panel_aksi.pack(fill="x", padx=30, pady=(5, 30))

    def _render_paginasi(self):
        total_pages = math.ceil(len(self.hasil_scrapping) / self.items_per_page)
        if total_pages <= 1: return

        pag_container = ctk.CTkFrame(self.frame_paginasi, fg_color="transparent")
        pag_container.pack(side="right")

        btn_prev = ctk.CTkButton(
            pag_container, text="<", width=30, height=30, 
            fg_color="#FFFFFF", border_width=1, border_color="#D1D5DB", text_color="#374151",
            hover_color="#F3F4F6", command=self._prev_page, state="normal" if self.current_page > 1 else "disabled"
        )
        btn_prev.pack(side="left", padx=4)

        for p in range(1, total_pages + 1):
            is_active = (p == self.current_page)
            btn_page = ctk.CTkButton(
                pag_container, text=str(p), width=30, height=30,
                fg_color="#10B981" if is_active else "#E5E7EB",
                text_color="#FFFFFF" if is_active else "#374151",
                hover_color="#059669" if is_active else "#D1D5DB",
                command=lambda page=p: self._go_to_page(page)
            )
            btn_page.pack(side="left", padx=4)

        btn_next = ctk.CTkButton(
            pag_container, text=">", width=30, height=30, 
            fg_color="#FFFFFF", border_width=1, border_color="#D1D5DB", text_color="#374151",
            hover_color="#F3F4F6", command=self._next_page, state="normal" if self.current_page < total_pages else "disabled"
        )
        btn_next.pack(side="left", padx=4)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._tampilkan_halaman()

    def _next_page(self):
        total_pages = math.ceil(len(self.hasil_scrapping) / self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self._tampilkan_halaman()

    def _go_to_page(self, page):
        self.current_page = page
        self._tampilkan_halaman()

    # ── AKSI DATA ──
    def _buka_form_edit(self, data: dict):
        if FormWisata is None: return messagebox.showwarning("Info", "Modul FormWisata tidak ditemukan.")
        self.pack_forget()
        def kembali():
            self.pack(fill="both", expand=True)
            frame_form.destroy()
            self._tampilkan_halaman()
        frame_form = ctk.CTkFrame(self.master, fg_color="transparent")
        frame_form.pack(fill="both", expand=True)
        # Tambahkan .pack() agar form muncul di layar
        FormWisata(frame_form, callback_back=kembali, mode="Edit Scrape", data=data).pack(fill="both", expand=True)

    def _hapus_item(self, data: dict):
        nama = data.get("identitas", {}).get("nama", "destinasi ini")
        if not messagebox.askyesno("Konfirmasi", f"Hapus '{nama}' dari hasil scrapping?"): return
        
        item_id = data.get("id", "")
        self.hasil_scrapping = [d for d in self.hasil_scrapping if d.get("id") != item_id]
        self.status_duplikat.pop(item_id, None)
        
        total_pages = math.ceil(len(self.hasil_scrapping) / self.items_per_page)
        if self.current_page > total_pages and self.current_page > 1:
            self.current_page -= 1
            
        self._tampilkan_halaman()

    def _hapus_semua_duplikat(self):
        if not messagebox.askyesno("Konfirmasi", "Hapus semua item duplikat?"): return
        id_dup = {k for k, v in self.status_duplikat.items() if v}
        self.hasil_scrapping = [d for d in self.hasil_scrapping if d.get("id") not in id_dup]
        for k in id_dup: self.status_duplikat.pop(k, None)
        self.current_page = 1
        self._tampilkan_halaman()

    def _simpan_database(self):
        if not self.hasil_scrapping: return messagebox.showwarning("Peringatan", "Tidak ada data untuk disimpan.")
        disimpan = diskip = error = 0

        for item in self.hasil_scrapping:
            item_id = item.get("id", "")
            if self.status_duplikat.get(item_id, False):
                diskip += 1
                continue
            try:
                if tambah_data_wisata is not None:
                    idnt, oper, jam, info = item.get("identitas", {}), item.get("operasional", {}), item.get("operasional", {}).get("jam_operasional", {}), item.get("informasi_tambahan", {})
                    input_mentah = {
                        "nama": idnt.get("nama", ""), "rating": idnt.get("rating", 0), "alamat": idnt.get("alamat", ""),
                        "maps": idnt.get("maps", ""), "tipe": idnt.get("tipe", "Lainnya"), "htm": oper.get("htm", "0"),
                        "hari_buka": oper.get("hari_buka", []), "jam_mulai": jam.get("buka", "08:00"),
                        "jam_selesai": jam.get("tutup", "17:00"), "fasilitas": info.get("fasilitas", []),
                        "kondisi_jalan": info.get("kondisi_jalan", "-"), "jarak_dari_kab_kota": info.get("jarak_dari_kab_kota", "-"),
                        "jumlah_ulasan": idnt.get("jumlah_ulasan", 0),
                    }
                    tambah_data_wisata(input_mentah, idnt.get("foto", ""))
                else: tambah_data(item)
                disimpan += 1
            except: error += 1

        pesan = f"✅ {disimpan} data berhasil disimpan."
        if diskip: pesan += f"\n⚠ {diskip} data di-skip (duplikat)."
        if error: pesan += f"\n❌ {error} data gagal disimpan."
        messagebox.showinfo("Hasil", pesan)
        if disimpan > 0: self.callback_back()

    # ── LOG (thread-safe) ──
    def _log_reset(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def _log(self, msg: str):
        def _w():
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", msg + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(0, _w)

    def _cb_log(self, msg: str):
        self._log(msg)

    def _cb_progress(self, current: int, total: int):
        def _u():
            pct = min(current / max(total, 1), 1.0)
            self.progressbar.set(pct)
            self.lbl_persen.configure(text=f"{int(pct*100)}%")
        self.after(0, _u)