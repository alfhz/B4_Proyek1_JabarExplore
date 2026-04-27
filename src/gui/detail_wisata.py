"""
detail_wisata.py  — VERSI OPTIMASI
Perbaikan performa:
  1. Gambar di-load secara async (thread terpisah) → main thread tidak freeze.
  2. Placeholder ditampilkan dulu, gambar asli muncul setelah selesai load.
  3. Referensi CTkImage disimpan di self agar tidak di-GC Tkinter.
"""

import customtkinter as ctk
import os
import threading
from PIL import Image
from src.utils.file_handler import PROJECT_ROOT
from src.utils.validators import format_harga_idr, cek_kondisi_akses


class DetailWisata(ctk.CTkFrame):
    """Menampilkan detail destinasi wisata dengan tata letak dua kolom."""

    _IMG_SIZE = (200, 200)

    def __init__(self, parent, callback_back, data):
        super().__init__(parent, fg_color="transparent")
        self.callback_back = callback_back
        self.data          = data
        self._ctk_img      = None   # simpan referensi agar tidak ter-GC
        self.pack(fill="both", expand=True, padx=30, pady=20)
        self._build_ui()

    # ─────────────────────── BUILD UI ───────────────────────────────────────

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkButton(header, text="← Kembali", width=100, command=self.callback_back).pack(side="left")
        ctk.CTkLabel(
            header, text="Detail Destinasi Wisata",
            font=("Arial", 24, "bold")
        ).pack(side="left", padx=20)

        # Konten scroll
        scroll = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        scroll.pack(fill="both", expand=True)

        identitas   = self.data.get("identitas", {})
        operasional = self.data.get("operasional", {})
        tambahan    = self.data.get("informasi_tambahan", {})

        # ── Baris foto + info dasar ──────────────────────────────────────
        top_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=10)

        # Placeholder label (ditampilkan langsung)
        w, h    = self._IMG_SIZE
        self._lbl_img = ctk.CTkLabel(
            top_frame, text="⏳",
            width=w, height=h,
            fg_color="#E5E7EB", corner_radius=8
        )
        self._lbl_img.pack(side="left", padx=20)

        # Load gambar di background
        foto_nama = identitas.get("foto", "default.png")
        path_foto = os.path.join(PROJECT_ROOT, "assets", "uploads", foto_nama)
        if not os.path.exists(path_foto):
            path_foto = os.path.join(PROJECT_ROOT, "assets", "placeholder.png")
        threading.Thread(
            target=self._load_image,
            args=(path_foto,),
            daemon=True
        ).start()

        # Info ringkas
        info = ctk.CTkFrame(top_frame, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=20)
        ctk.CTkLabel(info, text=identitas.get("nama", "-"),  font=("Arial", 20, "bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=f"⭐ {identitas.get('rating', 0)} / 5.0", font=("Arial", 14)).pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(info, text=f"📍 {identitas.get('alamat', '-')}",      font=("Arial", 12)).pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(info, text=f"🗺️ {identitas.get('maps', '-')}",        font=("Arial", 12)).pack(anchor="w")

        # ── Grid detail ──────────────────────────────────────────────────
        detail_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        detail_frame.pack(fill="x", padx=20, pady=20)
        detail_frame.grid_columnconfigure(0, weight=1)
        detail_frame.grid_columnconfigure(1, weight=1)

        htm_val      = format_harga_idr(operasional.get("htm", 0))
        fasilitas    = ", ".join(tambahan.get("fasilitas", [])) or "-"
        kondisi      = tambahan.get("kondisi_jalan", "")
        deskripsi_jl = cek_kondisi_akses(kondisi)

        rows = [
            ("Tipe Wisata:",            identitas.get("tipe", "-")),
            ("Harga Tiket:",            htm_val),
            ("Jam Buka:",               operasional.get("jam_buka", "-")),
            ("Fasilitas:",              fasilitas),
            ("Kondisi Jalan:",          f"{kondisi} - {deskripsi_jl}"),
            ("Jarak dari Pusat Kota:",  tambahan.get("jarak_dari_kab_kota", "-")),
            ("Ditambahkan pada:",       self.data.get("tanggal_ditambahkan", "-")),
        ]

        for r, (label, value) in enumerate(rows):
            ctk.CTkLabel(detail_frame, text=label, font=("Arial", 13, "bold")).grid(
                row=r, column=0, sticky="w", pady=5
            )
            ctk.CTkLabel(detail_frame, text=value).grid(
                row=r, column=1, sticky="w", pady=5
            )

    # ─────────────────────── ASYNC IMAGE LOAD ───────────────────────────────

    def _load_image(self, path: str):
        """Berjalan di thread terpisah; update label via after() di main thread."""
        try:
            img     = Image.open(path)
            img     = img.resize(self._IMG_SIZE, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=self._IMG_SIZE)
            # Simpan referensi sebelum scheduling agar tidak ter-GC
            self._ctk_img = ctk_img
            self.after(0, lambda: self._lbl_img.configure(image=ctk_img, text=""))
        except Exception:
            self.after(0, lambda: self._lbl_img.configure(text="[Gambar tidak tersedia]", fg_color="#E5E7EB"))