import json
import shutil
import os

# Get the base directory of the project (3 levels up from src/utils/file_handler.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def buka_json():
    """Membuka database utama"""
    path = os.path.join(BASE_DIR, "data", "data_wisata.json")
    if not os.path.exists(path): 
        return []
    try:
        with open(path, 'r') as f:
            content = f.read()
            if not content.strip():
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def simpan_json(data):
    """Menyimpan data terbaru ke database"""
    path = os.path.join(BASE_DIR, "data", "data_wisata.json")
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def simpan_gambar_ke_lokal(source_path):
    """Menyalin gambar dari komputer ke folder assets/uploads"""
    if not source_path or not os.path.exists(source_path):
        return "default.png"
    
    target_dir = os.path.join(BASE_DIR, "assets", "uploads")
    os.makedirs(target_dir, exist_ok=True)
    
    filename = os.path.basename(source_path)
    target_path = os.path.join(target_dir, filename)
    
    shutil.copy(source_path, target_path)
    return filename