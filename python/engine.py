"""
============================================================
CORE ENGINE: Sistem Rekomendasi Pestisida
Flask API — CBF + TF-IDF + Cosine Similarity
============================================================
Menghubungkan PHP frontend dengan mesin rekomendasi Python.
Endpoint:
  GET  /api/options          → ambil opsi dropdown dari MySQL
  POST /api/recommend        → hitung rekomendasi
  GET  /api/health           → cek status engine
============================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import pandas as pd
import numpy as np
import re
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Opsional: Sastrawi untuk stemming Bahasa Indonesia ──────────────
# Jika Sastrawi tidak ter-install, preprocessing tetap jalan tanpa stemming
try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
    stemmer_factory  = StemmerFactory()
    stemmer          = stemmer_factory.create_stemmer()
    sw_factory       = StopWordRemoverFactory()
    sw_remover       = sw_factory.create_stop_word_remover()
    SASTRAWI_READY   = True
except ImportError:
    SASTRAWI_READY   = False

# ── Konfigurasi MySQL ─────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "rekomendasi_pestisida"),
    "charset":  "utf8mb4",
}

# ── Konstanta preprocessing ───────────────────────────────────────────
STOPWORD_TAMBAHAN = {
    'untuk', 'dengan', 'pada', 'dan', 'atau', 'dapat', 'digunakan',
    'sebagai', 'yang', 'ini', 'itu', 'dari', 'ke', 'di', 'sampai',
    'serta', 'juga', 'adalah', 'akan', 'agar', 'tersebut', 'sehingga',
    'apabila', 'gejala', 'cara', 'jika', 'saat', 'mulai', 'per',
    'kali', 'sekali',
}
WHITELIST_KATA = {
    'insektisida', 'fungisida', 'herbisida', 'akarisida', 'rodentisida',
    'bakterisida', 'nematisida', 'sistemik', 'kontak', 'protektif',
    'kuratif', 'wereng', 'thrips', 'aphid', 'blast', 'antraknosa', 'gulma',
}

app = Flask(__name__)
CORS(app)  # izinkan request dari PHP

# ── State global (di-load ulang setiap restart) ───────────────────────
_df           = None
_tfidf_matrix = None
_vectorizer   = None


# ============================================================
# PREPROCESSING
# ============================================================

def case_folding(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def stopword_removal(tokens: list) -> list:
    hasil = []
    for token in tokens:
        if token in WHITELIST_KATA:
            hasil.append(token)
            continue
        if token in STOPWORD_TAMBAHAN:
            continue
        if SASTRAWI_READY:
            cek = sw_remover.remove(token)
            if cek.strip():
                hasil.append(token)
        else:
            hasil.append(token)
    return hasil


def stemming(tokens: list) -> list:
    if not SASTRAWI_READY:
        return tokens
    hasil = []
    for token in tokens:
        if token in WHITELIST_KATA:
            hasil.append(token)
        else:
            hasil.append(stemmer.stem(token))
    return hasil


def preprocess(text: str) -> str:
    text   = case_folding(text)
    tokens = text.split()
    tokens = stopword_removal(tokens)
    tokens = stemming(tokens)
    return ' '.join(tokens)


# ============================================================
# DATASET & MODEL
# ============================================================

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def load_dataset() -> pd.DataFrame:
    conn   = get_db_connection()
    query  = "SELECT * FROM produk WHERE stok > 0 ORDER BY produk_id"
    df     = pd.read_sql(query, conn)
    conn.close()

    # Bersihkan kolom teks
    for col in ['kategori', 'tanaman_target', 'hama_penyakit', 'fase_aplikasi', 'nama_produk']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    df['kategori'] = df['kategori'].str.lower()
    return df


def gabungkan_teks(row) -> str:
    """Buat corpus per produk dari 4 kolom atribut (masing-masing bobot 2x)."""
    bagian = [
        str(row['kategori']),       str(row['kategori']),
        str(row['tanaman_target']), str(row['tanaman_target']),
        str(row['hama_penyakit']),  str(row['hama_penyakit']),
        str(row['fase_aplikasi']),  str(row['fase_aplikasi']),
    ]
    return ' '.join(bagian)


def build_model(df: pd.DataFrame):
    """Fit TF-IDF dari dataset yang sudah dimuat."""
    df['teks_gabungan'] = df.apply(gabungkan_teks, axis=1)
    df['teks_bersih']   = df['teks_gabungan'].apply(preprocess)

    vectorizer = TfidfVectorizer(
        token_pattern=r'\S+',
        use_idf=False,   # TF saja (lihat penjelasan di notebook)
        norm='l2',
    )
    tfidf_matrix = vectorizer.fit_transform(df['teks_bersih'])
    return df, tfidf_matrix, vectorizer


def init_engine():
    """Muat dataset dari MySQL dan build model TF-IDF."""
    global _df, _tfidf_matrix, _vectorizer
    print("[Engine] Memuat dataset dari MySQL...")
    _df = load_dataset()
    print(f"[Engine] {len(_df)} produk dimuat.")
    _df, _tfidf_matrix, _vectorizer = build_model(_df)
    print("[Engine] Model TF-IDF selesai dibangun.")


# ============================================================
# HELPER: DROPDOWN OPTIONS
# ============================================================

def ambil_nilai_unik(df: pd.DataFrame, kolom: str) -> list:
    semua = []
    for isi in df[kolom]:
        for bagian in str(isi).split(','):
            b = bagian.strip().lower()
            if b:
                semua.append(b)
    return sorted(set(semua))


def nilai_per_kategori(df: pd.DataFrame, kolom: str) -> dict:
    hasil = {'__all__': []}
    for _, row in df.iterrows():
        kat  = str(row['kategori']).strip().lower()
        vals = [v.strip().lower() for v in str(row[kolom]).split(',') if v.strip()]
        for v in vals:
            if kat and v not in hasil.get(kat, []):
                hasil.setdefault(kat, []).append(v)
            if v not in hasil['__all__']:
                hasil['__all__'].append(v)
    for k in hasil:
        hasil[k] = sorted(hasil[k])
    return hasil


# ============================================================
# REKOMENDASI
# ============================================================

def bentuk_query(jenis='', tanaman='', opt='', fase='') -> str:
    bagian = [b for b in [jenis, tanaman, opt, fase] if b.strip()]
    return ' '.join(bagian)


def rekomendasi(query_text: str, kategori_filter: str = None, top_n: int = 5) -> list:
    global _df, _tfidf_matrix, _vectorizer

    pool = _df.copy()
    if kategori_filter and kategori_filter.lower() != '__all__':
        pool = pool[pool['kategori'] == kategori_filter.lower()]

    if pool.empty:
        return []

    idx            = pool.index.tolist()
    subset_matrix  = _tfidf_matrix[idx]
    query_bersih   = preprocess(query_text)
    query_vector   = _vectorizer.transform([query_bersih])
    skor           = cosine_similarity(query_vector, subset_matrix).flatten()

    pool           = pool.copy()
    pool['score']  = skor
    pool           = pool[pool['score'] > 0]
    pool           = pool.sort_values('score', ascending=False).head(top_n)

    kolom = ['produk_id', 'nama_produk', 'kategori', 'tanaman_target',
             'hama_penyakit', 'fase_aplikasi', 'deskripsi', 'dosis_pemakaian',
             'harga', 'stok', 'score']

    hasil = []
    for _, row in pool.iterrows():
        item = {}
        for k in kolom:
            val = row.get(k, '')
            if isinstance(val, float) and np.isnan(val):
                val = ''
            elif isinstance(val, (np.integer,)):
                val = int(val)
            elif isinstance(val, (np.floating,)):
                val = round(float(val), 4)
            item[k] = val
        hasil.append(item)

    return hasil


# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/health', methods=['GET'])
def health():
    status = {
        "status":        "ok",
        "engine_ready":  _df is not None,
        "sastrawi":      SASTRAWI_READY,
        "total_produk":  len(_df) if _df is not None else 0,
    }
    return jsonify(status)


@app.route('/api/options', methods=['GET'])
def options():
    """Kembalikan opsi dropdown berdasarkan dataset aktif di MySQL."""
    if _df is None:
        return jsonify({"error": "Engine belum siap"}), 503

    all_kat = sorted(_df['kategori'].replace('', pd.NA).dropna().unique().tolist())

    map_tanaman = nilai_per_kategori(_df, 'tanaman_target')
    map_opt     = nilai_per_kategori(_df, 'hama_penyakit')
    map_fase    = nilai_per_kategori(_df, 'fase_aplikasi')

    return jsonify({
        "kategori": all_kat,
        "tanaman":  map_tanaman,
        "opt":      map_opt,
        "fase":     map_fase,
    })


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """Hitung rekomendasi berdasarkan pilihan dropdown."""
    if _df is None:
        return jsonify({"error": "Engine belum siap"}), 503

    data     = request.get_json(force=True)
    jenis    = data.get('jenis',   '').strip()
    tanaman  = data.get('tanaman', '').strip()
    opt      = data.get('opt',     '').strip()
    fase     = data.get('fase',    '').strip()
    top_n    = int(data.get('top_n', 5))

    if not any([jenis, tanaman, opt, fase]):
        return jsonify({"error": "Pilih minimal satu atribut"}), 400

    query  = bentuk_query(jenis, tanaman, opt, fase)
    hasil  = rekomendasi(query, kategori_filter=jenis or None, top_n=top_n)

    return jsonify({
        "query":   query,
        "filter":  jenis or None,
        "count":   len(hasil),
        "results": hasil,
    })


@app.route('/api/reload', methods=['POST'])
def reload_engine():
    """Reload dataset (misal setelah update data di MySQL)."""
    try:
        init_engine()
        return jsonify({"status": "ok", "total_produk": len(_df)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    init_engine()
    app.run(host='0.0.0.0', port=5000, debug=False)
