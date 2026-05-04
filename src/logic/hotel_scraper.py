# FILE BARU
import os
import pandas as pd
from tabulate import tabulate
from apify_base import ApifyBase

class HotelScraper(ApifyBase):
    """
    Class ini akan Mewarisi fungsionalitas dari ApifyBase.
    Tugasnya: Membaca file CSV dari Hasil Tahap 1, lalu mencari Hotel/Penginapan untuk tiap tempat.
    """
    def scrape_hotel_dari_csv(self, csv_wisata_path, max_hotels=3):
        print("=== TAHAP 2: MENCARI HOTEL BERDASARKAN FILE WISATA ===")
        
        if not os.path.exists(csv_wisata_path):
            print(f"[X] Gagal! File {csv_wisata_path} tidak ditemukan.")
            print("Harap jalankan Tahap 1 (wisata_scraper.py) terlebih dahulu.")
            return
            
        wisata_df = pd.read_csv(csv_wisata_path)
        search_queries = []
        
        # Mengekstrak judul dari baris Excel/CSV menjadi array antrean (Keyword pencarian hotel)
        for _, row in wisata_df.iterrows():
            title = str(row.get('title', ''))
            if title and title.lower() != "nan" and title != "Data Kosong / Tidak Spesifik":
                search_queries.append(f"Penginapan hotel info di dekat {title}")
                
        if not search_queries:
            print("Tidak ada satupun nama destinasi wisata valid di file Anda untuk dicari hotelnya.")
            return
            
        # Payload khusus untuk mengekstrak Hotel menggunakan Array Keyword berjumlah banyak
        payload = {
            "searchStringsArray": search_queries, 
            "language": "id",
            "countryCode": "id",
            "maxCrawledPlacesPerSearch": max_hotels, 
            # Fitur Harga / Info Hotel akan tercapture karena kata kunci mengarah pada "Penginapan"
        }
        
        # Kirim pekerjaan ini ke Base Class
        df = self.run_actor(payload, f"(Mencari maks {max_hotels} hotel per tiap wisata)")
        
        if df is not None and not df.empty:
            # Seleksi hanya kolom-kolom yang relevan dengan Hotel (Biasanya punya data 'hotelAccommodation')
            hotel_cols = ['title', 'categoryName', 'address', 'totalScore', 'reviewsCount', 'hotelAccommodation', 'additionalInfo', 'website', 'phone']
            avail_cols = [c for c in hotel_cols if c in df.columns]
            df = df[avail_cols]
            
            # Merapikan data String dan membalik format Array (JSON)
            for col in ['hotelAccommodation', 'additionalInfo']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    
            df = df.fillna("Data Tidak Disediakan Oleh Google / Pemilik Hotel")
            
            # Tempatkan Tahap 2 ini di Folder yang sama dengan Tahap 1 agar Rapi
            save_path = os.path.join(os.path.dirname(csv_wisata_path), "tahap2_hotel.csv")
            df.to_csv(save_path, index=False, escapechar='\\')
            
            # --- MENAMPILKAN TABEL PENGINAPAN DI TERMINAL ---
            print("\n" + "="*90)
            print("                 HASIL DATA HOTEL & PENGINAPAN TERDEKAT (PREVIEW)")
            print("="*90)
            # Karena info Hotel panjang, kita potong sekilas untuk preview terminal
            df_preview = df[['title', 'categoryName', 'totalScore', 'reviewsCount']].head(10)
            print(tabulate(df_preview, headers='keys', tablefmt='psql', showindex=False))
            print("="*90)
            
            print(f"\n[*] DATA PENGINAPAN Berhasil disimpan bentuk utuhnya di CSV: {save_path}")

if __name__ == "__main__":
    try:
        # Tentukan posisi file sumber secara dinamis (Data CSV Wisatanya)
        # Sistem akan mencari 2 Step ke atas/root (../..) kemudian masuk ke folder /data
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        sumber_file_wisata = os.path.join(project_root, 'data', 'tahap1_wisata.csv')
        
        # Eksekusi Scraper
        scraper = HotelScraper()
        scraper.scrape_hotel_dari_csv(sumber_file_wisata, max_hotels=2)
        
    except Exception as e:
        print(f"Error Eksekusi: {e}")
