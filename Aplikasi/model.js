/* Reproduksi Ward hierarchical clustering pada sqrt(proporsi kategori ICD).
 * Seluruh perhitungan dilakukan lokal di perangkat. Tidak ada koneksi jaringan.
 */
(function (root) {
  'use strict';
  function euclid(a,b){let s=0; for(let i=0;i<a.length;i++){const d=a[i]-b[i];s+=d*d;}return Math.sqrt(s);}
  function ward(dataset,k){
    if(!dataset || !Array.isArray(dataset.values))throw new Error('Dataset tidak lengkap');
    const p=dataset.values;const n=p.length;
    if(k<2||k>=n)throw new Error('Jumlah cluster tidak valid');
    const X=p.map(row=>row.map(v=>Math.sqrt(v)));
    let groups=X.map((v,i)=>({ids:[i],n:1,mean:v.slice()}));
    while(groups.length>k){
      let best=Infinity, a=-1, b=-1;
      for(let i=0;i<groups.length;i++)for(let j=i+1;j<groups.length;j++){
        const A=groups[i],B=groups[j]; let sq=0;
        for(let q=0;q<A.mean.length;q++)sq+=(A.mean[q]-B.mean[q])**2;
        const cost=A.n*B.n/(A.n+B.n)*sq;
        if(cost<best-1e-13){best=cost;a=i;b=j;}
      }
      const A=groups[a],B=groups[b],total=A.n+B.n;
      const merged={ids:A.ids.concat(B.ids),n:total,mean:A.mean.map((v,z)=>(v*A.n+B.mean[z]*B.n)/total)};
      groups.splice(b,1);groups.splice(a,1);groups.push(merged);
    }
    groups.sort((a,b)=>{
      const aHas0=a.ids.includes(0),bHas0=b.ids.includes(0);
      if(aHas0!==bHas0)return aHas0?-1:1;
      return Math.min(...a.ids)-Math.min(...b.ids);
    });
    const labels=Array(n).fill(-1);
    groups.forEach((g,index)=>g.ids.forEach(i=>labels[i]=index));
    return {labels,sizes:groups.map(g=>g.n),groups:groups.map(g=>g.ids),X,silhouette:silhouette(X,labels),n};
  }
  function silhouette(X,lab){
    const n=X.length, distances=X.map((a,i)=>X.map((b,j)=>i===j?0:euclid(a,b)));
    const uniq=[...new Set(lab)]; let score=0;
    for(let i=0;i<n;i++){
      const own=lab.map((z,j)=>z===lab[i]&&i!==j?j:-1).filter(j=>j>=0);
      if(own.length===0)continue; // singleton -> 0, sama seperti sklearn
      const a=own.reduce((s,j)=>s+distances[i][j],0)/own.length;
      let b=Infinity;
      for(const lbl of uniq){if(lbl===lab[i])continue;
        const other=lab.map((z,j)=>z===lbl?j:-1).filter(j=>j>=0);
        const m=other.reduce((s,j)=>s+distances[i][j],0)/other.length;
        b=Math.min(b,m);
      }
      score+=(b-a)/Math.max(a,b);
    }
    return score/n;
  }
  function summaries(dataset,result){
    return result.groups.map((ids,group)=>({cluster:'C'+(group+1),count:ids.length,features:dataset.features.map((f,j)=>({feature:f,value:ids.reduce((s,i)=>s+dataset.values[i][j],0)/ids.length})).sort((a,b)=>b.value-a.value),names:ids.map(i=>dataset.names[i])}));
  }
  /* PCA (komponen utama) pada X = sqrt(proporsi), hanya untuk menggambar peta 2D.
   * Pengelompokan Ward tetap dihitung pada seluruh fitur, bukan pada 2 sumbu ini. */
  function jacobi(A){
    const n=A.length;A=A.map(r=>r.slice());
    const V=Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>i===j?1:0));
    for(let sweep=0;sweep<100;sweep++){
      let off=0;for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)off+=A[i][j]*A[i][j];
      if(off<1e-22)break;
      for(let p=0;p<n-1;p++)for(let q=p+1;q<n;q++){
        if(Math.abs(A[p][q])<1e-30)continue;
        const theta=(A[q][q]-A[p][p])/(2*A[p][q]);
        const t=Math.sign(theta||1)/(Math.abs(theta)+Math.sqrt(theta*theta+1));
        const c=1/Math.sqrt(t*t+1),s=t*c;
        for(let k=0;k<n;k++){const akp=A[k][p],akq=A[k][q];A[k][p]=c*akp-s*akq;A[k][q]=s*akp+c*akq;}
        for(let k=0;k<n;k++){const apk=A[p][k],aqk=A[q][k];A[p][k]=c*apk-s*aqk;A[q][k]=s*apk+c*aqk;}
        for(let k=0;k<n;k++){const vkp=V[k][p],vkq=V[k][q];V[k][p]=c*vkp-s*vkq;V[k][q]=s*vkp+c*vkq;}
      }
    }
    return {values:A.map((r,i)=>r[i]),vectors:V};
  }
  function pca(X){
    const n=X.length,d=X[0].length;
    const mean=Array.from({length:d},(_,j)=>X.reduce((s,r)=>s+r[j],0)/n);
    const Z=X.map(r=>r.map((v,j)=>v-mean[j]));
    const C=Array.from({length:d},(_,a)=>Array.from({length:d},(_,b)=>Z.reduce((s,r)=>s+r[a]*r[b],0)/(n-1)));
    const e=jacobi(C),order=e.values.map((v,i)=>i).sort((a,b)=>e.values[b]-e.values[a]);
    const total=e.values.reduce((s,v)=>s+v,0);
    const axes=order.slice(0,2).map(i=>{
      const vec=e.vectors.map(r=>r[i]);
      const big=vec.reduce((m,v)=>Math.abs(v)>Math.abs(m)?v:m,0);
      return big<0?vec.map(v=>-v):vec; // tanda sumbu dibuat deterministik
    });
    return {coords:Z.map(r=>axes.map(v=>r.reduce((s,x,j)=>s+x*v[j],0))),explained:order.slice(0,2).map(i=>e.values[i]/total)};
  }
  const api={ward,summaries,pca};
  if(typeof module!=='undefined' && module.exports)module.exports=api;
  root.SeiModel=api;
})(typeof window==='undefined'?globalThis:window);
