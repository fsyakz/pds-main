# Analisa Inflasi dan Mata Uang

Website fullstack menggunakan Streamlit untuk analisis data inflasi Indonesia dan konversi mata uang dengan struktur modular yang terorganisir.

## 🚀 Cara Menjalankan

### 1. Install Dependencies
```bash
pip install -r config/requirements.txt
```

### 2. Jalankan Aplikasi
```bash
streamlit run src/app.py
```

Aplikasi akan otomatis terbuka di browser Anda pada `http://localhost:8501`

## 📁 Struktur Proyek

```
tubes psd/
├── src/                      # Source code utama
│   ├── __init__.py          # Python package init
│   ├── app.py               # Main application dengan routing
│   ├── utils.py             # Fungsi utility (data processing)
│   ├── styles.py            # CSS styling netral (mengikuti theme Streamlit)
│   ├── dashboard_utama.py   # Modul Dashboard Utama
│   ├── visualisasi_inflasi.py # Modul Visualisasi Data
│   ├── analisa_gis.py        # Modul Analisis GIS/Peta
│   ├── statistik_data.py     # Modul Statistik Lengkap
│   ├── database_inflasi.py   # Modul Database & Filter
│   ├── kalkulator_mata_uang.py # Modul Konversi Mata Uang
│   └── bi_data.py           # Modul Data BI-7Day-RR
├── data/                     # Data files
│   ├── Data Inflasi.xlsx
│   ├── Inflasi Tahunan (Y-on-Y) 38 Provinsi (2022=100), 2024.xlsx
│   ├── Inflasi Tahunan (Y-on-Y) 38 Provinsi (2022=100), 2025.xlsx
│   ├── Informasi Kurs Jisdor.xlsx
│   └── BI-7Day-RR.xlsx
├── config/                   # Configuration files
│   ├── requirements.txt      # Dependencies Python
│   └── .gitignore           # Git ignore rules
└── docs/                     # Documentation
    └── README.md            # Dokumentasi ini
```

## 🎯 Fitur Utama

### 1. Dashboard Utama
- Tampilan overview aplikasi dengan tema hitam & ungu
- Statistik singkat inflasi
- Hero section dengan informasi sistem
- Feature cards yang interaktif

### 2. Visualisasi Inflasi
- **Line Chart**: Tren inflasi berdasarkan waktu
- **Bar Chart**: Perbandingan inflasi per provinsi
- **Pie Chart**: Distribusi inflasi (tersedia untuk semua filter)
- Filter berdasarkan provinsi dan tahun
- Support data tahun 2025

### 3. Analisis GIS Inflasi
- Peta Indonesia dengan Plotly Scatter Map
- Warna provinsi berdasarkan tingkat inflasi
- Tooltip informasi detail
- Filter tahun dan bulan

### 4. Statistik Data
- Rata-rata inflasi
- Inflasi tertinggi dan terendah
- Standar deviasi
- Histogram dan box plot distribusi
- Statistik deskriptif lengkap

### 5. Database Inflasi
- Tabel data lengkap dengan filter
- Filter berdasarkan provinsi, tahun, dan bulan
- Export data ke CSV
- Informasi jumlah data

### 6. Kalkulator Mata Uang
- Konversi 10 mata uang internasional
- Kalkulator batch untuk multiple konversi
- Kurs referensi terhadap IDR
- Hasil konversi yang jelas

## 🎨 Desain & Tema

### Theme mengikuti Streamlit

Aplikasi menggunakan fitur bawaan Streamlit **Settings → Choose app theme** (Light/Dark/Custom).

- CSS yang disuntikkan hanya memberi *polish* aman (spacing, radius, konsistensi komponen), tanpa memaksa warna global.
- Visualisasi Plotly tidak dipaksa template tertentu agar mengikuti theme yang dipilih.

Catatan: pada halaman GIS terdapat kontrol **Basemap (Auto/Terang/Gelap)** agar peta tetap jelas di light maupun dark.

### Responsive Design
- Mobile friendly
- Touch optimized
- Consistent theme across all pages
- Smooth hover effects dan transitions

## 📊 Sumber Data

Aplikasi secara otomatis mencoba membaca file Excel yang tersedia di folder `data/`:
- `Data Inflasi.xlsx`
- `Inflasi Tahunan (Y-on-Y) 38 Provinsi (2022=100), 2024.xlsx`
- `Inflasi Tahunan (Y-on-Y) 38 Provinsi (2022=100), 2025.xlsx`
- `BI-7Day-RR.xlsx`
- `Informasi Kurs Jisdor.xlsx`

Jika file tidak tersedia atau tidak dapat dibaca, aplikasi akan menampilkan pemberitahuan bahwa data tidak tersedia.

## 🔌 Integrasi Supabase (Opsional, Minimal)

Aplikasi ini bisa mengambil data dari **Supabase** jika kredensial tersedia. Jika Supabase belum dikonfigurasi, aplikasi otomatis fallback ke file Excel di folder `data/`.

### 1) Konfigurasi kredensial

Salin file `.env.example` menjadi `.env` pada root project, lalu isi nilainya:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Opsional:

- `SUPABASE_INFLASI_TABLE` (default: `inflasi`)
- `SUPABASE_BI_TABLE` (default: `bi_7day_rr`)
- `SUPABASE_JISDOR_TABLE` (default: `kurs_jisdor`)
- `SUPABASE_FETCH_LIMIT` (default: `10000`)

> Catatan keamanan:
> - Jangan pernah commit `.env` ke git.
> - Jika key Supabase pernah terlanjur masuk ke commit/public repo, anggap sudah bocor dan **wajib di-rotate**.

> Alternatif: pada deployment Streamlit, Anda juga bisa menyimpan nilai tersebut di `st.secrets` dengan key yang sama.

### 2) Skema tabel yang diharapkan

#### Tabel inflasi (default: `inflasi`)

Minimal kolom (nama kolom fleksibel; sistem mencoba mengenali beberapa variasi):

- `provinsi` (text)
- `tahun` (int)
- `bulan` (int)
- `inflasi` (numeric) — akan dipetakan ke `Inflasi (%)`

#### Tabel BI-7Day-RR (default: `bi_7day_rr`)

- `tanggal` (date/timestamp)
- `bi_7day_rr` (numeric)

#### Tabel kurs JISDOR (default: `kurs_jisdor`)

- `tanggal` (date/timestamp)
- `kurs` (numeric)

### 3) SQL seed siap pakai (skema)

Repo ini menyediakan file seed skema: `supabase/seed.sql`.
File ini hanya membuat **tabel + RLS policy SELECT** yang dibutuhkan aplikasi (tanpa mengisi data), sehingga tidak ada data berdasarkan asumsi.

Jalankan dengan salah satu cara berikut:

- **Supabase Dashboard**: SQL Editor → New query → paste isi `supabase/seed.sql` → Run.
- **psql** (kalau Anda punya connection string Postgres dari Supabase): jalankan file itu sebagai script.
- **Supabase CLI**: bila project sudah ter-link, Anda bisa menjalankan migrasi/seed sesuai workflow tim Anda (umumnya via reset DB lokal). File seed ini tetap bisa dipakai sebagai sumber SQL.

Untuk mengisi data aktual, Anda bisa mengimpor data Anda ke tabel tersebut (mis. CSV), atau menggunakan salah satu opsi berikut:

- `scripts/upload_excel_to_supabase.py` untuk mengunggah data dari folder `data/` langsung ke Supabase.
- `scripts/generate_supabase_seed_from_excel.py` untuk menghasilkan SQL seed dari folder `data/`.

## 🏗️ Struktur Data Minimal

Aplikasi mendukung berbagai format data Excel dengan kolom minimal:
- `Provinsi` (nama provinsi Indonesia)
- `Tahun` (tahun data)
- `Bulan` (bulan data, 1-12)
- `Inflasi (%)` (persentase inflasi)

## 🔧 Teknologi

- **Backend**: Python (disarankan gunakan versi yang didukung paket di `config/requirements.txt`)
- **Frontend**: Streamlit
- **Visualisasi**: Plotly
- **Data Processing**: Pandas, NumPy
- **Styling**: Custom CSS dengan Google Fonts

## 🌐 Arsitektur Modular

### Keuntungan Struktur Modular
- **Maintainability**: Setiap halaman terisolasi
- **Scalability**: Mudah menambah fitur baru
- **Team Development**: Banyak developer bisa kerja simultan
- **Reusability**: Functions dapat di-reuse

### Struktur Folder
- **`src/`**: Semua source code aplikasi
- **`data/`**: File data inflasi dan kurs
- **`config/`**: Konfigurasi dan dependencies
- **`docs/`**: Dokumentasi proyek

### Modul-Modul
- **`utils.py`**: Fungsi shared untuk data processing
- **`styles.py`**: Centralized CSS styling
- **Halaman Modules**: Setiap halaman dalam file terpisah

## 📦 Installation & Deployment

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd tubes-psd

# Install dependencies
pip install -r config/requirements.txt

# Run aplikasi
streamlit run src/app.py
```

### Production Deployment
```bash
# Install package
pip install -e .

# Jalankan
analisa-inflasi
```

## 💡 Catatan Penting

- Data kurs pada kalkulator mata uang memiliki fallback otomatis saat offline
- Koordinat peta provinsi adalah aproksimasi
- Aplikasi menggunakan error handling untuk file yang tidak dapat dibaca
- Semua teks menggunakan Bahasa Indonesia
- Tidak ada emoji dalam UI untuk tampilan profesional

## 🔧 Troubleshooting

### Error membaca file Excel
- Pastikan file Excel tidak sedang dibuka di program lain
- Cek format file (.xlsx atau .xls)
- Pastikan file berada di folder `data/`

### Error dependencies
- Jalankan `pip install -r config/requirements.txt`
- Pastikan menggunakan Python 3.8+

### Import errors
- Pastikan menjalankan dari root directory
- Gunakan `streamlit run src/app.py` bukan `python src/app.py`

### Peta tidak muncul
- Pastikan koneksi internet stabil
- Coba refresh browser

## 🤝 Kontribusi

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

**Dikembangkan dengan ❤️ menggunakan Streamlit - Arsitektur Modular Terorganisir**
