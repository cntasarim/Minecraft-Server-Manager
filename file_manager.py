# file_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
import shutil

class FileManager:
    def __init__(self, parent, log_area):
        self.frame = ttk.Frame(parent)
        self.log_area = log_area
        self.current_file = None
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        main_frame.columnconfigure(1, weight=3)  # Sağ alan daha büyük
        main_frame.rowconfigure(0, weight=1)

        # Sol taraf: Dosya listesi
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

        ttk.Label(left_frame, text="Config Dosyaları:").pack(anchor="w")
        self.file_list = tk.Listbox(left_frame, width=40, height=25)
        self.file_list.pack(fill="y", pady=5)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.file_list.bind("<<ListboxSelect>>", self.load_file)

        # Sağ taraf: Dosya içeriği
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        content_header = ttk.Frame(right_frame)
        content_header.pack(fill="x")
        ttk.Label(content_header, text="Dosya İçeriği:").pack(side="left", anchor="w")
        ttk.Button(content_header, text="Kaydet", command=self.save_file).pack(side="left", padx=5)

        self.content_area = tk.Text(right_frame, width=80, height=25, wrap="none")
        self.content_area.pack(fill="both", expand=True, pady=5)
        x_scrollbar = ttk.Scrollbar(right_frame, orient="horizontal", command=self.content_area.xview)
        x_scrollbar.pack(fill="x")
        y_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.content_area.yview)
        y_scrollbar.pack(side="right", fill="y")
        self.content_area.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        # Alt kısım: İşlem butonları
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Button(button_frame, text="Dosya Sil", command=self.delete_file).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Dosya Ekle", command=self.add_file).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Klasör Ekle", command=self.add_folder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Yenile", command=self.refresh_files).pack(side="left", padx=5)

        self.refresh_files()

    def refresh_files(self):
        self.file_list.delete(0, tk.END)
        server_dir = "servers/server1"
        if not os.path.exists(server_dir):
            self.log_area.insert("1.0", f"Hata: {server_dir} bulunamadı.\n")
            self.log_area.see("1.0")
            logging.error(f"{server_dir} bulunamadı.")
            return

        for root, dirs, files in os.walk(server_dir):
            for file in files:
                if file.endswith((".yml", ".json", ".txt", ".properties")):
                    rel_path = os.path.relpath(os.path.join(root, file), server_dir)
                    self.file_list.insert(tk.END, rel_path)
            for dir in dirs:
                rel_path = os.path.relpath(os.path.join(root, dir), server_dir)
                self.file_list.insert(tk.END, rel_path)

        self.log_area.insert("1.0", "Dosya listesi yenilendi.\n")
        self.log_area.see("1.0")
        logging.info("Dosya listesi yenilendi.")

    def load_file(self, event):
        selection = self.file_list.curselection()
        if not selection:
            return
        file_path = self.file_list.get(selection[0])
        full_path = os.path.join("servers/server1", file_path)
        if os.path.isfile(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.content_area.delete("1.0", tk.END)
                self.content_area.insert("1.0", content)
                self.current_file = full_path
                self.log_area.insert("1.0", f"Dosya yüklendi: {file_path}\n")
                self.log_area.see("1.0")
                logging.info(f"Dosya yüklendi: {file_path}")
            except Exception as e:
                self.log_area.insert("1.0", f"Dosya yükleme hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Dosya yükleme hatası: {str(e)}")
        else:
            self.content_area.delete("1.0", tk.END)
            self.current_file = None
            self.log_area.insert("1.0", f"Seçilen öğe dosya değil: {file_path}\n")
            self.log_area.see("1.0")
            logging.info(f"Seçilen öğe dosya değil: {file_path}")

    def save_file(self):
        if not self.current_file:
            self.log_area.insert("1.0", "Hata: Kaydedilecek dosya seçilmedi.\n")
            self.log_area.see("1.0")
            logging.error("Kaydedilecek dosya seçilmedi.")
            return
        try:
            content = self.content_area.get("1.0", tk.END).rstrip()
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.log_area.insert("1.0", f"Dosya kaydedildi: {self.current_file}\n")
            self.log_area.see("1.0")
            logging.info(f"Dosya kaydedildi: {self.current_file}")
        except Exception as e:
            self.log_area.insert("1.0", f"Dosya kaydetme hatası: {str(e)}\n")
            self.log_area.see("1.0")
            logging.error(f"Dosya kaydetme hatası: {str(e)}")

    def delete_file(self):
        selection = self.file_list.curselection()
        if not selection:
            self.log_area.insert("1.0", "Hata: Silinecek dosya seçilmedi.\n")
            self.log_area.see("1.0")
            logging.error("Silinecek dosya seçilmedi.")
            return
        file_path = self.file_list.get(selection[0])
        full_path = os.path.join("servers/server1", file_path)
        if messagebox.askyesno("Silme Onayı", f"{file_path} silinsin mi?"):
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    self.log_area.insert("1.0", f"Dosya silindi: {file_path}\n")
                    self.log_area.see("1.0")
                    logging.info(f"Dosya silindi: {file_path}")
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                    self.log_area.insert("1.0", f"Klasör silindi: {file_path}\n")
                    self.log_area.see("1.0")
                    logging.info(f"Klasör silindi: {file_path}")
                self.refresh_files()
                self.content_area.delete("1.0", tk.END)
                self.current_file = None
            except Exception as e:
                self.log_area.insert("1.0", f"Silme hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Silme hatası: {str(e)}")

    def add_file(self):
        file_name = tk.simpledialog.askstring("Dosya Ekle", "Dosya adı (uzantı ile):")
        if file_name:
            full_path = os.path.join("servers/server1", file_name)
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("")
                self.refresh_files()
                self.log_area.insert("1.0", f"Dosya oluşturuldu: {file_name}\n")
                self.log_area.see("1.0")
                logging.info(f"Dosya oluşturuldu: {file_name}")
            except Exception as e:
                self.log_area.insert("1.0", f"Dosya oluşturma hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Dosya oluşturma hatası: {str(e)}")

    def add_folder(self):
        folder_name = tk.simpledialog.askstring("Klasör Ekle", "Klasör adı:")
        if folder_name:
            full_path = os.path.join("servers/server1", folder_name)
            try:
                os.makedirs(full_path, exist_ok=True)
                self.refresh_files()
                self.log_area.insert("1.0", f"Klasör oluşturuldu: {folder_name}\n")
                self.log_area.see("1.0")
                logging.info(f"Klasör oluşturuldu: {folder_name}")
            except Exception as e:
                self.log_area.insert("1.0", f"Klasör oluşturma hatası: {str(e)}\n")
                self.log_area.see("1.0")
                logging.error(f"Klasör oluşturma hatası: {str(e)}")