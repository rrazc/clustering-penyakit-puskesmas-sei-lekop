"""Pengujian opsional untuk memeriksa hasil aplikasi dari matriks proporsi agregat.
Jalankan: pip install numpy pandas scikit-learn
         python Uji_Model_Python.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

here=Path(__file__).resolve().parent
for n,score_target,sizes_target in [(9,0.3917,[2,7]),(11,0.3059,[3,8])]:
    df=pd.read_csv(here/f'Matriks_Proporsi_{n}.csv')
    p=df.iloc[:,1:].to_numpy(float)
    assert np.allclose(p.sum(axis=1),1.0)
    x=np.sqrt(p)
    labels=AgglomerativeClustering(n_clusters=2,linkage='ward').fit_predict(x)
    sizes=sorted(np.bincount(labels))
    score=silhouette_score(x,labels)
    assert round(score,4)==score_target,(n,score)
    assert sizes==sizes_target,(n,sizes)
    print(f'PASS: {n} wilayah, silhouette={score:.4f}, ukuran cluster={sizes}')
print('Validasi selesai. Dataset hanya menggunakan agregat wilayah.')
