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