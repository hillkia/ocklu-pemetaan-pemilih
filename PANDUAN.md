# Ocklu Pemetaan Pemilih — Command Center

Dasbor pemetaan pemilih + sistem drone untuk pemenangan pilkada / DPR / DPRD.
Berdiri sendiri (standalone): tanpa internet, tanpa API, tanpa basis data. Hanya Python 3 bawaan macOS.

## Jalankan
Klik dua kali **Buka Ocklu Pemilu.command**, atau:
```bash
cd ~/ocklu-pemilu && python3 server.py 4488
```
Buka http://127.0.0.1:4488/

## Alur kerja
1. Ganti isi `data/*.csv` dengan data resmi.
2. Ubah `konfigurasi.json` (koalisi pengusung, tanggal coblosan, bobot, parameter drone, honor saksi).
3. `python3 mesin.py` → menulis `web/data.json`. Muat ulang dasbor.
   (server juga menghitung ulang tiap kali dijalankan; endpoint `/api/hitung` menghitung tanpa restart)

## Input data
**Manual** — tab *Input Data* → klik tabel mana pun → grid isian → Simpan. Atau klik nama daerah di mana saja (peta, tabel, laporan): terbuka jendela wilayah berisi profil (nama, DPT, TPS, koordinat, dapil) plus 10 sub-tabel terkait wilayah itu — survei, door-to-door, saksi, relawan, isu, anggaran, hasil lalu, partai, ormas, drone.
**Otomatis** —
1. Seret berkas CSV ke kotak di tab Input Data, atau
2. taruh CSV di `data/masuk/` — pengawas server memeriksa tiap 5 detik, mencocokkan kolom dengan tabel tujuan, mengimpor, mengarsipkan ke `data/masuk/selesai/`, lalu menghitung ulang sendiri. Kolom yang namanya beda bisa dipetakan lewat "Pratinjau & petakan kolom".
Setiap simpan/impor: cadangan versi lama ke `data/cadangan/` → tulis CSV → `mesin.py` → `worker.py` → dasbor menghitung ulang. Riwayatnya ada di `data/log_impor.json`.

## Berkas data (ganti dengan data resmi)
| Berkas | Isi | Sumber resmi |
|---|---|---|
| `wilayah.csv` | kode, kecamatan, desa, dapil, dpt, kk, tps, lat, lon, luas_km2, indeks_urban | DPT KPU + peta BIG |
| `hasil_lalu.csv` | kode_wilayah, tahun, partai, suara | Rekap KPU pemilu sebelumnya |
| `survei.csv` | kode_wilayah, tanggal, lembaga, n_sampel, kandidat, responden_dukung | Lembaga survei |
| `dtd.csv` | terdata, mendukung, ragu, menolak | Pendataan door-to-door tim |
| `relawan.csv` | tim, jumlah, aktif_30hari | Struktur tim |
| `saksi.csv` | tps_terisi_saksi, saksi_terlatih | Koordinator saksi |
| `isu.csv` | isu, penyebutan, sentimen_ke_kita (−1..1) | FGD / monitoring |
| `anggaran.csv` | pos, rencana, realisasi | Bendahara |
| `kandidat.csv`, `caleg.csv` | peserta + suara pribadi | KPU |
| `drone_misi.csv` | tujuan, luas_target_km2, status | Tim udara |
| `partai.csv` | kode_wilayah, partai, pengurus_aktif, saksi_disiapkan, mesin_skor, dukungan_ke_kita | Struktur partai |
| `ormas.csv` | kode_wilayah, ormas, anggota, pengurus, kedekatan (−1..1), pengaruh | Tim tokoh |
| `kandidat.csv` | bio lengkap calon & petahana (25 kolom: pendidikan, karier, LHKPN, program, kekuatan, kelemahan, basis massa…) | KPU, LHKPN, riset lawan |

Baris boleh setingkat kecamatan **atau** desa/kelurahan — kolom `desa` diisi bila ingin lebih halus. Mesin tidak peduli granularitas.

## Yang dihitung (bukan dikarang)
- **IKC (Indeks Kekuatan Calon)** — rata-rata tertimbang dari basis koalisi, survei, door-to-door, mesin darat, tokoh. **Komponen yang datanya kosong tidak ditebak**; bobotnya dinormalkan ulang dan kolom "Data" menampilkan berapa persen bobot yang benar-benar terisi.
- **Proyeksi suara** = DPT × turnout × 97% sah × share. Share = campuran survei (60%) + basis koalisi terkalibrasi (25%) + door-to-door (15%), bobot dinormalkan pada data yang ada.
- **Kalibrasi k** — rasio rata-rata survei/basis dari wilayah yang punya keduanya, dipakai untuk menaksir wilayah tanpa survei. Nilainya ditampilkan supaya bisa dibantah.
- **Margin of error** — 1,96·√(p(1−p)/n) dengan koreksi populasi terbatas dan efek desain 1,5.
- **Peluang menang** — sebaran normal atas selisih share; **otomatis disembunyikan** bila kelengkapan data di bawah ambang `batas_kelengkapan_data`.
- **Zona prioritas** — kuadran potensi (DPT) × kekuatan (IKC): BASIS / GARAP / AMANKAN / EFISIENSI.
- **Rencana penutup gap** — alokasi rakus dari biaya per suara termurah; ruang naik tiap wilayah = swing maksimum × (100−IKC)/100.
- **Kursi Sainte-Laguë** — pembagi 1,3,5,7…; harga kursi terakhir; kursi internal partai jatuh ke suara pribadi terbanyak (aturan sejak 2019).
- **Saksi TPS** — kebutuhan, cakupan, TPS rawan, dan suara berisiko (faktor risiko diatur di `konfigurasi.json`).
- **Drone** — fotogrametri sebenarnya: GSD = (lebar sensor × tinggi terbang × 100)/(fokal × lebar piksel); jarak jalur = swath × (1−sidelap); luas/sortie = kecepatan × endurance efektif × jarak jalur. Dari situ: jumlah sortie, jam terbang, set baterai, hari kerja, biaya.

## Modul lanjutan
- **Kekuatan partai** — mesin partai per wilayah (pengurus aktif, saksi disiapkan, skor mesin, dukungan ke kita), bobot 14% di IKC, plus matriks partai × wilayah.
- **Kekuatan ormas** — jangkauan = anggota × kedekatan × pengaruh, dipisah pro-kita dan pro-lawan; bobot 11% di IKC.
- **Calon & Petahana** — bio lengkap tiap calon, penanda PETAHANA, kekuatan/kelemahan, 5 wilayah terkuat, dan peta perebutan per wilayah.
- **Ontologi (cara Palantir)** — 12 silo data disatukan jadi objek (Wilayah, Partai, Ormas, Isu, Kandidat) + hubungan berbobot + sentralitas, lalu **anomali lintas silo**: DPT vs KK tidak wajar, survei jauh dari basis, klaim relawan tanpa pendataan, anggaran besar tapi kekuatan tetap rendah, ormas condong ke lawan, basis tanpa saksi, suara lama melebihi DPT, dan resolusi entitas (wilayah ganda / koordinat berdempet).
- **Risiko (cara Aladdin)** — model faktor: paparan portofolio suara terhadap 5 faktor (basis partai, ormas, urban, isu, ketergantungan turnout), korelasi silang-wilayah dari data nyata, volatilitas guncangan dari konfigurasi. Keluarannya: σ, **VaR 95%** dalam satuan suara, konsentrasi HHI + jumlah wilayah efektif, tracking error ke target, kontribusi risiko per wilayah, dan 7 uji tekanan (turnout anjlok, ormas berbalik, isu viral, mesin partai mogok, serangan gabungan, saksi kosong, konsolidasi berhasil).
- **Worker AI + DNA** — `worker.py` menyusun perintah kerja dari hasil mesin, lalu menyaringnya lewat 11 aturan DNA (`dna.json`): tanpa angka rujukan dibuang, biaya per suara di atas ambang dibuang, kata terlarang (politik uang, SARA, data pribadi) dibuang, satu wilayah satu perintah per kategori. Perintah yang ditolak tetap ditampilkan beserta alasannya. Narasi AI hanya ditulis kalau otak lokal (Ollama) hidup; kalau mati, worker mengatakannya dan tetap bekerja dengan aturan — tidak pernah mengarang.
- **Peta drone bergerak** — drone berjalan menyusuri jalur serpentin sesuai jarak jalur hasil hitungan fotogrametri, garis biru = jaringan wilayah terhubung (berbagi ormas/partai kuat + kedekatan jarak), garis ungu putus-putus = relay ke POSKO (wilayah ber-IKC tertinggi). Bisa dijeda, dipercepat, dan jaringannya dimatikan.

## Ganti jenis pemilihan
Dropdown di kepala dasbor: **Presiden · DPR RI · DPRD I · DPRD II · Gubernur · Bupati · Wali Kota · Kepala Desa · RT/RW · Camat · Lurah**. Aturan menangnya ikut berganti sendiri:
- pluralitas (suara terbanyak) untuk kepala daerah, pilkades, RT/RW;
- Sainte-Laguë + harga kursi untuk DPR/DPRD (ambang parlemen 4% khusus DPR RI);
- >50% + sebaran ≥20% di lebih dari separuh provinsi untuk presiden (kalau tak terpenuhi: putaran kedua);
- camat & lurah **tidak dipilih lewat pemungutan suara** — dasbor otomatis beralih ke mode peta dukungan & pemangku kepentingan dan mematikan proyeksi suara.
Dropdown kedua mengatur tingkat analisis (provinsi → kabupaten → kecamatan → desa → RW → RT).

## Struktur partai sampai ranting
`data/struktur_partai.csv` menyimpan DPC/DPD II, PAC per kecamatan, ranting per desa, dan anak ranting per RT: jumlah unit terbentuk vs target, pengurus, kader. Tab **Struktur & Ranting** menampilkan kelengkapan per partai dan kekurangan ranting per wilayah. Standarnya 1 ranting per 2.500 pemilih dan 1 anak ranting per TPS — supaya tiap TPS punya penanggung jawab yang sekaligus calon saksi.

## Saran menang & keputusan
- **Saran Menang** — vonis per daerah (MENANG AMAN / MENANG TIPIS / IMBANG / KALAH TIPIS / KALAH) dengan peluang lokal, berapa suara kurang, berapa rumah tangga harus didatangi (dihitung dari pemilih per KK × turnout × konversi door-to-door wilayah itu), berapa relawan, berapa ranting, berapa TPS tanpa saksi — plus langkah bernomor per daerah. Tiga **jalur kemenangan** (Kehadiran / Rebut Medan Tempur / Struktur & Ormas) masing-masing dengan tambahan suara, biaya, dan Rp per suara.
- **Keputusan & Pemicu** — 14 pemicu (`pemicu.json`) memantau ukuran nyata; begitu ambang terlampaui, pemicu berubah jadi keputusan dengan pilihan, penanggung jawab, dan tenggat. Setiap keputusan yang diambil tercatat di ledger.
- **Otak Neutron** — inti keputusan deterministik: tujuh lensa (proyeksi, ketahanan risiko, sebaran daerah, pengamanan suara, struktur partai, mutu data, benchmark) memberi suara berbobot; hasilnya konsisten untuk data yang sama karena tidak memakai model bahasa. Urutan otak: **neutron → Groq → Gemini → Ollama**; kunci API dibaca dari `~/shamar/.env`. Nama model Gemini ditanyakan langsung ke API (nama model sering berubah), Groq dikirim dengan User-Agent supaya tidak ditolak Cloudflare 1010.

## Benchmark
Tab **Benchmark** menilai kesiapan 0–100 (huruf A–E) atas 8 pilar berbobot: kelengkapan data, struktur sampai ranting, cakupan saksi, mesin darat, dukungan ormas, sentimen isu, efisiensi anggaran, pemetaan udara. Patokan pembanding antar wilayah diambil dari **kuartil atas wilayah sendiri** — standar yang sudah terbukti bisa dicapai tim ini, bukan angka impor. Dari situ keluar "potensi tambahan suara bila semua wilayah setara patokan".

## Ledger
`data/ledger.jsonl` — buku besar berantai (SHA-256, tiap baris menyimpan hash baris sebelumnya). Yang tercatat: setiap hitungan mesin, perubahan data, perubahan konfigurasi, pemicu merah yang aktif, putusan Neutron, dan setiap keputusan yang diambil. Kartu "Keutuhan rantai" langsung merah kalau ada baris lama yang diubah.

## Kesimpulan
Tab **Kesimpulan** merangkum semuanya jadi satu halaman siap cetak: vonis menang/kalah, syarat menang (checklist ✓/✗), apa yang bisa membuat kalah beserta dampaknya dalam suara, tiga cara memenangkan, daftar daerah wajib dipertahankan / harus direbut / jangan dibakar uang, kebutuhan total (relawan, rumah, saksi, ranting, biaya), jadwal H-90 → H-0, dan indikator pantau mingguan.

## Pagar (sengaja dipasang)
- Selama `sumber_data` masih `"contoh"`, seluruh dasbor bertanda **DATA SIMULASI**.
- Angka tidak pernah diketik tangan; data contoh dihasilkan `benih.py` secara deterministik.
- Metrik tanpa data ditulis `—`, bukan ditebak.
- Peluang menang mati bila data terlalu tipis.
- Perencanaan drone hanya menghitung teknis; izin ruang udara, ketinggian, dan area larangan tetap urusan operator.
- Worker AI gagal-tertutup: otak AI mati → dikatakan mati, bukan diganti karangan.
- Gerbang DNA menolak perintah yang melanggar hukum pemilu atau tidak menunjuk angka.

## Kepatuhan
Dasbor ini bekerja pada data agregat wilayah (DPT per wilayah, hasil rekap, survei, pendataan tim). Jangan memasukkan NIK, alamat rumah, nomor telepon, atau data pribadi pemilih ke dalamnya — selain melanggar UU PDP, satu wilayah pun tidak butuh itu untuk semua hitungan di atas.
