import sys
import os
import pandas as pd
import uuid

# Pastikan working directory dan import bisa jalan
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.utils.file_handler import buka_json, simpan_json

def sinkron_csv_ke_json(csv_path="data/tahap1_wisata.csv"):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} belum ada. Lewati sinkronisasi.")
        return

    data_master = buka_json()
    
    # Ambil judul-judul yang sudah ada agar tidak duplikat
    judul_sudah_ada = {item['identitas']['nama'].lower() for item in data_master}
    import json
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print("Gagal membaca CSV:", e)
        return
        
    ditambahkan = 0
    
    for _, row in df.iterrows():
        judul = str(row.get('title', ''))
        if not judul or judul.lower() == 'nan':
            continue
            
        lokasi = str(row.get('address', 'Jawa Barat'))
        if lokasi.lower() == 'nan': lokasi = "Jawa Barat"
        
        rating = 0.0
        try:
            r = row.get('totalScore', 0)
            rating = float(r) if str(r).lower() != 'nan' else 0.0
        except:
            pass
            
        ulasan = 0
        try:
            u = row.get('reviewsCount', 0)
            ulasan = int(float(u)) if str(u).lower() != 'nan' else 0
        except:
            pass
            
        galeri = []
        try:
            g = row.get('galeri', '[]')
            if str(g).lower() != 'nan':
                galeri = json.loads(g)
        except:
            pass
            
        foto = str(row.get('foto', 'default.png'))

        if judul.lower() in judul_sudah_ada:
            for item in data_master:
                if item['identitas']['nama'].lower() == judul.lower():
                    item['identitas']['foto'] = foto
                    item['identitas']['galeri'] = galeri
            continue

        data_baru = {
            "id": f"apify-{str(uuid.uuid4())[:6]}",
            "identitas": {
                "nama": judul,
                "foto": foto,
                "galeri": galeri,
                "rating": rating,
                "alamat": lokasi,
                "maps": "",
                "tipe": "Destinasi Google Maps",
                "jumlah_ulasan": ulasan
            },
            "operasional": {
                "htm": "0",
                "hari_buka": "Senin - Minggu",
                "jam_buka": "08:00 - 17:00"
            },
            "informasi_tambahan": {
                "fasilitas": str(row.get('additionalInfo', '')),
                "kondisi_jalan": "-",
                "jarak_dari_kab_kota": "-"
            }
        }
        
        data_master.append(data_baru)
        judul_sudah_ada.add(judul.lower())
        ditambahkan += 1

    # Membuat file baru untuk penyimpanan seperti yang Anda minta (opsional, backup juga)
    simpan_json(data_master) # Tetap simpan ke data_wisata.json agar UI bisa membaca
    
    # Simpan ke file baru
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_folder = os.path.join(project_root, 'data')
    baru_path = os.path.join(data_folder, 'data_wisata_baru.json')
    with open(baru_path, 'w', encoding='utf-8') as f:
        json.dump(data_master, f, indent=4)
        
    print(f"[MIGRASI] Berhasil mensinkronkan/mengupdate {ditambahkan} data baru dari CSV ke JSON!")
    print(f"[MIGRASI] Data juga disimpan di file baru: {baru_path}")

if __name__ == "__main__":
    sinkron_csv_ke_json()