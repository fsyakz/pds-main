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
            day = int(day_s)
            year = int(year_s)
        except Exception:
            return pd.NaT

        if month is None:
            return pd.NaT

        return pd.Timestamp(year=year, month=month, day=day)

    return pd.to_datetime(s, errors="coerce")


def _parse_rate_percent(value: Any) -> float | None:
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

def baca_data_bi():
    try:
        try:
            if supabase_client is not None:
                df_sb = supabase_client.fetch_bi_7day_rr_df()
                if df_sb is not None and not df_sb.empty:
                    return df_sb
        except Exception:
            pass

        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset'),
            os.path.join(os.path.dirname(__file__), 'dataset'),
            'dataset',
            './dataset',
        ]
        
        for data_dir in possible_paths:
            file_path = os.path.join(data_dir, 'bi_7day_rr.csv')
            if os.path.exists(file_path):
                print(f"Loading BI data from: {file_path}")
                break
        else:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset', 'bi_7day_rr.csv')
        
        df = pd.read_csv(file_path)
        
        if len(df.columns) >= 2:
            df.columns = ['Tanggal', 'BI-7Day-RR']

            df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
            df['BI-7Day-RR'] = pd.to_numeric(df['BI-7Day-RR'], errors='coerce')
            
            df = df.dropna(subset=['Tanggal', 'BI-7Day-RR'])
            
            df = df.reset_index(drop=True)
            
            return df
        else:
            return pd.DataFrame(columns=['Tanggal', 'BI-7Day-RR'])
            
    except Exception:
        return pd.DataFrame(columns=['Tanggal', 'BI-7Day-RR'])

def tampilkan_bi_data():
    """
    Menampilkan halaman Data BI
    """
    ui.page_title(
        "Data BI-7Day-RR",
        "BI-7Day Reverse Repo Rate (BI-7Day-RR). Sumber data: Supabase (opsional) atau `data/BI-7Day-RR.xlsx`. ",
    )

    # URL state -> session_state (sekali per session)
    ui.sync_state_from_url(
        "bi",
        keys=["app_page", "bi_start", "bi_end", "bi_view"],
        coercers={
            "bi_start": ui.coerce_iso_date,
            "bi_end": ui.coerce_iso_date,
        },
    )

    st.caption(
        "Gunakan filter tanggal untuk membatasi periode. Anda bisa menyimpan tampilan, atau membagikan tautan agar rekan kerja membuka periode yang sama."
    )

    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def _load_bi_cached():
        return baca_data_bi()
    
    # Baca data (dengan feedback + cache)
    with st.spinner("Memuat data BI-7Day-RR..."):
        df_bi = _load_bi_cached()
    
    if df_bi is None or df_bi.empty:
        ui.empty_data_state(
            "Data BI-7Day-RR tidak dapat dimuat.",
            checks=[
                "Pastikan file `data/BI-7Day-RR.xlsx` tersedia",
                "Atau konfigurasi Supabase (`SUPABASE_URL` & `SUPABASE_ANON_KEY`)",
            ],
        )
        return

    # Normalisasi & sort untuk konsistensi UX
    df_bi = df_bi.copy()
    # Pastikan dtype datetime agar .dt dan .date aman
    df_bi['Tanggal'] = pd.to_datetime(df_bi['Tanggal'], errors='coerce')
    df_bi = df_bi.dropna(subset=['Tanggal']).copy()
    df_bi = df_bi.sort_values('Tanggal').reset_index(drop=True)

    min_ts = pd.to_datetime(df_bi['Tanggal'], errors='coerce').min()
    max_ts = pd.to_datetime(df_bi['Tanggal'], errors='coerce').max()
    if pd.isna(min_ts) or pd.isna(max_ts):
        ui.empty_data_state("Tanggal pada data BI tidak valid.")
        return
    min_date = pd.Timestamp(min_ts).date()
    max_date = pd.Timestamp(max_ts).date()

    # Stabilkan nilai date input jika datang dari URL (clamp ke min/max)
    import datetime as _dt

    sd = st.session_state.get("bi_start")
    ed = st.session_state.get("bi_end")
    if not isinstance(sd, _dt.date) or isinstance(sd, _dt.datetime):
        sd = min_date
    if not isinstance(ed, _dt.date) or isinstance(ed, _dt.datetime):
        ed = max_date
    sd = max(min_date, min(sd, max_date))
    ed = max(min_date, min(ed, max_date))
    if sd > ed:
        sd, ed = min_date, max_date
    st.session_state["bi_start"] = sd
    st.session_state["bi_end"] = ed

    with st.expander("Filter", expanded=True):
        with st.form("bi_filter_form"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Tanggal mulai",
                    key="bi_start",
                    min_value=min_date,
                    max_value=max_date,
                )
            with col2:
                end_date = st.date_input(
                    "Tanggal selesai",
                    key="bi_end",
                    min_value=min_date,
                    max_value=max_date,
                )
            st.form_submit_button("Terapkan")

    # Streamlit date_input stubs menggunakan union yang lebar; pastikan tipe date.
    def _as_date(v: Any, fallback: _dt.date) -> _dt.date:
        if isinstance(v, _dt.date) and not isinstance(v, _dt.datetime):
            return v
        if isinstance(v, tuple) and v and isinstance(v[0], _dt.date):
            return v[0]
        return fallback

    start_date = _as_date(start_date, sd)
    end_date = _as_date(end_date, ed)

    if end_date < start_date:
        st.error("Tanggal selesai harus lebih besar atau sama dengan tanggal mulai.")
        return

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    mask = (df_bi['Tanggal'] >= start_ts) & (df_bi['Tanggal'] <= end_ts)
    df_filtered = df_bi.loc[mask].copy()

    ui.active_filters_bar(
        items={
            "Mulai": start_date,
            "Selesai": end_date,
        },
        reset_keys=["bi_start", "bi_end", "bi_view"],
    )

    view = ui.section_nav(
        "Tampilan",
        options=["Ringkasan", "Tabel", "Visualisasi"],
        key="bi_view",
        default="Ringkasan",
    )

    if view == "Ringkasan":
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total data", ui.format_int(len(df_filtered)))

        if not df_filtered.empty:
            latest_rate = df_filtered['BI-7Day-RR'].iloc[-1]
            col2.metric("Rate terbaru", f"{latest_rate:.2f}%")

        avg_rate = df_filtered['BI-7Day-RR'].mean() if not df_filtered.empty else 0
        col3.metric("Rata-rata", f"{avg_rate:.2f}%")

        max_rate = df_filtered['BI-7Day-RR'].max() if not df_filtered.empty else 0
        col4.metric("Tertinggi", f"{max_rate:.2f}%")

        st.caption(f"Rentang data: {min_date} s/d {max_date}.")

    elif view == "Tabel":
        st.dataframe(df_filtered, height=420, **ui.kw_full_width(st.dataframe))

    elif view == "Visualisasi":

        fig_line = px.line(
            df_filtered,
            x='Tanggal',
            y='BI-7Day-RR',
            title='Tren BI-7Day-RR',
            markers=True,
        )
        fig_line.update_layout(
            title_font_size=16,
            title_x=0.5,
            xaxis_title="Tanggal",
            yaxis_title="BI-7Day-RR (%)"
        )
        st.plotly_chart(fig_line, **ui.kw_plotly_chart())

        fig_hist = px.histogram(
            df_filtered,
            x='BI-7Day-RR',
            nbins=20,
            title='Distribusi BI-7Day-RR',
        )
        fig_hist.update_layout(
            title_font_size=16,
            title_x=0.5,
            xaxis_title="BI-7Day-RR (%)",
            yaxis_title="Frekuensi"
        )
        st.plotly_chart(fig_hist, **ui.kw_plotly_chart())

def tampilkan_database_bi():
    """
    Menampilkan halaman Database BI - Interface yang sederhana dan ramah pengguna
    """
    ui.page_title(
        "Database BI",
        "Cari dan kelola data BI-7Day-RR dengan mudah.",
    )
    
    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def _load_bi_cached():
        """Load data BI dari Supabase atau file lokal"""
        try:
            # Coba ambil dari Supabase
            if supabase_client is not None:
                df_sb = supabase_client.fetch_bi_7day_rr_df()
                if df_sb is not None and not df_sb.empty:
                    return df_sb
        except Exception:
            pass
        
        # Fallback ke file lokal
        return baca_data_bi()
    
    # Baca data (dengan feedback + cache)
    with st.spinner("Memuat data BI-7Day-RR..."):
        df_bi = _load_bi_cached()
    
    if df_bi is None or df_bi.empty:
        ui.empty_data_state(
            "Data BI-7Day-RR tidak tersedia.",
            checks=[
                "Periksa file `data/BI-7Day-RR.xlsx` atau konfigurasi Supabase",
            ],
        )
        return

    # Normalisasi & sort untuk konsistensi UX
    df = df_bi.copy()
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    df = df.dropna(subset=['Tanggal']).copy()
    df = df.sort_values('Tanggal').reset_index(drop=True)

    # Extract date components untuk filter
    df['Tahun'] = df['Tanggal'].dt.year
    df['Bulan'] = df['Tanggal'].dt.month
    df['Hari'] = df['Tanggal'].dt.day

    # Get unique values untuk filter
    tahun_all = sorted(df['Tahun'].unique())
    bulan_all = sorted(df['Bulan'].unique())
    hari_all = sorted(df['Hari'].unique())

    # Simple Filter Interface
    with st.expander("Cari Data", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tahun_filter = st.selectbox(
                "Tahun",
                options=["Semua Tahun"] + tahun_all,
                key="db_bi_tahun_simple",
                index=0
            )
        
        with col2:
            bulan_filter = st.selectbox(
                "Bulan",
                options=["Semua Bulan"] + bulan_all,
                key="db_bi_bulan_simple",
                index=0
            )
        
        with col3:
            hari_filter = st.selectbox(
                "Hari",
                options=["Semua Hari"] + hari_all,
                key="db_bi_hari_simple",
                index=0
            )
        
        # Date range filter
        st.markdown("**Rentang Tanggal**")
        col4, col5 = st.columns(2)
        with col4:
            start_date = st.date_input(
                "Tanggal Mulai",
                key="db_bi_start_date",
                min_value=df['Tanggal'].min().date(),
                max_value=df['Tanggal'].max().date(),
                value=df['Tanggal'].min().date()
            )
        
        with col5:
            end_date = st.date_input(
                "Tanggal Selesai",
                key="db_bi_end_date",
                min_value=df['Tanggal'].min().date(),
                max_value=df['Tanggal'].max().date(),
                value=df['Tanggal'].max().date()
            )
        
        # Rate range filter
        st.markdown("**Rentang Rate (%)**")
        col6, col7 = st.columns(2)
        with col6:
            min_rate = st.number_input(
                "Rate Minimum",
                key="db_bi_min_rate",
                value=float(df['BI-7Day-RR'].min()),
                step=0.01,
                format="%.2f"
            )
        
        with col7:
            max_rate = st.number_input(
                "Rate Maximum",
                key="db_bi_max_rate",
                value=float(df['BI-7Day-RR'].max()),
                step=0.01,
                format="%.2f"
            )
        
        # Apply filter button
        if st.button("Terapkan Filter", use_container_width=True, type="primary"):
            st.session_state["bi_filter_applied"] = True
        else:
            if "bi_filter_applied" not in st.session_state:
                st.session_state["bi_filter_applied"] = True
    
    # Terapkan filter
    df_tampil = df.copy()

    # Filter berdasarkan tahun
    if tahun_filter != "Semua Tahun":
        df_tampil = df_tampil[df_tampil['Tahun'] == tahun_filter]
    
    # Filter berdasarkan bulan
    if bulan_filter != "Semua Bulan":
        df_tampil = df_tampil[df_tampil['Bulan'] == bulan_filter]
    
    # Filter berdasarkan hari
    if hari_filter != "Semua Hari":
        df_tampil = df_tampil[df_tampil['Hari'] == hari_filter]
    
    # Filter berdasarkan date range
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    df_tampil = df_tampil[(df_tampil['Tanggal'] >= start_ts) & (df_tampil['Tanggal'] <= end_ts)]
    
    # Filter berdasarkan rate range
    df_tampil = df_tampil[(df_tampil['BI-7Day-RR'] >= min_rate) & (df_tampil['BI-7Day-RR'] <= max_rate)]

    # Tampilkan metrics dengan design yang lebih baik
    st.markdown("### Ringkasan Data")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Data Ditemukan",
            value=f"{len(df_tampil):,}",
            delta=f"dari {len(df):,} total"
        )
    
    with col2:
        st.metric(
            label="Rentang Waktu",
            value=f"{(df_tampil['Tanggal'].max() - df_tampil['Tanggal'].min()).days} hari"
        )
    
    with col3:
        if not df_tampil.empty:
            latest_rate = df_tampil['BI-7Day-RR'].iloc[-1]
            st.metric(
                label="Rate Terbaru",
                value=f"{latest_rate:.2f}%"
            )
    
    with col4:
        if not df_tampil.empty:
            avg_rate = df_tampil['BI-7Day-RR'].mean()
            st.metric(
                label="Rata-rata",
                value=f"{avg_rate:.2f}%"
            )

    if df_tampil.empty:
        st.warning("Tidak ada data untuk kombinasi filter tersebut. Coba ubah filter Anda.")
        return

    # Tampilkan data dengan design yang lebih baik
    st.markdown("### Tabel Data")
    
    # Pagination
    col_page1, col_page2 = st.columns([1, 2])
    with col_page1:
        page_size = st.selectbox(
            "Tampilkan per halaman",
            options=[10, 25, 50, 100],
            index=1,
            key="db_bi_page_size"
        )
    
    with col_page2:
        total_rows = len(df_tampil)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        
        if total_pages > 1:
            page = st.number_input(
                "Halaman", 
                min_value=1, 
                max_value=total_pages, 
                value=1, 
                key="db_bi_page"
            )
        else:
            page = 1
    
    start = (page - 1) * page_size
    end = start + page_size

    # Prepare display dataframe dengan format yang lebih baik
    df_display = df_tampil[['Tanggal', 'BI-7Day-RR']].copy()
    df_display['Tanggal'] = df_display['Tanggal'].dt.strftime('%d %b %Y')
    df_display['BI-7Day-RR'] = df_display['BI-7Day-RR'].round(2)
    df_display.columns = ['Tanggal', 'BI-7Day-RR (%)']
    
    df_page = df_display.iloc[start:end]
    st.dataframe(df_page, height=400, use_container_width=True)

    st.caption(f"Menampilkan {start + 1:,}–{min(end, total_rows):,} dari {total_rows:,} data")

    # Download section dengan design yang lebih baik
    st.markdown("### Unduh Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df_tampil.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"data_bi_7day_rr_{len(df_tampil)}_records.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_tampil.to_excel(writer, index=False, sheet_name='Data BI-7Day-RR')
        excel_buffer.seek(0)
        
        st.download_button(
            label="Download Excel",
            data=excel_buffer,
            file_name=f"data_bi_7day_rr_{len(df_tampil)}_records.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
