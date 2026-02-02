import streamlit as st
import pandas as pd
import plotly.express as px
from utils import hitung_statistik
import ui
import data_prep
from supabase_client import fetch_bi_7day_rr_df, fetch_kurs_jisdor_df

def tampilkan_dashboard_utama(df_inflasi):
    """
    Menampilkan halaman Dashboard Utama dengan gabungan inflasi dan BI
    """
    ui.page_title(
        "Dashboard Utama",
        "Ringkasan lengkap inflasi, data BI-7Day-RR, dan Kurs JISDOR.",
    )

    def _goto(page_label: str) -> None:
        # Navigasi aman: jangan langsung set session_state[app_page] setelah widget dibuat.
        ui.request_navigation(page_label, key="app_page")

    # Load data BI dan Kurs
    try:
        import bi_data
        with st.spinner("Memuat data BI..."):
            df_bi = bi_data.baca_data_bi()
    except Exception:
        df_bi = None
    
    try:
        import kurs_data
        with st.spinner("Memuat data Kurs..."):
            df_kurs = kurs_data.baca_data_kurs()
    except Exception:
        df_kurs = None
    
    data_ready_inflasi = df_inflasi is not None and not df_inflasi.empty
    data_ready_bi = df_bi is not None and not df_bi.empty
    data_ready_kurs = df_kurs is not None and not df_kurs.empty
    
    if not data_ready_inflasi and not data_ready_bi and not data_ready_kurs:
        ui.empty_data_state(
            "Data belum tersedia.",
            checks=[
                "File CSV tersedia di folder `data_dummy/`",
                "Atau Supabase sudah dikonfigurasi",
            ],
        )
        return

    # --- Dashboard Gabungan ---
    st.subheader("Ringkasan Data")
    
    # Metrics untuk inflasi
    if data_ready_inflasi:
        @st.cache_data(ttl=60 * 60, show_spinner=False)
        def _prep_cached(dfi: pd.DataFrame) -> pd.DataFrame:
            return data_prep.prep_inflasi_with_tanggal(dfi)

        df_all = _prep_cached(df_inflasi)
        
        try:
            tahun_min = int(df_all['Tahun'].min())
            tahun_max = int(df_all['Tahun'].max())
        except Exception:
            tahun_min, tahun_max = None, None

        prov_n = int(df_all['Provinsi'].nunique()) if 'Provinsi' in df_all.columns else 0
        row_n = int(len(df_all))

        try:
            dmin = pd.to_datetime(df_all['Tanggal']).min().date()
            dmax = pd.to_datetime(df_all['Tanggal']).max().date()
            date_range = f"{dmin:%Y-%m-%d} – {dmax:%Y-%m-%d}"
        except Exception:
            date_range = "-"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status Inflasi", "Tersedia")
        c2.metric("Data Inflasi", ui.format_int(row_n))
        c3.metric("Provinsi", ui.format_int(prov_n))
        with c4:
            st.caption("Rentang Tanggal")
            st.text(date_range)
    
    # Metrics untuk BI
    if data_ready_bi:
        bi_row_n = int(len(df_bi))
        try:
            bi_dmin = df_bi['Tanggal'].min().date()
            bi_dmax = df_bi['Tanggal'].max().date()
            bi_date_range = f"{bi_dmin:%Y-%m-%d} – {bi_dmax:%Y-%m-%d}"
        except Exception:
            bi_date_range = "-"
        
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Status BI", "Tersedia")
        c6.metric("Data BI", ui.format_int(bi_row_n))
        c7.metric("Rentang", f"{(df_bi['Tanggal'].max() - df_bi['Tanggal'].min()).days} hari")
        with c8:
            st.caption("Rentang BI")
            st.text(bi_date_range)

    # Metrics untuk Kurs JISDOR
    if data_ready_kurs:
        kurs_row_n = int(len(df_kurs))
        try:
            kurs_dmin = df_kurs['Tanggal'].min().date()
            kurs_dmax = df_kurs['Tanggal'].max().date()
            kurs_date_range = f"{kurs_dmin:%Y-%m-%d} – {kurs_dmax:%Y-%m-%d}"
        except Exception:
            kurs_date_range = "-"
        
        # Get latest kurs
        latest_kurs = df_kurs.iloc[-1]['Kurs'] if not df_kurs.empty else 0
        
        c9, c10, c11, c12 = st.columns(4)
        c9.metric("Status Kurs", "Tersedia")
        c10.metric("Data Kurs", ui.format_int(kurs_row_n))
        c11.metric("Kurs Terkini", f"Rp {latest_kurs:,.0f}")
        with c12:
            st.caption("Rentang Kurs")
            st.text(kurs_date_range)

    st.divider()

    # --- Preview Charts ---
    st.subheader("Preview Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if data_ready_inflasi:
            st.markdown("**Tren Inflasi**")
            try:
                # Ambil 30 hari terakhir
                df_latest = df_all.tail(30).copy()
                fig = px.line(
                    df_latest, 
                    x='Tanggal', 
                    y='Inflasi (%)',
                    title='Inflasi (30 hari terakhir)',
                    labels={'Inflasi (%)': 'Inflasi (%)', 'Tanggal': 'Tanggal'},
                    template='plotly_white'
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Gagal memuat grafik inflasi: {e}")
        else:
            st.info("Data inflasi tidak tersedia")
    
    with col2:
        if data_ready_bi:
            st.markdown("**Tren BI-7Day-RR**")
            try:
                # Ambil 30 hari terakhir
                df_bi_latest = df_bi.tail(30).copy()
                fig = px.line(
                    df_bi_latest, 
                    x='Tanggal', 
                    y='BI-7Day-RR',
                    title='BI-7Day-RR (30 hari terakhir)',
                    labels={'BI-7Day-RR': 'BI-7Day-RR (%)', 'Tanggal': 'Tanggal'},
                    template='plotly_white'
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Gagal memuat grafik BI: {e}")
        else:
            st.info("Data BI tidak tersedia")
    
    with col3:
        if data_ready_kurs:
            st.markdown("**Tren Kurs JISDOR**")
            try:
                # Ambil 30 hari terakhir
                df_kurs_latest = df_kurs.tail(30).copy()
                fig = px.line(
                    df_kurs_latest, 
                    x='Tanggal', 
                    y='Kurs',
                    title='Kurs JISDOR (30 hari terakhir)',
                    labels={'Kurs': 'Kurs (IDR/USD)', 'Tanggal': 'Tanggal'},
                    template='plotly_white'
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Gagal memuat grafik kurs: {e}")
        else:
            st.info("Data kurs tidak tersedia")

    st.divider()
    
    # --- Preview Tables ---
    st.subheader("Preview Tabel Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if data_ready_inflasi:
            st.markdown("**Data Inflasi Terkini**")
            try:
                # Ambil 5 data terbaru
                df_preview_inflasi = df_all.tail(10).copy()
                df_preview_inflasi['Tanggal'] = df_preview_inflasi['Tanggal'].dt.strftime('%d %b %Y')
                df_preview_inflasi['Inflasi (%)'] = df_preview_inflasi['Inflasi (%)'].round(2)
                
                st.dataframe(
                    df_preview_inflasi[['Tanggal', 'Provinsi', 'Inflasi (%)']].tail(5),
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                st.error(f"Gagal memuat tabel inflasi: {e}")
        else:
            st.info("Data inflasi tidak tersedia")
    
    with col2:
        if data_ready_bi:
            st.markdown("**Data BI-7Day-RR Terkini**")
            try:
                # Ambil 5 data terbaru
                df_preview_bi = df_bi.tail(5).copy()
                df_preview_bi['Tanggal'] = df_preview_bi['Tanggal'].dt.strftime('%d %b %Y')
                df_preview_bi['BI-7Day-RR'] = df_preview_bi['BI-7Day-RR'].round(2)
                
                st.dataframe(
                    df_preview_bi[['Tanggal', 'BI-7Day-RR']],
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                st.error(f"Gagal memuat tabel BI: {e}")
        else:
            st.info("Data BI tidak tersedia")
    
    with col3:
        if data_ready_kurs:
            st.markdown("**Data Kurs JISDOR Terkini**")
            try:
                # Ambil 5 data terbaru
                df_preview_kurs = df_kurs.tail(5).copy()
                df_preview_kurs['Tanggal'] = df_preview_kurs['Tanggal'].dt.strftime('%d %b %Y')
                df_preview_kurs['Kurs'] = df_preview_kurs['Kurs'].apply(lambda x: f"Rp {x:,.0f}")
                
                st.dataframe(
                    df_preview_kurs[['Tanggal', 'Kurs']],
                    use_container_width=True,
                    hide_index=True
                )
            except Exception as e:
                st.error(f"Gagal memuat tabel kurs: {e}")
        else:
            st.info("Data kurs tidak tersedia")

    st.divider()
    
    # --- Simple Footer ---
    st.markdown("**Ringkasan lengkap inflasi, data BI-7Day-RR, dan Kurs JISDOR**")


