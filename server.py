#!/usr/bin/env python3
"""Server Ocklu Pemetaan Pemilih — sajian dasbor + API input data (manual & otomatis).
python3 server.py [port]   (bawaan 4488)

API:
  GET  /api/tabel?nama=wilayah.csv      -> {kolom, baris}
  GET  /api/berkas                      -> daftar tabel + jumlah baris + waktu ubah
  GET  /api/konfigurasi                 -> isi konfigurasi.json
  GET  /api/hitung                      -> jalankan mesin.py
  GET  /api/log                         -> log impor otomatis
  POST /api/simpan     {nama,kolom,baris}          -> tulis ulang CSV (dicadangkan dulu)
  POST /api/konfigurasi {..}                        -> tulis konfigurasi.json
  POST /api/impor      {nama,teks,mode,peta}        -> impor tempelan/berkas CSV
Pengawas otomatis: berkas CSV yang ditaruh di data/masuk/ langsung diimpor,
dan setiap perubahan data/*.csv memicu hitung ulang.
"""
import http.server, socketserver, os, subprocess, sys, json, csv, io, shutil, threading, time, datetime, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger

BASE = os.path.dirname(os.path.abspath(__file__))
WEB, DATA = os.path.join(BASE, 'web'), os.path.join(BASE, 'data')
MASUK, SELESAI, CADANGAN = os.path.join(DATA, 'masuk'), os.path.join(DATA, 'masuk', 'selesai'), os.path.join(DATA, 'cadangan')
for d in (MASUK, SELESAI, CADANGAN): os.makedirs(d, exist_ok=True)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4488
LOG = os.path.join(DATA, 'log_impor.json')
KUNCI = threading.Lock()

TABEL = {
 'wilayah.csv':    dict(label='Wilayah & DPT', kunci='kode',
   kolom=['kode','provinsi','kabupaten','kecamatan','desa','dapil','dpt','kk','tps','lat','lon','luas_km2','indeks_urban']),
 'hasil_lalu.csv': dict(label='Hasil pemilu lalu', kunci=None, kolom=['kode_wilayah','tahun','partai','suara']),
 'survei.csv':     dict(label='Survei', kunci=None, kolom=['kode_wilayah','tanggal','lembaga','n_sampel','kandidat','responden_dukung']),
 'dtd.csv':        dict(label='Door-to-door', kunci='kode_wilayah', kolom=['kode_wilayah','tanggal','terdata','mendukung','ragu','menolak']),
 'relawan.csv':    dict(label='Relawan / mesin darat', kunci=None, kolom=['kode_wilayah','tim','jumlah','aktif_30hari']),
 'saksi.csv':      dict(label='Saksi TPS', kunci='kode_wilayah', kolom=['kode_wilayah','tps_terisi_saksi','saksi_terlatih']),
 'isu.csv':        dict(label='Isu lokal', kunci=None, kolom=['kode_wilayah','isu','penyebutan','sentimen_ke_kita']),
 'anggaran.csv':   dict(label='Anggaran', kunci=None, kolom=['kode_wilayah','pos','rencana','realisasi']),
 'kandidat.csv':   dict(label='Calon & petahana (bio)', kunci='nomor', kolom=['nomor', 'nama', 'nama_lengkap', 'gelar', 'status', 'petahana', 'partai_utama', 'koalisi', 'tempat_lahir', 'tanggal_lahir', 'usia', 'agama', 'pendidikan', 'karier', 'jabatan_sekarang', 'periode_menjabat', 'kekayaan_lhkpn', 'program_unggulan', 'isu_utama', 'kekuatan', 'kelemahan', 'basis_massa', 'ormas_pendukung', 'medsos', 'catatan']),
 'caleg.csv':      dict(label='Caleg (DPR/DPRD)', kunci=None, kolom=['dapil','partai','nama','nomor_urut','suara_pribadi','status']),
 'drone_misi.csv': dict(label='Misi drone', kunci='kode_wilayah', kolom=['kode_wilayah','tujuan','luas_target_km2','status','catatan']),
 'partai.csv':     dict(label='Kekuatan partai', kunci=None, kolom=['kode_wilayah','partai','pengurus_aktif','saksi_disiapkan','mesin_skor','dukungan_ke_kita']),
 'struktur_partai.csv': dict(label='Struktur partai (DPC/PAC/Ranting/RT)', kunci=None, kolom=['partai', 'tingkat', 'kode_wilayah', 'nama_unit', 'pengurus', 'kader', 'target_unit', 'terbentuk', 'ketua', 'kontak']),
 'riwayat_pemilihan.csv': dict(label='Riwayat pemilihan sebelumnya', kunci=None, kolom=['tahun', 'jenis', 'wilayah', 'pemenang', 'nomor', 'partai_pengusung', 'suara', 'persen', 'turnout', 'lawan_utama', 'suara_lawan', 'selisih_persen', 'petahana_ikut', 'hasil_petahana', 'catatan']),
 'dinasti.csv':    dict(label='Kekerabatan / dinasti', kunci='nama', kolom=['nama', 'peran', 'hubungan_dengan', 'jenis_hubungan', 'jabatan', 'periode', 'partai', 'masih_menjabat', 'catatan']),
 'ormas.csv':      dict(label='Kekuatan ormas', kunci=None, kolom=['kode_wilayah','ormas','anggota','pengurus','kedekatan','pengaruh']),
}

def log_tulis(pesan, jenis='info', rinci=None):
    try: isi = json.load(open(LOG))
    except Exception: isi = []
    isi.insert(0, dict(waktu=datetime.datetime.now().isoformat(timespec='seconds'),
                       jenis=jenis, pesan=pesan, rinci=rinci or {}))
    json.dump(isi[:200], open(LOG, 'w'), ensure_ascii=False, indent=1)

def baca_tabel(nama):
    p = os.path.join(DATA, nama)
    if not os.path.exists(p): return TABEL.get(nama, {}).get('kolom', []), []
    with open(p, newline='') as f:
        rd = csv.DictReader(f)
        return (rd.fieldnames or []), [dict(r) for r in rd]

def tulis_tabel(nama, kolom, baris):
    p = os.path.join(DATA, nama)
    if os.path.exists(p):
        cap = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        shutil.copy2(p, os.path.join(CADANGAN, f"{nama}.{cap}.bak"))
    with open(p, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=kolom, extrasaction='ignore')
        w.writeheader()
        for b in baris: w.writerow({k: b.get(k, '') for k in kolom})
    return len(baris)

def hitung():
    with KUNCI:
        p = subprocess.run([sys.executable, os.path.join(BASE, 'mesin.py')], capture_output=True, text=True)
        w = subprocess.run([sys.executable, os.path.join(BASE, 'worker.py')], capture_output=True, text=True) \
            if p.returncode == 0 else None
    return dict(ok=p.returncode == 0, keluaran=p.stdout + (w.stdout if w else ''),
                galat=p.stderr + (w.stderr if w else ''))

def urai_csv(teks):
    teks = teks.strip('﻿').strip()
    if not teks: return [], []
    contoh = teks[:2000]
    delim = max([',', ';', '\t', '|'], key=lambda d: contoh.count(d))
    rd = list(csv.reader(io.StringIO(teks), delimiter=delim))
    if not rd: return [], []
    return rd[0], rd[1:]

def cocokkan_tabel(kolom):
    """Tebak tabel tujuan dari nama kolom (untuk impor otomatis)."""
    kk = {c.strip().lower() for c in kolom}
    skor = {n: len(kk & {c.lower() for c in t['kolom']}) / max(1, len(t['kolom'])) for n, t in TABEL.items()}
    n = max(skor, key=skor.get)
    return (n, skor[n]) if skor[n] >= 0.5 else (None, skor[n])

def impor(nama, teks, mode='tambah', peta=None):
    kol_src, baris_src = urai_csv(teks)
    if not kol_src: return dict(ok=False, pesan='Berkas kosong / tidak terbaca.')
    if not nama:
        nama, skor = cocokkan_tabel(kol_src)
        if not nama: return dict(ok=False, pesan=f'Kolom tidak cocok dengan tabel mana pun (kecocokan tertinggi {skor:.0%}). Pilih tabel tujuan secara manual.')
    target = TABEL[nama]['kolom']
    peta = peta or {}
    # pemetaan otomatis untuk kolom yang namanya sama
    for t in target:
        if t not in peta:
            for i, s in enumerate(kol_src):
                if s.strip().lower() == t.lower(): peta[t] = i; break
    baris = []
    for r in baris_src:
        if not any(str(x).strip() for x in r): continue
        baris.append({t: (r[peta[t]].strip() if t in peta and peta[t] is not None and peta[t] < len(r) else '') for t in target})
    kolom_lama, lama = baca_tabel(nama)
    kunci = TABEL[nama]['kunci']
    if mode == 'timpa':
        gabung = baris
    elif kunci:
        idx = {b[kunci]: b for b in lama}
        for b in baris: idx[b[kunci]] = b
        gabung = list(idx.values())
    else:
        gabung = lama + baris
    n = tulis_tabel(nama, target, gabung)
    log_tulis(f'Impor {len(baris)} baris ke {nama} (mode {mode}) — total {n}', 'impor',
              dict(tabel=nama, masuk=len(baris), total=n))
    return dict(ok=True, nama=nama, masuk=len(baris), total=n, hitung=hitung())

def pengawas():
    """Impor otomatis berkas di data/masuk/ + hitung ulang saat data berubah."""
    cap = {}
    while True:
        try:
            for f in sorted(os.listdir(MASUK)):
                p = os.path.join(MASUK, f)
                if not os.path.isfile(p) or not f.lower().endswith(('.csv', '.txt', '.tsv')): continue
                if time.time() - os.path.getmtime(p) < 1.5: continue  # tunggu selesai disalin
                dasar = f.lower().split('.')[0].split('-')[0].split('_')[0]
                tujuan = next((n for n in TABEL if n.startswith(dasar)), None)
                try:
                    hasil = impor(tujuan, open(p, encoding='utf-8-sig', errors='replace').read(), 'tambah')
                    shutil.move(p, os.path.join(SELESAI, datetime.datetime.now().strftime('%Y%m%d-%H%M%S-') + f))
                    log_tulis(f'Otomatis: {f} -> {hasil.get("nama")}', 'otomatis', hasil)
                except Exception as e:
                    log_tulis(f'Gagal impor otomatis {f}: {e}', 'galat')
                    shutil.move(p, os.path.join(SELESAI, 'GAGAL-' + f))
            baru = {n: os.path.getmtime(os.path.join(DATA, n)) for n in TABEL if os.path.exists(os.path.join(DATA, n))}
            if cap and baru != cap: hitung()
            cap = baru
        except Exception as e:
            log_tulis(f'Pengawas: {e}', 'galat')
        time.sleep(5)

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=WEB, **k)
    def kirim(self, obj, kode=200):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode()
        self.send_response(kode); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == '/api/tabel':
            nama = q.get('nama', [''])[0]
            if nama not in TABEL: return self.kirim(dict(ok=False, pesan='tabel tidak dikenal'), 400)
            kol, baris = baca_tabel(nama)
            return self.kirim(dict(ok=True, nama=nama, label=TABEL[nama]['label'], kunci=TABEL[nama]['kunci'],
                                   kolom=kol or TABEL[nama]['kolom'], baris=baris))
        if u.path == '/api/berkas':
            out = []
            for n, t in TABEL.items():
                p = os.path.join(DATA, n); ada = os.path.exists(p)
                kol, baris = baca_tabel(n) if ada else ([], [])
                out.append(dict(nama=n, label=t['label'], baris=len(baris), ada=ada,
                                diubah=(datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec='seconds') if ada else None)))
            return self.kirim(dict(ok=True, tabel=out, masuk=[f for f in os.listdir(MASUK) if os.path.isfile(os.path.join(MASUK, f))],
                                   folder_masuk=MASUK))
        if u.path == '/api/konfigurasi':
            return self.kirim(json.load(open(os.path.join(BASE, 'konfigurasi.json'))))
        if u.path == '/api/log':
            try: return self.kirim(json.load(open(LOG)))
            except Exception: return self.kirim([])
        if u.path == '/api/ledger':
            return self.kirim(dict(ok=True, verifikasi=ledger.verifikasi(), catatan=ledger.baca(400)))
        if u.path == '/api/hitung': return self.kirim(hitung())
        return super().do_GET()
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        try: d = json.loads(self.rfile.read(n) or b'{}')
        except Exception: return self.kirim(dict(ok=False, pesan='JSON tidak sah'), 400)
        u = urllib.parse.urlparse(self.path).path
        try:
            if u == '/api/simpan':
                nama = d['nama']
                if nama not in TABEL: return self.kirim(dict(ok=False, pesan='tabel tidak dikenal'), 400)
                kolom = d.get('kolom') or TABEL[nama]['kolom']
                jml = tulis_tabel(nama, kolom, d.get('baris', []))
                log_tulis(f'Simpan manual {nama}: {jml} baris', 'manual', dict(tabel=nama, baris=jml))
                ledger.catat('data', f'Simpan manual {nama}: {jml} baris', dict(tabel=nama, baris=jml), oleh='pemilik')
                return self.kirim(dict(ok=True, baris=jml, hitung=hitung()))
            if u == '/api/konfigurasi':
                p = os.path.join(BASE, 'konfigurasi.json')
                shutil.copy2(p, os.path.join(CADANGAN, 'konfigurasi.' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.bak'))
                json.dump(d, open(p, 'w'), ensure_ascii=False, indent=2)
                log_tulis('Konfigurasi diperbarui', 'manual')
                ledger.catat('konfigurasi', 'Konfigurasi diperbarui',
                             dict(jenis=d.get('jenis_pemilihan'), tingkat=d.get('tingkat_analisis'),
                                  sumber=d.get('sumber_data')), oleh='pemilik')
                return self.kirim(dict(ok=True, hitung=hitung()))
            if u == '/api/keputusan':
                c = ledger.catat('keputusan', f"{d.get('kode','')} {d.get('judul','')} -> {d.get('pilihan','')}",
                                 dict(kode=d.get('kode'), judul=d.get('judul'), pilihan=d.get('pilihan'),
                                      catatan=d.get('catatan', ''), tingkat=d.get('tingkat'), pj=d.get('pj')),
                                 oleh=d.get('oleh', 'pemilik'))
                return self.kirim(dict(ok=True, catatan=c, verifikasi=ledger.verifikasi()))
            if u == '/api/impor':
                return self.kirim(impor(d.get('nama') or None, d.get('teks', ''), d.get('mode', 'tambah'), d.get('peta')))
        except Exception as e:
            log_tulis(f'Galat {u}: {e}', 'galat')
            return self.kirim(dict(ok=False, pesan=str(e)), 500)
        return self.kirim(dict(ok=False, pesan='rute tidak dikenal'), 404)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(self, *a): pass

hitung()
threading.Thread(target=pengawas, daemon=True).start()
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), H) as s:
    print(f"Ocklu Pemetaan Pemilih -> http://127.0.0.1:{PORT}/   (Ctrl+C berhenti)")
    print(f"Impor otomatis: taruh CSV di {MASUK}")
    s.serve_forever()
