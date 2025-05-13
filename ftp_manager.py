# ftp_manager.py
import tkinter as tk
from tkinter import ttk
import os
import threading
import logging
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

class FTPManager:
    def __init__(self, parent, log_area):
        self.frame = ttk.Frame(parent)
        self.log_area = log_area
        self.ftp_server = None
        self.ftp_thread = None
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="FTP Sunucu Durumu:").pack(pady=5)
        self.status_label = ttk.Label(main_frame, text="FTP Sunucusu durduruldu")
        self.status_label.pack(pady=5)

        ttk.Label(main_frame, text="FTP Kullanıcı Adı:").pack(pady=5)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.insert(0, "admin")
        self.username_entry.pack(pady=5)

        ttk.Label(main_frame, text="FTP Şifresi:").pack(pady=5)
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.insert(0, "password")
        self.password_entry.pack(pady=5)

        ttk.Label(main_frame, text="FTP Portu:").pack(pady=5)
        self.port_entry = ttk.Entry(main_frame)
        self.port_entry.insert(0, "21")
        self.port_entry.pack(pady=5)

        ttk.Button(main_frame, text="FTP Sunucusunu Başlat", command=self.start_ftp_server).pack(pady=5)
        ttk.Button(main_frame, text="FTP Sunucusunu Durdur", command=self.stop_ftp_server).pack(pady=5)

    def start_ftp_server(self):
        if self.ftp_server:
            self.log_area.insert(tk.END, "Hata: FTP sunucusu zaten çalışıyor.\n")
            logging.error("FTP sunucusu zaten çalışıyor.")
            return

        username = self.username_entry.get()
        password = self.password_entry.get()
        port = self.port_entry.get()
        ftp_dir = os.path.abspath("servers")

        try:
            port = int(port)
        except ValueError:
            self.log_area.insert(tk.END, "Hata: Port sayı olmalı.\n")
            logging.error("Port sayı olmalı.")
            return

        os.makedirs(ftp_dir, exist_ok=True)

        authorizer = DummyAuthorizer()
        authorizer.add_user(username, password, ftp_dir, perm="elradfmw")

        handler = FTPHandler
        handler.authorizer = authorizer

        try:
            self.ftp_server = FTPServer(("0.0.0.0", port), handler)
            self.ftp_thread = threading.Thread(target=self.ftp_server.serve_forever)
            self.ftp_thread.daemon = True
            self.ftp_thread.start()
            self.status_label["text"] = f"FTP Sunucusu çalışıyor (Port: {port})"
            self.log_area.insert(tk.END, f"FTP sunucusu başlatıldı: {username}@{port}\n")
            logging.info(f"FTP sunucusu başlatıldı: {username}@{port}")
        except Exception as e:
            self.log_area.insert(tk.END, f"FTP başlatma hatası: {str(e)}\n")
            logging.error(f"FTP başlatma hatası: {str(e)}")
            self.ftp_server = None

    def stop_ftp_server(self):
        if self.ftp_server:
            try:
                self.ftp_server.close_all()
                self.ftp_thread.join(timeout=5)
                self.ftp_server = None
                self.ftp_thread = None
                self.status_label["text"] = "FTP Sunucusu durduruldu"
                self.log_area.insert(tk.END, "FTP sunucusu durduruldu.\n")
                logging.info("FTP sunucusu durduruldu.")
            except Exception as e:
                self.log_area.insert(tk.END, f"FTP durdurma hatası: {str(e)}\n")
                logging.error(f"FTP durdurma hatası: {str(e)}")
        else:
            self.log_area.insert(tk.END, "Hata: FTP sunucusu zaten durdurulmuş.\n")
            logging.info("FTP sunucusu zaten durdurulmuş.")