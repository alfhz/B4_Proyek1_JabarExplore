# src/utils/file_handler.py
import json
import shutil
import os
import uuid

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _path_json():
    return os.path.join(PROJECT_ROOT, "data", "data_wisata.json")

def buka_json():
    path = _path_json()
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def simpan_json(data):
    path = _path_json()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def simpan_gambar_ke_lokal(path_asal):
    if not path_asal or not os.path.exists(path_asal):
        return "default.png"
    upload_dir = os.path.join(PROJECT_ROOT, "assets", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    ekstensi = os.path.splitext(path_asal)[1].lower()
    if ekstensi not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        ekstensi = '.png'
    nama_unik = f"{uuid.uuid4().hex}{ekstensi}"
    path_tujuan = os.path.join(upload_dir, nama_unik)
    shutil.copy2(path_asal, path_tujuan)
    return nama_unik