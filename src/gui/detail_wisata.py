import customtkinter as ctk
from src.utils.validators import format_harga_idr

class DetailWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_kembali, data_wisata):
        super().__init__(parent, fg_color="transparent")
        self.callback_kembali = callback_kembali
        self.data_wisata = data_wisata
        self.pack(fill="both", expand=True, padx=30, pady=20)
        self.halaman_detail_wisata()

    def halaman_detail_wisata(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkButton(header, text="← Kembali", width=80, command=self.callback_kembali).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(header, text="Detail Wisata", font=("Arial", 28, "bold"), text_color="black").pack(side="left")

        kontainer = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        kontainer.pack(fill="both", expand=True, padx=5, pady=5)

        identitas = self.data_wisata.get('identitas', {})
        operasional = self.data_wisata.get('operasional', {})
        info_tambah = self.data_wisata.get('informasi_tambahan', {})

        # Data identitas
        self._buat_section(kontainer, "IDENTITAS WISATA")
        self._buat_baris(kontainer, "Nama", identitas.get('nama', '-'))
        self._buat_baris(kontainer, "Tipe", identitas.get('tipe', '-'))
        self._buat_baris(kontainer, "Alamat", identitas.get('alamat', '-'))
        self._buat_baris(kontainer, "Google Maps", identitas.get('maps', '-'), link=True)
        self._buat_baris(kontainer, "Rating", f"★ {identitas.get('rating', 0)}")
        self._buat_baris(kontainer, "Jumlah Ulasan", f"{identitas.get('jumlah_ulasan', 0)} ulasan")

        # Operasional
        self._buat_section(kontainer, "OPERASIONAL")
        htm = operasional.get('htm', 0)
        self._buat_baris(kontainer, "Harga Tiket", format_harga_idr(htm))
        hari_buka = ", ".join(operasional.get('hari_buka', []))
        self._buat_baris(kontainer, "Hari Buka", hari_buka if hari_buka else "-")
        jam = operasional.get('jam_operasional', {})
        jam_str = f"{jam.get('buka', '-')} - {jam.get('tutup', '-')}"
        self._buat_baris(kontainer, "Jam Operasional", jam_str)

        # Informasi tambahan
        self._buat_section(kontainer, "INFORMASI TAMBAHAN")
        self._buat_baris(kontainer, "Fasilitas", ", ".join(info_tambah.get('fasilitas', [])) or "-")
        self._buat_baris(kontainer, "Kondisi Jalan", info_tambah.get('kondisi_jalan', '-'))
        jarak = info_tambah.get('jarak_dari_kab_kota', '')
        self._buat_baris(kontainer, "Jarak dari Pusat Kota", f"{jarak} km" if jarak else "-")

    def _buat_section(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=("Arial", 14, "bold"),
                     text_color="#10B981").pack(anchor="w", padx=10, pady=(20, 5))
        ctk.CTkFrame(parent, height=2, fg_color="#F3F4F6").pack(fill="x", padx=10, pady=(0, 10))

    def _buat_baris(self, parent, label, value, link=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(frame, text=f"{label}:", font=("Arial", 12, "bold"),
                     width=140, anchor="w").pack(side="left")
        if link and value and value.startswith("http"):
            import webbrowser
            btn = ctk.CTkButton(frame, text="Buka Maps", fg_color="transparent",
                                text_color="#3B82F6", hover_color="#E5E7EB",
                                command=lambda: webbrowser.open(value))
            btn.pack(side="left")
        else:
            ctk.CTkLabel(frame, text=value, font=("Arial", 12), anchor="w").pack(side="left", fill="x", expand=True)