"""
============================================================
CORE ENGINE: Sistem Rekomendasi Pestisida
Flask API — CBF + TF-IDF + Cosine Similarity
DATA SOURCE: CSV file (data/produk.csv)
============================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Sastrawi (opsional) ───────────────────────────────────────
try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
    stemmer        = StemmerFactory().create_stemmer()
    sw_remover     = StopWordRemoverFactory().create_stop_word_remover()
    SASTRAWI_READY = True
except ImportError:
    SASTRAWI_READY = False

# ── Path CSV ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, '..', 'data', 'produk.csv')

# ── Konstanta preprocessing ───────────────────────────────────
STOPWORD_TAMBAHAN = {
    'untuk','dengan','pada','dan','atau','dapat','digunakan','sebagai',
    'yang','ini','itu','dari','ke','di','sampai','serta','juga',
    'adalah','akan','agar','tersebut','sehingga','apabila','gejala',
    'cara','jika','saat','mulai','per','kali','sekali',
}
WHITELIST_KATA = {
    'insektisida','fungisida','herbisida','akarisida','rodentisida',
    'bakterisida','nematisida','sistemik','kontak','protektif','kuratif',
    'wereng','thrips','aphid','blast','antraknosa','gulma',
}

app = Flask(__name__)
CORS(app)

# ── State global ──────────────────────────────────────────────
_df           = None
_tfidf_matrix = None
_vectorizer   = None


# ============================================================
# PREPROCESSING
# ============================================================

def case_folding(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def stopword_removal(tokens):
    hasil = []
    for t in tokens:
        if t in WHITELIST_KATA:
            hasil.append(t); continue
        if t in STOPWORD_TAMBAHAN:
            continue
        if SASTRAWI_READY:
            if sw_remover.remove(t).strip():
                hasil.append(t)
        else:
            hasil.append(t)
    return hasil

def stemming(tokens):
    if not SASTRAWI_READY:
        return tokens
    return [t if t in WHITELIST_KATA else stemmer.stem(t) for t in tokens]

def preprocess(text):
    tokens = case_folding(text).split()
    tokens = stopword_removal(tokens)
    tokens = stemming(tokens)
    return ' '.join(tokens)


# ============================================================
# LOAD CSV & BUILD MODEL
# ============================================================

def load_dataset():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"File CSV tidak ditemukan: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')

    # Normalisasi nama kolom (strip spasi, lowercase)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    required = ['nama_produk', 'kategori', 'tanaman_target', 'fase_aplikasi', 'hama_penyakit']
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ada di CSV: {missing}")

    # Bersihkan kolom teks
    for col in required:
        df[col] = df[col].fillna('').astype(str).str.strip()

    df['kategori'] = df['kategori'].str.lower()

    # Kolom opsional
    for col in ['deskripsi', 'dosis_pemakaian', 'keyword', 'media_tanam']:
        if col not in df.columns:
            df[col] = ''

    for col in ['harga', 'stok']:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(r'[^0-9.\-]', '', regex=True),
            errors='coerce'
        ).fillna(0)

    df['stok'] = df['stok'].astype(int)

    # Tambah produk_id kalau belum ada
    if 'produk_id' not in df.columns:
        df.insert(0, 'produk_id', range(1, len(df) + 1))

    # Filter stok > 0
    df = df[df['stok'] > 0].reset_index(drop=True)
    return df

def gabungkan_teks(row):
    bagian = [
        str(row['kategori']),       str(row['kategori']),
        str(row['tanaman_target']), str(row['tanaman_target']),
        str(row['hama_penyakit']),  str(row['hama_penyakit']),
        str(row['fase_aplikasi']),  str(row['fase_aplikasi']),
    ]
    return ' '.join(bagian)

def build_model(df):
    df['teks_gabungan'] = df.apply(gabungkan_teks, axis=1)
    df['teks_bersih']   = df['teks_gabungan'].apply(preprocess)
    vectorizer   = TfidfVectorizer(token_pattern=r'\S+', use_idf=False, norm='l2')
    tfidf_matrix = vectorizer.fit_transform(df['teks_bersih'])
    return df, tfidf_matrix, vectorizer

def init_engine():
    global _df, _tfidf_matrix, _vectorizer
    print(f"[Engine] Membaca CSV: {CSV_PATH}")
    _df = load_dataset()
    print(f"[Engine] {len(_df)} produk dimuat.")
    _df, _tfidf_matrix, _vectorizer = build_model(_df)
    print("[Engine] Model TF-IDF selesai dibangun.")


# ============================================================
# HELPER DROPDOWN
# ============================================================

def nilai_per_kategori(df, kolom):
    hasil = {'__all__': []}
    for _, row in df.iterrows():
        kat  = str(row['kategori']).strip().lower()
        vals = [v.strip().lower() for v in str(row[kolom]).split(',') if v.strip()]
        for v in vals:
            hasil.setdefault(kat, [])
            if v not in hasil[kat]:      hasil[kat].append(v)
            if v not in hasil['__all__']: hasil['__all__'].append(v)
    for k in hasil:
        hasil[k] = sorted(hasil[k])
    return hasil


# ============================================================
# REKOMENDASI
# ============================================================

def bentuk_query(jenis='', tanaman='', opt='', fase=''):
    return ' '.join(b for b in [jenis, tanaman, opt, fase] if b.strip())

def rekomendasi(query_text, kategori_filter=None, top_n=5):
    pool = _df.copy()
    if kategori_filter and kategori_filter != '__all__':
        pool = pool[pool['kategori'] == kategori_filter.lower()]
    if pool.empty:
        return []

    idx           = pool.index.tolist()
    subset_matrix = _tfidf_matrix[idx]
    query_vector  = _vectorizer.transform([preprocess(query_text)])
    skor          = cosine_similarity(query_vector, subset_matrix).flatten()

    pool          = pool.copy()
    pool['score'] = skor
    pool          = pool[pool['score'] > 0].sort_values('score', ascending=False).head(top_n)

    kolom = ['produk_id','nama_produk','kategori','tanaman_target','hama_penyakit',
             'fase_aplikasi','deskripsi','dosis_pemakaian','harga','stok','score']
    hasil = []
    for _, row in pool.iterrows():
        item = {}
        for k in kolom:
            val = row.get(k, '')
            if isinstance(val, float) and np.isnan(val): val = ''
            elif isinstance(val, np.integer):             val = int(val)
            elif isinstance(val, np.floating):            val = round(float(val), 4)
            item[k] = val
        hasil.append(item)
    return hasil


# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status":       "ok",
        "engine_ready": _df is not None,
        "sastrawi":     SASTRAWI_READY,
        "total_produk": len(_df) if _df is not None else 0,
        "csv_path":     CSV_PATH,
    })

@app.route('/api/options', methods=['GET'])
def options():
    if _df is None:
        return jsonify({"error": "Engine belum siap"}), 503
    all_kat = sorted(_df['kategori'].replace('', pd.NA).dropna().unique().tolist())
    return jsonify({
        "kategori": all_kat,
        "tanaman":  nilai_per_kategori(_df, 'tanaman_target'),
        "opt":      nilai_per_kategori(_df, 'hama_penyakit'),
        "fase":     nilai_per_kategori(_df, 'fase_aplikasi'),
    })

@app.route('/api/recommend', methods=['POST'])
def recommend():
    if _df is None:
        return jsonify({"error": "Engine belum siap"}), 503
    data    = request.get_json(force=True)
    jenis   = data.get('jenis',   '').strip()
    tanaman = data.get('tanaman', '').strip()
    opt     = data.get('opt',     '').strip()
    fase    = data.get('fase',    '').strip()
    top_n   = int(data.get('top_n', 5))
    if not any([jenis, tanaman, opt, fase]):
        return jsonify({"error": "Pilih minimal satu atribut"}), 400
    query  = bentuk_query(jenis, tanaman, opt, fase)
    hasil  = rekomendasi(query, kategori_filter=jenis or None, top_n=top_n)
    return jsonify({"query": query, "filter": jenis or None, "count": len(hasil), "results": hasil})

@app.route('/api/reload', methods=['POST'])
def reload_engine():
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
