# Aktivasi Z-Research untuk 2 device (MacBook + HP/laptop)

1. Backup folder `local_data` dari instalasi lama jika ada data penelitian. Jangan hapus instalasi lama sebelum backup.
2. Ekstrak ZIP ini di Downloads. Pastikan folder `z-research-v0.9.3` tidak tertukar dengan folder versi lama. Jika perlu, ubah nama folder hasil ekstraksi menjadi `z-research-v0.9.3-2devices`.
3. Buka folder hasil ekstraksi. Klik kanan `START_2_DEVICES_MAC.command` > Open (jika diblokir macOS), atau jalankan `bash START_2_DEVICES_MAC.command` dari Terminal di folder itu.
4. Launcher membuat `.venv-2devices` dan memasang dependensi saat pertama dijalankan; tunggu sampai muncul alamat MacBook dan alamat device kedua.
5. Pastikan kedua device memakai Wi-Fi pribadi yang sama, lalu buka alamat `http://IP-MACBOOK:8765` yang tercetak pada HP/laptop kedua. Tidak perlu menginstal aplikasi di device kedua.
6. Jika device kedua tidak dapat terhubung: cek macOS Firewall dan izinkan Python menerima koneksi masuk, matikan VPN, dan pastikan router tidak memakai guest/client isolation.

GraphInsight di port 8000 tidak disentuh. Launcher ini memakai port 8765 dan tidak menghentikan proses lain. Jika port 8765 sudah terpakai, launcher berhenti dan menampilkan prosesnya.

PENTING: mode ini mengekspos aplikasi ke seluruh perangkat di jaringan Wi-Fi yang sama, bukan hanya dua perangkat. Gunakan jaringan tepercaya, jangan gunakan port forwarding atau Wi-Fi publik. Z-Research masih local beta; hindari pengeditan proyek yang sama secara bersamaan oleh dua orang sebelum audit kolaborasi selesai.

Jika Python tidak ada, instal Python 3.11 atau 3.12. Jika terjadi error, salin 10 baris terakhir Terminal untuk diagnosis.
