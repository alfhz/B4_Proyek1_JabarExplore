"""
daftar_wisata.py
Halaman Kelola Data Wisata untuk aplikasi JabarExplore.
Fitur: tampil tabel, pencarian teks, filter kota & kategori, tambah/edit/hapus.
Optimasi performa: image cache, lazy batch rendering, dan pencarian dari cache data.
"""

import customtkinter as ctk
import os
from tkinter import messagebox
from PIL import Image

from src.logic.crud_engine import hapus_data_wisata
from src.logic.search_engine import cari_wisata
from src.utils.file_handler import buka_json, PROJECT_ROOT
from src.utils.validators import format_harga_idr

# ── Cache gambar & placeholder ────────────────────────────────────────────────
_IMG_CACHE: dict = {}
_IMG_PLACEHOLDER: "ctk.CTkImage | None" = None


def _get_placeholder() -> ctk.CTkImage:
    """Kembalikan gambar placeholder abu-abu 50×50 (dibuat sekali, disimpan)."""
    global _IMG_PLACEHOLDER
    if _IMG_PLACEHOLDER is None:
        img = Image.new("RGB", (50, 50), (229, 231, 235))
        _IMG_PLACEHOLDER = ctk.CTkImage(light_image=img, size=(50, 50))
    return _IMG_PLACEHOLDER


def _load_image(foto_nama: str) -> ctk.CTkImage:
    """
    Muat gambar dari disk dengan cache modul.
    Jika file tidak ditemukan atau gagal dibuka, kembalikan placeholder.
    """
    if foto_nama in _IMG_CACHE:
        return _IMG_CACHE[foto_nama]
    path = os.path.join(PROJECT_ROOT, "assets", "uploads", foto_nama)
    if not os.path.exists(path):
        path = os.path.join(PROJECT_ROOT, "assets", "placeholder.png")
    try:
        img_obj = Image.open(path).convert("RGB")
        # BILINEAR lebih cepat dari LANCZOS untuk thumbnail kecil
        img_obj.thumbnail((50, 50), Image.BILINEAR)
        ctk_img = ctk.CTkImage(light_image=img_obj, size=(50, 50))
        _IMG_CACHE[foto_nama] = ctk_img
        return ctk_img
    except Exception:
        return _get_placeholder()


# ── Helpers ekstraksi data item ───────────────────────────────────────────────

def _get_kota(item: dict) -> str:
    """Ekstrak nama kota/kabupaten dari field alamat atau kabupaten."""
    alamat = item.get("identitas", {}).get("alamat", "") or item.get("kabupaten", "")
    return alamat.split(",")[0].strip() if "," in alamat else alamat.strip()


def _get_kategori(item: dict) -> str:
    """Ekstrak kategori/tipe wisata dari data item."""
    idn = item.get("identitas", item)
    return (idn.get("tipe") or idn.get("kategori") or "Umum").strip()


# ── Kelas utama ───────────────────────────────────────────────────────────────

class DaftarWisata(ctk.CTkFrame):
    """
    Halaman Kelola Data Wisata.
    Data dibaca sekali dari JSON, lalu disimpan di _data_master untuk
    semua operasi filter & pencarian (tanpa buka file berulang kali).
    """

    # Jumlah item yang dirender per frame untuk mencegah freeze UI
    BATCH_SIZE = 15

    def __init__(self, parent, callback_form, callback_detail):
        super().__init__(parent, fg_color="transparent")
        self.callback_form   = callback_form
        self.callback_detail = callback_detail
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Lebar kolom tabel
        self.w_kota = 120
        self.w_htm  = 110
        self.w_jam  = 130
        self.w_rate = 80
        self.w_aksi = 120

        # State data
        self._data_master: list = []   # semua data dari JSON (tidak berubah kecuali refresh)
        self._data_tampil: list = []   # data yang sedang ditampilkan (hasil filter)
        self._render_idx:  int  = 0    # pointer batch rendering

        self._tampilkan_layout()
        self._muat_data_awal()

    # ─────────────────────── LAYOUT ──────────────────────────────────────────

    def _tampilkan_layout(self):
        """Bangun struktur UI: header, area filter, header tabel, scroll area."""
        # Header judul halaman
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Kelola Data Wisata",
                     font=("Arial", 28, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(header,
                     text="Tambah, edit, atau hapus data destinasi wisata Jawa Barat",
                     font=("Arial", 14), text_color="#4B5563").pack(anchor="w", pady=(5, 0))

        # Area filter & pencarian
        filter_frame = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), ipady=15, ipadx=15)

        # Baris pencarian teks
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        self.teks_ui_nama_wisata = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Cari destinasi wisata...",
            height=35, fg_color="white", text_color="black"
        )
        self.teks_ui_nama_wisata.pack(fill="x", expand=True)
        # Debounce: pencarian dijadwalkan ulang setiap keystroke agar tidak lag
        self._search_after_id = None
        self.teks_ui_nama_wisata.bind("<KeyRelease>", self._on_search_keyrelease)

        # Baris dropdown filter kota + kategori + tombol tambah
        combo_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        combo_frame.pack(fill="x")

        self.filter_kota = ctk.CTkComboBox(
            combo_frame,
            values=["Semua Kota / Kabupaten"],   # akan diisi setelah data dimuat
            width=190, fg_color="white", text_color="black",
            command=self._terapkan_filter          # dipanggil saat nilai berubah
        )
        self.filter_kota.set("Semua Kota / Kabupaten")
        self.filter_kota.pack(side="left", padx=(0, 10))

        self.filter_kategori = ctk.CTkComboBox(
            combo_frame,
            values=["Semua Kategori"],            # akan diisi setelah data dimuat
            width=160, fg_color="white", text_color="black",
            command=self._terapkan_filter          # dipanggil saat nilai berubah
        )
        self.filter_kategori.set("Semua Kategori")
        self.filter_kategori.pack(side="left", padx=10)

        ctk.CTkButton(
            combo_frame, text="+ Tambah Data",
            font=("Arial", 12, "bold"),
            fg_color="#10B981", hover_color="#059669", text_color="white",
            command=lambda: self.callback_form("Tambah", None)
        ).pack(side="right")

        # Header kolom tabel
        table_header = ctk.CTkFrame(self, fg_color="#F9FAFB", corner_radius=5)
        table_header.pack(fill="x", pady=(0, 5), ipady=8)
        table_header.grid_columnconfigure(0, weight=1)
        for col, (teks, w, anchor) in enumerate([
            ("NAMA WISATA", None, "w"),
            ("KOTA",        self.w_kota, "w"),
            ("HARGA",       self.w_htm,  "w"),
            ("OPERASIONAL", self.w_jam,  "w"),
            ("RATING",      self.w_rate, "w"),
            ("AKSI",        self.w_aksi, "e"),
        ]):
            kw = {"width": w} if w else {}
            pad = {"padx": 20} if col in (0, 5) else {}
            ctk.CTkLabel(table_header, text=teks, font=("Arial", 11, "bold"),
                         text_color="#9CA3AF", anchor=anchor, **kw).grid(
                row=0, column=col, sticky=f"{'ew' if col == 0 else 'w' if anchor == 'w' else 'e'}",
                **pad)

        # Area scroll untuk baris data
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

    # ─────────────────────── LOAD DATA ───────────────────────────────────────

    def _muat_data_awal(self):
        """
        Baca JSON sekali saat halaman pertama kali dibuka.
        Setelah data tersedia, isi dropdown filter dan render tabel.
        """
        self._data_master = buka_json() or []
        self._isi_dropdown_filter()
        self._data_tampil  = list(self._data_master)
        self._render_idx   = 0
        self._render_batch()

    def _isi_dropdown_filter(self):
        """Isi pilihan dropdown kota dan kategori dari data master."""
        kota_set = set()
        kat_set  = set()
        for item in self._data_master:
            kota_set.add(_get_kota(item))
            kat_set.add(_get_kategori(item))

        # Hilangkan nilai kosong, urutkan alfabet
        kota_sorted = sorted(k for k in kota_set if k)
        kat_sorted  = sorted(k for k in kat_set  if k)

        self.filter_kota.configure(
            values=["Semua Kota / Kabupaten"] + kota_sorted
        )
        self.filter_kategori.configure(
            values=["Semua Kategori"] + kat_sorted
        )

    # ─────────────────────── FILTER & PENCARIAN ──────────────────────────────

    def _terapkan_filter(self, _=None):
        """
        Terapkan kombinasi filter kota + kategori + teks pencarian.
        Dipanggil dari: perubahan dropdown kota, dropdown kategori, atau search.
        """
        pilih_kota = self.filter_kota.get()
        pilih_kat  = self.filter_kategori.get()
        teks       = self.teks_ui_nama_wisata.get().strip().lower()

        # Mulai dari data master (tanpa buka file lagi)
        hasil = self._data_master

        if pilih_kota and pilih_kota != "Semua Kota / Kabupaten":
            hasil = [i for i in hasil if _get_kota(i) == pilih_kota]

        if pilih_kat and pilih_kat != "Semua Kategori":
            hasil = [i for i in hasil if _get_kategori(i) == pilih_kat]

        if teks:
            hasil = cari_wisata(teks, hasil)

        if not hasil:
            self._tampil_pesan_kosong(
                f"Tidak ada wisata yang cocok dengan filter/pencarian."
            )
        else:
            self.refresh_tabel(hasil)

    def _on_search_keyrelease(self, event=None):
        """
        Debounce input pencarian: tunggu 300 ms setelah ketikan terakhir
        sebelum menjalankan filter, agar tidak terjadi lag per keystroke.
        """
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._terapkan_filter)

    # Alias publik untuk kompatibilitas pemanggilan dari luar
    def proses_pencarian(self, event=None):
        """Jalankan pencarian berdasarkan input teks (alias _terapkan_filter)."""
        self._terapkan_filter()

    # ─────────────────────── RENDER TABEL ────────────────────────────────────

    def refresh_tabel(self, data_master=None):
        """
        Bersihkan scroll area lalu render ulang data secara bertahap.
        Jika data_master tidak disediakan, gunakan _data_master (cache JSON).
        """
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        if data_master is None:
            data_master = self._data_master
        if not data_master:
            ctk.CTkLabel(self.scroll_frame, text="Belum ada data wisata.",
                         text_color="gray").pack(pady=20)
            return
        self._data_tampil = list(data_master)
        self._render_idx  = 0
        self._render_batch()

    def _render_batch(self):
        """
        Render BATCH_SIZE kartu berikutnya ke scroll area.
        Sisa item dijadwalkan via after() agar event loop tidak terblokir.
        """
        end = min(self._render_idx + self.BATCH_SIZE, len(self._data_tampil))
        for i in range(self._render_idx, end):
            self.render_kartu_wisata(self._data_tampil[i])
        self._render_idx = end
        if self._render_idx < len(self._data_tampil):
            self.after(16, self._render_batch)

    def _tampil_pesan_kosong(self, pesan: str):
        """Kosongkan scroll area dan tampilkan pesan tidak ada hasil."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.scroll_frame, text=f"🔍 {pesan}",
                     font=("Arial", 14, "italic"),
                     text_color="#9CA3AF").pack(pady=60)

    # Alias untuk kompatibilitas nama lama
    def tampil_pesan_error(self, pesan: str):
        self._tampil_pesan_kosong(pesan)

    # ─────────────────────── RENDER KARTU ────────────────────────────────────

    def render_kartu_wisata(self, item: dict):
        """Render satu baris kartu wisata (nama, kota, harga, operasional, rating, aksi)."""
        row = ctk.CTkFrame(self.scroll_frame, fg_color="white", corner_radius=5)
        row.pack(fill="x", pady=4, ipady=10)
        row.grid_columnconfigure(0, weight=1)

        identitas   = item.get("identitas", {})
        operasional = item.get("operasional", {})
        jam_data    = operasional.get("jam_operasional", {})

        # Parse jam buka-tutup (bisa berupa dict {jam, menit} atau string langsung)
        buka  = jam_data.get("buka",  {})
        tutup = jam_data.get("tutup", {})
        waktu_buka  = (f"{str(buka.get('jam','00')).zfill(2)}:{str(buka.get('menit','00')).zfill(2)}"
                       if isinstance(buka, dict) else str(buka))
        waktu_tutup = (f"{str(tutup.get('jam','00')).zfill(2)}:{str(tutup.get('menit','00')).zfill(2)}"
                       if isinstance(tutup, dict) else str(tutup))
        jam_tampil = f"{waktu_buka} - {waktu_tutup}"
        if not jam_data or jam_tampil in ("{} - {}", "- -"):
            jam_tampil = "-"

        nama      = identitas.get("nama", "-")
        tipe      = identitas.get("tipe", "Umum")
        foto_nama = identitas.get("foto", "default.png")
        kota      = _get_kota(item)
        rating    = identitas.get("rating", "0.0")
        htm       = format_harga_idr(operasional.get("htm", 0))

        # Kolom 0: foto thumbnail (dari cache) + nama + tipe
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20)

        ctk.CTkLabel(info_frame, image=_load_image(foto_nama), text="").pack(
            side="left", padx=(0, 10))

        teks_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        teks_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(teks_frame, text=nama,
                     font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(teks_frame, text=tipe,
                     font=("Arial", 11), text_color="#6B7280", anchor="w").pack(fill="x")

        # Kolom 1–4: detail tabel
        ctk.CTkLabel(row, text=kota,      width=self.w_kota, anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row, text=htm,       width=self.w_htm,  anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(row, text=jam_tampil,width=self.w_jam,  anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(row, text=f"★ {rating}", width=self.w_rate,
                     font=("Arial", 12, "bold"), text_color="#F59E0B",
                     anchor="w").grid(row=0, column=4, sticky="w")

        # Kolom 5: tombol aksi (lihat, edit, hapus)
        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=self.w_aksi)
        action_frame.grid(row=0, column=5, sticky="e", padx=20)

        ctk.CTkButton(action_frame, text="👁️", width=30, fg_color="transparent",
                      text_color="#10B981",
                      command=lambda i=item: self.callback_detail(i)).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="✏️", width=30, fg_color="transparent",
                      text_color="#3B82F6",
                      command=lambda i=item: self.callback_form("Edit", i)).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="🗑️", width=30, fg_color="transparent",
                      text_color="#EF4444",
                      command=lambda id_w=item.get("id"), nama_w=nama:
                          self.notif_konfirmasi(id_w, nama_w)).pack(side="left", padx=2)

    # ─────────────────────── AKSI ─────────────────────────────────────────────

    def notif_konfirmasi(self, id_wisata: str, nama_wisata: str):
        """Tampilkan dialog konfirmasi hapus; jika ya, hapus data dan perbarui tabel."""
        if messagebox.askyesno("Konfirmasi Hapus",
                               f"Apakah Anda yakin ingin menghapus '{nama_wisata}'?"):
            hapus_data_wisata(id_wisata)
            # Hapus cache gambar agar konsisten setelah penghapusan
            _IMG_CACHE.clear()
            # Muat ulang data dari file setelah perubahan
            self._data_master = buka_json() or []
            self._isi_dropdown_filter()
            self.refresh_tabel()
            messagebox.showinfo("Berhasil", "Data wisata berhasil dihapus.")

    # ─────────────────────── ALIAS KOMPATIBILITAS ─────────────────────────────

    def tampilkan_halaman_daftar_wisata(self):
        """Alias untuk _tampilkan_layout (menjaga kompatibilitas pemanggilan lama)."""
        self._tampilkan_layout()