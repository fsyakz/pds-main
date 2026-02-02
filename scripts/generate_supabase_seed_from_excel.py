"""Generate seed SQL Supabase dari file Excel di folder data/.

Output:
- supabase/seed_actual.sql

Tujuan:
- Seed ini menggunakan DATA AKTUAL yang ada di repo (Excel), bukan data dummy.

Catatan:
- Script ini tidak butuh koneksi ke Supabase.
- Jalankan dari root repo.

Contoh:
  python scripts/generate_supabase_seed_from_excel.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_FILE = ROOT / "supabase" / "seed_actual.sql"


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

    try:
        return pd.to_datetime(value, errors="raise")
    except Exception:
        pass

    s = str(value).strip()
    if not s:
        return pd.NaT

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

    return pd.to_datetime(s, errors="coerce")


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


def _sql_literal(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "null"
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, (float,)):
        # gunakan representasi aman
        if pd.isna(value):
            return "null"
        return str(float(value))
    # datetime/date
    if isinstance(value, (pd.Timestamp,)):
        if pd.isna(value):
            return "null"
        return "'" + value.strftime("%Y-%m-%d") + "'"

    s = str(value)
    s = s.replace("'", "''")
    return f"'{s}'"


def _chunked(rows: List[Tuple], chunk_size: int) -> Iterable[List[Tuple]]:
    for i in range(0, len(rows), chunk_size):
        yield rows[i : i + chunk_size]


def _write_header(f):
    f.write(
        """-- Seed AKTUAL Supabase untuk project pds
-- Generated from Excel files in data/ by scripts/generate_supabase_seed_from_excel.py
--
-- Cara pakai (paling mudah): Supabase Dashboard -> SQL Editor -> paste file ini -> Run
--
-- Tabel default (sesuai src/supabase_client.py):
--   - public.inflasi (provinsi, tahun, bulan, inflasi)
--   - public.bi_7day_rr (tanggal, bi_7day_rr)
--   - public.kurs_jisdor (tanggal, kurs)
--
-- Catatan keamanan: seed ini mengaktifkan RLS dan menambahkan policy SELECT publik untuk anon/auth
-- agar aplikasi bisa read via anon key. Sesuaikan jika Anda butuh akses lebih ketat.

"""
    )


def _write_schema(f):
        f.write(
                """begin;

-- =========================
-- 1) TABEL INFLASI
-- =========================
create table if not exists public.inflasi (
    id bigserial primary key,
    provinsi text not null,
    tahun int not null,
    bulan int not null check (bulan between 1 and 12),
    inflasi numeric not null,
    created_at timestamptz not null default now(),
    constraint inflasi_unique unique (provinsi, tahun, bulan)
);

create index if not exists inflasi_tahun_bulan_idx on public.inflasi (tahun, bulan);
create index if not exists inflasi_provinsi_idx on public.inflasi (provinsi);

alter table public.inflasi enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
            and tablename  = 'inflasi'
            and policyname = 'Public read inflasi'
    ) then
        create policy "Public read inflasi"
            on public.inflasi
            for select
            to anon, authenticated
            using (true);
    end if;
end $$;

-- =========================
-- 2) TABEL BI-7DAY-RR
-- =========================
create table if not exists public.bi_7day_rr (
    id bigserial primary key,
    tanggal date not null,
    bi_7day_rr numeric not null,
    created_at timestamptz not null default now(),
    constraint bi_7day_rr_unique unique (tanggal)
);

create index if not exists bi_7day_rr_tanggal_idx on public.bi_7day_rr (tanggal);

alter table public.bi_7day_rr enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
            and tablename  = 'bi_7day_rr'
            and policyname = 'Public read BI-7Day-RR'
    ) then
        create policy "Public read BI-7Day-RR"
            on public.bi_7day_rr
            for select
            to anon, authenticated
            using (true);
    end if;
end $$;

-- =========================
-- 3) TABEL KURS JISDOR
-- =========================
create table if not exists public.kurs_jisdor (
    id bigserial primary key,
    tanggal date not null,
    kurs numeric not null,
    created_at timestamptz not null default now(),
    constraint kurs_jisdor_unique unique (tanggal)
);

create index if not exists kurs_jisdor_tanggal_idx on public.kurs_jisdor (tanggal);

alter table public.kurs_jisdor enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
            and tablename  = 'kurs_jisdor'
            and policyname = 'Public read kurs_jisdor'
    ) then
        create policy "Public read kurs_jisdor"
            on public.kurs_jisdor
            for select
            to anon, authenticated
            using (true);
    end if;
end $$;

"""
        )


def _load_inflasi_from_excel() -> pd.DataFrame:
    """Baca dan gabungkan semua sumber inflasi yang dipakai app."""

    # Import util normalisasi dari src/utils.py (agar konsisten)
    import sys

    sys.path.append(str(ROOT / "src"))
    import utils  # type: ignore

    df = utils.baca_data_inflasi_excel()
    if df is None or df.empty:
        return pd.DataFrame(columns=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])

    # Bersihkan / enforce tipe
    df = df[["Provinsi", "Tahun", "Bulan", "Inflasi (%)"]].copy()
    df["Provinsi"] = df["Provinsi"].astype(str)
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")
    df["Bulan"] = pd.to_numeric(df["Bulan"], errors="coerce")
    df["Inflasi (%)"] = pd.to_numeric(df["Inflasi (%)"], errors="coerce")
    df = df.dropna(subset=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])
    df["Tahun"] = df["Tahun"].astype(int)
    df["Bulan"] = df["Bulan"].astype(int)

    # Dedupe: pakai nilai terakhir per (provinsi,tahun,bulan)
    df = df.sort_values(["Provinsi", "Tahun", "Bulan"]).drop_duplicates(
        subset=["Provinsi", "Tahun", "Bulan"], keep="last"
    )

    return df


def _load_jisdor_from_excel() -> pd.DataFrame:
    """Baca kurs JISDOR dari `data/Informasi Kurs Jisdor.xlsx`."""

    path = DATA_DIR / "Informasi Kurs Jisdor.xlsx"
    if not path.exists():
        return pd.DataFrame(columns=["Tanggal", "Kurs"])

    sheet_name: str | int = "Informasi Kurs Jisdor"
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, skiprows=4)
    except Exception:
        df = pd.read_excel(path, sheet_name=0, skiprows=4)

    if df is None or df.empty:
        return pd.DataFrame(columns=["Tanggal", "Kurs"])

    if len(df.columns) >= 3:
        df = df.iloc[:, :3].copy()
        df.columns = ["NO", "Tanggal", "Kurs"]
    else:
        return pd.DataFrame(columns=["Tanggal", "Kurs"])

    df = df[df["NO"].astype(str).str.strip().str.lower() != "no"].copy()
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce", dayfirst=False)
    df["Kurs"] = pd.to_numeric(df["Kurs"], errors="coerce")
    df = df.dropna(subset=["Tanggal", "Kurs"]).copy()
    df = df.sort_values(["Tanggal"]).drop_duplicates(subset=["Tanggal"], keep="last")
    return df[["Tanggal", "Kurs"]].reset_index(drop=True)


def _load_bi_from_excel() -> pd.DataFrame:
    """Baca BI-7Day-RR dari Excel yang dipakai app."""

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

    df = df[df["NO"].astype(str).str.strip().str.lower() != "no"].copy()
    df["Tanggal"] = df["Tanggal"].apply(_parse_tanggal_indonesia)  # type: ignore[call-arg]
    df["BI-7Day-RR"] = df["BI-7Day-RR"].apply(_parse_rate_percent)  # type: ignore[call-arg]
    df["BI-7Day-RR"] = pd.to_numeric(df["BI-7Day-RR"], errors="coerce")
    df = df.dropna(subset=["Tanggal", "BI-7Day-RR"]).copy()

    # Dedupe per tanggal
    df = df.sort_values(["Tanggal"]).drop_duplicates(subset=["Tanggal"], keep="last")

    return df[["Tanggal", "BI-7Day-RR"]].reset_index(drop=True)


def _emit_inserts_inflasi(f, df: pd.DataFrame, chunk_size: int = 500):
    f.write("-- =========================\n")
    f.write("-- SEED DATA: INFLASI (AKTUAL DARI EXCEL)\n")
    f.write("-- =========================\n\n")

    rows = [
        (
            row["Provinsi"],
            int(row["Tahun"]),
            int(row["Bulan"]),
            float(row["Inflasi (%)"]),
        )
        for _, row in df.iterrows()
    ]

    if not rows:
        f.write("-- (Tidak ada data inflasi yang berhasil dibaca dari Excel)\n\n")
        return

    for part in _chunked(rows, chunk_size):
        values_sql = ",\n".join(
            f"({_sql_literal(p)}, {_sql_literal(t)}, {_sql_literal(b)}, {_sql_literal(i)})"
            for (p, t, b, i) in part
        )
        f.write(
            "insert into public.inflasi (provinsi, tahun, bulan, inflasi) values\n"
            + values_sql
            + "\n"
            + "on conflict (provinsi, tahun, bulan) do update set inflasi = excluded.inflasi;\n\n"
        )


def _emit_inserts_bi(f, df: pd.DataFrame, chunk_size: int = 500):
    f.write("-- =========================\n")
    f.write("-- SEED DATA: BI-7DAY-RR (AKTUAL DARI EXCEL)\n")
    f.write("-- =========================\n\n")

    rows = [
        (
            pd.Timestamp(row["Tanggal"]).normalize(),
            float(row["BI-7Day-RR"]),
        )
        for _, row in df.iterrows()
    ]

    if not rows:
        f.write("-- (Tidak ada data BI-7Day-RR yang berhasil dibaca dari Excel)\n\n")
        return

    for part in _chunked(rows, chunk_size):
        values_sql = ",\n".join(
            f"({_sql_literal(d)}, {_sql_literal(r)})" for (d, r) in part
        )
        f.write(
            "insert into public.bi_7day_rr (tanggal, bi_7day_rr) values\n"
            + values_sql
            + "\n"
            + "on conflict (tanggal) do update set bi_7day_rr = excluded.bi_7day_rr;\n\n"
        )


def _emit_inserts_jisdor(f, df: pd.DataFrame, chunk_size: int = 500):
    f.write("-- =========================\n")
    f.write("-- SEED DATA: KURS JISDOR (AKTUAL DARI EXCEL)\n")
    f.write("-- =========================\n\n")

    rows = [
        (
            pd.Timestamp(row["Tanggal"]).normalize(),
            float(row["Kurs"]),
        )
        for _, row in df.iterrows()
    ]

    if not rows:
        f.write("-- (Tidak ada data kurs JISDOR yang berhasil dibaca dari Excel)\n\n")
        return

    for part in _chunked(rows, chunk_size):
        values_sql = ",\n".join(f"({_sql_literal(d)}, {_sql_literal(k)})" for (d, k) in part)
        f.write(
            "insert into public.kurs_jisdor (tanggal, kurs) values\n"
            + values_sql
            + "\n"
            + "on conflict (tanggal) do update set kurs = excluded.kurs;\n\n"
        )


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    df_inflasi = _load_inflasi_from_excel()
    df_bi = _load_bi_from_excel()
    df_jisdor = _load_jisdor_from_excel()

    with OUT_FILE.open("w", encoding="utf-8") as f:
        _write_header(f)
        _write_schema(f)
        _emit_inserts_inflasi(f, df_inflasi)
        _emit_inserts_bi(f, df_bi)
        _emit_inserts_jisdor(f, df_jisdor)
        f.write("commit;\n")

    print(f"Wrote: {OUT_FILE}")
    print(f"Inflasi rows: {len(df_inflasi)}")
    print(f"BI rows: {len(df_bi)}")
    print(f"JISDOR rows: {len(df_jisdor)}")


if __name__ == "__main__":
    main()
