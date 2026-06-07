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

<<<<<<< Updated upstream
from src.utils.validators import cek_duplikat, validasi_item, buat_id
=======
import uuid
def buat_id(): return f"wst-{uuid.uuid4().hex[:6]}"
def validasi_item(item):
    if not item: return False, "Item kosong"
    nama = item.get("identitas", {}).get("nama") or item.get("judul")
    if not nama: return False, "Nama tidak ada"
    return True, "Valid"
def cek_duplikat(item, list_data):
    nama_baru = (item.get("identitas", {}).get("nama") or item.get("judul") or "").lower()
    for d in list_data:
        nama_exist = (d.get("identitas", {}).get("nama") or d.get("judul") or "").lower()
        if nama_baru and nama_baru == nama_exist: return True
    return False
>>>>>>> Stashed changes
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

        # Intercept Apify URL
        if "google.com/maps" in url.lower() or "maps.google" in url.lower() or "apify" in url.lower():
            return self.scrape_apify(url, limit)
        hasil_baru     = []
        data_existing  = buka_json()   # cache agar cek duplikat cepat
        halaman        = 1
        current_url    = url

        self.log(f"[START] Mulai scraping: {url}")
        self.log(f"[INFO]  Target {limit} data baru | Data di DB: {len(data_existing)}")

        while current_url and not self._stop_flag:
            # ---- 1. Ambil HTML ----
            self.log(f"[PAGE {halaman}] Mengambil HTML...")
            soup = self.scrape_html_web(current_url)

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

                item = self.scrape_data_wisata(card, url)
                if not item:
                    continue

                # Bersihkan whitespace berlebih di memori
                item = self.cleaning_data(item)

                # ==========================================
                # 1. FILTER LOKASI KHUSUS JAWA BARAT
                # ==========================================
                lokasi_teks = item.get("lokasi", "").lower()
                deskripsi_teks = item.get("deskripsi", "").lower()
                teks_gabungan = f"{lokasi_teks} {deskripsi_teks}"
                
                # DAFTAR HITAM (Tolak jika ada provinsi lain)
                provinsi_ditolak = [
                    "jawa timur", "jatim", 
                    "jawa tengah", "jateng", 
                    "bali", "banten", "jakarta", "dki", "yogyakarta", "diy"
                ]
                if any(ditolak in teks_gabungan for ditolak in provinsi_ditolak):
                    self.log(f"[SKIP] '{item.get('judul')}' — Terdeteksi provinsi lain.")
                    continue

                # DAFTAR PUTIH (Wajib ada kata kunci Jabar)
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
                # 2. FILTER KHUSUS WISATA ALAM
                # ==========================================
                judul_teks = item.get("judul", "").lower()
                kata_kunci_alam = [
                    "gunung", "pantai", "curug", "air terjun", "danau", "situ", 
                    "kawah", "hutan", "bukit", "goa", "lembah", "kebun teh", 
                    "puncak", "sungai", "alam", "pulau", "teluk", "mata air", 
                    "pemandian", "cagar", "taman nasional"
                ]
                teks_konten = f"{judul_teks} {deskripsi_teks}"
                if not any(k in teks_konten for k in kata_kunci_alam):
                    self.log(f"[SKIP ALAM] '{item.get('judul')}' — Tidak terdeteksi wisata alam.")
                    continue

                # ==========================================
                # 3. VALIDASI & SIMPAN KE MEMORI SEMENTARA
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

                # Kumpulkan saja di memori (jangan langsung simpan ke file JSON)
                hasil_baru.append(item)
                self.log(f"[DITEMUKAN {len(hasil_baru)}/{limit}] {item['judul']}")
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

    def scrape_apify(self, url: str, limit: int) -> list:
        self.log(f"[START] Mulai APIFY Scraping: {url}")
        from src.logic.apify_base import ApifyBase
        import urllib.parse
        import json
        import uuid
        
        if "/search/" in url:
            keyword = urllib.parse.unquote(url.split("/search/")[1].split("/")[0]).replace('+', ' ')
            payload = {
                "searchStringsArray": [keyword],
                "language": "id", "countryCode": "id",
                "maxCrawledPlacesPerSearch": limit,
                "includeReviews": True, "reviewsMaxCount": 30, "reviewsSort": "newest",
                "includeOpeningHours": True, "includeImages": True, "maxImageCount": 5
            }
        else:
            payload = {
                "startUrls": [{"url": url}],
                "language": "id", "countryCode": "id",
                "maxCrawledPlacesPerSearch": limit,
                "includeReviews": True, "reviewsMaxCount": 30, "reviewsSort": "newest",
                "includeOpeningHours": True, "includeImages": True, "maxImageCount": 5
            }

        apify = ApifyBase()
        self.log(f"Menghubungi Cloud API Apify untuk target {limit} lokasi...")
        
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        
        df = None
        try:
            df = apify.run_actor_sync(payload, f"(Target {limit} lokasi)")
        except Exception as e:
            self.log(f"[ERROR] APIFY Gagal: {e}")
        finally:
            sys.stdout = old_stdout
            for line in new_stdout.getvalue().splitlines():
                if line.strip(): self.log(line.strip())

        if df is None or df.empty:
            self.log("[INFO] Tidak ada data yang dikembalikan oleh Apify.")
            return []

        # Filter Dummy
        blocked_words = ['dummy', 'test', 'review', 'contoh', 'palsu', 'uji coba']
        if 'title' in df.columns:
            pattern = '|'.join(blocked_words)
            df = df[~df['title'].str.contains(pattern, case=False, na=False)]

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        uploads_folder = os.path.join(project_root, 'assets', 'uploads')
        if not os.path.exists(uploads_folder):
            os.makedirs(uploads_folder, exist_ok=True)

        hasil = []
        total = len(df)
        self.log(f"Berhasil mengekstrak {total} baris data mentah dari cloud.")
        
        for idx, row in df.iterrows():
            if self._stop_flag: break
            self.progress(idx+1, total)
            
            judul = row.get("title", "Tanpa Judul")
            alamat = row.get("address", "Jawa Barat")
            
            if "jawa barat" not in alamat.lower() and "jabar" not in alamat.lower():
                self.log(f"[SKIP] '{judul}' bukan di Jawa Barat.")
                continue
                
            self.log(f"Memproses '{judul}'...")
            
            foto_filename = ""
            image_urls = row.get("imageUrls", [])
            if isinstance(image_urls, list) and len(image_urls) > 0:
                try:
                    response = requests.get(image_urls[0], timeout=10)
                    if response.status_code == 200:
                        foto_filename = f"foto_{uuid.uuid4().hex[:8]}.jpg"
                        img_path = os.path.join(uploads_folder, foto_filename)
                        with open(img_path, "wb") as f:
                            f.write(response.content)
                except Exception as e:
                    pass
            
            item = {
                "id": buat_id(),
                "identitas": {
                    "nama": judul,
                    "tipe": "Alam",
                    "alamat": alamat,
                    "maps": row.get("url", ""),
                    "rating": float(row.get("totalScore", 0)) if pd.notnull(row.get("totalScore")) else 0.0,
                    "foto": foto_filename,
                    "deskripsi": str(row.get("additionalInfo", {})) if isinstance(row.get("additionalInfo"), dict) else "",
                    "jumlah_ulasan": int(row.get("reviewsCount", 0)) if pd.notnull(row.get("reviewsCount")) else 0
                },
                "operasional": {
                    "htm": "Gratis",
                    "hari_buka": ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"],
                    "jam_operasional": {"buka": "08:00", "tutup": "17:00"}
                },
                "informasi_tambahan": {
                    "fasilitas": [],
                    "kondisi_jalan": "-",
                    "jarak_dari_kab_kota": "-"
                },
                "reviews": row.get("reviews", [])
            }
            hasil.append(item)
            
        self.log(f"[DONE] Apify Scraping selesai. Total data valid: {len(hasil)}")
        return hasil

    # ... Helper Private methods (_fetch_html, _cari_cards, _ekstrak_item, dsb tetap sama)
    # [dipotong untuk efisiensi ruang tampilan sesuai blok asli]
    
    # Meneruskan fungsi internal (agar utuh berdasarkan prompt)
    def scrape_html_web(self, url: str):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, 'lxml')
        except requests.exceptions.RequestException as e:
            self.log(f"[ERROR] {e}")
            return None

    def _cari_cards(self, soup: BeautifulSoup) -> list:
        kata_kunci_card = ['card', 'item', 'post', 'wisata', 'destination', 'place', 'produk', 'entry']
        kandidat = []
        kandidat.extend(soup.find_all(class_=lambda c: c and any(k in ' '.join(c).lower() for k in kata_kunci_card)))
        kandidat.extend(soup.find_all('article'))
        kandidat.extend(soup.find_all(['h2', 'h3']))
        kandidat.extend(soup.find_all('li'))
        unik = []
        for k in kandidat:
            if k not in unik:
                unik.append(k)
        return unik

    def scrape_data_wisata(self, card, base_url: str) -> dict:
        try:
            judul = ""
            deskripsi = ""
            if card.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                judul = card.get_text(strip=True)
            elif card.name == 'li':
                a_tag = card.find('a')
                if a_tag:
                    judul = a_tag.get_text(strip=True)
                else:
                    judul = card.get_text(strip=True).split('\n')[0]
            else:
                judul_el = (
                    card.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=lambda c: c and any(x in ' '.join(c).lower() for x in ['title', 'judul', 'name', 'heading']))
                    or card.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    or card.find(class_=lambda c: c and 'title' in ' '.join(c).lower())
                )
                judul = judul_el.get_text(strip=True) if judul_el else ""
            
            if len(judul) < 3 or len(judul) > 60: return None
            if judul.lower() in ['edit', 'talk', 'read', 'view source', 'view history', 'main page']: return None
            
            import re
            judul = re.sub(r'^\d+[\.\)\-]\s*', '', judul).strip()

            if card.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                desc_el = card.find_next_sibling('p')
                deskripsi = desc_el.get_text(strip=True) if desc_el else ""
            elif card.name == 'li':
                deskripsi = card.get_text(strip=True).replace(judul, '').strip()
            else:
                desc_el = (
                    card.find('p', class_=lambda c: c and any(x in ' '.join(c).lower() for x in ['desc', 'excerpt', 'content', 'deskripsi']))
                    or card.find('p')
                )
                deskripsi = desc_el.get_text(strip=True) if desc_el else ""

            lokasi = "Jawa Barat"
            if card.name not in ['h1', 'h2', 'h3', 'h4', 'h5']:
                lokasi_el = card.find(class_=lambda c: c and any(x in ' '.join(c).lower() for x in ['lokasi', 'location', 'address', 'alamat']))
                if lokasi_el: lokasi = lokasi_el.get_text(strip=True)
                    
            kota_jabar = ["bandung", "bogor", "depok", "bekasi", "cianjur", "sukabumi", "garut", "tasikmalaya", "ciamis", "pangandaran", "kuningan", "cirebon", "majalengka", "sumedang", "indramayu", "subang", "purwakarta", "karawang", "cimahi", "banjar", "lembang", "puncak"]
            teks_gabung = f"{judul} {deskripsi}".lower()
            for k in kota_jabar:
                if k in teks_gabung:
                    lokasi = f"{k.title()}, Jawa Barat"
                    break

            link_el = card.find('a', href=True)
            if card.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                link_el = card.find('a', href=True) or card.find_next_sibling('a', href=True)
                
            url_sumber = ""
            if link_el:
                href = link_el['href'].strip()
                if href.startswith('http'): url_sumber = href
                elif href.startswith('/') or href.startswith('#'):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    url_sumber = f"{parsed.scheme}://{parsed.netloc}{href}"
                else: url_sumber = base_url.rstrip('/') + '/' + href

            # ==========================================
            # EKSTRAKSI GAMBAR (Teknik Pemindaian Visual)
            # ==========================================
            img_el = card.find('img')
            
            if not img_el:
                # 1. Maju perlahan ke bawah mencari gambar terdekat (Memprioritaskan gambar SESUDAH judul)
                for el in card.next_elements:
                    if isinstance(el, str): continue
                    
                    if el.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and el != card:
                        break
                        
                    if el.name == 'img':
                        img_el = el
                        break

            if not img_el:
                # 2. Mundur perlahan ke atas mencari gambar terdekat (Fallback jika gambar SEBELUM judul)
                for el in card.previous_elements:
                    if isinstance(el, str): continue
                    
                    if el.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and el != card:
                        break
                        
                    if el.name == 'img':
                        img_el = el
                        break
            
            # Jika masih tidak ada, coba cari di figure
            if not img_el:
                fig = card.find_next_sibling('figure')
                if fig: img_el = fig.find('img')

            gambar = ""
            if img_el:
                # Prioritaskan srcset karena src seringkali sengaja dirusak (404) oleh website
                gambar_mentah = ""
                srcset = img_el.get('srcset') or img_el.get('data-srcset')
                if srcset:
                    # srcset format: "url1 800w, url2 400w"
                    # Ambil url pertama (biasanya resolusi tertinggi)
                    gambar_mentah = srcset.split(',')[0].strip().split(' ')[0]
                
                # Fallback ke atribut lain
                if not gambar_mentah:
                    gambar_mentah = (
                        img_el.get('data-src') or 
                        img_el.get('data-lazy-src') or 
                        img_el.get('data-original') or 
                        img_el.get('src') or 
                        img_el.get('data-url') or
                        ""
                    )
                
                # CLEANUP URL: NativeIndonesia sengaja mengubah /wp-content/uploads/ menjadi /foto/ yang menghasilkan 404
                if '/foto/' in gambar_mentah and 'nativeindonesia.com' in gambar_mentah:
                    gambar_mentah = gambar_mentah.replace('/foto/', '/wp-content/uploads/')

                if gambar_mentah:
                    gambar_mentah = gambar_mentah.strip()
                    if gambar_mentah.startswith('http'):
                        gambar = gambar_mentah
                    elif gambar_mentah.startswith('//'):
                        gambar = "https:" + gambar_mentah
                    elif gambar_mentah.startswith('/'):
                        from urllib.parse import urlparse
                        parsed = urlparse(base_url)
                        gambar = f"{parsed.scheme}://{parsed.netloc}{gambar_mentah}"
                    else:
                        gambar = base_url.rstrip('/') + '/' + gambar_mentah

            return {
                "id": buat_id(),
                "judul": judul,
                "lokasi": lokasi,
                "deskripsi": deskripsi,
                "gambar": gambar,
                "url_sumber": url_sumber,
                "tanggal_scrape": datetime.now().isoformat(),
            }
        except Exception as e:
            self.log(f"[WARN] Gagal ekstrak item: {e}")
            return None

    def cleaning_data(self, item: dict) -> dict:
        for key, val in item.items():
            if isinstance(val, str):
                item[key] = ' '.join(val.split())
        return item

    def _cari_next_url(self, soup: BeautifulSoup, base_url: str) -> str:
        kata_next = ['next', 'selanjutnya', 'berikutnya', '›', '»', '>']
        tag = soup.find('a', rel='next')
        if tag and tag.get('href'): return self._abs_url(tag['href'], base_url)

        for anchor in soup.find_all('a', href=True):
            teks = anchor.get_text(strip=True).lower()
            if any(k in teks for k in kata_next):
                return self._abs_url(anchor['href'], base_url)

        tag = soup.find('a', class_=lambda c: c and 'next' in ' '.join(c).lower())
        if tag and tag.get('href'): return self._abs_url(tag['href'], base_url)
        return None

    def _abs_url(self, href: str, base_url: str) -> str:
        href = href.strip()
        if href.startswith('http'): return href
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        if href.startswith('/'): return f"{parsed.scheme}://{parsed.netloc}{href}"
        return base_url.rstrip('/') + '/' + href