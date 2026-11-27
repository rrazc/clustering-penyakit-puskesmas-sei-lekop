"""Membuat gambar laporan dari hasil_model.json (hitungan per diagnosis). Jalankan: python Buat_Gambar_Laporan.py <folder_paket>"""
import sys, os, json
import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.stats import chi2_contingency
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
R = json.load(open(os.path.join(ROOT, 'hasil_model.json'))); OUT = os.path.join(ROOT, 'Gambar_Laporan')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
GO = ['J','K','I','E','R','M','L','S_T','A_B','H0_59','LAINNYA']
SHORT = {'J':'Pernapasan (J)','K':'Pencernaan (K)','I':'Sirkulasi (I)','E':'Endokrin (E)','R':'Gejala/tanda (R)','M':'Otot-tulang (M)','L':'Kulit (L)','S_T':'Cedera (S–T)','A_B':'Infeksi (A–B)','H0_59':'Mata (H00–H59)','LAINNYA':'Kategori lain'}
HEAD = {'J':'J\nPernapasan','K':'K\nPencernaan','I':'I\nSirkulasi','E':'E\nEndokrin','R':'R\nGejala','M':'M\nOtot','L':'L\nKulit','S_T':'S–T\nCedera','A_B':'A–B\nInfeksi','H0_59':'H00–59\nMata','LAINNYA':'Lainnya'}
nice = lambda w: {'BATU SEMBILAN':'Batu Sembilan'}.get(w, w.title())
names = [nice(w) for w in R['order']]; P = np.array(R['P11']); F = np.array(R['F11']); lab = R['lab11']; nv = [R['nv'][w] for w in R['order']]
X = np.sqrt(P); Z = linkage(X, 'ward'); n = len(names)
fmt = lambda x, d=1: (f'%.{d}f' % x).replace('.', ',')
dend = dendrogram(Z, no_plot=True); leaf = dend['leaves']          # urutan daun
cut = (Z[-2, 2] + Z[-1, 2]) / 2

# ---- tabel turunan untuk laporan
D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
steps, memb = [], {i: [i] for i in range(n)}
code = lambda ids: ('W%d' % (ids[0] + 1)) if len(ids) == 1 else ('(' + ', '.join('W%d' % (i + 1) for i in sorted(ids)) + ')')
for j, (a, b, h, c) in enumerate(Z):
    ma, mb = memb[int(a)], memb[int(b)]; memb[n + j] = ma + mb
    steps.append(dict(langkah=j + 1, a=sorted(ma), b=sorted(mb), jarak=float(h), n=int(c)))
c1 = [i for i in range(n) if lab[i] == 'C1']; c2 = [i for i in range(n) if lab[i] == 'C2']
mean1, mean2 = P[c1].mean(0), P[c2].mean(0)
# residual baku 4 wilayah terbesar (Pearson: (O-E)/sqrt(E)) pada frekuensi baris diagnosis
core = [0, 1, 2, 3]; chi = chi2_contingency(F[core]); E = chi[3]; RES = (F[core] - E) / np.sqrt(E)
T = dict(dist=D.tolist(), steps=steps, c1=c1, c2=c2, mean1=mean1.tolist(), mean2=mean2.tolist(), kehadiran=F.sum(0).tolist(), res=RES.tolist(), cut=float(cut), leaf=leaf)
json.dump(T, open(os.path.join(ROOT, 'tabel_laporan.json'), 'w'), indent=1)

def heat(ax, M, rows, cols, vmax, cmap='Greys', annot_fmt=lambda v: fmt(v), colorbar=False, tick_top=True, fs=9):
    im = ax.imshow(M, cmap=cmap, vmin=0 if cmap == 'Greys' else -vmax, vmax=vmax, aspect='auto')
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]; dark = (v > vmax * 0.55) if cmap == 'Greys' else abs(v) > vmax * 0.6
            ax.text(j, i, annot_fmt(v), ha='center', va='center', fontsize=fs, color='white' if dark else '#222')
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, fontsize=fs)
    if tick_top: ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows, fontsize=fs + 1)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0); return im

# ---- Gambar 3.1
fig, ax = plt.subplots(figsize=(14, 8.2)); im = heat(ax, 100 * P, names, [HEAD[g] for g in GO], 45)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label('Proporsi (%)'); fig.tight_layout(); fig.savefig(f'{OUT}/Gambar_3_1_Heatmap_Proporsi.png', dpi=130); plt.close(fig)

# ---- Gambar 4.1 dendrogram horizontal
fig, ax = plt.subplots(figsize=(11, 6.4))
d2 = dendrogram(Z, orientation='right', labels=names, color_threshold=0, above_threshold_color='#444', ax=ax)
ax.axvline(cut, color='#c0392b', ls='--', lw=1); ax.set_xlabel('Jarak penggabungan Ward (ruang akar proporsi)'); ax.set_ylabel('Wilayah asal pasien')
ax.set_title('Dendrogram Ward — 11 wilayah, k=2 sebagai potongan awal'); ax.grid(axis='x', alpha=.3); fig.tight_layout(); fig.savefig(f'{OUT}/Gambar_4_1_Dendrogram.png', dpi=130); plt.close(fig)

# ---- Gambar 4.2 profil cluster
fig, ax = plt.subplots(figsize=(11, 5.4)); xs = np.arange(len(GO)); w = .4
ax.bar(xs - w / 2, mean1, w, color='#555', edgecolor='#222', label=f'Cluster 1 ({len(c1)} wilayah)'); ax.bar(xs + w / 2, mean2, w, color='#aaa', edgecolor='#222', label=f'Cluster 2 ({len(c2)} wilayah)')
ax.set_xticks(xs); ax.set_xticklabels(GO); ax.set_ylabel('Rata-rata proporsi kehadiran kategori'); ax.set_title('Profil deskriptif tiap cluster (bukan prevalensi penduduk)'); ax.legend(); ax.grid(axis='y', alpha=.3)
fig.tight_layout(); fig.savefig(f'{OUT}/Gambar_4_2_Profil_Cluster.png', dpi=130); plt.close(fig)

# ---- Gambar 5.1 silhouette
fig, ax = plt.subplots(figsize=(10, 5))
for tag, c, nm in (('9', '#1f77b4', '9 wilayah'), ('11', '#ff7f0e', '11 wilayah')):
    rr = [r for r in R['uji' + tag] if r['algoritma'] == 'Ward']; ks = [r['k'] for r in rr]; sv = [r['silhouette'] for r in rr]
    ax.plot(ks, sv, 'o-', color=c, lw=3, ms=9, label=nm); ax.annotate(f'{sv[0]:.4f}', (ks[0], sv[0]), textcoords='offset points', xytext=(8, 8))
ax.set_xticks([2, 3, 4, 5]); ax.set_xlabel('Jumlah cluster (k)'); ax.set_ylabel('Silhouette score'); ax.set_title('Evaluasi Ward pada dua skenario wilayah'); ax.grid(alpha=.3); ax.legend(); ax.set_ylim(0.2, 0.46)
fig.tight_layout(); fig.savefig(f'{OUT}/Gambar_5_1_Silhouette.png', dpi=130); fig.savefig(f'{ROOT}/Hasil_Evaluasi/Gambar_5_1_Silhouette.png', dpi=130); plt.close(fig)

# ---- Gambar 4.4 : satu diagram, X = kelompok penyakit, Y = rasio (%)
fig, ax = plt.subplots(figsize=(12, 6.2)); xs = np.arange(len(GO))
for i in range(n):
    c = '#c0392b' if lab[i] == 'C2' else '#2c6fad'
    ax.plot(xs, 100 * P[i], 'o-', color=c, alpha=.85 if nv[i] >= 50 else .6, lw=1.8 if nv[i] >= 50 else 1.2, ms=4, ls='-' if nv[i] >= 50 else '--')
    ax.annotate(f'{names[i]}', (xs[0], 100 * P[i, 0]), textcoords='offset points', xytext=(-6, 0), ha='right', fontsize=7, color=c) if False else None
ax.set_xticks(xs); ax.set_xticklabels([SHORT[g] for g in GO], rotation=30, ha='right'); ax.set_ylabel('Rasio kategori terhadap total diagnosis wilayah (%)'); ax.set_xlabel('Kelompok penyakit (ICD-10)')
ax.grid(alpha=.3); ax.set_title('Rasio kelompok penyakit per wilayah (11 wilayah, tahun 2025)')
from matplotlib.lines import Line2D
h = [Line2D([0], [0], color='#2c6fad', lw=2, label=f'Cluster 1 ({len(c1)} wilayah)'), Line2D([0], [0], color='#c0392b', lw=2, label=f'Cluster 2 ({len(c2)} wilayah)'), Line2D([0], [0], color='#888', lw=1.2, ls='--', label='Garis putus-putus: n kunjungan klinis < 50')]
ax.legend(handles=h, loc='upper right'); fig.tight_layout(); fig.savefig(f'{OUT}/Gambar_4_4_Rasio_Per_Kategori.png', dpi=130); plt.close(fig)

# ---- Gambar gabungan (dendrogram + heatmap + pengayaan)
def combined(portrait):
    if portrait:
        fig = plt.figure(figsize=(10.5, 15)); gs = GridSpec(2, 4, width_ratios=[1.2, 2.1, 6, .22], height_ratios=[1.2, .85], hspace=.22, wspace=.08)
        axd = fig.add_subplot(gs[0, 0]); axh = fig.add_subplot(gs[0, 2]); cax1 = fig.add_subplot(gs[0, 3]); axr = fig.add_subplot(gs[1, 2]); cax2 = fig.add_subplot(gs[1, 3])
    else:
        fig = plt.figure(figsize=(22, 8.8)); gs = GridSpec(1, 7, width_ratios=[1.2, 1.9, 7, .2, 1.7, 3.6, .2], wspace=.1)
        axd = fig.add_subplot(gs[0]); axh = fig.add_subplot(gs[2]); cax1 = fig.add_subplot(gs[3]); axr = fig.add_subplot(gs[5]); cax2 = fig.add_subplot(gs[6])
    dd = dendrogram(Z, orientation='left', no_labels=True, color_threshold=0, above_threshold_color='#444', ax=axd); axd.invert_xaxis()
    axd.set_xlabel('Jarak Ward'); axd.set_title('Klaster hirarki (Ward)', fontsize=10)
    for sp in ('top', 'right', 'left'): axd.spines[sp].set_visible(False)
    axd.set_yticks([])
    rows_order = dd['leaves'][::-1]
    Pl = 100 * P[rows_order]; labs = [f'{names[i]} (n={nv[i]})' for i in rows_order]
    im = heat(axh, Pl, labs, [SHORT[g] for g in GO], 45, annot_fmt=lambda v: fmt(v), tick_top=False, fs=8)
    for t, i in zip(axh.get_yticklabels(), rows_order): t.set_color('#c0392b' if lab[i] == 'C2' else '#2c6fad'); t.set_fontweight('bold')
    axh.set_xticklabels([SHORT[g] for g in GO], rotation=40, ha='right', fontsize=8); axh.set_title('Profil kategori diagnosis per wilayah (% baris diagnosis)', fontsize=10)
    fig.colorbar(im, cax=cax1).set_label('Proporsi (%)')
    vm = 4; im2 = axr.imshow(RES.T, cmap='RdBu_r', vmin=-vm, vmax=vm, aspect='auto')
    for a in range(RES.shape[0]):
        for b in range(RES.shape[1]): v = RES[a, b]; axr.text(a, b, f'{v:+.1f}'.replace('.', ','), ha='center', va='center', fontsize=8, color='white' if abs(v) > 2.4 else '#222', fontweight='bold' if abs(v) > 2 else 'normal')
    axr.set_xticks(range(4)); axr.set_xticklabels([names[a].replace(' ', '\n', 1) for a in core], fontsize=8); axr.xaxis.tick_top(); axr.set_yticks(range(len(GO))); axr.set_yticklabels([SHORT[g] for g in GO], fontsize=8)
    axr.set_title('Pengayaan 4 wilayah inti (residual baku; |z|>2 ditebalkan)', fontsize=10, pad=30); axr.tick_params(length=0)
    for sp in axr.spines.values(): sp.set_visible(False)
    fig.colorbar(im2, cax=cax2).set_label('Residual baku (z-score)')
    r_, v_ = f'{R["n_rows_11"]:,}'.replace(',', '.'), f'{R["n_visits_11"]:,}'.replace(',', '.')
    ttl = f'Analisis Cluster dan Asosiasi: Wilayah vs Kelompok Diagnosis\n(11 wilayah, N = {r_} baris diagnosis dari {v_} kunjungan klinis, 2025)'
    fig.suptitle(ttl if portrait else ttl.replace('\n', ' '), fontsize=11, fontweight='bold', y=.99 if portrait else .985)
    foot = f'Warna nama wilayah: biru = Cluster 1 ({len(c1)} wilayah), merah = Cluster 2 ({len(c2)} wilayah) pada k=2. Fitur = proporsi; jarak Ward pada akar kuadrat proporsi (Hellinger).\nn = kunjungan klinis 2025; wilayah dengan n kecil perlu dibaca hati-hati.'
    fig.text(.01, .008, foot if portrait else foot.replace('\n', ' '), fontsize=7.5, color='#444')
    fig.subplots_adjust(top=.86 if not portrait else .92, bottom=.17 if not portrait else .045, left=.03 if not portrait else .04, right=.96 if not portrait else .90)
    fig.savefig(f'{OUT}/Gambar_Gabungan_Dendrogram_Heatmap{"_Portrait" if portrait else ""}.png', dpi=120); plt.close(fig)
combined(False); combined(True)
print('selesai; residual maks', np.abs(RES).max().round(2), '| Cedera:', RES[:, GO.index('S_T')].round(1), '| Sirkulasi:', RES[:, GO.index('I')].round(1))
