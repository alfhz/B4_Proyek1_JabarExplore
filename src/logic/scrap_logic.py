'''bertugas mengambil HTML dari URL, mengekstrak data wisata dari setiap card yang ditemukan, lalu memvalidasi dan menyimpannya ke database —
sambil memastikan tidak ada data duplikat dan bisa berpindah halaman otomatis hingga limit tercapai.'''
import sys
import os
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Pastikan root project masuk ke sys.path agar import antar-modul bekerja
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.utils.validators import cek_duplikat, validasi_item, buat_id
from src.utils.file_handler import buka_json, tambah_data

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}


class ScrapLogic:
    """
    Engine scraping utama untuk Tim A.

    Alur kerja:
        1. Ambil HTML dari URL
        2. Bersihkan data di memori
        3. Cek duplikat via validators.py
        4. Simpan data bersih via file_handler.py

    Mendukung pagination dan limit jumlah data.
    UI tetap responsif karena class ini dijalankan oleh threads.py.
    """

    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self._stop_flag = False

    def log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def progress(self, current: int, total: int):
        if self.progress_callback:
            self.progress_callback(current, total)

    def stop(self):
        self._stop_flag = True

    def scrape(self, url: str, limit: int = 50) -> list:
        """
        Fungsi utama scraping. Mengembalikan list dict item yang BARU berhasil disimpan.
        """
        self._stop_flag = False
        hasil_baru     = []
        data_existing  = buka_json()   # cache agar cek duplikat cepat
        halaman        = 1
        current_url    = url

        self.log(f"[START] Mulai scraping: {url}")
        self.log(f"[INFO]  Target {limit} data baru | Data di DB: {len(data_existing)}")

        while current_url and not self._stop_flag:
            # ---- 1. Ambil HTML ----
            self.log(f"[PAGE {halaman}] Mengambil HTML...")
            soup = self._fetch_html(current_url)

            if soup is None:
                self.log("[ERROR] Gagal mengambil halaman, scraping dihentikan.")
                break

            # ---- 2. Temukan card/item di halaman ----
            cards = self._cari_cards(soup)
            if not cards:
                self.log("[WARN] Tidak ada card/item ditemukan di halaman ini.")
                break

            self.log(f"[PAGE {halaman}] {len(cards)} card ditemukan. Memproses...")

            # ---- 3. Proses tiap card ----
            for card in cards:
                if self._stop_flag or len(hasil_baru) >= limit:
                    break

                item = self._ekstrak_item(card, url)
                if not item:
                    continue

                # Bersihkan whitespace berlebih di memori
                item = self._bersihkan_item(item)

                # ==========================================
                # FILTER LOKASI KHUSUS JAWA BARAT
                # ==========================================
                lokasi_teks = item.get("lokasi", "").lower()
                deskripsi_teks = item.get("deskripsi", "").lower()
                teks_gabungan = f"{lokasi_teks} {deskripsi_teks}"
                
                # 1. DAFTAR HITAM (Tolak jika ada kata ini)
                provinsi_ditolak = [
                    "jawa timur", "jatim", 
                    "jawa tengah", "jateng", 
                    "bali", "banten", "jakarta", "dki", "yogyakarta", "diy"
                ]
                
                if any(ditolak in teks_gabungan for ditolak in provinsi_ditolak):
                    self.log(f"[SKIP] '{item.get('judul')}' — Terdeteksi provinsi lain.")
                    continue

                # 2. DAFTAR PUTIH (Wajib ada salah satu kata ini)
                indikator_jabar = [
                    "jawa barat", "jabar", "bandung", "bogor", "depok", "bekasi", 
                    "cianjur", "sukabumi", "garut", "tasikmalaya", "ciamis", 
                    "pangandaran", "kuningan", "cirebon", "majalengka", "sumedang", 
                    "indramayu", "subang", "purwakarta", "karawang", "cimahi", "banjar"
                ]
                
                if not any(jabar in teks_gabungan for jabar in indikator_jabar):
                    self.log(f"[SKIP] '{item.get('judul')}' — Bukan/Tidak ada indikator Jawa Barat.")
                    continue
                # ==========================================

                # Validasi field wajib
                valid, alasan = validasi_item(item)
                if not valid:
                    self.log(f"[SKIP] '{item.get('judul', '?')}' — {alasan}")
                    continue

                # Cek duplikat (DB + hasil sesi ini)
                if cek_duplikat(item, data_existing + hasil_baru):
                    self.log(f"[DUPLIKAT] '{item['judul']}' sudah ada.")
                    continue

                # Simpan ke file via file_handler
                if tambah_data(item):
                    hasil_baru.append(item)
                    self.log(f"[SAVED {len(hasil_baru)}/{limit}] {item['judul']}")
                    self.progress(len(hasil_baru), limit)

            # ---- 4. Limit tercapai? ----
            if len(hasil_baru) >= limit or self._stop_flag:
                break

            # ---- 5. Cari tombol Next (pagination) ----
            next_url = self._cari_next_url(soup, current_url)
            if next_url:
                halaman += 1
                delay = round(random.uniform(0.5, 1.0), 2)
                self.log(f"[NEXT] Halaman {halaman} dalam {delay}s...")
                time.sleep(delay)
                current_url = next_url
            else:
                self.log("[INFO] Tidak ada halaman berikutnya.")
                break

        status = "dihentikan manual" if self._stop_flag else "selesai"
        self.log(f"\n[DONE] Scraping {status}. Total disimpan: {len(hasil_baru)} data baru.")
        return hasil_baru

    # ------------------------------------------------------------------
    # Helper Private
    # ------------------------------------------------------------------

    def _fetch_html(self, url: str):
        """Mengambil HTML dari URL. Return BeautifulSoup atau None jika gagal."""
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, 'lxml')
        except requests.exceptions.RequestException as e:
            self.log(f"[ERROR] {e}")
            return None

    def _cari_cards(self, soup: BeautifulSoup) -> list:
        """
        Mencari elemen card/item di halaman.
        Mencoba beberapa pola CSS umum yang dipakai website wisata Indonesia.
        """
        kata_kunci_card = ['card', 'item', 'post', 'wisata', 'destination', 'place', 'produk', 'entry']

        cards = soup.find_all(
            class_=lambda c: c and any(k in ' '.join(c).lower() for k in kata_kunci_card)
        )
        if cards:
            return cards

        # Fallback ke tag semantik
        cards = soup.find_all('article')
        if cards:
            return cards

        # Fallback terakhir: li yang punya class
        return soup.find_all('li', class_=True)

    def _ekstrak_item(self, card, base_url: str) -> dict:
        """
        Mengekstrak data satu item wisata dari elemen card HTML.
        Mencoba berbagai selector agar fleksibel di banyak website.
        Return dict item atau None jika gagal total.
        """
        try:
            # Judul
            judul_el = (
                card.find(['h1', 'h2', 'h3', 'h4'],
                          class_=lambda c: c and any(x in ' '.join(c).lower() for x in ['title', 'judul', 'name', 'heading']))
                or card.find(['h1', 'h2', 'h3', 'h4'])
                or card.find(class_=lambda c: c and 'title' in ' '.join(c).lower())
            )
            judul = judul_el.get_text(strip=True) if judul_el else ""

            # Deskripsi
            desc_el = (
                card.find('p', class_=lambda c: c and any(x in ' '.join(c).lower() for x in ['desc', 'excerpt', 'content', 'deskripsi']))
                or card.find('p')
            )
            deskripsi = desc_el.get_text(strip=True) if desc_el else ""

            # Lokasi
            lokasi_el = card.find(
                class_=lambda c: c and any(x in ' '.join(c).lower() for x in ['lokasi', 'location', 'address', 'alamat'])
            )
            lokasi = lokasi_el.get_text(strip=True) if lokasi_el else "Jawa Barat"

            # URL sumber
            link_el    = card.find('a', href=True)
            url_sumber = ""
            if link_el:
                href = link_el['href'].strip()
                if href.startswith('http'):
                    url_sumber = href
                elif href.startswith('/'):
                    # Ambil base domain saja
                    from urllib.parse import urlparse
                    parsed    = urlparse(base_url)
                    url_sumber = f"{parsed.scheme}://{parsed.netloc}{href}"
                else:
                    url_sumber = base_url.rstrip('/') + '/' + href

            # Gambar
            img_el = card.find('img', src=True)
            gambar = img_el['src'] if img_el else ""

            return {
                "id"            : buat_id(url_sumber or judul),
                "judul"         : judul,
                "lokasi"        : lokasi,
                "deskripsi"     : deskripsi,
                "gambar"        : gambar,
                "url_sumber"    : url_sumber,
                "tanggal_scrape": datetime.now().isoformat(),
            }

        except Exception as e:
            self.log(f"[WARN] Gagal ekstrak item: {e}")
            return None

    def _bersihkan_item(self, item: dict) -> dict:
        """Membersihkan whitespace ganda dan karakter tidak perlu dari semua field string."""
        for key, val in item.items():
            if isinstance(val, str):
                item[key] = ' '.join(val.split())
        return item

    def _cari_next_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """
        Mencari URL halaman berikutnya (pagination).
        Return URL string atau None jika tidak ada.
        """
        kata_next = ['next', 'selanjutnya', 'berikutnya', '›', '»', '>']

        # Cari via rel="next"
        tag = soup.find('a', rel='next')
        if tag and tag.get('href'):
            return self._abs_url(tag['href'], base_url)

        # Cari via teks anchor
        for anchor in soup.find_all('a', href=True):
            teks = anchor.get_text(strip=True).lower()
            if any(k in teks for k in kata_next):
                return self._abs_url(anchor['href'], base_url)

        # Cari via class yang mengandung 'next'
        tag = soup.find('a', class_=lambda c: c and 'next' in ' '.join(c).lower())
        if tag and tag.get('href'):
            return self._abs_url(tag['href'], base_url)

        return None

    def _abs_url(self, href: str, base_url: str) -> str:
        """Mengkonversi href relatif menjadi URL absolut."""
        href = href.strip()
        if href.startswith('http'):
            return href
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        if href.startswith('/'):
            return f"{parsed.scheme}://{parsed.netloc}{href}"
        return base_url.rstrip('/') + '/' + href