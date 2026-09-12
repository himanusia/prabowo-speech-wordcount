# Research pack — Prabowo speech corpus

Everything below is derived from Indonesian YouTube caption tracks, deduplicated by speech
event. Generated from `data/expanded/analysis.json`; no raw caption text is included.

## Headline

```text
pidato (event unik)      46
unggahan (upload)        80
token                    109.197
kata unik (surface form) 9.247
rentang                  2025-02-10 → 2026-09-09
```

Tier sumber: full_media 29, official 11, media 6

Sebaran per tahun: 2025 8 pidato, 2026 38 pidato

Sebaran per bulan:

```text
2025-02   1 pidato
2025-04   1 pidato
2025-07   1 pidato
2025-08   2 pidato
2025-09   1 pidato
2025-10   1 pidato
2025-12   1 pidato
2026-01   1 pidato
2026-02   2 pidato
2026-03   2 pidato
2026-05   6 pidato
2026-06   7 pidato
2026-07  11 pidato
2026-08   7 pidato
2026-09   2 pidato
```

## Distribusi token per pidato

```text
terpanjang    11989
median         1619
terpendek        68
5 teratas     37068  (33.9% dari seluruh token)
```

Pidato terpanjang:

  2026-08-14   11989  [FULL] Pidato Presiden Prabowo-Puan Maharani soal RAPBN 2027
  2026-08-14    7750  [FULL] Pidato Presiden Prabowo di Sidang Tahunan MPR RI 2026
  2026-02-02    6257  [FULL] PIDATO PRESIDEN PRABOWO DI RAKORNAS PEMERINTAH PUSAT 
  2026-07-20    5868  [FULL] Pidato Presiden Prabowo Di Sidang Kabinet Paripurna |
  2025-09-29    5204  [FULL] Pidato Lengkap Presiden Prabowo di Munas Ke-VI PKS | 

Implikasi: frekuensi kata agregat sebagian besar ditentukan lima pidato panjang. Untuk klaim
tentang Prabowo secara umum, pakai `per 1.000 token` dan kolom `speech_count`, bukan total.

## Kata isi teratas (fungsi kata dan pronomina dibuang)

```text
  1. indonesia           1152   10.55/1k  45/46 pidato
  2. rakyat               808    7.40/1k  42/46 pidato
  3. harus                724    6.63/1k  43/46 pidato
  4. negara               593    5.43/1k  42/46 pidato
  5. tahun                586    5.37/1k  42/46 pidato
  6. bangsa               585    5.36/1k  45/46 pidato
  7. enggak               456    4.18/1k  31/46 pidato
  8. ketua                387    3.54/1k  32/46 pidato
  9. menteri              371    3.40/1k  38/46 pidato
 10. presiden             356    3.26/1k  43/46 pidato
 11. apa                  296    2.71/1k  31/46 pidato
 12. mau                  294    2.69/1k  34/46 pidato
 13. seluruh              284    2.60/1k  43/46 pidato
 14. republik             272    2.49/1k  40/46 pidato
 15. hadir                270    2.47/1k  40/46 pidato
 16. satu                 243    2.23/1k  38/46 pidato
 17. punya                230    2.11/1k  35/46 pidato
 18. pak                  229    2.10/1k  27/46 pidato
 19. dia                  228    2.09/1k  27/46 pidato
 20. dunia                227    2.08/1k  38/46 pidato
 21. orang                223    2.04/1k  32/46 pidato
 22. boleh                212    1.94/1k  36/46 pidato
 23. wakil                206    1.89/1k  33/46 pidato
 24. masih                206    1.89/1k  38/46 pidato
 25. mungkin              204    1.87/1k  38/46 pidato
 26. umum                 200    1.83/1k  26/46 pidato
 27. ingin                199    1.82/1k  38/46 pidato
 28. pemerintah           198    1.81/1k  35/46 pidato
 29. bukan                191    1.75/1k  35/46 pidato
 30. nanti                186    1.70/1k  31/46 pidato
 31. hormati              183    1.68/1k  38/46 pidato
 32. ekonomi              181    1.66/1k  33/46 pidato
 33. benar                178    1.63/1k  33/46 pidato
 34. luar                 176    1.61/1k  34/46 pidato
 35. selalu               167    1.53/1k  38/46 pidato
 36. terus                159    1.46/1k  35/46 pidato
 37. iya                  158    1.45/1k  31/46 pidato
 38. tni                  155    1.42/1k  32/46 pidato
 39. waktu                155    1.42/1k  32/46 pidato
 40. mana                 155    1.42/1k  36/46 pidato
```

## Sinyal topik (leksikal, per 1.000 token)

```text
nasional_dan_identitas    32.54/1k   46/46 pidato
ekonomi                    5.91/1k   41/46 pidato
pangan                     4.10/1k   33/46 pidato
kesehatan_dan_gizi         3.94/1k   41/46 pidato
pertahanan_dan_keamanan    3.83/1k   37/46 pidato
tata_kelola                3.67/1k   39/46 pidato
pendidikan                 2.60/1k   33/46 pidato
mbg                        0.72/1k   17/46 pidato
```

Kategori boleh tumpang tindih. Ini proksi leksikal, bukan klasifikasi: `anak` selalu masuk
`kesehatan_dan_gizi` walau konteksnya bukan program gizi.

## Framing pronomina

```text
saya      2.729   24.99/1k  45/46 pidato
kita      4.167   38.16/1k  46/46 pidato
kami        177    1.62/1k  25/46 pidato
mereka      313    2.87/1k  35/46 pidato
```

`kita` 4167 vs `saya` 2729. Di sampel awal 10 video keduanya
hampir seri; di korpus ini `kita` menang jelas. Klaim "Prabowo personalis" tidak bertahan di
sampel besar.

## MBG

```text
MBG eksak (token)         54
sinyal kebijakan total    79
pidato memuat MBG         18 dari 46 (39%)
```

| tanggal | MBG eksak | sinyal | ambigu | pidato |
|---|---:|---:|---:|---|
| 2025-07-01 | 0 | 2 | 0 | Full Pidato Presiden Prabowo di Upacara Peringatan k |
| 2025-09-29 | 0 | 4 | 0 | [FULL] Pidato Lengkap Presiden Prabowo di Munas Ke-V |
| 2026-01-05 | 7 | 11 | 0 | (FULL) Pidato Presiden Prabowo di Perayaan Natal Nas |
| 2026-02-02 | 8 | 11 | 0 | [FULL] PIDATO PRESIDEN PRABOWO DI RAKORNAS PEMERINTA |
| 2026-05-01 | 4 | 5 | 0 | Pidato Presiden Prabowo pada Peringatan Hari Buruh I |
| 2026-05-16 | 9 | 9 | 0 | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PE |
| 2026-06-01 | 0 | 1 | 0 | FULL Pidato Prabowo di Upacara Hari Lahir Pancasila |
| 2026-06-03 | 0 | 3 | 0 | Pidato Presiden RI pada Acara Building Indonesia's F |
| 2026-06-24 | 4 | 4 | 0 | [FULL] Pidato Prabowo di PNKT XVII 2026: Australia M |
| 2026-07-01 | 1 | 2 | 0 | FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum |
| 2026-07-10 | 7 | 7 | 0 | Full Pidato Presiden Prabowo di Lombok, MBG KITA LAN |
| 2026-07-20 | 2 | 3 | 0 | [FULL] Pidato Presiden Prabowo Di Sidang Kabinet Par |
| 2026-07-24 | 0 | 0 | 1 | Pidato Prabowo di Harlah PKB |
| 2026-07-31 | 0 | 1 | 0 | [Breaking News] Pidato Presiden Prabowo di Pertemuan |
| 2026-08-14 | 5 | 7 | 0 | [FULL] Pidato Presiden Prabowo-Puan Maharani soal RA |
| 2026-08-14 | 4 | 5 | 0 | [FULL] Pidato Presiden Prabowo di Sidang Tahunan MPR |
| 2026-08-27 | 3 | 3 | 0 | [FULL] Pidato Presiden Prabowo Hadiri Muktamar ke-35 |
| 2026-09-09 | 0 | 1 | 0 | Pidato Lengkap Presiden Prabowo di HUT ke 25 Partai  |

Sinyal = `MBG` eksak, frasa `makan bergizi gratis`, `makan` + `bergizi` dalam satu caption,
atau konteks SPPG. Kolom ambigu menandai akronim yang bukan program, misalnya lelucon
"MBG singkatan Mas Bahlil ganteng" di Harlah PKB. Jadi angka eksak itu lantai, bukan plafon.

## Daftar pidato

| tanggal | token | kata unik | tier | MBG | judul |
|---|---:|---:|---|---:|---|
| 2025-02-10 | 1465 | 551 | full_media | 0 | (FULL) Pidato Presiden Prabowo Dalam Kongres ke-18 Muslimat  |
| 2025-04-10 | 807 | 335 | official | 0 | Pidato Kenegaraan Presiden Prabowo di Hadapan Parlemen Turki |
| 2025-07-01 | 1102 | 424 | official | 2 | Full Pidato Presiden Prabowo di Upacara Peringatan ke 79 Har |
| 2025-08-07 | 588 | 315 | official | 0 | Presiden Prabowo Hadiri KSTI Indonesia 2025 |
| 2025-08-31 | 739 | 329 | media | 0 | Pernyataan Presiden Prabowo Menyikapi Aksi Demo |
| 2025-09-29 | 5204 | 1385 | full_media | 4 | [FULL] Pidato Lengkap Presiden Prabowo di Munas Ke-VI PKS |  |
| 2025-10-24 | 236 | 144 | official | 0 | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Santri |
| 2025-12-25 | 213 | 120 | official | 0 | Presiden Prabowo Sampaikan Ucapan Selamat Hari Natal 2025, J |
| 2026-01-05 | 2952 | 830 | full_media | 11 | (FULL) Pidato Presiden Prabowo di Perayaan Natal Nasional 20 |
| 2026-02-02 | 6257 | 1619 | full_media | 11 | [FULL] PIDATO PRESIDEN PRABOWO DI RAKORNAS PEMERINTAH PUSAT  |
| 2026-02-28 | 333 | 175 | official | 0 | Sambutan Presiden Prabowo pada Perayaan Tahun Baru Imlek Nas |
| 2026-03-10 | 1388 | 559 | full_media | 0 | BREAKING NEWS - [FULL] Pidato Presiden Prabowo di Peringatan |
| 2026-03-11 | 1205 | 459 | media | 0 | Pidato Presiden Prabowo di Tasyakuran HUT ke-1 Danantara |
| 2026-05-01 | 2044 | 691 | official | 5 | Pidato Presiden Prabowo pada Peringatan Hari Buruh Internasi |
| 2026-05-13 | 2769 | 916 | full_media | 0 | BREAKING NEWS - [FULL] PIDATO PRESIDEN PRABOWO DI PENYERAHAN |
| 2026-05-16 | 3552 | 1104 | full_media | 9 | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PERESMIAN  |
| 2026-05-20 | 68 | 47 | official | 0 | Presiden Prabowo Sampaikan Pidato pada Rapat Paripurna DPR R |
| 2026-05-29 | 661 | 261 | full_media | 0 | [FULL] Pidato Presiden Prabowo: Pujian untuk Macron Hingga B |
| 2026-05-31 | 352 | 206 | official | 0 | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Tri Su |
| 2026-06-01 | 1520 | 605 | full_media | 1 | FULL Pidato Prabowo di Upacara Hari Lahir Pancasila |
| 2026-06-03 | 2386 | 730 | official | 3 | Pidato Presiden RI pada Acara Building Indonesia's Future Ge |
| 2026-06-10 | 4297 | 1246 | full_media | 0 | [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG KRIT |
| 2026-06-23 | 2358 | 795 | full_media | 0 | Pidato Lengkap Presiden Prabowo Subianto di Musyawarah Ulama |
| 2026-06-24 | 2990 | 901 | full_media | 4 | [FULL] Pidato Prabowo di PNKT XVII 2026: Australia Minta Pup |
| 2026-06-26 | 1619 | 617 | official | 0 | Pembukaan Sarasehan Kebangsaan KSTI 2026 |
| 2026-06-28 | 1137 | 462 | media | 0 | Pidato Penutupan Sarasehan Kebangsaan KSTI 2026 |
| 2026-07-01 | 1822 | 679 | full_media | 2 | FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum Tak Bol |
| 2026-07-09 | 2541 | 879 | full_media | 0 | [FULL] Pidato Prabowo Luncurkan Biodiesel B50: Indonesia Jad |
| 2026-07-10 | 3129 | 948 | full_media | 7 | Full Pidato Presiden Prabowo di Lombok, MBG KITA LANJUTKAN.. |
| 2026-07-16 | 1575 | 601 | full_media | 0 | FULL! Pidato Prabowo Resmikan Groundbreaking LNG Abadi Masel |
| 2026-07-17 | 2617 | 905 | full_media | 0 | [FULL] Pidato Presiden Prabowo di Panen Raya Tebu Serentak d |
| 2026-07-20 | 5868 | 1482 | full_media | 3 | [FULL] Pidato Presiden Prabowo Di Sidang Kabinet Paripurna | |
| 2026-07-24 | 2730 | 900 | media | 0 | Pidato Prabowo di Harlah PKB |
| 2026-07-29 | 1616 | 604 | full_media | 0 | [FULL] Pidato Presiden Prabowo di Pelantikan Pamong Praja Mu |
| 2026-07-30 | 2412 | 834 | full_media | 0 | [FULL] Pidato Prabowo di Akad Rumah Subsidi: Singgung Presta |
| 2026-07-30 | 1414 | 601 | full_media | 0 | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO SAAT RESMIKAN |
| 2026-07-31 | 2501 | 913 | media | 1 | [Breaking News] Pidato Presiden Prabowo di Pertemuan dengan  |
| 2026-08-06 | 1185 | 448 | full_media | 0 | [FULL] Pidato Prabowo Depan 150 Peneliti BRIN Soroti Pendidi |
| 2026-08-07 | 2315 | 818 | full_media | 0 | FULL! Pidato Prabowo di Peluncuran Buku Bahlil: Swasembada P |
| 2026-08-14 | 11989 | 2631 | full_media | 7 | [FULL] Pidato Presiden Prabowo-Puan Maharani soal RAPBN 2027 |
| 2026-08-14 | 7750 | 1884 | full_media | 5 | [FULL] Pidato Presiden Prabowo di Sidang Tahunan MPR RI 2026 |
| 2026-08-25 | 1388 | 576 | full_media | 0 | [FULL] PIDATO PRABOWO RESMIKAN PLTS DI BALI: BERI BINTANG LA |
| 2026-08-27 | 1697 | 675 | full_media | 3 | [FULL] Pidato Presiden Prabowo Hadiri Muktamar ke-35 NU: Sin |
| 2026-08-31 | 1595 | 645 | full_media | 0 | [FULL] PIDATO PRESIDEN PRABOWO DI PENUTUPAN MUKTAMAR KE-35 N |
| 2026-09-09 | 3238 | 973 | full_media | 1 | Pidato Lengkap Presiden Prabowo di HUT ke 25 Partai Demokrat |
| 2026-09-09 | 1573 | 632 | media | 0 | [FUUL] Sambutan Presiden Prabowo Lepas Kontingen Indonesia k |

## Batasan yang wajib dibaca sebelum mengutip angka

1. Semua caption auto-generated, bukan ground truth audio. Nama, angka, dan akronim adalah
   titik gagal yang paling sering.
2. Pemotongan jendela pidato hanya diterapkan pada 10 unggahan yang dicek manual. Sisanya
   memakai track penuh, jadi beberapa event masih membawa MC, musik, atau penutup.
3. Hitungan adalah surface form. `mbg` dan `MBG` sama setelah casefold, tapi `asing` dan
   `masing-masing` berbeda token.
4. Korpus tidak lengkap: 30 kandidat ditolak YouTube (HTTP 429), 29 belum
   dicoba, 14 tanpa track Indonesia, 3 subtitle dimatikan.
   Gap terbesar: Okt 2024 – Des 2025.
5. 46 pidato ini bukan sampel acak. Pidato panjang dan acara besar lebih mungkin muncul di
   pencarian, jadi komposisinya bias ke acara kenegaraan dan ormas besar.

## Berkas data

- `analysis.json` — sumber kebenaran: total, indeks kata, hitungan per pidato, bukti MBG
- `word-frequency.csv` — 9.247 surface form agregat + jumlah + coverage
- `word-frequency-by-event.csv` — hitungan per pidato
- `events.csv` — satu baris per pidato dengan kolom MBG
- `README.md` — metodologi dan cara rebuild
