import json
import os
import shutil
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _path_json():
    return os.path.join(PROJECT_ROOT, "data", "data_wisata.json")

def buka_json():
    """Membuka database utama"""
    path = _path_json()
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def simpan_json(data):
    """Menyimpan data terbaru ke database"""
    path = _path_json()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def simpan_gambar_ke_lokal(path_gambar_sementara):
    """Menyimpan gambar dari path sementara ke folder assets/uploads"""
    if not path_gambar_sementara or not os.path.exists(path_gambar_sementara):
        return "default.png"
    
    upload_dir = os.path.join(PROJECT_ROOT, "assets", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    ekstensi = os.path.splitext(path_gambar_sementara)[1].lower()
    if ekstensi not in ['.jpg', '.jpeg', '.png', '.gif']:
        ekstensi = '.png'
    
    nama_file = f"wisata_{hash(path_gambar_sementara)}_{os.path.basename(path_gambar_sementara)}"
    nama_file = nama_file[:50] + ekstensi
    tujuan = os.path.join(upload_dir, nama_file)
    
    shutil.copy2(path_gambar_sementara, tujuan)
    return nama_file