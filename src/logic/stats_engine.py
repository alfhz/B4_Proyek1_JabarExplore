"""
src/logic/stats_engine.py
=========================
Mesin kalkulasi statistik Dashboard — berbasis Pandas.
Modul ini mengolah data mentah JSON menjadi metrik dan agregat
yang siap ditampilkan di layar Dashboard.

Alur data:
  buka_json() → buat_dataframe() → hitung_metrik_dashboard() / rekap_wisata_per_kota()

Dependensi  : pandas
Digunakan oleh : stats_logic.py (fasad publik), dashboard.py (via stats_logic)
"""

from __future__ import annotations

import pandas as pd


def _normalisasi_baris(data: list[dict]) -> list[dict]:
    """
    [FUNGSI INTERNAL] Menyatukan dua format data wisata yang berbeda
    menjadi satu skema baris yang seragam untuk Pandas.

    Format 1 (nested)  : {"identitas": {...}, "operasional": {...}}
    Format 2 (datar)   : {"nama": "...", "kategori": "...", ...}

    I.S : data adalah list of dict dengan format yang mungkin beragam
          (nested dari CRUD atau datar dari scraping lama).
    F.S : Mengembalikan list of dict dengan kolom seragam:
          id, nama, kategori, kabupaten, rating, jumlah_ulasan,
          harga_tiket, tanggal_ditambahkan.
          Elemen yang bukan dict dilewati (dibuang).

    Param:
        data (list[dict]): Data mentah dari buka_json().
    Return:
        list[dict]: List baris yang terstandarisasi.
    """
    rows: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue  # Lewati item yang bukan dict (data korup)

        if "identitas" in item:
            # ── Format Nested (hasil CRUD / form input) ───────────────────
            idn = item["identitas"]
            op  = item.get("operasional", {})

            # Ekstrak kabupaten dari bagian pertama alamat (sebelum koma)
            alamat = (idn.get("alamat") or "").strip()
            kab    = alamat.split(",")[0].strip() if "," in alamat else (alamat or "Lainnya")

            # Normalisasi HTM: hapus pemisah ribuan lalu konversi ke int
            htm_raw = op.get("htm", 0)
            try:
                harga = int(str(htm_raw).replace(".", "").replace(",", ""))
            except (TypeError, ValueError):
                harga = 0

            try:
                rating = float(idn.get("rating") or 0)
            except (TypeError, ValueError):
                rating = 0.0

            rows.append({
                "id":                  item.get("id", ""),
                "nama":               idn.get("nama", "-"),
                "kategori":           idn.get("tipe") or idn.get("kategori") or "Umum",
                "kabupaten":          kab or "Lainnya",
                "rating":             rating,
                "jumlah_ulasan":      int(idn.get("jumlah_ulasan") or 0),
                "harga_tiket":        harga,
                "tanggal_ditambahkan": item.get("tanggal_ditambahkan", "2024-01-01"),
            })
        else:
            # ── Format Datar (data lama / hasil import langsung) ──────────
            try:
                rating = float(item.get("rating") or 0)
            except (TypeError, ValueError):
                rating = 0.0
            try:
                harga = int(item.get("harga_tiket") or 0)
            except (TypeError, ValueError):
                harga = 0

            rows.append({
                "id":                  item.get("id", ""),
                "nama":               item.get("nama", "-"),
                "kategori":           item.get("kategori", "Umum"),
                "kabupaten":          item.get("kabupaten", "Lainnya"),
                "rating":             rating,
                "jumlah_ulasan":      int(item.get("jumlah_ulasan") or 0),
                "harga_tiket":        harga,
                "tanggal_ditambahkan": item.get("tanggal_ditambahkan", "2024-01-01"),
            })
    return rows


def buat_dataframe(data: list[dict]) -> pd.DataFrame:
    """
    Mengubah list data wisata mentah menjadi DataFrame Pandas yang siap diolah.
    Memanggil _normalisasi_baris() terlebih dahulu untuk menyeragamkan format.

    I.S : data adalah list of dict hasil buka_json(), format bisa beragam.
          Bisa berisi list kosong [] jika file JSON kosong.
    F.S : Mengembalikan pd.DataFrame dengan kolom terstandar:
          id, nama, kategori, kabupaten, rating, jumlah_ulasan,
          harga_tiket, tanggal_ditambahkan.
          Jika data kosong, mengembalikan DataFrame kosong.

    Param:
        data (list[dict]): Data wisata mentah dari buka_json().
    Return:
        pd.DataFrame: DataFrame siap pakai untuk kalkulasi statistik.
    """
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(_normalisasi_baris(data))


def hitung_rata_rating(list_rating: list) -> float:
    """
    Menghitung rata-rata rating dari sebuah list nilai rating.

    I.S : list_rating adalah list of float/int berisi nilai rating masing-masing wisata.
          Bisa berisi list kosong [] jika belum ada data rating.
    F.S : Mengembalikan nilai rata-rata rating dibulatkan 2 angka desimal.
          Jika list kosong, mengembalikan 0.0.

    Param:
        list_rating (list): List nilai rating (0.0 - 5.0).
    Return:
        float: Rata-rata rating. Contoh: [4.5, 4.3, 4.1] → 4.3
    """
    if not list_rating:
        return 0.0
    return round(sum(list_rating) / len(list_rating), 2)


def hitung_metrik_dashboard(df: pd.DataFrame) -> dict:
    """
    Menghitung metrik utama untuk ditampilkan di kartu ringkasan Dashboard.
    Menghasilkan total wisata, rata-rata rating, daftar top destinasi, dll.

    I.S : df adalah pd.DataFrame hasil buat_dataframe().
          Bisa berupa DataFrame kosong jika tidak ada data wisata.
    F.S : Mengembalikan dict berisi 5 metrik kunci:
          - total_wisata  : jumlah seluruh destinasi wisata (int)
          - rata_rating   : rata-rata rating semua wisata (float)
          - top_destinasi : list 4 wisata dengan rating tertinggi (list[dict])
          - total_ulasan  : total akumulasi ulasan seluruh wisata (int)
          - rata_harga    : rata-rata harga tiket masuk (float)
          Jika df kosong, semua nilai di-set ke 0 / list kosong.

    Param:
        df (pd.DataFrame): DataFrame wisata dari buat_dataframe().
    Return:
        dict: Dict metrik dashboard.
    """
    if df.empty:
        return {
            "total_wisata":  0,
            "rata_rating":   0.0,
            "top_destinasi": [],
            "total_ulasan":  0,
            "rata_harga":    0.0,
        }

    ratings = df["rating"].tolist() if "rating" in df.columns else []

    # Ambil 4 wisata dengan rating tertinggi untuk kartu Top Destinasi
    cols_needed = ["nama", "kategori", "rating", "jumlah_ulasan", "harga_tiket"]
    top: list[dict] = []
    if all(c in df.columns for c in cols_needed):
        top = (
            df[cols_needed]
            .sort_values("rating", ascending=False)
            .head(4)
            .to_dict("records")
        )

    return {
        "total_wisata":  len(df),
        "rata_rating":   hitung_rata_rating(ratings),
        "top_destinasi": top,
        "total_ulasan":  int(df["jumlah_ulasan"].sum()) if "jumlah_ulasan" in df.columns else 0,
        "rata_harga":    round(float(df["harga_tiket"].mean()), 0) if "harga_tiket" in df.columns else 0.0,
    }


def rekap_wisata_per_kota(df: pd.DataFrame) -> dict:
    """
    Menghasilkan berbagai agregat statistik untuk grafik-grafik di Dashboard.
    Setiap kunci dalam hasil dict langsung digunakan oleh fungsi chart di dashboard.py.

    I.S : df adalah pd.DataFrame hasil buat_dataframe().
          Bisa berupa DataFrame kosong jika tidak ada data.
    F.S : Mengembalikan dict berisi 7 agregat Pandas:
          - sebaran_kategori    : jumlah wisata per kategori (Series)
          - total_per_kabupaten : jumlah wisata per kabupaten/kota (Series)
          - total_rating_wisata : rata-rata rating per kategori (Series)
          - distribusi_harga    : jumlah wisata per kelompok harga (Series)
          - distribusi_rating   : jumlah wisata per bintang 1-5 (Series)
          - tren_bulanan        : jumlah wisata ditambahkan per bulan (Series)
          - scatter_data        : list dict untuk grafik scatter (list[dict])
          Jika df kosong, semua nilai adalah Series kosong / list kosong.

    Param:
        df (pd.DataFrame): DataFrame wisata dari buat_dataframe().
    Return:
        dict: Dict berisi seluruh agregat statistik.
    """
    if df.empty:
        z = pd.Series(dtype=int)
        return {
            "sebaran_kategori":    z,
            "total_per_kabupaten": z,
            "total_rating_wisata": pd.Series(dtype=float),
            "distribusi_harga":    z,
            "distribusi_rating":   pd.Series({i: 0 for i in range(1, 6)}, dtype=int),
            "tren_bulanan":        z,
            "scatter_data":        [],
        }

    sebaran_kategori = df["kategori"].value_counts() if "kategori" in df.columns else pd.Series(dtype=int)
    total_per_kabupaten = df["kabupaten"].value_counts() if "kabupaten" in df.columns else pd.Series(dtype=int)
    total_rating_wisata = (
        df.groupby("kategori")["rating"].mean().round(2)
        if all(c in df.columns for c in ("kategori", "rating"))
        else pd.Series(dtype=float)
    )

    distribusi_harga = pd.Series(dtype=int)
    if "harga_tiket" in df.columns:
        bins = [0, 15_000, 30_000, 75_000, float("inf")]
        labels = ["<=15k\n(Murah)", "15k-30k\n(Terjangkau)", "30k-75k\n(Menengah)", ">75k\n(Premium)"]
        d2 = df.copy()
        d2["bucket"] = pd.cut(d2["harga_tiket"], bins=bins, labels=labels, right=True)
        distribusi_harga = d2["bucket"].value_counts().reindex(labels).fillna(0).astype(int)

    distribusi_rating = pd.Series({i: 0 for i in range(1, 6)}, dtype=int)
    if "rating" in df.columns:
        r = pd.to_numeric(df["rating"], errors="coerce").dropna()
        if not r.empty:
            stars = r.round().clip(1, 5).astype(int)
            distribusi_rating = stars.value_counts().reindex(range(1, 6), fill_value=0).astype(int)

    tren_bulanan = pd.Series(dtype=int)
    if "tanggal_ditambahkan" in df.columns:
        d3 = df.copy()
        d3["tanggal_ditambahkan"] = pd.to_datetime(d3["tanggal_ditambahkan"], errors="coerce")
        d3["bulan"] = d3["tanggal_ditambahkan"].dt.to_period("M")
        tren_bulanan = d3.groupby("bulan").size().sort_index()

    scatter_data: list[dict] = []
    if all(c in df.columns for c in ("rating", "jumlah_ulasan", "kategori", "nama")):
        scatter_data = (
            df[["nama", "rating", "jumlah_ulasan", "kategori"]]
            .rename(columns={"jumlah_ulasan": "ulasan"})
            .to_dict("records")
        )

    return {
        "sebaran_kategori": sebaran_kategori,
        "total_per_kabupaten": total_per_kabupaten,
        "total_rating_wisata": total_rating_wisata,
        "distribusi_harga": distribusi_harga,
        "distribusi_rating": distribusi_rating,
        "tren_bulanan": tren_bulanan,
        "scatter_data": scatter_data,
    }
