
import uuid
import os


# fungsi untuk membuat ID unik pendek untuk entri data wisata baru
def buat_id():
    return f"auto-{str(uuid.uuid4())[:6]}"


# fugsi untuk cek data wisata yang sudah ada di database
def cek_duplikat(item_or_nama, data_master):
    if not item_or_nama:
        return True 

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

# fungsi untuk validasi hasil scraping yang layal untuk disimpan di db
def validasi_item(item):
    nama = item.get('judul') or item.get('identitas', {}).get('nama')
    if not nama:
        return False, "Judul/Nama kosong"
    return True, "Valid"

# fungsi untuk validasi input form tidak boleh kosong
def validasi_input_form(data_nama, data_htm):
    # Nama tidak boleh kosong atau hanya spasi
    if not data_nama.strip():
        return False, "Nama Wisata tidak boleh kosong!"

    # HTM harus berupa angka (boleh menggunakan pemisah titik/koma)
    if not str(data_htm).replace('.', '').replace(',', '').isdigit():
        return False, "HTM harus berupa angka!"

    return True, "Valid"


# funsgi untuk memformat harga menjadi string rupiah
def format_harga_idr(harga):
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

# fungsi untuk mengubah string harga ke int agar json konsisten
def parse_harga_ke_int(harga_str):
    try:
        return int(str(harga_str).replace('.', '').replace(',', ''))
    except Exception:
        return 0

# fungsi unutk
def cek_kondisi_akses(kode):
    mapping = {
        "Sangat Baik":  "Jalan beraspal mulus, lebar, dan terawat.",
        "Baik":         "Jalan beraspal, nyaman dilalui semua kendaraan.",
        "Cukup":        "Jalan beraspal namun berlubang di beberapa titik.",
        "Rusak":        "Jalan rusak , perlu kehati-hatian.",
    }
    return mapping.get(kode, kode)



def cek_duplikat_nama(nama, id_sekarang=None):
    from src.utils.file_handler import buka_json
    data = buka_json()
    for item in data:
        if item.get('identitas', {}).get('nama', '').strip().lower() == nama.strip().lower():
            if id_sekarang and item.get('id') == id_sekarang:
                continue
            return True
    return False


def cek_angka(teks):
    return str(teks).isdigit()


def cek_rating(rate):
    try:
        return 0 <= float(rate) <= 5
    except (ValueError, TypeError):
        return False


def cek_ukuran_foto(path):
    if not os.path.exists(path):
        return True
    return os.path.getsize(path) <= 2 * 1024 * 1024


def cek_input_kosong(data_map):
    field_kosong = []
    for label, nilai in data_map.items():
        if not nilai or str(nilai).strip() == "":
            field_kosong.append(label)
    return field_kosong