# src/logic/filter_engine.py
from typing import Optional, List, Dict

def filter_destinasi(
    data: List[Dict],
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    harga_max: Optional[int] = None,
    lokasi: Optional[str] = None,
) -> List[Dict]:
    hasil = []
    for item in data:
        identitas = item.get('identitas', {})
        operasional = item.get('operasional', {})
        rating = identitas.get('rating', 0.0)
        htm_str = operasional.get('htm', '0')
        try:
            harga = int(str(htm_str).replace('.', '').replace(',', ''))
        except:
            harga = 0
        alamat = identitas.get('alamat', '')
        kota = alamat.split(',')[0].strip() if ',' in alamat else alamat.strip()

        if rating_min is not None and rating < rating_min:
            continue
        if rating_max is not None and rating > rating_max:
            continue
        if harga_max is not None and harga > harga_max:
            continue
        if lokasi and lokasi.lower() not in kota.lower():
            continue
        hasil.append(item)
    return hasil