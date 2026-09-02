#!/usr/bin/env python3
"""Ocklu Pemetaan Pemilih — mesin hitung.
Semua angka di dasbor keluar dari file ini. Tidak ada angka yang ditulis tangan.
Setiap metrik menyimpan rumus + kelengkapan datanya supaya bisa diaudit.
Jalankan: python3 mesin.py   ->  web/data.json
"""
import csv, json, math, os, sys, datetime, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, 'data')
CFG = json.load(open(os.path.join(BASE, 'konfigurasi.json')))
PERINGATAN = []

def baca(nama):
    p = os.path.join(D, nama)
    if not os.path.exists(p):
        PERINGATAN.append(f"File {nama} tidak ada — metrik terkait dikosongkan, bukan ditebak.")
        return []
    with open(p, newline='') as f:
        return list(csv.DictReader(f))

def num(v, d=0.0):
    try: return float(str(v).replace(',', '.'))
    except Exception: return d

def erf_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))

# ---------- muat ----------
wilayah   = baca('wilayah.csv')
hasil     = baca('hasil_lalu.csv')
survei    = baca('survei.csv')
dtd       = baca('dtd.csv')
relawan   = baca('relawan.csv')
saksi     = baca('saksi.csv')
isu       = baca('isu.csv')
anggaran  = baca('anggaran.csv')
kandidat  = baca('kandidat.csv')
caleg     = baca('caleg.csv')
misi      = baca('drone_misi.csv')
partai_kk = baca('partai.csv')
ormas_kk  = baca('ormas.csv')
struktur  = baca('struktur_partai.csv')
riwayat   = baca('riwayat_pemilihan.csv')
dinasti   = baca('dinasti.csv')

KITA = CFG['kandidat_kita']
KOALISI = set(CFG['koalisi_pengusung'])
KOALISI_LAWAN = {}
for k in kandidat:
    if k['status'] != 'kita':
        KOALISI_LAWAN[k['nomor']] = set(k['koalisi'].split('|'))
NAMA_KAND = {k['nomor']: k['nama'] for k in kandidat}

# ---------- indeks per wilayah ----------
h_by_w = collections.defaultdict(dict)
for r in hasil:
    h_by_w[r['kode_wilayah']][r['partai']] = h_by_w[r['kode_wilayah']].get(r['partai'], 0) + num(r['suara'])
sv_by_w = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0]))  # kand -> [dukung, n]
for r in survei:
    c = sv_by_w[r['kode_wilayah']][r['kandidat']]
    c[0] += num(r['responden_dukung']); c[1] += num(r['n_sampel'])
dtd_by_w = {r['kode_wilayah']: r for r in dtd}
rel_by_w = collections.defaultdict(lambda: [0.0, 0.0])
for r in relawan:
    rel_by_w[r['kode_wilayah']][0] += num(r['jumlah']); rel_by_w[r['kode_wilayah']][1] += num(r['aktif_30hari'])
sak_by_w = {r['kode_wilayah']: r for r in saksi}
isu_by_w = collections.defaultdict(list)
for r in isu:
    isu_by_w[r['kode_wilayah']].append(r)
ang_by_w = collections.defaultdict(lambda: [0.0, 0.0])
for r in anggaran:
    ang_by_w[r['kode_wilayah']][0] += num(r['rencana']); ang_by_w[r['kode_wilayah']][1] += num(r['realisasi'])
misi_by_w = {r['kode_wilayah']: r for r in misi}
partai_by_w = collections.defaultdict(list)
for r in partai_kk: partai_by_w[r['kode_wilayah']].append(r)
ormas_by_w = collections.defaultdict(list)
for r in ormas_kk: ormas_by_w[r['kode_wilayah']].append(r)
str_by_w = collections.defaultdict(list)
for r in struktur: str_by_w[r['kode_wilayah']].append(r)
AT = CFG['aturan_pemilihan'][CFG['jenis_pemilihan']]
SP = CFG['struktur_partai']

BOBOT = CFG['bobot_ikc']
TURNOUT = CFG['turnout_proyeksi']
SAH = 0.97  # rasio suara sah dari yang hadir (ganti dari data resmi bila ada)

rows = []
for w in wilayah:
    kode = w['kode']; dpt = num(w['dpt']); tps = num(w['tps'])
    nama = w['kecamatan'] + (f" / {w['desa']}" if w.get('desa') else "")

    # a) basis koalisi dari pemilu lalu
    hp = h_by_w.get(kode, {})
    total_lalu = sum(hp.values())
    basis = sum(v for p, v in hp.items() if p in KOALISI) / total_lalu if total_lalu else None
    basis_lawan = {n: (sum(v for p, v in hp.items() if p in ko) / total_lalu if total_lalu else None)
                   for n, ko in KOALISI_LAWAN.items()}

    # b) survei wilayah + margin of error (koreksi populasi terbatas)
    sv = sv_by_w.get(kode, {})
    n_sampel = max([c[1] for c in sv.values()], default=0)
    survei_share, moe = None, None
    if n_sampel > 0 and KITA in sv:
        survei_share = sv[KITA][0] / sv[KITA][1] if sv[KITA][1] else None
        if survei_share is not None:
            fpc = math.sqrt(max(0.0, (dpt - n_sampel) / (dpt - 1))) if dpt > 1 else 1.0
            moe = 1.96 * math.sqrt(survei_share * (1 - survei_share) / n_sampel) * fpc * math.sqrt(1.5)
    survei_lawan = {n: (sv[n][0] / sv[n][1] if n in sv and sv[n][1] else None) for n in KOALISI_LAWAN}

    # c) door to door
    d = dtd_by_w.get(kode)
    dtd_share = (num(d['mendukung']) / num(d['terdata'])) if d and num(d['terdata']) else None
    dtd_cakupan = (num(d['terdata']) / dpt) if d and dpt else None

    # d) mesin darat: target 1 relawan aktif per 100 pemilih
    rel = rel_by_w.get(kode)
    mesin = min(1.0, rel[1] / (dpt / 100.0)) if rel and dpt else None
    # e) kekuatan mesin partai koalisi pengusung (ditimbang suara partai di wilayah itu)
    pr = partai_by_w.get(kode, [])
    pk = [x for x in pr if x['partai'] in KOALISI]
    partai_skor, partai_rinci = None, []
    if pk:
        bs = [hp.get(x['partai'], 0.0) for x in pk]
        tot_b = sum(bs)
        if tot_b > 0:
            partai_skor = sum((num(x['mesin_skor']) * .5 + num(x['dukungan_ke_kita']) * .5) * b
                              for x, b in zip(pk, bs)) / tot_b
        else:
            partai_skor = sum(num(x['mesin_skor']) * .5 + num(x['dukungan_ke_kita']) * .5 for x in pk) / len(pk)
    partai_rinci = [dict(partai=x['partai'], mesin=num(x['mesin_skor']), dukungan=num(x['dukungan_ke_kita']),
                         pengurus=num(x['pengurus_aktif']), saksi_disiapkan=num(x['saksi_disiapkan']),
                         suara_lalu=hp.get(x['partai'], 0.0), koalisi=(x['partai'] in KOALISI)) for x in pr]

    # e2) struktur partai koalisi: PAC, ranting, anak ranting
    st = [x for x in str_by_w.get(kode, []) if x['partai'] in KOALISI]
    def _n(v):
        try: return float(str(v).replace(',', '.'))
        except Exception: return 0.0
    ranting_target = sum(_n(x['target_unit']) for x in st if x['tingkat'].startswith('Ranting'))
    ranting_ada    = sum(_n(x['terbentuk']) for x in st if x['tingkat'].startswith('Ranting'))
    anak_target    = sum(_n(x['target_unit']) for x in st if x['tingkat'].startswith('Anak'))
    anak_ada       = sum(_n(x['terbentuk']) for x in st if x['tingkat'].startswith('Anak'))
    pac_ada        = sum(1 for x in st if x['tingkat'].startswith('PAC') and str(x['terbentuk']).lower() in ('ya', '1', 'true'))
    pengurus_total = sum(_n(x['pengurus']) for x in st)
    kader_total    = sum(_n(x['kader']) for x in st)
    struktur_skor = None
    if st and (ranting_target or anak_target):
        cakup_ranting = (ranting_ada / ranting_target) if ranting_target else 0
        cakup_anak = (anak_ada / anak_target) if anak_target else 0
        rasio_kader = min(1.0, (kader_total / max(1.0, dpt / 1000)) / SP['kader_per_1000_dpt'])
        struktur_skor = min(1.0, .45 * cakup_ranting + .3 * cakup_anak + .25 * rasio_kader)
    struktur_rinci = dict(pac_ada=pac_ada, pac_target=len(KOALISI),
                          ranting_ada=ranting_ada, ranting_target=ranting_target,
                          anak_ada=anak_ada, anak_target=anak_target,
                          pengurus=pengurus_total, kader=kader_total,
                          kader_per_1000=(kader_total / max(1.0, dpt / 1000)), skor=struktur_skor,
                          per_partai=[dict(partai=x['partai'], tingkat=x['tingkat'], unit=x['nama_unit'],
                                           pengurus=_n(x['pengurus']), kader=_n(x['kader']),
                                           target=_n(x['target_unit']), terbentuk=x['terbentuk'])
                                      for x in str_by_w.get(kode, [])])
    if partai_skor is not None and struktur_skor is not None:
        partai_skor = partai_skor * .7 + struktur_skor * .3
    elif struktur_skor is not None:
        partai_skor = struktur_skor

    # f) kekuatan ormas: jangkauan anggota x kedekatan x pengaruh, dibanding 25% DPT
    orl = ormas_by_w.get(kode, [])
    ormas_skor, jangkauan, jangkauan_lawan = None, 0.0, 0.0
    for x in orl:
        a, ke, pe = num(x['anggota']), num(x['kedekatan']), num(x['pengaruh'])
        if ke >= 0: jangkauan += a * ke * pe
        else: jangkauan_lawan += a * (-ke) * pe
    if orl and dpt:
        ormas_skor = min(1.0, jangkauan / (dpt * 0.25))
    ormas_rinci = [dict(ormas=x['ormas'], anggota=num(x['anggota']), pengurus=num(x['pengurus']),
                        kedekatan=num(x['kedekatan']), pengaruh=num(x['pengaruh']),
                        jangkauan=num(x['anggota']) * num(x['kedekatan']) * num(x['pengaruh'])) for x in orl]

    # g) tokoh: belum ada berkas -> sengaja kosong (bobot dinormalkan ulang)
    tokoh = None

    komp = {'basis_koalisi': basis, 'survei': survei_share, 'dtd': dtd_share,
            'mesin_darat': mesin, 'partai': partai_skor, 'ormas': ormas_skor, 'tokoh': tokoh}
    ada = {k: v for k, v in komp.items() if v is not None}
    bobot_ada = sum(BOBOT[k] for k in ada) or 1.0
    ikc = sum(min(1.0, v) * BOBOT[k] for k, v in ada.items()) / bobot_ada * 100 if ada else None
    kelengkapan = sum(BOBOT[k] for k in ada) / sum(BOBOT.values())

    rows.append(dict(kode=kode, nama=nama, kecamatan=w['kecamatan'], dapil=w['dapil'],
                     dpt=dpt, kk=num(w['kk']), tps=tps, lat=num(w['lat']), lon=num(w['lon']),
                     luas_km2=num(w['luas_km2']), indeks_urban=num(w['indeks_urban']),
                     basis=basis, basis_lawan=basis_lawan, survei=survei_share, moe=moe,
                     n_sampel=n_sampel, survei_lawan=survei_lawan,
                     dtd=dtd_share, dtd_cakupan=dtd_cakupan, mesin=mesin,
                     partai=partai_skor, partai_rinci=partai_rinci, struktur=struktur_rinci, ormas=ormas_skor,
                     ormas_rinci=ormas_rinci, ormas_jangkauan=jangkauan, ormas_lawan=jangkauan_lawan,
                     ikc=ikc, kelengkapan=kelengkapan,
                     relawan=(rel[0] if rel else 0), relawan_aktif=(rel[1] if rel else 0),
                     saksi_terisi=num(sak_by_w.get(kode, {}).get('tps_terisi_saksi', 0)),
                     saksi_terlatih=num(sak_by_w.get(kode, {}).get('saksi_terlatih', 0)),
                     anggaran_rencana=ang_by_w[kode][0], anggaran_realisasi=ang_by_w[kode][1],
                     isu=[dict(isu=i['isu'], sebut=num(i['penyebutan']), sentimen=num(i['sentimen_ke_kita']))
                          for i in sorted(isu_by_w.get(kode, []), key=lambda x: -num(x['penyebutan']))[:3]]))

# ---------- kalibrasi survei vs basis (untuk wilayah tanpa survei) ----------
pasangan = [(r['survei'], r['basis']) for r in rows if r['survei'] and r['basis']]
k_kal = sum(s / b for s, b in pasangan) / len(pasangan) if pasangan else 1.0
k_lawan = {}
for n in KOALISI_LAWAN:
    pp = [(r['survei_lawan'].get(n), r['basis_lawan'].get(n)) for r in rows
          if r['survei_lawan'].get(n) and r['basis_lawan'].get(n)]
    k_lawan[n] = sum(s / b for s, b in pp) / len(pp) if pp else 1.0
if len(pasangan) < 3:
    PERINGATAN.append("Kalibrasi survei<->basis dipakai dari <3 wilayah. Proyeksi wilayah tanpa survei lemah.")

def proyeksi_share(r, nomor):
    """Campuran survei / basis terkalibrasi / door-to-door, bobot dinormalkan pada yang tersedia."""
    if nomor == KITA:
        sv, ba, dd = r['survei'], (r['basis'] * k_kal if r['basis'] else None), r['dtd']
    else:
        sv = r['survei_lawan'].get(nomor)
        ba = r['basis_lawan'].get(nomor) * k_lawan[nomor] if r['basis_lawan'].get(nomor) else None
        dd = None
    w = {'sv': 0.60, 'ba': 0.25, 'dd': 0.15}
    pot = {'sv': sv, 'ba': ba, 'dd': dd}
    ada = {k: v for k, v in pot.items() if v is not None}
    if not ada: return None
    tot = sum(w[k] for k in ada)
    return sum(v * w[k] for k, v in ada.items()) / tot

kandidat_nomor = [KITA] + list(KOALISI_LAWAN.keys())
for r in rows:
    sh = {n: proyeksi_share(r, n) for n in kandidat_nomor}
    jml = sum(v for v in sh.values() if v)
    if jml and jml > 1.0:  # normalisasi bila hasil campuran melebihi 100%
        sh = {n: (v / jml if v else v) for n, v in sh.items()}
    r['share'] = sh
    suara_sah = r['dpt'] * TURNOUT * SAH
    r['suara_sah_proyeksi'] = suara_sah
    r['proyeksi'] = {n: (suara_sah * v if v else 0.0) for n, v in sh.items()}

# ---------- agregat ----------
DPT = sum(r['dpt'] for r in rows)
TPS = sum(r['tps'] for r in rows)
SUARA_SAH = sum(r['suara_sah_proyeksi'] for r in rows)
tot_proy = {n: sum(r['proyeksi'][n] for r in rows) for n in kandidat_nomor}
share_tot = {n: (v / SUARA_SAH if SUARA_SAH else 0) for n, v in tot_proy.items()}
lawan_terkuat = max(KOALISI_LAWAN, key=lambda n: tot_proy[n]) if KOALISI_LAWAN else None
metode = AT['metode']
aturan_info = dict(jenis=CFG['jenis_pemilihan'], nama=AT['nama'], metode=metode,
                   tingkat=AT.get('tingkat'), catatan=AT.get('catatan', ''), syarat=[])
if metode == 'penunjukan':
    target_suara = None
    PERINGATAN.append(f"{AT['nama']}: jabatan ini tidak dipilih lewat pemungutan suara. Dasbor beralih ke peta dukungan & pemangku kepentingan — proyeksi suara dan target kemenangan dimatikan.")
elif metode == 'mayoritas_sebaran':
    suara_50 = SUARA_SAH * AT.get('ambang', .5) + 1
    lawan_plus = tot_proy[lawan_terkuat] * (1 + CFG['margin_aman']) if lawan_terkuat else 0
    target_suara = max(suara_50, lawan_plus)
    prov = collections.defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        p = r.get('provinsi') or 'TANPA PROVINSI'
        prov[p][0] += r['proyeksi'][KITA]; prov[p][1] += r['suara_sah_proyeksi']
    lolos = [p for p, v in prov.items() if v[1] and v[0] / v[1] >= AT.get('sebaran_persen', .2)]
    perlu = math.ceil(len(prov) * AT.get('sebaran_wilayah_min', .5)) + (0 if len(prov) % 2 else 1)
    aturan_info['syarat'].append(dict(nama=f"Sebaran >={AT.get('sebaran_persen',.2):.0%} di lebih dari separuh provinsi",
                                      nilai=f"{len(lolos)} dari {len(prov)} provinsi", perlu=perlu,
                                      terpenuhi=len(lolos) >= perlu))
    aturan_info['syarat'].append(dict(nama=f"Suara sah >{AT.get('ambang',.5):.0%}",
                                      nilai=f"{share_tot[KITA]:.1%}", perlu=AT.get('ambang', .5) * 100,
                                      terpenuhi=share_tot[KITA] > AT.get('ambang', .5)))
    if not all(x['terpenuhi'] for x in aturan_info['syarat']):
        aturan_info['syarat'].append(dict(nama='Putaran kedua', nilai='kemungkinan besar terjadi', perlu=None, terpenuhi=False))
elif metode == 'sainte_lague':
    dsu = collections.defaultdict(lambda: collections.defaultdict(float))
    for r in rows:
        for pp, vv in h_by_w.get(r['kode'], {}).items(): dsu[r['dapil']][pp] += vv
    harga = []
    for dp, kursi in CFG['kursi_dapil'].items():
        sp = dsu.get(dp, {})
        if not sp: continue
        kuota = sorted([sp[q] / (2 * i + 1) for q in sp for i in range(int(kursi))], reverse=True)
        if len(kuota) >= int(kursi): harga.append(kuota[int(kursi) - 1])
    harga_rata = sum(harga) / len(harga) if harga else 0
    target_suara = harga_rata * (1 + CFG['margin_aman'])
    aturan_info['syarat'].append(dict(nama='Harga kursi terakhir (rata-rata dapil)', nilai=f"{harga_rata:,.0f} suara",
                                      perlu=None, terpenuhi=tot_proy[KITA] >= harga_rata))
    if AT.get('ambang_parlemen'):
        aturan_info['syarat'].append(dict(nama=f"Ambang parlemen {AT['ambang_parlemen']:.0%} nasional",
                                          nilai=f"{share_tot[KITA]:.1%} (di wilayah kerja ini)",
                                          perlu=AT['ambang_parlemen'] * 100,
                                          terpenuhi=share_tot[KITA] >= AT['ambang_parlemen']))
else:
    target_suara = tot_proy[lawan_terkuat] * (1 + CFG['margin_aman']) if lawan_terkuat else SUARA_SAH * 0.5
    aturan_info['syarat'].append(dict(nama='Suara terbanyak', nilai=f"{tot_proy[KITA]:,.0f} vs {tot_proy.get(lawan_terkuat,0):,.0f}",
                                      perlu=None, terpenuhi=(tot_proy[KITA] > tot_proy.get(lawan_terkuat, 0))))
gap = (target_suara - tot_proy[KITA]) if target_suara is not None else 0.0
aturan_info['target'] = target_suara

# ketidakpastian: MoE survei tertimbang + risiko turnout
n_efektif = sum(r['n_sampel'] for r in rows)
sd_survei = math.sqrt(share_tot[KITA] * (1 - share_tot[KITA]) / n_efektif * 1.5) if n_efektif else 0.05
sd_turnout = 0.02
kelengkapan_rata = sum(r['kelengkapan'] * r['dpt'] for r in rows) / DPT if DPT else 0
sd_total = math.sqrt(sd_survei ** 2 + sd_turnout ** 2 + (0.03 * (1 - kelengkapan_rata)) ** 2)
margin_share = share_tot[KITA] - (share_tot[lawan_terkuat] if lawan_terkuat else 0)
peluang = erf_cdf(margin_share / (sd_total * math.sqrt(2))) if sd_total else None
if kelengkapan_rata < CFG['batas_kelengkapan_data']:
    peluang = None
    PERINGATAN.append(f"Kelengkapan data {kelengkapan_rata:.0%} < batas {CFG['batas_kelengkapan_data']:.0%} — peluang menang tidak ditampilkan.")

# ---------- zona prioritas (kuadran potensi x kekuatan) ----------
ikc_list = sorted([r['ikc'] for r in rows if r['ikc'] is not None])
med_ikc = ikc_list[len(ikc_list) // 2] if ikc_list else 0
dpt_list = sorted([r['dpt'] for r in rows]); med_dpt = dpt_list[len(dpt_list) // 2] if dpt_list else 0
for r in rows:
    kuat = (r['ikc'] or 0) >= med_ikc; besar = r['dpt'] >= med_dpt
    r['zona'] = 'BASIS — jaga & naikkan hadir' if (kuat and besar) else \
                'GARAP — medan tempur utama'   if (not kuat and besar) else \
                'AMANKAN — murah dipertahankan' if (kuat and not besar) else \
                'EFISIENSI — jangan boros'
    r['saksi_butuh'] = r['tps'] * CFG['saksi_per_tps']
    r['saksi_cakupan'] = (r['saksi_terisi'] * CFG['saksi_per_tps'] / r['saksi_butuh']) if r['saksi_butuh'] else 0
    r['tps_tanpa_saksi'] = max(0, r['tps'] - r['saksi_terisi'])
    r['rawan'] = (not kuat) and r['saksi_cakupan'] < 0.8
    r['biaya_per_suara'] = (r['anggaran_realisasi'] / r['proyeksi'][KITA]) if r['proyeksi'][KITA] else None

# ---------- alokasi anggaran greedy untuk menutup gap ----------
SWING = CFG['swing_maksimal_per_program']
biaya_dasar = (sum(r['anggaran_realisasi'] for r in rows) / max(1.0, sum(r['proyeksi'][KITA] for r in rows)))
kandidat_aksi = []
for r in rows:
    headroom = SWING * (1 - (r['ikc'] or 0) / 100.0)      # wilayah lemah = ruang naik lebih besar
    tambah = r['suara_sah_proyeksi'] * headroom
    biaya_unit = biaya_dasar * (1 + (1 - (r['ikc'] or 0) / 100.0) * 1.5)  # makin lemah makin mahal per suara
    if tambah > 0:
        kandidat_aksi.append(dict(kode=r['kode'], nama=r['nama'], zona=r['zona'], ikc=r['ikc'],
                                  tambahan_suara=tambah, biaya=tambah * biaya_unit,
                                  biaya_per_suara=biaya_unit))
kandidat_aksi.sort(key=lambda x: x['biaya_per_suara'])
kum_suara = 0.0; kum_biaya = 0.0; rencana = []
for a in kandidat_aksi:
    if kum_suara >= gap and gap > 0: break
    perlu = (gap - kum_suara) if gap > 0 else 0
    pakai = min(a['tambahan_suara'], perlu) if perlu > 0 else 0
    if pakai <= 0: break
    kum_suara += pakai; kum_biaya += pakai * a['biaya_per_suara']
    rencana.append(dict(a, dipakai_suara=pakai, dipakai_biaya=pakai * a['biaya_per_suara'],
                        kumulatif_suara=kum_suara, kumulatif_biaya=kum_biaya))
gap_tertutup = kum_suara >= gap if gap > 0 else True

# ---------- Sainte-Lague per dapil (mode DPR/DPRD) ----------
def sainte_lague(suara_partai, kursi):
    alok = {p: 0 for p in suara_partai}
    for _ in range(int(kursi)):
        best, bv = None, -1
        for p, v in suara_partai.items():
            q = v / (2 * alok[p] + 1)
            if q > bv: bv, best = q, p
        alok[best] += 1
    return alok

dapil_suara = collections.defaultdict(lambda: collections.defaultdict(float))
for r in rows:
    for p, v in h_by_w.get(r['kode'], {}).items():
        dapil_suara[r['dapil']][p] += v
caleg_by = collections.defaultdict(list)
for c in caleg:
    caleg_by[(c['dapil'], c['partai'])].append(c)
kursi_out = []
for dp, kursi in CFG['kursi_dapil'].items():
    sp = dict(dapil_suara.get(dp, {}))
    if not sp: continue
    alok = sainte_lague(sp, kursi)
    total = sum(sp.values())
    # harga kursi = kuota terakhir yang lolos
    kuota = sorted([sp[p] / (2 * i + 1) for p in sp for i in range(int(kursi))], reverse=True)
    harga = kuota[int(kursi) - 1] if len(kuota) >= kursi else None
    daftar = []
    for p in sorted(sp, key=lambda x: -sp[x]):
        cl = sorted(caleg_by.get((dp, p), []), key=lambda c: -num(c['suara_pribadi']))
        terpilih = [c['nama'] for c in cl[:alok[p]]]
        kita = [c for c in cl if c['status'] == 'kita']
        daftar.append(dict(partai=p, suara=sp[p], persen=sp[p] / total * 100, kursi=alok[p],
                           terpilih=terpilih,
                           kita_lolos=(bool(kita) and kita[0]['nama'] in terpilih) if kita else None,
                           kita_nama=(kita[0]['nama'] if kita else None),
                           kita_suara=(num(kita[0]['suara_pribadi']) if kita else None),
                           ambang_internal=(num(cl[alok[p] - 1]['suara_pribadi']) if alok[p] > 0 and len(cl) >= alok[p] else None)))
    kursi_out.append(dict(dapil=dp, kursi=kursi, total_suara=total, harga_kursi=harga, partai=daftar))

# ---------- drone: fotogrametri nyata ----------
dr = CFG['drone']
gsd = (dr['sensor_lebar_mm'] * dr['tinggi_terbang_m'] * 100.0) / (dr['fokal_mm'] * dr['lebar_piksel'])  # cm/px
swath_w = gsd / 100.0 * dr['lebar_piksel']            # meter (melintang jalur)
swath_h = gsd / 100.0 * dr['tinggi_piksel']           # meter (searah jalur)
jarak_jalur = swath_w * (1 - dr['overlap_samping'])
v_maks_overlap = swath_h * (1 - dr['overlap_depan']) / dr['interval_jepret_detik']
v = min(v_maks_overlap, dr['kecepatan_maks_ms'])
detik_efektif = dr['endurance_menit'] * 60 * (1 - dr['cadangan_baterai'])
luas_per_sortie_ha = v * detik_efektif * jarak_jalur / 10000.0
total_target_km2 = sum(num(m['luas_target_km2']) for m in misi)
sortie = math.ceil(total_target_km2 * 100 / luas_per_sortie_ha) if luas_per_sortie_ha else 0
misi_out = []
for m in misi:
    l = num(m['luas_target_km2'])
    s = math.ceil(l * 100 / luas_per_sortie_ha) if luas_per_sortie_ha else 0
    w = next((x for x in rows if x['kode'] == m['kode_wilayah']), None)
    misi_out.append(dict(kode=m['kode_wilayah'], nama=(w['nama'] if w else m['kode_wilayah']),
                         tujuan=m['tujuan'], luas_km2=l, status=m['status'], sortie=s,
                         jam_terbang=round(s * dr['endurance_menit'] * (1 - dr['cadangan_baterai']) / 60, 2),
                         biaya=s * dr['biaya_per_sortie'],
                         rumah_perkiraan=(w['kk'] if w else None),
                         dpt_per_km2=(round(w['dpt'] / w['luas_km2']) if w and w['luas_km2'] else None)))
drone_out = dict(gsd_cm_px=round(gsd, 2), swath_m=round(swath_w, 1), jarak_jalur_m=round(jarak_jalur, 1),
                 kecepatan_ms=round(v, 2), luas_per_sortie_ha=round(luas_per_sortie_ha, 1),
                 total_target_km2=round(total_target_km2, 1), sortie=sortie,
                 hari=math.ceil(sortie / dr['sortie_per_hari']) if dr['sortie_per_hari'] else None,
                 baterai_set=math.ceil(sortie / 3), biaya=sortie * dr['biaya_per_sortie'],
                 jam_terbang=round(sortie * dr['endurance_menit'] * (1 - dr['cadangan_baterai']) / 60, 1),
                 misi=misi_out, parameter=dr)

# ---------- saksi & logistik ----------
saksi_butuh = sum(r['saksi_butuh'] for r in rows)
saksi_ada = sum(r['saksi_terisi'] * CFG['saksi_per_tps'] for r in rows)
tps_rawan = sum(r['tps_tanpa_saksi'] for r in rows if r['rawan'])
saksi_out = dict(butuh=saksi_butuh, ada=saksi_ada, kurang=max(0, saksi_butuh - saksi_ada),
                 cakupan=(saksi_ada / saksi_butuh if saksi_butuh else 0),
                 biaya_penuh=saksi_butuh * CFG['honor_saksi'],
                 biaya_kurang=max(0, saksi_butuh - saksi_ada) * CFG['honor_saksi'],
                 tps_rawan_tanpa_saksi=tps_rawan,
                 risiko_faktor=CFG['risiko_selisih_tanpa_saksi'],
                 suara_beresiko=round(tps_rawan * CFG['maks_pemilih_per_tps'] * TURNOUT
                                      * share_tot[KITA] * CFG['risiko_selisih_tanpa_saksi']))

# ---------- isu nasional (agregat tertimbang DPT) ----------
agg_isu = collections.defaultdict(lambda: [0.0, 0.0])
for r in rows:
    for i in r['isu']:
        agg_isu[i['isu']][0] += i['sebut']
        agg_isu[i['isu']][1] += i['sentimen'] * i['sebut']
isu_out = sorted([dict(isu=k, sebut=v[0], sentimen=(v[1] / v[0] if v[0] else 0))
                  for k, v in agg_isu.items()], key=lambda x: -x['sebut'])

# ---------- pagar kejujuran ----------
if CFG['sumber_data'] == 'contoh':
    PERINGATAN.insert(0, "SUMBER DATA = CONTOH. Seluruh angka simulasi. Ganti data/*.csv dengan DPT & hasil resmi KPU, lalu set sumber_data='resmi'.")
tanpa_survei = [r['nama'] for r in rows if r['survei'] is None]
if tanpa_survei:
    PERINGATAN.append(f"{len(tanpa_survei)} wilayah tanpa survei — proyeksinya dari basis partai terkalibrasi (k={k_kal:.2f}): " + ", ".join(tanpa_survei))
if not any(r['mesin'] is not None for r in rows):
    PERINGATAN.append("Data relawan kosong — komponen mesin darat tidak dihitung.")
PERINGATAN.append("Komponen 'tokoh' belum punya berkas data; bobotnya dinormalkan ke komponen lain, tidak ditebak.")



# ---------- ONTOLOGI ala Palantir: satukan silo -> objek, hubungan, anomali ----------
def bangun_ontologi():
    entitas, hubungan, anomali = [], [], []
    def E(i, t, n, nilai=None, skor=None, ket=None):
        entitas.append(dict(id=i, tipe=t, nama=n, nilai=nilai, skor=skor, ket=ket))
    def L(a, b, jenis, bobot, ket=None):
        hubungan.append(dict(dari=a, ke=b, jenis=jenis, bobot=bobot, ket=ket))

    for r in rows:
        E('W:' + r['kode'], 'Wilayah', r['nama'], r['dpt'], r['ikc'], r['zona'])
    # partai sebagai objek lintas wilayah
    pagg = collections.defaultdict(lambda: dict(suara=0.0, pengurus=0.0, saksi=0.0, wilayah=0, dukungan=0.0))
    for r in rows:
        for x in r['partai_rinci']:
            a = pagg[x['partai']]
            a['suara'] += x['suara_lalu']; a['pengurus'] += x['pengurus']
            a['saksi'] += x['saksi_disiapkan']; a['wilayah'] += 1; a['dukungan'] += x['dukungan']
            L('W:' + r['kode'], 'P:' + x['partai'], 'basis_suara', x['suara_lalu'])
    for p, a in pagg.items():
        E('P:' + p, 'Partai', p, a['suara'], (a['dukungan'] / a['wilayah'] * 100) if a['wilayah'] else None,
          ('koalisi pengusung' if p in KOALISI else 'di luar koalisi'))
    # ormas
    oagg = collections.defaultdict(lambda: dict(anggota=0.0, wilayah=0, jangkauan=0.0))
    for r in rows:
        for x in r['ormas_rinci']:
            a = oagg[x['ormas']]
            a['anggota'] += x['anggota']; a['wilayah'] += 1; a['jangkauan'] += x['jangkauan']
            L('W:' + r['kode'], 'O:' + x['ormas'], 'jangkauan_ormas', x['jangkauan'])
    for o, a in oagg.items():
        E('O:' + o, 'Ormas', o, a['anggota'],
          (a['jangkauan'] / a['anggota'] * 100) if a['anggota'] else None, f"hadir di {a['wilayah']} wilayah")
    # isu & kandidat
    for i in isu_out:
        E('I:' + i['isu'], 'Isu', i['isu'], i['sebut'], i['sentimen'] * 100)
    for r in rows:
        for i in r['isu']:
            L('W:' + r['kode'], 'I:' + i['isu'], 'isu_dominan', i['sebut'], f"sentimen {i['sentimen']}")
    for k in kandidat:
        E('K:' + k['nomor'], 'Kandidat', k['nama'], tot_proy.get(k['nomor'], 0), share_tot.get(k['nomor'], 0) * 100, k['status'])
        for p in k['koalisi'].split('|'):
            L('K:' + k['nomor'], 'P:' + p, 'diusung', pagg.get(p, {}).get('suara', 0))

    # sentralitas berbobot (leverage lintas wilayah)
    dg = collections.defaultdict(float)
    for h in hubungan:
        dg[h['dari']] += h['bobot']; dg[h['ke']] += h['bobot']
    mx = max(dg.values()) if dg else 1
    for e in entitas:
        e['sentralitas'] = round(dg.get(e['id'], 0) / mx, 4) if mx else 0

    # ---- anomali (insight ala Maven) ----
    def z(vals):
        m = sum(vals) / len(vals); sd = (sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1)) ** .5
        return m, sd
    rasio = [r['dpt'] / r['kk'] for r in rows if r['kk']]
    m_r, sd_r = z(rasio) if rasio else (0, 0)
    q_ang = sorted(r['anggaran_realisasi'] for r in rows)
    q3 = q_ang[int(len(q_ang) * .75)] if q_ang else 0
    for r in rows:
        if r['kk'] and sd_r and abs(r['dpt'] / r['kk'] - m_r) / sd_r > 2:
            anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='DPT vs KK tidak wajar',
                skor=round(min(1, abs(r['dpt'] / r['kk'] - m_r) / sd_r / 4), 2),
                bukti=f"rasio DPT/KK {r['dpt']/r['kk']:.2f} vs rata-rata {m_r:.2f}",
                tindakan='Cocokkan DPT dengan data KK/rumah (pakai ortofoto drone) sebelum dipakai sebagai target.'))
        if r['survei'] is not None and r['basis'] and r['moe']:
            beda = abs(r['survei'] - r['basis'] * k_kal)
            if beda > 3 * r['moe']:
                anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='Survei jauh dari basis partai',
                    skor=round(min(1, beda / (6 * r['moe'])), 2),
                    bukti=f"survei {r['survei']:.1%} vs basis terkalibrasi {r['basis']*k_kal:.1%} (MoE ±{r['moe']:.1%})",
                    tindakan='Ulangi sampel di wilayah ini atau verifikasi lewat door-to-door sebelum menggeser anggaran.'))
        if r['mesin'] and r['mesin'] > .6 and (r['dtd_cakupan'] or 0) < .1:
            anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='Klaim mesin darat tanpa bukti pendataan',
                skor=round(min(1, r['mesin'] - (r['dtd_cakupan'] or 0)), 2),
                bukti=f"relawan aktif {r['relawan_aktif']:.0f} tapi door-to-door hanya {(r['dtd_cakupan'] or 0):.1%} DPT",
                tindakan='Minta setoran data door-to-door; tanpa itu skor mesin darat tidak boleh dipakai menaikkan target.'))
        if r['anggaran_realisasi'] >= q3 and (r['ikc'] or 0) < med_ikc:
            anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='Anggaran besar, kekuatan tetap rendah',
                skor=round(min(1, (q3 and r['anggaran_realisasi'] / q3 or 1) - .5), 2),
                bukti=f"realisasi Rp {r['anggaran_realisasi']:,.0f} tapi IKC {r['ikc']:.1f} di bawah median {med_ikc:.1f}",
                tindakan='Audit pos belanja wilayah ini sebelum menambah alokasi.'))
        if r['ormas_lawan'] > r['ormas_jangkauan'] and r['ormas_jangkauan'] >= 0:
            anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='Ormas condong ke lawan',
                skor=round(min(1, (r['ormas_lawan'] - r['ormas_jangkauan']) / max(1, r['dpt'] * .1)), 2),
                bukti=f"jangkauan ormas lawan {r['ormas_lawan']:,.0f} vs pro-kita {r['ormas_jangkauan']:,.0f}",
                tindakan='Buka jalur silaturahmi ke pengurus ormas dominan; jangan kirim materi konfrontatif ke wilayah ini.'))
        if r['zona'].startswith('BASIS') and r['saksi_cakupan'] < .6:
            anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='Basis tanpa penjagaan saksi',
                skor=round(1 - r['saksi_cakupan'], 2),
                bukti=f"zona basis tapi cakupan saksi {r['saksi_cakupan']:.0%} ({r['tps_tanpa_saksi']:.0f} TPS kosong)",
                tindakan='Isi saksi di TPS basis lebih dulu — suara terbanyak justru paling mudah hilang di sini.'))
        tot_lalu = sum(h_by_w.get(r['kode'], {}).values())
        if tot_lalu > r['dpt']:
            anomali.append(dict(kode=r['kode'], wilayah=r['nama'], jenis='Suara pemilu lalu melebihi DPT',
                skor=1.0, bukti=f"suara {tot_lalu:,.0f} > DPT {r['dpt']:,.0f}",
                tindakan='Data salah tempel/duplikat. Perbaiki sebelum dipakai — mesin memakai ini sebagai basis.'))
    # resolusi entitas: wilayah kembar (nama mirip / koordinat berdekatan)
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            dekat = ((a['lat'] - b['lat']) ** 2 + (a['lon'] - b['lon']) ** 2) ** .5 * 111 < 0.5
            if a['nama'].strip().lower() == b['nama'].strip().lower() or dekat:
                anomali.append(dict(kode=a['kode'], wilayah=f"{a['nama']} ↔ {b['nama']}", jenis='Kemungkinan wilayah ganda',
                    skor=.8, bukti='nama sama' if a['nama'].strip().lower() == b['nama'].strip().lower() else 'jarak < 0,5 km',
                    tindakan='Gabungkan atau perbaiki koordinat/kode wilayah agar DPT tidak dihitung dua kali.'))
    anomali.sort(key=lambda x: -x['skor'])
    return dict(entitas=sorted(entitas, key=lambda e: -(e['sentralitas'] or 0)), hubungan=hubungan,
                anomali=anomali, jumlah=dict(entitas=len(entitas), hubungan=len(hubungan), anomali=len(anomali)))

# ---------- RISIKO ala Aladdin: model faktor, VaR, kontribusi risiko, uji tekanan ----------
def bangun_risiko():
    """Model faktor ala Aladdin: paparan portofolio suara, VaR, kontribusi risiko, uji tekanan."""
    FR = CFG.get('faktor_risiko', {})
    faktor = ['basis_partai', 'ormas', 'urban', 'isu', 'ketergantungan_turnout']
    vol = [0.05, FR.get('guncangan_ormas', .2), 0.05, FR.get('guncangan_isu', .15), FR.get('guncangan_turnout', .08)]
    E = []   # paparan positif 0..1 (berapa besar suara kita bergantung pada faktor itu)
    for r in rows:
        seb = sum(i['sebut'] for i in r['isu']) or 1
        isu_s = sum(i['sentimen'] * i['sebut'] for i in r['isu']) / seb
        E.append([r['basis'] or 0, r['ormas'] or 0, r['indeks_urban'], (1 + isu_s) / 2, 1.0])
    n, k = len(E), len(faktor)
    mu = [sum(x[j] for x in E) / n for j in range(k)]
    sd = [max(1e-9, (sum((x[j] - mu[j]) ** 2 for x in E) / max(1, n - 1)) ** .5) for j in range(k)]
    Z = [[(x[j] - mu[j]) / sd[j] for j in range(k)] for x in E]
    korelasi = [[(sum(Z[i][a] * Z[i][b] for i in range(n)) / max(1, n - 1)) if sd[a] > 1e-8 and sd[b] > 1e-8 else (1.0 if a == b else 0.0)
                 for b in range(k)] for a in range(k)]
    C = [[korelasi[a][b] * vol[a] * vol[b] for b in range(k)] for a in range(k)]
    tot = sum(r['proyeksi'][KITA] for r in rows) or 1
    w = [r['proyeksi'][KITA] / tot for r in rows]
    b = [sum(w[i] * E[i][j] for i in range(n)) for j in range(k)]          # paparan portofolio
    Cb = [sum(C[a][j] * b[j] for j in range(k)) for a in range(k)]
    var_faktor = sum(b[a] * Cb[a] for a in range(k))
    def s_idio(r):
        return (r['moe'] / 1.96) if r['moe'] else 0.05 * (1.3 - (r['kelengkapan'] or 0))
    id_var = sum((w[i] * s_idio(rows[i])) ** 2 for i in range(n))
    sigma = (var_faktor + id_var) ** .5
    zc = 1.645 if FR.get('tingkat_keyakinan', .95) >= .95 else 1.282
    kontrib = []
    for i, r in enumerate(rows):
        mc = (sum(E[i][a] * Cb[a] for a in range(k)) + w[i] * s_idio(r) ** 2) / sigma if sigma else 0
        kontrib.append(dict(kode=r['kode'], nama=r['nama'], bobot=w[i], marginal=mc,
                            kontribusi=w[i] * mc,
                            kontribusi_persen=(w[i] * mc / sigma * 100) if sigma else 0,
                            paparan={faktor[j]: E[i][j] for j in range(k)},
                            idio=s_idio(r)))
    kontrib.sort(key=lambda x: -x['kontribusi'])
    hhi = sum(x ** 2 for x in w)
    target_share = (target_suara / SUARA_SAH) if (SUARA_SAH and target_suara is not None) else share_tot[KITA]
    te = abs(share_tot[KITA] - target_share)
    def tekanan(nama, guncang, ket, tambahan=0.0):
        d = sum(b[j] * vol[j] * guncang.get(faktor[j], 0) for j in range(k))
        suara = tot_proy[KITA] * (1 + d) + tambahan
        lw = tot_proy.get(lawan_terkuat, 0)
        return dict(nama=nama, ket=ket, dampak_persen=d * 100, suara=suara,
                    selisih_suara=suara - tot_proy[KITA],
                    margin=((suara - lw) / SUARA_SAH * 100) if SUARA_SAH else 0, menang=(suara > lw))
    hilang_saksi = -(saksi_out['suara_beresiko'] or 0)
    uji = [
        tekanan('Turnout anjlok 2 simpangan', {'ketergantungan_turnout': -2}, 'Partisipasi turun; wilayah padat paling terpukul'),
        tekanan('Ormas berbalik', {'ormas': -2}, 'Ormas pendukung berpindah dukungan'),
        tekanan('Isu negatif viral', {'isu': -2}, 'Sentimen isu berbalik dua simpangan'),
        tekanan('Mesin partai mogok', {'basis_partai': -2}, 'Partai koalisi tidak menggerakkan struktur'),
        tekanan('Serangan gabungan', {'ormas': -1.5, 'isu': -1.5, 'ketergantungan_turnout': -1}, 'Tiga guncangan sekaligus'),
        tekanan('Saksi tidak dilengkapi', {}, 'Suara berisiko di TPS rawan tanpa saksi', hilang_saksi),
        tekanan('Konsolidasi berhasil', {'basis_partai': 1.5, 'ormas': 1, 'isu': 1}, 'Struktur partai + ormas + isu bergerak searah'),
    ]
    uji.sort(key=lambda x: x['selisih_suara'])
    return dict(faktor=faktor, volatilitas={faktor[j]: vol[j] for j in range(k)}, korelasi=korelasi,
                paparan_portofolio={faktor[j]: b[j] for j in range(k)},
                sigma=sigma, sigma_suara=sigma * tot_proy[KITA], var95=zc * sigma * tot_proy[KITA],
                var95_persen=zc * sigma * 100, hhi=hhi, wilayah_efektif=(1 / hhi if hhi else None),
                tracking_error=te * 100, kontribusi=kontrib, uji_tekanan=uji,
                catatan='Paparan = seberapa besar suara kita bergantung pada tiap faktor (0-1, ditimbang proyeksi wilayah). Kovarians = korelasi silang wilayah x volatilitas guncangan dari konfigurasi. VaR 95% = 1,645 x sigma x proyeksi suara kita. Ini pengukur risiko, bukan ramalan.')


# ---------- STRATEGI: proyeksi menang/kalah per daerah + cara memenangkannya ----------
KUNJUNGAN_PER_RELAWAN_HARI = 15
HARI_EFEKTIF = max(7, min(120, (datetime.date.fromisoformat(CFG['tanggal_pemungutan']) - datetime.date.today()).days))

def strategi_wilayah():
    hasil = []
    for r in rows:
        sh = r['share'][KITA] or 0
        pesaing = sorted(((n, r['share'].get(n) or 0) for n in KOALISI_LAWAN), key=lambda x: -x[1])
        lw = pesaing[0] if pesaing else (None, 0.0)
        margin = sh - lw[1]
        sd = (r['moe'] / 1.96) if r['moe'] else 0.06 * (1.3 - (r['kelengkapan'] or 0))
        sd = (sd ** 2 + 0.02 ** 2) ** .5
        p = erf_cdf(margin / (sd * math.sqrt(2))) if sd else None
        kat = ('MENANG AMAN' if p >= .8 else 'MENANG TIPIS' if p >= .6 else 'IMBANG' if p >= .4
               else 'KALAH TIPIS' if p >= .2 else 'KALAH')
        kurang = max(0.0, (lw[1] - sh) * r['suara_sah_proyeksi']) + (1 if margin < 0 else 0)
        aman = max(0.0, (lw[1] + CFG['margin_aman'] - sh) * r['suara_sah_proyeksi'])
        pemilih_per_kk = (r['dpt'] / r['kk']) if r['kk'] else 3.0
        konversi = r['dtd'] if (r['dtd'] and r['dtd'] > .05) else 0.30
        rumah = aman / max(0.01, pemilih_per_kk * TURNOUT * konversi)
        rumah = min(rumah, r['kk'])
        relawan_butuh = math.ceil(rumah / (KUNJUNGAN_PER_RELAWAN_HARI * HARI_EFEKTIF)) if rumah else 0
        relawan_kurang = max(0, relawan_butuh - r['relawan_aktif'])
        st = r['struktur']
        ranting_kurang = max(0.0, st['ranting_target'] - st['ranting_ada'])
        anak_kurang = max(0.0, st['anak_target'] - st['anak_ada'])
        isu_top = r['isu'][0]['isu'] if r['isu'] else None
        isu_negatif = [i['isu'] for i in r['isu'] if i['sentimen'] < 0]
        ormas_besar = sorted(r['ormas_rinci'], key=lambda x: -x['anggota'])[:2]
        ormas_lawan = [o['ormas'] for o in r['ormas_rinci'] if o['kedekatan'] < 0][:2]
        partai_lemah = [x['partai'] for x in r['partai_rinci'] if x['koalisi'] and x['mesin'] < .5]
        langkah = []
        def L(judul, rinci, angka=None, biaya=None):
            langkah.append(dict(langkah=judul, rinci=rinci, angka=angka, biaya=biaya))
        if r['tps_tanpa_saksi'] > 0:
            L(f"Isi {r['tps_tanpa_saksi']:.0f} TPS tanpa saksi",
              "Tanpa C-Hasil pembanding, selisih di TPS ini tidak bisa dibantah.",
              f"{r['tps_tanpa_saksi']*CFG['saksi_per_tps']:.0f} saksi",
              r['tps_tanpa_saksi'] * CFG['saksi_per_tps'] * CFG['honor_saksi'])
        if kat in ('MENANG AMAN', 'MENANG TIPIS'):
            L("Kunci kehadiran pemilih (bukan cari suara baru)",
              f"Suara sudah unggul {margin*100:.1f} poin; yang mahal adalah pendukung tidak datang. Bagi tugas per TPS: pengingat H-1 dan H-0, antar-jemput lansia.",
              f"target hadir {TURNOUT+0.04:.0%} (naik 4 poin = +{r['dpt']*0.04*0.97*sh:,.0f} suara)")
        if kat in ('IMBANG', 'KALAH TIPIS'):
            L(f"Rebut {aman:,.0f} suara lewat door-to-door terjadwal",
              f"Datangi {rumah:,.0f} rumah tangga; konversi dipakai {konversi:.0%} (dari data door-to-door wilayah ini), {pemilih_per_kk:.1f} pemilih per KK.",
              f"{relawan_butuh} relawan x {KUNJUNGAN_PER_RELAWAN_HARI} rumah/hari x {HARI_EFEKTIF} hari")
        if kat == 'KALAH':
            L("Jangan bakar uang di sini — tahan kekalahan, jangan diperbesar",
              f"Selisih {abs(margin)*100:.1f} poin terlalu lebar untuk dibalik dengan sisa waktu {HARI_EFEKTIF} hari. Cukup jaga saksi, pindahkan belanja ke wilayah IMBANG.",
              f"hemat sekitar {rp_singkat(r['anggaran_rencana'] - r['anggaran_realisasi'])}")
        if relawan_kurang > 0:
            L(f"Tambah {relawan_kurang} relawan aktif",
              f"Sekarang {r['relawan_aktif']:.0f} aktif; kebutuhan {relawan_butuh} untuk menyelesaikan kunjungan tepat waktu.",
              f"{relawan_kurang} orang")
        if ranting_kurang > 0 or anak_kurang > 0:
            L(f"Bentuk {ranting_kurang:.0f} ranting & {anak_kurang:.0f} anak ranting",
              f"Struktur koalisi baru {st['ranting_ada']:.0f}/{st['ranting_target']:.0f} ranting dan {st['anak_ada']:.0f}/{st['anak_target']:.0f} anak ranting. Satu anak ranting = satu TPS terjaga.",
              f"{st['kader']:,.0f} kader tersedia ({st['kader_per_1000']:.1f} per 1.000 DPT)")
        if partai_lemah:
            L(f"Konsolidasi {', '.join(partai_lemah)}",
              "Mesin partai koalisi di bawah 0,5: rapat struktur, target suara per ranting, lembar komitmen bertanda tangan.", None, 8_000_000)
        if ormas_lawan:
            L(f"Silaturahmi ke {', '.join(ormas_lawan)}",
              "Ormas ini condong ke lawan. Audiensi resmi, bawa program yang mereka minta, catat komitmen. Dilarang memakai uang atau menyentuh urusan keyakinan.", None, 5_000_000)
        elif ormas_besar:
            L(f"Kunci dukungan {', '.join(o['ormas'] for o in ormas_besar)}",
              f"Jangkauan {sum(o['anggota'] for o in ormas_besar):,.0f} anggota — minta pengurus jadi juru bicara program di wilayah ini.")
        if isu_top:
            L(f"Jawab isu '{isu_top}' dengan janji terukur",
              ("Isu bersentimen negatif ke kita: " + ', '.join(isu_negatif) + ". Siapkan bantahan berbasis data dan program konkret."
               if isu_negatif else "Isu ini paling banyak disebut — jadikan materi utama kampanye di wilayah ini."))
        hasil.append(dict(kode=r['kode'], nama=r['nama'], dapil=r['dapil'], zona=r['zona'], dpt=r['dpt'],
                          share=sh, lawan=NAMA_KAND.get(lw[0]), share_lawan=lw[1], margin=margin,
                          sd=sd, peluang=(p * 100 if p is not None else None), kategori=kat,
                          suara_kurang=kurang, suara_aman=aman, rumah_target=rumah, konversi=konversi,
                          relawan_butuh=relawan_butuh, relawan_kurang=relawan_kurang,
                          ranting_kurang=ranting_kurang, anak_kurang=anak_kurang,
                          tps_tanpa_saksi=r['tps_tanpa_saksi'], isu=isu_top, langkah=langkah,
                          biaya_langkah=sum(x['biaya'] or 0 for x in langkah)))
    hasil.sort(key=lambda x: (x['peluang'] if x['peluang'] is not None else 50))
    return hasil

def rp_singkat(v):
    v = v or 0
    return f"Rp {v/1e9:.1f} M" if v >= 1e9 else f"Rp {v/1e6:.0f} juta" if v >= 1e6 else f"Rp {v:,.0f}"

def jalur_kemenangan(strat):
    """Tiga jalur berbeda untuk menutup gap — masing-masing dengan hitungan sendiri."""
    jalur = []
    basis = [r for r in rows if r['zona'].startswith('BASIS')]
    naik = 0.04
    tambah = sum(r['dpt'] * naik * SAH * (r['share'][KITA] or 0) for r in basis)
    jalur.append(dict(nama='Jalur Kehadiran', ringkas=f"Naikkan kehadiran {naik:.0%} di {len(basis)} wilayah basis",
                      tambahan=tambah, biaya=tambah * (AG_DASAR * .6),
                      langkah=['Data pemilih per TPS dipegang koordinator TPS', 'Pengingat H-1 dan H-0 lewat jaringan ranting',
                               'Antar-jemput lansia & pemilih jauh', 'Saksi penuh supaya suara tidak bocor'],
                      kelayakan='tinggi — memakai pendukung yang sudah ada, biaya paling murah per suara'))
    garap = [r for r in rows if r['zona'].startswith('GARAP')]
    sw = CFG['swing_maksimal_per_program']
    tambah2 = sum(r['suara_sah_proyeksi'] * sw * (1 - (r['ikc'] or 0) / 100) for r in garap)
    rumah2 = sum(s['rumah_target'] for s in strat if s['kode'] in {r['kode'] for r in garap})
    jalur.append(dict(nama='Jalur Rebut Medan Tempur', ringkas=f"Swing sampai {sw:.0%} di {len(garap)} wilayah GARAP",
                      tambahan=tambah2, biaya=tambah2 * AG_DASAR * 1.8,
                      langkah=[f"Door-to-door {rumah2:,.0f} rumah tangga", 'Temu warga per dusun dengan program isu setempat',
                               'APK di titik ramai hasil pemetaan drone', 'Tokoh lokal jadi juru bicara'],
                      kelayakan='sedang — butuh relawan banyak dan waktu; biaya per suara paling mahal'))
    ranting_kurang = sum(s['ranting_kurang'] for s in strat)
    anak_kurang = sum(s['anak_kurang'] for s in strat)
    ormas_potensi = sum(max(0.0, r['ormas_lawan'] - r['ormas_jangkauan']) for r in rows) * .15
    tambah3 = ranting_kurang * SP['pemilih_per_ranting'] * TURNOUT * .03 + ormas_potensi
    jalur.append(dict(nama='Jalur Struktur & Ormas',
                      ringkas=f"Lengkapi {ranting_kurang:.0f} ranting + {anak_kurang:.0f} anak ranting, rebut ormas yang condong ke lawan",
                      tambahan=tambah3, biaya=ranting_kurang * 1_500_000 + 5_000_000 * len([r for r in rows if r['ormas_lawan'] > r['ormas_jangkauan']]),
                      langkah=[f"Bentuk {ranting_kurang:.0f} ranting (1 ranting per {SP['pemilih_per_ranting']:,} pemilih)",
                               f"Isi {anak_kurang:.0f} anak ranting supaya tiap TPS punya penanggung jawab",
                               'Audiensi pengurus ormas — program, bukan uang', 'Kader jadi saksi TPS sekaligus'],
                      kelayakan='tinggi jangka panjang — sekaligus menutup kekurangan saksi'))
    for j in jalur:
        j['rp_per_suara'] = (j['biaya'] / j['tambahan']) if j['tambahan'] else None
        j['cukup_sendiri'] = j['tambahan'] >= gap if gap > 0 else True
    gabungan = sum(j['tambahan'] for j in jalur)
    return dict(jalur=jalur, gabungan=gabungan, gap=gap, cukup=(gabungan >= gap if gap > 0 else True))

AG_DASAR = (sum(r['anggaran_realisasi'] for r in rows) / max(1.0, sum(r['proyeksi'][KITA] for r in rows)))
strategi_out = strategi_wilayah()
jalur_out = jalur_kemenangan(strategi_out)
papan_daerah = dict(
    menang=len([s for s in strategi_out if s['kategori'].startswith('MENANG')]),
    imbang=len([s for s in strategi_out if s['kategori'] == 'IMBANG']),
    kalah=len([s for s in strategi_out if s['kategori'].startswith('KALAH')]),
    dpt_menang=sum(s['dpt'] for s in strategi_out if s['kategori'].startswith('MENANG')),
    dpt_kalah=sum(s['dpt'] for s in strategi_out if s['kategori'].startswith('KALAH')),
    suara_kurang_total=sum(s['suara_kurang'] for s in strategi_out),
    rumah_total=sum(s['rumah_target'] for s in strategi_out),
    relawan_kurang_total=sum(s['relawan_kurang'] for s in strategi_out),
    biaya_total=sum(s['biaya_langkah'] for s in strategi_out))

# ---------- STRUKTUR PARTAI: agregat sampai ranting ----------
def struktur_agregat():
    ag = collections.defaultdict(lambda: collections.defaultdict(lambda: dict(unit=0, target=0, pengurus=0, kader=0)))
    for x in struktur:
        p, t = x['partai'], x['tingkat']
        d = ag[p][t]
        d['pengurus'] += num(x['pengurus']); d['kader'] += num(x['kader']); d['target'] += num(x['target_unit'])
        d['unit'] += (1 if str(x['terbentuk']).lower() in ('ya', 'true', '1') else num(x['terbentuk']))
    out = []
    for p, tk in ag.items():
        tot_t = sum(v['target'] for v in tk.values()); tot_u = sum(v['unit'] for v in tk.values())
        out.append(dict(partai=p, koalisi=(p in KOALISI), tingkat=[dict(tingkat=t, **v) for t, v in tk.items()],
                        pengurus=sum(v['pengurus'] for v in tk.values()), kader=sum(v['kader'] for v in tk.values()),
                        unit=tot_u, target=tot_t, kelengkapan=(tot_u / tot_t if tot_t else None)))
    out.sort(key=lambda x: (-x['koalisi'], -(x['kelengkapan'] or 0)))
    return out
struktur_out = struktur_agregat()

# ---------- ROLLUP ke tingkat analisis ----------
def rollup():
    kunci = CFG.get('tingkat_analisis', 'kecamatan')
    ag = collections.defaultdict(lambda: dict(dpt=0.0, tps=0.0, kita=0.0, sah=0.0, saksi=0.0, saksi_butuh=0.0, n=0))
    for r in rows:
        k = r.get(kunci) or r.get('kecamatan') or r['nama']
        d = ag[k]
        d['dpt'] += r['dpt']; d['tps'] += r['tps']; d['kita'] += r['proyeksi'][KITA]
        d['sah'] += r['suara_sah_proyeksi']; d['saksi'] += r['saksi_terisi'] * CFG['saksi_per_tps']
        d['saksi_butuh'] += r['saksi_butuh']; d['n'] += 1
    return dict(tingkat=kunci, baris=[dict(nama=k, **v, share=(v['kita'] / v['sah'] if v['sah'] else 0),
                                           cakupan_saksi=(v['saksi'] / v['saksi_butuh'] if v['saksi_butuh'] else 0))
                                      for k, v in sorted(ag.items(), key=lambda x: -x[1]['dpt'])])
rollup_out = rollup()

ontologi_out = bangun_ontologi()
risiko_out = bangun_risiko()


# ---------- BENCHMARK: nilai kesiapan + patokan internal antar wilayah ----------
def kuartil(v, q=.75):
    v = sorted(x for x in v if x is not None)
    if not v: return 0
    i = min(len(v) - 1, int(len(v) * q))
    return v[i]

def bangun_benchmark():
    kel_struktur = [ (r['struktur']['ranting_ada'] / r['struktur']['ranting_target'])
                     if r['struktur']['ranting_target'] else None for r in rows ]
    isu_pos = sum(max(0.0, i['sentimen']) * i['sebut'] for r in rows for i in r['isu'])
    isu_tot = sum(abs(i['sentimen']) * i['sebut'] for r in rows for i in r['isu']) or 1
    ormas_pro = sum(r['ormas_jangkauan'] for r in rows)
    ormas_kon = sum(r['ormas_lawan'] for r in rows) + ormas_pro or 1
    biaya_baik = kuartil([r['biaya_per_suara'] for r in rows if r['biaya_per_suara']], .25) or 1
    drone_selesai = len([m for m in misi if m['status'] == 'selesai']) / max(1, len(misi))
    pilar = [
        dict(pilar='Kelengkapan data', nilai=kelengkapan_rata, target=.85, bobot=.15,
             sumber='meta.kelengkapan_data', perbaikan='Isi survei & door-to-door di wilayah yang kosong.'),
        dict(pilar='Struktur partai sampai ranting',
             nilai=(sum(x for x in kel_struktur if x is not None) / max(1, len([x for x in kel_struktur if x is not None]))),
             target=.90, bobot=.15, sumber='struktur_partai.csv', perbaikan='Bentuk ranting & anak ranting yang belum ada.'),
        dict(pilar='Cakupan saksi TPS', nilai=saksi_out['cakupan'], target=.95, bobot=.20,
             sumber='saksi.csv', perbaikan='Rekrut & latih saksi mulai dari TPS basis.'),
        dict(pilar='Mesin darat (relawan)',
             nilai=(sum((r['mesin'] or 0) * r['dpt'] for r in rows) / DPT if DPT else 0), target=.80, bobot=.15,
             sumber='relawan.csv', perbaikan='Target 1 relawan aktif per 100 pemilih.'),
        dict(pilar='Dukungan ormas', nilai=(ormas_pro / ormas_kon), target=.60, bobot=.10,
             sumber='ormas.csv', perbaikan='Audiensi ke ormas yang condong ke lawan.'),
        dict(pilar='Sentimen isu', nilai=(isu_pos / isu_tot), target=.60, bobot=.10,
             sumber='isu.csv', perbaikan='Jawab isu negatif dengan program terukur.'),
        dict(pilar='Efisiensi anggaran',
             nilai=min(1.0, biaya_baik / (AG_DASAR or biaya_baik)), target=.80, bobot=.10,
             sumber='anggaran.csv', perbaikan='Geser belanja ke wilayah dengan biaya per suara terendah.'),
        dict(pilar='Pemetaan udara (drone)', nilai=drone_selesai, target=.70, bobot=.05,
             sumber='drone_misi.csv', perbaikan='Selesaikan misi pemetaan di wilayah GARAP.'),
    ]
    for x in pilar:
        x['skor'] = min(1.0, (x['nilai'] or 0) / x['target']) if x['target'] else 0
        x['status'] = 'baik' if x['skor'] >= .9 else 'cukup' if x['skor'] >= .7 else 'kurang'
    nilai_total = sum(x['skor'] * x['bobot'] for x in pilar) * 100
    huruf = 'A' if nilai_total >= 85 else 'B' if nilai_total >= 70 else 'C' if nilai_total >= 55 else 'D' if nilai_total >= 40 else 'E'
    # patokan internal antar wilayah (kuartil atas jadi standar)
    pat = dict(ikc=kuartil([r['ikc'] for r in rows]), saksi=kuartil([r['saksi_cakupan'] for r in rows]),
               dtd=kuartil([r['dtd_cakupan'] for r in rows]),
               struktur=kuartil([x for x in kel_struktur if x is not None]),
               biaya=biaya_baik)
    banding, potensi = [], 0.0
    for i, r in enumerate(rows):
        naik = max(0.0, (pat['ikc'] - (r['ikc'] or 0)) / 100) * CFG['swing_maksimal_per_program'] / max(1e-9, CFG['swing_maksimal_per_program'])
        tambah = r['suara_sah_proyeksi'] * min(CFG['swing_maksimal_per_program'], max(0.0, (pat['ikc'] - (r['ikc'] or 0)) / 100))
        potensi += tambah
        st = (kel_struktur[i] or 0)
        banding.append(dict(kode=r['kode'], nama=r['nama'], ikc=r['ikc'], gap_ikc=(pat['ikc'] - (r['ikc'] or 0)),
                            saksi=r['saksi_cakupan'], gap_saksi=(pat['saksi'] - r['saksi_cakupan']),
                            struktur=st, gap_struktur=(pat['struktur'] - st),
                            dtd=r['dtd_cakupan'], biaya=r['biaya_per_suara'],
                            potensi_suara=tambah,
                            setara_patokan=(r['ikc'] or 0) >= pat['ikc']))
    banding.sort(key=lambda x: -x['potensi_suara'])
    return dict(nilai=nilai_total, huruf=huruf, pilar=pilar, patokan=pat, banding=banding,
                potensi_jika_setara=potensi,
                catatan='Patokan diambil dari kuartil atas wilayah sendiri — standar yang sudah terbukti bisa dicapai tim ini, bukan angka impor.')

benchmark_out = bangun_benchmark()

# ---------- KESIMPULAN LENGKAP ----------
def bangun_kesimpulan():
    menang = (target_suara is not None and gap <= 0)
    wajib_menang = [s for s in strategi_out if s['kategori'].startswith('MENANG')][-5:]
    harus_rebut = [s for s in strategi_out if s['kategori'] in ('IMBANG', 'KALAH TIPIS')]
    lepas = [s for s in strategi_out if s['kategori'] == 'KALAH']
    terburuk = RISIKO_TERBURUK
    langkah_waktu = [
        dict(tahap='H-90 sampai H-60', fokus='Struktur & data',
             isi=[f"Bentuk {sum(s['ranting_kurang'] for s in strategi_out):.0f} ranting dan {sum(s['anak_kurang'] for s in strategi_out):.0f} anak ranting",
                  f"Tuntaskan pendataan door-to-door di {len([r for r in rows if (r['dtd_cakupan'] or 0) < .2])} wilayah yang cakupannya di bawah 20%",
                  f"Selesaikan {len([m for m in misi if m['status'] != 'selesai'])} misi pemetaan udara untuk mencocokkan rumah dengan DPT"]),
        dict(tahap='H-60 sampai H-30', fokus='Rebut & konsolidasi',
             isi=[f"Door-to-door {sum(s['rumah_target'] for s in harus_rebut):,.0f} rumah tangga di {len(harus_rebut)} daerah imbang/tipis",
                  f"Rekrut {sum(s['relawan_kurang'] for s in strategi_out):.0f} relawan tambahan",
                  "Audiensi ormas yang condong ke lawan; rapat struktur partai yang mesinnya di bawah 0,5"]),
        dict(tahap='H-30 sampai H-7', fokus='Kunci suara',
             isi=[f"Lengkapi {saksi_out['kurang']:,.0f} saksi ({rp_singkat(saksi_out['biaya_kurang'])})",
                  "Jawab isu negatif dengan program terukur, bukan bantahan kosong",
                  "Kampanye akbar hanya di daerah yang masih imbang"]),
        dict(tahap='H-7 sampai H-0', fokus='Kehadiran & pengamanan suara',
             isi=["Pengingat H-1 dan H-0 lewat jaringan ranting sampai anak ranting",
                  "Antar-jemput pemilih lansia dan pemilih jauh",
                  "Saksi masuk TPS dengan formulir C-Hasil; foto & kirim ke pusat data sebelum meninggalkan TPS"]),
    ]
    syarat_menang = [
        dict(syarat=f"Tambahan {max(0.0, gap):,.0f} suara bersih", tercapai=(gap <= 0),
             cara=f"Gabungan tiga jalur menghasilkan {jalur_out['gabungan']:,.0f} suara"),
        dict(syarat=f"Cakupan saksi minimal 95% (sekarang {saksi_out['cakupan']:.0%})",
             tercapai=(saksi_out['cakupan'] >= .95),
             cara=f"{saksi_out['kurang']:,.0f} saksi lagi = {rp_singkat(saksi_out['biaya_kurang'])}"),
        dict(syarat=f"Menang di daerah ber-DPT terbesar", tercapai=all(s['kategori'].startswith('MENANG') for s in sorted(strategi_out, key=lambda x: -x['dpt'])[:3]),
             cara='Tiga daerah terbesar menyumbang ' + f"{sum(s['dpt'] for s in sorted(strategi_out, key=lambda x: -x['dpt'])[:3])/DPT:.0%} DPT"),
        dict(syarat='Kelengkapan data di atas ambang', tercapai=(kelengkapan_rata >= CFG['batas_kelengkapan_data']),
             cara=f"sekarang {kelengkapan_rata:.0%}, ambang {CFG['batas_kelengkapan_data']:.0%}"),
    ] + [dict(syarat=y['nama'], tercapai=y['terpenuhi'], cara=y['nilai']) for y in aturan_info['syarat']]
    sebab_kalah = [
        dict(sebab=terburuk['nama'], dampak=f"{terburuk['selisih_suara']:,.0f} suara", jaga=terburuk['ket']),
        dict(sebab='Saksi tidak lengkap', dampak=f"-{saksi_out['suara_beresiko']:,.0f} suara",
             jaga=f"{saksi_out['tps_rawan_tanpa_saksi']:,.0f} TPS rawan tanpa saksi"),
        dict(sebab='Anomali data dipakai mentah', dampak=f"{len(ontologi_out['anomali'])} temuan belum diverifikasi",
             jaga='Selesaikan verifikasi sebelum menggeser anggaran'),
        dict(sebab='Konsentrasi wilayah', dampak=f"HHI {risiko_out['hhi']:.3f} = {risiko_out['wilayah_efektif']:.1f} wilayah efektif",
             jaga='Kalau satu wilayah besar goyah, tidak ada penyangga'),
    ]
    pantau = [
        dict(indikator='Cakupan saksi', sekarang=f"{saksi_out['cakupan']:.0%}", target='95%', sumber='saksi.csv'),
        dict(indikator='Ranting terbentuk',
             sekarang=f"{sum(r['struktur']['ranting_ada'] for r in rows):.0f}/{sum(r['struktur']['ranting_target'] for r in rows):.0f}",
             target='100%', sumber='struktur_partai.csv'),
        dict(indikator='Cakupan door-to-door',
             sekarang=f"{sum((r['dtd_cakupan'] or 0) * r['dpt'] for r in rows)/DPT:.0%}", target='30%', sumber='dtd.csv'),
        dict(indikator='Selisih survei ke lawan', sekarang=f"{margin_share*100:+.1f} poin",
             target=f"+{CFG['margin_aman']*100:.0f} poin", sumber='survei.csv'),
        dict(indikator='Nilai benchmark kesiapan', sekarang=f"{benchmark_out['nilai']:.0f} ({benchmark_out['huruf']})",
             target='85 (A)', sumber='benchmark'),
    ]
    return dict(
        vonis=('MENANG pada proyeksi sekarang' if menang else 'KALAH pada proyeksi sekarang' if target_suara is not None
               else 'MODE PENUNJUKAN — tidak ada proyeksi suara'),
        margin=margin_share * 100, peluang=(peluang * 100 if peluang is not None else None),
        aturan=aturan_info, gap=gap, suara_kita=tot_proy[KITA], target=target_suara,
        cara_menang=jalur_out['jalur'], gabungan_jalur=jalur_out['gabungan'],
        wajib_dipertahankan=wajib_menang, harus_direbut=harus_rebut, jangan_dibakar_uang=lepas,
        kebutuhan=dict(relawan=sum(s['relawan_kurang'] for s in strategi_out),
                       rumah=sum(s['rumah_target'] for s in strategi_out),
                       saksi=saksi_out['kurang'], ranting=sum(s['ranting_kurang'] for s in strategi_out),
                       anak_ranting=sum(s['anak_kurang'] for s in strategi_out),
                       biaya=sum(s['biaya_langkah'] for s in strategi_out) + saksi_out['biaya_kurang']),
        jadwal=langkah_waktu, syarat_menang=syarat_menang, sebab_kalah=sebab_kalah, pantau=pantau,
        benchmark=dict(nilai=benchmark_out['nilai'], huruf=benchmark_out['huruf'],
                       potensi=benchmark_out['potensi_jika_setara']),
        catatan_kejujuran=PERINGATAN)

RISIKO_TERBURUK = min(risiko_out['uji_tekanan'], key=lambda x: x['selisih_suara'])
kesimpulan_out = bangun_kesimpulan()


# ---------- RIWAYAT PEMENANGAN & DINASTI ----------
def bangun_riwayat():
    jenis_kini = CFG['jenis_pemilihan']
    nama_kand = {k['nama'] for k in kandidat}
    rw = [r for r in riwayat if (r.get('jenis') or '').strip() == jenis_kini]
    if not rw:
        rw = [r for r in riwayat if r.get('pemenang') in nama_kand or r.get('lawan_utama') in nama_kand]
    if not rw:
        rw = riwayat
    rw = sorted(rw, key=lambda x: num(x.get('tahun')))
    pemilu = []
    for r in rw:
        pemilu.append(dict(tahun=int(num(r.get('tahun'))), jenis=r.get('jenis'), wilayah=r.get('wilayah'),
                           pemenang=r.get('pemenang'), nomor=r.get('nomor'), partai=r.get('partai_pengusung'),
                           suara=num(r.get('suara')), persen=num(r.get('persen')), turnout=num(r.get('turnout')),
                           lawan=r.get('lawan_utama'), suara_lawan=num(r.get('suara_lawan')),
                           selisih=num(r.get('selisih_persen')),
                           petahana_ikut=(str(r.get('petahana_ikut','')).strip().lower() == 'ya'),
                           hasil_petahana=r.get('hasil_petahana'), catatan=r.get('catatan')))
    ikut = [p for p in pemilu if p['petahana_ikut']]
    menang_ikut = [p for p in ikut if (p['hasil_petahana'] or '').lower() == 'menang']
    keunggulan = (sum(p['selisih'] for p in ikut) / len(ikut)) if ikut else None
    tanpa = [p for p in pemilu if not p['petahana_ikut'] and p['selisih']]
    keunggulan_tanpa = (sum(p['selisih'] for p in tanpa) / len(tanpa)) if tanpa else None

    # dinasti: siapa berhubungan dengan siapa
    simpul, sisi = [], []
    for d in dinasti:
        simpul.append(dict(nama=d.get('nama'), peran=d.get('peran'), jabatan=d.get('jabatan'),
                           periode=d.get('periode'), partai=d.get('partai'),
                           menjabat=(str(d.get('masih_menjabat','')).strip().lower() == 'ya'),
                           catatan=d.get('catatan'), hubungan=d.get('jenis_hubungan'),
                           dengan=d.get('hubungan_dengan')))
        if d.get('hubungan_dengan') and d.get('hubungan_dengan') != '-':
            sisi.append(dict(dari=d.get('nama'), ke=d.get('hubungan_dengan'), jenis=d.get('jenis_hubungan')))
    keluarga = [x for x in simpul if x['dengan'] and x['dengan'] != '-'] 
    jabatan_dikuasai = [x for x in simpul if x['menjabat'] and (x['peran'] or '').startswith(('petahana', 'keluarga'))]

    def hitung_periode(teks):
        return len([b for b in str(teks or '').split('&') if b.strip()])
    petahana = next((k for k in kandidat if str(k.get('petahana', '')).strip().lower() in ('ya', 'y', 'true', '1')), None)
    pet_nama = petahana['nama'] if petahana else None
    pet_simpul = next((x for x in simpul if x['nama'] == pet_nama), None)
    periode_pet = hitung_periode(pet_simpul['periode']) if pet_simpul else len([p for p in pemilu if p['pemenang'] == pet_nama])
    BATAS_PERIODE = {'presiden': 2, 'gubernur': 2, 'bupati': 2, 'walikota': 2, 'kepala_desa': 3}
    batas = BATAS_PERIODE.get(CFG['jenis_pemilihan'])
    boleh_maju = (periode_pet < batas) if batas else True
    tahun_kuasa = None
    tahun_semua = [p['tahun'] for p in pemilu if p['pemenang'] in {x['nama'] for x in simpul if (x['peran'] or '').startswith(('petahana','tokoh','keluarga'))}]
    if tahun_semua:
        tahun_kuasa = int(datetime.date.fromisoformat(CFG['tanggal_pemungutan']).year - min(tahun_semua))
    # pergeseran: hasil terakhir vs proyeksi sekarang
    seuai = [p for p in pemilu if p['pemenang'] in nama_kand or p['lawan'] in nama_kand] or pemilu
    terakhir = seuai[-1] if seuai else None
    geser = []
    if terakhir:
        sah_lalu = (terakhir['suara'] / (terakhir['persen'] / 100)) if terakhir['persen'] else None
        for k in kandidat:
            kini = share_tot.get(k['nomor'], 0) * 100
            lalu = None
            if k['nama'] == terakhir['pemenang']:
                lalu = terakhir['persen']
            elif k['nama'] == terakhir['lawan'] and sah_lalu:
                lalu = terakhir['suara_lawan'] / sah_lalu * 100
            elif (k.get('partai_utama') or '') and (k.get('partai_utama') or '') == (terakhir['partai'] or '').split('+')[0]:
                lalu = terakhir['persen']
            geser.append(dict(nama=k['nama'], nomor=k['nomor'], tahun_lalu=terakhir['tahun'], lalu=lalu, kini=kini,
                              selisih=(kini - lalu) if lalu is not None else None,
                              catatan=('tidak ikut / tidak tercatat pada ' + str(terakhir['tahun'])) if lalu is None else None))
    catatan = []
    if batas and periode_pet >= batas:
        catatan.append(f"Petahana sudah {periode_pet} periode — untuk jabatan yang sama tidak bisa maju lagi. Peluang terbesar justru muncul dari kursi yang kosong; siapkan menghadapi calon estafet (kerabat/orang dekat), bukan menghadapi petahana.")
    elif batas:
        catatan.append(f"Petahana baru {periode_pet} periode dan masih boleh maju satu kali lagi.")
    if keunggulan is not None:
        catatan.append(f"Dari {len(ikut)} pemilu yang diikuti petahana, {len(menang_ikut)} dimenangkan dengan rata-rata selisih {keunggulan:.1f} poin" + (f"; tanpa petahana rata-rata selisih hanya {keunggulan_tanpa:.1f} poin." if keunggulan_tanpa is not None else "."))
    if len(keluarga) >= 2:
        catatan.append(f"Terindikasi jaringan keluarga: {len(keluarga)} nama terhubung ke petahana/tokoh lama" + (f", berkuasa sekitar {tahun_kuasa} tahun" if tahun_kuasa else "") + f", menguasai {len(jabatan_dikuasai)} jabatan yang masih berjalan. Lawan sesungguhnya adalah jaringan ini, bukan satu orang.")
    return dict(pemilu=pemilu, keunggulan_petahana=keunggulan, keunggulan_tanpa_petahana=keunggulan_tanpa,
                menang_saat_ikut=len(menang_ikut), ikut=len(ikut),
                petahana=dict(nama=pet_nama, periode=periode_pet, batas=batas, boleh_maju=boleh_maju,
                              jabatan=(pet_simpul or {}).get('jabatan'), periode_teks=(pet_simpul or {}).get('periode')),
                dinasti=dict(simpul=simpul, sisi=sisi, anggota_keluarga=len(keluarga),
                             jabatan_dikuasai=[x['nama'] + ' — ' + (x['jabatan'] or '') for x in jabatan_dikuasai],
                             tahun_berkuasa=tahun_kuasa),
                pergeseran=geser, catatan=catatan)

riwayat_out = bangun_riwayat()
for _c in riwayat_out['catatan'][:1]:
    PERINGATAN.append('Riwayat: ' + _c)

out = dict(
    meta=dict(dibuat=datetime.datetime.now().isoformat(timespec='seconds'),
              sumber_data=CFG['sumber_data'], wilayah_kerja=CFG['wilayah_kerja'],
              jenis=CFG['jenis_pemilihan'], hari_menuju=(
                  (datetime.date.fromisoformat(CFG['tanggal_pemungutan']) - datetime.date.today()).days),
              tanggal_pemungutan=CFG['tanggal_pemungutan'],
              kelengkapan_data=kelengkapan_rata, peringatan=PERINGATAN, versi="1.0"),
    konfigurasi=CFG,
    kandidat=[dict(k, proyeksi=tot_proy.get(k['nomor'], 0), persen=share_tot.get(k['nomor'], 0) * 100,
                   petahana=(str(k.get('petahana', '')).strip().lower() in ('ya', 'y', 'true', '1')),
                   wilayah_terkuat=sorted([dict(nama=r['nama'], suara=r['proyeksi'].get(k['nomor'], 0),
                                                share=r['share'].get(k['nomor']) or 0)
                                           for r in rows], key=lambda x: -x['suara'])[:5])
              for k in kandidat],
    ringkas=dict(dpt=DPT, tps=TPS, suara_sah_proyeksi=SUARA_SAH, turnout=TURNOUT,
                 proyeksi_kita=tot_proy[KITA], persen_kita=share_tot[KITA] * 100,
                 lawan_terkuat=NAMA_KAND.get(lawan_terkuat), lawan_terkuat_suara=tot_proy.get(lawan_terkuat, 0),
                 target=target_suara, gap=gap, margin_share=margin_share * 100,
                 peluang_menang=(peluang * 100 if peluang is not None else None),
                 sd_total=sd_total * 100, kalibrasi_k=k_kal, n_sampel_total=n_efektif,
                 median_ikc=med_ikc),
    wilayah=rows, kursi=kursi_out, drone=drone_out, saksi=saksi_out, isu=isu_out,
    ontologi=ontologi_out, risiko=risiko_out, aturan=aturan_info, strategi=strategi_out,
    benchmark=benchmark_out, kesimpulan=kesimpulan_out, riwayat=riwayat_out,
    jalur=jalur_out, papan_daerah=papan_daerah, struktur=struktur_out, rollup=rollup_out,
    anggaran=dict(rencana=sum(r['anggaran_rencana'] for r in rows),
                  realisasi=sum(r['anggaran_realisasi'] for r in rows),
                  biaya_per_suara=biaya_dasar,
                  gap_tertutup=gap_tertutup, biaya_menutup_gap=kum_biaya,
                  suara_didapat=kum_suara, rencana_alokasi=rencana),
)
os.makedirs(os.path.join(BASE, 'web'), exist_ok=True)
with open(os.path.join(BASE, 'web', 'data.json'), 'w') as f:
    json.dump(out, f, ensure_ascii=False, separators=(',', ':'), default=float)
ledger.catat('hitung', f"proyeksi {tot_proy[KITA]:,.0f} ({share_tot[KITA]*100:.1f}%), gap {gap:,.0f}",
             dict(jenis=CFG['jenis_pemilihan'], dpt=DPT, proyeksi=tot_proy[KITA], target=target_suara, gap=gap,
                  peluang=(peluang * 100 if peluang else None), benchmark=benchmark_out['nilai'],
                  anomali=len(ontologi_out['anomali']), var95=risiko_out['var95'],
                  sumber_data=CFG['sumber_data']))
print(f"OK  DPT {DPT:,.0f} | TPS {TPS:,.0f} | proyeksi {tot_proy[KITA]:,.0f} ({share_tot[KITA]*100:.1f}%) "
      f"| target {format(target_suara, ',.0f') if target_suara is not None else 'tidak berlaku (penunjukan)'} "
      f"| gap {gap:,.0f} | peluang {('%.0f%%' % (peluang * 100)) if peluang else 'n/a'}")
print(f"    drone: GSD {gsd:.2f} cm/px, {luas_per_sortie_ha:.0f} ha/sortie, {sortie} sortie, {drone_out['hari']} hari")
for p in PERINGATAN: print("  ! " + p[:150])
