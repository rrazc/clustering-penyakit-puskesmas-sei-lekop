"""Bangun ulang matriks, model Ward, evaluasi, dan bootstrap dengan hitungan PER DIAGNOSIS (1 baris = 1 kode ICD-3 klinis).
Sumber: Data_Siap_Mining/Master_Kunjungan_Anonim.csv  ->  python Bangun_Model_PerDiagnosis.py <folder_paket>
Keluaran: hasil_model.json + matriks CSV di Data_Siap_Mining/. Bootstrap dibaca dari hasil_bootstrap.json (dibuat oleh Pipeline_Pengolahan.py --bootstrap)."""
import sys, os, json, re
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
ORDER = ['SUNGAI LEKOP','GUNUNG LENGKUAS','GUNUNG KIJANG','KIJANG KOTA','BATU SEMBILAN','PINANG KENCANA','TOAPAYA SELATAN','SUNGAI ENAM','TANJUNG AYUN SAKTI','KAWAL','SEI JANG']
GO = ['J','K','I','E','R','M','L','S_T','A_B','H0_59','LAINNYA']
ALL19 = ['J','K','I','E','R','M','L','S_T','A_B','H0_59','G','TELINGA','N','F','O','NEO','DARAH','P','Q']
LABEL = {'J':'Pernapasan (J)','K':'Pencernaan (K)','I':'Sirkulasi (I)','E':'Endokrin (E)','R':'Gejala/tanda (R)','M':'Otot-tulang (M)','L':'Kulit (L)','S_T':'Cedera (S–T)','A_B':'Infeksi (A–B)','H0_59':'Mata (H00–H59)','LAINNYA':'Kategori lain'}

def group_of(c3):
    L = c3[0]; n = int(c3[1:3]) if c3[1:3].isdigit() else -1
    if L in 'AB': return 'A_B'
    if L == 'C': return 'NEO'
    if L == 'D': return 'NEO' if n <= 48 else 'DARAH'
    if L in 'EFGIJKLMNOPQR': return L
    if L == 'H': return 'H0_59' if n <= 59 else 'TELINGA'
    if L in 'ST': return 'S_T'
    return None

def load_rows():
    m = pd.read_csv(os.path.join(ROOT, 'Data_Siap_Mining', 'Master_Kunjungan_Anonim.csv'))
    k = m[m.ada_kode_klinis == 1].copy()
    k['kode_icd3'] = k.kode_icd3.str.split(r'\s*\|\s*')
    e = k.explode('kode_icd3'); e['g'] = e.kode_icd3.map(group_of)
    return e[e.g.notna()].reset_index(drop=True)          # buang kode Z/U/V-Y yang menumpang pada kunjungan klinis

def feat(g, fs):  # kelompok -> fitur
    return g if fs == '19' or g in GO[:-1] else 'LAINNYA'

def matrix(E, wil, fs='11'):
    cols = ALL19 if fs == '19' else GO
    F = E[E.kelurahan.isin(wil)].assign(f=lambda d: d.g.map(lambda x: feat(x, fs))).pivot_table(index='kelurahan', columns='f', values='id_kunjungan', aggfunc='count', fill_value=0)
    return F.reindex(index=wil, columns=cols, fill_value=0)

def X_of(F, sqrt=True):
    P = F.div(F.sum(axis=1), axis=0).values
    return np.sqrt(P) if sqrt else P

def ward(X, k): return AgglomerativeClustering(k, linkage='ward').fit_predict(X)
def sizes(l): return sorted(np.bincount(l).tolist())

def bootstrap(E, wil, fs='11', sqrt=True, n=200, seed=888):
    cols = ALL19 if fs == '19' else GO
    V = {}
    for w in wil:
        d = E[E.kelurahan == w].assign(f=lambda d: d.g.map(lambda x: feat(x, fs)))
        V[w] = pd.crosstab(d.id_kunjungan, d.f).reindex(columns=cols, fill_value=0).values
    X0 = X_of(matrix(E, wil, fs), sqrt); base = ward(X0, 2)
    rng = np.random.RandomState(seed); ari, sing, sil = [], 0, []
    for _ in range(n):
        rows = []
        for w in wil:
            v = V[w]; idx = rng.randint(0, len(v), len(v)); c = v[idx].sum(axis=0).astype(float); rows.append(c / c.sum())
        P = np.array(rows); X = np.sqrt(P) if sqrt else P; l = ward(X, 2)
        ari.append(adjusted_rand_score(base, l)); sing += int(min(np.bincount(l)) == 1)
        if len(set(l)) > 1: sil.append(silhouette_score(X, l))
    return dict(ari_mean=float(np.mean(ari)), ari_median=float(np.median(ari)), singleton_pct=sing / n * 100, sil_boot=float(np.mean(sil)))

if __name__ == '__main__':
    E = load_rows()
    nv = E[E.kelurahan.isin(ORDER)].groupby('kelurahan').id_kunjungan.nunique()
    nv_all = E.groupby('kelurahan').id_kunjungan.nunique()
    W11 = list(ORDER); W9 = [w for w in ORDER if nv[w] >= 30]; W5 = [w for w in ORDER if nv[w] >= 50]
    W12 = W11 + ['AIR RAJA']
    R = dict(order=ORDER, w9=W9, w5=W5, nv={w: int(nv_all[w]) for w in W12}, n_rows_all=len(E), n_rows_11=int(E.kelurahan.isin(W11).sum()), n_visits_11=int(E[E.kelurahan.isin(W11)].id_kunjungan.nunique()))
    out = os.path.join(ROOT, 'Data_Siap_Mining')
    for tag, wil in (('11', W11), ('9', W9), ('12', W12)):
        F = matrix(E, wil); P = F.div(F.sum(axis=1), axis=0)
        Fo = F.copy(); Fo['total_kehadiran_kategori'] = F.sum(axis=1); Fo['kunjungan_klinis_2025'] = [int(nv_all[w]) for w in wil]; Fo.index.name = 'wilayah_asal_pasien'
        Fo.to_csv(f'{out}/Matriks_Frekuensi_{tag}.csv', encoding='utf-8-sig'); P.index.name = 'wilayah_asal_pasien'; P.round(13).to_csv(f'{out}/Matriks_Proporsi_{tag}.csv', encoding='utf-8-sig')
        R['F' + tag] = F.values.tolist(); R['P' + tag] = P.values.tolist()
        rows = []
        for k in range(2, 6):
            X = X_of(F); lw = ward(X, k); lk = KMeans(k, n_init=10, random_state=42).fit_predict(X)
            for nm, l in (('Ward', lw), ('K-Means', lk)):
                rows.append(dict(skenario_wilayah=len(wil), algoritma=nm, k=k, silhouette=round(silhouette_score(X, l), 4), davies_bouldin=round(davies_bouldin_score(X, l), 4), calinski_harabasz=round(calinski_harabasz_score(X, l), 4), ukuran_cluster='-'.join(map(str, sizes(l))), jumlah_singleton=int((np.bincount(l) == 1).sum())))
            if k == 2: R['ari_ward_kmeans_' + tag] = float(adjusted_rand_score(lw, lk))
        R['uji' + tag] = rows
        l2 = ward(X_of(F), 2); big = np.bincount(l2).argmax(); R['lab' + tag] = [('C1' if x == big else 'C2') for x in l2]
    pd.concat([pd.DataFrame(R['uji' + t]) for t in ('9', '11', '12')]).to_csv(os.path.join(ROOT, 'Hasil_Evaluasi', 'Tabel_Pengujian_Model.csv'), index=False)
    pd.DataFrame([dict(skenario_wilayah=t, wilayah_asal=w.title(), kunjungan_klinis=int(nv_all[w]), cluster=c) for t, wl in (('9', W9), ('11', W11), ('12', W12)) for w, c in zip(wl, R['lab' + t])]).to_csv(os.path.join(ROOT, 'Hasil_Evaluasi', 'Keanggotaan_Cluster.csv'), index=False)
    # bootstrap: hasil resmi berasal dari Pipeline_Pengolahan.py --bootstrap (jalur dari 34 berkas mentah) -> hasil_bootstrap.json
    bp = os.path.join(ROOT, 'hasil_bootstrap.json')
    R['boot'] = json.load(open(bp)) if os.path.exists(bp) else {}
    json.dump(R, open(os.path.join(ROOT, 'hasil_model.json'), 'w'), ensure_ascii=False, indent=1)
    print({k: R[k] for k in ('n_rows_11', 'n_visits_11', 'lab11', 'ari_ward_kmeans_11')}); print(R['boot'].get('11'))
