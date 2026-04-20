# src/utils/validators.py
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