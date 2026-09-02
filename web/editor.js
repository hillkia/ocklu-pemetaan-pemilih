/* Editor data Ocklu Pemetaan Pemilih — semua tabel bisa diklik & diubah. */
const TABEL_LABEL={'wilayah.csv':'Wilayah & DPT','hasil_lalu.csv':'Hasil pemilu lalu','survei.csv':'Survei',
 'dtd.csv':'Door-to-door','relawan.csv':'Relawan','saksi.csv':'Saksi TPS','isu.csv':'Isu lokal',
 'anggaran.csv':'Anggaran','kandidat.csv':'Calon & petahana (bio)','caleg.csv':'Caleg','drone_misi.csv':'Misi drone',
 'partai.csv':'Kekuatan partai','ormas.csv':'Kekuatan ormas','struktur_partai.csv':'Struktur partai (DPC/PAC/Ranting/RT)','riwayat_pemilihan.csv':'Riwayat pemilihan','dinasti.csv':'Kekerabatan / dinasti'};
const TERKAIT=[['survei.csv','Survei'],['dtd.csv','Door-to-door'],['saksi.csv','Saksi'],['relawan.csv','Relawan'],
 ['isu.csv','Isu'],['anggaran.csv','Anggaran'],['hasil_lalu.csv','Hasil lalu'],['partai.csv','Partai'],
 ['ormas.csv','Ormas'],['struktur_partai.csv','Struktur partai'],['drone_misi.csv','Drone']];
let TCACHE={};
async function ambilTabel(nama,segar){if(!segar&&TCACHE[nama])return TCACHE[nama];
 const t=await api('/api/tabel?nama='+encodeURIComponent(nama));if(!t.ok){toast(t.pesan||'gagal',1);return null}
 TCACHE[nama]=t;return t}
async function simpanTabel(nama){const t=TCACHE[nama];if(!t)return;
 const r=await api('/api/simpan',{nama:nama,kolom:t.kolom,baris:t.baris});
 if(r.ok){toast(TABEL_LABEL[nama]+' tersimpan ('+r.baris+' baris) & dihitung ulang');await muat()}
 else toast('Gagal simpan: '+(r.pesan||''),1)}
function setSel(nama,i,kol,v){TCACHE[nama].baris[i][kol]=v}
function hapusBaris(nama,i,ulang){TCACHE[nama].baris.splice(i,1);ulang()}
function tambahBaris(nama,awal,ulang){const t=TCACHE[nama];const b={};t.kolom.forEach(k=>b[k]='');
 Object.assign(b,awal||{});t.baris.push(b);ulang()}
function cocok(b,f){return !f||Object.keys(f).every(k=>String(b[k]||'')===String(f[k]))}
function grid(nama,f,idUlang){const t=TCACHE[nama];if(!t)return'<div class="sub">tabel kosong</div>';
 const idx=t.baris.map((b,i)=>i).filter(i=>cocok(t.baris[i],f));
 return'<div class="scroll"><table class="gridin"><thead><tr>'+t.kolom.map(k=>'<th>'+k+'</th>').join('')+'<th></th></tr></thead><tbody>'+
 idx.map(i=>'<tr>'+t.kolom.map(k=>'<td><input value="'+esc(t.baris[i][k])+'" oninput="setSel(\''+nama+'\','+i+',\''+k+'\',this.value)"></td>').join('')+
 '<td><button class="dgr" onclick="hapusBaris(\''+nama+'\','+i+','+idUlang+')">hapus</button></td></tr>').join('')+
 '</tbody></table></div>'+(idx.length?'':'<div class="sub" style="padding:8px 0">Belum ada baris untuk saringan ini — tekan "+ baris".</div>')}
async function bukaTabel(nama,f){const t=await ambilTabel(nama,true);if(!t)return;
 const awal=f||{};
 modal(TABEL_LABEL[nama]+' <span class="sub">('+nama+(f?' · saringan '+esc(JSON.stringify(f)):'')+')</span>',
  '<div id="gridBox">'+grid(nama,f,'ulangGrid')+'</div>'+
  '<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">'+
  '<button class="gh" onclick=\'tambahBaris("'+nama+'",'+JSON.stringify(awal)+',ulangGrid)\'>+ baris</button>'+
  '<button class="act" onclick="simpanTabel(\''+nama+'\').then(tutup)">Simpan & hitung ulang</button>'+
  '<button class="gh" onclick="tutup()">Batal</button>'+
  '<span style="flex:1"></span><button class="gh" onclick="imporKe(\''+nama+'\')">Impor CSV ke tabel ini</button></div>'+
  '<div class="mini">Setiap penyimpanan mencadangkan versi lama ke data/cadangan/ lalu menjalankan mesin.py.</div>');
 window.ulangGrid=()=>{document.getElementById('gridBox').innerHTML=grid(nama,f,'ulangGrid')}}

/* ---------- WILAYAH: klik nama daerah -> buka & custom ---------- */
async function bukaWilayah(kode,sub){const t=await ambilTabel('wilayah.csv',true);if(!t)return;
 let i=t.baris.findIndex(b=>b.kode===kode);
 if(kode==null){const kd='W'+String(Date.now()).slice(-7);
  t.baris.push({kode:kd,provinsi:'',kabupaten:'',kecamatan:'Wilayah baru',desa:'',dapil:'',dpt:'0',kk:'0',tps:'0',
   lat:String(D.wilayah.length?(D.wilayah.reduce((a,b)=>a+b.lat,0)/D.wilayah.length).toFixed(4):-7.8),
   lon:String(D.wilayah.length?(D.wilayah.reduce((a,b)=>a+b.lon,0)/D.wilayah.length).toFixed(4):110.4),
   luas_km2:'10',indeks_urban:'0.5'});
  i=t.baris.length-1;kode=kd}
 if(i<0)return toast('Wilayah tidak ditemukan',1);
 const w=D.wilayah.find(x=>x.kode===kode);
 const F=(k,lab,tipe)=>'<div><div class="sub">'+lab+'</div><input type="'+(tipe||'text')+'" value="'+esc(t.baris[i][k])+
  '" oninput="setSel(\'wilayah.csv\','+i+',\''+k+'\',this.value)" style="width:100%"></div>';
 modal('<span id="judulW">'+esc(t.baris[i].kecamatan||'Wilayah')+'</span> <span class="sub">'+esc(kode)+'</span>',
 '<div class="stab" id="stab">'+[['profil','Profil & ubah nama']].concat(TERKAIT.map(x=>[x[0],x[1]]))
   .map(x=>'<button data-s="'+x[0]+'" onclick="subW(\''+kode+'\',\''+x[0]+'\','+i+')">'+x[1]+'</button>').join('')+'</div>'+
 '<div id="subIsi"></div>',1000);
 subW(kode,sub||'profil',i)}
async function subW(kode,s,i){[...document.querySelectorAll('#stab button')].forEach(b=>b.classList.toggle('on',b.dataset.s===s));
 const box=document.getElementById('subIsi');const w=D.wilayah.find(x=>x.kode===kode);
 if(s==='profil'){const t=TCACHE['wilayah.csv'];
  const F=(k,lab,tipe)=>'<div><div class="sub">'+lab+'</div><input type="'+(tipe||'text')+'" value="'+esc(t.baris[i][k])+
   '" oninput="setSel(\'wilayah.csv\','+i+',\''+k+'\',this.value);if(\''+k+'\'==\'kecamatan\')document.getElementById(\'judulW\').textContent=this.value" style="width:100%"></div>';
  box.innerHTML='<div class="grid g3">'+F('kecamatan','Nama kecamatan / kapanewon')+F('desa','Desa / kelurahan (opsional)')+
   F('dapil','Dapil')+F('provinsi','Provinsi')+F('kabupaten','Kabupaten / kota')+F('kode','Kode wilayah')+
   F('dpt','DPT','number')+F('tps','Jumlah TPS','number')+F('kk','Jumlah KK','number')+
   F('lat','Lintang (lat)','number')+F('lon','Bujur (lon)','number')+F('luas_km2','Luas km²','number')+
   F('indeks_urban','Indeks urban 0–1','number')+'</div>'+
   '<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">'+
   '<button class="act" onclick="simpanTabel(\'wilayah.csv\').then(tutup)">Simpan & hitung ulang</button>'+
   '<button class="gh" onclick="hitungTPS('+i+')">Hitung TPS otomatis dari DPT</button>'+
   '<button class="gh" onclick="salinKoordinat('+i+')">Ambil koordinat dari tetangga</button>'+
   '<button class="dgr" onclick="hapusWilayah('+i+')">Hapus wilayah ini</button></div>'+
   (w?'<div class="mini">Hasil hitungan sekarang: IKC '+n1(w.ikc)+' · proyeksi '+n0(w.proyeksi[K()])+' ('+pc(w.share[K()])+') · zona '+esc(w.zona)+' · kelengkapan data '+pc(w.kelengkapan)+'</div>':'<div class="mini">Wilayah baru — simpan dulu supaya masuk hitungan.</div>')}
 else{const kolKunci=s==='wilayah.csv'?'kode':'kode_wilayah';const t=await ambilTabel(s,true);if(!t)return;
  const f={};f[kolKunci]=kode;
  box.innerHTML='<div id="gridBox">'+grid(s,f,'ulangSub')+'</div><div style="margin-top:10px;display:flex;gap:8px">'+
   '<button class="gh" onclick=\'tambahBaris("'+s+'",'+JSON.stringify(f)+',ulangSub)\'>+ baris</button>'+
   '<button class="act" onclick="simpanTabel(\''+s+'\')">Simpan & hitung ulang</button>'+
   '<button class="gh" onclick="bukaTabel(\''+s+'\')">Buka seluruh tabel</button></div>';
  window.ulangSub=()=>{document.getElementById('gridBox').innerHTML=grid(s,f,'ulangSub')}}}
function hitungTPS(i){const t=TCACHE['wilayah.csv'],dpt=+t.baris[i].dpt||0;
 t.baris[i].tps=String(Math.ceil(dpt/(D.konfigurasi.maks_pemilih_per_tps||600)));
 if(!+t.baris[i].kk)t.baris[i].kk=String(Math.round(dpt/3));subW(t.baris[i].kode,'profil',i);toast('TPS dihitung dari DPT')}
function salinKoordinat(i){const t=TCACHE['wilayah.csv'];const lain=D.wilayah[0];if(!lain)return;
 t.baris[i].lat=String(lain.lat+0.01);t.baris[i].lon=String(lain.lon+0.01);subW(t.baris[i].kode,'profil',i);
 toast('Koordinat sementara dipasang — geser ke titik sebenarnya')}
async function hapusWilayah(i){const t=TCACHE['wilayah.csv'];const kode=t.baris[i].kode;
 if(!confirm('Hapus wilayah '+t.baris[i].kecamatan+'? Baris data terkait tidak ikut terhapus.'))return;
 t.baris.splice(i,1);await simpanTabel('wilayah.csv');tutup()}

/* ---------- TAB INPUT DATA ---------- */
async function vData(){const b=await api('/api/berkas');BERKAS=b;const log=await api('/api/log');
 document.getElementById('v-data').innerHTML='<div class="grid g12">'+
 '<div class="card"><h3>Tabel data — klik untuk ubah</h3>'+
 b.tabel.map(t=>'<div class="row klik" onclick="bukaTabel(\''+t.nama+'\')"><span>'+esc(t.label)+
  '<div class="sub">'+t.nama+(t.diubah?' · '+t.diubah.replace('T',' '):' · belum ada')+'</div></span>'+
  '<b class="'+(t.baris?'':'wrn')+'">'+n0(t.baris)+' baris</b></div>').join('')+
 '<div class="mini">Tiap simpan otomatis: cadangan versi lama → tulis CSV → jalankan mesin.py → dasbor menghitung ulang.</div></div>'+
 '<div><div class="card"><h3>Input otomatis</h3>'+
 '<div class="grid g2"><div>'+
 '<div class="drop" id="drop" onclick="document.getElementById(\'berkas\').click()">Seret berkas CSV ke sini, atau klik untuk pilih berkas'+
 '<input type="file" id="berkas" accept=".csv,.txt,.tsv" multiple style="display:none" onchange="pilihBerkas(this.files)"></div>'+
 '<div class="mini">Kolom dicocokkan otomatis dengan tabel tujuan. Kalau nama kolom berbeda, pakai pemetaan di bawah.</div></div>'+
 '<div><div class="sub">Pantauan folder (jalan terus tiap 5 detik)</div>'+
 '<div style="font-family:ui-monospace,Menlo,monospace;font-size:11px;background:var(--pnl2);padding:8px;border-radius:8px;word-break:break-all">'+esc(b.folder_masuk)+'</div>'+
 '<div class="mini">Taruh CSV di folder itu — langsung diimpor, diarsipkan ke masuk/selesai/, lalu dihitung ulang tanpa menyentuh dasbor.'+
 (b.masuk.length?' <b class="wrn">Menunggu: '+b.masuk.map(esc).join(', ')+'</b>':'')+'</div>'+
 '<button class="gh" onclick="vData()" style="margin-top:8px">Segarkan</button></div></div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Input manual — tempel data</h3>'+
 '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px">'+
 '<select id="imTabel"><option value="">Tebak otomatis dari kolom</option>'+
 b.tabel.map(t=>'<option value="'+t.nama+'">'+esc(t.label)+'</option>').join('')+'</select>'+
 '<select id="imMode"><option value="tambah">Tambah / perbarui</option><option value="timpa">Timpa seluruh tabel</option></select>'+
 '<button class="act" onclick="imporTempel()">Impor</button>'+
 '<button class="gh" onclick="pratinjau()">Pratinjau & petakan kolom</button></div>'+
 '<textarea id="imTeks" rows="7" style="width:100%" placeholder="Tempel dari Excel/Google Sheets/SIREKAP (baris pertama = nama kolom). Pemisah koma, titik koma, atau tab."></textarea>'+
 '<div id="imPratinjau"></div></div>'+
 '<div class="card" style="margin-top:12px"><h3>Riwayat masuk</h3><div class="scroll" style="max-height:220px">'+
 (log.length?log.map(l=>'<div class="row"><span class="sub">'+esc(l.waktu.replace('T',' '))+' · '+esc(l.jenis)+'</span><b style="font-weight:500">'+esc(l.pesan)+'</b></div>').join(''):'<div class="sub">belum ada</div>')+
 '</div></div></div></div>';
 const d=document.getElementById('drop');
 d.ondragover=e=>{e.preventDefault();d.classList.add('hot')};d.ondragleave=()=>d.classList.remove('hot');
 d.ondrop=e=>{e.preventDefault();d.classList.remove('hot');pilihBerkas(e.dataTransfer.files)}}
function pilihBerkas(files){[...files].forEach(f=>{const r=new FileReader();
 r.onload=async()=>{const h=await api('/api/impor',{nama:document.getElementById('imTabel').value||null,
  teks:r.result,mode:document.getElementById('imMode').value});
  if(h.ok){toast(f.name+' → '+h.nama+' ('+h.masuk+' baris)');TCACHE={};await muat();vData()}else toast(h.pesan,1)};
 r.readAsText(f)})}
async function imporTempel(){const teks=document.getElementById('imTeks').value;if(!teks.trim())return toast('Kosong',1);
 const h=await api('/api/impor',{nama:document.getElementById('imTabel').value||null,teks:teks,
  mode:document.getElementById('imMode').value,peta:window._peta||null});
 if(h.ok){toast('Masuk '+h.masuk+' baris ke '+h.nama);document.getElementById('imTeks').value='';window._peta=null;
  TCACHE={};await muat();vData()}else toast(h.pesan,1)}
function pratinjau(){const teks=document.getElementById('imTeks').value.trim();if(!teks)return toast('Kosong',1);
 const dl=[',',';','\t','|'].sort((a,b)=>teks.split(b).length-teks.split(a).length)[0];
 const baris=teks.split(/\r?\n/).map(r=>r.split(dl));const kol=baris[0];
 const nama=document.getElementById('imTabel').value;
 const target=(BERKAS.tabel.find(t=>t.nama===nama)||{}).nama;
 const kolTarget=KOLOM_TABEL[nama]||[];
 document.getElementById('imPratinjau').innerHTML='<div class="mini">Pemisah terdeteksi: '+(dl==='\t'?'TAB':dl)+' · '+(baris.length-1)+' baris data</div>'+
 (kolTarget.length?'<div class="grid g3" style="margin-top:8px">'+kolTarget.map(k=>'<div><div class="sub">'+k+'</div>'+
  '<select onchange="petaKolom(\''+k+'\',this.value)"><option value="">— kosongkan —</option>'+
  kol.map((c,i)=>'<option value="'+i+'"'+(c.trim().toLowerCase()===k.toLowerCase()?' selected':'')+'>'+esc(c)+'</option>').join('')+
  '</select></div>').join('')+'</div>':'<div class="mini">Pilih tabel tujuan dulu untuk memetakan kolom.</div>')+
 '<div class="scroll" style="max-height:180px;margin-top:8px"><table><thead><tr>'+kol.map(c=>'<th>'+esc(c)+'</th>').join('')+'</tr></thead><tbody>'+
 baris.slice(1,6).map(r=>'<tr>'+r.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
 window._peta={};kolTarget.forEach(k=>{const i=kol.findIndex(c=>c.trim().toLowerCase()===k.toLowerCase());if(i>=0)window._peta[k]=i})}
function petaKolom(k,v){window._peta=window._peta||{};if(v==='')delete window._peta[k];else window._peta[k]=+v}
function imporKe(nama){go('data');setTimeout(()=>{const s=document.getElementById('imTabel');if(s)s.value=nama;tutup()},60)}
const KOLOM_TABEL={'wilayah.csv':['kode','provinsi','kabupaten','kecamatan','desa','dapil','dpt','kk','tps','lat','lon','luas_km2','indeks_urban'],
 'hasil_lalu.csv':['kode_wilayah','tahun','partai','suara'],'survei.csv':['kode_wilayah','tanggal','lembaga','n_sampel','kandidat','responden_dukung'],
 'dtd.csv':['kode_wilayah','tanggal','terdata','mendukung','ragu','menolak'],'relawan.csv':['kode_wilayah','tim','jumlah','aktif_30hari'],
 'saksi.csv':['kode_wilayah','tps_terisi_saksi','saksi_terlatih'],'isu.csv':['kode_wilayah','isu','penyebutan','sentimen_ke_kita'],
 'anggaran.csv':['kode_wilayah','pos','rencana','realisasi'],'kandidat.csv':['nomor', 'nama', 'nama_lengkap', 'gelar', 'status', 'petahana', 'partai_utama', 'koalisi', 'tempat_lahir', 'tanggal_lahir', 'usia', 'agama', 'pendidikan', 'karier', 'jabatan_sekarang', 'periode_menjabat', 'kekayaan_lhkpn', 'program_unggulan', 'isu_utama', 'kekuatan', 'kelemahan', 'basis_massa', 'ormas_pendukung', 'medsos', 'catatan'],
 'caleg.csv':['dapil','partai','nama','nomor_urut','suara_pribadi','status'],'drone_misi.csv':['kode_wilayah','tujuan','luas_target_km2','status','catatan'],
 'partai.csv':['kode_wilayah','partai','pengurus_aktif','saksi_disiapkan','mesin_skor','dukungan_ke_kita'],
 'ormas.csv':['kode_wilayah','ormas','anggota','pengurus','kedekatan','pengaruh'],'struktur_partai.csv':['partai', 'tingkat', 'kode_wilayah', 'nama_unit', 'pengurus', 'kader', 'target_unit', 'terbentuk', 'ketua', 'kontak'],'riwayat_pemilihan.csv':['tahun', 'jenis', 'wilayah', 'pemenang', 'nomor', 'partai_pengusung', 'suara', 'persen', 'turnout', 'lawan_utama', 'suara_lawan', 'selisih_persen', 'petahana_ikut', 'hasil_petahana', 'catatan'],'dinasti.csv':['nama', 'peran', 'hubungan_dengan', 'jenis_hubungan', 'jabatan', 'periode', 'partai', 'masih_menjabat', 'catatan']};

/* ---------- KONFIGURASI ---------- */
async function vKonfig(){KONF=await api('/api/konfigurasi');
 const inp=(jalur,v)=>{const id='k_'+jalur.replace(/\./g,'_');
  if(Array.isArray(v))return'<input id="'+id+'" value="'+esc(v.join(', '))+'" data-t="arr" data-j="'+jalur+'" style="width:100%">';
  if(typeof v==='number')return'<input id="'+id+'" type="number" step="any" value="'+v+'" data-t="num" data-j="'+jalur+'" style="width:100%">';
  if(typeof v==='boolean')return'<select id="'+id+'" data-t="bool" data-j="'+jalur+'"><option value="true"'+(v?' selected':'')+'>ya</option><option value="false"'+(v?'':' selected')+'>tidak</option></select>';
  return'<input id="'+id+'" value="'+esc(v)+'" data-t="str" data-j="'+jalur+'" style="width:100%">'};
 const blok=(obj,pre)=>Object.keys(obj).map(k=>{const v=obj[k],j=pre?pre+'.'+k:k;
  if(v&&typeof v==='object'&&!Array.isArray(v))return'<div class="card" style="background:var(--pnl2)"><h3>'+k.replace(/_/g,' ')+'</h3>'+
   '<div class="grid g2">'+blok(v,j)+'</div></div>';
  return'<div><div class="sub">'+k.replace(/_/g,' ')+'</div>'+inp(j,v)+'</div>'}).join('');
 document.getElementById('v-konfig').innerHTML='<div class="card"><h3>Konfigurasi — semua angka pengendali mesin</h3>'+
 '<div class="grid g3">'+blok(KONF,'')+'</div>'+
 '<div style="margin-top:12px;display:flex;gap:8px"><button class="act" onclick="simpanKonfig()">Simpan & hitung ulang</button>'+
 '<button class="gh" onclick="vKonfig()">Batalkan perubahan</button>'+
 '<button class="gh" onclick="setResmi()">Tandai data sudah RESMI</button></div>'+
 '<div class="mini">sumber_data = "contoh" membuat seluruh dasbor bertanda SIMULASI. Ubah ke "resmi" hanya setelah data/*.csv benar-benar diganti data KPU.</div></div>'}
async function simpanKonfig(){const o=JSON.parse(JSON.stringify(KONF));
 document.querySelectorAll('#v-konfig [data-j]').forEach(el=>{const j=el.dataset.j.split('.');let t=el.dataset.t,v=el.value;
  v=t==='num'?+v:t==='arr'?v.split(',').map(s=>s.trim()).filter(Boolean):t==='bool'?v==='true':v;
  let c=o;for(let i=0;i<j.length-1;i++)c=c[j[i]];c[j[j.length-1]]=v});
 const r=await api('/api/konfigurasi',o);if(r.ok){toast('Konfigurasi tersimpan & dihitung ulang');await muat();vKonfig()}else toast('Gagal',1)}
async function setResmi(){KONF.sumber_data='resmi';const r=await api('/api/konfigurasi',KONF);
 if(r.ok){toast('Ditandai RESMI');await muat();vKonfig()}}
