"""
src/utils/file_handler.py
=========================
Modul utilitas untuk mengelola file JSON dan foto wisata.
Bertanggung jawab atas operasi baca/tulis data ke disk, serta
proses upload/download foto ke folder assets/uploads/.

Dependensi  : json, shutil, os, uuid, time, requests (untuk download URL)
Digunakan oleh : crud_engine.py, dashboard.py, detail_wisata.py
"""

import json
import shutil
import os
import uuid
import time

# Path absolut root proyek (2 level di atas file ini: utils/ → src/ → root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Cache in-memory untuk file JSON ─────────────────────────────────────────
# Agar tidak perlu membaca file dari disk setiap kali dipanggil
_json_cache = None        # Hasil baca JSON terakhir
_json_cache_time = 0      # Timestamp saat cache dibuat
_CACHE_TTL = 2            # Masa berlaku cache (dalam detik)


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI INTERNAL
# ─────────────────────────────────────────────────────────────────────────────

def _path_json():
    """
    Mengembalikan path absolut ke file data_wisata.json.

    I.S : PROJECT_ROOT sudah terdefinisi saat modul diimpor.
    F.S : Mengembalikan string path lengkap ke data/data_wisata.json.
    """
    return os.path.join(PROJECT_ROOT, "data", "data_wisata.json")


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI PUBLIK — BACA / TULIS JSON
# ─────────────────────────────────────────────────────────────────────────────

def buka_json(force_reload=False):
    """
    Membaca seluruh data wisata dari file data_wisata.json.
    Menggunakan cache in-memory agar tidak membaca disk berulang kali
    dalam waktu singkat (TTL = 2 detik).

    I.S : File data_wisata.json mungkin ada atau tidak ada di disk.
          Parameter force_reload menentukan apakah cache harus diabaikan.
    F.S : Mengembalikan list of dict berisi seluruh data wisata.
          Jika file tidak ditemukan, mengembalikan list kosong [].

    Param:
        force_reload (bool): Jika True, selalu baca dari disk meski cache masih valid.
    Return:
        list[dict]: Data wisata dari JSON, atau [] jika file tidak ada.
    """
    global _json_cache, _json_cache_time

    # Kembalikan cache jika masih valid dan tidak dipaksa reload
    if not force_reload and _json_cache is not None and (time.time() - _json_cache_time) < _CACHE_TTL:
        return _json_cache

    path = _path_json()

    # Jika file tidak ada, kembalikan list kosong
    if not os.path.exists(path):
        return []

    # Baca file dan simpan ke cache
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    _json_cache = data
    _json_cache_time = time.time()
    return data


def simpan_json(data):
    """
    Menyimpan seluruh data wisata ke file data_wisata.json.
    Setelah simpan, cache in-memory diperbarui agar konsisten.

    I.S : data adalah list of dict yang valid dan siap disimpan.
          Folder data/ belum tentu ada.
    F.S : File data_wisata.json diperbarui dengan data terbaru.
          Cache in-memory juga diperbarui sehingga buka_json()
          berikutnya tidak perlu membaca disk.

    Param:
        data (list[dict]): Seluruh data wisata yang akan disimpan.
    """
    global _json_cache, _json_cache_time

    path = _path_json()

    # Pastikan folder data/ sudah ada
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Tulis ke disk dengan format indented (mudah dibaca manusia)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Perbarui cache agar sinkron
    _json_cache = data
    _json_cache_time = time.time()


def tambah_data(data_baru):
    """
    Menambahkan satu entri data wisata baru ke dalam list JSON.

    I.S : data_baru adalah dict satu entri wisata yang sudah terbentuk.
          File JSON sudah ada dan dapat dibaca.
    F.S : Entri baru ditambahkan di akhir list dan file disimpan kembali.
          Mengembalikan True sebagai tanda keberhasilan.

    Param:
        data_baru (dict): Data satu destinasi wisata baru.
    Return:
        bool: True jika berhasil ditambahkan.
    """
    data = buka_json(force_reload=True)
    data.append(data_baru)
    simpan_json(data)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI PUBLIK — UPLOAD / DOWNLOAD FOTO
# ─────────────────────────────────────────────────────────────────────────────

def upload_foto_wisata(path_asal):
    """
    Menyimpan foto wisata ke folder assets/uploads/ dengan nama file unik (UUID).
    Mendukung dua sumber foto:
      1. File lokal  — path di komputer pengguna (contoh: C:/foto.jpg)
      2. URL internet — link gambar dari hasil scraping (contoh: https://...)

    I.S : path_asal berisi string path file lokal atau URL gambar.
          Bisa juga kosong/None jika tidak ada foto yang dipilih.
    F.S : Foto disalin/diunduh ke assets/uploads/<uuid>.<ekstensi>.
          Mengembalikan nama file unik (bukan path lengkap).
          Jika gagal (file tidak ada / URL error), mengembalikan "default.png".

    Param:
        path_asal (str): Path file lokal atau URL gambar.
    Return:
        str: Nama file foto hasil upload (misal: "a3f9c1b2.jpg"),
             atau "default.png" jika input kosong/gagal.
    """
    # Jika input kosong, gunakan gambar default
    if not path_asal:
        return "default.png"

    import requests
    import urllib.parse

    # Tentukan apakah input adalah URL atau path lokal
    is_url = path_asal.startswith('http')

    # Validasi: jika bukan URL dan file tidak ada di disk, kembalikan default
    if not is_url and not os.path.exists(path_asal):
        return "default.png"

    # Pastikan folder tujuan tersedia
    upload_dir = os.path.join(PROJECT_ROOT, "assets", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    if is_url:
        # ── MODE URL: Download dari internet lalu simpan ─────────────────
        try:
            parsed = urllib.parse.urlparse(path_asal)
            ekstensi = os.path.splitext(parsed.path)[1].lower()

            # Pastikan ekstensi valid; fallback ke .jpg jika tidak dikenali
            if ekstensi not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ekstensi = '.jpg'

            # Gunakan prefix foto_ dan ambil 8 karakter hex awal saja agar nama file tidak kepanjangan
            nama_unik = f"foto_{uuid.uuid4().hex[:8]}{ekstensi}"
            path_tujuan = os.path.join(upload_dir, nama_unik)

            # Download gambar dengan User-Agent browser lengkap agar tidak diblokir server
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
                'Referer': 'https://www.google.com/'
            }

            # Lakukan request download (dengan verify=False untuk menghindari kendala SSL lokal)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(path_asal, headers=headers, stream=True, timeout=15, verify=False)

            if response.status_code == 200:
                # Tulis isi response ke file secara streaming
                with open(path_tujuan, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                print(f"DEBUG: Berhasil download {path_asal} ke {nama_unik}")
                return nama_unik
            else:
                print(f"DEBUG: Gagal download ({response.status_code}) dari {path_asal}")
                return "default.png"

        except Exception as e:
            # Tangani semua error jaringan/file dengan fallback default
            print(f"DEBUG: Exception saat download {path_asal}: {str(e)}")
            return "default.png"

    else:
        # ── MODE FILE LOKAL: Salin file dari disk pengguna ───────────────
        ekstensi = os.path.splitext(path_asal)[1].lower()

        # Pastikan ekstensi valid
        if ekstensi not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ekstensi = '.png'

        nama_unik = f"{uuid.uuid4().hex}{ekstensi}"
        path_tujuan = os.path.join(upload_dir, nama_unik)

        # Salin file sambil mempertahankan metadata (waktu modifikasi, dll)
        shutil.copy2(path_asal, path_tujuan)
        return nama_unik


def simpan_gambar_ke_lokal(path_asal):
    """
    Menyimpan foto lokal ke folder assets/uploads/ dengan nama file unik.
    Berbeda dengan upload_foto_wisata, fungsi ini hanya menangani file lokal
    (tanpa dukungan URL). Digunakan oleh form multi-foto.

    I.S : path_asal berisi path file lokal yang valid.
    F.S : Foto disalin ke assets/uploads/<uuid>.<ekstensi>.
          Mengembalikan nama file unik, atau "default.png" jika gagal.

    Param:
        path_asal (str): Path file foto lokal.
    Return:
        str: Nama file hasil simpan.
    """
    if not path_asal or not os.path.exists(path_asal):
        return "default.png"

    upload_dir = os.path.join(PROJECT_ROOT, "assets", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    ekstensi = os.path.splitext(path_asal)[1].lower()
    if ekstensi not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        ekstensi = '.png'

    nama_unik = f"{uuid.uuid4().hex}{ekstensi}"
    path_tujuan = os.path.join(upload_dir, nama_unik)
    shutil.copy2(path_asal, path_tujuan)
    return nama_unik


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI PUBLIK — EXPORT DATA KE CSV
# ─────────────────────────────────────────────────────────────────────────────

def export_ke_csv(data_list, path_tujuan):
    """
    Mengekspor data wisata ke file CSV.

    I.S : data_list adalah list of dict data wisata.
          path_tujuan adalah path file CSV tujuan dari user.
    F.S : File CSV dibuat dengan kolom: Nama, Kategori, Kota, HTM, Rating, Kondisi Jalan.

    Param:
        data_list (list[dict]): Data wisata yang akan diekspor.
        path_tujuan (str): Path file CSV tujuan.
    Return:
        bool: True jika berhasil.
    """
    import csv
    with open(path_tujuan, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nama Wisata', 'Kategori', 'Kota/Kabupaten', 'HTM', 'Rating', 'Kondisi Jalan'])
        for item in data_list:
            idnt = item.get('identitas', {})
            oper = item.get('operasional', {})
            info = item.get('informasi_tambahan', {})

            nama = idnt.get('nama', '-')
            kategori = idnt.get('tipe', '-')
            parts = idnt.get('alamat', '-').split(',')
            kota = parts[-1].strip()
            if "Jawa Barat" in kota and len(parts) > 1:
                kota = parts[-2].strip()
            htm = oper.get('htm', '0')
            rating = idnt.get('rating', '0.0')
            kondisi = info.get('kondisi_jalan', '-')

            writer.writerow([nama, kategori, kota, htm, rating, kondisi])
    return True


# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI PUBLIK — LOG AKTIVITAS
# ─────────────────────────────────────────────────────────────────────────────

def _path_log():
    """Mengembalikan path absolut ke file log_aktivitas.json."""
    return os.path.join(PROJECT_ROOT, "data", "log_aktivitas.json")


def catat_log(aksi, nama_wisata):
    """
    Mencatat aktivitas (tambah/edit/hapus) ke file log JSON.

    I.S : aksi dan nama_wisata adalah string deskripsi aktivitas.
    F.S : Entri log baru ditambahkan ke data/log_aktivitas.json.

    Param:
        aksi (str): Jenis aksi (contoh: "Tambah", "Edit", "Hapus").
        nama_wisata (str): Nama wisata terkait.
    """
    import datetime
    path = _path_log()
    log_data = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except Exception:
            pass

    waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data.append({
        "waktu": waktu,
        "aksi": aksi,
        "nama_wisata": nama_wisata
    })

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4)


def export_log_ke_csv(path_tujuan):
    """
    Mengekspor riwayat log aktivitas ke file CSV.

    I.S : path_tujuan adalah path file CSV tujuan.
    F.S : File CSV dibuat dari data/log_aktivitas.json.

    Param:
        path_tujuan (str): Path file CSV tujuan.
    Return:
        bool: True jika berhasil, False jika log kosong/tidak ada.
    """
    import csv
    path = _path_log()
    if not os.path.exists(path):
        return False

    with open(path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)

    with open(path_tujuan, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Waktu', 'Aksi', 'Nama Wisata'])
        for item in log_data:
            writer.writerow([item.get('waktu'), item.get('aksi'), item.get('nama_wisata')])

    return True