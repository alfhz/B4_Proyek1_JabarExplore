"""
Logika statistik Dashboard (Tim C) — Pandas.
Alur: file_handler.buka_json() → buat_dataframe → ambil_metrik_data / ambil_data_stats
"""

from __future__ import annotations

import pandas as pd


def _normalisasi_baris(data: list[dict]) -> list[dict]:
    """Satukan format nested (identitas/operasional) dan format datar ke satu skema."""
    rows: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "identitas" in item:
            idn = item["identitas"]
            op = item.get("operasional", {})
            alamat = (idn.get("alamat") or "").strip()
            kab = alamat.split(",")[0].strip() if "," in alamat else (alamat or "Lainnya")
            htm_raw = op.get("htm", 0)
            try:
                harga = int(str(htm_raw).replace(".", "").replace(",", ""))
            except (TypeError, ValueError):
                harga = 0
            try:
                rating = float(idn.get("rating") or 0)
            except (TypeError, ValueError):
                rating = 0.0
            rows.append(
                {
                    "id": item.get("id", ""),
                    "nama": idn.get("nama", "-"),
                    "kategori": idn.get("tipe") or idn.get("kategori") or "Umum",
                    "kabupaten": kab or "Lainnya",
                    "rating": rating,
                    "jumlah_ulasan": int(idn.get("jumlah_ulasan") or 0),
                    "harga_tiket": harga,
                    "tanggal_ditambahkan": item.get("tanggal_ditambahkan", "2024-01-01"),
                }
            )
        else:
            try:
                rating = float(item.get("rating") or 0)
            except (TypeError, ValueError):
                rating = 0.0
            try:
                harga = int(item.get("harga_tiket") or 0)
            except (TypeError, ValueError):
                harga = 0
            rows.append(
                {
                    "id": item.get("id", ""),
                    "nama": item.get("nama", "-"),
                    "kategori": item.get("kategori", "Umum"),
                    "kabupaten": item.get("kabupaten", "Lainnya"),
                    "rating": rating,
                    "jumlah_ulasan": int(item.get("jumlah_ulasan") or 0),
                    "harga_tiket": harga,
                    "tanggal_ditambahkan": item.get("tanggal_ditambahkan", "2024-01-01"),
                }
            )
    return rows


def buat_dataframe(data: list[dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(_normalisasi_baris(data))


def hitung_rata_rating(list_rating: list) -> float:
    if not list_rating:
        return 0.0
    return round(sum(list_rating) / len(list_rating), 2)


def ambil_metrik_data(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_wisata": 0,
            "rata_rating": 0.0,
            "top_destinasi": [],
            "total_ulasan": 0,
            "rata_harga": 0.0,
        }

    ratings = df["rating"].tolist() if "rating" in df.columns else []
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
        "total_wisata": len(df),
        "rata_rating": hitung_rata_rating(ratings),
        "top_destinasi": top,
        "total_ulasan": int(df["jumlah_ulasan"].sum()) if "jumlah_ulasan" in df.columns else 0,
        "rata_harga": round(float(df["harga_tiket"].mean()), 0) if "harga_tiket" in df.columns else 0.0,
    }


def ambil_data_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        z = pd.Series(dtype=int)
        return {
            "sebaran_kategori": z,
            "total_per_kabupaten": z,
            "total_rating_wisata": pd.Series(dtype=float),
            "distribusi_harga": z,
            "distribusi_rating": pd.Series({i: 0 for i in range(1, 6)}, dtype=int),
            "tren_bulanan": z,
            "scatter_data": [],
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
