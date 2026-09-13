# -*- coding: utf-8 -*-
"""Kerja harian Pemetaan Pemilih: hitung ulang angka lalu tulis laporan HP."""
import json, pathlib, time
import mesin

AKAR = pathlib.Path(__file__).resolve().parent
hasil = mesin.rollup()
(AKAR / "web").mkdir(exist_ok=True)
(AKAR / "web" / "data.json").write_text(json.dumps(hasil, ensure_ascii=False, default=str))

def hitung(x):
    return len(x) if isinstance(x, (list, dict)) else "-"

baris = ["# Pemetaan Pemilih — laporan", "",
         f"_diperbarui {time.strftime('%Y-%m-%d %H:%M')}_", ""]
for k, v in (hasil.items() if isinstance(hasil, dict) else []):
    baris.append(f"- **{k}**: {hitung(v)}")
baris += ["", "Angka dihitung ulang dari data yang ada, bukan ditulis tangan."]
(AKAR / "LAPORAN.md").write_text("\n".join(baris) + "\n")
print("rollup selesai")
