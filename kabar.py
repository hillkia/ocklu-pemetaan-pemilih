# -*- coding: utf-8 -*-
"""KABAR (umum) — kabari pemilik tiap kerja harian selesai.

Berdiri sendiri: tidak butuh berkas lain dari proyek. Isinya diambil dari
LAPORAN.md kalau ada; kalau tidak ada, dari ringkasan seadanya.

Pakai:  python3 kabar.py "nama-proyek: putaran kerja selesai"
"""
import json, os, pathlib, smtplib, ssl, sys, time, urllib.parse, urllib.request
from email.message import EmailMessage

AKAR = pathlib.Path(__file__).resolve().parent
PROYEK = os.environ.get("PROYEK") or AKAR.name


def _env(nama, bawaan=""):
    v = os.environ.get(nama)
    if v:
        return v.strip()
    for p in (AKAR / ".env", pathlib.Path.home() / "shamar" / ".env"):
        try:
            for baris in p.read_text(errors="ignore").splitlines():
                if baris.strip().startswith(nama + "="):
                    return baris.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return bawaan


def isi_laporan(batas_baris=45):
    p = AKAR / "LAPORAN.md"
    if p.exists():
        baris = [b for b in p.read_text(errors="ignore").splitlines()]
        return "\n".join(baris[:batas_baris]).strip()
    catatan = AKAR / "data" / "harian.log"
    if catatan.exists():
        return "\n".join(catatan.read_text(errors="ignore").splitlines()[-25:])
    return "Putaran kerja selesai. Proyek ini belum menulis LAPORAN.md."


def teks(judul):
    return (f"{judul}\n{time.strftime('%Y-%m-%d %H:%M')}\n\n{isi_laporan()}\n\n"
            f"Gudang: https://github.com/hillkia/{PROYEK}")


def telegram(pesan):
    kunci, tujuan = _env("TELEGRAM_BOT_TOKEN"), _env("TELEGRAM_CHAT_ID")
    if not (kunci and tujuan):
        return {"jalur": "telegram", "terkirim": False, "sebab": "isian belum ada"}
    try:
        data = urllib.parse.urlencode({"chat_id": tujuan, "text": pesan[:3900],
                                       "disable_web_page_preview": "true"}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{kunci}/sendMessage",
                                     data=data, headers={"User-Agent": "ocklu/1.0"})
        urllib.request.urlopen(req, timeout=30).read()
        return {"jalur": "telegram", "terkirim": True}
    except Exception as e:
        return {"jalur": "telegram", "terkirim": False, "sebab": str(e)[:120]}


def email(judul, pesan):
    user = _env("SMTP_USER", "hillkiacakep@gmail.com")
    sandi = _env("SMTP_PASS") or _env("GMAIL_PASS")
    if not sandi:
        return {"jalur": "email", "terkirim": False, "sebab": "sandi email belum ada"}
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = user, _env("KABAR_KE", user), judul
    m.set_content(pesan)
    try:
        with smtplib.SMTP_SSL(_env("SMTP_HOST", "smtp.gmail.com"), int(_env("SMTP_PORT", "465")),
                              context=ssl.create_default_context(), timeout=40) as s:
            s.login(user, sandi)
            s.send_message(m)
        return {"jalur": "email", "terkirim": True}
    except Exception as e:
        return {"jalur": "email", "terkirim": False, "sebab": str(e)[:140]}


def kirim(judul=None):
    judul = judul or f"{PROYEK}: putaran kerja selesai"
    pesan = teks(judul)
    hasil = [telegram(pesan), email(judul, pesan)]
    print("[kabar] " + json.dumps(hasil, ensure_ascii=False), flush=True)
    return hasil


if __name__ == "__main__":
    kirim(sys.argv[1] if len(sys.argv) > 1 else None)
