import json
import os

# mengembalikan objek data wisata siap proses
def load_data_wisata(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception:
        return []

# mengembalikan daftar_wisata yang dicari base on input user
def cari_wisata(nama_wisata, data_master):
    if not nama_wisata:
        return data_master
    
    keyword = nama_wisata.lower()
    
    # filter berdasarkan kecocokan nama_wisata
    hasil = [
        item for item in data_master 
        if keyword in item.get('identitas', {}).get('nama', '').lower()
    ]
    return hasil