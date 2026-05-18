"""
Fasad modul statistik untuk Dashboard (nama selaras dokumen proyek).
Implementasi: stats_engine.py
"""

from src.logic.stats_engine import (
    ambil_data_stats,
    ambil_metrik_data,
    buat_dataframe,
    hitung_rata_rating,
)

__all__ = [
    "ambil_data_stats",
    "ambil_metrik_data",
    "buat_dataframe",
    "hitung_rata_rating",
]
