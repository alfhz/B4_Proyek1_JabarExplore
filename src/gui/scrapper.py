import sys
import os

# Pastikan root project ada di path agar import src.* berjalan
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import customtkinter as ctk
from src.logic.scrap_logic import ScrapLogic
from src.utils.threads import ScrapThread
from src.utils.file_handler import get_jumlah_data, hapus_semua


# ── Tema & palet warna ──────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_WARNA_HIJAU  = "#2ecc71"
_WARNA_MERAH  = "#e74c3c"
_WARNA_KUNING = "#f39c12"
_WARNA_ABU    = "#7f8c8d"


# ============================================================================
class ScrapeFrame(ctk.CTkFrame):
    """
    Panel scraping utama — bagian dari UI JabarExplore.

    Hubungan file:
        scrapper.py  →  threads.py  →  scrap_logic.py
                                    →  validators.py
                                    →  file_handler.py

    Komponen UI:
        - Input URL target
        - Spinner limit (1–200)
        - Tombol Mulai / Hentikan
        - Progress bar
        - Log area (ScrolledTextbox)
        - Counter data tersimpan
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self._thread: ScrapThread | None = None
        self._scraper: ScrapLogic | None = None

        self._build_ui()
        self._refresh_counter()

    # ── Builder UI ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Judul panel
        ctk.CTkLabel(
            self, text="Scraping Wisata Jawa Barat",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=(16, 4), padx=16, sticky="w")

        ctk.CTkLabel(
            self, text="Ambil data dari website wisata dan simpan ke database lokal.",
            font=ctk.CTkFont(size=12), text_color=_WARNA_ABU
        ).grid(row=1, column=0, padx=16, sticky="w")

        # ── Form input ──────────────────────────────────────────────────────
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=2, column=0, padx=16, pady=(12, 0), sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        # URL
        ctk.CTkLabel(form, text="URL Target:", width=90, anchor="w").grid(
            row=0, column=0, padx=(0, 8), pady=6, sticky="w"
        )
        self._entry_url = ctk.CTkEntry(
            form,
            placeholder_text="https://contoh-website-wisata.com/daftar",
            height=36
        )
        self._entry_url.grid(row=0, column=1, sticky="ew", pady=6)

        # Limit
        ctk.CTkLabel(form, text="Limit Data:", width=90, anchor="w").grid(
            row=1, column=0, padx=(0, 8), pady=6, sticky="w"
        )
        limit_frame = ctk.CTkFrame(form, fg_color="transparent")
        limit_frame.grid(row=1, column=1, sticky="w", pady=6)

        self._var_limit = ctk.IntVar(value=50)
        self._slider_limit = ctk.CTkSlider(
            limit_frame, from_=1, to=200, number_of_steps=199,
            variable=self._var_limit, width=200,
            command=self._on_slider_change
        )
        self._slider_limit.grid(row=0, column=0, padx=(0, 10))

        self._lbl_limit_val = ctk.CTkLabel(
            limit_frame, text="50 data", width=70, anchor="w"
        )
        self._lbl_limit_val.grid(row=0, column=1)

        # ── Tombol aksi ─────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=16, pady=10, sticky="ew")

        self._btn_mulai = ctk.CTkButton(
            btn_frame, text="Mulai Scraping",
            width=140, height=36, fg_color=_WARNA_HIJAU, hover_color="#27ae60",
            command=self._mulai_scraping
        )
        self._btn_mulai.pack(side="left", padx=(0, 8))

        self._btn_henti = ctk.CTkButton(
            btn_frame, text="Hentikan",
            width=120, height=36, fg_color=_WARNA_MERAH, hover_color="#c0392b",
            state="disabled", command=self._hentikan_scraping
        )
        self._btn_henti.pack(side="left", padx=(0, 8))

        self._btn_reset = ctk.CTkButton(
            btn_frame, text="Reset DB",
            width=100, height=36, fg_color=_WARNA_KUNING, hover_color="#e67e22",
            command=self._reset_database
        )
        self._btn_reset.pack(side="left")

        # ── Progress bar ────────────────────────────────────────────────────
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.grid(row=4, column=0, padx=16, pady=(0, 4), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(progress_frame, height=12)
        self._progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._progress.set(0)

        self._lbl_progress = ctk.CTkLabel(progress_frame, text="0%", width=40)
        self._lbl_progress.grid(row=0, column=1)

        # ── Counter ─────────────────────────────────────────────────────────
        self._lbl_counter = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color=_WARNA_ABU
        )
        self._lbl_counter.grid(row=5, column=0, padx=16, pady=(0, 4), sticky="w")

        # ── Log area ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Log Proses:", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=6, column=0, padx=16, sticky="w")

        self._log_box = ctk.CTkTextbox(self, height=300, font=ctk.CTkFont(family="Consolas", size=11))
        self._log_box.grid(row=7, column=0, padx=16, pady=(4, 16), sticky="nsew")
        self.grid_rowconfigure(7, weight=1)
        self._log_box.configure(state="disabled")

    # ── Aksi tombol ─────────────────────────────────────────────────────────

    def _mulai_scraping(self):
        url   = self._entry_url.get().strip()
        limit = self._var_limit.get()

        if not url:
            self._log("[ERROR] URL tidak boleh kosong.")
            return
        if not url.startswith("http"):
            self._log("[ERROR] URL harus diawali 'http://' atau 'https://'")
            return
        if self._thread and self._thread.is_running:
            self._log("[WARN] Scraping sedang berjalan.")
            return

        # Reset UI
        self._progress.set(0)
        self._lbl_progress.configure(text="0%")
        self._bersihkan_log()
        self._set_tombol_scraping(True)

        # Buat scraper dengan callback ke UI
        self._scraper = ScrapLogic(
            log_callback      = self._log,
            progress_callback = self._update_progress,
        )

        # Buat dan jalankan thread
        self._thread = ScrapThread(
            scraper  = self._scraper,
            url      = url,
            limit    = limit,
            on_done  = self._on_done,
            on_error = self._on_error,
        )
        self._thread.start()

    def _hentikan_scraping(self):
        if self._thread and self._thread.is_running:
            self._log("[STOP] Menghentikan scraping...")
            self._thread.stop()
            self._set_tombol_scraping(False)

    def _reset_database(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Konfirmasi Reset")
        dialog.geometry("320x140")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Hapus SEMUA data wisata?",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            dialog, text="Tindakan ini tidak bisa dibatalkan.",
            text_color=_WARNA_ABU
        ).pack(pady=(0, 14))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame, text="Ya, Hapus", width=110, fg_color=_WARNA_MERAH,
            hover_color="#c0392b",
            command=lambda: self._konfirmasi_reset(dialog)
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            btn_frame, text="Batal", width=90,
            command=dialog.destroy
        ).pack(side="left", padx=6)

    def _konfirmasi_reset(self, dialog):
        dialog.destroy()
        hapus_semua()
        self._log("[RESET] Database berhasil dikosongkan.")
        self._progress.set(0)
        self._lbl_progress.configure(text="0%")
        self._refresh_counter()

    # ── Callbacks dari thread (thread-safe via .after) ───────────────────────

    def _on_done(self, hasil: list):
        self.after(0, lambda: self._selesai(len(hasil)))

    def _on_error(self, pesan: str):
        self.after(0, lambda: self._error_handler(pesan))

    def _selesai(self, jumlah: int):
        self._log(f"\n[SELESAI] {jumlah} data baru berhasil disimpan ke database.")
        self._set_tombol_scraping(False)
        self._refresh_counter()

    def _error_handler(self, pesan: str):
        self._log(f"[ERROR] {pesan}")
        self._set_tombol_scraping(False)

    # ── Update UI ────────────────────────────────────────────────────────────

    def _update_progress(self, saved: int, total: int):
        """Dipanggil dari thread — gunakan .after() agar aman di customtkinter."""
        persen = saved / total if total > 0 else 0

        def _update():
            self._progress.set(persen)
            self._lbl_progress.configure(text=f"{int(persen * 100)}%")
            self._refresh_counter()

        self.after(0, _update)

    def _log(self, pesan: str):
        """Menambah baris ke log area. Thread-safe via .after()."""
        def _tulis():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", pesan + "\n")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")

        # Cek apakah kita di main thread atau worker thread
        try:
            self.after(0, _tulis)
        except RuntimeError:
            pass   # widget sudah dihancurkan

    def _bersihkan_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _set_tombol_scraping(self, sedang_jalan: bool):
        if sedang_jalan:
            self._btn_mulai.configure(state="disabled")
            self._btn_henti.configure(state="normal")
        else:
            self._btn_mulai.configure(state="normal")
            self._btn_henti.configure(state="disabled")

    def _on_slider_change(self, val):
        self._lbl_limit_val.configure(text=f"{int(val)} data")

    def _refresh_counter(self):
        jumlah = get_jumlah_data()
        self._lbl_counter.configure(text=f"Data tersimpan di DB: {jumlah} wisata")


# ============================================================================
# Jalankan standalone (untuk testing tanpa aplikasi utama)
# ============================================================================
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("JabarExplore — Scraper")
    root.geometry("780x680")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    frame = ScrapeFrame(root)
    frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    root.mainloop()
