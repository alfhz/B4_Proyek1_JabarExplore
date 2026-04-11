<<<<<<< Updated upstream
=======
<<<<<<< Updated upstream
import uuid
import os
from src.utils.file_handler import buka_json, simpan_json, simpan_gambar_ke_lokal

# modul tambah data wisata
def tambah_data_wisata(input_user, path_foto_mentah):
    list_data = buka_json()
    
    # Logic Handling Gambar
    nama_foto = simpan_gambar_ke_lokal(path_foto_mentah) if path_foto_mentah else "default.png"
    
    # Logic Penyusunan Struktur Data
    data_baru = {
        "id": str(uuid.uuid4())[:8],
        "identitas": {
            "nama": input_user['nama'],
            "foto": nama_foto,
            "rating": float(input_user['rating'] or 0),
            "alamat": input_user['alamat'],
            "maps": input_user['maps'],
            "tipe": input_user['tipe']
        },
        "operasional": {
            "htm": input_user['htm'],
            "hari_buka": "Senin - Minggu",
            "jam_buka": input_user['jam_buka']
        },
        "informasi_tambahan": {
            "fasilitas": input_user['fasilitas'],
            "kondisi_jalan": input_user['kondisi_jalan'],
            "jarak_dari_kab_kota": input_user['jarak_dari_kab_kota']
        }
    }
    
    list_data.append(data_baru)
    simpan_json(list_data)

# modul update/edit wisata
def update_data_wisata(id_wisata, input_user, path_foto_mentah, foto_lama):
    list_data = buka_json()
    
    # Logic Handling Gambar 
    nama_foto = simpan_gambar_ke_lokal(path_foto_mentah) if path_foto_mentah else foto_lama

    for i, item in enumerate(list_data):
        if str(item.get('id')) == str(id_wisata):
            data_update = {
                "id": id_wisata,
                "identitas": {
                    "nama": input_user['nama'],
                    "foto": nama_foto,
                    "rating": float(input_user['rating'] or 0),
                    "alamat": input_user['alamat'],
                    "maps": input_user['maps'],
                    "tipe": input_user['tipe']
                },
                "operasional": {
                    "htm": input_user['htm'],
                    "hari_buka": item['operasional'].get('hari_buka', 'Senin - Minggu'),
                    "jam_buka": input_user['jam_buka']
                },
                "informasi_tambahan": {
                    "fasilitas": input_user['fasilitas'],
                    "kondisi_jalan": input_user['kondisi_jalan'],
                    "jarak_dari_kab_kota": input_user['jarak_dari_kab_kota']
                }
            }
            list_data[i] = data_update
            simpan_json(list_data)
            return True
    return False

# modul delete wisata
def hapus_data_wisata(id_wisata):
    list_data = buka_json()
    data_filter = [item for item in list_data if str(item.get('id')) != str(id_wisata)]
    simpan_json(data_filter)
=======
"""CRUD minimal — dipakai halaman daftar wisata (Tim B)."""

from src.utils.file_handler import buka_json, simpan_json


def hapus_data_wisata(id_wisata):
    data = buka_json()
    filtered = [x for x in data if str(x.get("id")) != str(id_wisata)]
    simpan_json(filtered)
>>>>>>> Stashed changes
>>>>>>> Stashed changes
