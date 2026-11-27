DATA SIAP MINING - Project Penambangan Data Puskesmas Sei Lekop (Ketua: 2401020017)
Hasil pra-proses dari 34 berkas data mentah tahun 2025 yang sudah disamarkan (Mentah_2401020017). Versi 19 Nov 2026 (hitungan per diagnosis).

Master_Kunjungan_Anonim.csv   30.008 catatan kunjungan (satu baris = satu kunjungan), tanpa pengenal pasien
  kolom: id_kunjungan, bulan, tahun, kelurahan, kategori_kunjungan, kode_icd3, kelompok_diagnosis, jumlah_kode_valid, kelompok_klinis, ada_kode_klinis
Data_Siap_Mining_Pecah_Baris.csv   17.876 baris diagnosis (satu baris = satu kode ICD-3 klinis; id_kunjungan sama bila satu kunjungan punya beberapa diagnosis)
  kolom: id_kunjungan, bulan, tahun, kelurahan, kategori_kunjungan, kode_icd3, kelompok_klinis, ada_kode_klinis
  dibuat dengan: hapus ada_kode_klinis = 0, pecah kode_icd3 majemuk, buang kode Z/U/V-Y, label Neoplasma ditulis tanpa koma
Matriks_Frekuensi_11.csv / _9.csv / _12.csv   jumlah BARIS DIAGNOSIS per wilayah dan 11 kategori (tahun 2025); _12 = 11 wilayah + Air Raja (sensitivitas)
Matriks_Proporsi_11.csv / _9.csv / _12.csv    proporsi kategori (baris berjumlah 1) = fitur yang dimasukkan ke Ward clustering

Aturan hitung: 1 baris diagnosis = 1 hitungan; dua kode berbeda pada bab yang sama dalam satu kunjungan dihitung 2x.
Model: Ward hierarchical clustering pada akar kuadrat proporsi (transformasi Hellinger), k=2.
Model utama = 11 wilayah (total kunjungan >= 30, termasuk Kawal dan Sei Jang); 9 wilayah (>= 30 kunjungan klinis) = pembanding.
