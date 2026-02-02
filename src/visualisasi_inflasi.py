import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ui
import data_prep

def tampilkan_visualisasi_inflasi(df_inflasi):
    """
    Menampilkan halaman Visualisasi Inflasi
    """
    ui.page_title(
        "Visualisasi Inflasi",
        "Grafik tren dan perbandingan inflasi berdasarkan provinsi, tahun, dan bulan.",
    )
    
    if df_inflasi.empty:
        ui.empty_data_state(
            "Data inflasi tidak tersedia.",
            checks=["Periksa file Excel di folder `data/` atau konfigurasi Supabase"],
        )
        return

    # URL state -> session_state (sekali per session)
    ui.sync_state_from_url(
        "viz",
        keys=["viz_provinsi", "viz_tahun", "viz_tipe_grafik", "viz_view"],
    )

    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def _prep_cached(df: pd.DataFrame) -> pd.DataFrame:
        return data_prep.prep_inflasi_with_tanggal(df)

    df_all = _prep_cached(df_inflasi)

    tahun_list = sorted(df_all['Tahun'].unique())
    prov_list = sorted(df_all['Provinsi'].unique())
    tahun_default = data_prep.latest_year(df_all)

    with st.expander("Filter", expanded=True):
        with st.form("viz_filter"):
            col1, col2 = st.columns(2)
            with col1:
                provinsi = ui.persisted_selectbox(
                    "Provinsi",
                    options=["Semua"] + prov_list,
                    key="viz_provinsi",
                    default="Semua",
                )
            with col2:
                tahun = ui.persisted_selectbox(
                    "Tahun",
                    options=["Semua"] + tahun_list,
                    key="viz_tahun",
                    default=(tahun_default if tahun_default is not None else "Semua"),
                )

            tipe_grafik = ui.persisted_radio(
                "Tipe grafik",
                options=["Tren", "Perbandingan", "Komposisi"],
                key="viz_tipe_grafik",
                default="Tren",
                horizontal=True,
            )

            st.form_submit_button("Terapkan")

        ui.views_panel(
            "viz",
                keys=["app_page", "viz_provinsi", "viz_tahun", "viz_tipe_grafik", "viz_view"],
            title="Tampilan tersimpan (Visualisasi)",
            expanded=False,
        )

    df_f = df_all.copy()
    provinsi_s = str(provinsi)
    tahun_s = str(tahun)
    tahun_i: int | None = None
    if tahun_s != "Semua":
        try:
            tahun_i = int(tahun)  # type: ignore[arg-type]
        except Exception:
            tahun_i = None

    if provinsi_s != "Semua":
        df_f = df_f[df_f['Provinsi'] == provinsi_s]
    if tahun_i is not None:
        df_f = df_f[df_f['Tahun'] == tahun_i]

    # Ringkasan kecil (HCI: visibility + konteks)
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah baris", ui.format_int(len(df_f)))
    col2.metric("Provinsi", provinsi_s)
    col3.metric("Tahun", tahun_s)

    ui.active_filters_bar(
        items={
            "Provinsi": provinsi,
            "Tahun": tahun,
            "Grafik": tipe_grafik,
        },
        reset_keys=["viz_provinsi", "viz_tahun", "viz_tipe_grafik", "viz_view"],
    )

    view = ui.section_nav(
        "Tampilan",
        options=["Grafik", "Tabel", "Unduh"],
        key="viz_view",
        default="Grafik",
    )

    if view == "Grafik":
        if df_f.empty:
            ui.empty_data_state("Tidak ada data untuk kombinasi filter tersebut.")
            return

        if tipe_grafik == "Tren":
            if provinsi == "Semua":
                df_nasional = df_f.groupby(['Tanggal'], as_index=False)['Inflasi (%)'].mean()
                fig = px.line(
                    df_nasional,
                    x='Tanggal',
                    y='Inflasi (%)',
                    title='Tren Inflasi Nasional (rata-rata)',
                )
            else:
                fig = px.line(
                    df_f,
                    x='Tanggal',
                    y='Inflasi (%)',
                    title=f"Tren Inflasi — {provinsi}",
                )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
            st.plotly_chart(fig, **ui.kw_plotly_chart())

        elif tipe_grafik == "Perbandingan":
            if provinsi == "Semua":
                df_prov = (
                    df_f.groupby('Provinsi', as_index=False)['Inflasi (%)']
                    .mean()
                    .sort_values(by='Inflasi (%)', ascending=False)  # type: ignore[call-arg]
                    .head(12)
                )
                fig = px.bar(
                    df_prov,
                    x='Inflasi (%)',
                    y='Provinsi',
                    orientation='h',
                    title='Rata-rata inflasi (Top 12 provinsi)',
                )
            else:
                df_m = df_f.groupby('Tanggal', as_index=False)['Inflasi (%)'].mean()
                fig = px.bar(
                    df_m,
                    x='Tanggal',
                    y='Inflasi (%)',
                    title=f"Inflasi bulanan — {provinsi}",
                )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
            st.plotly_chart(fig, **ui.kw_plotly_chart())

        else:  # Komposisi
            if provinsi == "Semua":
                st.caption("Komposisi paling berguna untuk jumlah kategori kecil. Menampilkan Top 10 provinsi.")
                df_prov = (
                    df_f.groupby('Provinsi', as_index=False)['Inflasi (%)']
                    .mean()
                    .sort_values(by='Inflasi (%)', ascending=False)  # type: ignore[call-arg]
                    .head(10)
                )
                fig = px.pie(
                    df_prov,
                    values='Inflasi (%)',
                    names='Provinsi',
                    title='Komposisi rata-rata inflasi (Top 10 provinsi)',
                )
            else:
                df_b = df_f.groupby('Bulan', as_index=False)['Inflasi (%)'].mean()
                fig = px.pie(
                    df_b,
                    values='Inflasi (%)',
                    names='Bulan',
                    title=f"Komposisi inflasi per bulan — {provinsi}",
                )
            fig.update_layout(margin=dict(l=0, r=0, t=50, b=0))
            st.plotly_chart(fig, **ui.kw_plotly_chart())

    elif view == "Tabel":
        st.dataframe(
            df_f[['Provinsi', 'Tahun', 'Bulan', 'Inflasi (%)']].copy(),
            height=420,
            **ui.kw_full_width(st.dataframe),
        )

    else:  # Unduh
        csv = df_f.to_csv(index=False)
        st.download_button(
            "Download CSV (hasil filter)",
            data=csv,
            file_name="inflasi_filtered.csv",
            mime="text/csv",
        )
