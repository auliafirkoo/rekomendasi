# 🌾 Sistem Rekomendasi Pestisida
**Content-Based Filtering · TF-IDF · Cosine Similarity**  
*Toko Tani Gintung*

---

## 📁 Struktur Folder

```
rekomendasi-pestisida/
│
├── python/
│   ├── engine.py           ← Core AI engine (Flask API)
│   └── requirements.txt    ← Daftar library Python
│
├── php/
│   ├── index.php           ← Halaman utama web
│   ├── api_bridge.php      ← Jembatan PHP → Python
│   └── config.php          ← Konfigurasi DB & API
│
├── sql/
│   └── dataproduk.sql      ← Schema + contoh data MySQL
│
├── assets/
│   ├── css/
│   │   └── style.css       ← Tampilan web
│   └── js/
│       └── app.js          ← Logika frontend
│
└── README.md               ← Panduan ini
```

---

## ⚙️ Cara Setup & Menjalankan

### 1. Import Database MySQL

1. Buka **phpMyAdmin** atau **MySQL Workbench** / **VSCode SQLTools**
2. Buat database baru bernama `rekomendasi_pestisida`
3. Import file `sql/dataproduk.sql`
4. Isi / ganti data di tabel `produk` sesuai data pestisida Anda

### 2. Konfigurasi

Edit file `php/config.php`:
```php
define('DB_HOST',        'localhost');   // host MySQL
define('DB_USER',        'root');        // user MySQL
define('DB_PASS',        '');            // password MySQL
define('DB_NAME',        'rekomendasi_pestisida');
define('PYTHON_API_URL', 'http://localhost:5000');  // port Flask
```

Edit file `python/engine.py` bagian `DB_CONFIG` (atau set environment variable):
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",
    "database": "rekomendasi_pestisida",
}
```

### 3. Install Library Python

Buka terminal di folder `python/`:
```bash
pip install -r requirements.txt
```

> Jika PySastrawi gagal install, sistem tetap berjalan tanpa stemming Bahasa Indonesia.

### 4. Jalankan Python Engine

```bash
cd python
python engine.py
```

Engine berjalan di `http://localhost:5000`. Biarkan terminal ini tetap terbuka.

### 5. Jalankan Web PHP

Gunakan salah satu cara berikut:

**Opsi A — XAMPP / Laragon:**
- Salin seluruh folder `rekomendasi-pestisida/` ke `htdocs/`
- Buka browser: `http://localhost/rekomendasi-pestisida/php/index.php`

**Opsi B — PHP Built-in Server (VSCode Terminal):**
```bash
cd php
php -S localhost:8080
```
Buka browser: `http://localhost:8080/index.php`

---

## 🔄 Alur Kerja Sistem

```
Browser (HTML/JS)
      ↓ AJAX fetch
php/api_bridge.php          ← PHP menerima request dari browser
      ↓ HTTP/cURL
python/engine.py (Flask)    ← Python menghitung TF-IDF + Cosine Similarity
      ↓ Query
MySQL (tabel produk)        ← Data produk pestisida
```

---

## 🗃️ Struktur Tabel `produk`

| Kolom           | Tipe          | Keterangan                              |
|-----------------|---------------|-----------------------------------------|
| `produk_id`     | INT (PK)      | ID unik produk                          |
| `nama_produk`   | VARCHAR(255)  | Nama merek produk                       |
| `kategori`      | VARCHAR(100)  | insektisida / fungisida / herbisida     |
| `tanaman_target`| VARCHAR(255)  | Multi-nilai dipisah koma                |
| `fase_aplikasi` | VARCHAR(255)  | Multi-nilai dipisah koma                |
| `hama_penyakit` | VARCHAR(255)  | Multi-nilai dipisah koma                |
| `media_tanam`   | VARCHAR(255)  | Opsional                                |
| `dosis_pemakaian`| TEXT         | Opsional                                |
| `keyword`       | TEXT          | Kata kunci tambahan (tidak masuk TF-IDF)|
| `deskripsi`     | TEXT          | Deskripsi lengkap                       |
| `harga`         | DECIMAL(12,2) | Harga satuan                            |
| `stok`          | INT           | Jumlah stok (0 = tidak tampil)          |

---

## 🔧 API Endpoint Python

| Endpoint         | Method | Fungsi                                    |
|------------------|--------|-------------------------------------------|
| `/api/health`    | GET    | Cek status engine                         |
| `/api/options`   | GET    | Ambil opsi dropdown dari dataset          |
| `/api/recommend` | POST   | Hitung rekomendasi (JSON body)            |
| `/api/reload`    | POST   | Reload dataset setelah update MySQL       |

**Contoh POST `/api/recommend`:**
```json
{
  "jenis":   "insektisida",
  "tanaman": "cabai",
  "opt":     "lalat buah",
  "fase":    "",
  "top_n":   5
}
```

---

## 💡 Tips

- **Setelah menambah/mengubah data di MySQL**, klik reload engine atau restart `engine.py`
- **Cascade dropdown** otomatis memfilter opsi berdasarkan Jenis Pestisida yang dipilih
- **Skor similarity** ≥ 0.7 = sangat relevan (hijau), 0.4–0.7 = cukup relevan (kuning), < 0.4 = kurang relevan (merah)
- Produk dengan `stok = 0` tidak akan muncul di hasil

---

## 🛠️ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Badge merah "Python engine tidak berjalan" | Jalankan `python engine.py` dulu di terminal |
| Dropdown kosong | Periksa koneksi MySQL di `config.php` dan `engine.py` |
| Skor similarity sangat rendah | Pastikan nilai kolom `kategori`, `tanaman_target`, dll konsisten (huruf kecil, tidak ada typo) |
| cURL error di PHP | Pastikan ekstensi `php_curl` aktif di `php.ini` |
