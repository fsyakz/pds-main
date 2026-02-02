import streamlit as st
import pandas as pd
import ui
import data_prep

def tampilkan_database_inflasi(df_inflasi):
    """
    Menampilkan halaman Database Inflasi - Interface yang sederhana dan ramah pengguna
    """
    ui.page_title(
        "Database Inflasi",
        "Cari dan unduh data inflasi dengan mudah.",
    )
    
    if df_inflasi.empty:
        ui.empty_data_state(
            "Data inflasi tidak tersedia.",
            checks=["Periksa file Excel di folder `data/` atau konfigurasi Supabase"],
        )
        return

    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def _prep_cached(dfi: pd.DataFrame) -> pd.DataFrame:
        return data_prep.prep_inflasi_base(dfi)

    df = _prep_cached(df_inflasi)

    prov_all = sorted(df['Provinsi'].unique())
    tahun_all = sorted(df['Tahun'].unique())
    bulan_all = sorted(df['Bulan'].unique())
    tahun_default = data_prep.latest_year(df)

    # Simple Filter Interface
    with st.expander(" Cari Data", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            provinsi_filter = st.selectbox(
                "Pilih Provinsi",
                options=["Semua Provinsi"] + prov_all,
                key="db_provinsi_simple",
                index=0
            )
        
        with col2:
            tahun_filter = st.selectbox(
                "Pilih Tahun",
                options=["Semua Tahun"] + tahun_all,
                key="db_tahun_simple",
                index=0
            )
        
        with col3:
            bulan_filter = st.selectbox(
                "Pilih Bulan",
                options=["Semua Bulan"] + bulan_all,
                key="db_bulan_simple",
                index=0
            )
        
        # Search bar
        search_query = st.text_input(
            "Cari Provinsi (ketik untuk mencari)",
            placeholder="Contoh: Jakarta, Bali, Sumatera...",
            key="db_search_simple"
        )
        
        # Apply filter button
        if st.button("Terapkan Filter", use_container_width=True, type="primary"):
            st.session_state["filter_applied"] = True
        else:
            if "filter_applied" not in st.session_state:
                st.session_state["filter_applied"] = True
    
    # Terapkan filter
    df_tampil = df.copy()
    
    if provinsi_filter != "Semua Provinsi":
        df_tampil = df_tampil[df_tampil['Provinsi'] == provinsi_filter]
    
    if tahun_filter != "Semua Tahun":
        df_tampil = df_tampil[df_tampil['Tahun'] == tahun_filter]
    
    if bulan_filter != "Semua Bulan":
        df_tampil = df_tampil[df_tampil['Bulan'] == bulan_filter]
    
    if search_query.strip():
        q = search_query.strip().lower()
        df_tampil = df_tampil[df_tampil['Provinsi'].astype(str).str.lower().str.contains(q, na=False)]

    col1, col2 = st.columns(2)
    col1.metric("Data Ditemukan", ui.format_int(len(df_tampil)))
    col2.metric("Total Data", ui.format_int(len(df)))

    if df_tampil.empty:
        st.warning("Tidak ada data untuk kombinasi filter tersebut.")
        return

    st.subheader("Tabel Data")
    
    page_size = st.selectbox(
        "Tampilkan per halaman",
        options=[10, 25, 50, 100],
        index=1,
        key="db_page_size"
    )
    
    total_rows = len(df_tampil)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    
    if total_pages > 1:
        page = st.number_input(
            "Halaman", 
            min_value=1, 
            max_value=total_pages, 
            value=1, 
            key="db_page"
        )
    else:
        page = 1
    
    start = (page - 1) * page_size
    end = start + page_size

    df_page = df_tampil.sort_values(['Tahun', 'Bulan', 'Provinsi']).iloc[start:end]
    st.dataframe(df_page, height=400, use_container_width=True)

    st.caption(f"Menampilkan {start + 1:,}–{min(end, total_rows):,} dari {total_rows:,} data")

    st.divider()
    st.subheader("Unduh Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df_tampil.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"data_inflasi_{len(df_tampil)}_records.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_tampil.to_excel(writer, index=False, sheet_name='Data Inflasi')
        excel_buffer.seek(0)
        
        st.download_button(
            label="Download Excel",
            data=excel_buffer,
            file_name=f"data_inflasi_{len(df_tampil)}_records.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    view = ui.section_nav(
        "Tampilan",
        options=["Tabel", "Unduh"],
        key="db_view",
        default="Tabel",
    )

    if view == "Tabel":
        page_size = ui.persisted_selectbox(
            "Baris per halaman",
            options=[50, 100, 250, 500],
            key="db_page_size",
            default=100,
        )
        try:
            page_size = int(page_size)  # type: ignore[arg-type]
        except Exception:
            page_size = 100
        total_rows = len(df_tampil)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1, key="db_page")
        start = (int(page) - 1) * page_size
        end = start + page_size

        df_page = df_tampil.sort_values(['Tahun', 'Bulan', 'Provinsi']).iloc[start:end]
        st.dataframe(df_page, height=460, **ui.kw_full_width(st.dataframe))

        st.caption(f"Menampilkan {start + 1:,}–{min(end, total_rows):,} dari {total_rows:,} baris")

    else:  # Unduh
        csv = df_tampil.to_csv(index=False)
        st.download_button(
            label="Download CSV (hasil filter)",
            data=csv,
            file_name="data_inflasi_filter.csv",
            mime="text/csv"
        )
