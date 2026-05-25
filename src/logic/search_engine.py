import json
import os

# --------------- SEARCH ENGINE ---------------
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

