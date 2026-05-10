import uuid
from datetime import datetime
from src.utils.file_handler import buka_json, simpan_json

# prosedur penambahan entri baru dengan pembuatan id unik dan stempel waktu terkini
def tambah_data_wisata(input_user, list_nama_foto):
    list_data = buka_json()
    tanggal = datetime.now().strftime("%Y-%m-%d")
    id_acak = f"wst-{uuid.uuid4().hex[:6]}" 
    
    # penyusunan struktur objek data untuk kategori identitas, operasional, dan fasilitas
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
    # penggabungan entri baru ke dalam dataset dan persistensi ke format json
    list_data.append(data_baru)
    simpan_json(list_data)

# prosedur identifikasi dan pembaruan nilai pada entri yang memiliki id sesuai
def update_data_wisata(id_wisata, input_user, list_nama_foto):
    list_data = buka_json()
    tanggal = datetime.now().strftime("%Y-%m-%d")
    for i, item in enumerate(list_data):
        if str(item.get('id')) == str(id_wisata):
            # sinkronisasi seluruh perubahan field identitas, operasional, dan informasi tambahan
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
            # penyimpanan dataset hasil modifikasi dan pengembalian status sukses
            simpan_json(list_data)
            return True
    return False

# prosedur penghapusan entri secara permanen melalui metode filterisasi id
def hapus_data_wisata(id_wisata):
    list_data = buka_json()
    simpan_json([item for item in list_data if str(item.get('id')) != str(id_wisata)])