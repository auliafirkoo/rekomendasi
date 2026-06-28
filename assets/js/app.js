/* ============================================================
   SISTEM REKOMENDASI PESTISIDA — Frontend JS
   ============================================================ */

'use strict';

// ── KONSTANTA ─────────────────────────────────────────────────
const BRIDGE = 'api_bridge.php';   // relatif dari php/index.php
const PILIH  = '';

// ── STATE ─────────────────────────────────────────────────────
let _options = null;   // cache opsi dropdown dari engine

// ── ELEMEN ────────────────────────────────────────────────────
const ddJenis   = document.getElementById('dd-jenis');
const ddTanaman = document.getElementById('dd-tanaman');
const ddOpt     = document.getElementById('dd-opt');
const ddFase    = document.getElementById('dd-fase');
const sliderTopN = document.getElementById('slider-topn');
const topNVal    = document.getElementById('topn-val');
const btnCari    = document.getElementById('btn-cari');
const btnReset   = document.getElementById('btn-reset');
const badge      = document.getElementById('engine-badge');
const queryInfo  = document.getElementById('query-info');
const loading    = document.getElementById('loading');
const hasilSection = document.getElementById('hasil-section');
const hasilCount   = document.getElementById('hasil-count');
const hasilGrid    = document.getElementById('hasil-grid');
const emptyState   = document.getElementById('empty-state');
const errorBox     = document.getElementById('error-box');

// ── HELPERS ───────────────────────────────────────────────────

function show(el)  { el.classList.remove('hidden'); }
function hide(el)  { el.classList.add('hidden'); }
function fmt_rp(n) { return 'Rp ' + parseFloat(n).toLocaleString('id-ID'); }
function score_class(s) {
  if (s >= 0.7) return 'score-high';
  if (s >= 0.4) return 'score-medium';
  return 'score-low';
}

async function apiFetch(action, method = 'GET', data = {}) {
  const url = `${BRIDGE}?action=${action}`;
  const opts = { method };
  if (method === 'POST') {
    const fd = new FormData();
    Object.entries(data).forEach(([k, v]) => fd.append(k, v));
    opts.body = fd;
  }
  const res  = await fetch(url, opts);
  const json = await res.json();
  if (json.error && !json.results) throw new Error(json.error);
  return json;
}

// ── POPULATE DROPDOWN ─────────────────────────────────────────

function populateSelect(sel, items, placeholder) {
  sel.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach(v => {
    const o = document.createElement('option');
    o.value = v;
    o.textContent = v.charAt(0).toUpperCase() + v.slice(1);
    sel.appendChild(o);
  });
}

function updateCascade() {
  if (!_options) return;
  const kat = ddJenis.value.toLowerCase();
  const map  = key => kat ? (_options[key][kat] || []) : (_options[key]['__all__'] || []);
  populateSelect(ddTanaman, map('tanaman'),  '— Semua Tanaman —');
  populateSelect(ddOpt,     map('opt'),      '— Semua OPT —');
  populateSelect(ddFase,    map('fase'),     '— Semua Fase —');
}

// ── CEK ENGINE & LOAD OPTIONS ─────────────────────────────────

async function initEngine() {
  try {
    const health = await apiFetch('health');
    if (health.engine_ready) {
      badge.textContent = ` Engine OK · ${health.total_produk} produk`;
      badge.className   = 'badge badge-ok';
      // Load dropdown options
      _options = await apiFetch('options');
      populateSelect(ddJenis, _options.kategori, '— Semua Jenis —');
      updateCascade();
    } else {
      badge.textContent = ' Engine belum siap';
      badge.className   = 'badge badge-error';
    }
  } catch (err) {
    badge.textContent = ' Python engine tidak berjalan';
    badge.className   = 'badge badge-error';
    showError('Tidak dapat terhubung ke Python engine. Pastikan engine.py sudah dijalankan: <code>python engine.py</code>');
  }
}

// ── RENDER HASIL ──────────────────────────────────────────────

function renderHasil(results) {
  hasilGrid.innerHTML = '';

  results.forEach((p, idx) => {
    const skor = parseFloat(p.score);
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
      <div class="product-card-header">
        <div class="product-rank">#${idx + 1}</div>
        <div class="product-name">${p.nama_produk}</div>
        <span class="product-badge">${p.kategori}</span>
      </div>
      <div class="product-card-body">
        <div class="product-info-row">
          <span class="icon"></span>
          <span><strong>Tanaman:</strong>&nbsp;<span class="val">${p.tanaman_target || '-'}</span></span>
        </div>
        <div class="product-info-row">
          <span class="icon"></span>
          <span><strong>Hama/OPT:</strong>&nbsp;<span class="val">${p.hama_penyakit || '-'}</span></span>
        </div>
        <div class="product-info-row">
          <span class="icon"></span>
          <span><strong>Fase:</strong>&nbsp;<span class="val">${p.fase_aplikasi || '-'}</span></span>
        </div>
        ${p.dosis_pemakaian ? `
        <div class="product-info-row">
          <span class="icon"></span>
          <span><strong>Dosis:</strong>&nbsp;<span class="val">${p.dosis_pemakaian}</span></span>
        </div>` : ''}
        ${p.deskripsi ? `<div class="product-desc">${p.deskripsi}</div>` : ''}
      </div>
      <div class="product-card-footer">
        <div>
          <div class="product-harga">${fmt_rp(p.harga)}</div>
          <div class="product-stok">Stok: ${p.stok}</div>
        </div>
        <span class="product-score ${score_class(skor)}">
          Similarity: ${skor.toFixed(4)}
        </span>
      </div>
    `;
    hasilGrid.appendChild(card);
  });
}

// ── SHOW ERROR ────────────────────────────────────────────────

function showError(msg) {
  errorBox.innerHTML = '⚠️ ' + msg;
  show(errorBox);
  setTimeout(() => hide(errorBox), 8000);
}

function clearResults() {
  hide(hasilSection);
  hide(emptyState);
  hide(errorBox);
  hide(queryInfo);
}

// ── CARI ──────────────────────────────────────────────────────

async function cariRekomendasi() {
  const jenis   = ddJenis.value;
  const tanaman = ddTanaman.value;
  const opt     = ddOpt.value;
  const fase    = ddFase.value;
  const topN    = parseInt(sliderTopN.value, 10);

  if (!jenis && !tanaman && !opt && !fase) {
    showError('Pilih minimal satu atribut untuk mencari rekomendasi.');
    return;
  }

  clearResults();
  show(loading);
  btnCari.disabled = true;

  // Tampilkan info query
  const qParts = [jenis, tanaman, opt, fase].filter(Boolean);
  queryInfo.innerHTML = `<strong>Query:</strong> <code>${qParts.join(' · ')}</code>`
    + (jenis ? ` &nbsp;|&nbsp; <small>Filter kategori: <strong>${jenis}</strong></small>` : '');
  show(queryInfo);

  try {
    const res = await apiFetch('recommend', 'POST', { jenis, tanaman, opt, fase, top_n: topN });

    hide(loading);
    btnCari.disabled = false;

    if (!res.results || res.results.length === 0) {
      show(emptyState);
      return;
    }

    hasilCount.textContent = `Ditemukan ${res.results.length} produk yang relevan`;
    renderHasil(res.results);
    show(hasilSection);

    // Scroll ke hasil
    hasilSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    hide(loading);
    btnCari.disabled = false;
    showError(err.message || 'Terjadi kesalahan. Coba lagi.');
  }
}

// ── RESET ────────────────────────────────────────────────────

function resetForm() {
  ddJenis.value      = PILIH;
  sliderTopN.value   = 5;
  topNVal.textContent = 5;
  updateCascade();
  clearResults();
}

// ── EVENT LISTENERS ───────────────────────────────────────────

ddJenis.addEventListener('change', () => {
  updateCascade();
  clearResults();
});

sliderTopN.addEventListener('input', () => {
  topNVal.textContent = sliderTopN.value;
});

btnCari.addEventListener('click', cariRekomendasi);
btnReset.addEventListener('click', resetForm);

// Tekan Enter di select juga trigger cari
[ddJenis, ddTanaman, ddOpt, ddFase].forEach(sel => {
  sel.addEventListener('keydown', e => { if (e.key === 'Enter') cariRekomendasi(); });
});

// ── INIT ─────────────────────────────────────────────────────
initEngine();
