# server_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import psutil
import logging
import glob
import threading
import queue
import socket
import requests
from mcstatus import JavaServer
import json
import re
import platform

class ServerManager:
    def __init__(self, parent, app):
        self.frame = ttk.Frame(parent)
        self.app = app
        self.process = None
        self.output_queue = queue.Queue()
        self.running = False
        self.java_class_versions = {
            61: "17",
            65: "21"
        }
        self.setup_ui()
        self.update_server_info()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, sticky="n", padx=5, pady=5)

        console_frame = ttk.Frame(main_frame)
        console_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        ttk.Label(control_frame, text="Sunucu Durumu:").pack(pady=5)
        self.status_label = ttk.Label(control_frame, text="Sunucu durduruldu")
        self.status_label.pack(pady=5)

        self.start_button = ttk.Button(
            control_frame, text="SUNUCUYU BAŞLAT", command=self.start_server,
            style="Start.TButton"
        )
        self.start_button.pack(pady=5)

        self.stop_button = ttk.Button(
            control_frame, text="SUNUCUYU DURDUR", command=self.stop_server,
            style="Stop.TButton", state="disabled"
        )
        self.stop_button.pack(pady=5)

        self.restart_button = ttk.Button(
            control_frame, text="SUNUCUYU YENİDEN BAŞLAT", command=self.restart_server,
            style="Restart.TButton"
        )
        self.restart_button.pack(pady=5)

        ttk.Label(control_frame, text="Sunucu Adı:").pack(pady=5)
        self.server_name = ttk.Entry(control_frame)
        self.server_name.insert(0, "server1")
        self.server_name.pack(pady=5)

        ttk.Label(control_frame, text="RAM (MB):").pack(pady=5)
        self.ram_entry = ttk.Entry(control_frame)
        self.ram_entry.insert(0, "2048")
        self.ram_entry.pack(pady=5)

        ttk.Label(control_frame, text="Kişi Sayısı (Çevrimiçi/Maks):").pack(pady=5)
        self.player_count_label = ttk.Label(control_frame, text="0/20")
        self.player_count_label.pack(pady=5)

        ttk.Label(control_frame, text="Sunucu Bilgileri:").pack(pady=5)
        self.ip_port_label = ttk.Label(control_frame, text="IP:PORT\nYükleniyor...", background="#d3d3d3", padding=5)
        self.ip_port_label.pack(pady=5)

        ttk.Label(control_frame, text="Çevrimiçi Oyuncular:").pack(pady=5)
        self.player_list = tk.Listbox(control_frame, height=5, width=30)
        self.player_list.pack(pady=5)
        self.player_list.insert(tk.END, "Çevrimiçi oyuncu yok")

        self.progress = ttk.Progressbar(control_frame, length=200, mode="determinate")
        self.progress.pack(pady=5)

        ttk.Label(console_frame, text="Sunucu Konsolu:").pack(anchor="w")
        self.console_area = tk.Text(
            console_frame, height=20, width=60, state="disabled",
            bg="black", fg="white", insertbackground="white"
        )
        self.console_area.pack(side="left", fill="both", expand=True, pady=5)
        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.console_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.console_area.configure(yscrollcommand=scrollbar.set)

        self.console_area.tag_configure("INFO", foreground="#00ff00")
        self.console_area.tag_configure("ERROR", foreground="#ff0000")
        self.console_area.tag_configure("WARNING", foreground="#ffff00")

        style = ttk.Style()
        style.theme_use("classic")
        style.configure("Start.TButton", background="#28a745", foreground="white", font=("Arial", 10, "bold"), relief="flat")
        style.configure("Stop.TButton", background="#dc3545", foreground="white", font=("Arial", 10, "bold"), relief="flat")
        style.configure("Restart.TButton", background="#007bff", foreground="white", font=("Arial", 10, "bold"), relief="flat")
        style.map("Start.TButton", background=[("disabled", "#6c757d")])
        style.map("Stop.TButton", background=[("disabled", "#6c757d")])
        style.map("Restart.TButton", background=[("disabled", "#6c757d")])

        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Label(info_frame, text="Sunucu Durumu:").pack(side="left", padx=5)
        self.server_status_label = ttk.Label(info_frame, text="Kapalı")
        self.server_status_label.pack(side="left", padx=5)

        ttk.Label(info_frame, text="Oyuncu Sayısı:").pack(side="left", padx=5)
        self.server_player_label = ttk.Label(info_frame, text="0")
        self.server_player_label.pack(side="left", padx=5)

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

    def handle_eula(self, server_dir):
        eula_path = os.path.join(server_dir, "eula.txt")
        if os.path.exists(eula_path):
            with open(eula_path, "r") as f:
                content = f.read()
                if "eula=false" in content.lower():
                    if messagebox.askyesno(
                        "EULA Kabulü",
                        "Minecraft EULA’yı kabul ediyor musunuz? (https://www.minecraft.net/eula)"
                    ):
                        with open(eula_path, "w") as f:
                            f.write("eula=true\n")
                        self.app.log_area.insert("1.0", "EULA kabul edildi, eula.txt güncellendi.\n")
                        self.app.log_area.see("1.0")
                        logging.info("EULA kabul edildi, eula.txt güncellendi.")
                        return True
                    else:
                        self.app.log_area.insert("1.0", "EULA kabul edilmedi, sunucu başlatılamaz.\n")
                        self.app.log_area.see("1.0")
                        logging.error("EULA kabul edilmedi, sunucu başlatılamaz.")
                        return False
        else:
            if messagebox.askyesno(
                "EULA Kabulü",
                "Minecraft EULA’yı kabul ediyor musunuz? (https://www.minecraft.net/eula)"
            ):
                with open(eula_path, "w") as f:
                    f.write("eula=true\n")
                self.app.log_area.insert("1.0", "EULA kabul edildi, eula.txt oluşturuldu.\n")
                self.app.log_area.see("1.0")
                logging.info("EULA kabul edildi, eula.txt oluşturuldu.")
                return True
            else:
                self.app.log_area.insert("1.0", "EULA kabul edilmedi, sunucu başlatılamaz.\n")
                self.app.log_area.see("1.0")
                logging.error("EULA kabul edilmedi, sunucu başlatılamaz.")
                return False
        return True

    def get_max_players(self, server_dir):
        properties_path = os.path.join(server_dir, "server.properties")
        max_players = 20
        if os.path.exists(properties_path):
            with open(properties_path, "r") as f:
                for line in f:
                    if line.startswith("max-players="):
                        try:
                            max_players = int(line.split("=")[1].strip())
                        except ValueError:
                            pass
        return max_players

    def get_server_port(self, server_dir):
        properties_path = os.path.join(server_dir, "server.properties")
        port = "25565"
        if os.path.exists(properties_path):
            with open(properties_path, "r") as f:
                for line in f:
                    if line.startswith("server-port="):
                        try:
                            port = line.split("=")[1].strip()
                            if port.isdigit():
                                return port
                        except ValueError:
                            pass
        return port

    def get_ip_port(self, port):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except:
            local_ip = "127.0.0.1"
        try:
            global_ip = requests.get("https://api.ipify.org", timeout=5).text
        except:
            global_ip = "Bilinmiyor"
        return f"IP:PORT\n{port}\nGLOBAL IP:PORT\n{global_ip}:{port}\nLOCAL IP:PORT\n{local_ip}:{port}"

    def read_output(self, pipe, queue):
        for line in iter(pipe.readline, ''):
            queue.put(line)
        pipe.close()

    def update_console(self):
        while True:
            try:
                line = self.output_queue.get_nowait()
                self.console_area.configure(state="normal")
                tag = "INFO" if "[INFO]" in line else "ERROR" if "[ERROR]" in line else "WARNING" if "[WARNING]" in line else None
                self.console_area.insert("end", line, tag)
                self.console_area.see("end")
                self.console_area.configure(state="disabled")
            except queue.Empty:
                break
        if self.running:
            self.frame.after(100, self.update_console)

    def update_server_info(self):
        server_dir = f"servers/{self.server_name.get()}"
        port = self.get_server_port(server_dir)
        max_players = self.get_max_players(server_dir)

        if self.process and self.process.poll() is None:
            self.server_status_label["text"] = "Açık"
            try:
                server = JavaServer.lookup(f"localhost:{port}")
                status = server.status()
                online_players = status.players.online
                player_names = status.players.names if status.players.names else []
                self.server_player_label["text"] = str(online_players)
                self.player_count_label["text"] = f"{online_players}/{max_players}"
                self.player_list.delete(0, tk.END)
                if player_names:
                    for name in player_names:
                        self.player_list.insert(tk.END, name)
                else:
                    self.player_list.insert(tk.END, "Çevrimiçi oyuncu yok")
            except Exception as e:
                self.server_player_label["text"] = "0"
                self.player_count_label["text"] = f"0/{max_players}"
                self.player_list.delete(0, tk.END)
                self.player_list.insert(tk.END, "Çevrimiçi oyuncu yok")
                self.app.log_area.insert("1.0", f"Sunucu durumu sorgulama hatası: {str(e)}\n")
                self.app.log_area.see("1.0")
                logging.error(f"Sunucu durumu sorgulama hatası: {str(e)}")
        else:
            self.server_status_label["text"] = "Kapalı"
            self.server_player_label["text"] = "0"
            self.player_count_label["text"] = f"0/{max_players}"
            self.player_list.delete(0, tk.END)
            self.player_list.insert(tk.END, "Çevrimiçi oyuncu yok")

        self.ip_port_label["text"] = self.get_ip_port(port)
        self.frame.after(5000, self.update_server_info)

    def ensure_no_java_processes(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == "java.exe":
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                    self.app.log_area.insert("1.0", f"Java süreci sonlandırıldı: PID {proc.pid}\n")
                    self.app.log_area.see("1.0")
                    logging.info(f"Java süreci sonlandırıldı: PID {proc.pid}")
                except Exception as e:
                    self.app.log_area.insert("1.0", f"Java süreci sonlandırma hatası: {str(e)}\n")
                    self.app.log_area.see("1.0")
                    logging.error(f"Java süreci sonlandırma hatası: {str(e)}")

    def get_java_path(self, server_dir):
        config_file = os.path.join(server_dir, "server_config.json")
        java_version = "17"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                java_version = config.get("java_version", "17")
            except Exception as e:
                self.app.log_area.insert("1.0", f"Sunucu yapılandırması okuma hatası: {str(e)}\n")
                self.app.log_area.see("1.0")
                logging.error(f"Sunucu yapılandırması okuma hatası: {str(e)}")

        java_dir = os.path.join("Java", f"jdk-{java_version}")
        if not os.path.exists(java_dir):
            self.app.log_area.insert("1.0", f"Java {java_version} bulunamadı, indiriliyor...\n")
            self.app.log_area.see("1.0")
            if self.app.install_tab.download_java(java_version):
                self.app.log_area.insert("1.0", f"Java {java_version} indirildi ve kuruldu.\n")
                self.app.log_area.see("1.0")
            else:
                self.app.log_area.insert("1.0", f"Hata: Java {java_version} indirilemedi.\n")
                self.app.log_area.see("1.0")
                return None

        java_bin = os.path.join(java_dir, "bin", "java.exe" if platform.system() == "Windows" else "java")
        if not os.path.exists(java_bin):
            self.app.log_area.insert("1.0", f"Hata: Java çalıştırılabilir dosyası bulunamadı: {java_bin}\n")
            self.app.log_area.see("1.0")
            logging.error(f"Java çalıştırılabilir dosyası bulunamadı: {java_bin}")
            return None
        return java_bin

    def handle_java_version_error(self, error_output, server_dir):
        match = re.search(r"class file version (\d+\.\d+)", error_output)
        if match:
            class_version = int(float(match.group(1)))
            for cv, jv in self.java_class_versions.items():
                if class_version == cv:
                    self.app.log_area.insert("1.0", f"Uyumsuz Java sürümü tespit edildi, Java {jv} indiriliyor...\n")
                    self.app.log_area.see("1.0")
                    if self.app.install_tab.download_java(jv):
                        self.app.log_area.insert("1.0", f"Java {jv} indirildi ve kuruldu.\n")
                        self.app.log_area.see("1.0")
                        self.save_server_config(server_dir, jv)
                        return True
                    else:
                        self.app.log_area.insert("1.0", f"Hata: Java {jv} indirilemedi.\n")
                        self.app.log_area.see("1.0")
                        return False
        return False

    def save_server_config(self, server_dir, java_version):
        config_file = os.path.join(server_dir, "server_config.json")
        config = {"java_version": java_version}
        with open(config_file, "w") as f:
            json.dump(config, f)
        self.app.log_area.insert("1.0", f"Sunucu yapılandırması kaydedildi: Java {java_version}\n")
        self.app.log_area.see("1.0")
        logging.info(f"Sunucu yapılandırması kaydedildi: Java {java_version}")

    def start_server(self):
        server_name = self.server_name.get()
        ram = self.ram_entry.get()
        server_dir = f"servers/{server_name}"
        port = self.get_server_port(server_dir)

        server_jar = self.find_server_jar(server_dir)
        if not server_jar:
            self.app.log_area.insert("1.0", f"Hata: {server_dir} içinde geçerli .jar dosyası bulunamadı, sunucu kuruluyor...\n")
            self.app.log_area.see("1.0")
            logging.error(f"{server_dir} içinde geçerli .jar dosyası bulunamadı, sunucu kuruluyor.")
            try:
                self.app.install_tab.install_server()
                self.app.log_area.insert("1.0", "Sunucu kurulumu tamamlandı.\n")
                self.app.log_area.see("1.0")
                logging.info("Sunucu kurulumu tamamlandı.")
                server_jar = self.find_server_jar(server_dir)
                if not server_jar:
                    self.app.log_area.insert("1.0", f"Hata: Kurulum sonrası .jar dosyası hala bulunamadı.\n")
                    self.app.log_area.see("1.0")
                    logging.error("Kurulum sonrası .jar dosyası hala bulunamadı.")
                    return
            except Exception as e:
                self.app.log_area.insert("1.0", f"Sunucu kurulum hatası: {str(e)}\n")
                self.app.log_area.see("1.0")
                logging.error(f"Sunucu kurulum hatası: {str(e)}")
                return

        try:
            ram = int(ram)
        except ValueError:
            self.app.log_area.insert("1.0", "Hata: RAM sayı olmalı.\n")
            self.app.log_area.see("1.0")
            logging.error("RAM sayı olmalı.")
            return

        if self.process and self.process.poll() is None:
            self.app.log_area.insert("1.0", "Hata: Sunucu zaten çalışıyor.\n")
            self.app.log_area.see("1.0")
            logging.error("Sunucu zaten çalışıyor.")
            return

        if not self.handle_eula(server_dir):
            return

        with open(f"{server_dir}/server.properties", "w") as f:
            f.write(f"server-port={port}\n")

        java_bin = self.get_java_path(server_dir)
        if not java_bin:
            self.status_label["text"] = "Sunucu başlatılamadı"
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            return

        try:
            self.process = subprocess.Popen(
                [java_bin, f"-Xmx{ram}M", f"-Xms{ram}M", "-jar", server_jar, "nogui"],
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.running = True
            self.status_label["text"] = "Sunucu çalışıyor"
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.app.log_area.insert("1.0", f"Sunucu başlatıldı: {server_name} (Port: {port}, JAR: {server_jar}, Java: {java_bin})\n")
            self.app.log_area.see("1.0")
            logging.info(f"Sunucu başlatıldı: {server_name} (Port: {port}, JAR: {server_jar}, Java: {java_bin})")

            threading.Thread(target=self.read_output, args=(self.process.stdout, self.output_queue), daemon=True).start()
            threading.Thread(target=self.read_error_output, args=(self.process.stderr, self.output_queue, server_dir), daemon=True).start()
            self.update_console()
        except Exception as e:
            self.status_label["text"] = "Sunucu başlatılamadı"
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.app.log_area.insert("1.0", f"Sunucu başlatma hatası: {str(e)}\n")
            self.app.log_area.see("1.0")
            logging.error(f"Sunucu başlatma hatası: {str(e)}")

    def read_error_output(self, pipe, queue, server_dir):
        error_buffer = []
        for line in iter(pipe.readline, ''):
            queue.put(line)
            error_buffer.append(line)
            if "UnsupportedClassVersionError" in line:
                error_output = "\n".join(error_buffer[-10:])
                if self.handle_java_version_error(error_output, server_dir):
                    self.process.terminate()
                    self.process.wait(timeout=10)
                    self.start_server()
                break
        pipe.close()

    def stop_server(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
                self.status_label["text"] = "Sunucu durduruldu"
                self.app.log_area.insert("1.0", "Sunucu durduruldu.\n")
                self.app.log_area.see("1.0")
                logging.info("Sunucu durduruldu.")
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.status_label["text"] = "Sunucu zorla durduruldu"
                self.app.log_area.insert("1.0", "Sunucu zorla durduruldu.\n")
                self.app.log_area.see("1.0")
                logging.info("Sunucu zorla durduruldu.")
            self.ensure_no_java_processes()
        else:
            self.app.log_area.insert("1.0", "Hata: Sunucu zaten durdurulmuş.\n")
            self.app.log_area.see("1.0")
            logging.error("Sunucu zaten durdurulmuş.")
        self.running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.console_area.configure(state="normal")
        self.console_area.delete("1.0", tk.END)
        self.console_area.configure(state="disabled")

    def restart_server(self):
        self.stop_server()
        import time
        time.sleep(2)
        self.start_server()