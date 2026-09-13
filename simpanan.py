#!/usr/bin/env python3
"""SIMPANAN — cadangan isi folder data/ ke gudang GitHub pribadi.

Kenapa perlu: di server gratis (Render), isi folder data/ HILANG setiap kali
aplikasi dipasang ulang atau tidur lalu bangun. Tanpa ini, catatanmu hangus.

Caranya: seluruh folder data/ dibungkus jadi satu paket terkompres lalu
disimpan di gudang. Yang tidak ikut: berkas sementara (cache, log, kunci).

Butuh dua isian di server:
  GITHUB_TOKEN   token pribadi GitHub (izin: repo)
  GUDANG_DATA    contoh: hillkia/ocklu-data

Kalau kosong, modul ini diam saja — tidak error, tapi juga tidak pura-pura
sudah menyimpan.
"""
import base64, hashlib, io, json, os, tarfile, threading, time, urllib.error, urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(DIR, "data")
PROYEK = os.environ.get("PROYEK") or os.path.basename(DIR)
GUDANG = os.environ.get("GUDANG_DATA", "hillkia/ocklu-data")
JALAN = f"{PROYEK}/data.tar.gz"

# Tidak ikut dicadangkan:
#   - sementara / bisa dibuat ulang (cache, log, kunci proses)
#   - berkas berat yang SUDAH ikut di gudang kode (foto, bahan mentah, ebook)
# Yang dicadangkan hanya catatan yang berubah saat dipakai — itu yang tidak
# bisa dibuat ulang kalau hilang.
LEWATI = ("cache/", "__pycache__/", "gambar/", "mentah/", "ebook/",
          ".lock", ".log", ".tmp", ".bak.json", ".DS_Store", ".cadangan_terakhir")

def siap():
    return bool(os.environ.get("GITHUB_TOKEN") and GUDANG)

def _api(metode, isi=None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GUDANG}/contents/{JALAN}",
        data=json.dumps(isi).encode() if isi is not None else None, method=metode,
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "ocklu/1.0", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or "{}")

def _ikut(nama):
    return not any(x in nama for x in LEWATI)

def _bungkus():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for akar, _, berkas in os.walk(DATA):
            for b in berkas:
                p = os.path.join(akar, b)
                rel = os.path.relpath(p, DATA)
                if _ikut(rel):
                    try:
                        t.add(p, arcname=rel)
                    except (OSError, ValueError):
                        pass
    return buf.getvalue()

def simpan(paksa=False):
    """Simpan kalau isinya berubah. Balikin apa adanya, termasuk kalau gagal."""
    if not siap():
        return {"aktif": False, "sebab": "GITHUB_TOKEN / GUDANG_DATA belum diisi"}
    if not os.path.isdir(DATA):
        return {"aktif": True, "ok": False, "sebab": "folder data belum ada"}
    isi = _bungkus()
    sidik = hashlib.sha256(isi).hexdigest()
    tanda = os.path.join(DATA, ".cadangan_terakhir")
    if not paksa and os.path.exists(tanda) and open(tanda).read().strip() == sidik:
        return {"aktif": True, "ok": True, "dilewati": "isi belum berubah sejak cadangan terakhir"}
    try:
        sha = None
        try:
            sha = _api("GET").get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        badan = {"message": f"cadangan {PROYEK}", "content": base64.b64encode(isi).decode()}
        if sha:
            badan["sha"] = sha
        _api("PUT", badan)
        open(tanda, "w").write(sidik)
        return {"aktif": True, "ok": True, "bytes": len(isi), "jalan": JALAN}
    except Exception as e:
        return {"aktif": True, "ok": False, "sebab": str(e)[:160]}

def pulihkan(paksa=False):
    """Ambil catatan dari gudang dan tulis di atas salinan bawaan.

    Sengaja MENIMPA: berkas yang ada di server barusan datang dari gudang kode
    (salinan lama, ikut saat dipasang). Isi cadangan selalu lebih baru, dan
    isinya cuma catatan yang berubah — bukan foto atau bahan mentah.
    """
    if not siap():
        return {"aktif": False, "sebab": "GITHUB_TOKEN / GUDANG_DATA belum diisi"}
    try:
        d = _api("GET")
    except urllib.error.HTTPError as e:
        return {"aktif": True, "ok": False, "sebab": f"belum ada di gudang ({e.code})"}
    except Exception as e:
        return {"aktif": True, "ok": False, "sebab": str(e)[:160]}
    isi = base64.b64decode(d["content"]) if d.get("content") else b""
    if not isi and d.get("download_url"):
        req = urllib.request.Request(d["download_url"], headers={"User-Agent": "ocklu/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            isi = r.read()
    os.makedirs(DATA, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(isi), mode="r:gz") as t:
        anggota = [m for m in t.getmembers() if not m.name.startswith(("/", ".."))]
        t.extractall(DATA, members=anggota)
    return {"aktif": True, "ok": True, "berkas": len(anggota), "bytes": len(isi)}

def jaga(jeda=900):
    """Nyalakan penjaga di latar: pulihkan sekali, lalu simpan berkala."""
    if not siap():
        print("[cadangan] belum aktif — isi GITHUB_TOKEN & GUDANG_DATA kalau catatan mau aman", flush=True)
        return
    p = pulihkan()
    print(f"[cadangan] pulihkan: {p}", flush=True)
    def putar():
        while True:
            time.sleep(jeda)
            h = simpan()
            if not h.get("ok"):
                print(f"[cadangan] gagal: {h.get('sebab')}", flush=True)
    threading.Thread(target=putar, daemon=True).start()
    print(f"[cadangan] penjaga hidup, simpan tiap {jeda//60} menit", flush=True)

if __name__ == "__main__":
    import sys
    if "--pulihkan" in sys.argv:
        print(json.dumps(pulihkan(paksa="--paksa" in sys.argv), indent=1, ensure_ascii=False))
    else:
        print(json.dumps(simpan(paksa="--paksa" in sys.argv), indent=1, ensure_ascii=False))
