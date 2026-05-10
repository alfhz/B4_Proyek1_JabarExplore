"""
Fasad modul statistik untuk Dashboard (nama selaras dokumen proyek).
Implementasi: stats_engine.py
"""

from src.logic.stats_engine import (
    rekap_wisata_per_kota,
    hitung_metrik_dashboard,
    buat_dataframe,
    hitung_rata_rating,
)

# ── Daftar Kabupaten/Kota Jawa Barat resmi ──────────────────────────────────
DAFTAR_KAB_KOTA_JABAR = [
    "Bandung", "Bandung Barat", "Bekasi", "Bogor", "Ciamis",
    "Cianjur", "Cirebon", "Depok", "Garut", "Indramayu",
    "Karawang", "Kuningan", "Majalengka", "Pangandaran", "Purwakarta",
    "Subang", "Sukabumi", "Sumedang", "Tasikmalaya",
    "Kota Bandung", "Kota Bekasi", "Kota Bogor", "Kota Cimahi",
    "Kota Cirebon", "Kota Depok", "Kota Sukabumi", "Kota Tasikmalaya",
    "Kota Banjar",
]

# Alias: kata kunci dalam alamat → nama resmi kabupaten/kota
_ALIAS_KOTA: dict[str, str] = {
    "bandung barat": "Bandung Barat",
    "bandung":       "Bandung",
    "bekasi":        "Bekasi",
    "bogor":         "Bogor",
    "ciamis":        "Ciamis",
    "cianjur":       "Cianjur",
    "cirebon":       "Cirebon",
    "depok":         "Depok",
    "garut":         "Garut",
    "indramayu":     "Indramayu",
    "karawang":      "Karawang",
    "kuningan":      "Kuningan",
    "majalengka":    "Majalengka",
    "pangandaran":   "Pangandaran",
    "purwakarta":    "Purwakarta",
    "subang":        "Subang",
    "sukabumi":      "Sukabumi",
    "sumedang":      "Sumedang",
    "tasikmalaya":   "Tasikmalaya",
    "cimahi":        "Kota Cimahi",
    "banjar":        "Kota Banjar",
}


def get_official_kabupaten(alamat_raw: str) -> str:
    """
    Petakan string alamat mentah ke nama kabupaten/kota resmi Jawa Barat.
    Contoh: 'Subang, Jawa Barat' → 'Subang'
    """
    if not alamat_raw:
        return "Lainnya"
    teks = alamat_raw.lower()
    # Coba dari yang paling spesifik dulu (2 kata) ke yang umum
    for kunci, nama in _ALIAS_KOTA.items():
        if kunci in teks:
            return nama
    # Fallback: ambil bagian pertama sebelum koma
    bagian = alamat_raw.split(",")[0].strip()
    return bagian if bagian else "Lainnya"


def ambil_metrik_data(df, *, raw_data=None) -> dict:
    """
    Alias dari hitung_metrik_dashboard dengan dukungan raw_data tambahan.
    raw_data dipakai untuk menambahkan referensi objek asli di top_destinasi.
    """
    metrik = hitung_metrik_dashboard(df)

    # Tambahkan tanggal_terakhir
    metrik.setdefault("tanggal_terakhir", "-")

    # Enrichment top_destinasi dengan '_raw' jika raw_data tersedia
    if raw_data:
        raw_map: dict[str, dict] = {}
        for item in raw_data:
            nama = item.get("identitas", {}).get("nama") or item.get("nama", "")
            if nama:
                raw_map[nama.lower()] = item

        enriched = []
        for dest in metrik.get("top_destinasi", []):
            nama_key = dest.get("nama", "").lower()
            dest["_raw"] = raw_map.get(nama_key)
            enriched.append(dest)
        metrik["top_destinasi"] = enriched

    return metrik


def ambil_data_stats(df) -> dict:
    """Alias dari rekap_wisata_per_kota — nama sesuai dashboard.py baru."""
    return rekap_wisata_per_kota(df)


__all__ = [
    "rekap_wisata_per_kota",
    "hitung_metrik_dashboard",
    "buat_dataframe",
    "hitung_rata_rating",
    "ambil_metrik_data",
    "ambil_data_stats",
    "DAFTAR_KAB_KOTA_JABAR",
    "get_official_kabupaten",
]
