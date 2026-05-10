import json, shutil, os, uuid
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# utilitas internal untuk mendapatkan lokasi spesifik database json
def _path_json(): return os.path.join(PROJECT_ROOT, "data", "data_wisata.json")

# prosedur pembacaan dataset json dengan penanganan kondisi file tidak tersedia
def buka_json():
    p = _path_json()
    if not os.path.exists(p): return []
    with open(p, 'r', encoding='utf-8') as f: return json.load(f)
    
# prosedur persistensi data ke format json disertai pembuatan direktori otomatis
def simpan_json(d):
    p = _path_json(); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: json.dump(d, f, indent=4, ensure_ascii=False)
    
# prosedur duplikasi aset gambar ke direktori internal menggunakan identitas unik (uuid)
def simpan_gambar_ke_lokal(p_asal):
    if not os.path.exists(p_asal): return "default.png"
    u_dir = os.path.join(PROJECT_ROOT, "assets", "uploads"); os.makedirs(u_dir, exist_ok=True)
    n_unik = f"{uuid.uuid4().hex}{os.path.splitext(p_asal)[1].lower()}"
    shutil.copy2(p_asal, os.path.join(u_dir, n_unik)); return n_unik