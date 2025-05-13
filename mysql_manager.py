# mysql_manager.py
import tkinter as tk
from tkinter import ttk
import os
import subprocess
import requests
import zipfile
import shutil
import logging
import mysql.connector
from mysql.connector import Error
import socket
import psutil
import time
import glob

class MySQLManager:
    def __init__(self, parent, log_area):
        self.frame = ttk.Frame(parent)
        self.log_area = log_area
        self.mysql_installed = False
        self.connection = None
        self.mysql_dir = "mysql"
        self.mysql_port = "3306"
        self.mysql_host = "localhost"
        self.mysql_user = "root"
        self.mysql_password = ""
        self.setup_ui()
        self.check_mysql()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="n", padx=5)

        ttk.Label(left_frame, text="MySQL Durumu:").pack(pady=5)
        self.status_label = ttk.Label(left_frame, text="Kontrol ediliyor...")
        self.status_label.pack(pady=5)

        ttk.Button(left_frame, text="MySQL Başlat", command=self.start_mysql).pack(pady=5)
        ttk.Label(left_frame, text="Yeni Veritabanı Adı:").pack(pady=5)
        self.db_name_entry = ttk.Entry(left_frame)
        self.db_name_entry.pack(pady=5)
        ttk.Button(left_frame, text="Veritabanı Oluştur", command=self.create_database).pack(pady=5)

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="n", padx=5)

        ttk.Label(right_frame, text="Bağlantı Bilgileri:").pack(pady=5)
        conn_frame = ttk.Frame(right_frame)
        conn_frame.pack(pady=5)

        ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, sticky="e", padx=5)
        self.host_entry = ttk.Entry(conn_frame, width=20)
        self.host_entry.insert(0, self.mysql_host)
        self.host_entry.grid(row=0, column=1, pady=2)

        ttk.Label(conn_frame, text="Kullanıcı:").grid(row=1, column=0, sticky="e", padx=5)
        self.user_entry = ttk.Entry(conn_frame, width=20)
        self.user_entry.insert(0, self.mysql_user)
        self.user_entry.grid(row=1, column=1, pady=2)

        ttk.Label(conn_frame, text="Şifre:").grid(row=2, column=0, sticky="e", padx=5)
        self.pass_entry = ttk.Entry(conn_frame, width=20, show="*")
        self.pass_entry.insert(0, self.mysql_password)
        self.pass_entry.grid(row=2, column=1, pady=2)

        ttk.Label(conn_frame, text="Port:").grid(row=3, column=0, sticky="e", padx=5)
        self.port_entry = ttk.Entry(conn_frame, width=20)
        self.port_entry.insert(0, self.mysql_port)
        self.port_entry.grid(row=3, column=1, pady=2)

        ttk.Button(right_frame, text="Bağlantıyı Test Et", command=self.test_connection).pack(pady=5)

        ttk.Label(right_frame, text="Veritabanları:").pack(pady=5)
        self.db_list = tk.Listbox(right_frame, height=8, width=30)
        self.db_list.pack(pady=5)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.db_list.yview)
        self.db_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.progress = ttk.Progressbar(self.frame, length=200, mode="determinate")
        self.progress.pack(pady=5)

    def check_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def is_mysql_running(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == "mysqld.exe":
                return True
        return False

    def check_port(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('127.0.0.1', int(port))) == 0
        except Exception as e:
            self.log_area.insert("1.0", f"Port kontrol hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Port kontrol hatası: {str(e)}")
            return False

    def create_my_ini(self):
        my_ini_path = os.path.normpath(os.path.join(self.mysql_dir, "my.ini"))
        data_dir = os.path.normpath(os.path.join(self.mysql_dir, "data"))
        os.makedirs(data_dir, exist_ok=True)
        my_ini = f"""
[mysqld]
basedir="{os.path.abspath(self.mysql_dir).replace('\\', '/')}"
datadir="{os.path.abspath(data_dir).replace('\\', '/')}"
port={self.mysql_port}
bind-address=127.0.0.1
"""
        try:
            with open(my_ini_path, "w", encoding="utf-8") as f:
                f.write(my_ini)
            self.log_area.insert("1.0", f"my.ini oluşturuldu: {my_ini_path}\n")
            self.log_area.see("1.0")
            logging.info(f"my.ini oluşturuldu: {my_ini_path}")
        except Exception as e:
            self.log_area.insert("1.0", f"my.ini oluşturma hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"my.ini oluşturma hatası: {str(e)}")

    def check_mysql(self):
        my_ini_path = os.path.normpath(os.path.join(self.mysql_dir, "my.ini"))
        data_dir = os.path.normpath(os.path.join(self.mysql_dir, "data"))
        if os.path.exists(self.mysql_dir):
            self.mysql_installed = True
            self.status_label["text"] = "MySQL dizinde kurulu."
            self.log_area.insert("1.0", "MySQL dizinde kurulu.\n")
            self.log_area.see("1.0")
            logging.info("MySQL dizinde kurulu.")
            if not os.path.exists(my_ini_path):
                self.create_my_ini()
            if not os.path.exists(data_dir) or not os.listdir(data_dir):
                try:
                    mysql_bin = os.path.normpath(os.path.join(self.mysql_dir, "bin", "mysqld.exe"))
                    process = subprocess.Popen(
                        [mysql_bin, "--initialize-insecure"],
                        cwd=os.path.join(self.mysql_dir, "bin"),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=60)
                    if process.returncode != 0:
                        self.log_area.insert("1.0", f"MySQL ilklendirme hatası: {stderr}\n")
                        self.log_area.see("1.0")
                        logging.error(f"MySQL ilklendirme hatası: {stderr}")
                        self.log_area.insert("1.0", "Manuel ilklendirme talimatı: Komut isteminde şu komutu çalıştırın:\n")
                        self.log_area.insert("1.0", f'cd {self.mysql_dir}\\bin && mysqld --initialize-insecure\n')
                        self.log_area.see("1.0")
                        return
                    self.log_area.insert("1.0", "MySQL veri dizini ilklendirildi.\n")
                    self.log_area.see("1.0")
                    logging.info("MySQL veri dizini ilklendirildi.")
                except Exception as e:
                    self.log_area.insert("1.0", f"MySQL ilklendirme hatası: {str(e)}\n")
                    self.log_area.see("1.0")
                    logging.error(f"MySQL ilklendirme hatası: {str(e)}")
                    self.log_area.insert("1.0", "Manuel ilklendirme talimatı: Komut isteminde şu komutu çalıştırın:\n")
                    self.log_area.insert("1.0", f'cd {self.mysql_dir}\\bin && mysqld --initialize-insecure\n')
                    self.log_area.see("1.0")
                    return
        else:
            self.mysql_installed = False
            self.status_label["text"] = "MySQL bulunamadı, kurulum gerekiyor."
            self.log_area.insert("1.0", "MySQL bulunamadı, kurulum başlatılıyor...\n")
            self.log_area.see("1.0")
            logging.info("MySQL bulunamadı, kurulum başlatılıyor.")
            self.install_mysql()

    def install_mysql(self):
        self.progress["value"] = 0
        self.frame.update()

        if not self.check_internet():
            self.status_label["text"] = "İnternet bağlantısı yok."
            self.log_area.insert("1.0", "Hata: İnternet bağlantısı yok, MySQL indirilemedi.\n")
            self.log_area.see("1.0")
            logging.error("İnternet bağlantısı yok.")
            return

        try:
            mysql_zip_url = "https://downloads.mysql.com/archives/get/p/23/file/mysql-8.0.34-winx64.zip"
            zip_path = "mysql.zip"
            self.log_area.insert("1.0", "Portable MySQL indiriliyor...\n")
            self.log_area.see("1.0")
            response = requests.get(mysql_zip_url, timeout=10)
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(response.content)
            self.progress["value"] = 30
            self.frame.update()

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall("temp_mysql")
            os.remove(zip_path)
            self.progress["value"] = 50
            self.frame.update()

            temp_dir = os.path.normpath(os.path.join("temp_mysql", "mysql-8.0.34-winx64"))
            if os.path.exists(temp_dir):
                shutil.move(temp_dir, self.mysql_dir)
                shutil.rmtree("temp_mysql", ignore_errors=True)
            else:
                temp_files = os.listdir("temp_mysql")
                if temp_files:
                    shutil.move(os.path.join("temp_mysql", temp_files[0]), self.mysql_dir)
                shutil.rmtree("temp_mysql", ignore_errors=True)

            mysql_bin = os.path.normpath(os.path.join(self.mysql_dir, "bin", "mysqld.exe"))
            if not os.path.exists(mysql_bin):
                self.log_area.insert("1.0", f"Hata: {mysql_bin} bulunamadı. ZIP yapısı hatalı olabilir.\n")
                self.log_area.see("1.0")
                logging.error(f"{mysql_bin} bulunamadı. ZIP yapısı hatalı olabilir.")
                return

            self.create_my_ini()
            self.progress["value"] = 60
            self.frame.update()

            data_dir = os.path.normpath(os.path.join(self.mysql_dir, "data"))
            if not os.path.exists(data_dir) or not os.listdir(data_dir):
                try:
                    process = subprocess.Popen(
                        [mysql_bin, "--initialize-insecure"],
                        cwd=os.path.join(self.mysql_dir, "bin"),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=60)
                    if process.returncode != 0:
                        self.log_area.insert("1.0", f"MySQL ilklendirme hatası: {stderr}\n")
                        self.log_area.see("1.0")
                        logging.error(f"MySQL ilklendirme hatası: {stderr}")
                        self.log_area.insert("1.0", "Manuel ilklendirme talimatı: Komut isteminde şu komutu çalıştırın:\n")
                        self.log_area.insert("1.0", f'cd {self.mysql_dir}\\bin && mysqld --initialize-insecure\n')
                        self.log_area.see("1.0")
                        return
                    self.log_area.insert("1.0", "MySQL ilklendirme tamamlandı.\n")
                    self.log_area.see("1.0")
                    logging.info("MySQL ilklendirme tamamlandı.")
                except Exception as e:
                    self.log_area.insert("1.0", f"MySQL ilklendirme hatası: {str(e)}\n")
                    self.log_area.see("1.0")
                    logging.error(f"MySQL ilklendirme hatası: {str(e)}")
                    self.log_area.insert("1.0", "Manuel ilklendirme talimatı: Komut isteminde şu komutu çalıştırın:\n")
                    self.log_area.insert("1.0", f'cd {self.mysql_dir}\\bin && mysqld --initialize-insecure\n')
                    self.log_area.see("1.0")
                    return

            self.progress["value"] = 90
            self.frame.update()

            try:
                subprocess.run(
                    f'netsh advfirewall firewall add rule name="MySQL Port {self.mysql_port}" dir=in action=allow protocol=TCP localport={self.mysql_port}',
                    shell=True,
                    check=True,
                    capture_output=True
                )
                self.log_area.insert("1.0", f"Firewall kuralı eklendi: Port {self.mysql_port}\n")
                self.log_area.see("1.0")
                logging.info(f"Firewall kuralı eklendi: Port {self.mysql_port}")
            except subprocess.CalledProcessError as e:
                self.log_area.insert("1.0", f"Firewall kuralı ekleme hatası (yönetici izni gerekebilir): {e.stderr.decode()}\n")
                self.log_area.see("1.0")
                logging.error(f"Firewall kuralı ekleme hatası: {e.stderr.decode()}")
            except Exception as e:
                self.log_area.insert("1.0", f"Firewall kuralı ekleme hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Firewall kuralı ekleme hatası: {str(e)}")

            self.mysql_installed = True
            self.status_label["text"] = "MySQL kuruldu."
            self.progress["value"] = 100
            self.frame.update()
            self.log_area.insert("1.0", "Portable MySQL başarıyla kuruldu.\n")
            self.log_area.see("1.0")
            logging.info("Portable MySQL başarıyla kuruldu.")
        except requests.exceptions.RequestException as e:
            self.status_label["text"] = "MySQL kurulum hatası."
            self.log_area.insert("1.0", f"MySQL indirme hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"MySQL indirme hatası: {str(e)}")
        except Exception as e:
            self.status_label["text"] = "MySQL kurulum hatası."
            self.log_area.insert("1.0", f"MySQL kurulum hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"MySQL kurulum hatası: {str(e)}")

    def start_mysql(self):
        if self.is_mysql_running():
            self.log_area.insert("1.0", "MySQL zaten çalışıyor.\n")
            self.log_area.see("1.0")
            logging.info("MySQL zaten çalışıyor.")
            return

        mysql_bin = os.path.normpath(os.path.join(self.mysql_dir, "bin", "mysqld.exe"))
        my_ini_path = os.path.normpath(os.path.join(self.mysql_dir, "my.ini"))
        if not os.path.exists(mysql_bin):
            self.log_area.insert("1.0", f"Hata: {mysql_bin} bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error(f"{mysql_bin} bulunamadı.")
            return

        if not os.path.exists(my_ini_path):
            self.log_area.insert("1.0", f"Hata: {my_ini_path} bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error(f"{my_ini_path} bulunamadı.")
            self.create_my_ini()
            if not os.path.exists(my_ini_path):
                self.log_area.insert("1.0", "Hata: my.ini oluşturulamadı, lütfen manuel oluşturun.\n")
                self.log_area.see("1.0")
                self.log_area.insert("1.0", f"Manuel my.ini talimatı: {self.mysql_dir}\\my.ini dosyasına şu içeriği ekleyin:\n")
                self.log_area.insert("1.0", f"""
[mysqld]
basedir="{os.path.abspath(self.mysql_dir).replace('\\', '/')}"
datadir="{os.path.abspath(os.path.join(self.mysql_dir, 'data')).replace('\\', '/')}"
port={self.mysql_port}
bind-address=127.0.0.1
""")
                self.log_area.see("1.0")
                return

        if self.check_port(self.mysql_port):
            self.log_area.insert("1.0", f"Hata: Port {self.mysql_port} zaten kullanımda. Lütfen başka bir port deneyin (örneğin, 3307).\n")
            self.log_area.see("1.0")
            logging.error(f"Port {self.mysql_port} zaten kullanımda.")
            return

        try:
            process = subprocess.Popen(
                [mysql_bin, f"--defaults-file={my_ini_path}"],
                cwd=os.path.join(self.mysql_dir, "bin"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(5)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.log_area.insert("1.0", f"MySQL başlatma hatası: {stderr}\n")
                self.log_area.see("1.0")
                logging.error(f"MySQL başlatma hatası: {stderr}")
                err_files = glob.glob(os.path.join(self.mysql_dir, "data", "*.err"))
                if err_files:
                    with open(err_files[0], "r", encoding="utf-8", errors="ignore") as f:
                        err_log = f.read()
                        self.log_area.insert("1.0", f"MySQL hata günlüğü: {err_log}\n")
                        self.log_area.see("1.0")
                        logging.error(f"MySQL hata günlüğü: {err_log}")
                self.log_area.insert("1.0", "Manuel başlatma talimatı: Komut isteminde şu komutu çalıştırın:\n")
                self.log_area.insert("1.0", f'cd {self.mysql_dir}\\bin && mysqld --defaults-file="..\\my.ini"\n')
                self.log_area.see("1.0")
                self.log_area.insert("1.0", "Veri dizini bozuk olabilir, sıfırlamak için şu komutu çalıştırın:\n")
                self.log_area.insert("1.0", f'rmdir /s /q {self.mysql_dir}\\data && mkdir {self.mysql_dir}\\data && cd {self.mysql_dir}\\bin && mysqld --initialize-insecure\n')
                self.log_area.see("1.0")
                return

            self.log_area.insert("1.0", f"MySQL başlatıldı (Port: {self.mysql_port}).\n")
            self.log_area.see("1.0")
            logging.info(f"MySQL başlatıldı (Port: {self.mysql_port}).")
            self.connect_mysql()
            self.update_db_list()
        except Exception as e:
            self.log_area.insert("1.0", f"MySQL başlatma hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"MySQL başlatma hatası: {str(e)}")
            self.log_area.insert("1.0", "Manuel başlatma talimatı: Komut isteminde şu komutu çalıştırın:\n")
            self.log_area.insert("1.0", f'cd {self.mysql_dir}\\bin && mysqld --defaults-file="..\\my.ini"\n')
            self.log_area.see("1.0")
            self.log_area.insert("1.0", "Veri dizini bozuk olabilir, sıfırlamak için şu komutu çalıştırın:\n")
            self.log_area.insert("1.0", f'rmdir /s /q {self.mysql_dir}\\data && mkdir {self.mysql_dir}\\data && cd {self.mysql_dir}\\bin && mysqld --initialize-insecure\n')
            self.log_area.see("1.0")

    def test_connection(self):
        self.mysql_host = self.host_entry.get()
        self.mysql_user = self.user_entry.get()
        self.mysql_password = self.pass_entry.get()
        self.mysql_port = self.port_entry.get()

        if not self.is_mysql_running():
            self.log_area.insert("1.0", "Hata: MySQL servisi çalışmıyor, lütfen başlatın.\n")
            self.log_area.see("1.0")
            return

        self.connect_mysql()

    def connect_mysql(self):
        if self.connection:
            self.connection.close()
            self.connection = None

        try:
            self.connection = mysql.connector.connect(
                host=self.mysql_host,
                user=self.mysql_user,
                password=self.mysql_password,
                port=int(self.mysql_port)
            )
            self.log_area.insert("1.0", "MySQL bağlantısı kuruldu.\n")
            self.log_area.see("1.0")
            logging.info("MySQL bağlantısı kuruldu.")
            self.status_label["text"] = "MySQL bağlı."
            self.update_db_list()
        except Error as e:
            self.log_area.insert("1.0", f"MySQL bağlantı hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"MySQL bağlantı hatası: {str(e)}")
            self.connection = None
            self.status_label["text"] = "MySQL bağlantısı yok."

    def update_db_list(self):
        if not self.connection:
            self.log_area.insert("1.0", "Hata: MySQL bağlantısı yok, veritabanları listelenemedi.\n")
            self.log_area.see("1.0")
            logging.error("MySQL bağlantısı yok, veritabanları listelenemedi.")
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            self.db_list.delete(0, tk.END)
            for db in databases:
                self.db_list.insert(tk.END, db[0])
            cursor.close()
            self.log_area.insert("1.0", f"{len(databases)} veritabanı listelendi.\n")
            self.log_area.see("1.0")
            logging.info(f"{len(databases)} veritabanı listelendi.")
        except Error as e:
            self.log_area.insert("1.0", f"Veritabanı listeleme hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Veritabanı listeleme hatası: {str(e)}")

    def create_database(self):
        db_name = self.db_name_entry.get().strip()
        if not db_name:
            self.log_area.insert("1.0", "Hata: Veritabanı adı boş olamaz.\n")
            self.log_area.see("1.0")
            logging.error("Veritabanı adı boş.")
            return

        if not self.is_mysql_running():
            self.log_area.insert("1.0", "Hata: MySQL servisi çalışmıyor, lütfen başlatın.\n")
            self.log_area.see("1.0")
            return

        if not self.connection:
            self.log_area.insert("1.0", "Hata: MySQL bağlantısı yok, bağlanılıyor...\n")
            self.log_area.see("1.0")
            self.connect_mysql()
            if not self.connection:
                return

        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE `{db_name}`")
            self.connection.commit()
            cursor.close()
            self.update_db_list()
            self.log_area.insert("1.0", f"Veritabanı oluşturuldu: {db_name}\n")
            self.log_area.see("1.0")
            logging.info(f"Veritabanı oluşturuldu: {db_name}")
        except Error as e:
            self.log_area.insert("1.0", f"Veritabanı oluşturma hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Veritabanı oluşturma hatası: {str(e)}")