"""
src/logic/crud_engine.py
========================
Modul logika CRUD (Create, Read, Update, Delete) untuk data wisata.
Setiap operasi di sini menggunakan file_handler sebagai lapisan
akses database (JSON), sehingga crud_engine tidak berurusan
langsung dengan file system.

Alur umum:
  User mengisi Form → crud_engine memproses → file_handler menyimpan ke JSON

Dependensi  : uuid, datetime, file_handler (buka_json, simpan_json, upload_foto_wisata)
Digunakan oleh : form_wisata.py (GUI tambah/edit), daftar_wisata.py (GUI hapus)
"""

import uuid
from src.utils.file_handler import buka_json, simpan_json, upload_foto_wisata, catat_log
from datetime import date, datetime


# ─────────────────────────────────────────────────────────────────────────────
# CREATE — Tambah Data Wisata Baru
# ─────────────────────────────────────────────────────────────────────────────

def tambah_data_wisata(input_user, list_nama_foto):
    """
    Menambahkan satu data wisata baru ke dalam database JSON.
    Mengonversi input mentah dari form GUI menjadi struktur data
    terstandar sebelum disimpan.

    I.S : input_user adalah dict berisi data dari form input pengguna
          (nama, rating, alamat, maps, tipe, htm, hari_buka, dll).
          list_nama_foto bisa berupa:
            - list[str]: Daftar nama file foto (dari form multi-foto)
            - str: Path tunggal file foto lokal atau URL gambar
    F.S : Entri wisata baru dengan ID unik ditambahkan ke data_wisata.json.
          Tanggal hari ini dicatat otomatis sebagai tanggal_ditambahkan.

    Param:
        input_user    (dict): Data wisata dari form input GUI.
        list_nama_foto (list|str): Daftar nama file foto atau path tunggal.
    """
    # Baca data terkini dari disk (force_reload agar tidak tertinggal perubahan lain)
    list_data = buka_json(force_reload=True)

    # Proses foto: support list (multi-foto) dan string (single foto)
    foto_final = []
    if isinstance(list_nama_foto, list) and list_nama_foto:
        for f in list_nama_foto:
            # Panggil upload_foto_wisata untuk tiap item (bisa URL atau path lokal)
            foto_final.append(upload_foto_wisata(f))
    elif isinstance(list_nama_foto, str) and list_nama_foto:
        # Jika string (path tunggal), upload dan bungkus dalam list agar konsisten
        foto_final = [upload_foto_wisata(list_nama_foto)]
    
    if not foto_final:
        foto_final = ["default.png"]

    tanggal = datetime.now().strftime("%Y-%m-%d")

    # Buat struktur data terstandar sesuai skema data_wisata.json
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
            "kondisi_jalan":      input_user.get('kondisi_jalan', ''),
            "jarak_dari_kab_kota": input_user.get('jarak_dari_kab_kota', '')
        },
        "tanggal_ditambahkan": tanggal,
        "tanggal_diubah": tanggal
    }

    # Tambahkan ke list dan simpan ke disk
    list_data.append(data_baru)
    simpan_json(list_data)
    catat_log("TAMBAH", input_user.get('nama', 'Unknown'))


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE — Perbarui Data Wisata yang Ada
# ─────────────────────────────────────────────────────────────────────────────

def update_data_wisata(id_wisata, input_user, list_nama_foto):
    """
    Memperbarui data wisata yang sudah ada berdasarkan ID-nya.
    Mencari entri di list, lalu memperbarui field-field yang relevan.

    I.S : id_wisata adalah ID unik wisata yang ingin diedit.
          input_user adalah dict berisi data terbaru dari form edit.
          list_nama_foto bisa berupa:
            - list[str]: Daftar nama file foto (dari form multi-foto)
            - str: Path tunggal foto baru (legacy single-foto mode)
    F.S : Entri dengan ID tersebut diperbarui dengan data baru.
          Mengembalikan True jika berhasil, False jika ID tidak ditemukan.

    Param:
        id_wisata      (str): ID unik wisata yang ingin diperbarui.
        input_user    (dict): Data terbaru dari form edit GUI.
        list_nama_foto (list|str): Daftar foto baru atau path tunggal.
    Return:
        bool: True jika entri ditemukan dan berhasil diperbarui, False jika tidak.
    """
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


# ─────────────────────────────────────────────────────────────────────────────
# DELETE — Hapus Data Wisata
# ─────────────────────────────────────────────────────────────────────────────

def hapus_data_wisata(id_wisata):
    """
    Menghapus data wisata dari database berdasarkan ID-nya.
    Menggunakan teknik filter list (bukan delete in-place) untuk keamanan.

    I.S : id_wisata adalah ID unik wisata yang ingin dihapus.
          File JSON sudah dapat dibaca.
    F.S : Seluruh entri dengan ID tersebut dihilangkan dari list.
          File JSON diperbarui tanpa entri yang dihapus.
          Jika ID tidak ditemukan, file disimpan kembali tanpa perubahan.

    Param:
        id_wisata (str): ID unik wisata yang ingin dihapus.
    """
    list_data = buka_json(force_reload=True)

    # Cari nama wisata sebelum dihapus (untuk log)
    nama_dihapus = "Tidak Diketahui"
    for item in list_data:
        if str(item.get('id')) == str(id_wisata):
            nama_dihapus = item.get('identitas', {}).get('nama', 'Tidak Diketahui')
            break

    # Filter: simpan semua entri KECUALI yang ID-nya cocok
    data_filter = [item for item in list_data if str(item.get('id')) != str(id_wisata)]

    simpan_json(data_filter)
    catat_log("HAPUS", nama_dihapus)


# ─────────────────────────────────────────────────────────────────────────────
# READ — Baca Detail Satu Wisata
# ─────────────────────────────────────────────────────────────────────────────

def ambil_detail_spesifik(id_wisata):
    """
    Mengambil satu data wisata lengkap berdasarkan ID uniknya.
    Digunakan saat halaman detail wisata perlu memuat data terbaru dari disk.

    I.S : id_wisata adalah string ID unik wisata yang dicari.
          File JSON sudah dapat dibaca.
    F.S : Mengembalikan dict lengkap satu wisata jika ID ditemukan.
          Mengembalikan None jika tidak ada wisata dengan ID tersebut.

    Param:
        id_wisata (str): ID unik wisata yang ingin diambil.
    Return:
        dict | None: Data wisata lengkap, atau None jika tidak ditemukan.
    """
    data = buka_json()

    for item in data:
        if str(item.get('id')) == str(id_wisata):
            return item  # Kembalikan entri pertama yang cocok

    return None  # ID tidak ditemukan