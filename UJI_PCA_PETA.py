"""Uji: koordinat peta cluster (PCA) di dashboard JavaScript = scikit-learn (abaikan tanda sumbu)."""
import json,subprocess,os,numpy as np,pandas as pd
from sklearn.decomposition import PCA
here=os.path.dirname(os.path.abspath(__file__));app=os.path.join(here,'Aplikasi')
js="global.window=global;require('./data_model.js');const M=require('./model.js');const o={};for(const s of ['9','11']){const d=window.SEI_DATA[s];const r=M.ward(d,2);o[s]=M.pca(r.X);}console.log(JSON.stringify(o));"
out=json.loads(subprocess.check_output(['node','-e',js],cwd=app))
ok=True
for s in ['9','11']:
    X=np.sqrt(pd.read_csv(os.path.join(app,f'Matriks_Proporsi_{s}.csv'),index_col=0).values)
    p=PCA(2).fit(X);C=p.transform(X);J=np.array(out[s]['coords'])
    for a in range(2):
        d=min(np.abs(C[:,a]-J[:,a]).max(),np.abs(C[:,a]+J[:,a]).max())
        ev=abs(p.explained_variance_ratio_[a]-out[s]['explained'][a])
        good=d<1e-6 and ev<1e-9;ok&=good
        print(f'PCA {s} wilayah, sumbu {a+1}: selisih koordinat maks={d:.2e}, selisih varians={ev:.2e}; {"PASS" if good else "GAGAL"}')
print('UJI PCA PETA:','LULUS' if ok else 'GAGAL')
