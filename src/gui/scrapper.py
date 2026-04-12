import customtkinter as ctk
import threading
from tkinter import messagebox
from src.logic.scrap_logic import ScrapLogic

class ScrapperUI(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.scrap_logic = None
        self.tampilkan_ui()

    def tampilkan_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Scrapping Data Web", font=("Arial", 28, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(header, text="Ambil data wisata secara otomatis dari halaman web", font=("Arial", 14), text_color="#4B5563").pack(anchor="w", pady=(5,0))

        # Kontainer Utama
        main_container = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        main_container.pack(fill="both", expand=True, ipady=15, ipadx=15)

        # Form Input URL
        ctk.CTkLabel(main_container, text="Target URL:", font=("Arial", 14, "bold"), text_color="#374151").pack(anchor="w", padx=20, pady=(20, 5))
        self.url_input = ctk.CTkEntry(main_container, placeholder_text="Contoh: https://www.traveloka.com/id-id/explore/destination", height=40, font=("Arial", 13))
        self.url_input.pack(fill="x", padx=20)

        # Form Limit
        ctk.CTkLabel(main_container, text="Batas Jumlah Data:", font=("Arial", 14, "bold"), text_color="#374151").pack(anchor="w", padx=20, pady=(15, 5))
        self.limit_input = ctk.CTkEntry(main_container, placeholder_text="Contoh: 50", height=40, font=("Arial", 13))
        self.limit_input.insert(0, "50")
        self.limit_input.pack(fill="x", padx=20)

        # Tombol Aksi
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(20, 20))

        self.btn_mulai = ctk.CTkButton(btn_frame, text="▶ Mulai Scrapping", font=("Arial", 14, "bold"), height=45, fg_color="#10B981", hover_color="#059669", text_color="white", command=self.mulai_scraping)
        self.btn_mulai.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_berhenti = ctk.CTkButton(btn_frame, text="⏹ Hentikan", font=("Arial", 14, "bold"), height=45, fg_color="#EF4444", hover_color="#DC2626", text_color="white", command=self.hentikan_scraping, state="disabled")
        self.btn_berhenti.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Log Output Viewer
        ctk.CTkLabel(main_container, text="Log Proses:", font=("Arial", 14, "bold"), text_color="#374151").pack(anchor="w", padx=20, pady=(10, 5))
        self.log_textbox = ctk.CTkTextbox(main_container, height=200, font=("Consolas", 12), text_color="white", fg_color="#1F2937")
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def update_log(self, text):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_progress(self, saved, total):
        pass # Optional: update label if needed

    def mulai_scraping(self):
        url = self.url_input.get().strip()
        if not url:
            messagebox.showwarning("Peringatan", "URL tidak boleh kosong!")
            return

        limit_str = self.limit_input.get().strip()
        try:
            limit = int(limit_str)
        except ValueError:
            messagebox.showwarning("Peringatan", "Batas jumlah data harus berupa angka!")
            return

        # UI State update
        self.btn_mulai.configure(state="disabled", text="Sedang Berjalan...")
        self.btn_berhenti.configure(state="normal")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.url_input.configure(state="disabled")
        self.limit_input.configure(state="disabled")

        self.scrap_logic = ScrapLogic(log_callback=self.update_log, progress_callback=self.update_progress)

        # Run process in a separate thread to keep UI responsive
        def _run():
            try:
                hasil = self.scrap_logic.scrape(url, limit)
                self.update_log(f"\n[SELESAI] Data berhasil ditambahkan: {len(hasil)}")
                messagebox.showinfo("Beres", f"Selesai scrapping! {len(hasil)} data berhasil ditambahkan.")
            except Exception as e:
                self.update_log(f"\n[ERROR CRASH] {str(e)}")
                messagebox.showerror("Error", f"Terjadi kesalahan saat scrapping:\n{str(e)}")
            finally:
                self.btn_mulai.configure(state="normal", text="▶ Mulai Scrapping")
                self.btn_berhenti.configure(state="disabled")
                self.url_input.configure(state="normal")
                self.limit_input.configure(state="normal")

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()

    def hentikan_scraping(self):
        if self.scrap_logic:
            self.scrap_logic.stop()
            self.update_log("\n[INFO] Mengirim sinyal berhenti... harap tunggu...")
            self.btn_berhenti.configure(state="disabled")
