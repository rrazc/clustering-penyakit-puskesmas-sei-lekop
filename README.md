# Identifikasi Pola Sebaran Penyakit Antarwilayah Kelurahan/Desa dengan Data Mining di Puskesmas Sei Lekop

Project mata kuliah **Penambangan Data (INF11121)**, Teknik Informatika, Fakultas Teknik dan Teknologi Kemaritiman, Universitas Maritim Raja Ali Haji, semester ganjil 2026/2027.

**Video presentasi:** `(https://youtu.be/ZDbIlXIsW38)`

## Tim

| NIM | Nama |
|---|---|
| 2401020017 | Rashika Kasih Putri (Ketua) |
| 2401020001 | Amira Azza Nuuradiba |
| 2401020005 | Juan Prattycha Tazira |
| 2401020006 | Zafira Khairunnisa |
| 2401020014 | Naurah Nadhif Shahada |

---

## 1. Ringkasan

Puskesmas Sei Lekop mencatat setiap kunjungan pasien, termasuk **kelurahan/desa asal pasien** dan **kode diagnosis** (ICD-10). Catatan itu belum dimanfaatkan untuk melihat **wilayah mana yang punya pola penyakit mirip**.

Project ini mengelompokkan (clustering) kelurahan/desa asal pasien berdasarkan **komposisi diagnosis** pada kunjungan tahun 2025. Hasilnya ditampilkan di sebuah dashboard web offline.

> **Catatan penting.** "Pola sebaran" di sini berarti *kemiripan komposisi diagnosis antarwilayah asal pasien*, **bukan** letak geografis penderita dan **bukan** angka prevalensi penyakit penduduk. Data berasal dari satu fasilitas kesehatan saja, jadi hasilnya bersifat eksploratif.

## 2. Hasil Utama

- **Model utama:** Ward hierarchical clustering + transformasi Hellinger, **11 wilayah**, **k = 2**.
- **Cluster 1 (8 wilayah):** Sungai Lekop, Gunung Lengkuas, Gunung Kijang, Kijang Kota, Batu Sembilan, Pinang Kencana, Tanjung Ayun Sakti, Kawal.
- **Cluster 2 (3 wilayah):** Toapaya Selatan, Sungai Enam, Sei Jang.
- **Silhouette = 0,3059** (tergolong lemah, jadi hasil dibaca sebagai *kecenderungan*, bukan pemisahan tegas).
- Rata-rata proporsi diagnosis per cluster:

| Kategori ICD-10 | Cluster 1 | Cluster 2 |
|---|---|---|
| Pernapasan (J) | 19,93% | 31,31% |
| Pencernaan (K) | 14,62% | 14,57% |
| Sirkulasi (I) | 14,52% | 8,53% |
| Kulit (L) | 5,35% | 10,71% |

Cluster 2 punya porsi diagnosis pernapasan dan kulit yang lebih tinggi, dan porsi sirkulasi yang lebih rendah. Angka cluster (C1, C2) hanya nama kelompok, **bukan** tingkat bahaya penyakit.

### Perbandingan dan uji ketahanan

| Skenario | Silhouette | ARI bootstrap (rata-rata) | Ulangan dengan cluster tunggal |
|---|---|---|---|
| **11 wilayah, Ward, k=2 (utama)** | 0,3059 | 0,4796 | 15,5% |
| 9 wilayah, Ward, k=2 (pembanding) | 0,3917 | 0,6308 | 35,0% |
| 12 wilayah (+ Air Raja), Ward, k=2 | 0,2929 | 0,3369 | 12,0% |

- **Silhouette** mengukur seberapa jelas sebuah wilayah lebih dekat ke kelompoknya sendiri daripada ke kelompok lain (rentang -1 sampai 1, makin besar makin baik).
- **ARI (Adjusted Rand Index)** mengukur seberapa mirip dua hasil pengelompokan (1 = identik). Di sini dipakai untuk menguji kestabilan lewat **bootstrap 200 ulangan** (`seed = 888`).
- **K-Means** (k=2) dipakai sebagai pembanding. Pada 11 wilayah hasilnya berbeda dari Ward (ARI = 0,6196), karena **Sei Jang** berada di perbatasan antarkelompok. Pada 9 wilayah hasilnya identik.
- Pada uji Januari–November 2025, model 11 wilayah berubah (Sei Jang berpindah), sedangkan model 9 wilayah tetap.

## 3. Data

| Item | Keterangan |
|---|---|
| Sumber | Laporan kunjungan pasien Puskesmas Sei Lekop (data sekunder, dengan izin Puskesmas) |
| Bentuk awal | 34 berkas Excel, 24 kolom per berkas, 30.143 baris |
| Periode | Januari–awal Desember 2025 |
| Setelah deduplikasi | **30.008 catatan kunjungan** dari 9.489 pasien unik |
| Kunjungan klinis (punya kode penyakit A–T) | 14.129 pada 11 wilayah |
| Baris diagnosis | 17.691 pada 11 wilayah |

**Privasi.** Data mentah sudah **disamarkan secara konsisten** (nama, NIK, nomor rekam medis, alamat, nama ayah, dan nomor asuransi diganti kode, misalnya `P0001`; kode yang sama selalu untuk pasien yang sama). Analisis memakai tingkat kelurahan/desa, bukan alamat, RT/RW, atau koordinat. **Data mentah tidak disertakan di repo ini.** Hanya data siap mining (tanpa pengenal pasien) yang disertakan.

## 4. Alur Project (CRISP-DM)

1. **Business Understanding.** Menentukan masalah (pola penyakit antarwilayah belum terlihat jelas) dan tujuan (mengelompokkan wilayah yang komposisi diagnosisnya mirip).
2. **Data Understanding / EDA.** Memeriksa jumlah kunjungan per bulan dan per wilayah, kode diagnosis terbanyak, dan kualitas data. Temuan utamanya:
   - 135 catatan terunduh dua kali (semuanya 6 Oktober 2025) dan sudah dikeluarkan.
   - 165 catatan tanpa wilayah asal.
   - 678 catatan tanpa kode diagnosis valid.
   - 4.041 catatan punya lebih dari satu kode diagnosis.
   - Jumlah kunjungan sangat timpang: sebagian besar dari Sungai Lekop dan Gunung Lengkuas (distribusi *skewed*), sehingga memakai **proporsi** lebih tepat daripada jumlah mentah.
3. **Preprocessing.**
   - *Data selection:* hanya tahun 2025, dan 11 wilayah yang punya minimal 30 kunjungan.
   - Penyeragaman nama wilayah dan pemisahan kode diagnosis majemuk (satu kunjungan bisa punya beberapa kode).
   - Kode Z (layanan kesehatan), U, dan V–Y (penyebab luar) tidak dihitung sebagai fitur penyakit.
   - *Feature engineering:* mengubah data per kunjungan menjadi **proporsi 11 kategori ICD-10 per wilayah** (J, K, I, E, R, M, L, S–T, A–B, H00–H59, dan Lainnya).
4. **Modeling.** Akar kuadrat proporsi (**transformasi Hellinger**), jarak Euclidean, lalu **Ward hierarchical clustering**. Jumlah cluster diuji untuk k = 2 sampai 5.
5. **Evaluation.** Silhouette, Davies–Bouldin, ARI, bootstrap, dan perbandingan dengan K-Means.
6. **Deployment.** Dashboard web offline (HTML, CSS, JavaScript) untuk melihat hasil clustering.

## 5. Dashboard

Dashboard berjalan **sepenuhnya di komputer pengguna, tanpa server dan tanpa internet**. Fiturnya:

- memilih skenario **11 wilayah** (utama) atau **9 wilayah** (pembanding),
- memilih jumlah cluster **k = 2 sampai 5**,
- melihat silhouette, anggota cluster, dan profil diagnosis tiap cluster,
- melihat **peta cluster** dua dimensi (posisi titik dihitung dengan PCA, hanya untuk visualisasi),
- mengunduh hasil dalam bentuk CSV.

Wilayah dengan kurang dari 50 kunjungan klinis diberi penanda **"Sampel terbatas"**.

**Cara membuka:** buka `Aplikasi/JALANKAN_DASHBOARD.html` di peramban (Chrome/Edge/Firefox). Tidak perlu instalasi.

Hasil hitung versi JavaScript sudah dicocokkan dengan Python (scikit-learn): delapan skor silhouette sama sampai empat desimal, dan koordinat PCA selisihnya di bawah 1e-15.

## 6. Struktur Repo

```
.
├── Aplikasi/                  Dashboard web offline (index.html, app.js, model.js, data_model.js, ...)
├── Data_Siap_Mining/          Data hasil preprocessing (tanpa pengenal pasien)
│   ├── Master_Kunjungan_Anonim.csv            30.008 kunjungan, 1 baris = 1 kunjungan
│   ├── Data_Siap_Mining_Pecah_Baris.csv       17.876 baris diagnosis, 1 baris = 1 kode ICD-3 klinis
│   ├── Matriks_Frekuensi_{9,11,12}.csv        jumlah baris diagnosis per wilayah dan kategori
│   └── Matriks_Proporsi_{9,11,12}.csv         proporsi kategori (masukan untuk Ward clustering)
├── Skrip/
│   ├── Pipeline_Pengolahan.py                 mengolah 34 berkas mentah, menghitung bootstrap
│   ├── Bangun_Model_PerDiagnosis.py           membuat matriks, Ward, K-Means, tabel pengujian
│   └── Buat_Gambar_Laporan.py                 membuat grafik dari hasil_model.json
├── VALIDASI_MODEL.py          Uji kesesuaian matriks, Python, dan JavaScript
├── UJI_PCA_PETA.py            Uji koordinat peta dashboard terhadap scikit-learn
└── README.md
```

Angka `9`, `11`, `12` pada nama file adalah **jumlah wilayah**: 11 = model utama, 9 = pembanding (minimal 30 kunjungan klinis), 12 = 11 wilayah + Air Raja (uji sensitivitas).

## 7. Cara Menjalankan Ulang

Kebutuhan: Python 3 dengan `pandas`, `numpy`, `scipy`, `scikit-learn`, dan `matplotlib` (`openpyxl` untuk membaca berkas Excel mentah).

```bash
pip install pandas numpy scipy scikit-learn matplotlib openpyxl
```

Jalankan dari folder utama repo:

```bash
# 1. (Opsional) mengolah ulang dari 34 berkas mentah. Data mentah tidak ada di repo ini.
python Skrip/Pipeline_Pengolahan.py <folder_data_mentah> --bootstrap

# 2. Membangun model dan tabel pengujian dari data siap mining
python Skrip/Bangun_Model_PerDiagnosis.py .

# 3. Membuat grafik
python Skrip/Buat_Gambar_Laporan.py .

# 4. Validasi konsistensi matriks Python dan JavaScript
python VALIDASI_MODEL.py
```

Langkah 2–4 bisa dijalankan hanya dengan data di folder `Data_Siap_Mining/`.

## 8. Keterbatasan

- Jumlah unit wilayah kecil (11) dan jumlah kunjungan antarwilayah sangat timpang.
- Tiga wilayah di Cluster 2 hanya punya sekitar 30 kunjungan klinis masing-masing, dan keanggotaan **Sei Jang tidak stabil**.
- Data dihitung per **kunjungan**, bukan per pasien, jadi satu pasien bisa menyumbang banyak catatan.
- Tidak ada data jumlah penduduk sebagai pembagi, dan periode data tidak penuh setahun (Desember tidak lengkap).
- Belum ada validasi pengguna akhir oleh petugas Puskesmas.
- Karena itu, hasil **tidak boleh** dipakai untuk mendiagnosis pasien, memprediksi penyakit, atau menyimpulkan risiko kesehatan suatu wilayah.

## 9. Saran Pengembangan

1. Memakai data satu tahun penuh atau lebih, dan memastikan tidak terpotong batas 1.000 baris per berkas.
2. Memakai satuan wilayah yang lebih kecil (RT yang disamarkan) bila Puskesmas berkenan dan privasi terjamin.
3. Menambahkan data jumlah penduduk per wilayah.
4. Melakukan uji penerimaan pengguna (*user acceptance test*) bersama Puskesmas.

---

© Project Data Mining Course 2026, Universitas Maritim Raja Ali Haji
