# 🍓 Modul Raspi PMLD — Edge Device Agent & Dynamic Modular Platform

Repositori ini berisi kode runtime **IoT Device Agent** dan **Katalog Modul Mandiri** untuk perangkat Raspberry Pi yang mendukung konsep **Zero Touch Deployment (ZTD)** dan **Selective Module Pull (Git Sparse-Checkout)**.

---

## 🌟 Fitur Utama

*   **Zero Touch Auto-Discovery:** Perangkat mendaftarkan dirinya secara otomatis ke server cloud (VPS) saat pertama kali boot melalui topik MQTT register tanpa perlu input MAC address manual.
*   **Selective Module Pull (Hemat Memori & Kuota):** Menggunakan fitur *Git Sparse-Checkout*. Raspberry Pi **hanya mengunduh modul yang diperintahkan** oleh server. Modul lain (seperti modul kamera/AI yang berukuran besar) tidak akan pernah di-download ke kartu memori.
*   **Isolasi Virtual Environment:** Setiap modul berjalan di dalam virtual environment Python terpisah (`venv`), sehingga *dependency* antar modul tidak akan saling bertabrakan.
*   **Systemd Management:** Agen dan setiap modul yang terpasang dikelola secara otomatis sebagai daemon *systemd service* mandiri yang tahan banting (auto-restart saat reboot/crash).

---

## 📂 Struktur Repositori

```text
.
├── agent/
│   ├── main.py              # Daemon utama agen (MQTT listener & offline caching)
│   ├── module_manager.py    # Engine rekonsiliasi modul, sparse-checkout, & systemd control
│   └── requirements.txt     # Dependensi agen utama (paho-mqtt)
├── modules/
│   └── temperature/         # Contoh modul: Pembaca suhu CPU Raspberry Pi
│       ├── module.py        # Kode eksekusi modul (publish data suhu ke MQTT)
│       └── requirements.txt # Dependensi khusus modul
├── scripts/
│   └── install-agent.sh     # Skrip bootstrap otomatis saat first-boot Raspberry Pi
└── systemd/
    ├── iot-agent.service    # Unit service untuk agen utama
    └── iot-module@.service  # Template unit service systemd dinamis untuk setiap modul
```

---

## 🚀 Panduan Instalasi di Raspberry Pi (First Boot)

Setelah Raspberry Pi terhubung ke jaringan internet/Tailscale VPN, jalankan perintah bootstrap berikut di terminal Raspberry Pi:

```bash
# 1. Ekspor variabel konfigurasi yang sesuai dengan server VPS Anda
export MQTT_HOST="100.x.x.x"     # Ganti dengan IP Tailscale VPS Anda
export ROOM_ID="lab-01"          # Nama ruangan / penempatan perangkat
export REPO_URL="https://github.com/NICEganteng/modulraspipmld.git"

# 2. Unduh dan jalankan skrip instalasi otomatis
curl -sSL https://raw.githubusercontent.com/NICEganteng/modulraspipmld/main/scripts/install-agent.sh | sudo -E bash
```

### Apa yang Dilakukan Skrip Ini?
1. Meng-clone repositori ini ke `/opt/iot-platform` menggunakan **Git Sparse-Checkout** (hanya menarik folder `agent`, `scripts`, dan `systemd`). Folder `modules/` tetap kosong.
2. Menghasilkan identitas unik perangkat `/opt/iot-agent/device.json` berdasarkan hardware `/etc/machine-id` (misal: `raspi-a1b2c3`).
3. Menyiapkan virtual environment agen di `/opt/iot-agent/venv`.
4. Memasang dan mengaktifkan service daemon `iot-agent.service`.

---

## 🧩 Panduan Menambah Modul Baru (Developer Guide)

Jika Anda ingin menambahkan modul IoT baru (misal: modul kamera, sensor DHT22, atau deteksi suara):

1. **Buat Folder Modul Baru di Direktori `modules/`:**
   ```bash
   mkdir -p modules/kamera
   ```
2. **Sediakan File `module.py` dan `requirements.txt`:**
   * `modules/kamera/requirements.txt`: Tulis pustaka yang dibutuhkan saja (misal: `opencv-python-headless`).
   * `modules/kamera/module.py`: Kode utama modul. Baca konfigurasi broker dari file `/opt/iot-agent/device.json` dan publish data sensor ke topik `iot/room/{room_id}/...`.
3. **Commit dan Push ke GitHub:**
   ```bash
   git add modules/kamera
   git commit -m "feat: tambah modul kamera"
   git push origin main
   ```
4. **Deploy dari Cloud:** Modul baru Anda kini langsung bisa di-deploy ke perangkat mana pun di lapangan cukup dengan mengirimkan nama modul `kamera` pada *Desired State* di dashboard VPS!

---

## 🔍 Perintah Pengecekan & Pemecahan Masalah (Troubleshooting)

```bash
# Memeriksa status agen utama
sudo systemctl status iot-agent

# Memantau log agen secara live (real-time)
sudo journalctl -u iot-agent -f

# Memeriksa status modul tertentu (contoh: temperature)
sudo systemctl status iot-module@temperature

# Memantau log eksekusi modul tertentu
sudo journalctl -u iot-module@temperature -f

# Memeriksa identitas perangkat lokal
cat /opt/iot-agent/device.json

# Memeriksa modul apa saja yang saat ini ter-checkout di Raspi
git -C /opt/iot-platform sparse-checkout list
```
