/* Tab tambahan: Calon & Petahana, Partai, Ormas, Risiko (Aladdin), Ontologi (Palantir), Worker AI.
   Termasuk peta drone bergerak + jaringan terhubung. */
(function(){
 const BARU=[['calon','Calon & Petahana'],['partai','Kekuatan Partai'],['ormas','Kekuatan Ormas'],
  ['risiko','Risiko (Aladdin)'],['ontologi','Ontologi (Palantir)'],['worker','Worker AI']];
 const iData=TAB.findIndex(t=>t[0]==='data');
 TAB.splice(iData<0?TAB.length:iData,0,...BARU);
 const main=document.querySelector('main');
 BARU.forEach(([k])=>{const s=document.createElement('section');s.id='v-'+k;s.className='hide';main.appendChild(s)});
 window.EXTRA=[vCalon,vPartai,vOrmas,vRisiko,vOntologi,vWorker];
})();
let WORKER=null,ANIM={jalan:true,t:0,kecepatan:1,jaringan:true};

/* ============ CALON & PETAHANA ============ */
function vCalon(){const kk=D.kandidat;
 const kartu=k=>{const kita=k.nomor===K();
  const bio=[['Nama lengkap',(k.nama_lengkap||k.nama)+(k.gelar?', '+k.gelar:'')],['Jabatan sekarang',k.jabatan_sekarang],
   ['Periode',k.periode_menjabat],['Partai / koalisi',(k.partai_utama||'')+' — '+String(k.koalisi||'').replace(/\|/g,' + ')],
   ['Lahir',(k.tempat_lahir||'')+(k.tanggal_lahir?', '+k.tanggal_lahir:'')+(k.usia?' ('+k.usia+' th)':'')],
   ['Pendidikan',k.pendidikan],['Karier',k.karier],['LHKPN',k.kekayaan_lhkpn],['Program unggulan',k.program_unggulan],
   ['Isu utama',k.isu_utama],['Basis massa',k.basis_massa],['Ormas pendukung',String(k.ormas_pendukung||'').replace(/\|/g,', ')],
   ['Media sosial',k.medsos]].filter(x=>x[1]);
  return '<div class="card klik" onclick="bukaTabel(\'kandidat.csv\',{nomor:\''+k.nomor+'\'})" style="'+(kita?'border-color:var(--ac)':'')+'">'+
   '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'+
   '<span style="font-size:22px;font-weight:800">'+esc(k.nomor)+'</span>'+
   '<span style="font-size:16px;font-weight:700">'+esc(k.nama)+'</span>'+
   (kita?'<span class="tag z2">CALON KITA</span>':'')+(k.petahana?'<span class="tag z1">PETAHANA</span>':'<span class="tag z3">penantang</span>')+'</div>'+
   '<div class="grid g2" style="margin:10px 0"><div><div class="sub">Proyeksi suara</div><div style="font-size:20px;font-weight:800">'+n0(k.proyeksi)+'</div></div>'+
   '<div><div class="sub">Share</div><div style="font-size:20px;font-weight:800">'+pp(k.persen)+'</div></div></div>'+
   '<div class="bar" style="height:8px"><i style="width:'+Math.min(100,k.persen)+'%;background:'+(kita?'#38bdf8':k.petahana?'#ef4444':'#8296b3')+'"></i></div>'+
   bio.map(b=>'<div class="row"><span class="sub">'+b[0]+'</span><b style="font-weight:500;text-align:right;white-space:normal;max-width:60%">'+esc(b[1])+'</b></div>').join('')+
   '<div class="grid g2" style="margin-top:10px">'+
   '<div class="card" style="background:#22c55e10"><h3>Kekuatan</h3><div style="white-space:normal">'+esc(k.kekuatan||'—')+'</div></div>'+
   '<div class="card" style="background:#ef444410"><h3>Kelemahan</h3><div style="white-space:normal">'+esc(k.kelemahan||'—')+'</div></div></div>'+
   '<h3 style="margin-top:12px">5 wilayah terkuat</h3>'+
   (k.wilayah_terkuat||[]).map(w=>'<div class="row"><span>'+esc(w.nama)+'</span><b>'+n0(w.suara)+' <span class="sub">'+pc(w.share)+'</span></b></div>').join('')+
   '<div class="mini">Klik kartu untuk mengisi/mengubah bio (data/kandidat.csv).</div></div>'};
 const pet=kk.find(k=>k.petahana);
 document.getElementById('v-calon').innerHTML=
 '<div class="grid g4">'+
 kpi('Jumlah calon',kk.length,'klik untuk ubah daftar','',"bukaTabel('kandidat.csv')")+
 kpi('Petahana',pet?esc(pet.nama):'tidak ada',pet?esc(pet.jabatan_sekarang||''):'kursi kosong — pertarungan terbuka',pet?'dn':'up',pet?"bukaTabel('kandidat.csv',{nomor:'"+pet.nomor+"'})":"bukaTabel('kandidat.csv')")+
 kpi('Selisih ke lawan terkuat',pp(D.ringkas.margin_share)+' poin',n0(Math.abs(D.ringkas.gap))+' suara','',"go('target')")+
 kpi('Head-to-head',kk.map(k=>k.nomor+': '+pp(k.persen)).join(' · '),'klik untuk simulasi','',"go('simulasi')")+
 '</div><div class="grid g3" style="margin-top:12px">'+kk.map(kartu).join('')+'</div>'+
 '<div class="card" style="margin-top:12px"><h3>Peta perebutan per wilayah — klik baris</h3><table><thead><tr><th>Wilayah</th>'+
 kk.map(k=>'<th class="num">'+esc(k.nama)+(k.petahana?' (petahana)':'')+'</th>').join('')+'<th>Unggul</th></tr></thead><tbody>'+
 D.wilayah.map(w=>{const urut=kk.map(k=>({k,v:w.proyeksi[k.nomor]||0})).sort((a,b)=>b.v-a.v);
  return '<tr class="klik" onclick="bukaWilayah(\''+w.kode+'\')"><td>'+wlink(w)+'</td>'+
  kk.map(k=>'<td class="num'+(urut[0].k.nomor===k.nomor?' up':'')+'">'+n0(w.proyeksi[k.nomor])+' <span class="sub">'+pc(w.share[k.nomor])+'</span></td>').join('')+
  '<td>'+(urut[0].k.nomor===K()?'<span class="tag z0">kita</span>':'<span class="tag z1">'+esc(urut[0].k.nama)+'</span>')+'</td></tr>'}).join('')+
 '</tbody></table></div>'}

/* ============ KEKUATAN PARTAI ============ */
function aggPartai(){const a={};D.wilayah.forEach(w=>w.partai_rinci.forEach(p=>{
 const x=a[p.partai]||(a[p.partai]={partai:p.partai,koalisi:p.koalisi,suara:0,pengurus:0,saksi:0,mesin:0,dukungan:0,n:0,wil:[]});
 x.suara+=p.suara_lalu;x.pengurus+=p.pengurus;x.saksi+=p.saksi_disiapkan;x.mesin+=p.mesin;x.dukungan+=p.dukungan;x.n++;
 x.wil.push({kode:w.kode,nama:w.nama,suara:p.suara_lalu,mesin:p.mesin,dukungan:p.dukungan})}));
 return Object.values(a).map(x=>({...x,mesin:x.mesin/x.n,dukungan:x.dukungan/x.n})).sort((p,q)=>q.suara-p.suara)}
function vPartai(){const A=aggPartai(),tot=A.reduce((s,x)=>s+x.suara,0)||1;
 const koal=A.filter(x=>x.koalisi);
 document.getElementById('v-partai').innerHTML='<div class="grid g4">'+
 kpi('Basis koalisi pengusung',pc(koal.reduce((s,x)=>s+x.suara,0)/tot),koal.map(x=>x.partai).join(' + '),'',"go('konfig')")+
 kpi('Pengurus aktif koalisi',n0(koal.reduce((s,x)=>s+x.pengurus,0)),'orang di seluruh wilayah','',"bukaTabel('partai.csv')")+
 kpi('Saksi disiapkan partai',n0(koal.reduce((s,x)=>s+x.saksi,0)),'dari '+n0(D.saksi.butuh/D.konfigurasi.saksi_per_tps)+' TPS','',"go('saksi')")+
 kpi('Mesin partai rata-rata',pc(koal.reduce((s,x)=>s+x.mesin,0)/(koal.length||1)),'0–1, dari data/partai.csv','',"bukaTabel('partai.csv')")+
 '</div><div class="card" style="margin-top:12px"><h3>Kekuatan partai — klik baris untuk ubah data</h3>'+
 '<table><thead><tr><th>Partai</th><th>Posisi</th><th class="num">Suara lalu</th><th class="num">%</th><th class="num">Pengurus</th><th class="num">Saksi siap</th><th class="num">Mesin</th><th class="num">Dukungan ke kita</th><th style="width:20%">Kekuatan relatif</th></tr></thead><tbody>'+
 A.map(x=>'<tr class="klik" onclick="bukaTabel(\'partai.csv\',{partai:\''+x.partai+'\'})"><td><b>'+esc(x.partai)+'</b></td>'+
  '<td>'+(x.koalisi?'<span class="tag z0">koalisi kita</span>':'<span class="tag z3">luar koalisi</span>')+'</td>'+
  '<td class="num">'+n0(x.suara)+'</td><td class="num">'+pc(x.suara/tot)+'</td><td class="num">'+n0(x.pengurus)+'</td>'+
  '<td class="num">'+n0(x.saksi)+'</td><td class="num">'+pc(x.mesin)+'</td><td class="num">'+pc(x.dukungan)+'</td>'+
  '<td><div class="bar"><i style="width:'+(x.suara/tot*100)+'%;background:'+(x.koalisi?'#22c55e':'#64748b')+'"></i></div></td></tr>').join('')+
 '</tbody></table></div>'+
 '<div class="card" style="margin-top:12px"><h3>Matriks partai × wilayah (mesin partai) — klik sel</h3><div class="scroll"><table><thead><tr><th>Wilayah</th>'+
 A.map(x=>'<th class="num">'+esc(x.partai)+'</th>').join('')+'</tr></thead><tbody>'+
 D.wilayah.map(w=>'<tr><td>'+wlink(w)+'</td>'+A.map(x=>{const c=w.partai_rinci.find(p=>p.partai===x.partai);
  const v=c?c.mesin:null;return '<td class="num klik" onclick="bukaWilayah(\''+w.kode+'\',\'partai.csv\')" style="background:'+(v==null?'transparent':warna(v)+'33')+'">'+(v==null?'—':pc(v))+'</td>'}).join('')+'</tr>').join('')+
 '</tbody></table></div><div class="mini">Mesin partai = skor 0–1 kesiapan struktur. Bobotnya '+pc(D.konfigurasi.bobot_ikc.partai)+' di dalam IKC.</div></div>'}

/* ============ KEKUATAN ORMAS ============ */
function aggOrmas(){const a={};D.wilayah.forEach(w=>w.ormas_rinci.forEach(o=>{
 const x=a[o.ormas]||(a[o.ormas]={ormas:o.ormas,anggota:0,pengurus:0,jangkauan:0,lawan:0,wil:0,pengaruh:0,n:0});
 x.anggota+=o.anggota;x.pengurus+=o.pengurus;x.wil++;x.pengaruh+=o.pengaruh;x.n++;
 if(o.jangkauan>=0)x.jangkauan+=o.jangkauan;else x.lawan+=-o.jangkauan}));
 return Object.values(a).map(x=>({...x,pengaruh:x.pengaruh/x.n})).sort((p,q)=>q.anggota-p.anggota)}
function vOrmas(){const A=aggOrmas(),pro=A.reduce((s,x)=>s+x.jangkauan,0),kon=A.reduce((s,x)=>s+x.lawan,0);
 document.getElementById('v-ormas').innerHTML='<div class="grid g4">'+
 kpi('Jangkauan ormas pro-kita',n0(pro),'anggota × kedekatan × pengaruh','up',"bukaTabel('ormas.csv')")+
 kpi('Jangkauan ormas ke lawan',n0(kon),(kon>pro?'lebih besar dari kita — bahaya':'di bawah kita'),kon>pro?'dn':'',"go('wilayah')")+
 kpi('Total anggota terdata',n0(A.reduce((s,x)=>s+x.anggota,0)),pc(A.reduce((s,x)=>s+x.anggota,0)/D.ringkas.dpt)+' dari DPT','',"bukaTabel('ormas.csv')")+
 kpi('Bobot ormas di IKC',pc(D.konfigurasi.bobot_ikc.ormas),'klik untuk ubah bobot','',"go('konfig')")+
 '</div><div class="card" style="margin-top:12px"><h3>Ormas — klik baris untuk ubah data</h3><table><thead><tr><th>Ormas</th><th class="num">Anggota</th><th class="num">Pengurus</th><th class="num">Wilayah</th><th class="num">Pengaruh</th><th class="num">Jangkauan pro</th><th class="num">Jangkauan lawan</th><th style="width:18%">Arah</th></tr></thead><tbody>'+
 A.map(x=>'<tr class="klik" onclick="bukaTabel(\'ormas.csv\',{ormas:\''+x.ormas+'\'})"><td><b>'+esc(x.ormas)+'</b></td>'+
  '<td class="num">'+n0(x.anggota)+'</td><td class="num">'+n0(x.pengurus)+'</td><td class="num">'+n0(x.wil)+'</td>'+
  '<td class="num">'+pc(x.pengaruh)+'</td><td class="num up">'+n0(x.jangkauan)+'</td><td class="num dn">'+n0(x.lawan)+'</td>'+
  '<td><div style="position:relative;height:14px"><div style="position:absolute;left:50%;width:1px;height:100%;background:#334155"></div>'+
  '<div style="position:absolute;top:2px;height:10px;border-radius:3px;background:'+(x.lawan>x.jangkauan?'#ef4444':'#22c55e')+';'+
  (x.lawan>x.jangkauan?'right:50%;width:'+Math.min(49,x.lawan/(x.anggota||1)*49):'left:50%;width:'+Math.min(49,x.jangkauan/(x.anggota||1)*49))+'%"></div></div></td></tr>').join('')+
 '</tbody></table><div class="mini">Kedekatan −1..1 diisi tim lapangan. Pendekatan ke ormas lewat silaturahmi & program (aturan DNA D11) — bukan tekanan atau politisasi keyakinan.</div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Ormas per wilayah — klik baris</h3><table><thead><tr><th>Wilayah</th><th class="num">Jangkauan pro</th><th class="num">Jangkauan lawan</th><th class="num">Skor ormas</th><th>Ormas terbesar</th></tr></thead><tbody>'+
 [...D.wilayah].sort((a,b)=>(b.ormas_lawan-b.ormas_jangkauan)-(a.ormas_lawan-a.ormas_jangkauan)).map(w=>{
  const top=[...w.ormas_rinci].sort((a,b)=>b.anggota-a.anggota).slice(0,2).map(o=>o.ormas+' ('+n0(o.anggota)+')').join(', ');
  return '<tr class="klik" onclick="bukaWilayah(\''+w.kode+'\',\'ormas.csv\')"><td>'+wlink(w)+'</td>'+
  '<td class="num up">'+n0(w.ormas_jangkauan)+'</td><td class="num dn">'+n0(w.ormas_lawan)+'</td>'+
  '<td class="num">'+pc(w.ormas)+'</td><td class="sub">'+esc(top||'—')+'</td></tr>'}).join('')+'</tbody></table></div>'}

/* ============ RISIKO (ALADDIN) ============ */
function vRisiko(){const r=D.risiko;
 document.getElementById('v-risiko').innerHTML='<div class="grid g4">'+
 kpi('VaR 95%',n0(r.var95)+' suara','kerugian suara wajar terburuk ('+pp(r.var95_persen)+')','dn',"go('simulasi')")+
 kpi('Volatilitas (σ)',pp(r.sigma*100),'simpangan proyeksi suara kita','',"go('konfig')")+
 kpi('Konsentrasi (HHI)',n1(r.hhi*1000)/1000+'',n1(r.wilayah_efektif)+' wilayah efektif — makin kecil makin rapuh','',"go('wilayah')")+
 kpi('Tracking error ke target',pp(r.tracking_error),'jarak share sekarang ke share target','',"go('target')")+
 '</div><div class="grid g2" style="margin-top:12px">'+
 '<div class="card"><h3>Paparan portofolio suara terhadap faktor</h3>'+
 Object.keys(r.paparan_portofolio).map(f=>'<div class="row"><span class="sub">'+f.replace(/_/g,' ')+' <span class="sub">(vol '+pc(r.volatilitas[f])+')</span></span>'+
  '<b>'+pc(r.paparan_portofolio[f])+'</b></div><div class="bar" style="margin-bottom:6px"><i style="width:'+(r.paparan_portofolio[f]*100)+'%;background:'+warna(1-r.paparan_portofolio[f])+'"></i></div>').join('')+
 '<div class="mini">Paparan 1,0 = suara kita sepenuhnya bergantung pada faktor itu. Ketergantungan turnout selalu 1,0 — itulah sebabnya menaikkan kehadiran pemilih adalah pengungkit terbesar.</div></div>'+
 '<div class="card"><h3>Korelasi antar faktor</h3><table><thead><tr><th></th>'+r.faktor.map(f=>'<th class="num">'+f.slice(0,8)+'</th>').join('')+'</tr></thead><tbody>'+
 r.faktor.map((f,i)=>'<tr><td class="sub">'+f.replace(/_/g,' ')+'</td>'+r.korelasi[i].map(v=>'<td class="num" style="background:rgba('+(v<0?'239,68,68':'34,197,94')+','+Math.abs(v)*0.35+')">'+n1(v*100)/100+'</td>').join('')+'</tr>').join('')+
 '</tbody></table><div class="mini">Dihitung silang-wilayah dari data nyata: kalau dua faktor bergerak bersama, guncangan tidak saling menutupi.</div></div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Uji tekanan — klik baris untuk simulasi</h3><table><thead><tr><th>Skenario</th><th>Keterangan</th><th class="num">Dampak</th><th class="num">Suara</th><th class="num">Selisih</th><th class="num">Margin</th><th>Hasil</th></tr></thead><tbody>'+
 r.uji_tekanan.map(u=>'<tr class="klik" onclick="go(\'simulasi\')"><td><b>'+esc(u.nama)+'</b></td><td class="sub">'+esc(u.ket)+'</td>'+
  '<td class="num '+(u.dampak_persen<0?'dn':'up')+'">'+pp(u.dampak_persen)+'</td><td class="num">'+n0(u.suara)+'</td>'+
  '<td class="num '+(u.selisih_suara<0?'dn':'up')+'">'+n0(u.selisih_suara)+'</td><td class="num">'+pp(u.margin)+'</td>'+
  '<td>'+(u.menang?'<span class="tag z0">masih menang</span>':'<span class="tag z1">KALAH</span>')+'</td></tr>').join('')+
 '</tbody></table></div>'+
 '<div class="card" style="margin-top:12px"><h3>Kontribusi risiko per wilayah — klik baris</h3><table><thead><tr><th>Wilayah</th><th class="num">Bobot suara</th><th class="num">Kontribusi risiko</th><th class="num">% dari total</th><th class="num">Ketidakpastian sendiri</th><th style="width:20%"></th></tr></thead><tbody>'+
 r.kontribusi.map(k=>'<tr class="klik" onclick="bukaWilayah(\''+k.kode+'\')"><td>'+esc(k.nama)+'</td><td class="num">'+pc(k.bobot)+'</td>'+
  '<td class="num">'+pp(k.kontribusi*100)+'</td><td class="num">'+pp(k.kontribusi_persen)+'</td><td class="num">'+pc(k.idio)+'</td>'+
  '<td><div class="bar"><i style="width:'+Math.min(100,k.kontribusi_persen*4)+'%;background:'+warna(1-k.kontribusi_persen/25)+'"></i></div></td></tr>').join('')+
 '</tbody></table><div class="mini">'+esc(r.catatan)+'</div></div>'}

/* ============ ONTOLOGI (PALANTIR) ============ */
function vOntologi(){const o=D.ontologi;
 document.getElementById('v-ontologi').innerHTML='<div class="grid g4">'+
 kpi('Objek',n0(o.jumlah.entitas),'wilayah, partai, ormas, isu, kandidat','',"go('data')")+
 kpi('Hubungan',n0(o.jumlah.hubungan),'sambungan antar objek dari 12 silo data','',"go('data')")+
 kpi('Anomali',n0(o.jumlah.anomali),'ketidakcocokan antar sumber — klik untuk daftar',o.jumlah.anomali?'wrn':'up',"scrollTo(0,document.getElementById('anomBox').offsetTop)")+
 kpi('Objek paling berpengaruh',esc((o.entitas[0]||{}).nama||'—'),'sentralitas '+pc((o.entitas[0]||{}).sentralitas),'',"go('partai')")+
 '</div><div class="grid g21" style="margin-top:12px">'+
 '<div class="card"><h3>Graf hubungan — klik simpul</h3><canvas id="cvG" height="470"></canvas>'+
 '<div class="legend"><span><i style="background:#38bdf8"></i>Wilayah</span><span><i style="background:#22c55e"></i>Partai</span>'+
 '<span><i style="background:#a78bfa"></i>Ormas</span><span><i style="background:#f59e0b"></i>Isu</span><span><i style="background:#ef4444"></i>Kandidat</span></div></div>'+
 '<div class="card"><h3>Objek menurut pengaruh</h3><div class="scroll" style="max-height:470px">'+
 o.entitas.slice(0,40).map(e=>'<div class="row klik" onclick="klikEntitas(\''+esc(e.id)+'\')"><span>'+esc(e.nama)+
  ' <span class="sub">'+esc(e.tipe)+'</span></span><b>'+pc(e.sentralitas)+'</b></div>').join('')+'</div></div></div>'+
 '<div class="card" style="margin-top:12px" id="anomBox"><h3>Anomali & resolusi entitas — klik untuk membuka wilayahnya</h3>'+
 (o.anomali.length?o.anomali.map(a=>'<div class="row klik" onclick="bukaWilayah(\''+a.kode+'\')" style="align-items:flex-start">'+
  '<span style="max-width:70%;white-space:normal"><b>'+esc(a.jenis)+'</b> — '+esc(a.wilayah)+
  '<div class="sub">'+esc(a.bukti)+'</div><div class="sub ac">→ '+esc(a.tindakan)+'</div></span>'+
  '<b class="'+(a.skor>.7?'dn':'wrn')+'">skor '+n1(a.skor*100)/100+'</b></div>').join(''):'<div class="sub">tidak ada anomali</div>')+
 '<div class="mini">Anomali muncul dari membandingkan silo yang biasanya tidak pernah bertemu: DPT vs KK, survei vs basis partai, klaim relawan vs pendataan, anggaran vs kekuatan, ormas vs zona, suara lama vs DPT.</div></div>'}
function klikEntitas(id){const t=id.split(':')[0],n=id.slice(2);
 if(t==='W')return bukaWilayah(n);if(t==='P')return bukaTabel('partai.csv',{partai:n});
 if(t==='O')return bukaTabel('ormas.csv',{ormas:n});if(t==='I')return go('wilayah',{filter:{isu:n}});
 return bukaTabel('kandidat.csv')}
function grafOntologi(){const c=document.getElementById('cvG');if(!c||!c.offsetWidth||!D)return;
 const o=D.ontologi,dpr=devicePixelRatio||1,W=c.offsetWidth,H=+(c.dataset.h||(c.dataset.h=c.getAttribute('height')));
 c.width=W*dpr;c.style.height=H+'px';c.height=H*dpr;const g=c.getContext('2d');g.scale(dpr,dpr);g.clearRect(0,0,W,H);
 const TIPE={Wilayah:'#38bdf8',Partai:'#22c55e',Ormas:'#a78bfa',Isu:'#f59e0b',Kandidat:'#ef4444'};
 const grup={};o.entitas.forEach(e=>(grup[e.tipe]=grup[e.tipe]||[]).push(e));
 const tipe=Object.keys(grup),pos={};
 tipe.forEach((t,ti)=>{const arr=grup[t],R=Math.min(W,H)/2-40,cx=W/2,cy=H/2;
  const ring=R*(0.35+0.65*ti/Math.max(1,tipe.length-1));
  arr.forEach((e,i)=>{const a=i/arr.length*Math.PI*2+ti*0.4;
   pos[e.id]={x:cx+Math.cos(a)*ring,y:cy+Math.sin(a)*ring,e:e}})});
 const mx=Math.max(...o.hubungan.map(h=>h.bobot))||1;
 o.hubungan.forEach(h=>{const a=pos[h.dari],b=pos[h.ke];if(!a||!b)return;
  g.strokeStyle='rgba(56,189,248,'+(0.05+0.35*h.bobot/mx)+')';g.lineWidth=.4+1.6*h.bobot/mx;
  g.beginPath();g.moveTo(a.x,a.y);g.quadraticCurveTo((a.x+b.x)/2+(b.y-a.y)*.12,(a.y+b.y)/2+(a.x-b.x)*.12,b.x,b.y);g.stroke()});
 const pts=[];Object.values(pos).forEach(p=>{const r=4+10*(p.e.sentralitas||0);pts.push({...p,r});
  g.beginPath();g.arc(p.x,p.y,r,0,7);g.fillStyle=TIPE[p.e.tipe]||'#8296b3';g.globalAlpha=.9;g.fill();g.globalAlpha=1;
  if(r>7){g.fillStyle='#cbd5e1';g.font='600 9px system-ui';g.textAlign='center';g.fillText(p.e.nama.slice(0,14),p.x,p.y-r-3)}});
 c.onmousemove=e=>{const b=c.getBoundingClientRect(),p=pts.find(p=>Math.hypot(p.x-(e.clientX-b.left),p.y-(e.clientY-b.top))<p.r+3);
  c.style.cursor=p?'pointer':'default';
  tip(e,p?'<b>'+esc(p.e.nama)+'</b><br>'+esc(p.e.tipe)+' · sentralitas '+pc(p.e.sentralitas)+(p.e.ket?'<br>'+esc(p.e.ket):'')+'<br><i>klik untuk buka</i>':null)};
 c.onmouseleave=()=>tip(null,null);
 c.onclick=e=>{const b=c.getBoundingClientRect(),p=pts.find(p=>Math.hypot(p.x-(e.clientX-b.left),p.y-(e.clientY-b.top))<p.r+3);
  if(p)klikEntitas(p.e.id)}}

/* ============ WORKER AI ============ */
async function vWorker(){try{WORKER=await api('worker.json?'+Date.now())}catch(e){WORKER=null}
 const el=document.getElementById('v-worker');if(!el)return;
 if(!WORKER)return el.innerHTML='<div class="card"><h3>Worker AI</h3><div class="sub">worker.json belum ada. <button class="act" onclick="hitungUlang()">Jalankan sekarang</button></div></div>';
 const w=WORKER,p=w.papan;
 el.innerHTML='<div class="card" style="border-color:'+(w.cukup_data?'var(--ln)':'var(--wr)')+'">'+
 '<h3>Briefing worker <span class="sub">· '+esc(w.dibuat.replace('T',' '))+' · '+esc(w.otak)+'</span></h3>'+
 '<div style="font-size:15px;font-weight:700;'+(D.ringkas.gap>0?'color:var(--bd)':'')+'">'+esc(w.baris_pertama)+'</div>'+
 (w.narasi?'<div style="margin-top:8px;white-space:pre-wrap">'+esc(w.narasi)+'</div>':
  '<div class="mini">Narasi AI tidak ditulis: '+esc(w.otak)+'. Perintah di bawah tetap sahih karena lahir dari aturan + angka mesin, bukan dari model bahasa.</div>')+
 '<ul class="mini">'+w.catatan.map(c=>'<li>'+esc(c)+'</li>').join('')+'</ul>'+
 '<div style="margin-top:8px"><button class="act" onclick="hitungUlang().then(vWorker)">Jalankan ulang worker</button> '+
 '<button class="gh" onclick="lihatDNA()">Lihat DNA ('+w.dna.aturan.length+' aturan)</button></div></div>'+
 '<div class="grid g4" style="margin-top:12px">'+
 kpi('Perintah lolos DNA',n0(w.hitungan.lolos),'dari '+n0(w.hitungan.dibuat)+' yang dibuat','',"lihatDitolak()")+
 kpi('Ditolak DNA',n0(w.hitungan.ditolak),'klik untuk alasan penolakan',w.hitungan.ditolak?'wrn':'up',"lihatDitolak()")+
 kpi('Dampak rencana',n0(p.dampak_total)+' suara',p.tertutup?'cukup menutup gap':'belum menutup gap',p.tertutup?'up':'dn',"go('target')")+
 kpi('Biaya rencana',rp(p.biaya_total),rp(p.rp_per_suara)+' per suara','',"go('anggaran')")+
 '</div><div class="card" style="margin-top:12px"><h3>Perintah kerja — klik baris untuk buka wilayahnya</h3>'+
 '<table><thead><tr><th class="num">#</th><th>Kategori</th><th>Perintah</th><th>Siapa</th><th class="num">Dampak</th><th class="num">Biaya</th><th class="num">Rp/suara</th><th>Tenggat</th><th class="num">Skor</th></tr></thead><tbody>'+
 w.perintah.map((x,i)=>'<tr class="klik" onclick="lihatPerintah('+i+')"><td class="num">'+(i+1)+'</td>'+
  '<td><span class="tag '+({saksi:'z1',risiko:'z1',verifikasi:'z2',partai:'z0',ormas:'z2',kampanye:'z3',drone:'z3',caleg:'z0'}[x.kategori]||'z3')+'">'+esc(x.kategori)+'</span></td>'+
  '<td style="white-space:normal;max-width:340px">'+esc(x.judul)+'</td><td class="sub">'+esc(x.siapa)+'</td>'+
  '<td class="num">'+n0(x.dampak_suara)+'</td><td class="num">'+rp(x.biaya)+'</td>'+
  '<td class="num">'+(x.rp_per_suara?rp(x.rp_per_suara):'—')+'</td><td class="sub">'+esc(x.tenggat)+'</td>'+
  '<td class="num"><b>'+n1(x.skor*100)+'</b></td></tr>').join('')+
 '</tbody></table><div class="mini">Skor = prioritas kategori × dampak relatif × efisiensi biaya × urgensi hari. Perintah tanpa angka rujukan otomatis dibuang (DNA D1).</div></div>'}
function lihatPerintah(i){const x=WORKER.perintah[i];
 modal(esc(x.judul),'<div class="row"><span class="sub">Kategori</span><b>'+esc(x.kategori)+'</b></div>'+
 '<div class="row"><span class="sub">Wilayah</span><b>'+esc(x.wilayah)+'</b></div>'+
 '<div class="row"><span class="sub">Siapa yang mengerjakan</span><b>'+esc(x.siapa)+'</b></div>'+
 '<div class="row"><span class="sub">Tenggat</span><b>'+esc(x.tenggat)+'</b></div>'+
 '<div class="row"><span class="sub">Dampak</span><b>'+n0(x.dampak_suara)+' suara</b></div>'+
 '<div class="row"><span class="sub">Biaya</span><b>'+rp(x.biaya)+(x.rp_per_suara?' ('+rp(x.rp_per_suara)+'/suara)':'')+'</b></div>'+
 '<div class="card" style="margin-top:10px;background:var(--pnl2)"><h3>Langkah</h3><div style="white-space:normal">'+esc(x.langkah)+'</div></div>'+
 '<div class="card" style="margin-top:10px;background:var(--pnl2)"><h3>Angka rujukan (DNA D1)</h3><div class="sub" style="white-space:normal">'+esc(x.rujukan)+'</div>'+
 '<div class="mini">Dasar aturan: '+esc(x.dasar)+'</div></div>'+
 '<div style="margin-top:10px"><button class="gh" onclick="tutup();go(\'wilayah\',{filter:{cari:\''+esc(x.wilayah)+'\'}})">Buka wilayah</button></div>',760)}
function lihatDitolak(){const d=WORKER.ditolak;
 modal('Perintah yang ditolak gerbang DNA ('+d.length+')',
 (d.length?'<table><thead><tr><th>Aturan</th><th>Perintah</th><th>Alasan</th></tr></thead><tbody>'+
  d.map(x=>'<tr><td><b>'+esc(x.aturan)+'</b></td><td style="white-space:normal">'+esc(x.perintah)+'</td><td class="sub" style="white-space:normal">'+esc(x.alasan)+'</td></tr>').join('')+'</tbody></table>':'<div class="sub">tidak ada</div>')+
 '<div class="mini">Penolakan adalah fitur: worker boleh berpikir bebas, tapi hanya perintah yang lolos DNA yang boleh sampai ke tim.</div>',860)}
function lihatDNA(){modal(esc(WORKER.dna.nama)+' <span class="sub">v'+esc(WORKER.dna.versi)+'</span>',
 WORKER.dna.aturan.map(a=>'<div class="row" style="align-items:flex-start"><span style="max-width:78%;white-space:normal">'+
 '<b>'+esc(a.kode)+' · '+esc(a.nama)+'</b><div class="sub">'+esc(a.isi)+'</div></span><span class="tag z2">'+esc(a.penegakan)+'</span></div>').join('')+
 '<div class="mini">DNA ada di dna.json — ubah di sana kalau aturan mainnya berubah.</div>',860)}

/* ============ PETA DRONE BERGERAK + JARINGAN ============ */
function jaringanWilayah(){/* sambungan antar wilayah: berbagi ormas / partai koalisi kuat / tetangga terdekat */
 const E=[];const W=D.wilayah;
 for(let i=0;i<W.length;i++)for(let j=i+1;j<W.length;j++){
  const a=W[i],b=W[j];const jarak=Math.hypot(a.lat-b.lat,a.lon-b.lon)*111;
  const ormasSama=a.ormas_rinci.filter(o=>b.ormas_rinci.some(x=>x.ormas===o.ormas&&x.kedekatan>0&&o.kedekatan>0)).length;
  const partaiSama=a.partai_rinci.filter(p=>p.koalisi&&p.mesin>.5&&b.partai_rinci.some(x=>x.partai===p.partai&&x.mesin>.5)).length;
  const bobot=(ormasSama*.6+partaiSama*.5)/(1+jarak/6);
  if(bobot>.35||jarak<6)E.push({a:i,b:j,bobot:bobot,jarak:jarak})}
 return E.sort((x,y)=>y.bobot-x.bobot).slice(0,44)}
function petaAnim(){const c=document.getElementById('cvA');if(!c||!D)return;
 if(c._siap)return;c._siap=true;
 const EDGES=jaringanWilayah();
 const drones=D.drone.misi.filter(m=>m.sortie>0).map((m,i)=>({m:m,fase:i/Math.max(1,D.drone.misi.length),arah:1}));
 function frame(){
  if(!document.getElementById('cvA')){c._siap=false;return}
  const vis=!document.getElementById('v-drone').classList.contains('hide')||!document.getElementById('v-peta').classList.contains('hide');
  if(vis)gambar();requestAnimationFrame(frame)}
 function gambar(){
  const dpr=devicePixelRatio||1,W=c.offsetWidth,H=+(c.dataset.h||(c.dataset.h=c.getAttribute('height')));
  if(!W)return;c.width=W*dpr;c.style.height=H+'px';c.height=H*dpr;
  const g=c.getContext('2d');g.scale(dpr,dpr);g.clearRect(0,0,W,H);
  if(ANIM.jalan)ANIM.t+=0.004*ANIM.kecepatan;
  g.strokeStyle='#0f1826';for(let i=0;i<W;i+=40){g.beginPath();g.moveTo(i,0);g.lineTo(i,H);g.stroke()}
  for(let j=0;j<H;j+=40){g.beginPath();g.moveTo(0,j);g.lineTo(W,j);g.stroke()}
  const P=D.wilayah.map(w=>{const[x,y,s]=proj(w,W,H);return{w,x,y,s}});
  const posko=P.reduce((a,b)=>(b.w.ikc||0)>(a.w.ikc||0)?b:a,P[0]);
  if(ANIM.jaringan)EDGES.forEach((e,i)=>{const a=P[e.a],b=P[e.b];if(!a||!b)return;
   g.strokeStyle='rgba(56,189,248,'+(0.06+0.22*Math.min(1,e.bobot))+')';g.lineWidth=.6+1.4*Math.min(1,e.bobot);
   g.beginPath();g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.stroke();
   const t=(ANIM.t*1.6+i*0.07)%1,px=a.x+(b.x-a.x)*t,py=a.y+(b.y-a.y)*t;
   g.beginPath();g.arc(px,py,1.8,0,7);g.fillStyle='#7dd3fc';g.fill()});
  P.forEach(p=>{const R=Math.sqrt(p.w.luas_km2/Math.PI)*p.s/111.32;
   g.strokeStyle='#38bdf82e';g.lineWidth=1;g.beginPath();g.arc(p.x,p.y,R,0,7);g.stroke();
   g.beginPath();g.arc(p.x,p.y,5+9*Math.sqrt(p.w.dpt/Math.max(...D.wilayah.map(v=>v.dpt))),0,7);
   g.fillStyle=warna((p.w.ikc||0)/100);g.globalAlpha=.75;g.fill();g.globalAlpha=1;
   g.strokeStyle='#0a0e14';g.stroke();
   g.fillStyle='#cbd5e1';g.font='600 10px system-ui';g.textAlign='center';g.fillText(p.w.kecamatan,p.x,p.y+R+11)});
  // posko + lingkar relay
  const pulse=(Math.sin(ANIM.t*6)+1)/2;
  g.strokeStyle='rgba(167,139,250,'+(0.5-0.35*pulse)+')';g.lineWidth=1.5;
  g.beginPath();g.arc(posko.x,posko.y,18+22*pulse,0,7);g.stroke();
  g.fillStyle='#a78bfa';g.beginPath();g.arc(posko.x,posko.y,5,0,7);g.fill();
  g.fillStyle='#cbd5e1';g.font='700 10px system-ui';g.fillText('POSKO',posko.x,posko.y-12);
  // drone bergerak menyusuri jalur serpentin
  const spot=[];
  drones.forEach((d,i)=>{const p=P.find(x=>x.w.kode===d.m.kode);if(!p)return;
   const R=Math.sqrt(p.w.luas_km2/Math.PI)*p.s/111.32;
   const sp=Math.max(3,D.drone.jarak_jalur_m/1000*p.s/111.32),jalur=Math.max(2,Math.floor(2*R/sp));
   const t=(ANIM.t*0.6+d.fase)%1,idx=Math.floor(t*jalur),sisa=t*jalur-idx;
   const yy=p.y-R+sp*(idx+.5),bolak=idx%2?1-sisa:sisa;
   const lebar=Math.sqrt(Math.max(0,R*R-(yy-p.y)*(yy-p.y)));
   const x=p.x-lebar+2*lebar*bolak;
   g.strokeStyle='rgba(56,189,248,.35)';g.lineWidth=.8;
   g.beginPath();g.moveTo(p.x-lebar,yy);g.lineTo(p.x+lebar,yy);g.stroke();
   const warnaD=d.m.status==='selesai'?'#22c55e':d.m.status==='terbang'?'#38bdf8':'#f59e0b';
   g.save();g.translate(x,yy);g.rotate(idx%2?Math.PI:0);
   g.fillStyle=warnaD;g.beginPath();g.moveTo(6,0);g.lineTo(-4,3.6);g.lineTo(-4,-3.6);g.closePath();g.fill();
   g.strokeStyle=warnaD+'88';g.lineWidth=1;g.beginPath();g.arc(0,0,7+2*Math.sin(ANIM.t*14+i),0,7);g.stroke();g.restore();
   // tautan ke posko (jaringan relay)
   if(ANIM.jaringan){g.strokeStyle='rgba(167,139,250,.28)';g.setLineDash([3,4]);
    g.lineDashOffset=-ANIM.t*90;g.beginPath();g.moveTo(x,yy);g.lineTo(posko.x,posko.y);g.stroke();g.setLineDash([])}
   spot.push({x,y:yy,d})});
  c.onmousemove=e=>{const b=c.getBoundingClientRect(),mx=e.clientX-b.left,my=e.clientY-b.top;
   const s=spot.find(s=>Math.hypot(s.x-mx,s.y-my)<9),p=P.find(p=>Math.hypot(p.x-mx,p.y-my)<12);
   c.style.cursor=(s||p)?'pointer':'crosshair';
   tip(e,s?'<b>Drone · '+esc(s.d.m.nama)+'</b><br>'+esc(s.d.m.tujuan)+'<br>'+n0(s.d.m.sortie)+' sortie · '+n1(s.d.m.jam_terbang)+' jam · '+rp(s.d.m.biaya)+'<br>status '+esc(s.d.m.status)+'<br><i>klik untuk atur misi</i>'
    :p?'<b>'+esc(p.w.nama)+'</b><br>DPT '+n0(p.w.dpt)+' · IKC '+n1(p.w.ikc)+'<br>'+n0(p.w.dpt/p.w.luas_km2)+' pemilih/km²<br><i>klik untuk buka</i>':null)};
  c.onmouseleave=()=>tip(null,null);
  c.onclick=e=>{const b=c.getBoundingClientRect(),mx=e.clientX-b.left,my=e.clientY-b.top;
   const s=spot.find(s=>Math.hypot(s.x-mx,s.y-my)<9);if(s)return bukaTabel('drone_misi.csv',{kode_wilayah:s.d.m.kode});
   const p=P.find(p=>Math.hypot(p.x-mx,p.y-my)<12);if(p)bukaWilayah(p.w.kode)};
 }
 frame()}

/* sisipkan peta bergerak ke tab Sistem Drone + panggil graf ontologi */
const _vDrone=vDrone;vDrone=function(){_vDrone();
 const el=document.getElementById('v-drone');
 el.insertAdjacentHTML('afterbegin','<div class="card" style="margin-bottom:12px"><h3 style="display:flex;gap:10px;align-items:center">'+
 'Peta operasi bergerak — drone menyusuri jalur, garis biru = jaringan wilayah terhubung, garis ungu = relay ke posko'+
 '<button class="gh" style="margin-left:auto" onclick="ANIM.jalan=!ANIM.jalan;this.textContent=ANIM.jalan?\'Jeda\':\'Jalan\'">Jeda</button>'+
 '<button class="gh" onclick="ANIM.jaringan=!ANIM.jaringan">Jaringan on/off</button>'+
 '<select onchange="ANIM.kecepatan=+this.value"><option value="0.5">0,5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></h3>'+
 '<canvas id="cvA" height="470"></canvas><div class="legend">'+
 '<span><i style="background:#f59e0b"></i>rencana</span><span><i style="background:#38bdf8"></i>terbang</span>'+
 '<span><i style="background:#22c55e"></i>selesai</span><span><i style="background:#a78bfa"></i>posko & relay</span>'+
 '<span onclick="bukaTabel(\'drone_misi.csv\')">+ atur misi</span></div></div>');
 requestAnimationFrame(petaAnim)};
const _render=render;render=function(){_render();requestAnimationFrame(()=>{grafOntologi();petaAnim()})};
const _go=go;go=function(k,o){_go(k,o);requestAnimationFrame(()=>{if(k==='ontologi')grafOntologi();if(k==='drone'||k==='peta')petaAnim();if(k==='worker')vWorker()})};
/* pastikan tab tambahan ikut tergambar walau data sudah termuat sebelum berkas ini jalan */
(function(){const t=setInterval(()=>{if(window.D){clearInterval(t);render()}},100);setTimeout(()=>clearInterval(t),15000)})();
