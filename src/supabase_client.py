"""Helper minimal untuk integrasi Supabase.

Tujuan file ini:
- Menyediakan client Supabase jika environment variable tersedia.
- Menyediakan fungsi fetch DataFrame untuk tabel inflasi dan BI-7Day-RR.
- (Opsional) Menyediakan fungsi fetch untuk kurs JISDOR.

Catatan:
- Jika SUPABASE_URL / SUPABASE_ANON_KEY tidak di-set, fungsi fetch mengembalikan None.
- Kolom akan dinormalisasi ke format yang dipakai modul UI:
  - Inflasi: Provinsi, Tahun, Bulan, Inflasi (%)
  - BI: Tanggal, BI-7Day-RR
  - JISDOR: Tanggal, Kurs
"""

from __future__ import annotations

import os
from typing import Optional


def _get_config_value(key: str) -> Optional[str]:
    """Ambil konfigurasi dari st.secrets jika ada, lalu fallback ke env var."""
    try:
        import streamlit as st

        # st.secrets bersifat dict-like
        if key in st.secrets:
            value = st.secrets.get(key)
            return None if value is None else str(value).strip()
    except Exception:
        # Streamlit belum siap / tidak ada secrets
        pass

    value = os.getenv(key)
    return None if value is None else str(value).strip()


def _get_fetch_limit(default: int = 5000) -> int:
    raw = _get_config_value("SUPABASE_FETCH_LIMIT")
    if not raw:
        return default
    try:
        val = int(raw)
        return max(1, val)
    except Exception:
        return default


def get_supabase_client():
    """Buat Supabase client; return None jika belum dikonfigurasi."""
    url = _get_config_value("SUPABASE_URL")
    key = _get_config_value("SUPABASE_ANON_KEY")
    if not url or not key:
        # Load .env file dari root project
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            # Coba beberapa path yang mungkin
            paths_to_try = [
                Path(__file__).resolve().parents[1] / ".env",  # src/. -> .env
                Path(".env"),  # Current working directory
                Path(__file__).resolve().parent.parent / ".env",  # src/ -> .env
            ]
            
            for path in paths_to_try:
                if path.exists():
                    load_dotenv(path)
                    print(f"Loaded .env from: {path}")
                    break
            else:
                print("No .env file found")
        except Exception as e:
            print(f"Failed to load .env: {e}")
        url = _get_config_value("SUPABASE_URL")
        key = _get_config_value("SUPABASE_ANON_KEY")
        if not url or not key:
            return None

    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def _fetch_table_data(table: str, columns: str = "*", limit: Optional[int] = None):
    client = get_supabase_client()
    if client is None:
        return None

    if limit is None:
        limit = _get_fetch_limit()

    try:
        resp = client.table(table).select(columns).limit(limit).execute()
        return resp.data
    except Exception as e:
        print(f"Fetch error: {e}")
        return None


def fetch_inflasi_df():
    """Fetch data inflasi dari Supabase dan normalisasi kolom.

    Mengembalikan pandas.DataFrame atau None.
    """
    table = _get_config_value("SUPABASE_INFLASI_TABLE") or "inflasi"
    data = _fetch_table_data(table)
    if not data:
        return None

    try:
        import pandas as pd

        df = pd.DataFrame(data)
        if df.empty:
            return None

        # Normalisasi nama kolom (support berbagai gaya penamaan)
        rename_map = {}
        for col in df.columns:
            low = str(col).strip().lower()

            if low in {"provinsi", "province"}:
                rename_map[col] = "Provinsi"
            elif low in {"tahun", "year"}:
                rename_map[col] = "Tahun"
            elif low in {"bulan", "month"}:
                rename_map[col] = "Bulan"
            elif low in {
                "inflasi",
                "inflasi_persen",
                "inflasi_percent",
                "inflation",
                "inflation_percent",
                "inflation_%",
                "inflasi(%)",
                "inflasi (%)",
            }:
                rename_map[col] = "Inflasi (%)"

        df = df.rename(columns=rename_map)

        required = ["Provinsi", "Tahun", "Bulan", "Inflasi (%)"]
        if not all(col in df.columns for col in required):
            return None

        df = df[required].copy()

        # Normalisasi nama provinsi (handle uppercase dulu, baru title case)
        # Perbaiki format provinsi yang tidak standar (sebelum title case)
        provinsi_mapping_pre = {
            # Format uppercase ke format standar
            "ACEH": "Aceh",
            "BALI": "Bali",
            "BANTEN": "Banten",
            "BENGKULU": "Bengkulu",
            "DI YOGYAKARTA": "DI Yogyakarta",
            "DKI JAKARTA": "DKI Jakarta",
            "GORONTALO": "Gorontalo",
            "JAMBI": "Jambi",
            "JAWA BARAT": "Jawa Barat",
            "JAWA TENGAH": "Jawa Tengah",
            "JAWA TIMUR": "Jawa Timur",
            "KALIMANTAN BARAT": "Kalimantan Barat",
            "KALIMANTAN SELATAN": "Kalimantan Selatan",
            "KALIMANTAN TENGAH": "Kalimantan Tengah",
            "KALIMANTAN TIMUR": "Kalimantan Timur",
            "KALIMANTAN UTARA": "Kalimantan Utara",
            "KEPULAUAN BANGKA BELITUNG": "Bangka Belitung",
            "KEPULAUAN RIAU": "Kepulauan Riau",
            "LAMPUNG": "Lampung",
            "MALUKU": "Maluku",
            "PAPUA BARAT DAYA": "Papua Barat Daya",
        }
        
        df["Provinsi"] = df["Provinsi"].replace(provinsi_mapping_pre)
        
        # Baru kemudian title case untuk yang lain
        df["Provinsi"] = df["Provinsi"].str.title()
        
        # Perbaiki format provinsi yang tidak standar (setelah title case)
        provinsi_mapping_post = {
            # Variasi format yang sudah teridentifikasi
            "Di Yogyakarta": "DI Yogyakarta",
            "Dki Jakarta": "DKI Jakarta", 
            "Kep. Bangka Belitung": "Bangka Belitung",
            "Kep. Riau": "Kepulauan Riau",
            
            # Format lengkap ke format standar
            "Kepulauan Bangka Belitung": "Bangka Belitung",
            "Kepulauan Riau": "Kepulauan Riau",
        }
        
        df["Provinsi"] = df["Provinsi"].replace(provinsi_mapping_post)
        
        # Hapus duplikasi provinsi dengan format yang berbeda
        # Group by Provinsi, Tahun, Bulan dan ambil rata-rata inflasi jika ada duplikat
        df = df.groupby(["Provinsi", "Tahun", "Bulan"], as_index=False)["Inflasi (%)"].mean()

        # Coerce tipe data
        df["Provinsi"] = df["Provinsi"].astype(str)
        df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")
        df["Bulan"] = pd.to_numeric(df["Bulan"], errors="coerce")
        df["Inflasi (%)"] = pd.to_numeric(df["Inflasi (%)"], errors="coerce")

        df = df.dropna(subset=["Provinsi", "Tahun", "Bulan", "Inflasi (%)"])
        df["Tahun"] = df["Tahun"].astype(int)
        df["Bulan"] = df["Bulan"].astype(int)

        # Pastikan urutan deterministik (penting untuk metrik 'terkini' / head-tail)
        df = df.sort_values(["Tahun", "Bulan", "Provinsi"]).reset_index(drop=True)
        return df
    except Exception:
        return None


def fetch_bi_7day_rr_df():
    """Fetch data BI-7Day-RR dari Supabase.

    Mengembalikan DataFrame dengan kolom: Tanggal, BI-7Day-RR, atau None.
    """
    table = _get_config_value("SUPABASE_BI_TABLE") or "bi_7day_rr"
    data = _fetch_table_data(table)
    if not data:
        return None

    try:
        import pandas as pd

        df = pd.DataFrame(data)
        if df.empty:
            return None

        rename_map = {}
        for col in df.columns:
            low = str(col).strip().lower()
            if low in {"tanggal", "date", "datetime"}:
                rename_map[col] = "Tanggal"
            elif low in {
                "bi_7day_rr",
                "bi7dayrr",
                "rate",
                "bi_rate",
                "bi-7day-rr",
                "bi-7day-rr(%)",
                "bi-7day-rr %",
            }:
                rename_map[col] = "BI-7Day-RR"

        df = df.rename(columns=rename_map)

        required = ["Tanggal", "BI-7Day-RR"]
        if not all(col in df.columns for col in required):
            return None

        df = df[required].copy()
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
        df["BI-7Day-RR"] = pd.to_numeric(df["BI-7Day-RR"], errors="coerce")
        df = df.dropna(subset=["Tanggal", "BI-7Day-RR"]).reset_index(drop=True)
        return df
    except Exception:
        return None


def fetch_kurs_jisdor_df():
    """Fetch data kurs JISDOR dari Supabase.

    Mengembalikan DataFrame dengan kolom: Tanggal, Kurs, atau None.
    """
    table = _get_config_value("SUPABASE_JISDOR_TABLE") or "kurs_jisdor"
    data = _fetch_table_data(table)
    if not data:
        return None

    try:
        import pandas as pd

        df = pd.DataFrame(data)
        if df.empty:
            return None

        rename_map = {}
        for col in df.columns:
            low = str(col).strip().lower()
            if low in {"tanggal", "date", "datetime"}:
                rename_map[col] = "Tanggal"
            elif low in {"kurs", "rate", "jisdor", "kurs_jisdor"}:
                rename_map[col] = "Kurs"

        df = df.rename(columns=rename_map)
        required = ["Tanggal", "Kurs"]
        if not all(col in df.columns for col in required):
            return None

        df = df[required].copy()
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
        df["Kurs"] = pd.to_numeric(df["Kurs"], errors="coerce")
        df = df.dropna(subset=["Tanggal", "Kurs"]).reset_index(drop=True)
        return df
    except Exception:
        return None
