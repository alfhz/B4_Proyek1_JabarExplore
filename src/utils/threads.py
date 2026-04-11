import threading


class ScrapThread(threading.Thread):
    """
    Worker thread untuk menjalankan scraping di background.

    Tujuan: Memastikan UI (scrapper.py / customtkinter) TIDAK FREEZE
    saat proses scraping berjalan lama.

    Cara kerja:
        - Menerima instance ScrapLogic yang sudah dikonfigurasi.
        - Menjalankan scraper.scrape() di thread terpisah (daemon).
        - Memanggil on_done(hasil) atau on_error(pesan) saat selesai.
        - Bisa dihentikan kapan saja via method stop().

    Penggunaan (dari scrapper.py):
        thread = ScrapThread(
            scraper  = scraper_instance,
            url      = url,
            limit    = 50,
            on_done  = lambda hasil: print(f"Selesai: {len(hasil)} data"),
            on_error = lambda msg: print(f"Error: {msg}"),
        )
        thread.start()
        # ... nanti kalau mau berhenti:
        thread.stop()
    """

    def __init__(self, scraper, url: str, limit: int,
                 on_done=None, on_error=None):
        """
        Parameters
        ----------
        scraper  : ScrapLogic — instance engine scraping yang sudah dikonfigurasi.
        url      : str        — URL target scraping.
        limit    : int        — Jumlah maksimum data yang dikumpulkan.
        on_done  : callable(list) — Dipanggil dengan list hasil saat scraping selesai.
        on_error : callable(str)  — Dipanggil dengan pesan error jika ada exception.
        """
        super().__init__(daemon=True)   # daemon=True: thread otomatis mati jika app ditutup

        self._scraper    = scraper
        self._url        = url
        self._limit      = limit
        self._on_done    = on_done  or (lambda hasil: None)
        self._on_error   = on_error or (lambda msg: None)
        self._is_running = False

    # ------------------------------------------------------------------
    # Thread lifecycle
    # ------------------------------------------------------------------

    def run(self):
        """Entry point thread — dipanggil otomatis oleh thread.start()."""
        self._is_running = True
        try:
            hasil = self._scraper.scrape(self._url, self._limit)
            self._on_done(hasil)
        except Exception as e:
            self._on_error(str(e))
        finally:
            self._is_running = False

    def stop(self):
        """
        Menghentikan scraping secara graceful.
        Loop di ScrapLogic.scrape() akan berhenti di iterasi berikutnya.
        """
        self._scraper.stop()

    # ------------------------------------------------------------------
    # Property
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """True selama thread masih aktif mengerjakan scraping."""
        return self._is_running
