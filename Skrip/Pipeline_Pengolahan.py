"""Pipeline pengolahan Project Penambangan Data - Puskesmas Sei Lekop.

MODEL UTAMA: 11 wilayah, Ward + Hellinger, k=2; fitur dihitung PER BARIS DIAGNOSIS (1 kode ICD-3 klinis = 1 hitungan).
Membaca 34 berkas data mentah tahun 2025 yang SUDAH DISAMARKAN (Mentah_2401020017, setelah diekstrak),
lalu menghasilkan master anonim, matriks fitur, dan hasil Ward Hierarchical Clustering.

Pemakaian:
    pip install pandas numpy scikit-learn openpyxl scipy
    python Pipeline_Pengolahan.py <folder_berkas_xlsx> [--bootstrap]

Catatan: skrip tidak membutuhkan tabel pemetaan kode samaran dan tidak menulis data pasien.
"""
import sys, re, glob, os
import numpy as np, pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score

# urutan wilayah mengikuti Tabel 3.1 laporan (dipakai agar bootstrap dapat direproduksi)
ORDER = ['SUNGAI LEKOP','GUNUNG LENGKUAS','GUNUNG KIJANG','KIJANG KOTA','BATU SEMBILAN','PINANG KENCANA','TOAPAYA SELATAN','SUNGAI ENAM','TANJUNG AYUN SAKTI','KAWAL','SEI JANG']
GROUP_ORDER = ['J','K','I','E','R','M','L','S_T','A_B','H0_59','LAINNYA']
ALL19 = ['J','K','I','E','R','M','L','S_T','A_B','H0_59','G','TELINGA','N','F','O','NEO','DARAH','P','Q']
VALID = re.compile(r'^[A-Z]\d{2}(\.\d{1,2})?$')

def group_of(c3):
    L = c3[0]; n = int(c3[1:3]) if c3[1:3].isdigit() else -1
    if L in 'AB': return 'A_B'
    if L == 'C': return 'NEO'
    if L == 'D': return 'NEO' if n <= 48 else 'DARAH'
    if L in 'EFGIJKLMNOPQR': return L
    if L == 'H': return 'H0_59' if n <= 59 else 'TELINGA'
    if L in 'ST': return 'S_T'
    return None                       # Z, U, V-Y bukan kelompok klinis

def parse_codes(s):
    if pd.isna(s): return [], []
    full = [x.strip().upper() for x in re.split(r'[+|;,]', str(s)) if x.strip()]
    valid = list(dict.fromkeys(x for x in full if VALID.match(x)))
    return valid, list(dict.fromkeys(x[:3] for x in valid))

def load(folder):
    frames = []
    for f in sorted(glob.glob(os.path.join(folder, '*.xlsx'))):
        raw = pd.read_excel(f, header=None)
        h = raw.index[raw.iloc[:, 0].astype(str).str.strip().isin(['No.', 'No'])][0]
        d = raw.iloc[h + 1:].copy(); d.columns = ['No.' if str(c).strip() == 'No' else c for c in raw.iloc[h].tolist()]
        frames.append(d.dropna(subset=['No.']))
    return pd.concat(frames, ignore_index=True)

def build_master(D):
    cols = [c for c in D.columns if c != 'No.']          # seluruh kolom, termasuk kode pasien samaran
    n0 = len(D); D = D.drop_duplicates(subset=cols, keep='first'); dup = n0 - len(D)
    D['kel'] = D['Kelurahan'].astype(str).str.upper().str.replace(r'\s+', ' ', regex=True).str.strip()
    D.loc[D['Kelurahan'].isna() | D['kel'].isin(['', 'NAN', 'NONE']), 'kel'] = 'TIDAK DIISI'
    D['tahun'] = pd.to_datetime(D['Tanggal']).dt.year
    D['bulan'] = pd.to_datetime(D['Tanggal']).dt.strftime('%Y-%m')
    p = D['Kode Diagnosa'].map(parse_codes)
    D['icd3'] = p.map(lambda x: x[1])
    D['groups'] = D['icd3'].map(lambda l: sorted({g for g in (group_of(c) for c in l) if g}))
    D['cg'] = D['icd3'].map(lambda l: [g for g in (group_of(c) for c in l) if g])   # satu elemen per kode klinis (per diagnosis)
    D['klinis'] = D['groups'].map(bool)
    return D, dup

def feature_matrix(M, year=2025, min_total=30):
    tot = M[M.kel != 'TIDAK DIISI'].groupby('kel').size()
    cand = tot[tot >= min_total].index
    clin = M[(M.tahun == year) & M.klinis & M.kel.isin(cand)]
    rows = {}
    for k, g in clin.groupby('kel'):
        c = {f: 0 for f in GROUP_ORDER}
        for gl in g['cg']:                      # per baris diagnosis: kode berbeda pada bab sama dihitung dua kali
            for x in gl: c[x if x in c else 'LAINNYA'] += 1
        rows[k] = c
    F = pd.DataFrame(rows).T[GROUP_ORDER]
    return F, clin.groupby('kel').size()

def ward_report(P, label):
    X = np.sqrt(P.values)
    for k in range(2, 6):
        lab = AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(X)
        print(f'{label} k={k}: silhouette={silhouette_score(X, lab):.4f} DB={davies_bouldin_score(X, lab):.4f} ukuran={sorted(np.bincount(lab).tolist())}')

def bootstrap(clin, wil, fs='11', sqrt=True, n=200, seed=888):
    """Bootstrap atas kunjungan klinis per wilayah; fitur dihitung per baris diagnosis (list 'cg' = satu elemen per kode)."""
    cols = ALL19 if fs == '19' else GROUP_ORDER
    key = (lambda x: x) if fs == '19' else (lambda x: x if x in GROUP_ORDER[:-1] else 'LAINNYA')
    def prop(lists):
        c = {f: 0 for f in cols}
        for gl in lists:
            for x in gl: c[key(x)] += 1
        v = np.array([c[f] for f in cols], float); return v / v.sum()
    groups = {w: clin[clin.kel == w]['cg'].tolist() for w in wil}
    P0 = np.array([prop(groups[w]) for w in wil]); X0 = np.sqrt(P0) if sqrt else P0
    base = AgglomerativeClustering(2, linkage='ward').fit_predict(X0)
    rng = np.random.RandomState(seed); aris, sing, sils = [], 0, []
    for _ in range(n):
        rows = []
        for w in wil:
            g = groups[w]; idx = rng.randint(0, len(g), len(g)); rows.append(prop([g[i] for i in idx]))
        X = np.sqrt(np.array(rows)) if sqrt else np.array(rows); lab = AgglomerativeClustering(2, linkage='ward').fit_predict(X)
        aris.append(adjusted_rand_score(base, lab)); sing += int(min(np.bincount(lab)) == 1)
        if len(set(lab)) > 1: sils.append(silhouette_score(X, lab))
    return dict(n=len(wil), sil=float(silhouette_score(X0, base)), ari_mean=float(np.mean(aris)), ari_median=float(np.median(aris)), singleton_pct=sing / n * 100, sil_boot=float(np.mean(sils)))


if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 else '.'
    D = load(folder); M, dup = build_master(D)
    print('baris sumber', len(D), '| duplikat', dup, '| master', len(M), '| 2025:', int((M.tahun == 2025).sum()))
    F, ncl = feature_matrix(M); P = F.div(F.sum(axis=1), axis=0)
    sel9 = ncl[ncl >= 30].index
    print('kunjungan klinis 11 kandidat', int(ncl.sum()), '| 9 wilayah', int(ncl[sel9].sum()))
    sel9 = [w for w in ORDER if w in set(sel9)]; P = P.loc[ORDER]
    ward_report(P.loc[sel9], '9 wilayah'); ward_report(P, '11 wilayah')
    if len(sys.argv) > 2 and sys.argv[2] == '--bootstrap':
        # MODEL UTAMA = 11 wilayah (total kunjungan >= 30); 9 wilayah = pembanding; skenario lain = analisis sensitivitas
        import json
        clin = M[(M.tahun == 2025) & M.klinis]; w9 = [w for w in ORDER if w in set(sel9)]
        nclin = clin.groupby('kel').size(); w5 = [w for w in ORDER if nclin.get(w, 0) >= 50]
        scen = {'11': (list(ORDER), '11', True), '9': (w9, '11', True), '12': (list(ORDER) + ['AIR RAJA'], '11', True),
                '9_19bab': (w9, '19', True), '9_mentah': (w9, '11', False), '5': (w5, '11', True)}
        out = {}
        for k_, (wil, fs, sq) in scen.items():
            out[k_] = bootstrap(clin, wil, fs, sq); r = out[k_]
            print(f"bootstrap 200x (seed 888) {k_:9s} n={r['n']:2d}: silhouette={r['sil']:.4f} ARI rerata={r['ari_mean']:.4f}, median={r['ari_median']:.4f}, singleton={r['singleton_pct']:.1f}%, silhouette bootstrap={r['sil_boot']:.4f}")
        json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hasil_bootstrap.json'), 'w'), indent=1)
