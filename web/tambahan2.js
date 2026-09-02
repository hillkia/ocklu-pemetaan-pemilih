/* Tab: Saran Menang, Struktur & Ranting, Keputusan & Pemicu, Benchmark, Ledger, Kesimpulan
   + pemilih jenis pemilihan (presiden s/d RT) dan tingkat analisis. */
(function(){
 const BARU=[['menang','Saran Menang'],['struktur','Struktur & Ranting'],['keputusan','Keputusan & Pemicu'],
  ['benchmark','Benchmark'],['ledger','Ledger'],['kesimpulan','Kesimpulan']];
 const i=TAB.findIndex(t=>t[0]==='data');TAB.splice(i<0?TAB.length:i,0,...BARU);
 const main=document.querySelector('main');
 BARU.forEach(([k])=>{const s=document.createElement('section');s.id='v-'+k;s.className='hide';main.appendChild(s)});
 window.EXTRA=(window.EXTRA||[]).concat([pilihJenis,vMenang,vStruktur,vKeputusan,vBenchmark,vLedger,vKesimpulan]);
})();
const KAT={'MENANG AMAN':'z0','MENANG TIPIS':'z2','IMBANG':'z3','KALAH TIPIS':'z1','KALAH':'z1'};

/* ---- pemilih jenis pemilihan & tingkat ---- */
function pilihJenis(){const hd=document.querySelector('.hd');if(!hd)return;
 let el=document.getElementById('pilihJenis');
 const A=D.konfigurasi.aturan_pemilihan,J=D.konfigurasi.jenis_pemilihan;
 const html='<select id="pilihJenis" title="jenis pemilihan" onchange="gantiJenis(this.value)">'+
  Object.keys(A).map(k=>'<option value="'+k+'"'+(k===J?' selected':'')+'>'+esc(A[k].nama)+'</option>').join('')+'</select>'+
  '<select id="pilihTingkat" title="tingkat analisis" onchange="gantiTingkat(this.value)">'+
  ['provinsi','kabupaten','kecamatan','desa','rw','rt'].map(t=>'<option value="'+t+'"'+(t===D.konfigurasi.tingkat_analisis?' selected':'')+'>per '+t+'</option>').join('')+'</select>';
 if(el){el.parentElement.querySelector('#pilihTingkat').value=D.konfigurasi.tingkat_analisis;el.value=J;return}
 const w=document.createElement('span');w.style.cssText='display:flex;gap:6px';w.innerHTML=html;
 hd.insertBefore(w,document.getElementById('pWil'))}
async function gantiJenis(v){const k=await api('/api/konfigurasi');k.jenis_pemilihan=v;
 k.tingkat_analisis=k.aturan_pemilihan[v].tingkat||k.tingkat_analisis;
 const r=await api('/api/konfigurasi',k);if(r.ok){await muat();toast('Mode: '+k.aturan_pemilihan[v].nama)}}
async function gantiTingkat(v){const k=await api('/api/konfigurasi');k.tingkat_analisis=v;
 const r=await api('/api/konfigurasi',k);if(r.ok){await muat();toast('Tingkat analisis: '+v)}}

/* ---- SARAN MENANG ---- */
function vMenang(){const P=D.papan_daerah,J=D.jalur,S=D.strategi,A=D.aturan;
 document.getElementById('v-menang').innerHTML=
 '<div class="card klik" onclick="go(\'konfig\')" style="margin-bottom:12px"><h3>Aturan kemenangan yang dipakai</h3>'+
 '<div style="font-size:15px;font-weight:700">'+esc(A.nama)+' <span class="sub">metode '+esc(A.metode)+'</span></div>'+
 '<div class="mini">'+esc(A.catatan)+'</div>'+
 A.syarat.map(y=>'<div class="row"><span class="sub">'+esc(y.nama)+'</span><b class="'+(y.terpenuhi?'up':'dn')+'">'+esc(y.nilai)+' '+(y.terpenuhi?'✓':'✗')+'</b></div>').join('')+'</div>'+
 '<div class="grid g4">'+
 kpi('Daerah menang',n0(P.menang)+' / '+n0(P.menang+P.imbang+P.kalah),pc(P.dpt_menang/D.ringkas.dpt)+' DPT','up',"go('wilayah')")+
 kpi('Daerah imbang',n0(P.imbang),'di sinilah pemilu ditentukan',P.imbang?'wrn':'up',"go('menang')")+
 kpi('Daerah kalah',n0(P.kalah),pc(P.dpt_kalah/D.ringkas.dpt)+' DPT',P.kalah?'dn':'up',"go('menang')")+
 kpi('Rumah harus didatangi',n0(P.rumah_total),n0(P.relawan_kurang_total)+' relawan kurang · '+rp(P.biaya_total),'',"go('worker')")+
 '</div><div class="grid g3" style="margin-top:12px">'+
 J.jalur.map((j,i)=>'<div class="card"><h3>'+esc(j.nama)+'</h3><div class="sub">'+esc(j.ringkas)+'</div>'+
  '<div style="font-size:22px;font-weight:800;margin:8px 0">+'+n0(j.tambahan)+' <span class="sub" style="font-size:12px">suara</span></div>'+
  '<div class="row"><span class="sub">Biaya</span><b>'+rp(j.biaya)+'</b></div>'+
  '<div class="row"><span class="sub">Rp per suara</span><b>'+rp(j.rp_per_suara)+'</b></div>'+
  '<div class="row"><span class="sub">Cukup sendiri?</span><b class="'+(j.cukup_sendiri?'up':'dn')+'">'+(j.cukup_sendiri?'ya':'belum')+'</b></div>'+
  '<ul class="mini">'+j.langkah.map(l=>'<li>'+esc(l)+'</li>').join('')+'</ul>'+
  '<div class="mini">Kelayakan: '+esc(j.kelayakan)+'</div></div>').join('')+'</div>'+
 '<div class="card" style="margin-top:12px"><h3>Proyeksi menang/kalah per daerah — klik baris untuk cara memenangkannya</h3>'+
 '<table><thead><tr><th>Daerah</th><th>Vonis</th><th class="num">Peluang</th><th class="num">Selisih</th><th class="num">DPT</th>'+
 '<th class="num">Suara kurang</th><th class="num">Rumah</th><th class="num">Relawan −</th><th class="num">Ranting −</th><th class="num">TPS tanpa saksi</th><th>Isu utama</th></tr></thead><tbody>'+
 S.map((s,i)=>'<tr class="klik" onclick="caraMenang('+i+')"><td>'+esc(s.nama)+'</td>'+
  '<td><span class="tag '+(KAT[s.kategori]||'z3')+'">'+esc(s.kategori)+'</span></td>'+
  '<td class="num '+(s.peluang>=60?'up':s.peluang>=40?'wrn':'dn')+'">'+pp(s.peluang)+'</td>'+
  '<td class="num '+(s.margin>=0?'up':'dn')+'">'+pp(s.margin*100)+'</td><td class="num">'+n0(s.dpt)+'</td>'+
  '<td class="num">'+n0(s.suara_kurang)+'</td><td class="num">'+n0(s.rumah_target)+'</td>'+
  '<td class="num">'+n0(s.relawan_kurang)+'</td><td class="num">'+n0(s.ranting_kurang)+'</td>'+
  '<td class="num '+(s.tps_tanpa_saksi?'dn':'')+'">'+n0(s.tps_tanpa_saksi)+'</td><td class="sub">'+esc(s.isu||'—')+'</td></tr>').join('')+
 '</tbody></table><div class="mini">Peluang per daerah = sebaran normal atas selisih lokal dengan simpangan dari MoE survei wilayah itu + risiko turnout. Rumah = suara yang dibutuhkan ÷ (pemilih per KK × turnout × konversi door-to-door wilayah itu).</div></div>'}
function caraMenang(i){const s=D.strategi[i];
 modal(esc(s.nama)+' <span class="tag '+(KAT[s.kategori]||'z3')+'">'+esc(s.kategori)+'</span>',
 '<div class="grid g4">'+
 '<div class="card"><h3>Peluang</h3><div style="font-size:22px;font-weight:800">'+pp(s.peluang)+'</div><div class="sub">selisih '+pp(s.margin*100)+' poin</div></div>'+
 '<div class="card"><h3>Suara kurang</h3><div style="font-size:22px;font-weight:800">'+n0(s.suara_kurang)+'</div><div class="sub">aman: '+n0(s.suara_aman)+'</div></div>'+
 '<div class="card"><h3>Rumah didatangi</h3><div style="font-size:22px;font-weight:800">'+n0(s.rumah_target)+'</div><div class="sub">konversi '+pc(s.konversi)+'</div></div>'+
 '<div class="card"><h3>Relawan</h3><div style="font-size:22px;font-weight:800">'+n0(s.relawan_butuh)+'</div><div class="sub">kurang '+n0(s.relawan_kurang)+'</div></div></div>'+
 '<div style="margin-top:12px">'+s.langkah.map((l,i)=>'<div class="card" style="background:var(--pnl2);margin-bottom:8px">'+
  '<div style="font-weight:700">'+(i+1)+'. '+esc(l.langkah)+'</div><div class="sub" style="white-space:normal">'+esc(l.rinci)+'</div>'+
  (l.angka?'<div class="mini ac">'+esc(l.angka)+'</div>':'')+(l.biaya?'<div class="mini">Biaya: '+rp(l.biaya)+'</div>':'')+'</div>').join('')+'</div>'+
 '<div style="display:flex;gap:8px"><button class="gh" onclick="tutup();bukaWilayah(\''+s.kode+'\')">Buka data wilayah</button>'+
 '<button class="gh" onclick="tutup();go(\'worker\')">Lihat perintah worker</button></div>',900)}

/* ---- STRUKTUR & RANTING ---- */
function vStruktur(){const S=D.struktur,koal=S.filter(x=>x.koalisi);
 const totUnit=koal.reduce((a,b)=>a+b.unit,0),totTar=koal.reduce((a,b)=>a+b.target,0);
 document.getElementById('v-struktur').innerHTML='<div class="grid g4">'+
 kpi('Kelengkapan struktur koalisi',pc(totUnit/(totTar||1)),n0(totUnit)+' dari '+n0(totTar)+' unit',totUnit/totTar>=.9?'up':'wrn',"bukaTabel('struktur_partai.csv')")+
 kpi('Pengurus koalisi',n0(koal.reduce((a,b)=>a+b.pengurus,0)),'DPC + PAC + ranting + anak ranting','',"bukaTabel('struktur_partai.csv')")+
 kpi('Kader koalisi',n0(koal.reduce((a,b)=>a+b.kader,0)),n1(koal.reduce((a,b)=>a+b.kader,0)/(D.ringkas.dpt/1000))+' per 1.000 DPT','',"go('menang')")+
 kpi('Anak ranting vs TPS',n0(D.wilayah.reduce((a,w)=>a+w.struktur.anak_ada,0))+' / '+n0(D.ringkas.tps),'1 anak ranting = 1 TPS terjaga','',"go('saksi')")+
 '</div><div class="grid g2" style="margin-top:12px">'+
 S.map(p=>'<div class="card'+(p.koalisi?'':' ')+'" style="'+(p.koalisi?'border-color:#22c55e55':'')+'"><h3>'+esc(p.partai)+
  (p.koalisi?' <span class="tag z0">koalisi</span>':' <span class="tag z3">luar</span>')+'</h3>'+
  '<div class="row"><span class="sub">Kelengkapan</span><b>'+pc(p.kelengkapan)+'</b></div>'+
  '<div class="bar" style="margin-bottom:8px"><i style="width:'+Math.min(100,(p.kelengkapan||0)*100)+'%;background:'+warna(p.kelengkapan||0)+'"></i></div>'+
  '<table><thead><tr><th>Tingkat</th><th class="num">Terbentuk</th><th class="num">Target</th><th class="num">Pengurus</th><th class="num">Kader</th></tr></thead><tbody>'+
  p.tingkat.map(t=>'<tr class="klik" onclick="bukaTabel(\'struktur_partai.csv\',{partai:\''+p.partai+'\'})"><td>'+esc(t.tingkat)+'</td>'+
   '<td class="num">'+n0(t.unit)+'</td><td class="num">'+n0(t.target)+'</td><td class="num">'+n0(t.pengurus)+'</td><td class="num">'+n0(t.kader)+'</td></tr>').join('')+
  '</tbody></table></div>').join('')+'</div>'+
 '<div class="card" style="margin-top:12px"><h3>Kekurangan ranting per wilayah — klik baris</h3><table><thead><tr><th>Wilayah</th><th class="num">PAC</th>'+
 '<th class="num">Ranting ada</th><th class="num">Ranting target</th><th class="num">Kurang</th><th class="num">Anak ranting</th><th class="num">Kurang</th>'+
 '<th class="num">Pengurus</th><th class="num">Kader/1.000 DPT</th><th style="width:14%">Kelengkapan</th></tr></thead><tbody>'+
 [...D.wilayah].sort((a,b)=>(b.struktur.ranting_target-b.struktur.ranting_ada)-(a.struktur.ranting_target-a.struktur.ranting_ada))
 .map(w=>{const s=w.struktur,k=s.ranting_target?s.ranting_ada/s.ranting_target:0;
  return '<tr class="klik" onclick="bukaWilayah(\''+w.kode+'\',\'struktur_partai.csv\')"><td>'+wlink(w)+'</td>'+
  '<td class="num">'+n0(s.pac_ada)+'/'+n0(s.pac_target)+'</td><td class="num">'+n0(s.ranting_ada)+'</td><td class="num">'+n0(s.ranting_target)+'</td>'+
  '<td class="num dn">'+n0(Math.max(0,s.ranting_target-s.ranting_ada))+'</td><td class="num">'+n0(s.anak_ada)+'/'+n0(s.anak_target)+'</td>'+
  '<td class="num dn">'+n0(Math.max(0,s.anak_target-s.anak_ada))+'</td><td class="num">'+n0(s.pengurus)+'</td>'+
  '<td class="num">'+n1(s.kader_per_1000)+'</td><td><div class="bar"><i style="width:'+Math.min(100,k*100)+'%;background:'+warna(k)+'"></i></div></td></tr>'}).join('')+
 '</tbody></table><div class="mini">1 ranting per '+n0(D.konfigurasi.struktur_partai.pemilih_per_ranting)+' pemilih; anak ranting disamakan dengan jumlah TPS supaya tiap TPS punya penanggung jawab sekaligus calon saksi.</div></div>'}

/* ---- KEPUTUSAN & PEMICU ---- */
async function vKeputusan(){if(!WORKER)try{WORKER=await api('worker.json?'+Date.now())}catch(e){}
 const el=document.getElementById('v-keputusan');if(!el||!WORKER)return;
 const N=WORKER.neutron,P=WORKER.pemicu||[],KP=WORKER.keputusan||[];
 const aktif=P.filter(p=>p.kena);
 el.innerHTML='<div class="card" style="border-color:'+(N.putusan==='menang'?'var(--ok)':'var(--wr)')+'">'+
 '<h3>Otak Neutron — inti keputusan deterministik</h3>'+
 '<div style="font-size:15px;font-weight:700">'+esc(N.kalimat)+'</div>'+
 '<div class="grid g2" style="margin-top:10px"><div><table><thead><tr><th>Lensa</th><th>Suara</th><th class="num">Bobot</th><th>Alasan</th></tr></thead><tbody>'+
 N.lensa.map(l=>'<tr><td>'+esc(l.lensa)+'</td><td><span class="tag '+(l.suara==='menang'?'z0':l.suara==='rapuh'?'z1':'z3')+'">'+esc(l.suara)+'</span></td>'+
  '<td class="num">'+pc(l.bobot)+'</td><td class="sub" style="white-space:normal">'+esc(l.alasan)+'</td></tr>').join('')+'</tbody></table></div>'+
 '<div class="card" style="background:var(--pnl2)"><h3>Sebaran suara lensa</h3>'+
 Object.keys(N.sebaran).map(k=>'<div class="row"><span class="sub">'+esc(k)+'</span><b>'+pc(N.sebaran[k])+'</b></div>').join('')+
 '<div class="mini">'+esc(N.catatan)+'</div></div></div></div>'+
 '<div class="grid g4" style="margin-top:12px">'+
 kpi('Pemicu merah',n0(aktif.filter(p=>p.tingkat==='merah').length),'wajib diputuskan sekarang',aktif.filter(p=>p.tingkat==='merah').length?'dn':'up',"go('keputusan')")+
 kpi('Pemicu kuning',n0(aktif.filter(p=>p.tingkat==='kuning').length),'harus dijadwalkan','wrn',"go('keputusan')")+
 kpi('Pemicu aman',n0(P.length-aktif.length),'dari '+n0(P.length)+' pemicu dipantau','up',"go('keputusan')")+
 kpi('Keputusan menunggu',n0(KP.length),'klik untuk putuskan','',"go('keputusan')")+
 '</div><div class="card" style="margin-top:12px"><h3>Keputusan yang harus diambil — pilih, lalu tercatat di Ledger</h3>'+
 (KP.length?KP.map((k,i)=>'<div class="card" style="background:var(--pnl2);margin-bottom:10px;border-left:3px solid '+(k.tingkat==='merah'?'var(--bd)':'var(--wr)')+'">'+
  '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><b>'+esc(k.kode)+' · '+esc(k.judul)+'</b>'+
  '<span class="tag '+(k.tingkat==='merah'?'z1':'z3')+'">'+esc(k.tingkat)+'</span><span class="sub">PJ '+esc(k.pj)+' · tenggat '+esc(k.tenggat)+'</span></div>'+
  '<div class="sub">Dasar: '+esc(k.dasar)+'</div>'+
  '<div class="ac" style="margin:6px 0">Rekomendasi: '+esc(k.rekomendasi)+'</div>'+
  '<div style="display:flex;gap:6px;flex-wrap:wrap">'+k.opsi.map(o=>'<button class="gh" onclick="putuskan('+i+',\''+esc(o.pilihan).replace(/'/g,"")+'\')">'+esc(o.pilihan)+'</button>').join('')+'</div>'+
  '</div>').join(''):'<div class="sub">tidak ada keputusan tertunda</div>')+'</div>'+
 '<div class="card" style="margin-top:12px"><h3>Papan pemicu — semua ukuran yang dipantau</h3><table><thead><tr><th>Kode</th><th>Pemicu</th><th>Ukuran</th><th class="num">Nilai</th><th class="num">Ambang</th><th>Status</th><th>Aksi bila kena</th><th>PJ</th></tr></thead><tbody>'+
 P.map(p=>'<tr class="'+(p.kena?'':'')+'"><td>'+esc(p.kode)+'</td><td>'+esc(p.nama)+'</td><td class="sub">'+esc(p.ukuran)+'</td>'+
  '<td class="num">'+n1(p.nilai)+'</td><td class="num">'+esc(p.arah)+' '+n1(p.ambang)+'</td>'+
  '<td><span class="tag '+(p.kena?(p.tingkat==='merah'?'z1':'z3'):'z0')+'">'+(p.kena?'KENA':'aman')+'</span></td>'+
  '<td class="sub" style="white-space:normal;max-width:340px">'+esc(p.aksi)+'</td><td class="sub">'+esc(p.pj)+'</td></tr>').join('')+
 '</tbody></table><div class="mini">Ambang diubah di pemicu.json. Pemicu merah yang aktif otomatis dicatat di Ledger tiap worker berjalan.</div></div>'}
async function putuskan(i,pilihan){const k=WORKER.keputusan[i];
 const catatan=prompt('Catatan keputusan (opsional) untuk: '+k.judul+' → '+pilihan,'')||'';
 const r=await api('/api/keputusan',{kode:k.kode,judul:k.judul,pilihan:pilihan,catatan:catatan,tingkat:k.tingkat,pj:k.pj});
 if(r.ok){toast('Keputusan tercatat di ledger #'+r.catatan.nomor);vLedger()}else toast('Gagal',1)}

/* ---- BENCHMARK ---- */
function vBenchmark(){const B=D.benchmark;
 document.getElementById('v-benchmark').innerHTML='<div class="grid g4">'+
 kpi('Nilai kesiapan',n0(B.nilai)+' <span class="sub">/100</span>','peringkat '+B.huruf,B.nilai>=70?'up':'wrn',"go('kesimpulan')")+
 kpi('Potensi bila semua setara patokan','+'+n0(B.potensi_jika_setara)+' suara','patokan = kuartil atas wilayah sendiri','up',"go('menang')")+
 kpi('Patokan IKC',n1(B.patokan.ikc),'saksi '+pc(B.patokan.saksi)+' · struktur '+pc(B.patokan.struktur),'',"go('wilayah')")+
 kpi('Patokan biaya per suara',rp(B.patokan.biaya),'kuartil termurah — jadikan standar','',"go('anggaran')")+
 '</div><div class="card" style="margin-top:12px"><h3>Pilar kesiapan — klik untuk memperbaiki</h3><table><thead><tr><th>Pilar</th><th class="num">Nilai</th><th class="num">Target</th><th class="num">Skor</th><th class="num">Bobot</th><th>Status</th><th style="width:22%"></th><th>Perbaikan</th></tr></thead><tbody>'+
 B.pilar.map(p=>'<tr class="klik" onclick="go(\''+({'Cakupan saksi TPS':'saksi','Struktur partai sampai ranting':'struktur','Dukungan ormas':'ormas','Sentimen isu':'isu','Efisiensi anggaran':'anggaran','Pemetaan udara (drone)':'drone','Kelengkapan data':'data','Mesin darat (relawan)':'wilayah'}[p.pilar]||'wilayah')+'\')">'+
  '<td>'+esc(p.pilar)+'</td><td class="num">'+pc(p.nilai)+'</td><td class="num">'+pc(p.target)+'</td>'+
  '<td class="num">'+pc(p.skor)+'</td><td class="num">'+pc(p.bobot)+'</td>'+
  '<td><span class="tag '+(p.status==='baik'?'z0':p.status==='cukup'?'z3':'z1')+'">'+esc(p.status)+'</span></td>'+
  '<td><div class="bar"><i style="width:'+p.skor*100+'%;background:'+warna(p.skor)+'"></i></div></td>'+
  '<td class="sub" style="white-space:normal">'+esc(p.perbaikan)+'</td></tr>').join('')+
 '</tbody></table></div>'+
 '<div class="card" style="margin-top:12px"><h3>Perbandingan wilayah terhadap patokan — klik baris</h3><table><thead><tr><th>Wilayah</th><th class="num">IKC</th><th class="num">Jarak ke patokan</th><th class="num">Saksi</th><th class="num">Struktur</th><th class="num">DTD</th><th class="num">Rp/suara</th><th class="num">Potensi suara</th><th>Status</th></tr></thead><tbody>'+
 B.banding.map(b=>'<tr class="klik" onclick="bukaWilayah(\''+b.kode+'\')"><td>'+esc(b.nama)+'</td><td class="num">'+n1(b.ikc)+'</td>'+
  '<td class="num '+(b.gap_ikc>0?'dn':'up')+'">'+n1(b.gap_ikc)+'</td><td class="num">'+pc(b.saksi)+'</td>'+
  '<td class="num">'+pc(b.struktur)+'</td><td class="num">'+pc(b.dtd)+'</td><td class="num">'+rp(b.biaya)+'</td>'+
  '<td class="num up">+'+n0(b.potensi_suara)+'</td>'+
  '<td>'+(b.setara_patokan?'<span class="tag z0">setara patokan</span>':'<span class="tag z1">di bawah</span>')+'</td></tr>').join('')+
 '</tbody></table><div class="mini">'+esc(B.catatan)+'</div></div>'}

/* ---- LEDGER ---- */
async function vLedger(){const el=document.getElementById('v-ledger');if(!el)return;
 const L=await api('/api/ledger');const v=L.verifikasi;
 el.innerHTML='<div class="grid g4">'+
 kpi('Catatan ledger',n0(v.jumlah),'berantai dengan hash SHA-256','',"go('ledger')")+
 kpi('Keutuhan rantai',v.ok?'UTUH':'RUSAK',esc(v.pesan),v.ok?'up':'dn',"go('ledger')")+
 kpi('Keputusan tercatat',n0(L.catatan.filter(c=>c.jenis==='keputusan').length),'klik untuk ambil keputusan','',"go('keputusan')")+
 kpi('Pemicu tercatat',n0(L.catatan.filter(c=>c.jenis==='pemicu').length),'pemicu merah otomatis masuk ledger','wrn',"go('keputusan')")+
 '</div><div class="card" style="margin-top:12px"><h3>Buku besar — setiap hitungan, perubahan data, pemicu, dan keputusan</h3>'+
 '<div class="scroll" style="max-height:620px"><table><thead><tr><th class="num">#</th><th>Waktu</th><th>Jenis</th><th>Ringkas</th><th>Oleh</th><th>Hash</th></tr></thead><tbody>'+
 L.catatan.map(c=>'<tr class="klik" onclick="lihatCatatan('+c.nomor+')"><td class="num">'+c.nomor+'</td>'+
  '<td class="sub">'+esc(String(c.waktu).replace('T',' '))+'</td>'+
  '<td><span class="tag '+({hitung:'z2',worker:'z0',keputusan:'z0',pemicu:'z1',data:'z3',konfigurasi:'z3',neutron:'z2'}[c.jenis]||'z3')+'">'+esc(c.jenis)+'</span></td>'+
  '<td style="white-space:normal;max-width:520px">'+esc(c.ringkas)+'</td><td class="sub">'+esc(c.oleh)+'</td>'+
  '<td class="sub" style="font-family:ui-monospace,Menlo,monospace">'+esc(String(c.hash).slice(0,10))+'…</td></tr>').join('')+
 '</tbody></table></div><div class="mini">File: data/ledger.jsonl. Tiap baris menyimpan hash baris sebelumnya — mengubah satu angka lama membuat rantai putus dan langsung terlihat di kartu "Keutuhan rantai".</div></div>';
 window._ledger=L.catatan}
function lihatCatatan(n){const c=(window._ledger||[]).find(x=>x.nomor===n);if(!c)return;
 modal('Catatan ledger #'+n,'<div class="row"><span class="sub">Waktu</span><b>'+esc(String(c.waktu).replace('T',' '))+'</b></div>'+
 '<div class="row"><span class="sub">Jenis</span><b>'+esc(c.jenis)+'</b></div>'+
 '<div class="row"><span class="sub">Oleh</span><b>'+esc(c.oleh)+'</b></div>'+
 '<div class="row"><span class="sub">Ringkas</span><b style="white-space:normal;max-width:70%;text-align:right">'+esc(c.ringkas)+'</b></div>'+
 '<div class="card" style="background:var(--pnl2);margin-top:10px"><h3>Isi</h3><pre style="white-space:pre-wrap;font-size:11px">'+esc(JSON.stringify(c.data,null,1))+'</pre></div>'+
 '<div class="mini" style="font-family:ui-monospace,Menlo,monospace;word-break:break-all">hash: '+esc(c.hash)+'<br>sebelum: '+esc(c.hash_sebelum)+'</div>',820)}

/* ---- KESIMPULAN ---- */
function vKesimpulan(){const K=D.kesimpulan,menang=K.gap<=0;
 document.getElementById('v-kesimpulan').innerHTML=
 '<div class="card" style="border-color:'+(menang?'var(--ok)':'var(--bd)')+'"><h3>Kesimpulan — '+esc(D.aturan.nama)+'</h3>'+
 '<div style="font-size:20px;font-weight:800" class="'+(menang?'up':'dn')+'">'+esc(K.vonis)+'</div>'+
 '<div class="sub">Selisih '+pp(K.margin)+' poin · peluang '+(K.peluang==null?'tidak ditampilkan (data kurang)':pp(K.peluang))+
 ' · suara '+n0(K.suara_kita)+' vs target '+n0(K.target)+' · '+(K.gap>0?'kurang '+n0(K.gap):'surplus '+n0(-K.gap))+' suara</div>'+
 '<div class="mini">Nilai kesiapan '+n0(K.benchmark.nilai)+' ('+esc(K.benchmark.huruf)+'); bila semua wilayah setara patokan internal, tambahan '+n0(K.benchmark.potensi)+' suara.</div></div>'+
 '<div class="grid g2" style="margin-top:12px">'+
 '<div class="card"><h3>Syarat menang — harus semua ✓</h3>'+
 K.syarat_menang.map(s=>'<div class="row"><span style="white-space:normal;max-width:70%">'+(s.tercapai?'✓ ':'✗ ')+esc(s.syarat)+
  '<div class="sub">'+esc(s.cara)+'</div></span><b class="'+(s.tercapai?'up':'dn')+'">'+(s.tercapai?'tercapai':'belum')+'</b></div>').join('')+'</div>'+
 '<div class="card"><h3>Yang bisa membuat kalah</h3>'+
 K.sebab_kalah.map(s=>'<div class="row"><span style="white-space:normal;max-width:70%"><b>'+esc(s.sebab)+'</b><div class="sub">'+esc(s.jaga)+'</div></span><b class="dn">'+esc(s.dampak)+'</b></div>').join('')+'</div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Cara memenangkan — tiga jalur, boleh dipakai bersamaan</h3><div class="grid g3">'+
 K.cara_menang.map(j=>'<div class="card" style="background:var(--pnl2)"><h3>'+esc(j.nama)+'</h3><div style="font-size:20px;font-weight:800">+'+n0(j.tambahan)+'</div>'+
  '<div class="sub">'+esc(j.ringkas)+'</div><div class="row"><span class="sub">Biaya</span><b>'+rp(j.biaya)+'</b></div>'+
  '<div class="row"><span class="sub">Rp/suara</span><b>'+rp(j.rp_per_suara)+'</b></div>'+
  '<ul class="mini">'+j.langkah.map(l=>'<li>'+esc(l)+'</li>').join('')+'</ul></div>').join('')+'</div>'+
 '<div class="mini">Gabungan tiga jalur: '+n0(K.gabungan_jalur)+' suara.</div></div>'+
 '<div class="grid g3" style="margin-top:12px">'+
 '<div class="card"><h3>Wajib dipertahankan</h3>'+(K.wajib_dipertahankan.map(s=>'<div class="row klik" onclick="go(\'menang\')"><span>'+esc(s.nama)+'</span><b>'+pp(s.peluang)+'</b></div>').join('')||'<div class="sub">—</div>')+'</div>'+
 '<div class="card"><h3>Harus direbut</h3>'+(K.harus_direbut.map(s=>'<div class="row klik" onclick="go(\'menang\')"><span>'+esc(s.nama)+'<div class="sub">'+n0(s.suara_kurang)+' suara · '+n0(s.rumah_target)+' rumah</div></span><b class="wrn">'+pp(s.peluang)+'</b></div>').join('')||'<div class="sub">tidak ada</div>')+'</div>'+
 '<div class="card"><h3>Jangan dibakar uang</h3>'+(K.jangan_dibakar_uang.map(s=>'<div class="row"><span>'+esc(s.nama)+'</span><b class="dn">'+pp(s.peluang)+'</b></div>').join('')||'<div class="sub">tidak ada daerah yang dilepas</div>')+'</div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Kebutuhan total</h3><div class="grid g3">'+
 [['Relawan tambahan',n0(K.kebutuhan.relawan)+' orang'],['Rumah didatangi',n0(K.kebutuhan.rumah)+' KK'],
  ['Saksi kurang',n0(K.kebutuhan.saksi)+' orang'],['Ranting dibentuk',n0(K.kebutuhan.ranting)],
  ['Anak ranting dibentuk',n0(K.kebutuhan.anak_ranting)],['Biaya',rp(K.kebutuhan.biaya)]]
 .map(x=>'<div class="row"><span class="sub">'+x[0]+'</span><b>'+x[1]+'</b></div>').join('')+'</div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Jadwal kerja</h3><div class="grid g4">'+
 K.jadwal.map(j=>'<div class="card" style="background:var(--pnl2)"><h3>'+esc(j.tahap)+'</h3><div class="ac" style="font-weight:700;margin-bottom:6px">'+esc(j.fokus)+'</div>'+
  '<ul class="mini">'+j.isi.map(i=>'<li>'+esc(i)+'</li>').join('')+'</ul></div>').join('')+'</div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Indikator yang dipantau tiap minggu</h3><table><thead><tr><th>Indikator</th><th class="num">Sekarang</th><th class="num">Target</th><th>Sumber</th></tr></thead><tbody>'+
 K.pantau.map(p=>'<tr class="klik" onclick="go(\'keputusan\')"><td>'+esc(p.indikator)+'</td><td class="num">'+esc(p.sekarang)+'</td><td class="num">'+esc(p.target)+'</td><td class="sub">'+esc(p.sumber)+'</td></tr>').join('')+
 '</tbody></table></div>'+
 '<div class="warn" style="margin-top:12px"><b>Catatan kejujuran</b><ul>'+K.catatan_kejujuran.map(c=>'<li>'+esc(c)+'</li>').join('')+'</ul></div>'}
const _go2=go;go=function(k,o){_go2(k,o);if(k==='ledger')vLedger();if(k==='keputusan')vKeputusan()};
