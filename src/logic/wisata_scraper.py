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
        
        if isinstance(keyword, list):
            search_strings = keyword
        else:
            search_strings = [keyword]
            
        payload = {
            "searchStringsArray": search_strings,
            "language": "id",
            "countryCode": "id",
            "maxCrawledPlacesPerSearch": max_places,
            "zoom": 10,
            
            "includeReviews": True,
            "reviewsMaxCount": 30,
            "reviewsSort": "newest",
            "includeOpeningHours": True,    
            "includeImages": True,
            "maxImageCount": 5,
            "includeWebResults": True       
        }
        
        df = self.run_actor_sync(payload, f"(Target pencarian {max_places} lokasi)")
        
        if df is not None and not df.empty:
            cols = ['title', 'address', 'totalScore', 'reviewsCount', 'additionalInfo', 'reviews', 'imageUrls']
            avail_cols = [c for c in cols if c in df.columns]

            df_asli = df[avail_cols].copy()
            df = df_asli.fillna("Data Kosong / Tidak Spesifik")
            
            if 'address' in df.columns:
                df = df[df['address'].str.contains('Jawa Barat', case=False, na=False)]
                print(f"[*] Tersisa {len(df)} lokasi setelah di-filter khusus Jawa Barat.")
            
            df = df.head(50)
            
            if df.empty:
                print("Tidak ada lokasi Jawa Barat yang ditemukan.")
                return None
            
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            data_folder = os.path.join(project_root, 'data')
            uploads_folder = os.path.join(project_root, 'assets', 'uploads')
            
            if not os.path.exists(data_folder):
                os.makedirs(data_folder, exist_ok=True)
            if not os.path.exists(uploads_folder):
                os.makedirs(uploads_folder, exist_ok=True)
                
            import json
            import uuid
            import requests

            print("\n[*] Mulai mengunduh foto untuk masing-masing destinasi...")
            foto_list = []
            galeri_list = []

            for _, row in df.iterrows():
                image_urls = row.get("imageUrls", [])
                utama = "default.png"
                galeri = []

                if isinstance(image_urls, list) and len(image_urls) > 0:
                    for idx, image_url in enumerate(image_urls[:5]):
                        try:
                            response = requests.get(image_url, timeout=10)
                            if response.status_code == 200:
                                foto_filename = f"foto_{uuid.uuid4().hex[:8]}.jpg"
                                img_path = os.path.join(uploads_folder, foto_filename)
                                
                                with open(img_path, "wb") as f:
                                    f.write(response.content)
                                
                                if idx == 0:
                                    utama = foto_filename
                                else:
                                    galeri.append(foto_filename)
                        except Exception as e:
                            print(f"    [-] Gagal mengunduh foto ke-{idx+1} untuk {row.get('title')}: {e}")

                foto_list.append(utama)
                galeri_list.append(json.dumps(galeri))

            df['foto'] = foto_list
            df['galeri'] = galeri_list
            print(f"[*] Berhasil memproses pengunduhan foto.")

            export_path = os.path.join(data_folder, "tahap1_wisata.csv")
            df_csv = df.drop(columns=['reviews', 'imageUrls'], errors='ignore')
            df_csv.to_csv(export_path, index=False, escapechar='\\')
            
            if 'reviews' in df_asli.columns:
                reviews_data = []
                for _, row in df_asli.iterrows():
                    title = row.get('title', 'Unknown')
                    revs = row.get('reviews')
                    if isinstance(revs, list) and len(revs) > 0:
                        reviews_data.append({
                            "wisata": title,
                            "reviews": revs
                        })
                
                if reviews_data:
                    reviews_path = os.path.join(data_folder, "data_reviews.json")
                    with open(reviews_path, 'w', encoding='utf-8') as f:
                        json.dump(reviews_data, f, indent=4, ensure_ascii=False)
                    print(f"[*] MASTER DATA REVIEWS Berhasil diselamatkan dlm JSON: {reviews_path}")

            print("\n" + "="*80)
            print("                HASIL DATA WISATA (PREVIEW)")
            print("="*80)
            
            df_preview = df[['title', 'totalScore', 'reviewsCount']].head(10).copy()
            if 'address' in df.columns:
                df_preview['address_short'] = df['address'].str.slice(0, 30) + '...'
                
            print(tabulate(df_preview, headers='keys', tablefmt='psql', showindex=False))
            print("="*80)
            print(f"[*] MASTER DATA WISATA Berhasil diselamatkan dlm CSV: {export_path}")
            
            print("\n[*] Menjalankan Sinkronisasi agar muncul di GUI Kelola Data...")
            sinkron_csv_ke_json(export_path)
            
            return export_path
            
        return None

if __name__ == "__main__":
    try:
        scraper = WisataScraper()
        
        from src.utils.file_handler import buka_json
        data_master = buka_json()
        
        nama_wisata_list = []
        for item in data_master:
            nama = item.get('identitas', {}).get('nama')
            if nama:
                nama_wisata_list.append(f"{nama} Jawa Barat")
                
        nama_wisata_list = nama_wisata_list[:50]
        
        if not nama_wisata_list:
            print("Belum ada data di data_wisata.json!")
        else:
            print(f"[*] Memulai penarikan ulasan KHUSUS untuk {len(nama_wisata_list)} destinasi Anda...")
            scraper.scrape_wisata(nama_wisata_list, max_places=1)
    except Exception as e:
        print(f"Error Eksekusi: {e}")