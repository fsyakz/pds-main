import streamlit as st
import pandas as pd
import plotly.express as px
from utils import hitung_statistik
import ui
import data_prep

def tampilkan_statistik_data(df_inflasi):
    """
    Menampilkan halaman Statistik Data
    """
    ui.page_title(
        "Statistik Inflasi",
        "Ringkasan metrik dan distribusi inflasi berdasarkan filter yang dipilih.",
    )
    
    if df_inflasi.empty:
        ui.empty_data_state(
            "Data inflasi tidak tersedia.",
            checks=["Periksa file Excel di folder `data/` atau konfigurasi Supabase"],
        )
        return

    # URL state -> session_state (sekali per session)
    ui.sync_state_from_url(
        "stats",
        keys=["stats_provinsi", "stats_tahun", "stats_view"],
    )

    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def _prep_cached(df: pd.DataFrame) -> pd.DataFrame:
        return data_prep.prep_inflasi_with_tanggal(df)

    df_all = _prep_cached(df_inflasi)
    prov_list = sorted(df_all['Provinsi'].unique())
    tahun_list = sorted(df_all['Tahun'].unique())
    tahun_default = data_prep.latest_year(df_all)
    
    with st.expander("Filter", expanded=True):
        with st.form("stats_filter"):
            col1, col2 = st.columns(2)
            with col1:
                provinsi_stats = ui.persisted_selectbox(
                    "Provinsi",
                    options=["Semua"] + prov_list,
                    key="stats_provinsi",
                    default="Semua",
                )
            with col2:
                tahun_stats = ui.persisted_selectbox(
                    "Tahun",
                    options=["Semua"] + tahun_list,
                    key="stats_tahun",
                    default=(tahun_default if tahun_default is not None else "Semua"),
                )
            st.form_submit_button("Terapkan")
    
    # Filter data
    df_stats = df_all.copy()
    
    if provinsi_stats != "Semua":
        df_stats = df_stats[df_stats['Provinsi'] == provinsi_stats]
    
    if tahun_stats != "Semua":
        try:
            tahun_i = int(tahun_stats)  # type: ignore[arg-type]
        except Exception:
            tahun_i = None
        if tahun_i is not None:
            df_stats = df_stats[df_stats['Tahun'] == tahun_i]
    
    if df_stats.empty:
        ui.empty_data_state("Tidak ada data untuk kombinasi filter tersebut.")
        return

    ui.active_filters_bar(
        items={
            "Provinsi": provinsi_stats,
            "Tahun": tahun_stats,
        },
        reset_keys=["stats_provinsi", "stats_tahun", "stats_view"],
    )

    view = ui.section_nav(
        "Tampilan",
        options=["Ringkasan", "Distribusi", "Deskriptif"],
        key="stats_view",
        default="Ringkasan",
    )

    if view == "Ringkasan":
        stats = hitung_statistik(df_stats)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rata-rata", f"{stats['rata_rata']}%")
        col2.metric("Tertinggi", f"{stats['tertinggi']}%")
        col3.metric("Terendah", f"{stats['terendah']}%")
        col4.metric("Std dev", f"{stats['standar_deviasi']}")

        st.caption(f"Jumlah baris: {ui.format_int(len(df_stats))}.")

    elif view == "Distribusi":
        fig = px.histogram(
            df_stats,
            x='Inflasi (%)',
            nbins=20,
            title="Histogram distribusi",
            labels={'count': 'Frekuensi', 'Inflasi (%)': 'Inflasi (%)'},
        )
        fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig, **ui.kw_plotly_chart())

        fig_box = px.box(
            df_stats,
            y='Inflasi (%)',
            title="Box plot",
        )
        fig_box.update_layout(margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig_box, **ui.kw_plotly_chart())

    else:  # Deskriptif
        st.dataframe(
            df_stats['Inflasi (%)'].describe().reset_index(),
            **ui.kw_full_width(st.dataframe),
        )
