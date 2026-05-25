import uuid
from src.utils.file_handler import buka_json, simpan_json, upload_foto_wisata, catat_log
from datetime import date, datetime

# ------------ CRUD ENGINE — Logika Tambah, Edit, Hapus, Baca Detail ------------
def tambah_data_wisata(input_user, list_nama_foto):
    list_data = buka_json(force_reload=True)

    foto_final = []
    
    def proses_satu_foto(f):
        if not f: return "default.png"
        # Jika f hanya nama file (bukan path/URL), berarti sudah di-upload oleh form_wisata
        if "/" not in f and "\\" not in f and not f.startswith("http"):
            return f
        return upload_foto_wisata(f)

    if isinstance(list_nama_foto, list) and list_nama_foto:
        for f in list_nama_foto:
            foto_final.append(proses_satu_foto(f))
    elif isinstance(list_nama_foto, str) and list_nama_foto:
        foto_final = [proses_satu_foto(list_nama_foto)]
    
    if not foto_final:
        foto_final = ["default.png"]

    tanggal = datetime.now().strftime("%Y-%m-%d")

    # Buat struktur data terstandar sesuai format JSON yang diharapkan
    data_baru = {
        "id": f"wst-{uuid.uuid4().hex[:6]}",
        "identitas": {
            "nama":          input_user['nama'],
            "deskripsi":     input_user.get('deskripsi', ''),
            "foto":          foto_final,
            "rating":        float(input_user.get('rating', 0) or 0),
            "alamat":        input_user['alamat'],
            "maps":          input_user.get('maps', ''),
            "tipe":          input_user['tipe'],
            "jumlah_ulasan": int(input_user.get('jumlah_ulasan', 0))
        },
        "operasional": {
            "htm":       input_user['htm'],
            "hari_buka": input_user.get('hari_buka', []),
            "jam_operasional": {
                "buka":  input_user['jam_mulai'],
                "tutup": input_user['jam_selesai']
            }
        },
        "informasi_tambahan": {
            "fasilitas":          input_user.get('fasilitas', []),
            "kondisi_jalan":      input_user.get('kondisi_jalan', '')
        },
        "tanggal_ditambahkan": tanggal,
        "tanggal_diubah": tanggal
    }

    # Tambahkan ke list dan simpan ke disk
    list_data.append(data_baru)
    simpan_json(list_data)
    catat_log("TAMBAH", input_user.get('nama', 'Unknown'))

# ----------------- UPDATE — Edit Data Wisata -----------------
def update_data_wisata(id_wisata, input_user, list_nama_foto):
    list_data = buka_json(force_reload=True)
    tanggal = datetime.now().strftime("%Y-%m-%d")

    # Cari entri yang cocok berdasarkan ID
    for i, item in enumerate(list_data):
        if str(item.get('id')) == str(id_wisata):
            # Update identitas
            item['identitas'].update({
                "nama":          input_user['nama'],
                "deskripsi":     input_user.get('deskripsi', item.get('identitas', {}).get('deskripsi', '')),
                "foto":          list_nama_foto,
                "rating":        float(input_user.get('rating', 0) or 0),
                "alamat":        input_user['alamat'],
                "tipe":          input_user['tipe'],
                "maps":          input_user.get('maps', '')
            })
            # Update operasional
            item['operasional'].update({
                "htm":       input_user['htm'],
                "hari_buka": input_user.get('hari_buka', []),
                "jam_operasional": {
                    "buka":  input_user['jam_mulai'],
                    "tutup": input_user['jam_selesai']
                }
            })
            # Update informasi tambahan
            item['informasi_tambahan']['fasilitas'] = input_user.get('fasilitas', [])
            item['informasi_tambahan']['kondisi_jalan'] = input_user.get('kondisi_jalan', '')
            item['tanggal_diubah'] = tanggal

            simpan_json(list_data)
            catat_log("EDIT", input_user.get('nama', 'Unknown'))
            return True

    # Jika ID tidak ditemukan di seluruh list
    return False


# --------------- DELETE — Hapus Data Wisata ---------------
def hapus_data_wisata(id_wisata):
    list_data = buka_json(force_reload=True)

    # Cari nama wisata sebelum dihapus (untuk log)
    nama_dihapus = "Tidak Diketahui"
    for item in list_data:
        if str(item.get('id')) == str(id_wisata):
            nama_dihapus = item.get('identitas', {}).get('nama', 'Tidak Diketahui')
            break

    # Filter: simpan semua entri kecuali yang ID-nya cocok
    data_filter = [item for item in list_data if str(item.get('id')) != str(id_wisata)]

    simpan_json(data_filter)
    catat_log("HAPUS", nama_dihapus)


# ----------------- READ DETAIL — Ambil Data Wisata Spesifik  -----------------
def ambil_detail_spesifik(id_wisata):
    data = buka_json()

    for item in data:
        if str(item.get('id')) == str(id_wisata):
            return item

    return None