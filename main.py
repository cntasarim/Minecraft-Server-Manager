# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from server_manager import ServerManager
from ftp_manager import FTPManager
from rcon_manager import RCONManager
from backup_manager import BackupManager
from file_manager import FileManager
from install_manager import InstallManager
from mysql_manager import MySQLManager
import os
import datetime

class MinecraftServerManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Server Manager")
        self.root.geometry("1000x900")
        self.root.resizable(False, False)
        self.setup_logging()
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_logging(self):
        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/log_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            encoding="utf-8"
        )

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        main_frame.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.log_area = tk.Text(main_frame, height=8)
        self.log_area.grid(row=1, column=0, sticky="ew")
        self.log_area.insert("1.0", "Program başlatıldı.\n")
        self.log_area.see("1.0")
        logging.info("Program başlatıldı.")

        self.server_tab = ServerManager(self.notebook, self)
        self.notebook.add(self.server_tab.frame, text="Sunucu Yönetimi")

        self.install_tab = InstallManager(self.notebook, self.log_area)
        self.notebook.add(self.install_tab.frame, text="Sunucuyu Yeniden Kur")

        self.ftp_tab = FTPManager(self.notebook, self.log_area)
        self.notebook.add(self.ftp_tab.frame, text="FTP Sunucusu")

        self.rcon_tab = RCONManager(self.notebook, self.log_area)
        self.notebook.add(self.rcon_tab.frame, text="RCON Konsolu")

        # BackupManager için app parametresi olarak self geçiriliyor
        self.backup_tab = BackupManager(self.notebook, self.log_area, self)
        self.notebook.add(self.backup_tab.frame, text="Yedekleme")

        self.file_tab = FileManager(self.notebook, self.log_area)
        self.notebook.add(self.file_tab.frame, text="Dosya Yöneticisi")

        self.mysql_tab = MySQLManager(self.notebook, self.log_area)
        self.notebook.add(self.mysql_tab.frame, text="MySQL Yönetim")

    def on_closing(self):
        if messagebox.askokcancel("Çıkış", "Programdan çıkmak istediğinize emin misiniz?"):
            try:
                self.ftp_tab.stop_ftp_server()
                self.log_area.insert("1.0", "FTP sunucusu durduruldu.\n")
                self.log_area.see("1.0")
                logging.info("FTP sunucusu durduruldu.")
            except AttributeError as e:
                self.log_area.insert("1.0", f"FTP durdurma hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"FTP durdurma hatası: {str(e)}")
            except Exception as e:
                self.log_area.insert("1.0", f"FTP durdurma hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"FTP durdurma hatası: {str(e)}")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MinecraftServerManager(root)
    root.mainloop()