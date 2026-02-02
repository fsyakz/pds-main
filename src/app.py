import streamlit as st
import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Load environment variables dari .env
try:
    from dotenv import load_dotenv

    # Load .env dari root repo agar tidak tergantung current working directory
    load_dotenv(str(Path(__file__).resolve().parents[1] / ".env"))
except Exception:
    pass

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modul-modul yang telah dipisah
import utils
import styles
import dashboard_utama
import visualisasi_inflasi
import analisa_gis
import statistik_data
import database_inflasi
import kalkulator_mata_uang
import bi_data
import kurs_data
import ui

# Konfigurasi halaman
st.set_page_config(
    page_title="Analisa Inflasi dan Mata Uang",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=60 * 60, show_spinner=False)
def _load_inflasi_cached():
    """Load data inflasi dengan cache untuk mengurangi latency & rerun."""
    return utils.baca_data_inflasi()

def main():
    """
    Fungsi utama aplikasi Streamlit
    """
    # Set default halaman ke Dashboard Utama saat pertama kali buka
    if "app_page" not in st.session_state:
        st.session_state["app_page"] = "Dashboard Utama"
    
    # Deep-link: izinkan URL mengatur halaman yang aktif (sekali per session)
    ui.sync_state_from_url(
        "app",
        keys=["app_page"],
    )

    # Theme: gunakan fitur bawaan Streamlit (Choose app theme).
    # CSS di project ini dibuat netral (tidak memaksa dark/light lewat session_state).
    st.markdown(styles.get_custom_css(), unsafe_allow_html=True)

    st.sidebar.title("Dashboard Analisis")
    st.sidebar.caption("Analisis data inflasi dan BI-7Day-RR.")

    # --- Dashboard Utama (menu terpisah di atas) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Dashboard Utama")
    dashboard_main = st.sidebar.button("Dashboard Utama", key="dashboard_main", use_container_width=True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Menu Data")

    # --- Navigasi terkelompok (HCI: information architecture lebih jelas) ---
    pages_by_group = {
        "Data Inflasi": [
            "Visualisasi Inflasi",
            "Analisis GIS Inflasi",
            "Statistik Data",
            "Database Inflasi",
        ],
        "Data BI": [
            "Data BI-7Day-RR",
            "Database BI",
        ],
        "Data Kurs": [
            "Data Kurs JISDOR",
            "Database Kurs",
        ],
        "Tools": [
            "Kalkulator Mata Uang",
        ],
    }

    # --- Navigasi aman (hindari error: tidak boleh mengubah session_state[app_page] setelah widget dibuat) ---
    # Halaman lain boleh "request" navigasi dengan menulis ke _app_page_pending.
    pending_page = st.session_state.pop("_app_page_pending", None)
    if isinstance(pending_page, str) and pending_page.strip():
        wanted = pending_page.strip()
        all_pages = {p for group_pages in pages_by_group.values() for p in group_pages}
        if wanted in all_pages:
            st.session_state["app_page"] = wanted

    # Handle dashboard utama button
    if dashboard_main:
        st.session_state["app_page"] = "Dashboard Utama"

    # Sinkronkan group default dari page aktif (kalau deep-link/set state)
    current_page = st.session_state.get("app_page")
    
    # Selalu tampilkan menu analisis
    show_menu = True
    if current_page == "Dashboard Utama":
        halaman = "Dashboard Utama"
        show_menu = True
    
    if show_menu:
        current_group = None
        for g, opts in pages_by_group.items():
            if current_page in opts:
                current_group = g
                break
        if current_group is None:
            current_group = "Data Inflasi"

        # Pastikan state `nav_group` selalu valid sebelum widget selectbox dibuat
        try:
            if st.session_state.get("nav_group") not in pages_by_group:
                st.session_state["nav_group"] = current_group
        except Exception:
            st.session_state["nav_group"] = current_group

        nav_group = st.sidebar.selectbox(
            "Kategori",
            options=list(pages_by_group.keys()),
            index=list(pages_by_group.keys()).index(current_group),
            key="nav_group",
        )

        # Streamlit stubs kadang memodelkan selectbox return sebagai Optional[str]
        if not isinstance(nav_group, str):
            nav_group = current_group

        # Pastikan app_page valid terhadap group yang dipilih
        if st.session_state.get("app_page") not in pages_by_group[nav_group]:
            st.session_state["app_page"] = pages_by_group[nav_group][0]

        current_in_group = st.session_state.get("app_page")
        if not isinstance(current_in_group, str):
            current_in_group = pages_by_group[nav_group][0]
        try:
            nav_index = pages_by_group[nav_group].index(current_in_group)
        except Exception:
            nav_index = 0

        selected_page = st.sidebar.radio(
            "Navigasi",
            pages_by_group[nav_group],
            index=nav_index,
            key="app_page",
        )
        
        # Update halaman jika ada perubahan dari radio
        if selected_page != current_page and current_page != "Dashboard Utama":
            halaman = selected_page
        elif current_page == "Dashboard Utama":
            halaman = "Dashboard Utama"
        else:
            halaman = selected_page
    
    # Load data inflasi (dengan feedback + cache)
    with st.spinner("Memuat data inflasi..."):
        df_inflasi = _load_inflasi_cached()
    
    # Routing ke halaman yang sesuai
    if halaman == "Dashboard Utama":
        dashboard_utama.tampilkan_dashboard_utama(df_inflasi)
    
    elif halaman == "Visualisasi Inflasi":
        visualisasi_inflasi.tampilkan_visualisasi_inflasi(df_inflasi)
    
    elif halaman == "Analisis GIS Inflasi":
        analisa_gis.tampilkan_analisa_gis(df_inflasi)
    
    elif halaman == "Statistik Data":
        statistik_data.tampilkan_statistik_data(df_inflasi)
    
    elif halaman == "Database Inflasi":
        database_inflasi.tampilkan_database_inflasi(df_inflasi)
    
    elif halaman == "Data BI-7Day-RR":
        bi_data.tampilkan_bi_data()
    
    elif halaman == "Database BI":
        bi_data.tampilkan_database_bi()
    
    elif halaman == "Data Kurs JISDOR":
        kurs_data.tampilkan_kurs_data()
    
    elif halaman == "Database Kurs":
        kurs_data.tampilkan_database_kurs()
    
    elif halaman == "Kalkulator Mata Uang":
        kalkulator_mata_uang.tampilkan_kalkulator_mata_uang()
    
    else:
        # Fallback jika halaman tidak dikenali
        st.error(f"Halaman '{halaman}' tidak dikenali")
        st.write("Halaman yang tersedia:")
        for group, pages in pages_by_group.items():
            st.write(f"- {group}: {', '.join(pages)}")

if __name__ == "__main__":
    main()
