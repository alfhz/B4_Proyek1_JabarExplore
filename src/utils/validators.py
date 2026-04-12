def format_harga_idr(harga):
    try:
        # Bersihkan string harga
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
    """Mengubah string harga (misal '50.000' atau '50000') menjadi integer"""
    try:
        return int(str(harga_str).replace('.', '').replace(',', ''))
    except:
        return 0