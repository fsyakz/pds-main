import pandas as pd
import streamlit as st
import plotly.express as px
import os
import ui
import io
from typing import Any

try:
    import supabase_client
except Exception:
    supabase_client = None


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


def _parse_tanggal_indonesia(value: Any) -> Any:
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
            year = int(year_s)
            day = int(day_s)
            return pd.to_datetime(f"{year}-{month:02d}-{day:02d}", errors="coerce")
        except Exception:
            pass

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


def baca_data_kurs():
    """
    Membaca data Kurs JISDOR dari file Excel
    """
    try:
        # 0) Coba ambil dari Supabase
        try:
            if supabase_client is not None:
                df_sb = supabase_client.fetch_kurs_jisdor_df()
                if df_sb is not None and not df_sb.empty:
                    return df_sb
        except Exception:
            pass

        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'supabase', 'Kurs_Jisdor.xlsx')
        
        # Baca file Excel dengan skip rows untuk header
        df = pd.read_excel(file_path, skiprows=3)
        
        # Rename kolom berdasarkan struktur yang terlihat
        if len(df.columns) >= 3:
            df.columns = ['NO', 'Tanggal', 'Kurs']
            
            # Buang baris header yang ikut terbaca sebagai data
            df = df[df['NO'].astype(str).str.strip().str.lower() != 'no'].copy()

            # Parse tanggal bahasa Indonesia dan kurs
            df['Tanggal'] = df['Tanggal'].apply(_parse_tanggal_indonesia)
            df['Kurs'] = df['Kurs'].apply(_parse_rate_percent)
            df['Kurs'] = pd.to_numeric(df['Kurs'], errors='coerce')
            
            # Hapus baris dengan NaN
            df = df.dropna(subset=['Tanggal', 'Kurs'])
            
            # Reset index
            df = df.reset_index(drop=True)
            
            return df
        else:
            return pd.DataFrame(columns=['Tanggal', 'Kurs'])
            
    except Exception:
        return pd.DataFrame(columns=['Tanggal', 'Kurs'])


@st.cache_data(ttl=60 * 60, show_spinner=False)
def _load_kurs_cached():
    """Load data kurs dengan cache untuk mengurangi latency & rerun."""
    return baca_data_kurs()


def tampilkan_kurs_data():
    """
    Menampilkan halaman Data Kurs JISDOR
    """
    ui.page_title(
        "Data Kurs JISDOR",
        "Kurs tengah JISDOR (Jakarta Interbank Spot Dollar Rate)."
    )

    # Load data kurs (dengan feedback + cache)
    with st.spinner("Memuat data kurs..."):
        df_kurs = _load_kurs_cached()

    if df_kurs.empty:
        st.warning("❌ Data kurs JISDOR tidak tersedia.")
        st.info("💡 Pastikan file 'Kurs_Jisdor.xlsx' ada di folder 'supabase/' atau konfigurasi Supabase benar.")
        return

    # === METRICS ===
    st.markdown("### 📊 Ringkasan Kurs")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        latest_rate = df_kurs.iloc[-1]['Kurs'] if not df_kurs.empty else 0
        st.metric("Kurs Terkini", f"Rp {latest_rate:,.0f}")
    
    with col2:
        if len(df_kurs) >= 2:
            prev_rate = df_kurs.iloc[-2]['Kurs']
            change = latest_rate - prev_rate
            change_pct = (change / prev_rate) * 100 if prev_rate != 0 else 0
            st.metric("Perubahan", f"{change:+.0f} ({change_pct:+.2f}%)")
    
    with col3:
        avg_rate = df_kurs['Kurs'].mean()
        st.metric("Rata-rata (30 hari)", f"Rp {avg_rate:,.0f}")
    
    with col4:
        max_rate = df_kurs['Kurs'].max()
        min_rate = df_kurs['Kurs'].min()
        st.metric("Range (30 hari)", f"Rp {min_rate:,.0f} - {max_rate:,.0f}")

    # === FILTER ===
    st.markdown("### 🔍 Filter Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_date = df_kurs['Tanggal'].min().date()
        max_date = df_kurs['Tanggal'].max().date()
        start_date = st.date_input("Tanggal Mulai", min_date, min_value=min_date, max_value=max_date)
    
    with col2:
        end_date = st.date_input("Tanggal Selesai", max_date, min_value=min_date, max_value=max_date)

    # Filter data berdasarkan tanggal
    filtered_df = df_kurs[
        (df_kurs['Tanggal'].dt.date >= start_date) & 
        (df_kurs['Tanggal'].dt.date <= end_date)
    ].copy()

    if filtered_df.empty:
        st.warning("❌ Tidak ada data untuk periode yang dipilih.")
        return

    # === VISUALISASI ===
    st.markdown("### 📈 Visualisasi Kurs")
    
    tab1, tab2 = st.tabs(["📊 Grafik Garis", "📋 Tabel Data"])
    
    with tab1:
        # Grafik garis
        fig = px.line(
            filtered_df, 
            x='Tanggal', 
            y='Kurs',
            title=f'Kurs JISDOR ({start_date} - {end_date})',
            labels={'Kurs': 'Kurs (IDR/USD)', 'Tanggal': 'Tanggal'},
            template='plotly_white'
        )
        
        fig.update_layout(
            hovermode='x unified',
            xaxis_title="Tanggal",
            yaxis_title="Kurs (IDR/USD)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tambahkan statistik
        st.markdown("#### 📈 Statistik Periode")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tertinggi", f"Rp {filtered_df['Kurs'].max():,.0f}")
        
        with col2:
            st.metric("Terendah", f"Rp {filtered_df['Kurs'].min():,.0f}")
        
        with col3:
            volatility = filtered_df['Kurs'].std()
            st.metric("Volatilitas", f"Rp {volatility:.0f}")
    
    with tab2:
        # Tabel data
        st.markdown("#### 📋 Data Tabel")
        
        # Format untuk display
        display_df = filtered_df.copy()
        display_df['Tanggal'] = display_df['Tanggal'].dt.strftime('%d %b %Y')
        display_df['Kurs'] = display_df['Kurs'].apply(lambda x: f"Rp {x:,.0f}")
        
        st.dataframe(
            display_df.rename(columns={
                'Tanggal': 'Tanggal',
                'Kurs': 'Kurs (IDR/USD)'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"kurs_jisdor_{start_date}_{end_date}.csv",
            mime='text/csv'
        )


def tampilkan_database_kurs():
    """
    Menampilkan halaman Database Kurs (view-only)
    """
    ui.page_title(
        "Database Kurs",
        "Data lengkap Kurs JISDOR dari database."
    )

    # Load data kurs
    with st.spinner("Memuat data kurs..."):
        df_kurs = _load_kurs_cached()

    if df_kurs.empty:
        st.warning("❌ Data kurs tidak tersedia.")
        return

    # === INFO DATABASE ===
    st.markdown("### 📊 Informasi Database")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(df_kurs):,}")
    
    with col2:
        st.metric("Tanggal Awal", df_kurs['Tanggal'].min().strftime('%d %b %Y'))
    
    with col3:
        st.metric("Tanggal Akhir", df_kurs['Tanggal'].max().strftime('%d %b %Y'))
    
    with col4:
        st.metric("Source", "Supabase/Excel")

    # === FULL DATA TABLE ===
    st.markdown("### 🗃️ Data Lengkap")
    
    # Search/Filter
    search_term = st.text_input("🔍 Cari data...", placeholder="Masukkan tanggal...")
    
    if search_term:
        filtered_df = df_kurs[
            df_kurs['Tanggal'].dt.strftime('%d %b %Y').str.contains(search_term, case=False) |
            df_kurs['Kurs'].astype(str).str.contains(search_term, case=False)
        ]
    else:
        filtered_df = df_kurs

    # Format untuk display
    display_df = filtered_df.copy()
    display_df['Tanggal'] = display_df['Tanggal'].dt.strftime('%d %b %Y')
    display_df['Kurs'] = display_df['Kurs'].apply(lambda x: f"Rp {x:,.0f}")
    
    st.dataframe(
        display_df.rename(columns={
            'Tanggal': 'Tanggal',
            'Kurs': 'Kurs (IDR/USD)'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Download full data
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Data CSV",
        data=csv,
        file_name="kurs_jisdor_full_data.csv",
        mime='text/csv'
    )
