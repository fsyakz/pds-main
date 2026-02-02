"""Data preparation helpers.

Tujuan:
- Satu sumber kebenaran untuk normalisasi/typing kolom inflasi
- Mengurangi duplikasi preprocessing antar halaman
- Aman untuk data yang datang dari Excel maupun Supabase

Catatan:
- Fungsi di sini *pure* (input df -> output df) agar bisa dipakai ulang.
- Caching sebaiknya dilakukan oleh caller (halaman Streamlit) untuk menghindari
    side-effect saat modul di-import dari CLI/script.
"""

from __future__ import annotations

# NOTE: Workspace ini berjalan di Pandas.
# Di VS Code (terutama via GitHub VFS), analyzer bisa saja tidak menemukan
# environment Python sehingga muncul "import could not be resolved".
# Runtime aplikasi tetap membutuhkan paket ini.
import pandas as pd  # type: ignore[import-not-found]

INFLASI_REQUIRED_COLUMNS = ("Provinsi", "Tahun", "Bulan", "Inflasi (%)")


def has_inflasi_schema(df: pd.DataFrame) -> bool:
    return all(c in df.columns for c in INFLASI_REQUIRED_COLUMNS)


def empty_inflasi_df(extra_cols: tuple[str, ...] = ()) -> pd.DataFrame:
    cols = list(INFLASI_REQUIRED_COLUMNS) + list(extra_cols)
    return pd.DataFrame(columns=cols)


def prep_inflasi_base(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce schema inflasi: types + drop NA minimal.

    Output columns minimal: Provinsi, Tahun(int), Bulan(int), Inflasi (%)(float)
    """

    if df is None or getattr(df, "empty", True):
        return empty_inflasi_df()

    if not has_inflasi_schema(df):
        return empty_inflasi_df()

    d = df[list(INFLASI_REQUIRED_COLUMNS)].copy()

    d["Tahun"] = pd.to_numeric(d["Tahun"], errors="coerce")
    d["Bulan"] = pd.to_numeric(d["Bulan"], errors="coerce")
    d["Inflasi (%)"] = pd.to_numeric(d["Inflasi (%)"], errors="coerce")

    d = d.dropna(subset=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])  # type: ignore[arg-type]
    if d.empty:
        return empty_inflasi_df()

    # Normalize to int year/month for grouping/sorting
    d["Tahun"] = d["Tahun"].astype(int)
    d["Bulan"] = d["Bulan"].astype(int)

    return d.reset_index(drop=True)


def prep_inflasi_with_tanggal(df: pd.DataFrame) -> pd.DataFrame:
    """Prep inflasi + tambahkan kolom Tanggal (awal bulan)."""

    d = prep_inflasi_base(df)
    if d.empty:
        return empty_inflasi_df(extra_cols=("Tanggal",))

    d = d.copy()
    d["Tanggal"] = pd.to_datetime(
        d["Tahun"].astype(str)
        + "-"
        + d["Bulan"].astype(str).str.zfill(2)
        + "-01",
        errors="coerce",
    )
    d = d.dropna(subset=["Tanggal"])

    if d.empty:
        return empty_inflasi_df(extra_cols=("Tanggal",))

    return d.sort_values(["Tanggal", "Provinsi"]).reset_index(drop=True)


def latest_year(df_prepped: pd.DataFrame) -> int | None:
    if df_prepped is None or getattr(df_prepped, "empty", True):
        return None
    if "Tahun" not in df_prepped.columns:
        return None
    try:
        return int(df_prepped["Tahun"].max())
    except Exception:
        return None


def latest_month_in_year(df_prepped: pd.DataFrame, year: int) -> int | None:
    if df_prepped is None or getattr(df_prepped, "empty", True):
        return None
    if "Tahun" not in df_prepped.columns or "Bulan" not in df_prepped.columns:
        return None

    d = df_prepped[df_prepped["Tahun"] == int(year)]
    if d.empty:
        return None
    try:
        return int(d["Bulan"].max())
    except Exception:
        return None
