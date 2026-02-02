# pds

Aplikasi **Streamlit** untuk analisis data inflasi Indonesia, visualisasi, peta (GIS), statistik, serta modul **BI-7Day-RR** dan **kalkulator mata uang**.

Dokumentasi lengkap: lihat `docs/README.md`.

## Tema (Light/Dark)

Aplikasi ini mengikuti fitur bawaan Streamlit: **Settings → Choose app theme**.

- CSS dibuat **netral** (tidak memaksa mode gelap/terang lewat session state).
- Chart Plotly juga tidak dipaksa template tertentu agar ikut tema yang dipilih.

Catatan: pada halaman GIS tersedia kontrol **Basemap (Auto/Terang/Gelap)** untuk menjaga keterbacaan peta.

## Tampilan tersimpan & tautan berbagi

Beberapa halaman menyediakan panel **Tampilan tersimpan** untuk menyimpan kombinasi filter/view.
Konfigurasi juga bisa dibagikan melalui tautan (query parameter) agar rekan kerja membuka state yang sama.

## Quickstart

1) Install dependency

- Windows / macOS / Linux:
	- Install: `pip install -r config/requirements.txt`

2) Jalankan aplikasi

- `streamlit run src/app.py`

## Data

Aplikasi akan mencoba membaca data dari:

1) **Supabase** (opsional) jika `SUPABASE_URL` dan `SUPABASE_ANON_KEY` tersedia, atau
2) file Excel di folder `data/` sebagai fallback.

 Excel yang didukung saat ini termasuk inflasi, BI-7Day-RR, dan kurs JISDOR (lihat `docs/README.md`).

Untuk konfigurasi Supabase, copy `.env.example` -> `.env` lalu isi nilainya.

## Development (opsional)

Untuk linting ringan (tanpa mem-format ulang seluruh repo), gunakan Ruff:

1) Install dev tools:
	- `pip install -r config/requirements-dev.txt`
2) Jalankan lint:
	- `ruff check .`