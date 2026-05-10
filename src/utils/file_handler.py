# src/utils/file_handler.py
import json
import shutil
import os
import uuid
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_json_cache = None
_json_cache_time = 0
_CACHE_TTL = 60  # detik

def _path_json():
    return os.path.join(PROJECT_ROOT, "data", "data_wisata.json")

def buka_json(force_reload=False):
    global _json_cache, _json_cache_time
    if not force_reload and _json_cache is not None and (time.time() - _json_cache_time) < _CACHE_TTL:
        return _json_cache
    path = _path_json()
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _json_cache = data
    _json_cache_time = time.time()
    return data

def simpan_json(data):
    global _json_cache, _json_cache_time
    path = _path_json()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    # Update cache setelah simpan
    _json_cache = data
    _json_cache_time = time.time()

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

def export_ke_csv(data_list, path_tujuan):
    import csv
    with open(path_tujuan, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nama Wisata', 'Kategori', 'Kota/Kabupaten', 'HTM', 'Rating', 'Kondisi Jalan'])
        for item in data_list:
            idnt = item.get('identitas', {})
            oper = item.get('operasional', {})
            info = item.get('informasi_tambahan', {})
            
            nama = idnt.get('nama', '-')
            kategori = idnt.get('tipe', '-')
            kota = idnt.get('alamat', '-').split(',')[-1].strip()
            htm = oper.get('htm', '0')
            rating = idnt.get('rating', '0.0')
            kondisi = info.get('kondisi_jalan', '-')
            
            writer.writerow([nama, kategori, kota, htm, rating, kondisi])
    return True

def _path_log():
    return os.path.join(PROJECT_ROOT, "data", "log_aktivitas.json")

def catat_log(aksi, nama_wisata):
    import datetime
    path = _path_log()
    log_data = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except:
            pass
            
    waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data.append({
        "waktu": waktu,
        "aksi": aksi,
        "nama_wisata": nama_wisata
    })
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4)

def export_log_ke_csv(path_tujuan):
    import csv
    path = _path_log()
    if not os.path.exists(path):
        return False
        
    with open(path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
        
    with open(path_tujuan, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Waktu', 'Aksi', 'Nama Wisata'])
        for item in log_data:
            writer.writerow([item.get('waktu'), item.get('aksi'), item.get('nama_wisata')])
            
    return True