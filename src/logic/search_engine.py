# src/logic/search_engine.py
def cari_wisata(nama_wisata, data_master):
    """Mencari wisata berdasarkan nama (case-insensitive, substring)."""
    if not nama_wisata.strip():
        return data_master
    keyword = nama_wisata.lower().strip()
    hasil = []
    for item in data_master:
        identitas = item.get('identitas', {})
        nama = identitas.get('nama', '').lower()
        if keyword in nama:
            hasil.append(item)
    return hasil