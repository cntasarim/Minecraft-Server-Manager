# rcon_manager.py
import tkinter as tk
from tkinter import ttk
import logging

class RCONManager:
    def __init__(self, parent, log_area):
        self.frame = ttk.Frame(parent)
        self.log_area = log_area
        self.setup_ui()

    def setup_ui(self):
        # Sol ve Sağ Sütunlar
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sol Sütun
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="n", padx=5)

        # RCON Bilgileri
        ttk.Label(left_frame, text="RCON Şifre:").pack(pady=5)
        self.rcon_pass = ttk.Entry(left_frame, show="*")
        self.rcon_pass.insert(0, "rconpassword")
        self.rcon_pass.pack(pady=5)

        ttk.Label(left_frame, text="RCON Port:").pack(pady=5)
        self.rcon_port = ttk.Entry(left_frame)
        self.rcon_port.insert(0, "25575")
        self.rcon_port.pack(pady=5)

        # RCON Butonları
        ttk.Button(left_frame, text="Şifre Ayarla", command=self.set_rcon_password).pack(pady=5)
        ttk.Button(left_frame, text="Test Et", command=self.test_rcon).pack(pady=5)

        # Sağ Sütun
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="n", padx=5)

        # Server Logları
        ttk.Label(right_frame, text="Server Logları:").pack(pady=5)
        self.server_log = tk.Text(right_frame, height=10, width=30)
        self.server_log.pack(pady=5)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.server_log.yview)
        self.server_log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def set_rcon_password(self):
        password = self.rcon_pass.get()
        self.log_area.insert(tk.END, f"RCON şifresi ayarlandı: {password}\n")
        logging.info(f"RCON şifresi ayarlandı: {password}")
        self.server_log.insert(tk.END, f"RCON şifresi ayarlandı: {password}\n")

    def test_rcon(self):
        port = self.rcon_port.get()
        self.log_area.insert(tk.END, f"RCON testi yapıldı: Port {port}\n")
        logging.info(f"RCON testi yapıldı: Port {port}")
        self.server_log.insert(tk.END, f"RCON testi yapıldı: Port {port}\n")