"""
src/utils/validators.py
=======================
Modul utilitas validasi dan pemformatan data wisata.
Berisi fungsi-fungsi kecil yang membantu memastikan data input
dari user/scraper adalah valid sebelum disimpan ke database.

Dependensi  : uuid (built-in)
Digunakan oleh : crud_engine.py, scrap_logic.py, form_wisata.py
"""

import uuid
import os


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI GENERATOR ID
# ─────────────────────────────────────────────────────────────────────────────

def buat_id():
    """
    Membuat ID unik pendek untuk entri data wisata baru.

    I.S : Tidak ada kondisi awal khusus (stateless).
    F.S : Mengembalikan string ID dengan format "auto-xxxxxx"
          (6 karakter pertama dari UUID acak).
          Dijamin unik secara probabilistik.

    Return:
        str: ID unik, contoh: "auto-3f9c1b"
    """
    return f"auto-{str(uuid.uuid4())[:6]}"


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI VALIDASI DATA
# ─────────────────────────────────────────────────────────────────────────────

def cek_duplikat(item_or_nama, data_master):
    """
    Memeriksa apakah sebuah wisata sudah ada di dalam database (duplikat).
    Perbandingan dilakukan berdasarkan nama wisata (case-insensitive).

    I.S : item_or_nama adalah dict (data wisata) atau string (nama wisata).
          data_master adalah list seluruh data wisata yang sudah tersimpan.
    F.S : Mengembalikan True jika nama wisata sudah ada di data_master.
          Mengembalikan False jika wisata belum ada (aman untuk ditambahkan).

    Param:
        item_or_nama (dict | str): Data wisata baru atau string nama wisata.
        data_master (list[dict]) : Seluruh data wisata saat ini.
    Return:
        bool: True jika duplikat, False jika belum ada.
    """
    if not item_or_nama:
        return True  # Input kosong dianggap tidak valid (tolak)

    # Ekstrak nama dari dict atau gunakan langsung sebagai string
    if isinstance(item_or_nama, dict):
        nama = item_or_nama.get('judul') or item_or_nama.get('identitas', {}).get('nama', '')
    else:
        nama = str(item_or_nama)

    nama_lower = nama.lower().strip()

    # Bandingkan dengan setiap entri di database
    for existing in data_master:
        ex_nama = existing.get('identitas', {}).get('nama', '').lower().strip()
        if ex_nama == nama_lower:
            return True  # Ditemukan duplikat

    return False  # Tidak ada duplikat


def validasi_item(item):
    """
    Memvalidasi apakah sebuah item hasil scraping layak untuk disimpan.
    Syarat minimum: item harus memiliki judul atau nama yang tidak kosong.

    I.S : item adalah dict hasil scraping yang belum tentu lengkap.
    F.S : Mengembalikan tuple (status, pesan).
          status True  → item valid dan siap diproses.
          status False → item tidak valid, disertai alasan penolakan.

    Param:
        item (dict): Data wisata hasil scraping.
    Return:
        tuple(bool, str): (True, "Valid") atau (False, "alasan").
    """
    nama = item.get('judul') or item.get('identitas', {}).get('nama')
    if not nama:
        return False, "Judul/Nama kosong"
    return True, "Valid"


def validasi_input_form(data_nama, data_htm):
    """
    Memvalidasi input dari form tambah/edit wisata sebelum disimpan.
    Memastikan nama tidak kosong dan HTM berisi angka yang valid.

    I.S : data_nama dan data_htm adalah string dari input field form user.
          Kedua nilai belum divalidasi dan bisa berisi apapun.
    F.S : Mengembalikan tuple (status, pesan).
          Jika semua valid, mengembalikan (True, "Valid").
          Jika ada yang salah, mengembalikan (False, pesan_error).

    Param:
        data_nama (str): Nama wisata dari form input.
        data_htm  (str): Harga tiket masuk (HTM) dari form input.
    Return:
        tuple(bool, str): (True, "Valid") atau (False, "pesan kesalahan").
    """
    # Nama tidak boleh kosong atau hanya spasi
    if not data_nama.strip():
        return False, "Nama Wisata tidak boleh kosong!"

    # HTM harus berupa angka (boleh menggunakan pemisah titik/koma)
    if not str(data_htm).replace('.', '').replace(',', '').isdigit():
        return False, "HTM harus berupa angka!"

    return True, "Valid"


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI PEMFORMATAN DATA
# ─────────────────────────────────────────────────────────────────────────────

def format_harga_idr(harga):
    """
    Memformat angka harga menjadi string Rupiah yang mudah dibaca.
    Contoh: 20000 → "Rp 20.000", 0 → "Gratis"

    I.S : harga adalah int atau string angka (bisa mengandung titik/koma).
          Bisa juga None atau string tidak valid.
    F.S : Mengembalikan string harga terformat dalam Rupiah.
          Jika harga = 0, mengembalikan "Gratis".
          Jika konversi gagal (input tidak valid), mengembalikan "N/A".

    Param:
        harga (int | str): Nilai harga tiket masuk.
    Return:
        str: String harga terformat, contoh: "Rp 20.000", "Gratis", "N/A"
    """
    try:
        # Normalisasi: hapus pemisah ribuan lalu konversi ke int
        if isinstance(harga, str):
            v = int(harga.replace(".", "").replace(",", ""))
        else:
            v = int(harga)

        if v == 0:
            return "Gratis"

        # Format dengan pemisah ribuan lalu ganti koma → titik (format ID)
        return f"Rp {v:,}".replace(',', '.')

    except (TypeError, ValueError):
        return "N/A"


def parse_harga_ke_int(harga_str):
    """
    Mengubah string harga (dengan format apapun) menjadi integer murni.
    Berguna sebelum menyimpan data ke JSON agar tipe data konsisten.

    I.S : harga_str adalah string yang merepresentasikan angka harga.
          Bisa mengandung karakter titik/koma sebagai pemisah ribuan.
    F.S : Mengembalikan nilai integer bersih dari harga.
          Jika konversi gagal, mengembalikan 0 sebagai fallback.

    Param:
        harga_str (str | int | float): Nilai harga dalam berbagai format.
    Return:
        int: Nilai harga sebagai integer. Contoh: "20.000" → 20000
    """
    try:
        return int(str(harga_str).replace('.', '').replace(',', ''))
    except Exception:
        return 0


def cek_kondisi_akses(kode):
    """
    Mengubah kode/label kondisi jalan menjadi deskripsi tekstual panjang.
    Digunakan untuk menampilkan informasi kondisi jalan di halaman detail wisata.

    I.S : kode adalah string label kondisi jalan (misalnya "Baik", "Cukup").
          Label ini biasanya dipilih dari ComboBox di form wisata.
    F.S : Mengembalikan string deskripsi kondisi jalan yang informatif.
          Jika kode tidak dikenal, mengembalikan kode aslinya (pass-through).

    Param:
        kode (str): Label kondisi jalan dari database.
    Return:
        str: Deskripsi tekstual kondisi jalan, atau kode asli jika tidak dikenal.
    """
    mapping = {
        "Sangat Baik":  "Jalan beraspal mulus, lebar, dan terawat.",
        "Baik":         "Jalan beraspal, nyaman dilalui semua kendaraan.",
        "Cukup":        "Jalan beraspal namun berlubang di beberapa titik.",
        "Rusak Ringan": "Jalan rusak ringan, perlu kehati-hatian.",
        "Rusak Berat":  "Jalan rusak parah, hanya kendaraan offroad.",
        "aspal":        "Jalan aspal mulus.",
        "tanah":        "Jalan tanah, kurang nyaman saat hujan.",
    }
    return mapping.get(kode, kode)


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI VALIDASI FORM WISATA (GUI)
# ─────────────────────────────────────────────────────────────────────────────

def cek_duplikat_nama(nama, id_sekarang=None):
    """
    Memeriksa apakah nama wisata sudah ada di database (case-insensitive).
    Jika id_sekarang diberikan, item dengan ID tersebut akan dilewati
    (untuk kasus edit data sendiri).

    Param:
        nama (str): Nama wisata yang akan dicek.
        id_sekarang (str|None): ID item yang sedang diedit (skip duplikat diri sendiri).
    Return:
        bool: True jika nama sudah ada (duplikat), False jika aman.
    """
    from src.utils.file_handler import buka_json
    data = buka_json()
    for item in data:
        if item.get('identitas', {}).get('nama', '').strip().lower() == nama.strip().lower():
            if id_sekarang and item.get('id') == id_sekarang:
                continue
            return True
    return False


def cek_angka(teks):
    """
    Memeriksa apakah teks berisi angka saja.

    Param:
        teks (str): Teks yang akan dicek.
    Return:
        bool: True jika teks berisi digit, False jika tidak.
    """
    return str(teks).isdigit()


def cek_rating(rate):
    """
    Memeriksa apakah rating berada dalam rentang 0-5.

    Param:
        rate (str|float): Nilai rating yang akan dicek.
    Return:
        bool: True jika valid (0 <= rating <= 5), False jika tidak.
    """
    try:
        return 0 <= float(rate) <= 5
    except (ValueError, TypeError):
        return False


def cek_ukuran_foto(path):
    """
    Memeriksa apakah ukuran file foto tidak melebihi batas 2 MB.

    Param:
        path (str): Path file foto.
    Return:
        bool: True jika ukuran <= 2 MB atau file tidak ada, False jika melebihi.
    """
    if not os.path.exists(path):
        return True
    return os.path.getsize(path) <= 2 * 1024 * 1024


def cek_input_kosong(data_map):
    """
    Memeriksa field mana saja yang masih kosong dari dict {label: nilai}.

    Param:
        data_map (dict): Mapping {label_field: nilai_field}.
    Return:
        list[str]: Daftar label field yang kosong, atau [] jika semua terisi.
    """
    field_kosong = []
    for label, nilai in data_map.items():
        if not nilai or str(nilai).strip() == "":
            field_kosong.append(label)
    return field_kosong