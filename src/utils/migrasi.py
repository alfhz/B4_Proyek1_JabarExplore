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
            
        if judul.lower() in judul_sudah_ada:
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

        data_baru = {
            "id": f"apify-{str(uuid.uuid4())[:6]}",
            "identitas": {
                "nama": judul,
                "foto": "default.png",
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

    simpan_json(data_master)
    print(f"[MIGRASI] Berhasil mensinkronkan {ditambahkan} data baru dari CSV ke JSON!")

if __name__ == "__main__":
    sinkron_csv_ke_json()
