<?php
// ============================================================
// KONFIGURASI APLIKASI
// Sesuaikan nilai di bawah dengan environment Anda
// ============================================================

// ── MySQL ────────────────────────────────────────────────────
define('DB_HOST',     'localhost');
define('DB_USER',     'root');
define('DB_PASS',     '');
define('DB_NAME',     'rekomendasi_pestisida');
define('DB_CHARSET',  'utf8mb4');

// ── URL Python Flask API ──────────────────────────────────────
// Pastikan engine.py sedang berjalan sebelum membuka web
define('PYTHON_API_URL', 'http://localhost:5000');

// ── Nama Toko / Aplikasi ──────────────────────────────────────
define('APP_NAME',   'Sistem Rekomendasi Pestisida');
define('TOKO_NAMA',  'Toko Tani Gintung');
