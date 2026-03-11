[README.md](https://github.com/user-attachments/files/25893315/README.md)
Akses Aplikasi : https://anchor-tte.streamlit.app/
# PDF TTD Injector — Web Edition
**Streamlit app untuk menyisipkan anchor tanda tangan elektronik ke PDF RKA**

---

## 📁 Struktur File

```
ttd_injector_web/
├── app.py              ← aplikasi utama Streamlit
├── core.py             ← logika PDF (inject + merge)
├── requirements.txt    ← dependencies
└── README.md
```

---

## 🚀 Cara Deploy ke Streamlit Community Cloud (GRATIS)

### Langkah 1 — Upload ke GitHub
1. Buat akun GitHub (gratis) di https://github.com
2. Buat repository baru → misal: `pdf-ttd-injector`
3. Upload ketiga file: `app.py`, `core.py`, `requirements.txt`

### Langkah 2 — Deploy di Streamlit Cloud
1. Buka https://share.streamlit.io
2. Login dengan akun Google / GitHub
3. Klik **"New app"**
4. Pilih repository GitHub yang tadi dibuat
5. Pastikan **Main file path** = `app.py`
6. Klik **Deploy!**

Dalam ~2 menit aplikasi sudah online dengan URL seperti:
```
https://namaanda-pdf-ttd-injector.streamlit.app
```

URL ini bisa dibagikan ke seluruh tim — bisa diakses dari browser manapun tanpa install apapun.

---

## 💻 Cara Jalankan Lokal (untuk testing)

```bash
pip install streamlit pymupdf
streamlit run app.py
```

Buka browser ke http://localhost:8501

---

## ✨ Fitur

- **Upload multi-file** — pilih beberapa PDF sekaligus
- **Mode Single Anchor** — satu teks target + satu anchor (seperti versi desktop)
- **Mode Multi Anchor** — tabel dinamis, bisa inject beberapa TTD sekaligus (contoh: ttd_pengirim1 + ttd_pengirim2)
- **Download merged PDF** — semua output digabung jadi 1 file
- **Download ZIP** — semua file individual dikemas dalam zip
- **Download per-file** — unduh satu-satu

---

## 🔒 Catatan Keamanan

File PDF yang diupload **tidak disimpan permanen** di server — hanya diproses di memori (RAM) dan langsung tersedia untuk didownload. Setelah sesi browser ditutup, file hilang otomatis.

Untuk dokumen sangat rahasia, disarankan tetap menggunakan versi desktop yang berjalan 100% lokal di komputer Anda.
