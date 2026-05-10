# src/utils/validators.py
import os
from src.utils.file_handler import buka_json

def format_harga_idr(harga):
    try:
        if isinstance(harga, str):
            v = int(harga.replace(".", "").replace(",", ""))
        else:
            v = int(harga)
        if v == 0:
            return "Gratis"
        return f"Rp {v:,}".replace(',', '.')
    except (TypeError, ValueError):
        return "N/A"

def validasi_input_form(data_nama, data_htm):
    if not data_nama.strip():
        return False, "Nama Wisata tidak boleh kosong!"
    if not str(data_htm).replace('.', '').replace(',', '').isdigit():
        return False, "HTM harus berupa angka!"
    return True, "Valid"

def parse_harga_ke_int(harga_str):
    try:
        return int(str(harga_str).replace('.', '').replace(',', ''))
    except:
        return 0

def cek_kondisi_akses(kode):
    """Mengubah kode akses jalan menjadi deskripsi tekstual."""
    mapping = {
        "Sangat Baik": "Jalan beraspal mulus, lebar, dan terawat.",
        "Baik": "Jalan beraspal, nyaman dilalui semua kendaraan.",
        "Cukup": "Jalan beraspal namun berlubang di beberapa titik.",
        "Rusak Ringan": "Jalan rusak ringan, perlu kehati-hatian.",
        "Rusak Berat": "Jalan rusak parah, hanya kendaraan offroad.",
        "aspal": "Jalan aspal mulus.",
        "tanah": "Jalan tanah, kurang nyaman saat hujan."
    }
    return mapping.get(kode, kode)

def cek_duplikat_nama(nama, id_sekarang=None):
    data = buka_json()
    for item in data:
        if item['identitas']['nama'].strip().lower() == nama.strip().lower():
            if id_sekarang and item['id'] == id_sekarang: continue
            return True
    return False

def cek_angka(teks): return str(teks).isdigit()

def cek_rating(rate):
    try: return 0 <= float(rate) <= 5
    except: return False
    
def cek_ukuran_foto(path):
    if not os.path.exists(path): return True
    return os.path.getsize(path) <= 2 * 1024 * 1024

def cek_input_kosong(data_map):
    field_kosong = []
    for label, nilai in data_map.items():
        if not nilai or str(nilai).strip() == "":
            field_kosong.append(label)
    return field_kosong