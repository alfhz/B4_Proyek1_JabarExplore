# FILE BARU
import os
import time
import requests
import threading
import pandas as pd
from typing import Dict, Any, Optional, Callable
from dotenv import load_dotenv

# Memuat variabel environment dati file .env
load_dotenv()

class ApifyBase:
    """
    Kelas dasar untuk mengatur koneksi dengan Apify API.
    Refactored: Modular, Type-Hinted, dan Thread.
    """

    def __init__(self):
        self.token = os.environ.get("APIFY_TOKEN")
        if not self.token:
            raise ValueError("APIFY_TOKEN tidak ditemukan pada environment (.env)")
        
        self.base_url = "https://api.apify.com/v2"
        self.map_actor_id = "compass~google-maps-extractor"


    def _start_task (self, payload: Dict[str, Any]) -> str:
        """ Memulai task dan mengembalikan ID proses (run_id)"""
        url = f"{self.base_url}/acts/{self.map_actor_id}/runs"

        # Memisahkan token ke params agar URL lebih bersih
        response = requests.post(url, params={"token": self.token}, json=payload)
        response.raise_for_status()
        return response.json().get('data', {}).get('id')

    def _check_status (self, run_id: str) -> str:
        """ Mengecek status dari task yang sedang berjalan."""
        url = f"{self.base_url}/actor-runs/{run_id}"
        response = requests.get(url, params={"token": self.token})
        response.raise_for_status()
        return response.json().get('data', {}).get('status')
    
    def _get_dataset(self, run_id: str) -> Optional[pd.DataFrame]:
        """ Mengambil hasil dataset dari task yang sudah SUCCEEDED."""
        #1. Ambil ID dataset
        url = f"{self.base_url}/actor-runs/{run_id}"
        response = requests.get(url, params={"token": self.token})
        dataset_id = response.json().get('data', {}).get('defaultDatasetId')

        #2. Download isinya
        dataset_url = f"{self.base_url}/datasets/{dataset_id}/items"
        data_response = requests.get(dataset_url, params={"token": self.token})
        data_response.raise_for_status()

        return pd.DataFrame(data_response.json())
    
    def run_actor_sync (self, payload: Dict[str, Any], info_text: str = " ") -> Optional[pd.DataFrame]:
        """
        Versi Synchronus: Berjalan di thread utama (Membnlokir program sampai selesai)
        Gunakan hal ini jika menjalankan script secara terpisah via terminal
        """

        try:
            run_id = self._start_task(payload)
            print(f"[2] Cloud diterima (Task ID: {run_id}). System mulai bekerja...")

            while True:
                time.sleep(10)
                status = self._check_status(run_id)
                print(f"   - Status API saat ini: {status}")

                if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                    break

            if status != "SUCCEEDED":
                print(f"[X] Gagal menyelesaikan eksekusi Cloud. Status akhir: {status}")
                return None
        
            print("[3] Proses selesai! Mengunduh Dataset JSON...")
            return self._get_dataset(run_id)
    
        except requests.exceptions.RequestException as e:
            print(f"[X] Kesalahan Jaringan / API Apify: {e}")
            return None
    
    def run_actor_background(self, payload: Dict[str, Any], callback: Callable, info_text: str = ""):
        """
        Versi Asynchronous: Berjalan di latar belakang menggunakan Thread.
        Sangat aman untuk UI. UI tidak akan freeze, dan hasil dikirim via callback.
        """

        def task_thread():
            # proses utama berjalan di background
            has_df = self.run_actor_sync(payload, info_text)

            # setelah selesai, panggil fungsi callback untuk mengatur hasil ke UI
            if callback:
                callback(has_df)

        # Jalankan sebagaidaemon agar thread otomatis mati jika aplikasi ditutup
        thread = threading.Thread(target=task_thread, daemon=True)
        thread.start()
