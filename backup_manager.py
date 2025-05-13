# backup_manager.py
import tkinter as tk
from tkinter import ttk
import os
import shutil
import datetime
import logging

class BackupManager:
    def __init__(self, parent, log_area, app):
        self.frame = ttk.Frame(parent)
        self.log_area = log_area
        self.app = app  # MinecraftServerManager nesnesi doğrudan geçiriliyor
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Yedek Adı:").pack(pady=5)
        self.backup_name = ttk.Entry(main_frame)
        self.backup_name.pack(pady=5)
        self.backup_name.insert(0, f"backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

        ttk.Button(main_frame, text="Yedek Al", command=self.take_backup).pack(pady=5)
        ttk.Button(main_frame, text="Yedek Geri Yükle", command=self.restore_backup).pack(pady=5)

        ttk.Label(main_frame, text="Yedekler:").pack(pady=5)
        self.backup_list = tk.Listbox(main_frame, width=50, height=10)
        self.backup_list.pack(pady=5)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.backup_list.yview)
        self.backup_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.refresh_backups()

    def refresh_backups(self):
        self.backup_list.delete(0, tk.END)
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        for file in os.listdir(backup_dir):
            if file.endswith(".zip"):
                self.backup_list.insert(tk.END, file)
        self.log_area.insert("1.0", "Yedek listesi yenilendi.\n")
        self.log_area.see("1.0")
        logging.info("Yedek listesi yenilendi.")

    def take_backup(self):
        backup_name = self.backup_name.get().strip()
        if not backup_name:
            self.log_area.insert("1.0", "Hata: Yedek adı boş olamaz.\n")
            self.log_area.see("1.0")
            logging.error("Yedek adı boş.")
            return
        if not backup_name.endswith(".zip"):
            backup_name += ".zip"

        server_dir = "servers/server1"
        backup_dir = "backups"
        backup_path = os.path.join(backup_dir, backup_name)

        if not os.path.exists(server_dir):
            self.log_area.insert("1.0", f"Hata: {server_dir} bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error(f"{server_dir} bulunamadı.")
            return

        # Sunucu durumunu kontrol et
        server_running = hasattr(self.app.server_tab, 'process') and self.app.server_tab.process and self.app.server_tab.process.poll() is None
        if server_running:
            self.log_area.insert("1.0", "Hata: Sunucu çalışırken yedek alınamaz. Lütfen sunucuyu durdurun.\n")
            self.log_area.see("1.0")
            logging.error("Sunucu çalışırken yedek alınamaz.")
            return

        try:
            os.makedirs(backup_dir, exist_ok=True)
            shutil.make_archive(backup_path.replace(".zip", ""), "zip", server_dir)
            self.refresh_backups()
            self.log_area.insert("1.0", f"Yedek oluşturuldu: {backup_name}\n")
            self.log_area.see("1.0")
            logging.info(f"Yedek oluşturuldu: {backup_name}")
        except Exception as e:
            self.log_area.insert("1.0", f"Yedek oluşturma hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Yedek oluşturma hatası: {str(e)}")

    def restore_backup(self):
        selection = self.backup_list.curselection()
        if not selection:
            self.log_area.insert("1.0", "Hata: Geri yüklenecek yedek seçilmedi.\n")
            self.log_area.see("1.0")
            logging.error("Geri yüklenecek yedek seçilmedi.")
            return

        backup_file = self.backup_list.get(selection[0])
        server_dir = "servers/server1"
        backup_path = os.path.join("backups", backup_file)

        # Sunucu durumunu kontrol et
        server_running = hasattr(self.app.server_tab, 'process') and self.app.server_tab.process and self.app.server_tab.process.poll() is None
        if server_running:
            self.log_area.insert("1.0", "Hata: Sunucu çalışırken yedek geri yüklenemez. Lütfen sunucuyu durdurun.\n")
            self.log_area.see("1.0")
            logging.error("Sunucu çalışırken yedek geri yüklenemez.")
            return

        if not os.path.exists(backup_path):
            self.log_area.insert("1.0", f"Hata: {backup_path} bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error(f"{backup_path} bulunamadı.")
            return

        try:
            if os.path.exists(server_dir):
                shutil.rmtree(server_dir)
            os.makedirs(server_dir, exist_ok=True)
            shutil.unpack_archive(backup_path, server_dir, "zip")
            self.log_area.insert("1.0", f"Yedek geri yüklendi: {backup_file}\n")
            self.log_area.see("1.0")
            logging.info(f"Yedek geri yüklendi: {backup_file}")
        except Exception as e:
            self.log_area.insert("1.0", f"Yedek geri yükleme hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Yedek geri yükleme hatası: {str(e)}")