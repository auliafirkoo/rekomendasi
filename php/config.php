<?php
// ============================================================
// KONFIGURASI APLIKASI
// Tidak ada MySQL — data dibaca dari CSV oleh Python engine
// ============================================================

// ── URL Python Flask API ──────────────────────────────────────
// Jalankan python/engine.py dulu sebelum membuka web
define('PYTHON_API_URL', 'http://localhost:5000');

// ── Nama Toko / Aplikasi ──────────────────────────────────────
define('APP_NAME',   'Sistem Rekomendasi Pestisida');
define('TOKO_NAMA',  'Toko Tani Gintung');
