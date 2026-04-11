import json
import os
from datetime import datetime


# Path relatif dari root project — diselesaikan secara dinamis
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_DATA_PATH = os.path.join(_ROOT, 'data', 'data_wisata.json')


def buka_json() -> list:
    """Membuka dan mengembalikan seluruh isi database wisata."""
    if not os.path.exists(_DATA_PATH):
        return []
    try:
        with open(_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def simpan_json(data: list):
    """Menyimpan (overwrite) seluruh list data ke database."""
    os.makedirs(os.path.dirname(_DATA_PATH), exist_ok=True)
    with open(_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def tambah_data(item_baru: dict) -> bool:
    """
    Menambahkan satu item ke database.
    Otomatis mengisi 'tanggal_scrape' jika belum ada.
    Return True jika berhasil disimpan.
    """
    try:
        if "tanggal_scrape" not in item_baru:
            item_baru["tanggal_scrape"] = datetime.now().isoformat()

        data = buka_json()
        data.append(item_baru)
        simpan_json(data)
        return True
    except Exception:
        return False


def hapus_semua():
    """Menghapus seluruh data (reset database ke list kosong)."""
    simpan_json([])


def get_jumlah_data() -> int:
    """Mengembalikan jumlah total data yang tersimpan di database."""
    return len(buka_json())
