#!/usr/bin/env python3
"""Worker AI pemenangan — membaca hasil mesin, menyaringnya lewat DNA, lalu menerbitkan perintah.
Otak: aturan (selalu ada) + narasi dari LLM lokal Ollama bila hidup. Gagal-tertutup: kalau otak AI
mati, worker mengatakannya dan tetap bekerja dengan aturan — tidak pernah mengarang.
Jalankan: python3 worker.py  ->  web/worker.json
"""
import json, os, datetime, urllib.request, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger

BASE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(BASE, 'web', 'data.json')))
DNA = json.load(open(os.path.join(BASE, 'dna.json')))
PEMICU = json.load(open(os.path.join(BASE, 'pemicu.json')))
CFG = D['konfigurasi']; WK = CFG.get('worker', {})
KITA = CFG['kandidat_kita']
R, RG, ON, SK, AG = D['ringkas'], D['risiko'], D['ontologi'], D['saksi'], D['anggaran']
HARI = D['meta']['hari_menuju']
BIAYA_DASAR = AG['biaya_per_suara'] or 1
AMBANG_RP = BIAYA_DASAR * DNA['ambang']['rp_per_suara_maks_kali_dasar']

def tenggat(hari):
    return (datetime.date.today() + datetime.timedelta(days=hari)).isoformat()

perintah, ditolak = [], []
def P(kategori, judul, wilayah, siapa, langkah, dampak, biaya, rujukan, hari=14, dasar=''):
    perintah.append(dict(kategori=kategori, judul=judul, wilayah=wilayah, siapa=siapa, langkah=langkah,
                         dampak_suara=round(dampak), biaya=round(biaya), tenggat=tenggat(hari),
                         rp_per_suara=(biaya / dampak if dampak else None), rujukan=rujukan, dasar=dasar))

# ---------- 1. jaga suara yang sudah ada: saksi ----------
for w in sorted(D['wilayah'], key=lambda x: -(x['tps_tanpa_saksi'] * (x['share'][KITA] or 0))):
    if w['saksi_cakupan'] >= 0.9 or w['tps_tanpa_saksi'] <= 0: continue
    risiko = w['tps_tanpa_saksi'] * CFG['maks_pemilih_per_tps'] * CFG['turnout_proyeksi'] * (w['share'][KITA] or 0) * CFG['risiko_selisih_tanpa_saksi']
    biaya = w['tps_tanpa_saksi'] * CFG['saksi_per_tps'] * CFG['honor_saksi']
    P('saksi', f"Isi {w['tps_tanpa_saksi']:.0f} TPS tanpa saksi di {w['nama']}", w['nama'], 'Koordinator saksi',
      f"Rekrut & latih {w['tps_tanpa_saksi']*CFG['saksi_per_tps']:.0f} saksi, siapkan formulir C-Hasil, uji simulasi penghitungan.",
      risiko, biaya, f"wilayah[{w['kode']}].tps_tanpa_saksi={w['tps_tanpa_saksi']:.0f}; saksi_cakupan={w['saksi_cakupan']:.0%}",
      max(7, min(30, HARI - 7)), 'D6 jaga dulu baru rebut')

# ---------- 2. lindung nilai wilayah penyumbang risiko terbesar ----------
for k in RG['kontribusi'][:3]:
    w = next(x for x in D['wilayah'] if x['kode'] == k['kode'])
    dampak = w['proyeksi'][KITA] * RG['sigma'] * 0.5
    P('risiko', f"Lindungi {w['nama']} — penyumbang risiko terbesar ({k['kontribusi_persen']:.0f}%)", w['nama'],
      'Manajer kampanye',
      "Kunci tiga hal sekaligus: struktur partai koalisi, pengurus ormas dominan, dan saksi. Jadwalkan kunjungan kandidat.",
      dampak, w['anggaran_rencana'] * 0.15,
      f"risiko.kontribusi[{w['kode']}]={k['kontribusi_persen']:.1f}%; paparan turnout={k['paparan']['ketergantungan_turnout']:.2f}",
      21, 'D9 ikuti risiko')

# ---------- 3. konsolidasi mesin partai koalisi yang lemah ----------
for w in D['wilayah']:
    lemah = [p for p in w['partai_rinci'] if p['koalisi'] and (p['mesin'] < 0.45 or p['dukungan'] < 0.45)]
    if not lemah: continue
    dampak = w['suara_sah_proyeksi'] * 0.02 * len(lemah)
    P('partai', f"Konsolidasi struktur {', '.join(p['partai'] for p in lemah)} di {w['nama']}", w['nama'],
      'Sekretariat koalisi',
      "Rapat struktur tingkat kecamatan, verifikasi pengurus aktif, tetapkan target suara per ranting, tandatangani lembar komitmen.",
      dampak, 8_000_000,
      '; '.join(f"partai[{p['partai']}].mesin={p['mesin']:.2f},dukungan={p['dukungan']:.2f}" for p in lemah),
      21, 'D4 bisa dieksekusi')

# ---------- 4. ormas: silaturahmi, bukan manipulasi ----------
for w in D['wilayah']:
    if w['ormas_lawan'] <= w['ormas_jangkauan']: continue
    besar = sorted(w['ormas_rinci'], key=lambda x: x['jangkauan'])[:2]
    dampak = (w['ormas_lawan'] - w['ormas_jangkauan']) * 0.15
    P('ormas', f"Silaturahmi pengurus {', '.join(o['ormas'] for o in besar)} di {w['nama']}", w['nama'],
      'Tim tokoh & keagamaan',
      "Audiensi resmi ke pengurus, bawa program yang mereka minta (bukan uang), catat komitmen, jadwalkan kunjungan lanjutan.",
      dampak, 5_000_000,
      f"wilayah[{w['kode']}].ormas_lawan={w['ormas_lawan']:.0f} > pro-kita {w['ormas_jangkauan']:.0f}",
      28, 'D11 hormati ormas & keyakinan')

# ---------- 5. tutup gap suara dari rencana alokasi mesin ----------
for a in AG['rencana_alokasi'][:6]:
    P('kampanye', f"Program penambah suara di {a['nama']}", a['nama'], 'Koordinator wilayah',
      "Jalankan program sesuai isu teratas wilayah: door-to-door terjadwal, temu warga, dan penempatan APK di titik ramai hasil pemetaan drone.",
      a['dipakai_suara'], a['dipakai_biaya'],
      f"anggaran.rencana_alokasi[{a['kode']}].tambahan={a['dipakai_suara']:.0f} suara @ Rp {a['biaya_per_suara']:,.0f}",
      30, 'D5 uang dibandingkan')

# ---------- 6. anomali dari ontologi -> perintah verifikasi ----------
for an in ON['anomali'][:8]:
    P('verifikasi', f"{an['jenis']} — {an['wilayah']}", an['wilayah'], 'Tim data',
      an['tindakan'], 0, 0, f"ontologi.anomali: {an['bukti']}", 7, 'D1 nol karangan')

# ---------- 7. drone untuk wilayah GARAP yang belum dipetakan ----------
for m in D['drone']['misi']:
    w = next((x for x in D['wilayah'] if x['kode'] == m['kode']), None)
    if not w or m['status'] == 'selesai' or not w['zona'].startswith('GARAP'): continue
    P('drone', f"Terbangkan {m['sortie']} sortie di {w['nama']}", w['nama'], 'Tim udara',
      f"{m['tujuan']}. Hasil ortofoto dipakai mencocokkan rumah/KK dengan DPT dan menentukan titik APK.",
      w['suara_sah_proyeksi'] * 0.005, m['biaya'],
      f"drone.misi[{m['kode']}].sortie={m['sortie']}, status={m['status']}", 21, 'D4 bisa dieksekusi')

# ---------- 8. caleg (mode DPR/DPRD) ----------
for dp in D['kursi']:
    for p in dp['partai']:
        if p.get('kita_nama') and p.get('kita_lolos') is False and p['ambang_internal']:
            kurang = p['ambang_internal'] - (p['kita_suara'] or 0)
            P('caleg', f"Kejar {kurang:,.0f} suara pribadi di {dp['dapil']} ({p['partai']})", dp['dapil'], 'Tim caleg',
              "Fokus ke basis pribadi: kelompok pengajian/arisan, alumni, dan relawan inti. Kursi partai jatuh ke suara pribadi terbanyak.",
              kurang, kurang * BIAYA_DASAR,
              f"kursi[{dp['dapil']}].{p['partai']}: kita {p['kita_suara']:,.0f} vs ambang {p['ambang_internal']:,.0f}",
              30, 'D4 bisa dieksekusi')


# ================= OTAK NEUTRON: inti keputusan deterministik (selalu hidup) =================
def otak_neutron():
    """Tujuh lensa memeriksa pertanyaan yang sama — 'apakah kita menang dan lewat jalur apa' —
    lalu suaranya ditimbang. Tidak memakai model bahasa, jadi tidak bisa mengarang."""
    KS, BM = D['kesimpulan'], D['benchmark']
    lensa = []
    def V(nama, suara, keyakinan, alasan, rujukan, bobot):
        lensa.append(dict(lensa=nama, suara=suara, keyakinan=keyakinan, alasan=alasan, rujukan=rujukan, bobot=bobot))
    V('Proyeksi suara', 'menang' if R['gap'] <= 0 else 'kalah', min(1, abs(R['margin_share']) / 10),
      f"selisih {R['margin_share']:+.1f} poin terhadap {R['lawan_terkuat']}", 'ringkas.margin_share', .22)
    tahan = RG['var95'] < abs(R['gap'])
    V('Ketahanan risiko', 'menang' if tahan else 'rapuh', min(1, RG['var95'] / max(1, abs(R['gap']) or 1)),
      f"VaR 95% {RG['var95']:,.0f} suara vs selisih {abs(R['gap']):,.0f}", 'risiko.var95', .18)
    imbang = len([s for s in D['strategi'] if s['kategori'] in ('IMBANG', 'KALAH TIPIS')])
    V('Sebaran daerah', 'menang' if imbang <= 3 else 'rapuh', min(1, imbang / 8),
      f"{imbang} daerah imbang/tipis dari {len(D['strategi'])}", 'strategi', .15)
    V('Pengamanan suara', 'menang' if SK['cakupan'] >= .9 else 'rapuh', 1 - SK['cakupan'],
      f"cakupan saksi {SK['cakupan']:.0%}, {SK['tps_rawan_tanpa_saksi']:,.0f} TPS rawan kosong", 'saksi.cakupan', .17)
    st_ada = sum(x['struktur']['ranting_ada'] for x in D['wilayah'])
    st_tar = sum(x['struktur']['ranting_target'] for x in D['wilayah']) or 1
    V('Struktur partai', 'menang' if st_ada / st_tar >= .85 else 'rapuh', 1 - st_ada / st_tar,
      f"ranting {st_ada:.0f}/{st_tar:.0f} terbentuk", 'struktur_partai.csv', .12)
    V('Mutu data', 'menang' if D['meta']['kelengkapan_data'] >= .7 and len(ON['anomali']) <= 5 else 'ragu',
      1 - D['meta']['kelengkapan_data'], f"kelengkapan {D['meta']['kelengkapan_data']:.0%}, {len(ON['anomali'])} anomali",
      'meta.kelengkapan_data', .10)
    V('Kesiapan (benchmark)', 'menang' if BM['nilai'] >= 70 else 'rapuh', abs(70 - BM['nilai']) / 70,
      f"nilai {BM['nilai']:.0f} ({BM['huruf']}), potensi {BM['potensi_jika_setara']:,.0f} suara bila semua setara patokan",
      'benchmark.nilai', .06)
    skor = {}
    for l in lensa: skor[l['suara']] = skor.get(l['suara'], 0) + l['bobot']
    putusan = max(skor, key=skor.get)
    dukungan = skor[putusan]
    beda = [l for l in lensa if l['suara'] != putusan]
    jalur = sorted(D['jalur']['jalur'], key=lambda j: (j['rp_per_suara'] or 9e9))
    return dict(
        putusan=putusan, keyakinan=dukungan, sebaran=skor, lensa=lensa, dissent=beda,
        jalur_disarankan=[j['nama'] for j in jalur],
        kalimat=(f"Neutron: {putusan.upper()} dengan dukungan {dukungan:.0%} dari tujuh lensa"
                 + (f"; {len(beda)} lensa membantah ({', '.join(l['lensa'] for l in beda)})" if beda else " tanpa bantahan")
                 + f". Jalur termurah: {jalur[0]['nama']} ({jalur[0]['tambahan']:,.0f} suara, "
                 + (f"Rp {jalur[0]['rp_per_suara']:,.0f}/suara)." if jalur[0]['rp_per_suara'] else "biaya belum terhitung).")),
        catatan='Deterministik: hasil sama untuk data yang sama, tidak memakai model bahasa.')

# ================= PEMICU KEPUTUSAN =================
def ukuran_sekarang():
    st_ada = sum(x['struktur']['ranting_ada'] for x in D['wilayah'])
    st_tar = sum(x['struktur']['ranting_target'] for x in D['wilayah']) or 1
    ormas_pro = sum(x['ormas_jangkauan'] for x in D['wilayah'])
    ormas_kon = sum(x['ormas_lawan'] for x in D['wilayah'])
    return dict(
        saksi_cakupan=SK['cakupan'], margin_poin=R['margin_share'],
        peluang=(R['peluang_menang'] if R['peluang_menang'] is not None else 0),
        kelengkapan=D['meta']['kelengkapan_data'], ranting_kelengkapan=st_ada / st_tar,
        anomali=len(ON['anomali']), wilayah_efektif=RG['wilayah_efektif'],
        var_lebih_besar_dari_margin=(1 if RG['var95'] > abs(R['gap'] or 0) else 0),
        ormas_rasio=(ormas_pro / (ormas_pro + ormas_kon) if (ormas_pro + ormas_kon) else 0),
        biaya_rasio=(AG['biaya_per_suara'] / max(1, D['benchmark']['patokan']['biaya'])),
        hari_menuju=D['meta']['hari_menuju'], benchmark=D['benchmark']['nilai'],
        daerah_imbang=len([s for s in D['strategi'] if s['kategori'] in ('IMBANG', 'KALAH TIPIS')]),
        data_contoh=(1 if D['meta']['sumber_data'] == 'contoh' else 0))

def cek_pemicu():
    U = ukuran_sekarang(); aktif = []
    for t in PEMICU['pemicu']:
        v = U.get(t['ukuran'])
        if v is None: continue
        kena = (v < t['ambang']) if t['arah'] == '<' else (v > t['ambang'])
        aktif.append(dict(t, nilai=v, kena=kena,
                          tenggat=tenggat(t['tenggat_hari']),
                          selisih=(t['ambang'] - v if t['arah'] == '<' else v - t['ambang'])))
    return aktif

def keputusan_dari(pemicu_aktif, neutron):
    """Setiap pemicu merah/kuning yang kena berubah jadi keputusan dengan pilihan dan rekomendasi."""
    kep = []
    for t in [x for x in pemicu_aktif if x['kena']]:
        opsi = [dict(pilihan='Jalankan aksi pemicu', biaya='sesuai rencana', hasil=t['aksi']),
                dict(pilihan='Tunda 1 siklus (7 hari)', biaya='risiko naik',
                     hasil=f"ukuran {t['ukuran']} sekarang {t['nilai']:.2f} vs ambang {t['ambang']}"),
                dict(pilihan='Abaikan', biaya='harus tertulis alasannya', hasil='dicatat di ledger sebagai keputusan sadar')]
        kep.append(dict(kode=t['kode'], judul=t['nama'], tingkat=t['tingkat'], pj=t['pj'], tenggat=t['tenggat'],
                        dasar=f"{t['ukuran']} = {t['nilai']:.3f} (ambang {t['arah']} {t['ambang']})",
                        rekomendasi=t['aksi'], opsi=opsi, status='menunggu'))
    kep.sort(key=lambda k: (0 if k['tingkat'] == 'merah' else 1, k['tenggat']))
    if neutron['putusan'] != 'menang':
        kep.insert(0, dict(kode='N00', judul='Putusan inti Neutron: posisi belum aman', tingkat='merah',
                           pj='Ketua tim', tenggat=tenggat(3), dasar=neutron['kalimat'],
                           rekomendasi='Jalankan jalur termurah lebih dulu: ' + neutron['jalur_disarankan'][0],
                           opsi=[dict(pilihan=j, biaya='lihat tab Saran Menang', hasil='menutup sebagian gap')
                                 for j in neutron['jalur_disarankan']], status='menunggu'))
    return kep


# ================= PEMBURU DATA (mencari apa yang belum ada) =================
SUMBER = {
 'wilayah.csv': 'DPT resmi KPU (Sidalih) + peta wilayah BIG/BPS',
 'hasil_lalu.csv': 'Rekapitulasi KPU / Sirekap pemilu sebelumnya',
 'survei.csv': 'Lembaga survei terdaftar KPU / survei internal',
 'dtd.csv': 'Pendataan door-to-door tim sendiri',
 'relawan.csv': 'Basis data relawan internal',
 'saksi.csv': 'Koordinator saksi + kartu tugas',
 'isu.csv': 'FGD, monitoring media lokal, laporan korwil',
 'anggaran.csv': 'Bendahara tim + LPPDK',
 'kandidat.csv': 'Profil resmi KPU, LHKPN KPK, rekam jejak media',
 'caleg.csv': 'DCT KPU',
 'partai.csv': 'Sekretariat partai koalisi',
 'ormas.csv': 'Pengurus ormas, Kesbangpol',
 'struktur_partai.csv': 'SK kepengurusan DPC/PAC/ranting',
 'riwayat_pemilihan.csv': 'Arsip hasil KPU tahun-tahun sebelumnya',
 'dinasti.csv': 'Akta/berita resmi, profil KPU, penelusuran media',
 'drone_misi.csv': 'Rencana operasi tim udara',
 'tokoh.csv': 'Pemetaan tokoh (belum ada berkasnya)',
}
def pemburu_data():
    W = D['wilayah']; n = len(W)
    lubang = []
    def L(berkas, apa, kurang, dampak, prioritas):
        lubang.append(dict(berkas=berkas, apa=apa, kurang=kurang, dampak=dampak,
                           sumber=SUMBER.get(berkas, '—'), prioritas=round(prioritas, 3)))
    tanpa_survei = [w['nama'] for w in W if w['survei'] is None]
    if tanpa_survei:
        L('survei.csv', 'Sampel survei per wilayah', f"{len(tanpa_survei)} wilayah: {', '.join(tanpa_survei[:6])}",
          'Proyeksinya masih pakai basis partai terkalibrasi — simpangan lebih besar.', .95)
    kurang_dtd = [w['nama'] for w in W if (w['dtd_cakupan'] or 0) < .2]
    if kurang_dtd:
        L('dtd.csv', 'Door-to-door minimal 20% DPT', f"{len(kurang_dtd)} wilayah di bawah 20%",
          'Konversi door-to-door dipakai menghitung berapa rumah harus didatangi.', .85)
    if not any(w.get('tokoh') for w in W):
        L('tokoh.csv', 'Peta tokoh & endorser lokal', 'berkas belum ada sama sekali',
          f"Bobot {D['konfigurasi']['bobot_ikc'].get('tokoh',0):.0%} di IKC sekarang dinormalkan ke komponen lain.", .8)
    kos_lhkpn = [k['nama'] for k in D['kandidat'] if not (k.get('kekayaan_lhkpn') or '').strip()]
    if kos_lhkpn:
        L('kandidat.csv', 'LHKPN & rekam jejak lawan', ', '.join(kos_lhkpn),
          'Bahan pembanding kampanye dan penilaian risiko hukum.', .6)
    if D['meta']['sumber_data'] == 'contoh':
        L('semua', 'Ganti seluruh data contoh dengan data resmi', 'sumber_data masih "contoh"',
          'Selama ini semua angka hanya latihan.', 1.0)
    rw = D.get('riwayat', {}).get('pemilu', [])
    if len(rw) < 3:
        L('riwayat_pemilihan.csv', 'Riwayat pemilu minimal 3 periode', f"baru {len(rw)} baris",
          'Keunggulan petahana & tren margin tidak bisa diukur dari data tipis.', .7)
    if len(D.get('riwayat', {}).get('dinasti', {}).get('simpul', [])) < 3:
        L('dinasti.csv', 'Peta kekerabatan lawan', 'belum lengkap',
          'Jaringan keluarga menentukan siapa lawan sesungguhnya.', .65)
    kurang_isu = [w['nama'] for w in W if len(w['isu']) < 3]
    if kurang_isu:
        L('isu.csv', 'Minimal 3 isu per wilayah', f"{len(kurang_isu)} wilayah",
          'Materi kampanye per wilayah jadi menebak.', .5)
    lubang.sort(key=lambda x: -x['prioritas'])
    return lubang

# ================= AGI: daur tugas mandiri (gaya BabyAGI, eksekutor lokal) =================
def agi(tujuan, putaran=4):
    riwayat_tugas, antrean = [], []
    W, KS = D['wilayah'], D['kesimpulan']
    def tambah(judul, alat, muatan=None, dari=None):
        antrean.append(dict(judul=judul, alat=alat, muatan=muatan or {}, dari=dari))
    tambah('Periksa apakah proyeksi cukup untuk menang', 'cek_gap')
    tambah('Cari lubang data yang paling merusak keputusan', 'cek_data')
    tambah('Cari daerah penentu', 'cek_daerah')
    ALAT = {}
    def alat(nama):
        def bungkus(f): ALAT[nama] = f; return f
        return bungkus
    @alat('cek_gap')
    def _(m):
        g = R['gap']
        hasil = (f"Gap {g:,.0f} suara" if g > 0 else f"Surplus {abs(g):,.0f} suara")
        lanjut = [('Uji ketahanan surplus terhadap guncangan', 'cek_risiko')] if g <= 0 else \
                 [('Susun jalur termurah menutup gap', 'cek_jalur')]
        return hasil, lanjut
    @alat('cek_risiko')
    def _(m):
        u = min(RG['uji_tekanan'], key=lambda x: x['selisih_suara'])
        aman = abs(R['gap']) > RG['var95']
        hasil = (f"VaR95 {RG['var95']:,.0f} vs selisih {abs(R['gap']):,.0f} — "
                 + ('tahan' if aman else 'BELUM tahan') + f"; skenario terburuk {u['nama']} {u['selisih_suara']:,.0f} suara")
        return hasil, ([] if aman else [('Cari cara menaikkan bantalan suara', 'cek_jalur')])
    @alat('cek_jalur')
    def _(m):
        j = sorted(D['jalur']['jalur'], key=lambda x: (x['rp_per_suara'] or 9e9))[0]
        return (f"Jalur termurah: {j['nama']} +{j['tambahan']:,.0f} suara @ Rp {(j['rp_per_suara'] or 0):,.0f}/suara",
                [('Periksa kesiapan struktur untuk jalur itu', 'cek_struktur')])
    @alat('cek_data')
    def _(m):
        p = pemburu_data()
        atas = p[0] if p else None
        return ((f"{len(p)} lubang data; paling menentukan: {atas['apa']} ({atas['kurang']}) — sumber: {atas['sumber']}"
                 if atas else 'data lengkap'),
                [('Periksa anomali silang silo', 'cek_anomali')])
    @alat('cek_anomali')
    def _(m):
        a = ON['anomali'][:3]
        return (f"{len(ON['anomali'])} anomali; teratas: " + '; '.join(x['jenis'] + ' @ ' + x['wilayah'] for x in a),
                [('Periksa riwayat & dinasti lawan', 'cek_dinasti')])
    @alat('cek_daerah')
    def _(m):
        rebut = [s for s in D['strategi'] if s['kategori'] in ('IMBANG', 'KALAH TIPIS')]
        if not rebut:
            return 'Tidak ada daerah imbang — fokus mempertahankan', [('Periksa kesiapan struktur', 'cek_struktur')]
        r = max(rebut, key=lambda x: x['dpt'])
        return (f"{len(rebut)} daerah imbang; terbesar {r['nama']} ({r['dpt']:,.0f} DPT, kurang {r['suara_kurang']:,.0f} suara, "
                f"{r['rumah_target']:,.0f} rumah)", [('Hitung kebutuhan relawan daerah itu', 'cek_relawan')])
    @alat('cek_relawan')
    def _(m):
        kurang = sum(s['relawan_kurang'] for s in D['strategi'])
        return (f"Relawan kurang {kurang:,.0f} orang di seluruh wilayah" if kurang else 'Relawan sudah memenuhi target 1 per 100 pemilih',
                [('Periksa kesiapan struktur', 'cek_struktur')])
    @alat('cek_struktur')
    def _(m):
        ada = sum(w['struktur']['ranting_ada'] for w in W); tar = sum(w['struktur']['ranting_target'] for w in W) or 1
        anak = sum(w['struktur']['anak_ada'] for w in W); anak_t = sum(w['struktur']['anak_target'] for w in W) or 1
        return (f"Ranting {ada:.0f}/{tar:.0f} ({ada/tar:.0%}), anak ranting {anak:.0f}/{anak_t:.0f} ({anak/anak_t:.0%})",
                [] if ada / tar >= .95 else [('Cari lubang data yang menghambat', 'cek_data')])
    @alat('cek_dinasti')
    def _(m):
        rw = D.get('riwayat', {})
        p = rw.get('petahana', {})
        d = rw.get('dinasti', {})
        sisa = ('tidak bisa maju lagi' if p.get('batas') and not p.get('boleh_maju') else 'masih boleh maju')
        return (f"Petahana {p.get('nama')} {p.get('periode')} periode ({sisa}); jaringan keluarga {d.get('anggota_keluarga')} nama, "
                f"{len(d.get('jabatan_dikuasai') or [])} jabatan berjalan, sekitar {d.get('tahun_berkuasa')} tahun berkuasa", [])
    lihat = set()
    for putar in range(putaran):
        if not antrean: break
        gelombang, antrean = antrean, []
        for t in gelombang:
            if t['alat'] in lihat: continue
            lihat.add(t['alat'])
            f = ALAT.get(t['alat'])
            if not f:
                riwayat_tugas.append(dict(t, putaran=putar + 1, hasil='alat tidak ada', status='gagal')); continue
            hasil, lanjut = f(t['muatan'])
            riwayat_tugas.append(dict(judul=t['judul'], alat=t['alat'], putaran=putar + 1, hasil=hasil,
                                      status='selesai', dari=t.get('dari')))
            for j, a in lanjut: tambah(j, a, dari=t['judul'])
    return dict(tujuan=tujuan, putaran=putaran, tugas=riwayat_tugas,
                sisa_antrean=[t['judul'] for t in antrean],
                catatan='Setiap tugas dikerjakan alat lokal yang membaca hasil mesin — tidak ada langkah yang mengarang angka.')

# ================= MYTHOS: worker menyetel bobotnya sendiri (berpagar) =================
def mythos(prio_awal):
    berkas = os.path.join(BASE, 'mythos.json')
    try: st = json.load(open(berkas))
    except Exception: st = dict(bobot=dict(prio_awal), generasi=0, riwayat=[])
    bobot = dict(st.get('bobot') or prio_awal)
    kunci_ledger = [c for c in ledger.baca(400) if c['jenis'] == 'keputusan']
    dipakai = {}
    for c in kunci_ledger:
        k = (c.get('data') or {}).get('kode', '')
        dipakai[k] = dipakai.get(k, 0) + 1
    PETA = {'T01': 'saksi', 'T05': 'partai', 'T06': 'verifikasi', 'T08': 'risiko', 'T09': 'ormas',
            'T10': 'kampanye', 'T13': 'kampanye', 'T14': 'verifikasi', 'N00': 'risiko'}
    ubah = []
    for kode, n in dipakai.items():
        kat = PETA.get(kode)
        if not kat or kat not in bobot: continue
        lama = bobot[kat]
        baru = min(1.0, round(lama + min(.1, .02 * n), 3))
        if baru != lama:
            bobot[kat] = baru; ubah.append(dict(kategori=kat, dari=lama, ke=baru, sebab=f'{n} keputusan {kode} diambil'))
    # pagar: kategori penjaga suara tidak boleh turun di bawah 0,9
    for wajib in ('saksi', 'verifikasi'):
        if bobot.get(wajib, 1) < .9:
            ubah.append(dict(kategori=wajib, dari=bobot[wajib], ke=.9, sebab='pagar MYTHOS: penjaga suara tidak boleh turun'))
            bobot[wajib] = .9
    # pagar: mutasi dibatalkan kalau benchmark turun dibanding catatan terakhir
    hit = [c for c in ledger.baca(400) if c['jenis'] == 'hitung' and (c.get('data') or {}).get('benchmark')]
    turun = False
    if len(hit) >= 2 and hit[0]['data']['benchmark'] < hit[1]['data']['benchmark'] - 2:
        bobot = dict(st.get('bobot') or prio_awal); turun = True
        ubah = [dict(kategori='-', dari='-', ke='-', sebab='benchmark turun >2 poin — mutasi dibatalkan, kembali ke generasi sebelumnya')]
    if ubah and not turun:
        st['generasi'] = st.get('generasi', 0) + 1
    st['bobot'] = bobot
    st['riwayat'] = ([dict(generasi=st.get('generasi', 0), ubah=ubah)] + (st.get('riwayat') or []))[:20]
    json.dump(st, open(berkas, 'w'), ensure_ascii=False, indent=1)
    return dict(generasi=st.get('generasi', 0), bobot=bobot, ubah=ubah, dibatalkan=turun,
                catatan='Bobot prioritas worker berevolusi dari keputusan yang benar-benar diambil di ledger, dengan pagar: penjaga suara tidak boleh turun dan mutasi dibatalkan bila benchmark merosot.')

# ================= GERBANG DNA =================
def langgar_kata(t):
    t = t.lower()
    return [k for k in DNA['kata_terlarang'] if k in t]

lolos, terlihat = [], set()
for p in perintah:
    teks = ' '.join(str(p.get(x, '')) for x in ('judul', 'langkah', 'dasar'))
    kena = langgar_kata(teks)
    if kena:
        ditolak.append(dict(perintah=p['judul'], aturan='D3', alasan='mengandung: ' + ', '.join(kena))); continue
    if not p['rujukan']:
        ditolak.append(dict(perintah=p['judul'], aturan='D1', alasan='tidak menunjuk angka rujukan')); continue
    if not (p['siapa'] and p['langkah'] and p['tenggat']):
        ditolak.append(dict(perintah=p['judul'], aturan='D4', alasan='tidak lengkap siapa/langkah/tenggat')); continue
    if p['rp_per_suara'] and p['rp_per_suara'] > AMBANG_RP:
        ditolak.append(dict(perintah=p['judul'], aturan='D5',
                            alasan=f"Rp {p['rp_per_suara']:,.0f}/suara > ambang Rp {AMBANG_RP:,.0f}")); continue
    kunci = (p['kategori'], p['wilayah'])
    if kunci in terlihat:
        ditolak.append(dict(perintah=p['judul'], aturan='D7', alasan='sudah ada perintah sejenis di wilayah ini')); continue
    terlihat.add(kunci); lolos.append(p)

MY = mythos({'saksi': 1.0, 'verifikasi': .95, 'risiko': .9, 'partai': .8, 'ormas': .75, 'caleg': .7, 'kampanye': .65, 'drone': .5})
PRIO_DASAR = {'saksi': 1.0, 'verifikasi': .95, 'risiko': .9, 'partai': .8, 'ormas': .75, 'caleg': .7, 'kampanye': .65, 'drone': .5}
PRIO = MY['bobot']
maks_dampak = max([p['dampak_suara'] for p in lolos] or [1])
for p in lolos:
    efisiensi = 1 / (1 + (p['rp_per_suara'] or 0) / BIAYA_DASAR)
    urgensi = min(1.0, 60 / max(1, HARI)) if HARI > 0 else 1.0
    p['skor'] = round(PRIO.get(p['kategori'], .5) * (.45 + .55 * (p['dampak_suara'] / maks_dampak)) * (.6 + .4 * efisiensi) * (.7 + .3 * urgensi), 4)
lolos.sort(key=lambda p: -p['skor'])
lolos = [p for p in lolos if p['skor'] >= DNA['ambang']['prioritas_minimum']][:WK.get('maks_rekomendasi', 12)]

# ================= OTAK: aturan + LLM lokal (gagal-tertutup) =================
def muat_env():
    """Kunci API dibaca dari .env pusat (~/shamar/.env) lalu lingkungan proses."""
    kunci = {}
    for f in (os.path.expanduser('~/shamar/.env'), os.path.join(BASE, '.env'), os.path.expanduser('~/.env')):
        try:
            for baris in open(f):
                baris = baris.strip()
                if not baris or baris.startswith('#') or '=' not in baris: continue
                k, v = baris.split('=', 1)
                kunci.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception: pass
    for k, v in os.environ.items(): kunci.setdefault(k, v)
    return kunci
ENV = muat_env()

def _minta(url, data, headers, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers=dict({'Content-Type': 'application/json',
                                               'User-Agent': 'OckluPemilu/1.0 (+worker)',
                                               'Accept': 'application/json'}, **headers))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def otak_groq(prompt):
    key = ENV.get('GROQ_API_KEY') or ENV.get('GROQ_KEY')
    if not key: return None, 'groq: tidak ada GROQ_API_KEY'
    model = WK.get('model_groq', 'llama-3.3-70b-versatile')
    try:
        j = _minta('https://api.groq.com/openai/v1/chat/completions',
                   dict(model=model, temperature=0.2, max_tokens=420,
                        messages=[dict(role='user', content=prompt)]),
                   {'Authorization': 'Bearer ' + key})
        return j['choices'][0]['message']['content'].strip(), f'groq: {model}'
    except Exception as e:
        detail = ''
        try: detail = e.read().decode()[:120]
        except Exception: pass
        return None, f'groq gagal ({type(e).__name__}) {detail}'

def otak_gemini(prompt):
    key = ENV.get('GEMINI_API_KEY') or ENV.get('GOOGLE_API_KEY')
    if not key: return None, 'gemini: tidak ada GEMINI_API_KEY'
    daftar = list(WK.get('model_gemini', ['gemini-2.0-flash', 'gemini-flash-latest']))
    try:  # nama model Gemini berubah tanpa pemberitahuan — tanya dulu mana yang hidup
        req = urllib.request.Request(
            'https://generativelanguage.googleapis.com/v1beta/models?key=' + key,
            headers={'User-Agent': 'OckluPemilu/1.0', 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r:
            hidup = [m['name'].split('/')[-1] for m in json.load(r).get('models', [])
                     if 'generateContent' in m.get('supportedGenerationMethods', [])]
        daftar = [m for m in daftar if m in hidup] + [m for m in hidup if 'flash' in m and m not in daftar]
    except Exception:
        pass
    for model in daftar[:4]:
        try:
            j = _minta(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}',
                       dict(contents=[dict(parts=[dict(text=prompt)])],
                            generationConfig=dict(temperature=0.2, maxOutputTokens=420)), {})
            t = j['candidates'][0]['content']['parts'][0]['text'].strip()
            if t: return t, f'gemini: {model}'
        except Exception as e:
            detail = ''
            try: detail = e.read().decode()[:100]
            except Exception: pass
            terakhir = f'gemini gagal ({type(e).__name__}) {detail}'
            continue
    return None, locals().get('terakhir', 'gemini: semua model gagal')

def otak_lokal(ringkasan):
    url = WK.get('url_ollama', 'http://127.0.0.1:11434')
    try:
        with urllib.request.urlopen(url + '/api/tags', timeout=2) as r:
            model_ada = [m['name'] for m in json.load(r).get('models', [])]
    except Exception as e:
        return None, f'otak lokal mati ({type(e).__name__}) — worker jalan dengan aturan saja'
    if not model_ada: return None, 'otak lokal hidup tapi tidak ada model terpasang'
    mdl = next((m for m in model_ada if m.startswith(WK.get('model_lokal', 'llama3.2'))), model_ada[0])
    prompt = ("Kamu penasihat kampanye. Ringkas keadaan berikut jadi 4 kalimat bahasa Indonesia untuk rapat pagi. "
              "DILARANG menambah angka baru di luar yang diberikan. DILARANG menyarankan politik uang atau taktik yang "
              "mengeksploitasi agama.\n\n" + ringkasan)
    body = json.dumps(dict(model=mdl, prompt=prompt, stream=False,
                           options=dict(temperature=0.2, num_predict=320))).encode()
    try:
        req = urllib.request.Request(url + '/api/generate', data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r).get('response', '').strip(), f'otak lokal: {mdl}'
    except Exception as e:
        return None, f'otak lokal gagal menjawab ({type(e).__name__}) — worker jalan dengan aturan saja'

neutron_out = otak_neutron()
pemburu_out = pemburu_data()
agi_out = agi('Menangkan pemilihan dengan biaya terendah tanpa melanggar aturan')
pemicu_out = cek_pemicu()
keputusan_out = keputusan_dari(pemicu_out, neutron_out)
kelengkapan = D['meta']['kelengkapan_data']
cukup = kelengkapan >= CFG['batas_kelengkapan_data']
menang = R['gap'] <= 0
baris_pertama = (f"Proyeksi UNGGUL {abs(R['gap']):,.0f} suara ({R['margin_share']:+.1f} poin)." if menang
                 else f"Proyeksi KALAH {R['gap']:,.0f} suara dari target — ini kondisi kalah, bukan hampir menang.")
ringkasan = (f"{baris_pertama}\nSuara kita {R['proyeksi_kita']:,.0f} ({R['persen_kita']:.1f}%), lawan terkuat "
             f"{R['lawan_terkuat']} {R['lawan_terkuat_suara']:,.0f}. Cakupan saksi {SK['cakupan']:.0%} "
             f"({SK['kurang']:,.0f} saksi kurang). VaR 95% {RG['var95']:,.0f} suara. Skenario terburuk: "
             f"{RG['uji_tekanan'][0]['nama']} {RG['uji_tekanan'][0]['selisih_suara']:,.0f} suara. "
             f"Kelengkapan data {kelengkapan:.0%}. Anomali data {len(ON['anomali'])} temuan. "
             f"Tiga perintah teratas: " + '; '.join(p['judul'] for p in lolos[:3]) + '. ' + neutron_out['kalimat'])
PROMPT = ("Kamu penasihat kampanye pemenangan pemilu di Indonesia. Ringkas keadaan berikut jadi 5 kalimat "
          "bahasa Indonesia untuk rapat pagi tim: sebut kondisi menang/kalah, daerah yang harus digarap, dan "
          "langkah terdekat. DILARANG menambah angka baru di luar yang diberikan. DILARANG menyarankan politik "
          "uang, intimidasi, kampanye SARA, atau taktik yang mengeksploitasi keyakinan agama.\n\n" + ringkasan)
narasi, status_otak, jejak = None, 'worker dimatikan di konfigurasi', []
if WK.get('aktif', True):
    for nama_otak in WK.get('otak_urutan', ['groq', 'gemini', 'ollama']):
        if nama_otak == 'neutron': narasi, st = neutron_out['kalimat'], 'neutron core (deterministik)'
        elif nama_otak == 'groq': narasi, st = otak_groq(PROMPT)
        elif nama_otak == 'gemini': narasi, st = otak_gemini(PROMPT)
        elif nama_otak == 'ollama': narasi, st = otak_lokal(ringkasan)
        else: narasi, st = None, f'{nama_otak}: tidak dikenal'
        jejak.append(st)
        if narasi: status_otak = st; break
        status_otak = st
    if not narasi:
        status_otak = 'semua otak mati (' + ' | '.join(jejak) + ') — worker jalan dengan aturan saja' 
if narasi:
    kena = langgar_kata(narasi)
    if kena:
        ditolak.append(dict(perintah='narasi otak lokal', aturan='D3', alasan='mengandung: ' + ', '.join(kena)))
        narasi, status_otak = None, status_otak + ' — narasi ditolak gerbang DNA'

catatan = []
if not cukup:
    catatan.append(f"D2: kelengkapan data {kelengkapan:.0%} di bawah batas {CFG['batas_kelengkapan_data']:.0%} — "
                   "worker hanya boleh memerintahkan pengisian data, bukan menjanjikan kemenangan.")
if D['meta']['sumber_data'] == 'contoh':
    catatan.append("Sumber data masih CONTOH — semua perintah di bawah adalah latihan, bukan instruksi lapangan.")
catatan.append(f"Otak: {status_otak}.")

out = dict(
    dibuat=datetime.datetime.now().isoformat(timespec='seconds'),
    dna=dict(nama=DNA['nama'], versi=DNA['versi'], aturan=DNA['aturan']),
    otak=status_otak, jejak_otak=jejak, narasi=narasi, baris_pertama=baris_pertama, ringkasan=ringkasan,
    cukup_data=cukup, catatan=catatan,
    perintah=lolos, ditolak=ditolak, neutron=neutron_out, pemburu=pemburu_out, agi=agi_out, mythos=MY, pemicu=pemicu_out, keputusan=keputusan_out,
    hitungan=dict(dibuat=len(perintah), lolos=len(lolos), ditolak=len(ditolak)),
    papan=dict(dampak_total=sum(p['dampak_suara'] for p in lolos),
               biaya_total=sum(p['biaya'] for p in lolos),
               rp_per_suara=(sum(p['biaya'] for p in lolos) / max(1, sum(p['dampak_suara'] for p in lolos))),
               gap=R['gap'], tertutup=(sum(p['dampak_suara'] for p in lolos) >= R['gap'])),
)
json.dump(out, open(os.path.join(BASE, 'web', 'worker.json'), 'w'), ensure_ascii=False, default=float)
for _t in [x for x in pemicu_out if x['kena'] and x['tingkat'] == 'merah']:
    ledger.catat('pemicu', f"{_t['kode']} {_t['nama']} AKTIF", dict(ukuran=_t['ukuran'], nilai=_t['nilai'],
                 ambang=_t['ambang'], aksi=_t['aksi'], pj=_t['pj'], tenggat=_t['tenggat']))
ledger.catat('mythos', f"generasi {MY['generasi']}, {len(MY['ubah'])} penyesuaian bobot", dict(bobot=MY['bobot'], ubah=MY['ubah'])) if MY['ubah'] else None
ledger.catat('neutron', neutron_out['kalimat'],
             dict(putusan=neutron_out['putusan'], keyakinan=neutron_out['keyakinan'],
                  dissent=[l['lensa'] for l in neutron_out['dissent']]))
ledger.catat('worker', f"{out['hitungan']['lolos']} perintah lolos, {out['hitungan']['ditolak']} ditolak DNA",
             dict(otak=status_otak, dampak=out['papan']['dampak_total'], biaya=out['papan']['biaya_total'],
                  gap=R['gap'], tiga_teratas=[p['judul'] for p in lolos[:3]]))
print(f"WORKER  {out['hitungan']['lolos']} perintah lolos / {out['hitungan']['dibuat']} dibuat, "
      f"{out['hitungan']['ditolak']} ditolak DNA | dampak {out['papan']['dampak_total']:,.0f} suara "
      f"| biaya Rp {out['papan']['biaya_total']:,.0f} | {status_otak}")
