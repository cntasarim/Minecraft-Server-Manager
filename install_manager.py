# install_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
import io
import os
import shutil
import logging
import zipfile
import subprocess
import configparser
import glob
from bs4 import BeautifulSoup
import json
import platform
import tarfile
import tempfile

class InstallManager:
    def __init__(self, parent, log_area):
        self.frame = ttk.Frame(parent)
        self.log_area = log_area
        self.packages = []
        self.current_page = 0
        self.page_size = 30
        self.api_key = self.load_api_key()
        self.app = parent.master.master
        self.installing = False
        self.java_versions = {
            "1.16.5": "16",
            "1.17": "17",
            "1.18": "17",
            "1.19": "17",
            "1.20": "17",
            "1.20.5": "21",
            "1.21": "21"
        }
        self.java_download_urls = {
            "17": {
                "Windows": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip",
                "Linux": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.12_7.tar.gz"
            },
            "21": {
                "Windows": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_windows_hotspot_21.0.4_7.zip",
                "Linux": "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4%2B7/OpenJDK21U-jdk_x64_linux_hotspot_21.0.4_7.tar.gz"
            }
        }
        self.setup_ui()

    def load_api_key(self):
        config = configparser.ConfigParser()
        config_file = "config.ini"
        if os.path.exists(config_file):
            try:
                config.read(config_file)
                api_key = config.get("CurseForge", "api_key", fallback=None)
                if api_key:
                    self.log_area.insert("1.0", "CurseForge API key config.ini'den yüklendi.\n")
                    self.log_area.see("1.0")
                    logging.info("CurseForge API key config.ini'den yüklendi.")
                    return api_key
                else:
                    self.log_area.insert("1.0", "Hata: config.ini'de CurseForge api_key bulunamadı.\n")
                    self.log_area.see("1.0")
                    logging.error("config.ini'de CurseForge api_key bulunamadı.")
            except Exception as e:
                self.log_area.insert("1.0", f"Hata: config.ini okuma hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"config.ini okuma hatası: {str(e)}")
        else:
            self.log_area.insert("1.0", "Hata: config.ini dosyası bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error("config.ini dosyası bulunamadı.")
        messagebox.showerror("Hata", "CurseForge API key bulunamadı. Lütfen config.ini dosyasında [CurseForge] bölümüne api_key ekleyin.")
        return None

    def get_required_java_version(self, pkg):
        if pkg["type"] == "java":
            version = pkg["name"]
            for mc_version, java_version in self.java_versions.items():
                if version.startswith(mc_version):
                    return java_version
            return "17"
        else:
            return "21"

    def download_java(self, java_version):
        os_type = platform.system()
        if os_type not in self.java_download_urls[java_version]:
            self.log_area.insert("1.0", f"Hata: {os_type} için Java {java_version} indirme URL'si bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error(f"{os_type} için Java {java_version} indirme URL'si bulunamadı.")
            return False

        java_dir = os.path.join("Java", f"jdk-{java_version}")
        if os.path.exists(java_dir):
            self.log_area.insert("1.0", f"Java {java_version} zaten kurulu: {java_dir}\n")
            self.log_area.see("1.0")
            logging.info(f"Java {java_version} zaten kurulu: {java_dir}")
            return True

        url = self.java_download_urls[java_version][os_type]
        file_name = url.split("/")[-1]
        file_path = os.path.join("Java", file_name)
        
        try:
            self.log_area.insert("1.0", f"Java {java_version} indiriliyor: {url}\n")
            self.log_area.see("1.0")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            os.makedirs("Java", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)
            self.log_area.insert("1.0", f"Java {java_version} indirildi: {file_path}\n")
            self.log_area.see("1.0")
            logging.info(f"Java {java_version} indirildi: {file_path}")

            if file_name.endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall("Java")
            elif file_name.endswith(".tar.gz"):
                with tarfile.open(file_path, "r:gz") as tar_ref:
                    tar_ref.extractall("Java")
            os.remove(file_path)
            
            #extracted_dir = os.path.join("Java", file_name.replace(".zip", "").replace(".tar.gz", ""))
            #if os.path.exists(extracted_dir):
            #    shutil.move(extracted_dir, java_dir)
            # Yeni yöntem: klasörleri ara ve uygun olanı yeniden adlandır
            found_dir = None
            for entry in os.scandir("Java"):
                if entry.is_dir() and entry.name.startswith(f"jdk-{java_version}") and entry.name != f"jdk-{java_version}":
                    found_dir = os.path.join("Java", entry.name)
                    break

            if found_dir:
                if not os.path.exists(java_dir):
                    shutil.move(found_dir, java_dir)
                else:
                    shutil.rmtree(found_dir)  # Eğer zaten hedef varsa, geçici klasörü sil
            else:
                self.log_area.insert("1.0", f"Hata: Java {java_version} dizini bulunamadı ve yeniden adlandırılamadı.\n")
                self.log_area.see("1.0")
                logging.error(f"Java {java_version} dizini bulunamadı.")
                return False

            self.log_area.insert("1.0", f"Java {java_version} kuruldu: {java_dir}\n")
            self.log_area.see("1.0")
            logging.info(f"Java {java_version} kuruldu: {java_dir}")
            return True
        except Exception as e:
            self.log_area.insert("1.0", f"Java {java_version} indirme/kurulum hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Java {java_version} indirme/kurulum hatası: {str(e)}")
            return False

    def get_mod_id_from_slug(self, slug):
        """Fetch the numeric mod ID from the mod slug using CurseForge API."""
        try:
            headers = {"x-api-key": self.api_key, "Accept": "application/json"}
            params = {
                "gameId": 432,
                "classId": 6,  # Mods
                "searchFilter": slug
            }
            response = requests.get(
                "https://api.curseforge.com/v1/mods/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            mods = response.json()["data"]
            for mod in mods:
                if mod["slug"] == slug:
                    return str(mod["id"])
            self.log_area.insert("1.0", f"Uyarı: Mod slug '{slug}' için mod ID bulunamadı.\n")
            self.log_area.see("1.0")
            logging.warning(f"Mod slug '{slug}' için mod ID bulunamadı.")
            return None
        except Exception as e:
            self.log_area.insert("1.0", f"Mod ID alma hatası (slug: {slug}): {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Mod ID alma hatası (slug: {slug}): {str(e)}")
            return None

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Sunucu Türü:").pack(pady=5)
        self.server_type = ttk.Combobox(main_frame, values=["Minecraft Java", "CurseForge"])
        self.server_type.pack(pady=5)
        self.server_type.set("CurseForge")
        self.server_type.bind("<<ComboboxSelected>>", self.update_package_list)

        self.search_frame = ttk.Frame(main_frame)
        self.search_frame.pack(pady=5, fill="x")
        ttk.Label(self.search_frame, text="Modpack Ara:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(self.search_frame, width=50)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(self.search_frame, text="Ara", command=self.search_modpacks).pack(side="left", padx=5)

        self.notification_label = ttk.Label(main_frame, text="")
        self.notification_label.pack(pady=5)

        self.installation_status_label = ttk.Label(main_frame, text="")
        self.installation_status_label.pack(pady=5)

        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill="both", expand=True)

        self.package_canvas_frame = ttk.Frame(self.content_frame)
        self.package_canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.package_canvas_frame, height=700)
        self.scrollbar = ttk.Scrollbar(self.package_canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.package_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.package_frame, anchor="nw")
        self.package_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.pagination_frame = ttk.Frame(main_frame)
        self.pagination_frame.pack(pady=5)
        ttk.Button(self.pagination_frame, text="Önceki", command=self.prev_page).pack(side="left", padx=5)
        ttk.Button(self.pagination_frame, text="Sonraki", command=self.next_page).pack(side="left", padx=5)

        self.progress = ttk.Progressbar(main_frame, length=200, mode="determinate")
        self.progress.pack(pady=5)

        self.update_package_list()

    def search_modpacks(self):
        self.current_page = 0
        self.update_package_list()

    def update_package_list(self, event=None):
        if not self.api_key:
            self.notification_label["text"] = "Hata: CurseForge API key eksik."
            return

        self.notification_label["text"] = "İçerikler listeleniyor..."
        self.frame.update()

        for widget in self.package_frame.winfo_children():
            widget.destroy()
        self.packages = []

        if self.server_type.get() == "Minecraft Java":
            self.search_frame.pack_forget()
            try:
                versions = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json").json()
                for v in versions["versions"]:
                    self.packages.append({"name": v["id"], "image": None, "url": v["url"], "type": "java"})
                self.log_area.insert("1.0", "Minecraft Java sürümleri yüklendi.\n")
                self.log_area.see("1.0")
                logging.info("Minecraft Java sürümleri yüklendi.")
            except Exception as e:
                self.log_area.insert("1.0", f"Sürüm yükleme hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Sürüm yükleme hatası: {str(e)}")
        else:
            self.search_frame.pack(fill="x")
            try:
                headers = {"x-api-key": self.api_key, "Accept": "application/json"}
                params = {
                    "gameId": 432,
                    "classId": 4471,
                    "sortField": 2,
                    "sortOrder": "desc",
                    "pageSize": self.page_size,
                    "index": self.current_page * self.page_size
                }
                search_query = self.search_entry.get().strip()
                if search_query:
                    params["searchFilter"] = search_query

                response = requests.get(
                    "https://api.curseforge.com/v1/mods/search",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                mods = response.json()["data"]
                for mod in mods:
                    image_url = mod.get("logo", {}).get("thumbnailUrl", None)
                    self.packages.append({
                        "name": mod["name"],
                        "image": image_url,
                        "mod_id": mod["id"],
                        "type": "curseforge"
                    })
                self.log_area.insert("1.0", f"{len(self.packages)} CurseForge modpack yüklendi.\n")
                self.log_area.see("1.0")
                logging.info(f"{len(self.packages)} CurseForge modpack yüklendi.")
            except requests.exceptions.HTTPError as e:
                self.log_area.insert("1.0", f"CurseForge mod yükleme hatası: {str(e)}\n")
                self.log_area.insert("1.0", f"API yanıt detayları: {e.response.text}\n")
                self.log_area.see("1.0")
                logging.error(f"CurseForge mod yükleme hatası: {str(e)}, detay: {e.response.text}")
            except Exception as e:
                self.log_area.insert("1.0", f"CurseForge mod yükleme hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"CurseForge mod yükleme hatası: {str(e)}")

        self.display_packages()
        self.notification_label["text"] = f"{len(self.packages)} içerik listelendi."

    def prev_page(self):
        if self.current_page > 0 and not self.installing:
            self.current_page -= 1
            self.update_package_list()

    def next_page(self):
        if len(self.packages) >= self.page_size and not self.installing:
            self.current_page += 1
            self.update_package_list()

    def display_packages(self):
        for widget in self.package_frame.winfo_children():
            widget.destroy()

        if self.server_type.get() == "Minecraft Java":
            row = 0
            col = 0
            for pkg in self.packages:
                pkg_frame = ttk.Frame(self.package_frame)
                pkg_frame.grid(row=row, column=col, padx=5, pady=5, sticky="n")
                ttk.Label(pkg_frame, text=pkg["name"], wraplength=100, justify="center").pack()
                install_button = ttk.Button(pkg_frame, text="Bu Paketi Kur", command=lambda p=pkg: self.install_package(p))
                install_button.pack(pady=5)
                if self.installing:
                    install_button.configure(state="disabled")
                col += 1
                if col > 7:
                    col = 0
                    row += 1
        else:
            row = 0
            col = 0
            for pkg in self.packages:
                pkg_frame = ttk.Frame(self.package_frame)
                pkg_frame.grid(row=row, column=col, padx=5, pady=5, sticky="n")

                if pkg["image"]:
                    try:
                        response = requests.get(pkg["image"])
                        img_data = response.content
                        img = Image.open(io.BytesIO(img_data)).resize((80, 80))
                        photo = ImageTk.PhotoImage(img)
                        ttk.Label(pkg_frame, image=photo).pack()
                        pkg_frame.image = photo
                    except:
                        ttk.Label(pkg_frame, text=pkg["name"], wraplength=80, justify="center").pack()
                else:
                    ttk.Label(pkg_frame, text=pkg["name"], wraplength=80, justify="center").pack()

                install_button = ttk.Button(pkg_frame, text="Bu Paketi Kur", command=lambda p=pkg: self.install_package(p))
                install_button.pack(pady=5)
                if self.installing:
                    install_button.configure(state="disabled")

                col += 1
                if col > 9:
                    col = 0
                    row += 1

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def configure_server(self, server_dir):
        properties_path = os.path.join(server_dir, "server.properties")
        default_properties = {
            "server-port": "25565",
            "max-players": "20",
            "motd": "Minecraft Server",
            "pvp": "true",
            "difficulty": "normal",
            "online-mode": "true",
            "level-type": "minecraft:normal",
            "spawn-protection": "0"
        }
        if os.path.exists(properties_path):
            with open(properties_path, "r") as f:
                lines = f.readlines()
            with open(properties_path, "w") as f:
                for line in lines:
                    key = line.split("=")[0] if "=" in line else None
                    if key and key in default_properties:
                        f.write(f"{key}={default_properties[key]}\n")
                        del default_properties[key]
                    else:
                        f.write(line)
                for key, value in default_properties.items():
                    f.write(f"{key}={value}\n")
        else:
            with open(properties_path, "w") as f:
                for key, value in default_properties.items():
                    f.write(f"{key}={value}\n")
        self.log_area.insert("1.0", "server.properties yapılandırıldı.\n")
        self.log_area.see("1.0")
        logging.info("server.properties yapılandırıldı.")

    def process_modlist(self, server_dir):
        modlist_path = os.path.join(server_dir, "modlist.html")
        if not os.path.exists(modlist_path):
            self.log_area.insert("1.0", "Uyarı: modlist.html bulunamadı, modlar manuel olarak kontrol edilmeli.\n")
            self.log_area.see("1.0")
            logging.warning("modlist.html bulunamadı.")
            return False

        try:
            with open(modlist_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            mod_links = soup.find_all("a", href=True)
            mod_urls = [link["href"] for link in mod_links if "curseforge.com" in link["href"]]
            
            total_mods = len(mod_urls)
            self.installation_status_label["text"] = f"Modlar İndiriliyor .... Toplam: {total_mods} İndirilen: 0"
            self.frame.update()
            
            mods_dir = os.path.join(server_dir, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            
            successful_downloads = 0
            for i, url in enumerate(mod_urls):
                try:
                    slug = url.split("/")[-1]
                    mod_id = self.get_mod_id_from_slug(slug)
                    if not mod_id:
                        self.log_area.insert("1.0", f"Mod geçiliyor (URL: {url}): Mod ID bulunamadı.\n")
                        self.log_area.see("1.0")
                        logging.warning(f"Mod geçiliyor (URL: {url}): Mod ID bulunamadı.")
                        continue

                    headers = {"x-api-key": self.api_key}
                    response = requests.get(
                        f"https://api.curseforge.com/v1/mods/{mod_id}/files",
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    files = response.json()["data"]
                    if files:
                        file_url = files[0]["downloadUrl"]
                        mod_name = files[0]["fileName"]
                        response = requests.get(file_url, timeout=10)
                        response.raise_for_status()
                        with open(os.path.join(mods_dir, mod_name), "wb") as f:
                            f.write(response.content)
                        self.log_area.insert("1.0", f"Mod indirildi: {mod_name}\n")
                        self.log_area.see("1.0")
                        logging.info(f"Mod indirildi: {mod_name}")
                        successful_downloads += 1
                    self.progress["value"] = (i + 1) / len(mod_urls) * 50
                    self.installation_status_label["text"] = f"Modlar İndiriliyor .... Toplam: {total_mods} İndirilen: {successful_downloads}"
                    self.frame.update()
                except Exception as e:
                    self.log_area.insert("1.0", f"Mod indirme hatası (URL: {url}): {str(e)}\n")
                    self.log_area.see("1.0")
                    logging.error(f"Mod indirme hatası (URL: {url}): {str(e)}")
                    self.installation_status_label["text"] = f"Modlar İndiriliyor .... Toplam: {total_mods} İndirilen: {successful_downloads}"
                    self.frame.update()

            if successful_downloads == 0:
                self.log_area.insert("1.0", "Hata: Hiçbir mod indirilemedi, kurulum iptal ediliyor.\n")
                self.log_area.see("1.0")
                logging.error("Hiçbir mod indirilemedi, kurulum iptal ediliyor.")
                return False

            self.log_area.insert("1.0", f"{successful_downloads}/{total_mods} mod başarıyla indirildi.\n")
            self.log_area.see("1.0")
            logging.info(f"{successful_downloads}/{total_mods} mod başarıyla indirildi.")
            return True
        except Exception as e:
            self.log_area.insert("1.0", f"modlist.html işleme hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"modlist.html işleme hatası: {str(e)}")
            return False

    def find_server_jar(self, server_dir):
        jar_files = glob.glob(os.path.join(server_dir, "*.jar"))
        possible_jars = [
            "server.jar", "minecraft_server.jar", "forge.jar", "fabric.jar"
        ]
        for jar in possible_jars:
            if os.path.exists(os.path.join(server_dir, jar)):
                return jar
        for jar_file in jar_files:
            if os.path.basename(jar_file).lower().endswith(".jar"):
                return os.path.basename(jar_file)
        return None

    def save_server_config(self, server_dir, java_version):
        config_file = os.path.join(server_dir, "server_config.json")
        config = {"java_version": java_version}
        with open(config_file, "w") as f:
            json.dump(config, f)
        self.log_area.insert("1.0", f"Sunucu yapılandırması kaydedildi: Java {java_version}\n")
        self.log_area.see("1.0")
        logging.info(f"Sunucu yapılandırması kaydedildi: Java {java_version}")

    def backup_server(self, server_dir, temp_backup_dir):
        if os.path.exists(server_dir):
            try:
                shutil.copytree(server_dir, temp_backup_dir)
                self.log_area.insert("1.0", f"Geçici yedek oluşturuldu: {temp_backup_dir}\n")
                self.log_area.see("1.0")
                logging.info(f"Geçici yedek oluşturuldu: {temp_backup_dir}")
                return True
            except Exception as e:
                self.log_area.insert("1.0", f"Geçici yedek oluşturma hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Geçici yedek oluşturma hatası: {str(e)}")
                return False
        return True

    def restore_server(self, server_dir, temp_backup_dir):
        if os.path.exists(temp_backup_dir):
            try:
                if os.path.exists(server_dir):
                    shutil.rmtree(server_dir)
                shutil.copytree(temp_backup_dir, server_dir)
                self.log_area.insert("1.0", f"Sunucu geri yüklendi: {server_dir}\n")
                self.log_area.see("1.0")
                logging.info(f"Sunucu geri yüklendi: {server_dir}")
                shutil.rmtree(temp_backup_dir)
                self.log_area.insert("1.0", f"Geçici yedek silindi: {temp_backup_dir}\n")
                self.log_area.see("1.0")
                logging.info(f"Geçici yedek silindi: {temp_backup_dir}")
                return True
            except Exception as e:
                self.log_area.insert("1.0", f"Sunucu geri yükleme hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Sunucu geri yükleme hatası: {str(e)}")
                return False
        return True

    def install_package(self, pkg):
        if self.installing:
            messagebox.showwarning("Uyarı", "Bir kurulum zaten devam ediyor.")
            return
        self.installing = True
        self.installation_status_label["text"] = "Kurulum başlatılıyor..."
        self.frame.update()

        for widget in self.package_frame.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    child.configure(state="disabled")
        self.server_type.configure(state="disabled")
        self.search_entry.configure(state="disabled")
        self.pagination_frame.pack_forget()

        server_dir = "servers/server1"
        temp_backup_dir = os.path.join(tempfile.gettempdir(), "minecraft_server_backup")

        try:
            if not self.backup_server(server_dir, temp_backup_dir):
                raise Exception("Geçici yedek oluşturulamadı.")

            if os.path.exists(server_dir):
                if messagebox.askyesno(
                    "Yedekleme",
                    "Mevcut sunucu dosyaları tespit edildi. Yedek alınsın mı?"
                ):
                    try:
                        self.app.backup_tab.take_backup()
                        self.log_area.insert("1.0", "Sunucu yedeği alındı.\n")
                        self.log_area.see("1.0")
                        logging.info("Sunucu yedeği alındı.")
                    except Exception as e:
                        self.log_area.insert("1.0", f"Yedekleme hatası: {str(e)}\n")
                        self.log_area.see("1.0")
                        logging.error(f"Yedekleme hatası: {str(e)}")
                try:
                    shutil.rmtree(server_dir)
                    self.log_area.insert("1.0", f"Mevcut sunucu dosyaları silindi: {server_dir}\n")
                    self.log_area.see("1.0")
                    logging.info(f"Mevcut sunucu dosyaları silindi: {server_dir}")
                except Exception as e:
                    raise Exception(f"Dosya silme hatası: {str(e)}")

            os.makedirs(server_dir, exist_ok=True)
            self.progress["value"] = 0
            self.frame.update()

            java_version = self.get_required_java_version(pkg)
            if not self.download_java(java_version):
                raise Exception(f"Java {java_version} kurulamadı.")

            if pkg["type"] == "java":
                version_data = requests.get(pkg["url"]).json()
                server_url = version_data["downloads"]["server"]["url"]
                self.progress["value"] = 50
                self.installation_status_label["text"] = "Sunucu JAR dosyası indiriliyor..."
                self.frame.update()
                response = requests.get(server_url)
                with open(os.path.join(server_dir, "server.jar"), "wb") as f:
                    f.write(response.content)

                self.progress["value"] = 75
                self.installation_status_label["text"] = "Sunucu yapılandırılıyor..."
                self.frame.update()
                self.configure_server(server_dir)
                self.save_server_config(server_dir, java_version)

                self.progress["value"] = 100
                self.installation_status_label["text"] = "Sunucu başlatmaya hazır!"
                self.frame.update()
                self.log_area.insert("1.0", f"{pkg['name']} kuruldu.\n")
                self.log_area.see("1.0")
                logging.info(f"{pkg['name']} kuruldu.")
            else:
                self.installation_status_label["text"] = "Modpack indiriliyor..."
                self.frame.update()
                headers = {"x-api-key": self.api_key}
                response = requests.get(
                    f"https://api.curseforge.com/v1/mods/{pkg['mod_id']}/files",
                    headers=headers
                )
                response.raise_for_status()
                files = response.json()["data"]
                self.log_area.insert("1.0", f"API yanıtı: {len(files)} dosya bulundu için {pkg['name']}.\n")
                self.log_area.see("1.0")
                logging.info(f"API yanıtı: {len(files)} dosya bulundu için {pkg['name']}.")

                server_file = None
                for file in files:
                    if file.get("isServerPack", False):
                        server_file = file
                        break
                if not server_file:
                    if files:
                        server_file = files[0]
                        self.log_area.insert("1.0", f"Uyarı: {pkg['name']} için sunucu paketi bulunamadı, en son dosya deneniyor.\n")
                        self.log_area.see("1.0")
                        logging.warning(f"{pkg['name']} için sunucu paketi bulunamadı, en son dosya deneniyor.")
                    else:
                        raise Exception(f"{pkg['name']} için uygun dosya bulunamadı.")

                file_url = server_file["downloadUrl"]
                if not file_url:
                    raise Exception(f"{pkg['name']} için indirme URL’si bulunamadı.")

                self.progress["value"] = 25
                self.frame.update()
                response = requests.get(file_url, timeout=10)
                response.raise_for_status()
                with open(os.path.join(server_dir, "modpack.zip"), "wb") as f:
                    f.write(response.content)
                with zipfile.ZipFile(os.path.join(server_dir, "modpack.zip"), "r") as zip_ref:
                    zip_ref.extractall(server_dir)
                os.remove(os.path.join(server_dir, "modpack.zip"))
                self.progress["value"] = 50
                self.frame.update()

                if not self.process_modlist(server_dir):
                    raise Exception("Modlar indirilemedi, kurulum iptal ediliyor.")

                if not self.find_server_jar(server_dir):
                    self.installation_status_label["text"] = "Sunucu JAR dosyası indiriliyor..."
                    self.log_area.insert("1.0", "Uyarı: Sunucu JAR dosyası bulunamadı, varsayılan Minecraft JAR indiriliyor.\n")
                    self.log_area.see("1.0")
                    logging.warning("Sunucu JAR dosyası bulunamadı, varsayılan Minecraft JAR indiriliyor.")
                    try:
                        version_data = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json").json()
                        latest_release = version_data["latest"]["release"]
                        for version in version_data["versions"]:
                            if version["id"] == latest_release:
                                version_url = version["url"]
                                break
                        version_data = requests.get(version_url).json()
                        server_url = version_data["downloads"]["server"]["url"]
                        response = requests.get(server_url)
                        with open(os.path.join(server_dir, "server.jar"), "wb") as f:
                            f.write(response.content)
                        self.log_area.insert("1.0", "Varsayılan Minecraft JAR indirildi.\n")
                        self.log_area.see("1.0")
                        logging.info("Varsayılan Minecraft JAR indirildi.")
                    except Exception as e:
                        raise Exception(f"JAR indirme hatası: {str(e)}")

                self.progress["value"] = 75
                self.installation_status_label["text"] = "Sunucu yapılandırılıyor..."
                self.frame.update()
                self.configure_server(server_dir)
                self.save_server_config(server_dir, java_version)

                self.progress["value"] = 100
                self.installation_status_label["text"] = "Sunucu başlatmaya hazır!"
                self.frame.update()
                self.log_area.insert("1.0", f"{pkg['name']} (CurseForge paketi) kuruldu.\n")
                self.log_area.see("1.0")
                logging.info(f"{pkg['name']} (CurseForge paketi) kuruldu.")

        except Exception as e:
            self.log_area.insert("1.0", f"Kurulum hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Kurulum hatası: {str(e)}")
            self.restore_server(server_dir, temp_backup_dir)
            messagebox.showerror("Hata", f"Kurulum başarısız oldu: {str(e)}\nLütfen tekrar deneyin.")

        finally:
            self.installing = False
            self.progress["value"] = 0
            self.installation_status_label["text"] = ""
            for widget in self.package_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.configure(state="normal")
            self.server_type.configure(state="normal")
            self.search_entry.configure(state="normal")
            self.pagination_frame.pack(pady=5)
            self.update_package_list()

    def install_server(self):
        if self.packages:
            self.install_package(self.packages[0])
        else:
            self.log_area.insert("1.0", "Hata: Kurulum için paket seçilmedi.\n")
            self.log_area.see("1.0")
            logging.error("Kurulum için paket seçilmedi.")