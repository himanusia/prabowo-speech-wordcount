# Research pack — Prabowo speech corpus

Derived from Indonesian YouTube caption tracks, deduplicated by speech event and restricted to
actual speeches. Every number below comes from `data/expanded/analysis.json`; no raw caption
text is included.

```text
pidato (event unik)      67
unggahan (upload)        128
token                    153.699
kata unik (surface form) 11.630
rentang                  2024-08-27 → 2026-09-09
```

Tier sumber: full_media 39, media 16, official 12

## Sebaran per bulan

```text
2024-08   1
2024-10   2
2024-11   1
2024-12   3
2025-02   1
2025-04   1
2025-05   1
2025-06   2
2025-07   3
2025-08   3
2025-09   1
2025-10   2
2025-11   3
2025-12   2
2026-01   2
2026-02   2
2026-03   2
2026-04   1
2026-05   6
2026-06   7
2026-07  12
2026-08   7
2026-09   2
```

## Distribusi token per pidato

```text
terpanjang     7900
median         1788
terpendek        68
5 teratas     31343  (20.4% dari seluruh token)
```

Konsentrasi jauh lebih sehat daripada korpus sebelumnya (33,9% pada 46 pidato). Tidak ada satu
pidato yang mendominasi.

## Kata isi teratas (fungsi kata dan pronomina dibuang)

```text
indonesia           1688   10.98/1k  66/67
rakyat              1081    7.03/1k  63/67
harus                991    6.45/1k  64/67
bangsa               863    5.61/1k  64/67
negara               795    5.17/1k  62/67
tahun                708    4.61/1k  60/67
enggak               604    3.93/1k  49/67
menteri              548    3.57/1k  59/67
ketua                503    3.27/1k  48/67
presiden             501    3.26/1k  64/67
republik             398    2.59/1k  62/67
mau                  397    2.58/1k  53/67
seluruh              393    2.56/1k  63/67
apa                  378    2.46/1k  49/67
hadir                368    2.39/1k  61/67
satu                 346    2.25/1k  56/67
orang                325    2.11/1k  48/67
pak                  316    2.06/1k  42/67
punya                314    2.04/1k  54/67
dunia                299    1.95/1k  56/67
```

## Sinyal topik (leksikal, per 1.000 token)

```text
mbg                        0.57   24/67
pangan                     3.72   45/67
ekonomi                    5.64   60/67
pendidikan                 3.55   50/67
kesehatan_dan_gizi         3.48   61/67
tata_kelola                3.62   57/67
pertahanan_dan_keamanan    3.64   58/67
nasional_dan_identitas    32.52   67/67
```

Kategori boleh tumpang tindih. Ini proksi leksikal, bukan klasifikasi: `anak` selalu masuk
`kesehatan_dan_gizi` walau konteksnya bukan program gizi.

## Framing pronomina

```text
kita      5931   38.59/1k  67/67 pidato
saya      4096   26.65/1k  66/67 pidato
mereka     519    3.38/1k
kami       296    1.93/1k
```

`kita` menang jelas atas `saya` di seluruh rentang waktu. Arah ini stabil dari korpus 10 video,
45, dan 67 — yang berubah hanya selisihnya, bukan arahnya.

## MBG

```text
MBG eksak (token)         50
sinyal kebijakan total    88
pidato memuat MBG         25 dari 67 (37%)
```

Sinyal = `MBG` eksak, frasa `makan bergizi gratis`, `makan` + `bergizi` dalam satu caption, atau
konteks SPPG. Kasus ambigu (mis. lelucon "MBG singkatan Mas Bahlil ganteng") tidak dihitung
sebagai sinyal kebijakan, jadi angka eksak itu lantai.

## Cara transkrip diambil

Dua jalur dipakai, dan teksnya diverifikasi identik:

- **caption API** (`/api/timedtext` lewat youtube-transcript-api) untuk 84 upload pertama
- **panel transcript YouTube** (endpoint `youtubei get_panel`) untuk 58 upload sisanya

Panel dipakai karena endpoint caption memblokir IP ini dengan HTTP 429 setelah satu burst.
Validasi silang pada video `9rpZpKagShM`: API 628 snippet vs panel 255 segmen, keduanya
**15.621 karakter dan 2.362 kata**, rasio normalisasi 1.000, awal dan akhir teks sama persis.
Jadi pilihan jalur tidak mempengaruhi hitungan kata.

## Batasan yang wajib dibaca sebelum mengutip angka

1. Semua caption auto-generated, bukan ground truth audio. Nama, angka, dan akronim adalah titik
   gagal paling sering.
2. Pemotongan jendela pidato hanya diterapkan pada 10 unggahan yang dicek manual. Sisanya memakai
   track penuh, jadi beberapa event masih membawa MC, musik, atau penutup.
3. Hitungan adalah surface form. `mbg` dan `MBG` sama setelah casefold, tapi `asing` dan
   `masing-masing` berbeda token.
4. 15 kandidat tidak punya track Indonesia sama sekali (Prabowo bicara bahasa Inggris di forum
   internasional: EEF Rusia, APEC, ADF, SPIEF, forum bisnis Jepang/AS), 3 subtitle dimatikan, dan
   0 tersisa karena rate limit. Tidak ada lagi kandidat yang bisa ditarik.
5. 67 pidato ini bukan sampel acak. Pidato panjang di acara besar lebih mudah muncul di
   pencarian, jadi komposisinya bias ke acara kenegaraan dan ormas besar.
6. Kanal resmi hanya 12 dari 67. Sisanya kanal media, jadi judul dan durasi ikut apa yang
   diunggah kanal tersebut.

## Berkas data

- `analysis.json` — sumber kebenaran
- `word-frequency.csv` — 11.630 surface form agregat
- `word-frequency-by-event.csv` — hitungan per pidato
- `events.csv` — satu baris per pidato dengan kolom MBG
- `README.md` — metodologi dan cara rebuild
