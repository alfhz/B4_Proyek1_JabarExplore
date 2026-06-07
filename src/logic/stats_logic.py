"""
Fasad modul statistik untuk Dashboard (nama selaras dokumen proyek).
Implementasi: stats_engine.py
"""

from src.logic.stats_engine import (
    DAFTAR_KAB_KOTA_JABAR,
    ambil_data_stats,
    ambil_metrik_data,
    buat_dataframe,
    get_official_kabupaten,
    hitung_rata_rating,
)

__all__ = [
    "DAFTAR_KAB_KOTA_JABAR",
    "ambil_data_stats",
    "ambil_metrik_data",
    "buat_dataframe",
    "get_official_kabupaten",
    "hitung_rata_rating",
]
