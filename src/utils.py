import pandas as pd
import warnings
import os
import re
warnings.filterwarnings('ignore')

try:
    import supabase_client
except Exception:
    supabase_client = None

INFLASI_STD_COLUMNS = ['Provinsi', 'Tahun', 'Bulan', 'Inflasi (%)']

_ID_MONTH = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def _empty_inflasi_df() -> pd.DataFrame:
    """Return DataFrame kosong dengan schema standar inflasi."""
    return pd.DataFrame(columns=INFLASI_STD_COLUMNS)


def _parse_rate_percent(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("%", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _parse_periode_bulan_tahun(value) -> tuple[int | None, int | None]:
    """Parse string seperti 'Desember 2025' -> (bulan, tahun)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None
    s = str(value).strip()
    if not s:
        return None, None

    # Normal form: '<bulan> <tahun>'
    parts = s.split()
    if len(parts) >= 2:
        month_s = parts[0].strip().lower()
        year_s = parts[-1].strip()
        bulan = _ID_MONTH.get(month_s)
        try:
            tahun = int(year_s)
        except Exception:
            tahun = None
        return bulan, tahun

    return None, None


def _extract_year_from_filename(name: str) -> int | None:
    matches = re.findall(r"(19\d{2}|20\d{2})", str(name))
    if not matches:
        return None
    try:
        return int(matches[-1])
    except Exception:
        return None


def _load_inflasi_nasional_excel(path: str) -> pd.DataFrame:
    """Load `data/Data Inflasi.xlsx` -> schema standar.

    File ini umumnya berisi kolom: No, Periode, Data Inflasi (persen).
    Karena header tidak berada di baris pertama, kita baca tanpa header dan cari baris yang memuat 'Periode'.
    """
    try:
        raw = pd.read_excel(path, header=None)
    except Exception:
        return _empty_inflasi_df()

    header_idx = None
    for i in range(min(len(raw), 50)):
        row_vals = [str(v).strip().lower() for v in raw.iloc[i].tolist() if not (isinstance(v, float) and pd.isna(v))]
        if any(v == "periode" for v in row_vals) and any("inflasi" in v for v in row_vals):
            header_idx = i
            break
    if header_idx is None:
        return _empty_inflasi_df()

    # Tentukan indeks kolom periode & inflasi
    header_row = [str(v).strip() if not (isinstance(v, float) and pd.isna(v)) else "" for v in raw.iloc[header_idx].tolist()]
    periode_col = None
    inflasi_col = None
    for j, v in enumerate(header_row):
        low = v.strip().lower()
        if low == "periode":
            periode_col = j
        if "inflasi" in low:
            inflasi_col = j

    if periode_col is None or inflasi_col is None:
        return _empty_inflasi_df()

    records: list[dict] = []
    for i in range(header_idx + 1, len(raw)):
        periode = raw.iat[i, periode_col] if periode_col < raw.shape[1] else None
        val = raw.iat[i, inflasi_col] if inflasi_col < raw.shape[1] else None
        bulan, tahun = _parse_periode_bulan_tahun(periode)
        inflasi = _parse_rate_percent(val)
        if bulan is None or tahun is None or inflasi is None:
            continue
        records.append(
            {
                "Provinsi": "Nasional",
                "Tahun": tahun,
                "Bulan": bulan,
                "Inflasi (%)": inflasi,
            }
        )

    df = pd.DataFrame.from_records(records)
    if df.empty:
        return _empty_inflasi_df()
    return df


def _load_inflasi_tahunan_provinsi_excel(path: str, tahun: int | None) -> pd.DataFrame:
    """Load `Inflasi Tahunan (Y-on-Y) ... YYYY.xlsx` -> schema standar.

    Struktur umum:
    - Ada beberapa baris judul
    - Ada satu baris header bulan (Januari..Desember)
    - Kolom pertama berisi nama provinsi (mis. 'PROV ACEH')
    """
    try:
        raw = pd.read_excel(path, header=None)
    except Exception:
        return _empty_inflasi_df()

    header_idx = None
    for i in range(min(len(raw), 80)):
        row = raw.iloc[i].tolist()
        lowered = [str(v).strip().lower() for v in row if not (isinstance(v, float) and pd.isna(v))]
        if "januari" in lowered and "desember" in lowered:
            header_idx = i
            break
    if header_idx is None:
        return _empty_inflasi_df()

    # Map month name -> column index
    month_cols: dict[int, int] = {}
    header_row = raw.iloc[header_idx].tolist()
    for j, v in enumerate(header_row):
        s = str(v).strip().lower()
        if s in _ID_MONTH:
            month_cols[_ID_MONTH[s]] = j

    if len(month_cols) < 12:
        # minimal masih bisa jalan, tapi kemungkinan format berubah.
        pass

    records: list[dict] = []
    prov_col = 0
    for i in range(header_idx + 1, len(raw)):
        prov_raw = raw.iat[i, prov_col] if prov_col < raw.shape[1] else None
        if prov_raw is None or (isinstance(prov_raw, float) and pd.isna(prov_raw)):
            continue

        prov_s = str(prov_raw).strip()
        if not prov_s:
            continue

        # Banyak file memakai prefix 'PROV '
        prov = prov_s
        for prefix in ("PROV ", "Prov ", "prov "):
            if prov.startswith(prefix):
                prov = prov[len(prefix) :].strip()
                break

        for bulan, col_idx in month_cols.items():
            val = raw.iat[i, col_idx] if col_idx < raw.shape[1] else None
            if val is None or (isinstance(val, float) and pd.isna(val)):
                continue
            inflasi_num = pd.to_numeric(val, errors="coerce")
            if pd.isna(inflasi_num):
                inflasi = _parse_rate_percent(val)
            else:
                inflasi = float(inflasi_num)

            if inflasi is None:
                continue

            records.append(
                {
                    "Provinsi": prov,
                    "Tahun": int(tahun) if tahun is not None else None,
                    "Bulan": int(bulan),
                    "Inflasi (%)": float(inflasi),
                }
            )

    df = pd.DataFrame.from_records(records)
    if df.empty:
        return _empty_inflasi_df()

    # Tahun harus ada; jika tidak ada di filename, coba infer dari isi.
    if df["Tahun"].isna().any():
        inferred = _extract_year_from_filename(os.path.basename(path))
        if inferred is not None:
            df["Tahun"] = inferred

    df = df.dropna(subset=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")
    df["Bulan"] = pd.to_numeric(df["Bulan"], errors="coerce")
    df["Inflasi (%)"] = pd.to_numeric(df["Inflasi (%)"], errors="coerce")
    df = df.dropna(subset=["Tahun", "Bulan", "Inflasi (%)"])
    df["Tahun"] = df["Tahun"].astype(int)
    df["Bulan"] = df["Bulan"].astype(int)
    return df.reset_index(drop=True)


def _parse_inflasi_excel_file(path: str) -> pd.DataFrame:
    name = os.path.basename(str(path))
    if name.lower() == "data inflasi.xlsx":
        return _load_inflasi_nasional_excel(path)
    if "inflasi tahunan" in name.lower():
        year = _extract_year_from_filename(name)
        return _load_inflasi_tahunan_provinsi_excel(path, year)

    # fallback: format yang sudah punya header standar
    try:
        df = pd.read_excel(path)
        if df is None or df.empty:
            return _empty_inflasi_df()
        return normalisasi_data_inflasi(df, name)
    except Exception:
        return _empty_inflasi_df()


def baca_data_inflasi_excel() -> pd.DataFrame:
    """Load semua data inflasi dari file Excel di folder supabase/, lalu gabungkan.

    Mengembalikan DataFrame schema standar.
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'supabase')
    file_paths = [
        os.path.join(data_dir, "Inflasi_Tahunan_2024.xlsx"),
        os.path.join(data_dir, "Inflasi_Tahunan_2025.xlsx"),
    ]

    frames: list[pd.DataFrame] = []
    for path in file_paths:
        if not os.path.exists(path):
            continue
        df = _parse_inflasi_excel_file(path)
        if df is not None and not df.empty:
            frames.append(df)

    if not frames:
        out = _empty_inflasi_df()
        try:
            out.attrs["source"] = "empty"
        except Exception:
            pass
        return out

    df_all = pd.concat(frames, ignore_index=True)
    # Normalisasi tipe + dedupe key
    df_all = df_all[INFLASI_STD_COLUMNS].copy()
    df_all["Provinsi"] = df_all["Provinsi"].astype(str)
    df_all["Tahun"] = pd.to_numeric(df_all["Tahun"], errors="coerce")
    df_all["Bulan"] = pd.to_numeric(df_all["Bulan"], errors="coerce")
    df_all["Inflasi (%)"] = pd.to_numeric(df_all["Inflasi (%)"], errors="coerce")
    df_all = df_all.dropna(subset=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])
    df_all["Tahun"] = df_all["Tahun"].astype(int)
    df_all["Bulan"] = df_all["Bulan"].astype(int)

    df_all = df_all.sort_values(["Provinsi", "Tahun", "Bulan"]).drop_duplicates(
        subset=["Provinsi", "Tahun", "Bulan"], keep="last"
    )

    try:
        df_all.attrs["source"] = "excel:combined"
    except Exception:
        pass

    return df_all.reset_index(drop=True)

def baca_data_inflasi(file_path=None):
    """
    Membaca data inflasi dari file Excel
    Mendukung berbagai format data inflasi
    """
    try:
        if file_path is None:
            # 0) Coba ambil dari Supabase
            try:
                if supabase_client is not None:
                    df_sb = supabase_client.fetch_inflasi_df()
                    if df_sb is not None and not df_sb.empty:
                        try:
                            df_sb.attrs["source"] = "supabase"
                        except Exception:
                            pass
                        return df_sb
            except Exception:
                pass

            # Fallback: gabungkan semua sumber Excel yang tersedia
            return baca_data_inflasi_excel()
        
        else:
            out = _parse_inflasi_excel_file(str(file_path))
            try:
                out.attrs["source"] = f"excel:{os.path.basename(str(file_path))}"
            except Exception:
                pass
            return out
            
    except Exception:
        # Jika gagal membaca data, kembalikan DataFrame kosong
        out = _empty_inflasi_df()
        try:
            out.attrs["source"] = "empty"
        except Exception:
            pass
        return out

def normalisasi_data_inflasi(df, nama_file):
    """
    Menormalisasi data inflasi dari berbagai format
    menjadi format standar: Provinsi, Tahun, Bulan, Inflasi (% )
    """
    try:
        # Format umum - coba deteksi kolom
        kolom_mapping = {
            'provinsi': ['Provinsi', 'provinsi', 'Province', 'province'],
            'tahun': ['Tahun', 'tahun', 'Year', 'year'],
            'bulan': ['Bulan', 'bulan', 'Month', 'month'],
            'inflasi': ['Inflasi (%)', 'inflasi', 'Inflasi', 'inflation', 'Inflation (%)']
        }
        
        # Cari kolom yang sesuai
        kolom_terpilih = {}
        for key, possibilities in kolom_mapping.items():
            for col in df.columns:
                if col in possibilities:
                    kolom_terpilih[key] = col
                    break
        
        # Jika kolom minimal tidak lengkap, kembalikan DataFrame kosong
        if len(kolom_terpilih) < 4:
            return _empty_inflasi_df()
        
        # Normalisasi nama kolom
        df_normal = df[list(kolom_terpilih.values())].copy()
        df_normal.columns = ['Provinsi', 'Tahun', 'Bulan', 'Inflasi (%)']
        
        return df_normal
            
    except Exception:
        # Jika normalisasi gagal, kembalikan DataFrame kosong
        return _empty_inflasi_df()

def hitung_statistik(df):
    """
    Menghitung statistik data inflasi
    """
    if df.empty or 'Inflasi (%)' not in df.columns:
        return {
            'rata_rata': 0,
            'tertinggi': 0,
            'terendah': 0,
            'standar_deviasi': 0
        }
    
    return {
        'rata_rata': round(df['Inflasi (%)'].mean(), 2),
        'tertinggi': round(df['Inflasi (%)'].max(), 2),
        'terendah': round(df['Inflasi (%)'].min(), 2),
        'standar_deviasi': round(df['Inflasi (%)'].std(), 2)
    }
