#!/usr/bin/env python3
"""Ledger: catatan berantai (hash chain) untuk semua perubahan data, hitungan, dan keputusan.
Tidak bisa diubah diam-diam — mengubah satu baris merusak rantai dan langsung ketahuan."""
import json, os, hashlib, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE, 'data', 'ledger.jsonl')

def _hash(prev, isi):
    return hashlib.sha256((prev + json.dumps(isi, sort_keys=True, ensure_ascii=False, default=str)).encode()).hexdigest()

def terakhir():
    try:
        with open(FILE) as f:
            baris = [b for b in f if b.strip()]
        return json.loads(baris[-1]) if baris else None
    except Exception:
        return None

def catat(jenis, ringkas, data=None, oleh='sistem'):
    prev = (terakhir() or {}).get('hash', 'GENESIS')
    isi = dict(nomor=((terakhir() or {}).get('nomor', 0) + 1),
               waktu=datetime.datetime.now().isoformat(timespec='seconds'),
               jenis=jenis, ringkas=ringkas, oleh=oleh, data=data or {})
    isi['hash_sebelum'] = prev
    isi['hash'] = _hash(prev, isi)
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    with open(FILE, 'a') as f:
        f.write(json.dumps(isi, ensure_ascii=False, default=str) + '\n')
    return isi

def baca(batas=300):
    try:
        with open(FILE) as f:
            baris = [json.loads(b) for b in f if b.strip()]
    except Exception:
        return []
    return baris[-batas:][::-1]

def verifikasi():
    try:
        with open(FILE) as f:
            baris = [json.loads(b) for b in f if b.strip()]
    except Exception:
        return dict(ok=True, jumlah=0, rusak=None, pesan='ledger belum ada')
    prev = 'GENESIS'
    for i, b in enumerate(baris):
        isi = {k: v for k, v in b.items() if k != 'hash'}
        if b.get('hash_sebelum') != prev or _hash(prev, {k: v for k, v in isi.items() if k != 'hash_sebelum'} | {'hash_sebelum': prev}) != b['hash']:
            return dict(ok=False, jumlah=len(baris), rusak=i + 1, pesan=f'rantai putus di catatan ke-{i+1}')
        prev = b['hash']
    return dict(ok=True, jumlah=len(baris), rusak=None, pesan='rantai utuh')

if __name__ == '__main__':
    print(json.dumps(verifikasi(), ensure_ascii=False))
