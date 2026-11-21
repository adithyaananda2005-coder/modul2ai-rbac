# Praktikum 2 ? Chatbot RAG dengan RBAC

Aplikasi mengikuti modul yang disediakan: FastAPI, SQLite, JWT, ekstraksi PDF/DOCX/XLSX/CSV/TXT/MD, pencarian hybrid hashing dan leksikal, Groq, panel admin, serta sumber referensi.

## Menjalankan di Windows

Dari folder `modul2ai`, jalankan:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Jika menyalin proyek ke komputer lain:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Isi API key dan JWT_SECRET di .env.
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Chat: http://127.0.0.1:8000 ? Admin: http://127.0.0.1:8000/admin.
Akun lokal praktikum: admin / admin123; dosen / dosen123. Mahasiswa dapat chat tanpa login. Login dosen tersedia di bagian atas halaman chat. Ganti password dan JWT_SECRET sebelum deployment publik. Akun dibuat saat database pertama diinisialisasi; perubahan password .env tidak memperbarui akun yang sudah tersimpan.

## Penggunaan

1. Login sebagai admin, tambah role melalui Manajemen Role.
2. Pilih satu atau beberapa checkbox role saat upload. Tidak ada role yang dipilih secara otomatis.
3. Dokumen default SSC/TAK diindeks untuk mahasiswa. `INTERNAL_Panduan_Dosen_Demo.txt` khusus dosen dan jelas merupakan simulasi, bukan aturan kampus.
4. Tanyakan kode verifikasi moderasi menggunakan akun dosen; nilai demo adalah MODERASI-8472. Mahasiswa tidak dapat membaca sumber tersebut, termasuk melalui URL unduhan atau dengan memalsukan parameter role.
5. Gunakan Lihat Chunks, Aktifkan/Nonaktifkan, Hapus, preview chatbot berdasarkan role, dan Kuota Groq API.

Role baru dapat dipakai admin untuk preview dan pembatasan dokumen. Akun pengguna selain akun dosen demo belum disediakan melalui UI; manajemen akun pengguna tidak termasuk butir manajemen role di modul.

## Pengujian

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m unittest discover -s tests -v
# Jalankan server terlebih dahulu, kemudian:
.\.venv\Scripts\python tests/browser_check.py
```

Tes unit memakai database dan upload sementara serta mematikan Groq. Tes pemisahan konteks mengganti generator jawaban dengan pemeriksaan konteks agar tidak bergantung pada internet. Tes browser menggunakan Microsoft Edge yang sudah terpasang dan memanggil Groq sungguhan; hasilnya tersimpan di `evidence/`.

## Deployment Railway

Modul PDF deployment yang dilampirkan sudah dibaca dan konfigurasi diselaraskan dengan Railpack. Referensi tambahan: [panduan resmi Railway](https://railway.com/guides/fastapi).

1. Upload kode folder `modul2ai` ke repository milik Anda tanpa `.env`, `.venv`, database, dan uploads lokal. Jika repository berisi folder induk praktikum, atur Root Directory Railway menjadi `/modul2ai`.
2. Buat project Railway dari repository tersebut. Railpack dipilih secara eksplisit di railway.json; railpack.json dan Procfile menyediakan start command sesuai modul PDF. Dockerfile tetap tersedia sebagai alternatif manual. Server menggunakan `0.0.0.0` dan `$PORT`; health check `/health`.
3. Tambahkan volume pada `/data`. Atur `DB_PATH=/data/modul2ai.db` dan `UPLOAD_DIR=/data/uploads`. Jalankan satu instance karena aplikasi menggunakan SQLite.
4. Isi Variables: `GROQ_API_KEY`, `GROQ_MODEL=llama-3.3-70b-versatile`, `JWT_SECRET` acak minimal 32 karakter, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DOSEN_USERNAME`, `DOSEN_PASSWORD`. Gunakan password baru sebelum startup pertama.
5. Deploy, lalu Settings ? Networking ? Generate Domain. Uji chat mahasiswa, login dosen, sumber dokumen, dan dashboard. Ambil screenshot cloud dan catat URL aktif di laporan.

Model default dipilih dari [daftar model Groq](https://console.groq.com/docs/models). Kuota memerlukan request Groq yang berhasil; jika API key belum diisi, aplikasi menampilkan status konfigurasi dan sumber yang ditemukan. CSS Tailwind sudah dikompilasi menjadi `static/app.css`, sehingga tampilan tidak memerlukan CDN. Untuk membangun ulang setelah mengubah class HTML/JavaScript: `npx --yes tailwindcss@3.4.19 -i ./static/input.css -o ./static/app.css --minify`.

Deployment cloud belum dilakukan karena akses proyek Railway belum tersedia. Screenshot lokal tidak membuktikan deployment cloud. Template laporan individu tidak disertakan, sehingga LAPORAN_PRAKTIKUM.md adalah draf yang perlu dipindahkan ke template LMS.

Pengujian cloud: set `TEST_BASE_URL` ke domain Railway, `TEST_EVIDENCE_DIR=cloud`, `TEST_ADMIN_PASSWORD` dan `TEST_DOSEN_PASSWORD` sesuai akun cloud, lalu jalankan `python tests/browser_check.py`. Screenshot tersimpan terpisah di evidence/cloud/.
