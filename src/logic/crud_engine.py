# src/logic/crud_engine.py
import uuid
from src.utils.file_handler import buka_json, simpan_json, simpan_gambar_ke_lokal, catat_log
from datetime import datetime

# fungsi untuk menyusun data baru dari input user lalu simpan ke json
def tambah_data_wisata(input_user, list_nama_foto):
    list_data = buka_json()
    tanggal = datetime.now().strftime("%Y-%m-%d")
    id_acak = f"wst-{uuid.uuid4().hex[:6]}" 
    
    data_baru = {
        "id": id_acak,
        "identitas": {
            "nama": input_user['nama'],
            "deskripsi": input_user['deskripsi'],
            "foto": list_nama_foto if list_nama_foto else ["default.png"], 
            "rating": float(input_user.get('rating', 0)),
            "alamat": input_user['alamat'],
            "maps": input_user.get('maps', ''),
            "tipe": input_user['tipe']
        },
        "operasional": {
            "htm": input_user['htm'],
            "hari_buka": input_user['hari_buka'],
            "jam_operasional": {"buka": input_user['jam_mulai'], "tutup": input_user['jam_selesai']}
        },
        "informasi_tambahan": {
            "fasilitas": input_user.get('fasilitas', []),
            "kondisi_jalan": input_user['kondisi_jalan'] 
        },
        "tanggal_ditambahkan": tanggal,
        "tanggal_diubah": tanggal
    }
    list_data.append(data_baru)
    simpan_json(list_data)
    catat_log("TAMBAH", input_user.get('nama', 'Unknown'))

# update data lama dan perbarui tgl editnya
def update_data_wisata(id_wisata, input_user, list_nama_foto):
    list_data = buka_json()
    tanggal = datetime.now().strftime("%Y-%m-%d")
    for i, item in enumerate(list_data):
        if str(item.get('id')) == str(id_wisata):
            item['identitas'].update({
                "nama": input_user['nama'],
                "deskripsi": input_user['deskripsi'],
                "foto": list_nama_foto,
                "rating": float(input_user.get('rating', 0)),
                "alamat": input_user['alamat'],
                "tipe": input_user['tipe'],
                "maps": input_user.get('maps', '')
            })
            item['operasional'].update({
                "htm": input_user['htm'], 
                "hari_buka": input_user['hari_buka'],
                "jam_operasional": {"buka": input_user['jam_mulai'], "tutup": input_user['jam_selesai']}
            })
            item['informasi_tambahan']['fasilitas'] = input_user.get('fasilitas', [])
            item['informasi_tambahan']['kondisi_jalan'] = input_user['kondisi_jalan']
            item['tanggal_diubah'] = tanggal
            simpan_json(list_data)
            catat_log("EDIT", input_user.get('nama', 'Unknown'))
            return True
    return False

def hapus_data_wisata(id_wisata):
    list_data = buka_json()
    nama_dihapus = "Tidak Diketahui"
    for item in list_data:
        if str(item.get('id')) == str(id_wisata):
            nama_dihapus = item.get('identitas', {}).get('nama', 'Tidak Diketahui')
            break
            
    data_filter = [item for item in list_data if str(item.get('id')) != str(id_wisata)]
    simpan_json(data_filter)
    catat_log("HAPUS", nama_dihapus)

def ambil_detail_spesifik(id_wisata):
    """Mengambil satu data wisata berdasarkan ID."""
    data = buka_json()
    for item in data:
        if str(item.get('id')) == str(id_wisata):
            return item
    return None