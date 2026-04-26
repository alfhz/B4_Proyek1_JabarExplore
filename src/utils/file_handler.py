import json
import shutil
import os

def buka_json():
    """Membuka database utama"""
    path = "data/data_wisata.json"
    if not os.path.exists(path): return []
    with open(path, 'r') as f:
        return json.load(f)

def simpan_json(data):
    """Menyimpan data terbaru ke database"""
    path = "data/data_wisata.json"
    os.makedirs("data", exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)