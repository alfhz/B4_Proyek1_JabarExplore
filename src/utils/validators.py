import hashlib


def buat_id(teks: str) -> str:
    """Membuat ID unik 10 karakter dari hash teks (judul atau URL)."""
    return hashlib.md5(teks.encode('utf-8', errors='ignore')).hexdigest()[:10]


def cek_duplikat(item_baru: dict, data_existing: list) -> bool:
    """
    Memeriksa apakah item_baru sudah ada di data_existing.
    Cek berdasarkan kesamaan 'judul' (case-insensitive) atau 'url_sumber'.
    Return True jika DUPLIKAT, False jika AMAN untuk disimpan.
    """
    judul_baru = item_baru.get("judul", "").strip().lower()
    url_baru   = item_baru.get("url_sumber", "").strip()

    for item in data_existing:
        judul_lama = item.get("judul", "").strip().lower()
        url_lama   = item.get("url_sumber", "").strip()

        if judul_baru and judul_baru == judul_lama:
            return True
        if url_baru and url_lama and url_baru == url_lama:
            return True

    return False


def validasi_item(item: dict) -> tuple:
    """
    Memvalidasi field wajib sebuah item wisata.
    Return (True, "")          → item valid, boleh disimpan.
    Return (False, alasan)     → item tidak valid, harus di-skip.
    """
    judul     = item.get("judul", "").strip()
    deskripsi = item.get("deskripsi", "").strip()

    if not judul:
        return False, "Judul kosong"
    if len(judul) < 3:
        return False, f"Judul terlalu pendek: '{judul}'"
    if not deskripsi:
        return False, "Deskripsi kosong"

    return True, ""
