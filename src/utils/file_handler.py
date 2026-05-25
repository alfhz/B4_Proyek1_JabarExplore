import json
import shutil
import os
import uuid
import time

# Path untuk mendapatkan root project (src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# In-memory cache untuk data JSON agar tidak sering baca disk
_json_cache = None        # Hasil baca JSON terakhir
_json_cache_time = 0      # Timestamp saat cache dibuat
_CACHE_TTL = 2            # Masa berlaku cache (dalam detik)

# untuk memudahkan import di crud_engine.py dan search_engine.py
def _path_json():
    return os.path.join(PROJECT_ROOT, "data", "data_wisata.json")


# function untuk membuka file json, dengan cache in-memory agar tidak sering baca disk
def buka_json(force_reload=False):
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

# function untuk menyimpan data ke file json, sekaligus memperbarui cache
def simpan_json(data):
    global _json_cache, _json_cache_time

    path = _path_json()

    # Pastikan folder data/ sudah ada
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Tulis ke disk dengan format indented
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Perbarui cache agar sinkron
    _json_cache = data
    _json_cache_time = time.time()


# function untuk menambahkan satu entri baru ke data JSON, digunakan oleh crud_engine.py
def tambah_data(data_baru):
    data = buka_json(force_reload=True)
    data.append(data_baru)
    simpan_json(data)
    return True

# function untuk menyimpan foto wisata ke folder assets/uploads/ dengan nama file unik (UUID).
def upload_foto_wisata(path_asal):
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
        ekstensi = os.path.splitext(path_asal)[1].lower()

        # Pastikan ekstensi valid
        if ekstensi not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ekstensi = '.png'

        nama_unik = f"{uuid.uuid4().hex}{ekstensi}"
        path_tujuan = os.path.join(upload_dir, nama_unik)

        # Salin file sambil mempertahankan metadata (waktu modifikasi, dll)
        shutil.copy2(path_asal, path_tujuan)
        return nama_unik


# Fungsi tambahan untuk menyimpan foto lokal (tanpa dukungan URL) ke folder uploads, digunakan oleh form multi-foto
def simpan_gambar_ke_lokal(path_asal):
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

# Fungsi untuk mengekspor data wisata ke file CSV, digunakan oleh fitur ekspor di daftar_wisata.py
def export_ke_csv(data_list, path_tujuan):
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


def _path_log():
    return os.path.join(PROJECT_ROOT, "data", "log_aktivitas.json")

# Fungsi untuk mencatat aktivitas (tambah/edit/hapus) ke file log JSON, digunakan oleh crud_engine.py
def catat_log(aksi, nama_wisata):
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

# Fungsi untuk mengekspor log aktivitas ke file CSV, digunakan oleh fitur ekspor log di daftar_wisata.py
def export_log_ke_csv(path_tujuan):
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