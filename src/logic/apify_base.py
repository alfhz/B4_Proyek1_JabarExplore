# FILE BARU
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# Memuat variabel environment dari file .env
load_dotenv()

class ApifyBase:
    """Kelas dasar (Base Class) yang mengatur koneksi murni ke API Apify.
    Kelas ini tidak memedulikan data apa yang di-scrape, hanya fokus mengantar pesan ke Cloud Apify."""
    
    def __init__(self):
        self.token = os.environ.get("APIFY_TOKEN")
        if not self.token:
            raise ValueError("APIFY_TOKEN tidak ditemukan pada environment (.env).")
        
        self.base_url = "https://api.apify.com/v2"
        self.maps_actor_id = "compass~google-maps-extractor"

    def run_actor(self, payload, info_text=""):
        """Menjadi kurir yang menjalankan Apify dan mengembalikan Pandas DataFrame"""
        run_url = f"{self.base_url}/acts/{self.maps_actor_id}/runs?token={self.token}"
        
        print(f"\n[1] Mengirim tugas ke Cloud Apify... {info_text}")
        response = requests.post(run_url, json=payload)
        response.raise_for_status()
        
        run_info = response.json().get('data', {})
        run_id = run_info.get('id')
        dataset_id = run_info.get('defaultDatasetId')
        
        print(f"[2] Cloud diterima (Task ID: {run_id}). Robot mulai bekerja...")
        
        status_url = f"{self.base_url}/actor-runs/{run_id}?token={self.token}"
        while True:
            time.sleep(10)
            status = requests.get(status_url).json().get('data', {}).get('status')
            
            print(f"    - Status Apify saat ini: {status}")
            if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
                
        if status != "SUCCEEDED":
            print(f"[X] Gagal menyelesaikan eksekusi Cloud. Status: {status}")
            return None
            
        print("[3] Proses Selesai! Mengunduh Dataset JSON...")
        dataset_url = f"{self.base_url}/datasets/{dataset_id}/items?token={self.token}"
        
        # Kembalikan hasilnya dalam bentuk struktur mudah olah (Bentuk DataFrame)
        return pd.DataFrame(requests.get(dataset_url).json())
