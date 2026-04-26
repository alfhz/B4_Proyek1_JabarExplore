import customtkinter as ctk
import os
from PIL import Image
import threading
import pandas as pd
from tkinter import messagebox
try:
    from src.logic.apify_base import ApifyBase
except ImportError:
    ApifyBase = None

class DetailWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_kembali, data_wisata):
        super().__init__(parent, fg_color="transparent")
        self.callback_kembali = callback_kembali
        self.data_wisata = data_wisata
        
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.init_ui()

    def init_ui(self):
        # Header + Tombol Kembali
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        btn_kembali = ctk.CTkButton(header_frame, text="← Kembali", width=80, fg_color="#E5E7EB", text_color="black", hover_color="#D1D5DB", command=self.callback_kembali)
        btn_kembali.pack(side="left")
        
        identitas = self.data_wisata.get('identitas', {})
        nama = identitas.get('nama', 'Detail Wisata')
        
        ctk.CTkLabel(header_frame, text=nama, font=("Arial", 22, "bold"), text_color="black").pack(side="left", padx=20)

        # Main Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        self.scroll_frame.pack(fill="both", expand=True, ipady=15, ipadx=15)

        # Info Wisata
        info_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=10, padx=10)
        
        # Ekstrak data
        alamat = identitas.get('alamat', '-')
        rating = identitas.get('rating', '0.0')
        tipe = identitas.get('tipe', '-')
        
        operasional = self.data_wisata.get('operasional', {})
        jam_buka = operasional.get('jam_buka', '-')
        
        informasi_tambahan = self.data_wisata.get('informasi_tambahan', {})
        fasilitas = informasi_tambahan.get('fasilitas', '-')
        
        # Render Teks Detail
        details = [
            ("Kategori", tipe),
            ("Rating", f"⭐ {rating}"),
            ("Alamat", alamat),
            ("Jam Buka", jam_buka),
            ("Fasilitas / Deskripsi", fasilitas)
        ]
        
        for label, val in details:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=f"{label}:", font=("Arial", 12, "bold"), width=150, anchor="w", text_color="#374151").pack(side="left")
            ctk.CTkLabel(row, text=val, font=("Arial", 12), text_color="#4B5563", wraplength=700, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(self.scroll_frame, height=2, fg_color="#E5E7EB").pack(fill="x", pady=20, padx=10)

        # Bagian Rekomendasi Hotel
        hotel_header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        hotel_header.pack(fill="x", padx=10)
        ctk.CTkLabel(hotel_header, text="Rekomendasi Penginapan Sekitar", font=("Arial", 18, "bold"), text_color="black").pack(side="left")
        
        self.btn_cari_hotel = ctk.CTkButton(hotel_header, text="🔍 Cari Hotel Terdekat", fg_color="#3B82F6", hover_color="#2563EB", command=self.cari_hotel_api)
        self.btn_cari_hotel.pack(side="right")

        self.hotel_container = ctk.CTkFrame(self.scroll_frame, fg_color="#F9FAFB", corner_radius=8)
        self.hotel_container.pack(fill="both", expand=True, pady=15, padx=10)
        
        # Cek apakah hotel sudah tersimpan di data terpisah (data_hotel.json)
        from src.utils.file_handler import buka_json_hotel
        semua_hotel = buka_json_hotel()
        wisata_id = str(self.data_wisata.get('id'))
        
        relasi_hotel = [h['hotel_data'] for h in semua_hotel if str(h.get('wisata_id')) == wisata_id]
        
        if relasi_hotel:
            self.status_hotel = ctk.CTkLabel(self.hotel_container, text="")
            self.tampilkan_hasil_hotel(relasi_hotel, is_dataframe=False)
        else:
            self.status_hotel = ctk.CTkLabel(self.hotel_container, text="Data belum tersedia. Klik 'Cari Hotel Terdekat' untuk load otomatis.", text_color="#6B7280", pady=30)
            self.status_hotel.pack(expand=True)

    def cari_hotel_api(self):
        if ApifyBase is None:
            messagebox.showerror("Error", "Modul Apify tidak ditemukan.")
            return
            
        self.btn_cari_hotel.configure(state="disabled", text="Memuat API...")
        self.status_hotel.configure(text="Sedang mencari data penginapan di area tersebut... (Mohon tunggu)")

        def _run_fetch():
            try:
                scraper = ApifyBase()
                # Default max=3 hotel
                nama_wisata = self.data_wisata.get('identitas', {}).get('nama', '')
                payload = {
                    "searchStringsArray": [f"Penginapan hotel dekat {nama_wisata}"],
                    "language": "id",
                    "countryCode": "id",
                    "maxCrawledPlacesPerSearch": 3
                }
                df = scraper.run_actor(payload, f"(Mencari hotel sekitar {nama_wisata})")
                
                # Update UI
                self.after(0, self.tampilkan_hasil_hotel, df)
            except Exception as e:
                self.after(0, self.gagal_fetch, str(e))

        threading.Thread(target=_run_fetch, daemon=True).start()

    def gagal_fetch(self, error_msg):
        self.btn_cari_hotel.configure(state="normal", text="🔍 Coba Lagi")
        self.status_hotel.configure(text=f"Gagal mencari hotel:\n{error_msg}")

    def tampilkan_hasil_hotel(self, data_source, is_dataframe=True):
        self.btn_cari_hotel.configure(state="normal", text="🔍 Perbarui Pencarian")
        
        for widget in self.hotel_container.winfo_children():
            widget.destroy()

        # Konversi dataframe ke list dictionary jika asalnya dari tarikan API live
        if is_dataframe:
            if data_source is None or data_source.empty:
                ctk.CTkLabel(self.hotel_container, text="Tidak ada penginapan ditemukan di sekitar lokasi ini.", text_color="#6B7280", pady=20).pack()
                return
                
            hotel_list = []
            for _, row in data_source.iterrows():
                hotel_list.append({
                    "title": str(row.get('title', 'Hotel Tanpa Nama')),
                    "address": str(row.get('address', 'Alamat tidak tersedia')),
                    "score": str(row.get('totalScore', '0.0')),
                    "phone": str(row.get('phone', 'Tidak tersedia')),
                    "website": str(row.get('website', 'Tidak tersedia'))
                })
                
            # Simpan secara permanen ke file json hotel terpisah
            from src.utils.file_handler import buka_json_hotel, simpan_json_hotel
            semua_hotel = buka_json_hotel()
            wisata_id = str(self.data_wisata.get('id'))
            
            # Hapus data lama yang bereferensi sama jika ada
            semua_hotel = [h for h in semua_hotel if str(h.get('wisata_id')) != wisata_id]
            
            for hl in hotel_list:
                semua_hotel.append({
                    "wisata_id": wisata_id,
                    "hotel_data": hl
                })
                
            simpan_json_hotel(semua_hotel)
        else:
            hotel_list = data_source

        # Render kartu 
        for item in hotel_list:
            card = ctk.CTkFrame(self.hotel_container, fg_color="white", corner_radius=8, border_width=1, border_color="#E5E7EB")
            card.pack(fill="x", pady=8, padx=10, ipady=10, ipadx=15)
            
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x")
            
            ctk.CTkLabel(top_frame, text=item['title'], font=("Arial", 14, "bold"), text_color="#1F2937", anchor="w").pack(side="left")
            
            import tkinter.messagebox as mb
            def show_hotel(hx=item):
                msg = f"Nama: {hx.get('title', '-')}\n"
                msg += f"Rating: {hx.get('score', '-')}\n\n"
                msg += f"Alamat: {hx.get('address', '-')}\n"
                msg += f"Telepon: {hx.get('phone', 'Tidak tersedia')}\n"
                msg += f"Website: {hx.get('website', 'Tidak tersedia')}\n"
                mb.showinfo(f"Info {hx.get('title', 'Hotel')}", msg)

            ctk.CTkButton(top_frame, text="🔍 Detail", width=60, height=24, fg_color="#E5E7EB", hover_color="#D1D5DB", text_color="#374151", command=lambda x=item: show_hotel(x)).pack(side="right")
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(fill="x", pady=(5, 0))
            
            ctk.CTkLabel(info_frame, text=f"⭐ {item['score']}", font=("Arial", 12, "bold"), text_color="#F59E0B").pack(side="left", padx=(0, 15))
            ctk.CTkLabel(info_frame, text=item['address'], font=("Arial", 12), text_color="#6B7280").pack(side="left")
