# Ocklu Pemetaan Pemilih — Command Center

Dasbor konsultan pemilu: pemetaan kekuatan calon per wilayah, sistem drone, dan mesin keputusan pemenangan.
**Berdiri sendiri**: Python 3 bawaan (tanpa pustaka luar) + satu berkas HTML. Tanpa internet, tanpa basis data, tanpa akun.

![tab](https://img.shields.io/badge/tab-25-38bdf8) ![python](https://img.shields.io/badge/python-3.9%2B-22c55e) ![tanpa%20dependensi](https://img.shields.io/badge/dependensi-0-a78bfa)

## Jalankan

```bash
git clone https://github.com/hillkia/ocklu-pemetaan-pemilih.git
cd ocklu-pemetaan-pemilih
python3 server.py 4488
```

Buka http://127.0.0.1:4488/ — atau klik dua kali **Buka Ocklu Pemilu.command** (macOS).

## Isi

| Bagian | Yang dikerjakan |
|---|---|
| **Peta & wilayah** | IKC (indeks kekuatan calon) per wilayah, zona BASIS/GARAP/AMANKAN/EFISIENSI, peta kanvas tanpa peta daring |
| **Target & Gap** | Target menang sesuai aturan pemilihan, surplus/defisit per wilayah, rencana penutup gap termurah lebih dulu |
| **Saran Menang** | Vonis menang/kalah per daerah + langkah bernomor + tiga jalur kemenangan berikut biayanya |
| **Calon & Petahana** | Bio lengkap tiap calon, penanda petahana, peta perebutan per wilayah |
| **Riwayat & Dinasti** | Riwayat pemilihan sebelumnya, periode petahana vs batas, keunggulan petahana, peta kekerabatan |
| **Kekuatan Partai / Ormas** | Mesin partai per wilayah, struktur DPC→PAC→Ranting→Anak ranting, jangkauan ormas pro/kontra |
| **Kursi (Sainte-Laguë)** | Alokasi kursi per dapil, harga kursi, ambang internal caleg |
| **Sistem Drone** | Fotogrametri sungguhan (GSD, swath, sidelap, endurance) → sortie, jam terbang, biaya; peta bergerak + jaringan relay |
| **Saksi TPS** | Kebutuhan, cakupan, TPS rawan, suara berisiko |
| **Risiko (Aladdin)** | Model faktor, VaR 95%, HHI, kontribusi risiko per wilayah, 7 uji tekanan |
| **Ontologi (Palantir)** | 14 silo data disatukan jadi objek + hubungan + anomali lintas silo + resolusi wilayah ganda |
| **Worker AI** | Perintah kerja berperingkat, gerbang DNA, otak Neutron, daur tugas AGI, pemburu data, MYTHOS |
| **Keputusan & Pemicu** | 14 pemicu berambang → keputusan dengan penanggung jawab & tenggat |
| **Benchmark** | Nilai kesiapan 0–100 atas 8 pilar; patokan dari kuartil atas wilayah sendiri |
| **Ledger** | Buku besar berantai SHA-256 untuk setiap hitungan, perubahan data, pemicu, dan keputusan |
| **Kesimpulan** | Satu halaman siap cetak: vonis, syarat menang, sebab kalah, kebutuhan, jadwal H-90→H-0 |
| **Input Data** | Semua tabel bisa diklik & diubah; impor CSV dengan seret berkas, tempel, atau folder pantauan |

## Ganti jenis pemilihan

Dropdown di kepala dasbor — aturan kemenangannya ikut berganti sendiri:
Presiden (>50% + sebaran ≥20% di lebih dari separuh provinsi) · DPR RI / DPRD I / DPRD II (Sainte-Laguë + harga kursi, ambang 4% khusus DPR RI) · Gubernur / Bupati / Wali Kota / Kepala Desa / RT-RW (suara terbanyak) · Camat & Lurah (bukan pemilihan — dasbor beralih ke mode peta dukungan dan mematikan proyeksi suara).

## Ganti data

Seluruh isi `data/*.csv` adalah **data contoh yang dihasilkan `benih.py` secara deterministik**, bukan data nyata.
Selama `konfigurasi.json → sumber_data` masih `"contoh"`, seluruh dasbor bertanda **DATA SIMULASI**.

Ganti dengan data resmi (DPT KPU, rekap pemilu sebelumnya, survei berlisensi), lalu setel `sumber_data: "resmi"`.
Rincian kolom tiap berkas ada di [PANDUAN.md](PANDUAN.md).

## Pagar yang sengaja dipasang

- Komponen yang datanya kosong **tidak ditebak** — bobotnya dinormalkan ulang dan kelengkapan datanya ditampilkan.
- Peluang menang **mati sendiri** bila kelengkapan data di bawah ambang.
- Worker AI gagal-tertutup: kalau otak AI mati, dikatakan mati — narasi tidak dikarang. Otak Neutron (deterministik) tetap jalan.
- Gerbang DNA membuang perintah yang tidak menunjuk angka, yang biayanya di atas ambang, atau yang menyentuh politik uang, SARA, intimidasi, dan data pribadi pemilih.
- Perencanaan drone hanya menghitung teknis; izin ruang udara tetap urusan operator.
- Bekerja pada data agregat wilayah. **Jangan memasukkan NIK, alamat, atau nomor telepon pemilih** (UU PDP).

## Otak worker (opsional)

Urutan: **Neutron (deterministik, selalu hidup) → Groq → Gemini → Ollama**.
Kunci API dibaca dari `~/shamar/.env`, `.env` di folder proyek, atau lingkungan proses (`GROQ_API_KEY`, `GEMINI_API_KEY`).
Tanpa kunci pun dasbor tetap berjalan penuh — hanya narasi rapat pagi yang tidak ditulis.

## Struktur

```
mesin.py      hitungan (semua angka dasbor keluar dari sini)
worker.py     perintah kerja + gerbang DNA + Neutron + AGI + MYTHOS
ledger.py     buku besar berantai
server.py     server lokal + API input data + pengawas folder
benih.py      pembuat data contoh
konfigurasi.json  seluruh angka pengendali    dna.json  11 aturan    pemicu.json  14 pemicu
web/          dasbor satu halaman
data/         berkas CSV yang diganti dengan data resmi
```

## Lisensi

Hak cipta pemilik proyek. Dipakai untuk konsultasi pemenangan pemilu; wajib tunduk pada UU Pemilu, UU Pilkada, dan UU PDP.
