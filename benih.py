#!/usr/bin/env python3
"""Benih data CONTOH untuk Ocklu Pemetaan Pemilih.
Angka dihasilkan deterministik (LCG ber-seed), BUKAN diketik tangan, dan
seluruhnya ditandai sebagai simulasi. Ganti dengan data resmi sebelum dipakai."""
import csv, json, math, os

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, 'data')
os.makedirs(D, exist_ok=True)
CFG = json.load(open(os.path.join(BASE, 'konfigurasi.json')))

class R:
    def __init__(s, seed): s.x = seed
    def n(s):
        s.x = (1103515245 * s.x + 12345) % (2 ** 31)
        return s.x / (2 ** 31)
    def i(s, a, b): return a + int(s.n() * (b - a + 1))
    def f(s, a, b): return a + s.n() * (b - a)

r = R(20291127)

# nama kapanewon nyata; koordinat = perkiraan pusat kapanewon (ganti dgn shapefile BIG/KPU)
KEC = [
    ("3404010", "Moyudan",     -7.770, 110.253, 27.6,  "Dapil 5"),
    ("3404020", "Minggir",     -7.733, 110.242, 27.3,  "Dapil 5"),
    ("3404030", "Seyegan",     -7.712, 110.283, 26.6,  "Dapil 5"),
    ("3404040", "Godean",      -7.766, 110.292, 26.8,  "Dapil 5"),
    ("3404050", "Gamping",     -7.792, 110.322, 29.3,  "Dapil 4"),
    ("3404060", "Mlati",       -7.740, 110.345, 28.5,  "Dapil 4"),
    ("3404070", "Depok",       -7.762, 110.400, 35.5,  "Dapil 1"),
    ("3404080", "Berbah",      -7.803, 110.442, 23.0,  "Dapil 2"),
    ("3404090", "Prambanan",   -7.762, 110.492, 41.4,  "Dapil 2"),
    ("3404100", "Kalasan",     -7.762, 110.462, 35.8,  "Dapil 2"),
    ("3404110", "Ngemplak",    -7.712, 110.432, 35.7,  "Dapil 3"),
    ("3404120", "Ngaglik",     -7.712, 110.392, 38.5,  "Dapil 1"),
    ("3404130", "Sleman",      -7.700, 110.332, 31.3,  "Dapil 4"),
    ("3404140", "Tempel",      -7.663, 110.303, 32.5,  "Dapil 5"),
    ("3404150", "Turi",        -7.622, 110.342, 43.1,  "Dapil 3"),
    ("3404160", "Pakem",       -7.652, 110.402, 43.8,  "Dapil 3"),
    ("3404170", "Cangkringan", -7.633, 110.452, 47.9,  "Dapil 3"),
]
PARTAI = ["PDIP","GERINDRA","GOLKAR","PKB","PKS","NASDEM","DEMOKRAT","PAN","PPP","PSI"]
BOBOT_NASIONAL = [0.20,0.16,0.13,0.12,0.10,0.08,0.07,0.06,0.04,0.04]
MAKS_TPS = CFG["maks_pemilih_per_tps"]

# 1. wilayah
w_rows = []
for kode, nama, lat, lon, luas, dapil in KEC:
    dpt = int(r.f(18000, 92000))
    kk = int(dpt / r.f(2.7, 3.4))
    tps = math.ceil(dpt / MAKS_TPS)
    urban = round(min(1.0, dpt / luas / 2200), 3)
    w_rows.append(dict(kode=kode, provinsi="DI Yogyakarta", kabupaten="Sleman", kecamatan=nama,
                       desa="", dapil=dapil, dpt=dpt, kk=kk, tps=tps, lat=lat, lon=lon,
                       luas_km2=luas, indeks_urban=urban))
with open(f"{D}/wilayah.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(w_rows[0].keys())); wr.writeheader(); wr.writerows(w_rows)

# 2. hasil pemilu lalu (suara sah per partai per wilayah)
with open(f"{D}/hasil_lalu.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","tahun","partai","suara"])
    for w in w_rows:
        sah = int(w["dpt"] * r.f(0.70, 0.82) * 0.97)
        goyang = [max(0.01, b * r.f(0.55, 1.55)) for b in BOBOT_NASIONAL]
        tot = sum(goyang)
        sisa = sah
        for i, p in enumerate(PARTAI):
            v = int(sah * goyang[i] / tot) if i < len(PARTAI) - 1 else sisa
            sisa -= v
            wr.writerow([w["kode"], 2024, p, v])

# 3. survei berbasis wilayah (hanya sebagian wilayah punya sampel -> realistis)
with open(f"{D}/survei.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","tanggal","lembaga","n_sampel","kandidat","responden_dukung"])
    for idx, w in enumerate(w_rows):
        if idx % 17 in (3, 7, 11):  # 3 wilayah tanpa survei
            continue
        n = r.i(120, 420)
        p1 = r.f(0.26, 0.47); p2 = r.f(0.22, 0.40)
        p3 = max(0.03, min(0.25, 1 - p1 - p2 - r.f(0.05, 0.14)))
        for kand, p in (("01", p1), ("02", p2), ("03", p3)):
            wr.writerow([w["kode"], "2029-06-15", "Contoh Riset", n, kand, int(round(n * p))])

# 4. door to door (pendataan tim)
with open(f"{D}/dtd.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","tanggal","terdata","mendukung","ragu","menolak"])
    for w in w_rows:
        terdata = int(w["dpt"] * r.f(0.04, 0.31))
        mend = int(terdata * r.f(0.28, 0.58)); ragu = int(terdata * r.f(0.15, 0.34))
        wr.writerow([w["kode"], "2029-07-01", terdata, mend, ragu, terdata - mend - ragu])

# 5. relawan / mesin darat
with open(f"{D}/relawan.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","tim","jumlah","aktif_30hari"])
    for w in w_rows:
        for tim in ("Korcam", "Kordes", "Relawan"):
            j = {"Korcam": r.i(2, 6), "Kordes": r.i(8, 30), "Relawan": r.i(40, 420)}[tim]
            wr.writerow([w["kode"], tim, j, int(j * r.f(0.45, 0.95))])

# 6. saksi TPS
with open(f"{D}/saksi.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","tps_terisi_saksi","saksi_terlatih"])
    for w in w_rows:
        terisi = int(w["tps"] * r.f(0.35, 0.98))
        wr.writerow([w["kode"], terisi, int(terisi * r.f(0.4, 0.9))])

# 7. isu lokal
ISU = ["Air bersih","Jalan rusak","Lapangan kerja","Harga pupuk","Sampah","Banjir/lahar",
       "Pendidikan gratis","Kesehatan","Bantuan UMKM","Sengketa tanah"]
with open(f"{D}/isu.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","isu","penyebutan","sentimen_ke_kita"])
    for w in w_rows:
        for k in range(3):
            isu = ISU[(int(w["kode"][-3:]) // 10 + k * 3) % len(ISU)]
            wr.writerow([w["kode"], isu, r.i(15, 240), round(r.f(-0.6, 0.7), 2)])

# 8. anggaran
POS = ["APK & baliho","Konsolidasi tim","Saksi","Logistik kampanye","Media & digital","Program sosial"]
with open(f"{D}/anggaran.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","pos","rencana","realisasi"])
    for w in w_rows:
        for pos in POS:
            ren = int(w["dpt"] * r.f(180, 1200) / 1000) * 1000
            wr.writerow([w["kode"], pos, ren, int(ren * r.f(0.1, 0.85) / 1000) * 1000])

# 9. kandidat & caleg (untuk mode DPRD / Sainte-Lague)
with open(f"{D}/kandidat.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["nomor","nama","partai_utama","koalisi","status"])
    wr.writerow(["01","Calon A (contoh)","PDIP","PDIP|PKB|PSI","kita"])
    wr.writerow(["02","Calon B (contoh)","GERINDRA","GERINDRA|GOLKAR|PAN","lawan"])
    wr.writerow(["03","Calon C (contoh)","PKS","PKS|NASDEM|DEMOKRAT|PPP","lawan"])
with open(f"{D}/caleg.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["dapil","partai","nama","nomor_urut","suara_pribadi","status"])
    for dp in CFG["kursi_dapil"]:
        for p in PARTAI:
            for u in range(1, 5):
                nm = f"Caleg {p}-{dp[-1]}-{u} (contoh)"
                st = "kita" if (p == "PDIP" and u == 1) else "lain"
                wr.writerow([dp, p, nm, u, r.i(300, 9000), st])

# 10. misi drone (wilayah yang mau dipetakan udara)
with open(f"{D}/drone_misi.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","tujuan","luas_target_km2","status","catatan"])
    for w in w_rows:
        tuj = ["Validasi sebaran rumah vs DPT","Titik keramaian & rute kampanye",
               "Survei lokasi APK/baliho","Pemetaan akses jalan tim"][int(w["kode"][-3:]) // 10 % 4]
        wr.writerow([w["kode"], tuj, round(w["luas_km2"] * r.f(0.25, 0.8), 1),
                     ["rencana","terbang","selesai"][int(w["kode"][-3:]) // 10 % 3], ""])
print("Benih CONTOH ditulis ke", D)

# 11. kekuatan partai per wilayah (mesin partai koalisi & lawan)
with open(f"{D}/partai.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","partai","pengurus_aktif","saksi_disiapkan","mesin_skor","dukungan_ke_kita"])
    for w in w_rows:
        for p in PARTAI:
            wr.writerow([w["kode"], p, r.i(5, 90), r.i(0, w["tps"]), round(r.f(0.15, 0.95), 2), round(r.f(0.0, 1.0), 2)])

# 12. kekuatan ormas per wilayah
ORMAS = ["NU","Muhammadiyah","Ormas Pemuda","Ormas Tani","Ormas Nelayan","Ormas Perempuan","Paguyuban Warga","Ormas Keagamaan Lain"]
with open(f"{D}/ormas.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["kode_wilayah","ormas","anggota","pengurus","kedekatan","pengaruh"])
    for w in w_rows:
        for o in ORMAS:
            if r.n() < 0.25: continue
            wr.writerow([w["kode"], o, int(w["dpt"] * r.f(0.005, 0.09)), r.i(3, 60),
                         round(r.f(-0.5, 0.95), 2), round(r.f(0.2, 1.0), 2)])
print("Benih partai & ormas ditulis.")
