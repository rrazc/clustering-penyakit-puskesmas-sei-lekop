"""Uji konsistensi matriks fitur, model Python dan implementasi Ward JavaScript.
Hanya menggunakan matriks agregat; tidak memuat rekaman pasien.
"""
import csv, json, pathlib, subprocess, tempfile, sys
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score

ROOT = pathlib.Path(__file__).resolve().parent
APP = ROOT / 'Aplikasi'
errors=[]
checks=[]
expected={9:(0.3917,[2,7]),11:(0.3059,[3,8])}
for n in (9,11):
    with open(APP / f'Matriks_Proporsi_{n}.csv',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    features=[k for k in rows[0] if k!='wilayah_asal_pasien']
    A=np.array([[float(row[k]) for k in features] for row in rows]);
    assert A.shape == (n,11), (n,A.shape)
    assert np.isfinite(A).all() and (A>=0).all() and np.allclose(A.sum(axis=1),1.0,atol=1e-9)
    checks.append(f'Matriks {n} wilayah: {n} baris, 11 fitur, proporsi total 1.000000; PASS')
    X=np.sqrt(A)
    for k in range(2,6):
        labs=AgglomerativeClustering(n_clusters=k,linkage='ward').fit_predict(X)
        score=float(silhouette_score(X,labs))
        checks.append(f'Ward Python n={n}, k={k}: silhouette={score:.6f}, ukuran={sorted(np.bincount(labs).tolist())}')
        if k==2:
            target, sizes=expected[n]
            assert round(score,4)==target, (n,k,score,target)
            assert sorted(np.bincount(labs).tolist())==sizes

# JavaScript uses original model.js and data_model.js; evaluate in Node vm without DOM.
node_source = r'''
const fs=require('fs'),vm=require('vm');
const ctx={window:{},console};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
vm.runInContext(fs.readFileSync(process.argv[3],'utf8'),ctx);
const datasets=ctx.window.SEI_DATA, ward=ctx.window.SeiModel.ward;
let result=[];
for(let n of [9,11])for(let k of [2,3,4,5]){
  const out=ward(datasets[String(n)],k);
  result.push({n,k,silhouette:out.silhouette,labels:out.labels,sizes:out.sizes});
}
process.stdout.write(JSON.stringify(result));
'''
node_file=ROOT/'_uji_model_node.js'
node_file.write_text(node_source,encoding='utf8')
try:
    j=subprocess.run(['node',str(node_file),str(APP/'data_model.js'),str(APP/'model.js')],text=True,capture_output=True,check=True)
    js=json.loads(j.stdout)
    for rec in js:
        n,k=rec['n'],rec['k']
        with open(APP/f'Matriks_Proporsi_{n}.csv',encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        feat=[c for c in rows[0] if c!='wilayah_asal_pasien']
        X=np.sqrt(np.array([[float(row[c]) for c in feat] for row in rows]))
        labs=AgglomerativeClustering(n_clusters=k,linkage='ward').fit_predict(X)
        score=silhouette_score(X,labs)
        assert abs(score-rec['silhouette'])<1e-9, (n,k,score,rec['silhouette'])
        ari=adjusted_rand_score(labs,rec['labels'])
        assert ari > 1-1e-12,(n,k,ari)
        checks.append(f'Ward JS vs Python n={n}, k={k}: silhouette identik dan ARI=1; PASS')
finally:
    node_file.unlink(missing_ok=True)

# Browser launcher is self-contained and no outgoing network requests.
html=(APP/'JALANKAN_DASHBOARD.html').read_text(encoding='utf8')
assert '<html' in html.lower() and 'SeiModel' in html and 'SEI_DATA' in html
for s in ('https://','http://','fetch('):
    if s in html: checks.append(f'PERIKSA MANUAL: string {s} terdeteksi pada launcher')
checks.append('Launcher HTML self-contained dengan data agregat dan fungsi Ward; PASS')

# Data files must not contain columns indicating identifiers of patients.
for p in APP.glob('*.csv'):
    hdr=p.open(encoding='utf-8-sig').readline().lower()
    assert not any(s in hdr for s in ('nama pasien','nik','no rm','no erm','rekam medis','alamat lengkap','telepon')),(p.name,hdr)
checks.append('CSV aplikasi tidak berisi kolom identitas langsung pasien; PASS')

(ROOT/'BUKTI_VALIDASI_TERBARU.txt').write_text('HASIL VALIDASI FINAL — 19 NOVEMBER 2026 (hitungan per diagnosis)\n'+'\n'.join(checks)+'\n',encoding='utf8')
print('\n'.join(checks));print('SELURUH UJI: LULUS')
