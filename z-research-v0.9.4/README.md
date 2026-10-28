# Z-Research v0.9.4 — Easy Research Workspace

**Perubahan utama:** antarmuka lebih sederhana dalam bahasa Indonesia, tanpa mengubah algoritma SEM-PLS, format database, atau lapisan integritas riset v0.9.3. Ini adalah **rilis local beta**, bukan production server multi-user.

## Aktivasi MacBook: paling mudah, 2 perangkat

1. Ekstrak ZIP ke folder `z-research-v0.9.4` di **Downloads**.
2. Jika punya penelitian pada instalasi lama, **backup dan migrasikan `local_data` sebelum pertama kali menjalankan versi baru**. Lihat bagian migrasi di bawah.
3. Buka folder hasil ekstraksi. Klik kanan `START_2_DEVICES_MAC.command` > **Open**. Atau buka Terminal dari folder tersebut dan ketik: `bash START_2_DEVICES_MAC.command`.
4. Launcher otomatis membuat Python virtual environment `.venv-2devices` dan memasang library (hanya saat pertama kali). Biarkan Terminal tetap terbuka.
5. Buka `http://127.0.0.1:8765` di MacBook. Di perangkat kedua, buka alamat `http://IP-MACBOOK:8765` yang **ditampilkan Terminal**. Kedua perangkat harus dalam Wi-Fi pribadi yang sama.

**GraphInsight** yang menggunakan port 8000 tidak perlu dihentikan. Z-Research menggunakan port 8765.

Jika Safari/Chrome gagal membuka dari perangkat kedua: cek kedua perangkat pada Wi-Fi yang sama, izin firewall masuk untuk Python, router guest/client isolation, dan apakah Terminal masih menampilkan `Uvicorn running`.

## Windows

Jalankan `START_2_DEVICES_WINDOWS.bat`. Gunakan `ipconfig` untuk melihat IPv4 Address Windows, kemudian dari perangkat kedua buka `http://IP-WINDOWS:8765`. Izinkan Python pada **Private networks** jika Windows Firewall bertanya. Untuk akses komputer server saja gunakan `START_WINDOWS.bat`.

## Panduan UI — lima langkah

1. **Data:** Pilih file `.csv` / `.xlsx` (maks 10MB). Saat proyek belum ada, centang *Otomatis buat proyek* agar langsung lanjut.
2. **Model:** Pilih konstruk X menggunakan kotak centang, lalu pilih konstruk Y. Mediator dan moderator disembunyikan dalam opsi tambahan. **Nama kolom saja bukan validasi konstruk**.
3. **Analisis:** Klik hitung SEM-PLS. Pastikan model punya hubungan dan indikator memadai. Engine ini **eksperimental** dan hasil perlu benchmark sebelum publikasi.
4. **Referensi:** Masukkan artikel dan verifikasi bibliografinya. AI tidak boleh mengarang sumber.
5. **Menulis:** Buka Bab 1-4; sitasi dapat dihubungkan dengan referensi, riwayat dan integritas dapat ditinjau di menu pengaturan lanjutan.

Tombol **Lihat isi** pada daftar dataset memperlihatkan seluruh nama variabel dan contoh isi kolom. Klasifikasi numerik hanya perkiraan dari beberapa baris contoh.

## Migrasi data dari v0.9.3 / versi lama

> Jangan menghapus folder Z-Research lama dan jangan menimpa dataset tanpa backup.

1. Hentikan server Z-Research lama dengan `Control+C` (tidak perlu menghentikan GraphInsight).
2. Salin/cadangkan seluruh folder lama (terutama `local_data`) ke lokasi aman.
3. **Sebelum menjalankan instalasi baru untuk pertama kalinya**, copy **seluruh** folder `local_data` lama ke folder `z-research-v0.9.4/`. Folder `local_data` berisi database proyek, dokumen, serta dataset. Jangan hanya menyalin file `.db`.
4. Jika folder tujuan **sudah memiliki `local_data` berisi proyek baru**, jangan menimpa atau mencampur dua database. Backup keduanya dan minta bantuan migrasi terarah.
5. Jalankan launcher baru. Login dengan akun pemilik lokal yang sudah ada. Cek dataset, referensi, dan riwayat audit sebelum melanjutkan.

**Catatan:** tidak ada migrasi database otomatis saat membuka rilis ini. Jika Anda ingin tetap menjalankan v0.9.3, biarkan folder lama sebagai arsip.

## Status QA

- `91/91` Python automated tests passed (84 legacy + 7 UX regression tests).
- `46/46` JavaScript checks passed (13 + 20 + 13).
- Chromium E2E via isolated API bridge (desktop 1440px/mobile 390px): login, upload data, create project otomatis, model checkbox, auto-model, guided dashboard, mobile menu, layout overflow; no JavaScript page errors seen in the exercised routes.
- Shell: launcher Mac bash syntax verified.

**Belum diuji langsung pada Mac/Windows Anda.** Belum terverifikasi native two-device networking, stress simultan multi-user, power-loss recovery, pentest, SEM-PLS parity, serta produksi publik. Untuk data sensitif dan jaringan publik, jangan gunakan sampai penilaian keamanan terpisah selesai.

Berkas sumber dan hasil pengujian lama v0.9.3 disertakan sebagai arsip historis. Lihat `QA_RESULTS_V094.json` dan `qa_evidence_v094/` untuk pengujian UI terbaru.
