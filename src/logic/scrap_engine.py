# FILE BARU (Pondasi Scraper Biasa Tanpa Apify)
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

class ScrapEngine:
    def __init__(self, url):
        self.url = url
        self.html_content = None
        self.soup = None
        self.data_list = []
        self.df = None

    def fetch_data(self):
        """Mengambil data (HTML) dari URL yang ditentukan."""
        try:
            # Menambahkan header 'User-Agent' untuk mensimulasikan browser 
            # agar tidak diblokir oleh anti-scraper ringan
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            print(f"Mengambil data dari: {self.url} ...")
            response = requests.get(self.url, headers=headers)
            response.raise_for_status() # Akan me-raise error jika status bukan 200 (OK)
            
            self.html_content = response.text
            self.soup = BeautifulSoup(self.html_content, 'lxml') # menggunakan lxml karena lebih cepat
            print("Data HTML berhasil diambil!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Gagal mengambil data dari URL. Error: {e}")
            return False

    def parse_table_data(self):
        """Contoh fungsi untuk mengambil data berbentuk Tabel (HTML <table>) pada website."""
        if not self.soup:
            print("Peringatan: HTML belum diambil. Panggil fetch_data() terlebih dahulu.")
            return None

        # pandas bisa langsung mengekstrak tabel HTML menjadi DataFrame
        try:
            # Mengambil semua tabel di page.
            # Jika ada spesifik atribut, bs4 bisa mencari tabel spesifik lalu dikonversi string.
            tables = pd.read_html(self.html_content)
            
            if not tables:
                print("Tidak ditemukan tabel pada halaman ini.")
                return None
                
            # Mengambil tabel paling pertama secara default (index 0)
            self.df = tables[0]
            print(f"Berhasil mengekstrak tabel dengan dimensi: {self.df.shape}")
            return self.df
            
        except ValueError:
            print("Tidak ditemukan tag <table> HTML di dalam halaman web ini.")
            return None
        except Exception as e:
            print(f"Error saat mengekstrak tabel: {e}")
            return None

    def parse_custom_data(self, container_tag, container_class=None, title_tag='h2', desc_tag='p'):
        """Contoh fungsi untuk mengekstrak data dari struktur seperti artikel/produk."""
        if not self.soup:
            return None

        self.data_list = []
        
        # Cari semua elemen yang membungkus data utama (contoh: <div class="product">)
        if container_class:
            items = self.soup.find_all(container_tag, class_=container_class)
        else:
            items = self.soup.find_all(container_tag)
            
        for index, item in enumerate(items):
            title = item.find(title_tag)
            desc = item.find(desc_tag)
            
            # Buat dict / row data baru
            self.data_list.append({
                'id': index + 1,
                'judul': title.text.strip() if title else None,
                'deskripsi': desc.text.strip() if desc else None
            })
            
        # Konversi ke pandas dataframe
        self.df = pd.DataFrame(self.data_list)
        print(f"Berhasil mengambil spesifik data, total: {len(self.df)} baris.")
        return self.df

    def clean_data(self):
        """Membersihkan (Cleaning) data setelah berhasil di scrape"""
        if self.df is None or self.df.empty:
            print("Tidak ada data untuk dibersihkan.")
            return None

        print("Memulai proses pembersihan data...")
        
        # 1. Menghapus baris yang datanya kosong secara keseluruhan (NaN)
        self.df = self.df.dropna(how='all')
        
        # 2. Menghapus duplikat baris
        self.df = self.df.drop_duplicates()
        
        # 3. Mengisi nilai yang hilang (opsional, tergantung dari kebutuhan)
        self.df = self.df.fillna("Tidak Ada Data")
        
        # Membuang white space yang berlebih dari kolom bertipe string (Object)
        for col in self.df.select_dtypes(include=['object']).columns:
            self.df[col] = self.df[col].astype(str).str.strip()

        print("Pembersihan data selesai.")
        return self.df

    def get_data(self):
        """Mengembalikan data yang saat ini sudah diproses"""
        return self.df

    def export_csv(self, filename="scraped_data.csv"):
        """Export dataset ke dalam bentuk file CSV di folder data/"""
        if self.df is None or self.df.empty:
            print("Data kosong, tidak dapat diexport.")
            return

        # Pastikan direktori `data` sudah ada
        if not os.path.exists("data"):
            os.makedirs("data")
            
        filepath = os.path.join("data", filename)
        self.df.to_csv(filepath, index=False)
        print(f"Data berhasil diexport ke: {filepath}")

# Contoh Cara Penggunaan (Jika file dijalankan langsung):
if __name__ == "__main__":
    # URL target (contoh saja: website wikipedia bebas)
    target_url = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
    
    # Inisiasi engine
    scraper = ScrapEngine(target_url)
    
    # 1. Ambil data HTML dari web
    if scraper.fetch_data():
        
        # 2. Parsing / Ekstrak tabel (karena wiki memiliki banyak tabel)
        scraper.parse_table_data()
        
        # 3. Bersihkan (Clenaning) Data
        scraper.clean_data()
        
        # 4. Preview / Lihat hasil
        print(scraper.get_data().head())
        
        # 5. Export hasil akhir ke bentuk file CSV
        scraper.export_csv("film_terlaris.csv")
