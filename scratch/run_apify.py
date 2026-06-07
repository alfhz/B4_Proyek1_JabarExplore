import sys
import os

# Menambahkan root project ke sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.logic.scrap_logic import ScrapLogic
from src.utils.file_handler import tambah_data
from src.logic.crud_engine import tambah_data_wisata

def main():
    print("=== Memulai Scraping APIFY via Script ===")
    url = "https://www.google.com/maps/search/wisata+alam+lembang"
    limit = 2
    
    scraper = ScrapLogic()
    print(f"Target URL: {url}")
    print(f"Limit: {limit}")
    
    # Memanggil method yang baru kita buat
    hasil = scraper.scrape(url, limit)
    
    if not hasil:
        print("Tidak ada data yang berhasil diekstrak.")
        return

    print(f"\nBerhasil mengekstrak {len(hasil)} data. Menyimpan ke database...")
    
    reviews_data = []
    disimpan = 0
    
    for item in hasil:
        try:
            if tambah_data_wisata is not None:
                idnt = item.get("identitas", {})
                oper = item.get("operasional", {})
                jam = oper.get("jam_operasional", {})
                info = item.get("informasi_tambahan", {})
                
                input_mentah = {
                    "nama": idnt.get("nama", ""), "rating": idnt.get("rating", 0), "alamat": idnt.get("alamat", ""),
                    "maps": idnt.get("maps", ""), "tipe": idnt.get("tipe", "Lainnya"), "htm": oper.get("htm", "0"),
                    "hari_buka": oper.get("hari_buka", []), "jam_mulai": jam.get("buka", "08:00"),
                    "jam_selesai": jam.get("tutup", "17:00"), "fasilitas": info.get("fasilitas", []),
                    "kondisi_jalan": info.get("kondisi_jalan", "-"), "jarak_dari_kab_kota": info.get("jarak_dari_kab_kota", "-"),
                    "jumlah_ulasan": idnt.get("jumlah_ulasan", 0),
                }
                tambah_data_wisata(input_mentah, idnt.get("foto", ""))
            else:
                tambah_data(item)
                idnt = item.get("identitas", {})

            revs = item.get("reviews", [])
            if revs:
                reviews_data.append({
                    "wisata": idnt.get("nama", "Unknown"),
                    "reviews": revs
                })
            print(f" - [OK] Disimpan: {idnt.get('nama')}")
            disimpan += 1
        except Exception as e:
            print(f" - [GAGAL] Menyimpan item: {e}")

    if reviews_data:
        import json
        reviews_path = os.path.join(_ROOT, 'data', 'data_reviews.json')
        existing_reviews = []
        if os.path.exists(reviews_path):
            try:
                with open(reviews_path, 'r', encoding='utf-8') as f:
                    existing_reviews = json.load(f)
            except Exception:
                pass
        existing_reviews.extend(reviews_data)
        try:
            with open(reviews_path, 'w', encoding='utf-8') as f:
                json.dump(existing_reviews, f, indent=4, ensure_ascii=False)
            print(" - [OK] Review tersimpan di data_reviews.json")
        except Exception as e:
            print(f"Gagal menyimpan reviews: {e}")

    print(f"\nSelesai! {disimpan} data berhasil dimasukkan ke database.")

if __name__ == '__main__':
    main()
