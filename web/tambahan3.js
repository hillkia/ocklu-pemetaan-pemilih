/* Tab Riwayat & Dinasti + panel AGI / Pemburu data / MYTHOS di tab Worker AI */
(function(){
 const i=TAB.findIndex(t=>t[0]==='data');
 TAB.splice(i<0?TAB.length:i,0,['riwayat','Riwayat & Dinasti']);
 const s=document.createElement('section');s.id='v-riwayat';s.className='hide';
 document.querySelector('main').appendChild(s);
 window.EXTRA=(window.EXTRA||[]).concat([vRiwayat]);
})();
function vRiwayat(){const R=D.riwayat,P=R.petahana,DN=R.dinasti;
 const maks=Math.max(...R.pemilu.map(p=>p.persen||0),1);
 document.getElementById('v-riwayat').innerHTML='<div class="grid g4">'+
 kpi('Petahana',esc(P.nama||'—'),esc(P.jabatan||'')+' · '+esc(P.periode_teks||''),P.boleh_maju?'wrn':'up',"bukaTabel('dinasti.csv')")+
 kpi('Periode dijalani',n0(P.periode)+(P.batas?' / '+P.batas:''),P.batas?(P.boleh_maju?'masih boleh maju sekali lagi':'TIDAK BISA MAJU LAGI — kursi kosong'):'tidak ada batas periode untuk jabatan ini',P.boleh_maju?'wrn':'up',"bukaTabel('riwayat_pemilihan.csv')")+
 kpi('Keunggulan petahana',pp(R.keunggulan_petahana)+' poin','menang '+n0(R.menang_saat_ikut)+'/'+n0(R.ikut)+' kali · tanpa petahana '+pp(R.keunggulan_tanpa_petahana)+' poin','dn',"bukaTabel('riwayat_pemilihan.csv')")+
 kpi('Jaringan keluarga',n0(DN.anggota_keluarga)+' nama',(DN.tahun_berkuasa?DN.tahun_berkuasa+' tahun berkuasa · ':'')+n0((DN.jabatan_dikuasai||[]).length)+' jabatan berjalan','dn',"bukaTabel('dinasti.csv')")+
 '</div>'+
 (R.catatan.length?'<div class="warn" style="margin-top:12px"><b>Bacaan riwayat</b><ul>'+R.catatan.map(c=>'<li onclick="go(\'menang\')">'+esc(c)+'</li>').join('')+'</ul></div>':'')+
 '<div class="grid g21" style="margin-top:12px"><div class="card"><h3>Riwayat hasil pemilihan — klik baris untuk ubah</h3>'+
 '<table><thead><tr><th class="num">Tahun</th><th>Jenis</th><th>Pemenang</th><th>Pengusung</th><th class="num">Suara</th><th class="num">%</th>'+
 '<th>Lawan utama</th><th class="num">Selisih</th><th class="num">Turnout</th><th>Petahana ikut</th><th style="width:16%"></th></tr></thead><tbody>'+
 R.pemilu.map(p=>'<tr class="klik" onclick="bukaTabel(\'riwayat_pemilihan.csv\')"><td class="num">'+p.tahun+'</td>'+
  '<td class="sub">'+esc(p.jenis)+'</td><td><b>'+esc(p.pemenang)+'</b></td><td class="sub">'+esc(p.partai)+'</td>'+
  '<td class="num">'+n0(p.suara)+'</td><td class="num">'+pp(p.persen)+'</td><td class="sub">'+esc(p.lawan)+'</td>'+
  '<td class="num">'+pp(p.selisih)+'</td><td class="num">'+pp(p.turnout)+'</td>'+
  '<td>'+(p.petahana_ikut?'<span class="tag '+((p.hasil_petahana||'').toLowerCase()==='menang'?'z1':'z0')+'">ya · '+esc(p.hasil_petahana)+'</span>':'<span class="tag z3">tidak</span>')+'</td>'+
  '<td><div class="bar"><i style="width:'+((p.persen||0)/maks*100)+'%;background:'+(p.petahana_ikut?'#ef4444':'#38bdf8')+'"></i></div></td></tr>').join('')+
 '</tbody></table><div class="mini">Selisih rata-rata saat petahana ikut '+pp(R.keunggulan_petahana)+' poin vs '+pp(R.keunggulan_tanpa_petahana)+' poin saat kursi kosong — itulah harga sebenarnya dari status petahana.</div></div>'+
 '<div class="card"><h3>Pergeseran suara: pemilu lalu → proyeksi sekarang</h3>'+
 R.pergeseran.map(g=>'<div class="row"><span>'+esc(g.nama)+'<div class="sub">'+(g.lalu==null?esc(g.catatan||'—'):(g.tahun_lalu+': '+pp(g.lalu)))+'</div></span>'+
  '<b>'+pp(g.kini)+(g.selisih==null?'':' <span class="'+(g.selisih>=0?'up':'dn')+'">'+(g.selisih>0?'+':'')+n1(g.selisih)+'</span>')+'</b></div>').join('')+
 '<h3 style="margin-top:12px">Jabatan yang dikuasai jaringan</h3>'+
 ((DN.jabatan_dikuasai||[]).map(j=>'<div class="row klik" onclick="bukaTabel(\'dinasti.csv\')"><span>'+esc(j)+'</span><b class="dn">berjalan</b></div>').join('')||'<div class="sub">—</div>')+'</div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Peta kekerabatan — klik baris untuk ubah</h3>'+
 '<table><thead><tr><th>Nama</th><th>Peran</th><th>Hubungan</th><th>Dengan</th><th>Jabatan</th><th>Periode</th><th>Partai</th><th>Status</th><th>Catatan</th></tr></thead><tbody>'+
 DN.simpul.map(x=>'<tr class="klik" onclick="bukaTabel(\'dinasti.csv\',{nama:\''+esc(x.nama)+'\'})"><td><b>'+esc(x.nama)+'</b></td>'+
  '<td><span class="tag '+((x.peran||'').includes('kita')?'z0':(x.peran||'').includes('petahana')?'z1':'z3')+'">'+esc(x.peran)+'</span></td>'+
  '<td>'+esc(x.hubungan==='-'?'—':x.hubungan)+'</td><td class="sub">'+esc(x.dengan==='-'?'—':x.dengan)+'</td>'+
  '<td>'+esc(x.jabatan)+'</td><td class="sub">'+esc(x.periode)+'</td><td class="sub">'+esc(x.partai)+'</td>'+
  '<td>'+(x.menjabat?'<span class="tag z1">menjabat</span>':'<span class="tag z3">tidak</span>')+'</td>'+
  '<td class="sub" style="white-space:normal;max-width:280px">'+esc(x.catatan)+'</td></tr>').join('')+
 '</tbody></table><div class="mini">Kekerabatan diisi dari sumber terbuka (profil resmi KPU, berita, akta) — jangan memasukkan data pribadi yang tidak dipublikasikan.</div></div>'}

/* panel tambahan di tab Worker AI */
const _vWorker=vWorker;vWorker=async function(){await _vWorker();
 const el=document.getElementById('v-worker');if(!el||!WORKER||!WORKER.agi)return;
 const A=WORKER.agi,PB=WORKER.pemburu||[],M=WORKER.mythos||{};
 el.insertAdjacentHTML('beforeend',
 '<div class="grid g21" style="margin-top:12px"><div class="card"><h3>Daur tugas mandiri (AGI) — tujuan: '+esc(A.tujuan)+'</h3>'+
 '<table><thead><tr><th class="num">Putaran</th><th>Tugas</th><th>Alat</th><th>Hasil</th></tr></thead><tbody>'+
 A.tugas.map(t=>'<tr><td class="num">'+t.putaran+'</td><td>'+esc(t.judul)+(t.dari?'<div class="sub">lahir dari: '+esc(t.dari)+'</div>':'')+'</td>'+
  '<td class="sub">'+esc(t.alat)+'</td><td style="white-space:normal">'+esc(t.hasil)+'</td></tr>').join('')+
 '</tbody></table><div class="mini">'+esc(A.catatan)+(A.sisa_antrean.length?' Sisa antrean: '+A.sisa_antrean.map(esc).join('; '):'')+'</div></div>'+
 '<div class="card"><h3>MYTHOS — bobot yang berevolusi</h3>'+
 '<div class="row"><span class="sub">Generasi</span><b>'+n0(M.generasi)+'</b></div>'+
 Object.keys(M.bobot||{}).map(k=>'<div class="row"><span class="sub">'+esc(k)+'</span><b>'+n1((M.bobot[k]||0)*100)+'</b></div>').join('')+
 (M.ubah&&M.ubah.length?'<h3 style="margin-top:10px">Perubahan terakhir</h3>'+M.ubah.map(u=>'<div class="mini">'+esc(u.kategori)+': '+esc(u.dari)+' → '+esc(u.ke)+' — '+esc(u.sebab)+'</div>').join(''):'<div class="mini">belum ada mutasi pada siklus ini</div>')+
 '<div class="mini">'+esc(M.catatan||'')+'</div></div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Pemburu data — apa yang masih harus dicari, dari mana</h3>'+
 '<table><thead><tr><th class="num">Prioritas</th><th>Berkas</th><th>Yang dicari</th><th>Yang kurang</th><th>Kalau tidak ada</th><th>Sumber resmi</th></tr></thead><tbody>'+
 PB.map(p=>'<tr class="klik" onclick="'+(p.berkas==='semua'?'go(\'konfig\')':'bukaTabel(\''+p.berkas+'\')')+'">'+
  '<td class="num"><b>'+n1(p.prioritas*100)+'</b></td><td class="sub">'+esc(p.berkas)+'</td><td>'+esc(p.apa)+'</td>'+
  '<td class="sub" style="white-space:normal;max-width:260px">'+esc(p.kurang)+'</td>'+
  '<td class="sub" style="white-space:normal;max-width:300px">'+esc(p.dampak)+'</td><td class="sub">'+esc(p.sumber)+'</td></tr>').join('')+
 '</tbody></table><div class="mini">Pemburu hanya menunjuk lubang dan sumber resminya — pengambilan datanya tetap keputusan manusia, tidak ada yang ditebak.</div></div>')};
