"""Upload data AKTUAL dari Excel (folder data/) ke Supabase.

Ini adalah "cara lain" yang tidak membuat seed SQL raksasa, tapi langsung mengisi tabel Supabase
dengan isi Excel yang memang dipakai aplikasi.

Prasyarat:
1) Jalankan schema seed dulu (sekali saja): supabase/seed.sql
2) Set env var di .env:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY (REKOMENDASI untuk insert/upsert; jangan pernah commit)
     (opsional) SUPABASE_ANON_KEY (hanya cukup kalau Anda menambah policy insert/update sendiri)

Cara jalan:
  python scripts/upload_excel_to_supabase.py

Opsi:
  python scripts/upload_excel_to_supabase.py --dry-run
  python scripts/upload_excel_to_supabase.py --batch-size 500

Catatan keamanan:
- Script ini tidak mencetak key.
- Service role key memberikan akses tinggi; simpan aman.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv

        # Pastikan selalu load .env dari root repo (tidak tergantung cwd)
        load_dotenv(str(ROOT / ".env"))
    except Exception:
        pass


def _print_env_flags() -> None:
    # Jangan pernah print nilai key; cukup boolean.
    print(
        "Env flags: SUPABASE_URL=%s; SUPABASE_SERVICE_ROLE_KEY=%s; SUPABASE_ANON_KEY=%s"
        % (bool(_env("SUPABASE_URL")), bool(_env("SUPABASE_SERVICE_ROLE_KEY")), bool(_env("SUPABASE_ANON_KEY")))
    )


def _env(key: str) -> Optional[str]:
    val = os.getenv(key)
    if val is None:
        return None
    val = str(val).strip()
    return val or None


def _get_table_names() -> tuple[str, str, str]:
    inflasi_table = _env("SUPABASE_INFLASI_TABLE") or "inflasi"
    bi_table = _env("SUPABASE_BI_TABLE") or "bi_7day_rr"
    jisdor_table = _env("SUPABASE_JISDOR_TABLE") or "kurs_jisdor"
    return inflasi_table, bi_table, jisdor_table


def _get_supabase_client():
    url = _env("SUPABASE_URL")
    service_key = _env("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = _env("SUPABASE_ANON_KEY")

    if not url:
        raise SystemExit("SUPABASE_URL belum di-set (cek .env).")

    # Untuk write/upsert, service role key paling aman & tidak perlu policy INSERT.
    key = service_key or anon_key
    if not key:
        raise SystemExit(
            "Tidak ada key Supabase untuk autentikasi. Set SUPABASE_SERVICE_ROLE_KEY (disarankan) atau SUPABASE_ANON_KEY."
        )

    if service_key is None:
        # Anon key biasanya tidak bisa insert kalau RLS aktif dan belum ada policy INSERT.
        # Kita kasih peringatan keras biar user tidak bingung.
        print(
            "WARNING: SUPABASE_SERVICE_ROLE_KEY tidak ditemukan. Anda memakai SUPABASE_ANON_KEY.\n"
            "Jika RLS aktif (seed.sql mengaktifkan), INSERT/UPSERT kemungkinan akan ditolak kecuali Anda menambah policy INSERT/UPDATE.\n"
        )

    from supabase import create_client

    return create_client(url, key)


def _load_inflasi_excel() -> pd.DataFrame:
    """Baca semua sumber inflasi dan normalisasi dengan util project."""
    import sys

    sys.path.append(str(ROOT / "src"))
    import utils  # type: ignore

    df = utils.baca_data_inflasi_excel()
    if df is None or getattr(df, "empty", True):
        return pd.DataFrame(columns=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])

    # Pastikan schema & tipe konsisten (defensif sebelum upsert)
    df = df[["Provinsi", "Tahun", "Bulan", "Inflasi (%)"]].copy()
    df["Provinsi"] = df["Provinsi"].astype(str)
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")
    df["Bulan"] = pd.to_numeric(df["Bulan"], errors="coerce")
    df["Inflasi (%)"] = pd.to_numeric(df["Inflasi (%)"], errors="coerce")
    df = df.dropna(subset=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])
    df["Tahun"] = df["Tahun"].astype(int)
    df["Bulan"] = df["Bulan"].astype(int)
    df = df.sort_values(["Provinsi", "Tahun", "Bulan"]).drop_duplicates(
        subset=["Provinsi", "Tahun", "Bulan"], keep="last"
    )
    return df.reset_index(drop=True)


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


def _parse_tanggal_indonesia(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT

    # Sudah datetime atau serial Excel yang bisa diparse
    try:
        return pd.to_datetime(value, errors="raise")
    except Exception:
        pass

    s = str(value).strip()
    if not s:
        return pd.NaT

    # Contoh umum: "17 Desember 2025"
    parts = s.split()
    if len(parts) == 3:
        day_s, month_s, year_s = parts
        month = _ID_MONTH.get(month_s.strip().lower())
        try:
            day = int(day_s)
            year = int(year_s)
        except Exception:
            return pd.NaT

        if month is None:
            return pd.NaT

        return pd.Timestamp(year=year, month=month, day=day)

    # Fallback (misal: sudah ISO atau format lain)
    return pd.to_datetime(s, errors="coerce")


def _parse_rate_percent(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    s = str(value).strip()
    if not s:
        return None

    # Contoh: "4.75 %" atau "4,75 %"
    s = s.replace("%", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _load_bi_excel() -> pd.DataFrame:
    path = DATA_DIR / "BI-7Day-RR.xlsx"
    if not path.exists():
        return pd.DataFrame(columns=["Tanggal", "BI-7Day-RR"])

    df = pd.read_excel(path, skiprows=3)

    if len(df.columns) >= 4:
        df = df.iloc[:, :4].copy()
        df.columns = ["NO", "Tanggal", "BI-7Day-RR", "Extra"]
        df = df.drop(columns=["Extra"], errors="ignore")
    elif len(df.columns) == 3:
        df = df.iloc[:, :3].copy()
        df.columns = ["NO", "Tanggal", "BI-7Day-RR"]
    else:
        return pd.DataFrame(columns=["Tanggal", "BI-7Day-RR"])

    # Buang baris header yang ikut terbaca sebagai data (mis: kolom NO berisi string "NO")
    df = df[df["NO"].astype(str).str.strip().str.lower() != "no"].copy()

    # Parse tanggal bahasa Indonesia dan rate dengan simbol persen
    df["Tanggal"] = df["Tanggal"].apply(_parse_tanggal_indonesia)  # type: ignore[call-arg]
    df["BI-7Day-RR"] = df["BI-7Day-RR"].apply(_parse_rate_percent)  # type: ignore[call-arg]
    df["BI-7Day-RR"] = pd.to_numeric(df["BI-7Day-RR"], errors="coerce")
    df = df.dropna(subset=["Tanggal", "BI-7Day-RR"]).copy()

    df = df.sort_values(["Tanggal"]).drop_duplicates(subset=["Tanggal"], keep="last")
    return df[["Tanggal", "BI-7Day-RR"]].reset_index(drop=True)


def _load_jisdor_excel() -> pd.DataFrame:
    """Load kurs JISDOR harian dari `data/Informasi Kurs Jisdor.xlsx`.

    Struktur file yang umum:
    - Sheet: "Informasi Kurs Jisdor" (bisa juga sheet pertama)
    - Header sekitar baris ke-5: NO, Tanggal, Kurs
    - Tanggal biasanya seperti "1/13/2026 12:00:00 AM" (format m/d/Y) atau tipe datetime Excel.
    """

    path = DATA_DIR / "Informasi Kurs Jisdor.xlsx"
    if not path.exists():
        return pd.DataFrame(columns=["Tanggal", "Kurs"])

    # Header terdeteksi di row ~5 (1-indexed) -> skiprows=4.
    # Gunakan sheet pertama sebagai fallback bila nama sheet berubah.
    sheet_name: str | int = "Informasi Kurs Jisdor"
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, skiprows=4)
    except Exception:
        df = pd.read_excel(path, sheet_name=0, skiprows=4)

    if df is None or getattr(df, "empty", True):
        return pd.DataFrame(columns=["Tanggal", "Kurs"])

    # Normalisasi kolom: ambil 3 kolom awal (NO, Tanggal, Kurs)
    if len(df.columns) >= 3:
        df = df.iloc[:, :3].copy()
        df.columns = ["NO", "Tanggal", "Kurs"]
    else:
        return pd.DataFrame(columns=["Tanggal", "Kurs"])

    # Buang baris header yang ikut kebaca
    df = df[df["NO"].astype(str).str.strip().str.lower() != "no"].copy()

    # Parse: tanggal + kurs
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=False)
    df["Kurs"] = pd.to_numeric(df["Kurs"], errors="coerce")
    df = df.dropna(subset=["Tanggal", "Kurs"]).copy()

    df = df.sort_values(["Tanggal"]).drop_duplicates(subset=["Tanggal"], keep="last")
    return df[["Tanggal", "Kurs"]].reset_index(drop=True)


def _df_to_inflasi_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        rows.append(
            {
                "provinsi": str(r["Provinsi"]),
                "tahun": int(r["Tahun"]),
                "bulan": int(r["Bulan"]),
                "inflasi": float(r["Inflasi (%)"]),
            }
        )
    return rows


def _df_to_bi_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        # Supabase date: kirim ISO date string
        tanggal = pd.Timestamp(r["Tanggal"]).date().isoformat()
        rows.append({"tanggal": tanggal, "bi_7day_rr": float(r["BI-7Day-RR"])})
    return rows


def _df_to_jisdor_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        tanggal = pd.Timestamp(r["Tanggal"]).date().isoformat()
        rows.append({"tanggal": tanggal, "kurs": float(r["Kurs"])})
    return rows


def _warn_unhandled_excels(handled: set[str]) -> None:
    try:
        excel_files = sorted(p.name for p in DATA_DIR.glob("*.xlsx"))
        unknown = [name for name in excel_files if name not in handled]
        if unknown:
            print("WARNING: Ada file Excel yang belum diproses oleh uploader ini:")
            for name in unknown:
                print(f"  - {name}")
    except Exception:
        pass


def _upsert_in_batches(client, table: str, rows: List[Dict[str, Any]], on_conflict: str, batch_size: int, dry_run: bool):
    if not rows:
        print(f"{table}: 0 rows (skip)")
        return

    print(f"{table}: total rows to upsert = {len(rows)}")

    if dry_run:
        print(f"DRY RUN: tidak melakukan upsert ke {table}.")
        return

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            client.table(table).upsert(batch, on_conflict=on_conflict).execute()
        except Exception as e:
            # Error paling umum: RLS menolak saat pakai anon key.
            msg = str(e)
            if "pgrst205" in msg.lower() or "schema cache" in msg.lower() or "could not find the table" in msg.lower():
                raise SystemExit(
                    f"Gagal upsert ke tabel '{table}' karena tabel belum ada di Supabase (schema cache).\n"
                    f"Langkah perbaikan:\n"
                    f"1) Jalankan SQL schema: supabase/seed.sql (di Supabase Dashboard -> SQL Editor).\n"
                    f"2) Pastikan tabel '{table}' sudah terbentuk, lalu jalankan ulang script ini.\n"
                    f"Detail error: {msg}"
                )
            if "row-level security" in msg.lower() or "42501" in msg:
                raise SystemExit(
                    f"Gagal upsert ke tabel '{table}' karena Row Level Security (RLS).\n"
                    f"Solusi yang disarankan: set SUPABASE_SERVICE_ROLE_KEY di .env (service_role key bypass RLS).\n"
                    f"Alternatif (kurang aman): tambahkan policy INSERT/UPDATE untuk role yang Anda pakai.\n"
                    f"Detail error: {msg}"
                )
            raise
        print(f"  upserted batch {i//batch_size + 1} ({len(batch)} rows)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Baca & normalisasi saja, tidak upload")
    parser.add_argument("--batch-size", type=int, default=500, help="Ukuran batch upsert (default 500)")
    args = parser.parse_args()

    _load_dotenv_if_available()
    _print_env_flags()

    inflasi_table, bi_table, jisdor_table = _get_table_names()

    print("Loading Excel from:", DATA_DIR)

    _warn_unhandled_excels(
        handled={
            "Data Inflasi.xlsx",
            "Inflasi Tahunan (Y-on-Y) 38 Provinsi (2022=100), 2024.xlsx",
            "Inflasi Tahunan (Y-on-Y) 38 Provinsi (2022=100), 2025.xlsx",
            "BI-7Day-RR.xlsx",
            "Informasi Kurs Jisdor.xlsx",
        }
    )

    df_inflasi = _load_inflasi_excel()
    df_bi = _load_bi_excel()
    df_jisdor = _load_jisdor_excel()

    print(f"Inflasi rows after normalize/dedupe: {len(df_inflasi)}")
    print(f"BI rows after normalize/dedupe: {len(df_bi)}")
    print(f"JISDOR rows after normalize/dedupe: {len(df_jisdor)}")

    if args.dry_run:
        print("DRY RUN: selesai. Tidak membuat koneksi Supabase dan tidak melakukan upsert.")
        return

    # Baru butuh client Supabase saat benar-benar upload
    client = _get_supabase_client()

    inflasi_rows = _df_to_inflasi_rows(df_inflasi)
    bi_rows = _df_to_bi_rows(df_bi)
    jisdor_rows = _df_to_jisdor_rows(df_jisdor)

    _upsert_in_batches(
        client,
        inflasi_table,
        inflasi_rows,
        on_conflict="provinsi,tahun,bulan",
        batch_size=max(1, int(args.batch_size)),
        dry_run=False,
    )

    _upsert_in_batches(
        client,
        bi_table,
        bi_rows,
        on_conflict="tanggal",
        batch_size=max(1, int(args.batch_size)),
        dry_run=False,
    )

    _upsert_in_batches(
        client,
        jisdor_table,
        jisdor_rows,
        on_conflict="tanggal",
        batch_size=max(1, int(args.batch_size)),
        dry_run=False,
    )

    print("Done.")


if __name__ == "__main__":
    main()
