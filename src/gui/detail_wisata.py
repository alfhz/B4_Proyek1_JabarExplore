import customtkinter as ctk
import os
import webbrowser
from PIL import Image, ImageDraw

class DetailWisata(ctk.CTkFrame):
    def __init__(self, parent, callback_kembali, data_wisata, callback_edit=None):
        # frame utama halaman detail
        super().__init__(parent, fg_color="transparent")

        # callback kembali ke halaman sebelumnya
        self.callback_kembali = callback_kembali

        # callback ke halaman edit form
        self.callback_edit = callback_edit

        # data wisata yang dipilih dari daftar_wisata.py
        self.data_wisata = data_wisata

        # tampilkan frame
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # panggil halaman utama
        self.halaman_detail_wisata()

    def buat_foto_rounded(self, img, size, radius=16):
        # resize gambar ke ukuran yang diinginkan
        img = img.resize(size, Image.LANCZOS)
        img = img.convert("RGBA")

        # buat mask rounded rectangle (semua pojok: atas kiri, atas kanan, bawah kanan, bawah kiri)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)

        # terapkan mask ke gambar
        hasil = Image.new("RGBA", size, (0, 0, 0, 0))
        hasil.paste(img, mask=mask)
        return hasil

    def buat_foto_rounded_atas(self, img, size, radius=16):
        # rounded hanya pojok atas (untuk foto yang ada konten di bawahnya dalam card)
        img = img.resize(size, Image.LANCZOS)
        img = img.convert("RGBA")

        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        # gambar rounded rectangle penuh dulu
        draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
        # tutup pojok bawah dengan kotak penuh agar bawah tetap lurus
        draw.rectangle([0, size[1] - radius, size[0], size[1]], fill=255)

        hasil = Image.new("RGBA", size, (0, 0, 0, 0))
        hasil.paste(img, mask=mask)
        return hasil

    def buat_shadow_card(self, parent, pady=(0, 14), fg_color="white", corner_radius=14):
        # shadow efek di bagian bawah card
        # wrapper menampung shadow + card utama
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x", pady=pady)

        # frame shadow (abu-abu, offset ke bawah kanan)
        shadow = ctk.CTkFrame(
            wrapper,
            fg_color="#CBD5E1",
            corner_radius=corner_radius
        )
        shadow.place(relx=0, rely=0, relwidth=1, relheight=1, x=3, y=5)

        # card putih di atas shadow
        card = ctk.CTkFrame(
            wrapper,
            fg_color=fg_color,
            corner_radius=corner_radius
        )
        card.pack(fill="x")

        return wrapper, card

    def halaman_detail_wisata(self):
        identitas = self.data_wisata.get("identitas", {})
        operasional = self.data_wisata.get("operasional", {})
        tambahan = self.data_wisata.get("informasi_tambahan", {})

        # data identitas utama
        nama = identitas.get("nama", "-")
        alamat = identitas.get("alamat", "-")
        rating = identitas.get("rating", "0.0")
        maps = identitas.get("maps", "")
        tipe = identitas.get("tipe", "-")
        foto_raw = identitas.get("foto", "default.png")
        # foto bisa berupa list (format baru) atau string (format lama)
        foto = foto_raw[0] if isinstance(foto_raw, list) else foto_raw
        jumlah_ulasan = identitas.get("jumlah_ulasan", 0)
        deskripsi = identitas.get("deskripsi", f"{nama} merupakan destinasi wisata populer di Jawa Barat.")

        # data operasional
        htm = operasional.get("htm", "0")
        hari_buka = operasional.get("hari_buka", [])
        jam = operasional.get("jam_operasional", {})

        jam_buka = jam.get("buka", "-")
        jam_tutup = jam.get("tutup", "-")

        # data tambahan
        fasilitas = tambahan.get("fasilitas", [])
        kondisi_jalan = tambahan.get("kondisi_jalan", "-")
        jarak = tambahan.get("jarak_dari_kab_kota", "-")

        # ikon fasilitas
        ikon_fasilitas = {
            "Toilet": "🚻",
            "Parkir": "🅿",
            "Mushola": "🕌",
            "Warung": "🏪",
            "Gazebo": "⛺",
            "Camping Ground": "🏕",
            "Restoran": "🍽",
            "Kolam Renang": "🏊",
        }

        # header page - tombol kembali saja tanpa judul
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        # tombol kembali ke halaman daftar wisata - warna DEF4CA
        ctk.CTkButton(
            header,
            text="← Kembali",
            width=100,
            fg_color="#DEF4CA",
            text_color="#3A6B1A",
            hover_color="#c8ebb0",
            command=self.callback_kembali
        ).pack(side="left")

        # scrollable area utama
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ==================== HERO SECTION (dengan shadow) ====================
        # ambil gambar dari folder assets
        path_foto = os.path.join("assets/uploads", foto)

        # jika gambar tidak ada pakai placeholder
        if not os.path.exists(path_foto):
            path_foto = os.path.join("assets", "placeholder.png")

        _, hero = self.buat_shadow_card(scroll, pady=(0, 15), fg_color="white", corner_radius=14)

        try:
            img = Image.open(path_foto)

            # foto hero - rounded hanya pojok atas karena ada teks di bawahnya dalam card
            img_rounded_atas = self.buat_foto_rounded_atas(img, (1000, 260), radius=14)
            render = ctk.CTkImage(light_image=img_rounded_atas, size=(1000, 260))

            # tampilkan gambar utama tanpa padding agar mepet ke tepi card
            ctk.CTkLabel(hero, image=render, text="").pack(fill="x", padx=0, pady=0)

        except:
            # jika error tampilkan kotak kosong
            kotak = ctk.CTkFrame(hero, height=260, fg_color="#E5E7EB", corner_radius=0)
            kotak.pack(fill="x")

        # nama wisata di bawah gambar - font Courier Prime, warna #70A059
        ctk.CTkLabel(
            hero,
            text=nama,
            font=("Courier Prime", 28, "bold"),
            text_color="#70A059"
        ).pack(anchor="w", padx=20, pady=(15, 5))

        # badge tipe wisata di bawah nama (baris sendiri) - background #70A059
        ctk.CTkLabel(
            hero,
            text=f"  {tipe}  ",
            fg_color="#70A059",
            text_color="white",
            corner_radius=8,
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=20, pady=(0, 6))

        # bintang rating
        bintang_penuh = int(float(rating))
        bintang_str = "★" * bintang_penuh + "☆" * (5 - bintang_penuh)

        ctk.CTkLabel(
            hero,
            text=f"{bintang_str}  {rating}",
            text_color="#F59E0B",
            font=("Arial", 16)
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # ==================== BODY (kiri + kanan) ====================
        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="both", expand=True)

        kiri = ctk.CTkFrame(body, fg_color="transparent")
        kiri.pack(side="left", fill="both", expand=True, padx=(0, 10))

        kanan = ctk.CTkFrame(body, fg_color="transparent", width=320)
        kanan.pack(side="right", fill="y")
        kanan.pack_propagate(False)

        # ==================== KIRI: GALERI FOTO (dengan shadow) ====================
        _, galeri_frame = self.buat_shadow_card(kiri, pady=(0, 14), fg_color="white", corner_radius=14)

        ctk.CTkLabel(
            galeri_frame,
            text="Galeri Foto",
            font=("Chivo", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        grid_foto = ctk.CTkFrame(galeri_frame, fg_color="transparent")
        grid_foto.pack(fill="x", padx=15, pady=(0, 15))

        # tampilkan 4 foto dalam grid 2x2 (pakai foto yang sama) dengan semua pojok rounded
        try:
            img_kecil = Image.open(path_foto)
            for i in range(4):
                img_rounded_kecil = self.buat_foto_rounded(img_kecil, (330, 155), radius=12)
                render_kecil = ctk.CTkImage(light_image=img_rounded_kecil, size=(330, 155))
                baris = i // 2
                kolom = i % 2
                ctk.CTkLabel(
                    grid_foto,
                    image=render_kecil,
                    text="",
                    corner_radius=12
                ).grid(row=baris, column=kolom, padx=5, pady=5, sticky="nsew")
            grid_foto.columnconfigure(0, weight=1)
            grid_foto.columnconfigure(1, weight=1)
        except:
            ctk.CTkFrame(galeri_frame, height=160, fg_color="#E5E7EB").pack(fill="x", padx=15, pady=(0, 15))

        # ==================== KIRI: DESKRIPSI (dengan shadow) ====================
        self.card_section(kiri, "Deskripsi", deskripsi)

        # ==================== KIRI: FASILITAS (dengan shadow) ====================
        _, fasilitas_frame = self.buat_shadow_card(kiri, pady=(0, 14), fg_color="white", corner_radius=14)

        ctk.CTkLabel(
            fasilitas_frame,
            text="Fasilitas",
            font=("Chivo", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        badge_frame = ctk.CTkFrame(fasilitas_frame, fg_color="transparent")
        badge_frame.pack(fill="x", padx=15, pady=(0, 15))

        if fasilitas:
            for i, item in enumerate(fasilitas):
                ikon = ikon_fasilitas.get(item, "•")

                # kotak fasilitas warna DEF4CA
                badge = ctk.CTkFrame(badge_frame, fg_color="#DEF4CA", corner_radius=10)
                badge.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="ew")

                ctk.CTkLabel(
                    badge,
                    text=f"{ikon}\n{item}",
                    text_color="#3A6B1A",
                    font=("Gulzar", 11, "bold"),
                    justify="center"
                ).pack(padx=15, pady=10)

            for col in range(3):
                badge_frame.columnconfigure(col, weight=1)
        else:
            ctk.CTkLabel(badge_frame, text="-").pack(anchor="w")

        # ==================== KIRI: REVIEW PENGUNJUNG (dengan shadow) ====================
        _, review = self.buat_shadow_card(kiri, pady=(0, 14), fg_color="white", corner_radius=14)

        ctk.CTkLabel(
            review,
            text="Review Pengunjung",
            font=("Chivo", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        # contoh review sementara
        ulasan = self.data_wisata.get("ulasan", [
            {"nama": "Pengunjung A", "tanggal": "1 Januari 2026", "bintang": 5, "komentar": "Tempat wisata sangat bagus."},
            {"nama": "Pengunjung B", "tanggal": "2 Januari 2026", "bintang": 4, "komentar": "Cocok untuk liburan keluarga."},
        ])

        for ulasan_item in ulasan:
            item_frame = ctk.CTkFrame(review, fg_color="#F9FAFB", corner_radius=8)
            item_frame.pack(fill="x", padx=15, pady=(0, 8))

            nama_reviewer = ulasan_item.get("nama", "Anonim")
            tanggal_ulasan = ulasan_item.get("tanggal", "-")
            bintang_ulasan = ulasan_item.get("bintang", 5)
            komentar = ulasan_item.get("komentar", "")

            bintang_review_str = "★" * int(bintang_ulasan) + "☆" * (5 - int(bintang_ulasan))

            ctk.CTkLabel(
                item_frame,
                text=nama_reviewer,
                font=("Chivo", 13, "bold"),
                text_color="black"
            ).pack(anchor="w", padx=12, pady=(10, 2))

            info_row = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_row.pack(fill="x", padx=12)

            ctk.CTkLabel(
                info_row,
                text=bintang_review_str,
                text_color="#F59E0B",
                font=("Arial", 12)
            ).pack(side="left")

            ctk.CTkLabel(
                info_row,
                text=f"  {tanggal_ulasan}",
                text_color="#6B7280",
                font=("Gulzar", 11)
            ).pack(side="left")

            ctk.CTkLabel(
                item_frame,
                text=komentar,
                text_color="#374151",
                font=("Gulzar", 12)
            ).pack(anchor="w", padx=12, pady=(4, 10))

        # ==================== KANAN: ALAMAT + MAPS (dengan shadow) ====================
        _, alamat_frame = self.buat_shadow_card(kanan, pady=(0, 10), fg_color="white", corner_radius=14)

        alamat_row = ctk.CTkFrame(alamat_frame, fg_color="transparent")
        alamat_row.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            alamat_row,
            text="📍",
            font=("Arial", 16)
        ).pack(side="left")

        ctk.CTkLabel(
            alamat_row,
            text="Alamat",
            font=("Chivo", 13, "bold"),
            text_color="black"
        ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            alamat_frame,
            text=alamat,
            text_color="#374151",
            wraplength=270,
            justify="left",
            font=("Gulzar", 12)
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # tombol buka google maps
        ctk.CTkButton(
            alamat_frame,
            text="↗  Buka Google Maps",
            fg_color="#3A8C11",
            hover_color="#2d6e0d",
            command=lambda: self.buka_maps(maps)
        ).pack(fill="x", padx=10, pady=(0, 10))

        # ==================== KANAN: JAM OPERASIONAL (dengan shadow) ====================
        self.info_card_ikon(kanan, "🕐", "Jam Operasional", f"{jam_buka} - {jam_tutup}")

        # ==================== KANAN: HARGA TIKET (dengan shadow) ====================
        htm_text = f"Rp {int(htm):,}".replace(",", ".") if htm and htm != "0" else "Gratis"
        self.info_card_ikon(kanan, "🎫", "Harga Tiket", htm_text)

        # ==================== KANAN: KATEGORI (dengan shadow) ====================
        self.info_card_ikon(kanan, "🏷", "Kategori", tipe)

        # ==================== KANAN: RATING (dengan shadow) ====================
        _, rating_frame = self.buat_shadow_card(kanan, pady=(0, 10), fg_color="#F0FDF4", corner_radius=14)

        rating_row = ctk.CTkFrame(rating_frame, fg_color="transparent")
        rating_row.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            rating_row,
            text="⭐",
            font=("Arial", 16)
        ).pack(side="left")

        ctk.CTkLabel(
            rating_row,
            text="Rating",
            font=("Chivo", 13, "bold"),
            text_color="black"
        ).pack(side="left", padx=(6, 0))

        rating_detail_row = ctk.CTkFrame(rating_frame, fg_color="transparent")
        rating_detail_row.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            rating_detail_row,
            text=str(rating),
            font=("Chivo", 28, "bold"),
            text_color="black"
        ).pack(side="left")

        rating_kanan = ctk.CTkFrame(rating_detail_row, fg_color="transparent")
        rating_kanan.pack(side="left", padx=(8, 0))

        bintang_penuh_r = int(float(rating))
        bintang_str_r = "★" * bintang_penuh_r + "☆" * (5 - bintang_penuh_r)

        ctk.CTkLabel(
            rating_kanan,
            text=bintang_str_r,
            text_color="#F59E0B",
            font=("Arial", 13)
        ).pack(anchor="w")

        ctk.CTkLabel(
            rating_kanan,
            text=f"{jumlah_ulasan} reviews",
            text_color="#6B7280",
            font=("Gulzar", 11)
        ).pack(anchor="w")

        # ==================== KANAN: KONDISI AKSES JALAN (dengan shadow) ====================
        _, jalan_frame = self.buat_shadow_card(kanan, pady=(0, 10), fg_color="white", corner_radius=14)

        ctk.CTkLabel(
            jalan_frame,
            text="Kondisi Akses Jalan",
            font=("Chivo", 13, "bold"),
            text_color="black"
        ).pack(anchor="w", padx=12, pady=(12, 6))

        jalan_isi = ctk.CTkFrame(jalan_frame, fg_color="#F0FDF4", corner_radius=8)
        jalan_isi.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            jalan_isi,
            text=kondisi_jalan,
            text_color="#374151",
            wraplength=260,
            justify="left",
            font=("Gulzar", 12)
        ).pack(anchor="w", padx=10, pady=10)

    # card kiri (dengan shadow)
    def card_section(self, parent, title, isi):

        # card putih isi informasi
        _, frame = self.buat_shadow_card(parent, pady=(0, 14), fg_color="white", corner_radius=14)

        # judul card - font Chivo
        ctk.CTkLabel(
            frame,
            text=title,
            font=("Chivo", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 8))

        # isi card - font Gulzar
        ctk.CTkLabel(
            frame,
            text=isi,
            wraplength=650,
            justify="left",
            font=("Gulzar", 12)
        ).pack(anchor="w", padx=15, pady=(0, 15))

    # card kanan
    def info_card(self, parent, title, isi):

        # card info sidebar kanan (dengan shadow)
        _, frame = self.buat_shadow_card(parent, pady=(0, 10), fg_color="white", corner_radius=14)

        ctk.CTkLabel(
            frame,
            text=title,
            font=("Chivo", 12, "bold")
        ).pack(anchor="w", padx=12, pady=(10, 3))

        ctk.CTkLabel(
            frame,
            text=isi,
            font=("Gulzar", 12)
        ).pack(anchor="w", padx=12, pady=(0, 10))

    # card kanan dengan ikon
    def info_card_ikon(self, parent, ikon, title, isi):

        # card dengan shadow
        _, frame = self.buat_shadow_card(parent, pady=(0, 10), fg_color="white", corner_radius=14)

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(10, 3))

        ctk.CTkLabel(
            row,
            text=ikon,
            font=("Arial", 16)
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=title,
            font=("Chivo", 13, "bold"),
            text_color="black"
        ).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            frame,
            text=isi,
            text_color="#374151",
            font=("Gulzar", 12)
        ).pack(anchor="w", padx=12, pady=(0, 10))

    # buka link google maps
    def buka_maps(self, link):
        if link:
            webbrowser.open(link)

    # pindah ke halaman edit
    def proses_edit(self):
        if self.callback_edit:
            self.callback_edit("Edit", self.data_wisata)