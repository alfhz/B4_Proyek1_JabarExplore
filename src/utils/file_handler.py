import json
import shutil
import os

# membuka data_wisata.json
def buka_json():
    path = "data/data_wisata.json"
    if not os.path.exists(path): return []
    with open(path, 'r') as f:
        return json.load(f)

# menyimpan data baru ke data_wisata.json
def simpan_json(data):
    path = "data/data_wisata.json"
    os.makedirs("data", exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# membuka data_hotel.json
def buka_json_hotel():
    path = "data/data_hotel.json"
    if not os.path.exists(path): return []
    with open(path, 'r') as f:
        return json.load(f)

# menyimpan data baru ke data_hotel.json
def simpan_json_hotel(data):
    path = "data/data_hotel.json"
    os.makedirs("data", exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
        
# menyimpan foto wisata
def simpan_gambar_ke_lokal(path_asal):
    if not path_asal or not os.path.exists(path_asal):
        return "default.png" # Pake gambar default kalo kosong

    os.makedirs("assets/uploads", exist_ok=True)
    nama_file = os.path.basename(path_asal)
    path_tujuan = os.path.join("assets/uploads", nama_file)
    
    # Salin filenya
    shutil.copy(path_asal, path_tujuan)
    return nama_file

def tambah_data(item):
    try:
        data_baru = {
            "id": item.get("id"),
            "identitas": {
                "nama": item.get("judul", ""),
                "foto": item.get("gambar", "default.png"),
                "rating": 0.0,
                "alamat": item.get("lokasi", "Jawa Barat"),
                "maps": item.get("url_sumber", ""),
                "tipe": "Umum (Scraping)"
            },
            "operasional": {
                "htm": 0,
                "hari_buka": "Senin - Minggu",
                "jam_buka": "-"
            },
            "informasi_tambahan": {
                "fasilitas": item.get("deskripsi", ""),
                "kondisi_jalan": "",
                "jarak_dari_kab_kota": ""
            }
        }
        
        list_data = buka_json()
        list_data.append(data_baru)
        simpan_json(list_data)
        return True
    except Exception as e:
        print("Error tambah data scraping:", e)
        return False