# filter_engine.py - Optimasi
"""
filter_engine.py
Fungsi untuk menyaring daftar destinasi berdasarkan berbagai kriteria.
Dioptimasi dengan list comprehension dan pre-komputasi.
"""
from typing import Optional, List, Dict

def filter_destinasi(
    data: List[Dict],
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    harga_max: Optional[int] = None,
    lokasi: Optional[str] = None,
) -> List[Dict]:
    """
    Memfilter daftar destinasi dengan performa tinggi.
    """
    if not data:
        return []
    
    # Jika tidak ada filter, kembalikan data asli
    if rating_min is None and rating_max is None and harga_max is None and lokasi is None:
        return data
    
    # Pre-komputasi nilai filter
    hasil = []
    lokasi_lower = lokasi.lower() if lokasi else None
    
    for item in data:
        identitas = item.get('identitas', {})
        operasional = item.get('operasional', {})
        
        # Ambil rating
        rating = identitas.get('rating', 0.0)
        if rating_min is not None and rating < rating_min:
            continue
        if rating_max is not None and rating > rating_max:
            continue
        
        # Ambil harga
        if harga_max is not None:
            htm_str = operasional.get('htm', '0')
            try:
                # Parse harga tanpa replace berulang
                harga = int(htm_str) if htm_str.isdigit() else int(''.join(filter(str.isdigit, str(htm_str))) or '0')
            except:
                harga = 0
            if harga > harga_max:
                continue
        
        # Filter lokasi
        if lokasi_lower:
            alamat = identitas.get('alamat', '')
            # Cek dengan cepat
            if lokasi_lower not in alamat.lower():
                continue
        
        hasil.append(item)
    
    return hasil