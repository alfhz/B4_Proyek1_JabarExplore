# FILE BARU
import os
import pandas as pd
from tabulate import tabulate
from apify_base import ApifyBase

import sys
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from src.utils.migrasi import sinkron_csv_ke_json

class WisataScraper(ApifyBase):
    """
    Class ini akan Mewarisi (Inherit) fungsionalitas dari ApifyBase,
    tapi tugasnya spesifik hanya untuk mencari Master Data DESTINASI WISATA.
    """
    def scrape_wisata(self, keyword, max_places=10):
        print(f"=== TAHAP 1: MENCARI DESTINASI WISATA ({keyword}) ===")
        
        # Payload khusus untuk mencari Wisata (Dengan fitur Add-on internal lengkap)
        payload = {
            "searchStringsArray": [keyword],
            "language": "id",
            "countryCode": "id",
            "maxCrawledPlacesPerSearch": max_places,
            "zoom": 10,
            
            # --- Semua Add-on Wisata ---
            "includeReviews": True,         
            "reviewsMaxCount": 5,           
            "includeOpeningHours": True,    
            "includeImages": True,          
            "imagesMaxCount": 3,
            "includeWebResults": True       
        }
        
        # Kirim pekerjaan ini ke Base Class
        df = self.run_actor(payload, f"(Target pencarian {max_places} lokasi)")
        
        if df is not None and not df.empty:
            # Merapikan hanya kolom wisata saja
            cols = ['title', 'address', 'totalScore', 'reviewsCount', 'additionalInfo']
            avail_cols = [c for c in cols if c in df.columns]
            df = df[avail_cols].fillna("Data Kosong / Tidak Spesifik")
            
            # Membangun Absolute Path agar data/ konsisten tersimpan di Root Project
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            data_folder = os.path.join(project_root, 'data')
            
            if not os.path.exists(data_folder):
                os.makedirs(data_folder, exist_ok=True)
                
            export_path = os.path.join(data_folder, "tahap1_wisata.csv")
            df.to_csv(export_path, index=False, escapechar='\\')
            
            # --- MENAMPILKAN TABEL SANGAT RAPI DI TERMINAL ---
            print("\n" + "="*80)
            print("                HASIL DATA WISATA (PREVIEW)")
            print("="*80)
            
            # Kita potong kolomnya agar layar terminal tidak kepenuhan/berantakan
            df_preview = df[['title', 'totalScore', 'reviewsCount']].head(10).copy()
            
            # Khusus alamat, kita batasi panjang spasinya max 30 karakter agar estetis
            if 'address' in df.columns:
                df_preview['address_short'] = df['address'].str.slice(0, 30) + '...'
                
            print(tabulate(df_preview, headers='keys', tablefmt='psql', showindex=False))
            print("="*80)
            print(f"[*] MASTER DATA WISATA Berhasil diselamatkan dlm CSV: {export_path}")
            
            # --- SINKRONISASI KE JSON AGAR MUNCUL DI GUI ---
            print("\n[*] Menjalankan Sinkronisasi agar muncul di GUI Kelola Data...")
            sinkron_csv_ke_json(export_path)
            
            return export_path
            
        return None

if __name__ == "__main__":
    try:
        scraper = WisataScraper()
        # Mengambil sampel 3 wisata pertama
        scraper.scrape_wisata("Destinasi wisata yang ada di Jawa Barat", max_places=50)
    except Exception as e:
        print(f"Error Eksekusi: {e}")
