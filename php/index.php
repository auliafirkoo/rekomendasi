<?php require_once __DIR__ . '/config.php'; ?>
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title><?= APP_NAME ?> — <?= TOKO_NAMA ?></title>
  <link rel="stylesheet" href="../assets/css/style.css" />
</head>
<body>

<!-- ── HEADER ──────────────────────────────────────────────── -->
<header class="site-header">
  <div class="header-inner">
    <div class="header-logo img">
      <img src="../assets/logo.png" alt="Tanya Pak Tani" />
    </div>
    <div>
      <h1><?= APP_NAME ?></h1>
      <p> Tanya Pak Tani</p>
      <p><?= TOKO_NAMA ?> &mdash; Content-Based Filtering · TF-IDF · Cosine Similarity</p>
    </div>
    <div id="engine-badge" class="badge badge-loading">Memeriksa engine…</div>
  </div>
</header>

<!-- ── MAIN ────────────────────────────────────────────────── -->
<main class="container">

  <!-- FORM -->
  <section class="card form-card">
    <h2 class="card-title">🔍 Cari Rekomendasi Pestisida</h2>
    <p class="card-subtitle">Pilih minimal satu atribut — dropdown di bawah otomatis menyesuaikan pilihan yang tersedia.</p>

    <div class="form-grid">

      <!-- Jenis Pestisida -->
      <div class="form-group">
        <label for="dd-jenis">Jenis Pestisida</label>
        <select id="dd-jenis" name="jenis">
          <option value="">— Semua Jenis —</option>
        </select>
      </div>

      <!-- Tanaman Target -->
      <div class="form-group">
        <label for="dd-tanaman">Tanaman Target</label>
        <select id="dd-tanaman" name="tanaman">
          <option value="">— Semua Tanaman —</option>
        </select>
      </div>

      <!-- OPT / Hama-Penyakit -->
      <div class="form-group">
        <label for="dd-opt">OPT / Hama-Penyakit</label>
        <select id="dd-opt" name="opt">
          <option value="">— Semua OPT —</option>
        </select>
      </div>

      <!-- Fase Aplikasi -->
      <div class="form-group">
        <label for="dd-fase">Fase Aplikasi</label>
        <select id="dd-fase" name="fase">
          <option value="">— Semua Fase —</option>
        </select>
      </div>

    </div><!-- .form-grid -->

    <!-- Jumlah Hasil -->
    <div class="topn-row">
      <label for="slider-topn">Tampilkan <strong id="topn-val">5</strong> hasil teratas</label>
      <input type="range" id="slider-topn" min="1" max="10" value="5" />
    </div>

    <div class="btn-row">
      <button id="btn-cari" class="btn btn-primary">🔍 Cari Rekomendasi</button>
      <button id="btn-reset" class="btn btn-secondary">🔄 Reset</button>
    </div>

    <!-- Info query -->
    <div id="query-info" class="query-info hidden"></div>
  </section>

  <!-- LOADING -->
  <div id="loading" class="loading hidden">
    <div class="spinner"></div>
    <span>Menghitung rekomendasi…</span>
  </div>

  <!-- HASIL -->
  <section id="hasil-section" class="hidden">
    <h2 class="section-title">📋 Hasil Rekomendasi</h2>
    <div id="hasil-count" class="hasil-count"></div>
    <div id="hasil-grid" class="hasil-grid"></div>
  </section>

  <!-- EMPTY STATE -->
  <div id="empty-state" class="empty-state hidden">
    <div class="empty-icon">🌱</div>
    <p>Tidak ada produk yang cocok dengan pilihan Anda.<br>Coba ubah kombinasi atribut.</p>
  </div>

  <!-- ERROR -->
  <div id="error-box" class="error-box hidden"></div>

</main>

<!-- ── FOOTER ───────────────────────────────────────────────── -->
<footer class="site-footer">
  <p><?= TOKO_NAMA ?> &copy; <?= date('Y') ?> &mdash; Sistem Rekomendasi Pestisida berbasis CBF · TF-IDF · Cosine Similarity</p>
</footer>

<script src="../assets/js/app.js"></script>
</body>
</html>
