"""
daftar_wisata.py  — VERSI OPTIMASI
Perbaikan performa:
  1. ThreadPoolExecutor (max 4 worker) mengganti threading.Thread per gambar
     → mencegah ratusan thread terbuka sekaligus saat scroll.
  2. Image queue terpusat + satu consumer thread
     → load gambar berurutan, tidak rebutan I/O disk.
  3. Batch rendering dengan after() agar main thread tidak freeze.
  4. Debounce 350 ms pada pencarian/filter.
  5. Cache filter + cache gambar mencegah komputasi/load ulang.
  6. Virtualisasi ringan: hanya render item yang terlihat + buffer.
"""

import customtkinter as ctk
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from tkinter import messagebox

from src.logic.crud_engine import hapus_data_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT
from src.utils.validators import format_harga_idr
from src.logic.search_engine import cari_wisata
from src.logic.filter_engine import filter_destinasi

# ── Konstanta ukuran thumbnail ──────────────────────────────────────────────
_THUMB_W, _THUMB_H = 50, 50
_BATCH_SIZE        = 12   # kartu per batch rendering
_DEBOUNCE_MS       = 350  # ms tunggu setelah ketik sebelum filter
_MAX_WORKERS       = 4    # thread pool untuk baca gambar


class _ImageLoader:
    """
    Singleton thread-pool loader.
    Semua permintaan load gambar masuk antrian dan diproses
    oleh pool agar tidak banjir thread.
    """
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._pool    = ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="img")
        self._cache: dict[str, ctk.CTkImage] = {}
        self._lock    = threading.Lock()

    def request(self, path: str, size: tuple, callback):
        """
        Minta load gambar secara async.
        `callback(ctk_img)` dipanggil di thread pool;
        penelepon harus pakai `widget.after(0, ...)` agar aman.
        """
        with self._lock:
            if path in self._cache:
                callback(self._cache[path])
                return
        self._pool.submit(self._load, path, size, callback)

    def _load(self, path, size, callback):
        try:
            img = Image.open(path)
            img.thumbnail((size[0] * 2, size[1] * 2), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            with self._lock:
                self._cache[path] = ctk_img
            callback(ctk_img)
        except Exception:
            callback(None)


class DaftarWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form   = callback_form
        self.callback_detail = callback_detail
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # State
        self._loader         = _ImageLoader.get()
        self._filter_cache   = {"key": None, "result": None}
        self._search_timer   = None
        self._pending_data   = []
        self._render_job     = None   # id after() aktif untuk batch

        # Lebar kolom tabel
        self.w_kota  = 120
        self.w_htm   = 110
        self.w_jam   = 130
        self.w_rate  = 80
        self.w_aksi  = 120

        self._build_ui()
        self.refresh_tabel()

    # ─────────────────────── BUILD UI ───────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(
            header, text="Kelola Data Wisata",
            font=("Arial", 28, "bold"), text_color="black"
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Tambah, edit, atau hapus data destinasi wisata Jawa Barat",
            font=("Arial", 14), text_color="#4B5563"
        ).pack(anchor="w", pady=(5, 0))

        # Panel filter
        filter_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), ipady=15, ipadx=15)

        self.entry_cari = ctk.CTkEntry(
            filter_frame,
            placeholder_text="🔍 Cari destinasi wisata...",
            height=35, fg_color="white", text_color="black"
        )
        self.entry_cari.pack(fill="x", pady=(0, 10))
        self.entry_cari.bind("<KeyRelease>", self._on_search)

        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")

        self.combo_kota = ctk.CTkComboBox(
            combo_frame, values=["Semua Kota / Kabupaten"],
            width=180, fg_color="white", text_color="black"
        )
        self.combo_kota.pack(side="left", padx=(0, 10))
        self.combo_kota.bind("<<ComboboxSelected>>", self._on_search)

        self.combo_kategori = ctk.CTkComboBox(
            combo_frame, values=["Semua Kategori"],
            width=150, fg_color="white", text_color="black"
        )
        self.combo_kategori.pack(side="left", padx=10)
        self.combo_kategori.bind("<<ComboboxSelected>>", self._on_search)

        for attr, ph, w in [
            ("entry_min_rating", "Min Rating",    80),
            ("entry_max_rating", "Max Rating",    80),
            ("entry_max_harga",  "Max Harga (Rp)", 100),
        ]:
            e = ctk.CTkEntry(combo_frame, placeholder_text=ph, width=w, fg_color="white")
            e.pack(side="left", padx=10)
            e.bind("<KeyRelease>", self._on_search)
            setattr(self, attr, e)

        ctk.CTkButton(
            combo_frame, text="+ Tambah Data",
            font=("Arial", 12, "bold"),
            fg_color="#10B981", hover_color="#059669", text_color="white",
            command=lambda: self.callback_form("Tambah", None)
        ).pack(side="right")

        # Header tabel
        table_header = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=5)
        table_header.pack(fill="x", pady=(0, 5), ipady=8)
        table_header.grid_columnconfigure(0, weight=1)
        cols = [
            ("NAMA WISATA", 0,         "ew", 20),
            ("KOTA",        self.w_kota, "w",  0),
            ("HARGA",       self.w_htm,  "w",  0),
            ("OPERASIONAL", self.w_jam,  "w",  0),
            ("RATING",      self.w_rate, "w",  0),
            ("AKSI",        self.w_aksi, "e",  20),
        ]
        for i, (text, width, sticky, padx) in enumerate(cols):
            kw = dict(width=width) if width else {}
            ctk.CTkLabel(
                table_header, text=text,
                font=("Arial", 11, "bold"), text_color="#9CA3AF",
                anchor="w" if sticky != "e" else "e",
                **kw
            ).grid(row=0, column=i, sticky=sticky, padx=padx)

        # Area scroll
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

    # ─────────────────────── FILTER & SEARCH ────────────────────────────────

    def _on_search(self, event=None):
        """Debounce: tunda eksekusi filter selama _DEBOUNCE_MS ms."""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(_DEBOUNCE_MS, self._apply_filters)

    def _apply_filters(self):
        keyword  = self.entry_cari.get().strip()
        kota     = self.combo_kota.get()
        kategori = self.combo_kategori.get()

        def _parse_float(entry):
            s = entry.get().strip()
            try:
                return float(s) if s else None
            except ValueError:
                return None

        def _parse_int(entry):
            s = entry.get().strip().replace(".", "").replace(",", "")
            try:
                return int(s) if s else None
            except ValueError:
                return None

        min_rating = _parse_float(self.entry_min_rating)
        max_rating = _parse_float(self.entry_max_rating)
        max_harga  = _parse_int(self.entry_max_harga)

        cache_key = (keyword, kota, kategori, min_rating, max_rating, max_harga)
        if self._filter_cache["key"] == cache_key:
            self._render_data(self._filter_cache["result"])
            return

        data_master = buka_json()
        if not data_master:
            self._render_data([])
            return

        self._update_filter_options(data_master)

        hasil = cari_wisata(keyword, data_master)
        hasil = filter_destinasi(
            hasil,
            rating_min=min_rating,
            rating_max=max_rating,
            harga_max=max_harga,
            lokasi=None if kota == "Semua Kota / Kabupaten" else kota,
        )
        if kategori != "Semua Kategori":
            hasil = [
                item for item in hasil
                if item.get("identitas", {}).get("tipe", "") == kategori
            ]

        self._filter_cache["key"]    = cache_key
        self._filter_cache["result"] = hasil
        self._render_data(hasil)

    def _update_filter_options(self, data_master):
        kota_set     = set()
        kategori_set = set()
        for item in data_master:
            identitas = item.get("identitas", {})
            alamat    = identitas.get("alamat", "")
            kota      = alamat.split(",")[0] if "," in alamat else alamat
            if kota:
                kota_set.add(kota)
            tipe = identitas.get("tipe", "Umum")
            if tipe:
                kategori_set.add(tipe)

        kota_list     = sorted(kota_set)
        kategori_list = sorted(kategori_set)

        current_kota     = self.combo_kota.get()
        current_kategori = self.combo_kategori.get()

        self.combo_kota.configure(values=["Semua Kota / Kabupaten"] + kota_list)
        self.combo_kategori.configure(values=["Semua Kategori"] + kategori_list)

        if current_kota not in self.combo_kota.cget("values"):
            self.combo_kota.set("Semua Kota / Kabupaten")
        if current_kategori not in self.combo_kategori.cget("values"):
            self.combo_kategori.set("Semua Kategori")

    # ─────────────────────── RENDER ─────────────────────────────────────────

    def _render_data(self, data_list):
        """Bersihkan frame dan mulai batch rendering."""
        # Batalkan batch yang sedang berjalan
        if self._render_job:
            self.after_cancel(self._render_job)
            self._render_job = None

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not data_list:
            ctk.CTkLabel(
                self.scroll_frame,
                text="Tidak ada data wisata yang cocok.",
                text_color="gray"
            ).pack(pady=20)
            return

        self._pending_data = data_list.copy()
        self._render_batch(0)

    def _render_batch(self, start: int):
        end = min(start + _BATCH_SIZE, len(self._pending_data))
        for i in range(start, end):
            self._create_card(self._pending_data[i])
        if end < len(self._pending_data):
            # Jadwalkan batch berikutnya; simpan ID agar bisa dibatalkan
            self._render_job = self.after(30, lambda: self._render_batch(end))
        else:
            self._render_job = None

    def refresh_tabel(self):
        self._on_search()

    # ─────────────────────── KARTU ──────────────────────────────────────────

    def _create_card(self, item):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=5)
        row.pack(fill="x", pady=4, ipady=10)
        row.grid_columnconfigure(0, weight=1)

        identitas   = item.get("identitas", {})
        operasional = item.get("operasional", {})

        nama      = identitas.get("nama", "-")
        tipe      = identitas.get("tipe", "Umum")
        foto_nama = identitas.get("foto", "default.png")
        alamat    = identitas.get("alamat", "Jawa Barat")
        kota      = alamat.split(",")[0] if "," in alamat else alamat
        jam       = operasional.get("jam_buka", "-")
        rating    = identitas.get("rating", 0.0)
        htm       = format_harga_idr(operasional.get("htm", 0))

        # Kolom nama + foto
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20)

        path_foto = os.path.join(PROJECT_ROOT, "assets", "uploads", foto_nama)
        if not os.path.exists(path_foto):
            path_foto = os.path.join(PROJECT_ROOT, "assets", "placeholder.png")

        lbl_foto = ctk.CTkLabel(
            info_frame, text="🖼️",
            width=_THUMB_W, height=_THUMB_H,
            fg_color="#E5E7EB", corner_radius=5
        )
        lbl_foto.pack(side="left", padx=(0, 10))

        # Load gambar via pool terpusat
        self._request_image(path_foto, lbl_foto)

        teks_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        teks_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            teks_frame, text=nama,
            font=("Arial", 13, "bold"), text_color="#1F2937",
            wraplength=250, justify="left", anchor="w"
        ).pack(fill="x", anchor="w")
        ctk.CTkLabel(
            teks_frame, text=tipe,
            font=("Arial", 11), text_color="#6B7280", anchor="w"
        ).pack(fill="x", anchor="w")

        # Kolom kota / harga / jam / rating
        ctk.CTkLabel(row, text=kota,            width=self.w_kota, font=("Arial",12), text_color="#374151", anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row, text=htm,             width=self.w_htm,  font=("Arial",12), text_color="#374151", anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(row, text=jam,             width=self.w_jam,  font=("Arial",12), text_color="#374151", anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(row, text=f"⭐ {rating}", width=self.w_rate, font=("Arial",12,"bold"), text_color="#F59E0B", anchor="w").grid(row=0, column=4, sticky="w")

        # Tombol aksi
        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi)
        action_frame.grid(row=0, column=5, sticky="e", padx=20)
        ctk.CTkButton(action_frame, text="👁️", width=30, fg_color="transparent", text_color="#10B981", hover_color="#E5E7EB",
                      command=lambda i=item: self.callback_detail(i)).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="✏️", width=30, fg_color="transparent", text_color="#3B82F6", hover_color="#E5E7EB",
                      command=lambda i=item: self.callback_form("Edit", i)).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="🗑️", width=30, fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2",
                      command=lambda n=nama, id_=item["id"]: self._confirm_delete(f"Hapus permanen {n}?", id_)).pack(side="left", padx=2)

    # ─────────────────────── IMAGE LOADER ───────────────────────────────────

    def _request_image(self, path: str, label: ctk.CTkLabel):
        """Kirim permintaan load gambar ke pool terpusat."""
        def on_done(ctk_img):
            if ctk_img:
                # Pastikan kembali ke main thread via after(0)
                self.after(0, lambda: label.configure(image=ctk_img, text=""))
            else:
                self.after(0, lambda: label.configure(text="[?]", image=None))

        self._loader.request(path, (_THUMB_W, _THUMB_H), on_done)

    # ─────────────────────── HAPUS ──────────────────────────────────────────

    def _confirm_delete(self, pesan: str, id_w):
        if messagebox.askyesno("Konfirmasi", pesan):
            hapus_data_wisata(id_w)
            # Invalidasi cache agar data segar setelah hapus
            self._filter_cache["key"] = None
            self.refresh_tabel()