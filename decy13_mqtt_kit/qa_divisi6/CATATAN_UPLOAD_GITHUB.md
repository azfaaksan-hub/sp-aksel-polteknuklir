# Catatan unggah ke GitHub

File di folder ini sudah disusun agar dapat **disalin langsung ke root repository** `sp-aksel-polteknuklir`. Berkas baru diletakkan pada `decy13_mqtt_kit/qa_divisi6/`; tidak ada file divisi lain yang diganti.

**Branch kerja yang disarankan:** `divisi-6-mqtt-nodered-qa-testing` atau branch review baru dari branch tersebut, kemudian buat Pull Request untuk ketua menuju `main` sesuai alur kolaborasi tim. Jangan commit langsung ke `main` tanpa review.

## Melalui GitHub Desktop

1. Buka/clone repo `azfaaksan-hub/sp-aksel-polteknuklir` dan **Fetch origin**.
2. Pilih branch `divisi-6-mqtt-nodered-qa-testing`. Bila akan buat branch review, lakukan di GitHub Desktop melalui **Branch → New branch**.
3. Buka folder repo di File Explorer. Salin isi folder `decy13_mqtt_kit/qa_divisi6` dari paket ini ke folder repo dengan path yang sama, **tanpa** membuat folder `DECY13_Divisi6_GitHub_Handover_20261119` di dalam repo.
4. Periksa **Changes**; pastikan hanya berkas di `decy13_mqtt_kit/qa_divisi6/` yang ditambahkan.
5. **Commit to branch** dengan pesan `docs(divisi6): add QA report, test guide and safe handover`.
6. **Push origin**, lalu buka PR dan mintalah ketua memverifikasi sebelum merge.

## Melalui terminal Git

```bash
git checkout divisi-6-mqtt-nodered-qa-testing
git pull --ff-only origin divisi-6-mqtt-nodered-qa-testing
# salin isi paket ke root repository sesuai path

git status --short
git add decy13_mqtt_kit/qa_divisi6
git diff --cached --stat
git commit -m "docs(divisi6): add QA report, test guide and safe handover"
git push origin divisi-6-mqtt-nodered-qa-testing
```

Jangan jalankan perintah di atas sebelum meninjau perubahan dan memastikan tidak ada password. Tiga file CSV pengujian asli sudah ikut dalam `bukti/data_asli/`. Audit kolom hasil sudah dilakukan; periksa kembali kebijakan privasi repository publik sebelum push. File ekspor penuh dari Node-RED sengaja disimpan hanya sebagai arsip lokal (di luar folder UNTUK_GITHUB).
