import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ui
import data_prep

def buat_peta_indonesia_plotly(df_inflasi, *, basemap: str = "auto"):
    """
    Membuat peta Indonesia dengan data inflasi menggunakan Plotly Choropleth
    """
    # Data koordinat dan nilai inflasi per provinsi
    if df_inflasi.empty:
        return go.Figure()
    
    # Jika ada duplikasi baris untuk provinsi yang sama pada periode sama, gunakan rata-rata
    inflasi_terbaru = df_inflasi.groupby('Provinsi', as_index=False)['Inflasi (%)'].mean()
    
    # Koordinat untuk scatter map
    koordinat_provinsi = {
        'Aceh': [4.695135, 96.749397],
        'Sumatera Utara': [2.115341, 99.545096],
        'Sumatera Barat': [-0.739928, 100.800005],
        'Riau': [0.293347, 101.706829],
        'Jambi': [-1.610122, 103.613129],
        'Sumatera Selatan': [-3.319437, 104.913342],
        'Bengkulu': [-3.792848, 102.251597],
        'Lampung': [-4.558587, 105.406807],
        'DKI Jakarta': [-6.208763, 106.845599],
        'Jawa Barat': [-6.917464, 107.619123],
        'Jawa Tengah': [-7.250445, 110.175514],
        'DI Yogyakarta': [-7.795580, 110.369492],
        'Jawa Timur': [-7.536064, 112.238402],
        'Banten': [-6.405817, 106.064018],
        'Bali': [-8.340538, 115.091951],
        'Nusa Tenggara Barat': [-8.652382, 117.361648],
        'Nusa Tenggara Timur': [-8.657382, 121.079370],
        'Kalimantan Barat': [0.278781, 111.475285],
        'Kalimantan Tengah': [-1.682013, 113.382354],
        'Kalimantan Selatan': [-3.092642, 115.283759],
        'Kalimantan Timur': [1.682013, 116.419417],
        'Kalimantan Utara': [3.074931, 116.041393],
        'Sulawesi Utara': [0.729913, 123.948317],
        'Sulawesi Tengah': [-1.430025, 121.443043],
        'Sulawesi Selatan': [-3.668799, 119.974056],
        'Sulawesi Tenggara': [-4.144910, 122.174604],
        'Gorontalo': [0.543445, 123.058524],
        'Sulawesi Barat': [-2.844137, 119.232073],
        'Maluku': [-3.238462, 130.145273],
        'Maluku Utara': [1.570999, 127.808769],
        'Papua Barat': [-1.336115, 133.197629],
        'Papua': [-4.269928, 138.080353],
    }
    
    def _level(inflasi: float) -> int:
        # 0: hijau (<2), 1: kuning (2-<4), 2: oranye (4-<6), 3: merah (>=6)
        if inflasi < 2:
            return 0
        if inflasi < 4:
            return 1
        if inflasi < 6:
            return 2
        return 3

    def _level_label(level: int) -> str:
        return {
            0: "< 2%",
            1: "2–4%",
            2: "4–6%",
            3: "≥ 6%",
        }.get(int(level), "-")

    # Siapkan data untuk plot
    data_peta = []
    for _, row in inflasi_terbaru.iterrows():
        provinsi = row['Provinsi']
        inflasi = row['Inflasi (%)']
        
        if provinsi in koordinat_provinsi:
            lat, lon = koordinat_provinsi[provinsi]
            
            # Ukuran marker tetap berdasarkan tingkat inflasi
            if inflasi < 2:
                ukuran = 15
            elif inflasi < 4:
                ukuran = 20
            elif inflasi < 6:
                ukuran = 25
            else:
                ukuran = 30
            
            data_peta.append({
                'Provinsi': provinsi,
                'Lat': lat,
                'Lon': lon,
                'Inflasi': inflasi,
                'Level': _level(float(inflasi)),
                'Ukuran': ukuran
            })
    
    if not data_peta:
        return go.Figure()
    
    df_peta = pd.DataFrame(data_peta)

    # Discrete single-hue palette (lebih ramah color-blind dibanding red/green)
    # 0 (rendah) -> ungu terang, 3 (tinggi) -> ungu gelap
    color_map = {
        0: "#c4b5fd",
        1: "#a78bfa",
        2: "#7c3aed",
        3: "#4c1d95",
    }

    df_peta["LevelLabel"] = df_peta["Level"].apply(_level_label)

    # Buat scatter map (categorical legend)
    # Catatan: sengaja tidak pakai colorbar agar kompatibel lintas versi Plotly
    # (beberapa versi sensitif pada properti colorbar tertentu dan bisa memicu error).
    fig = go.Figure()
    for lvl in [0, 1, 2, 3]:
        sub = df_peta.loc[df_peta["Level"] == lvl].copy()
        if sub.empty:
            continue

        hover_text = [
            f"{p}<br>Inflasi: {float(i):.2f}%<br>Kategori: {lab}"
            for p, i, lab in zip(
                sub["Provinsi"].astype(str).tolist(),
                sub["Inflasi"].tolist(),
                sub["LevelLabel"].astype(str).tolist(),
            )
        ]

        fig.add_trace(
            go.Scattermapbox(
                lat=sub["Lat"],
                lon=sub["Lon"],
                mode="markers",
                marker=dict(
                    size=sub["Ukuran"],
                    color=color_map.get(int(lvl), "#a78bfa"),
                    symbol="circle",
                    sizemode="diameter",
                    opacity=0.92,
                ),
                text=hover_text,
                hovertemplate="<b>%{text}</b><extra></extra>",
                name=_level_label(int(lvl)),
                showlegend=True,
                legendgroup="kategori",
            )
        )
    
    # Update layout
    # Basemap dipilih eksplisit (Auto/Terang/Gelap) supaya stabil dan tidak
    # bergantung pada CSS override di level app.
    bm = str(basemap).lower().strip()
    if bm in {"auto", "default", "tema", "theme"}:
        base = ui.get_streamlit_theme_base(default="light")
        is_light = base != "dark"
    else:
        is_light = bm not in {"dark", "gelap"}
    dark_tiles = [
        "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
    ]

    title_color = "#0F172A" if is_light else "#F9FAFB"
    font_color = "#0F172A" if is_light else "#E5E7EB"
    legend_bg = "rgba(255,255,255,0.75)" if is_light else "rgba(17,24,39,0.65)"
    legend_border = "rgba(124,58,237,0.20)" if is_light else "rgba(124,58,237,0.25)"
    hover_bg = "#FFFFFF" if is_light else "#111827"
    hover_font = "#0F172A" if is_light else "#F9FAFB"

    mapbox_cfg: dict = {
        "center": dict(lat=-2.5, lon=118),
        "zoom": 4,
    }
    if is_light:
        mapbox_cfg.update(
            {
                "style": "open-street-map",
            }
        )
    else:
        mapbox_cfg.update(
            {
                "style": "white-bg",
                "layers": [
                    dict(
                        below="traces",
                        sourcetype="raster",
                        source=dark_tiles,
                        sourceattribution="© OpenStreetMap contributors © CARTO",
                    )
                ],
            }
        )

    fig.update_layout(
        title={
            'text': 'Peta Inflasi Indonesia',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'color': title_color}
        },
        legend={
            "title": {"text": "Kategori"},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 0.01,
            "xanchor": "left",
            "x": 0.01,
            "bgcolor": legend_bg,
            "bordercolor": legend_border,
            "borderwidth": 1,
            "font": {"color": font_color},
        },
        mapbox=mapbox_cfg,
        height=720,
        margin=dict(l=0, r=0, t=56, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=font_color),
        hoverlabel=dict(
            bgcolor=hover_bg,
            font=dict(color=hover_font),
            bordercolor='rgba(124, 58, 237, 0.35)',
        ),
    )

    return fig

def tampilkan_analisa_gis(df_inflasi):
    """
    Menampilkan halaman Analisis GIS Inflasi
    """
    ui.page_title(
        "Analisis GIS",
        "Peta inflasi per provinsi untuk periode yang dipilih.",
    )
    
    if df_inflasi.empty:
        ui.empty_data_state(
            "Data inflasi tidak tersedia.",
            checks=["Periksa file Excel di folder `data/` atau konfigurasi Supabase"],
        )
        return

    # URL state -> session_state (sekali per session)
    ui.sync_state_from_url(
        "gis",
        keys=["gis_tahun", "gis_bulan", "gis_basemap", "gis_view"],
    )

    st.caption("Tip: buka 'Cara membaca peta' jika butuh penjelasan kategori.")
    with st.expander("Cara membaca peta", expanded=False):
        st.markdown(
            "Peta menunjukkan tingkat inflasi per provinsi.\n\n"
            "Kategori ditandai oleh **warna**. Ukuran marker ikut naik saat inflasi lebih tinggi (indikasi tambahan).\n"
            "- Level 0: < 2%\n"
            "- Level 1: 2–4%\n"
            "- Level 2: 4–6%\n"
            "- Level 3: ≥ 6%\n"
            "\nSemakin gelap, inflasi semakin tinggi."
        )
    
    @st.cache_data(ttl=60 * 60, show_spinner=False)
    def _prep_cached(dfi: pd.DataFrame) -> pd.DataFrame:
        return data_prep.prep_inflasi_base(dfi)

    df = _prep_cached(df_inflasi)

    tahun_list = sorted(df['Tahun'].unique())
    tahun_default = data_prep.latest_year(df)

    # Default bulan: bulan terbesar yang tersedia pada tahun_default
    bulan_default = None
    if tahun_default is not None:
        bulan_default = data_prep.latest_month_in_year(df, tahun_default)

    with st.expander("Filter", expanded=True):
        with st.form("gis_filter"):
            col1, col2, col3 = st.columns(3)
            with col1:
                tahun_peta = ui.persisted_selectbox(
                    "Tahun",
                    options=tahun_list,
                    key="gis_tahun",
                    default=tahun_default,
                )
            with col2:
                bulan_opts = sorted(df.loc[df['Tahun'] == tahun_peta, 'Bulan'].unique())
                fallback_bulan = bulan_default
                if fallback_bulan is None and bulan_opts:
                    fallback_bulan = int(max(bulan_opts))
                bulan_peta = ui.persisted_selectbox(
                    "Bulan",
                    options=bulan_opts,
                    key="gis_bulan",
                    default=fallback_bulan,
                )
            with col3:
                basemap_label = ui.persisted_selectbox(
                    "Basemap",
                    options=["Auto", "Terang", "Gelap"],
                    key="gis_basemap",
                    default="Auto",
                )
            st.form_submit_button("Terapkan")
    
    # Filter data untuk peta
    df_peta = df[(df['Tahun'] == tahun_peta) & (df['Bulan'] == bulan_peta)]

    if df_peta.empty:
        ui.empty_data_state("Tidak ada data untuk periode tersebut.")
        return

    try:
        tahun_i = int(tahun_peta)  # type: ignore[arg-type]
    except Exception:
        tahun_i = tahun_default if tahun_default is not None else 0

    try:
        bulan_i = int(bulan_peta)  # type: ignore[arg-type]
    except Exception:
        bulan_i = int(bulan_default) if bulan_default is not None else 1

    ui.active_filters_bar(
        items={
            "Tahun": tahun_i,
            "Bulan": bulan_i,
            "Basemap": basemap_label,
        },
        reset_keys=["gis_tahun", "gis_bulan", "gis_basemap", "gis_view"],
    )

    view = ui.section_nav(
        "Tampilan",
        options=["Peta", "Tabel"],
        key="gis_view",
        default="Peta",
    )
    
    # UI layout: wide -> peta + panel ringkas, mobile -> stack otomatis via CSS
    if view == "Peta":
        left, right = st.columns([3, 1])
        with left:
            basemap = {
                "terang": "light",
                "gelap": "dark",
                "auto": "auto",
            }.get(str(basemap_label).lower().strip(), "auto")
            peta_inflasi = buat_peta_indonesia_plotly(df_peta, basemap=basemap)
            st.plotly_chart(peta_inflasi, **ui.kw_plotly_chart())

        with right:
            st.subheader("Peringkat")
            df_rank = df_peta[['Provinsi', 'Inflasi (%)']].copy().sort_values('Inflasi (%)', ascending=False)
            top = df_rank.head(8)
            st.dataframe(top, height=360, **ui.kw_full_width(st.dataframe))
            if len(df_rank) > 8:
                st.caption(f"Menampilkan 8 dari {len(df_rank):,} provinsi. Buka 'Tabel' untuk melihat semua.")

    else:  # Tabel
        st.subheader("Tabel")
        st.dataframe(
            df_peta[['Provinsi', 'Inflasi (%)']].sort_values('Inflasi (%)', ascending=False),
            height=520,
            **ui.kw_full_width(st.dataframe),
        )
