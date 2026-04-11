


# formater harga
def format_harga_idr(harga):
    try:
        if int(harga) == 0: return "Gratis"
        return f"Rp {int(harga):,}".replace(',', '.')
    except:
        return "N/A"

# validasi form tambah wisata
def validasi_input_form(data_nama, data_htm):
    if not data_nama.strip():
        return False, "Nama Wisata tidak boleh kosong!"
    if not str(data_htm).isdigit():
        return False, "HTM harus berupa angka!"
    return True, "Valid"

def format_harga_idr(harga):
    try:
        v = int(str(harga).replace(".", "").replace(",", ""))
        if v == 0:
            return "Gratis"
        return f"Rp {v:,}".replace(",", ".")
    except (TypeError, ValueError):
        return "N/A"

