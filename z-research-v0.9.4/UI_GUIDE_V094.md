# Cara pakai Z-Research v0.9.4 — versi sederhana

## Apa yang berubah?

- Dashboard sekarang menyarankan **satu tindakan berikutnya** berdasarkan progres proyek.
- Tab `Data & Proyek`: unggah data dan pembuatan proyek menjadi satu proses saat pengguna mengizinkan.
- Nama kolom dapat dilihat semuanya melalui tombol `Lihat isi`, termasuk nilai contoh.
- Pemilihan konstruk X, mediator, moderator tidak perlu menekan Cmd/Ctrl saat memilih banyak: cukup centang.
- Pengaturan lanjutan, integritas, dan opsi editing mentah tetap tersedia tetapi tidak memenuhi halaman awal.
- Saat mengganti dataset proyek yang sudah bermodel, ada dialog konfirmasi sebelum mereset model.
- Pengguna perangkat kedua cukup buka alamat IP server, **tidak perlu memasang Python atau aplikasi** di perangkat kedua.

## Jika ingin memakai dataset UMKM dengan kode KP1-KP7

Upload file CSV yang sudah memiliki kode dan nilai numerik. Data 7 indikator KP dapat ditampilkan. Namun, tujuh item `KP` saja akan dideteksi sebagai **satu kelompok** berdasarkan prefix. Model SEM-PLS dengan jalur X → Y memerlukan lebih dari satu konstruk **yang memang memiliki dasar teori**, bukan sekadar membagi kolom agar tombol Analisis bisa ditekan. Untuk survei evaluasi satu kelompok, gunakan statistik deskriptif bila lebih sesuai. Jangan menafsirkan pengelompokan otomatis sebagai validasi konsep.

## Membuka dua perangkat

- MacBook/PC pertama bertindak sebagai server dan harus tetap menyala.
- Semua perubahan tersimpan di perangkat server.
- Browser HP/laptop kedua menggunakan URL IP server dari Terminal, bukan `127.0.0.1`.
- Versi ini belum diuji untuk kolaborasi multi-user bersamaan pada dataset/proyek yang sama. Hindari pengeditan simultan atas objek riset yang sama.
