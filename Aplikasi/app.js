(function(){
 'use strict';
 const $=id=>document.getElementById(id);
 const label={J:'Pernapasan (J)',K:'Pencernaan (K)',I:'Sirkulasi (I)',E:'Endokrin (E)',R:'Gejala/tanda (R)',M:'Otot-tulang (M)',L:'Kulit (L)',S_T:'Cedera/keracunan (S–T)',A_B:'Infeksi (A–B)',H0_59:'Mata (H00–H59)',LAINNYA:'Kategori lain'};
 const fmt=x=>(100*x).toFixed(1).replace('.',',')+'%';
 const fixed=x=>x.toFixed(4).replace('.',',');
 let current=null;
 function el(tag,txt,cls){const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;if(cls)e.className=cls;return e;}
 function render(){
  const scenario=$('scenario').value,k=Number($('k').value);
  const data=window.SEI_DATA[scenario],result=window.SeiModel.ward(data,k);current={data,result,scenario,k};
  $('m-regions').textContent=result.n;$('m-clusters').textContent=k;$('m-score').textContent=fixed(result.silhouette);
  const singles=result.sizes.filter(z=>z===1).length;$('m-single').textContent=singles;
  const warning=singles?`PERHATIAN: ${singles} cluster hanya memiliki satu wilayah. Model ini kurang tepat untuk langsung digunakan sebagai dasar program kesehatan.`:
      'HASIL EKSPLORATIF: Tidak ada cluster tunggal pada pengaturan ini. Namun, bootstrap 200 kali pada model utama (11 wilayah, k=2) menunjukkan 15,5% ulangan menghasilkan cluster tunggal (pembanding 9 wilayah: 35,0%); profil dari wilayah dengan sedikit kunjungan belum stabil.';
  $('warning').textContent=warning;
  const member=$('cluster-members');member.replaceChildren();
  const profiles=window.SeiModel.summaries(data,result);
  for(const cluster of profiles){
    const section=el('div');section.style.marginBottom='18px';
    section.appendChild(el('h3',cluster.cluster+' · '+cluster.count+' wilayah','clusterName'));
    const badge=el('div',cluster.features.slice(0,2).map(f=>label[f.feature]).join(' · '),'tags');section.appendChild(badge);
    cluster.names.forEach(name=>{const r=el('div',undefined,'member');r.appendChild(el('span',title(name)));r.appendChild(el('span','Wilayah','small'));section.appendChild(r);});
    member.appendChild(section);
  }
  const features=data.features;
  const meanAll=features.map((f,j)=>({f,v:data.values.reduce((s,row)=>s+row[j],0)/data.values.length})).sort((a,b)=>b.v-a.v).slice(0,7);
  const bars=$('profile-bars');bars.replaceChildren();
  for(const obj of meanAll){
    const i=features.indexOf(obj.f), c1=profiles[0].features.find(z=>z.feature===obj.f).value;
    const c2=profiles[1]?profiles[1].features.find(z=>z.feature===obj.f).value:0;
    const r=el('div',undefined,'bar-row');r.appendChild(el('span',label[obj.f]));
    for(const [val,blue] of [[c1,false],[c2,true]]){const track=el('div',undefined,'track');const fill=el('div',undefined,blue?'fill blue':'fill');fill.style.width=(Math.min(100,val*200))+'%';track.appendChild(fill);r.appendChild(track);r.appendChild(el('span',fmt(val),'num'));}
    bars.appendChild(r);
  }
  $('profile-note').textContent=k>2?'Grafik ini hanya menampilkan Cluster 1 dan 2; tabel di bawah tetap memuat semua kelompok. Pilih k=2 untuk membaca profil model utama.':'Panjang batang diskalakan konsisten (50% = lebar penuh). Persentase dihitung dari rerata proporsi wilayah, bukan jumlah pasien unik.';
  drawMap(data,result,k);
  const tbody=$('table-body');tbody.replaceChildren();
  data.names.forEach((name,i)=>{
    const sorted=data.values[i].map((v,j)=>({f:features[j],v})).sort((a,b)=>b.v-a.v),tr=el('tr');
    tr.appendChild(el('td',title(name)));tr.appendChild(el('td','C'+(result.labels[i]+1)));
    tr.appendChild(el('td',label[sorted[0].f]+' · '+fmt(sorted[0].v)));
    tr.appendChild(el('td',label[sorted[1].f]+' · '+fmt(sorted[1].v)));
    const low=data.limited[i];tr.appendChild(el('td',low?'Sampel terbatas':'Sampel cukup',low?'state warning':'state'));
    tbody.appendChild(tr);
  });
 }

 const PAL=['#0b8172','#365e90','#b5651d','#8a5a9e','#6b7b78'];
 const NS='http:'+'//www.w3.org/2000/svg'; // namespace SVG, bukan koneksi jaringan
 function sv(tag,attrs,txt){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(txt!==undefined)e.textContent=txt;return e;}
 function hull(pts){
  const p=pts.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]);if(p.length<3)return p;
  const cr=(o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
  const lo=[];for(const q of p){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],q)<=0)lo.pop();lo.push(q);}
  const up=[];for(let i=p.length-1;i>=0;i--){const q=p[i];while(up.length>=2&&cr(up[up.length-2],up[up.length-1],q)<=0)up.pop();up.push(q);}
  lo.pop();up.pop();return lo.concat(up);
 }
 function drawMap(data,result,k){
  const svg=$('map');svg.replaceChildren();
  const pc=window.SeiModel.pca(result.X),W=760,H=470,L=62,R=24,T=18,B=52;
  const xs=pc.coords.map(c=>c[0]),ys=pc.coords.map(c=>c[1]);
  const pad=(lo,hi)=>{const s=(hi-lo)*0.14||0.05;return [lo-s,hi+s];};
  const [x0,x1]=pad(Math.min(...xs),Math.max(...xs)),[y0,y1]=pad(Math.min(...ys),Math.max(...ys));
  const sx=x=>L+(x-x0)/(x1-x0)*(W-L-R),sy=y=>H-B-(y-y0)/(y1-y0)*(H-T-B);
  const P=pc.coords.map(c=>[sx(c[0]),sy(c[1])]);
  // sumbu dan grid
  svg.appendChild(sv('rect',{x:L,y:T,width:W-L-R,height:H-T-B,fill:'#fff',stroke:'#d9e5e1'}));
  if(x0<0&&x1>0)svg.appendChild(sv('line',{x1:sx(0),x2:sx(0),y1:T,y2:H-B,stroke:'#cfdad6','stroke-dasharray':'4 4'}));
  if(y0<0&&y1>0)svg.appendChild(sv('line',{x1:L,x2:W-R,y1:sy(0),y2:sy(0),stroke:'#cfdad6','stroke-dasharray':'4 4'}));
  svg.appendChild(sv('text',{x:(L+W-R)/2,y:H-14,'text-anchor':'middle','font-size':12,fill:'#647a78'},'Komponen utama 1 ('+Math.round(pc.explained[0]*100)+'% variasi)'));
  const yl=sv('text',{x:16,y:(T+H-B)/2,'text-anchor':'middle','font-size':12,fill:'#647a78',transform:'rotate(-90 16 '+((T+H-B)/2)+')'},'Komponen utama 2 ('+Math.round(pc.explained[1]*100)+'% variasi)');svg.appendChild(yl);
  // lingkaran cluster
  result.groups.forEach((ids,g)=>{
   const col=PAL[g%PAL.length],pts=ids.map(i=>P[i]);
   if(pts.length===1){svg.appendChild(sv('circle',{cx:pts[0][0],cy:pts[0][1],r:20,fill:col,'fill-opacity':.12,stroke:col,'stroke-opacity':.55,'stroke-width':1.5,'stroke-dasharray':'5 3'}));return;}
   const h=hull(pts),d='M'+h.map(q=>q[0].toFixed(1)+','+q[1].toFixed(1)).join(' L')+(h.length>2?' Z':'');
   svg.appendChild(sv('path',{d,fill:col,'fill-opacity':.12,stroke:col,'stroke-opacity':.22,'stroke-width':26,'stroke-linejoin':'round','stroke-linecap':'round'}));
   svg.appendChild(sv('path',{d,fill:'none',stroke:col,'stroke-opacity':.7,'stroke-width':1.4,'stroke-linejoin':'round'}));
  });
  // titik
  const lab=result.labels;
  P.forEach((q,i)=>{const col=PAL[lab[i]%PAL.length],lim=data.limited[i];
   svg.appendChild(sv('circle',{cx:q[0],cy:q[1],r:6,fill:lim?'#fff':col,stroke:col,'stroke-width':2}));});
  // label tanpa tumpang tindih (penempatan greedy)
  const boxes=P.map(q=>({x:q[0]-8,y:q[1]-8,w:16,h:16})),inter=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
  const order=P.map((q,i)=>i).sort((a,b)=>P[a][1]-P[b][1]);
  order.forEach(i=>{
   const t=title(data.names[i]),w=t.length*5.6+4,h=13,q=P[i];
   const cands=[[10,-8],[10,14],[-w-10,-8],[-w-10,14],[-w/2,-14],[-w/2,22],[12,-22],[12,28],[-w-12,-22],[-w-12,28]];
   let best=null,bs=Infinity;
   for(const [dx,dy] of cands){
    const b={x:q[0]+dx,y:q[1]+dy-h+2,w,h};let s=0;
    if(b.x<L||b.x+b.w>W-R||b.y<T||b.y+b.h>H-B)s+=1000;
    boxes.forEach(o=>{if(inter(b,o))s+=100;});
    if(s<bs){bs=s;best=[dx,dy,b];}
   }
   boxes.push(best[2]);
   svg.appendChild(sv('text',{x:q[0]+best[0],y:q[1]+best[1],'font-size':11,fill:'#26433e'},t));
  });
  // legenda dan catatan
  const lg=$('map-legend');lg.replaceChildren();
  result.groups.forEach((ids,g)=>{const s=el('span');const d=el('i');d.style.cssText='width:10px;height:10px;border-radius:50%;background:'+PAL[g%PAL.length]+';display:inline-block';s.appendChild(d);s.appendChild(document.createTextNode('Cluster '+(g+1)+' ('+ids.length+' wilayah)'));lg.appendChild(s);});
  const s2=el('span');const d2=el('i');d2.style.cssText='width:10px;height:10px;border-radius:50%;border:2px solid #6b7b78;background:#fff;display:inline-block;box-sizing:border-box';s2.appendChild(d2);s2.appendChild(document.createTextNode('Sampel terbatas (< 50 kunjungan klinis)'));lg.appendChild(s2);
  $('map-note').textContent='Sumbu adalah komponen utama, yaitu ringkasan seluruh rasio kategori penyakit (bukan satu penyakit tertentu). Dua sumbu ini menjelaskan '+Math.round((pc.explained[0]+pc.explained[1])*100)+'% variasi, sehingga jarak antartitik bersifat perkiraan. Pengelompokan tetap dihitung dari seluruh kategori diagnosis. Cluster dengan sedikit kunjungan perlu dibaca sebagai kecenderungan.';
 }
 function title(s){return s.toLowerCase().replace(/\b\p{L}/gu,m=>m.toUpperCase());}
 function download(){if(!current)return;const {data,result,scenario,k}=current;
  const clean=s=>'"'+String(s).replace(/"/g,'""')+'"';
  const csv=['wilayah_asal,cluster,k,proporsi_kategori_dominan_1,proporsi_kategori_dominan_2'].concat(data.names.map((name,i)=>{
    const sort=data.values[i].map((v,j)=>({f:data.features[j],v})).sort((a,b)=>b.v-a.v);
    return [clean(name),'C'+(result.labels[i]+1),k,clean(sort[0].f+':'+sort[0].v.toFixed(5)),clean(sort[1].f+':'+sort[1].v.toFixed(5))].join(',');
  })).join('\n');
  const url=URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`hasil_cluster_${scenario}_wilayah_k${k}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
 }
 $('scenario').addEventListener('change',render);$('k').addEventListener('change',render);$('download').addEventListener('click',download);render();
})();
