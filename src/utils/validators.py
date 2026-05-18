import os
from src.utils.file_handler import buka_json

def format_harga_idr(harga):
    try:
        if not harga or harga == "": return "Gratis"
        v = int(str(harga).replace(".", "").replace(",", ""))
        return "Gratis" if v == 0 else f"Rp {v:,}".replace(',', '.')
    except: return "N/A"

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

# Validator utama untuk cek field kosong
def cek_input_kosong(data_map):
    field_kosong = []
    for label, nilai in data_map.items():
        if not nilai or str(nilai).strip() == "":
            field_kosong.append(label)
    return field_kosong