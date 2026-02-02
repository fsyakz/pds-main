import streamlit as st
import pandas as pd
import ui
import fx_rates


def konversi_mata_uang(
    jumlah: float,
    mata_uang_asal: str,
    mata_uang_tujuan: str,
    *,
    kurs_idr: dict[str, float],
) -> float | None:
    """
    Konversi mata uang sederhana
    """
    try:
        asal = str(mata_uang_asal).upper()
        tujuan = str(mata_uang_tujuan).upper()
        if asal not in kurs_idr or tujuan not in kurs_idr:
            return None
        # Konversi ke IDR dulu, lalu ke mata uang tujuan
        dalam_idr = float(jumlah) * float(kurs_idr[asal])
        hasil = dalam_idr / float(kurs_idr[tujuan])
        return round(float(hasil), 2)
    except Exception:
        return None


@st.cache_data(ttl=60 * 60, show_spinner=False)
def _load_rates_snapshot(refresh_token: int) -> fx_rates.RatesSnapshot:
    # refresh_token dipakai untuk "mem-bypass" cache saat user klik Refresh.
    return fx_rates.get_rates_snapshot(currencies=fx_rates.DEFAULT_CURRENCIES)

def tampilkan_kalkulator_mata_uang():
    """
    Menampilkan halaman Kalkulator Mata Uang
    """
    ui.page_title(
        "Kalkulator Mata Uang",
        "Konversi menggunakan kurs realtime (fallback otomatis jika offline).",
    )

    # Hydrate state dari URL (untuk share link) - aman karena tidak overwrite value user.
    ui.sync_state_from_url(
        "fx",
        keys=[
            "app_page",
            "fx_view",
            "fx_amount",
            "fx_from",
            "fx_to",
            "fx_from_batch",
            "fx_to_batch",
            "fx_batch_input",
        ],
    )

    st.session_state.setdefault("fx_view", "Konversi")
    st.session_state.setdefault("fx_amount", 100.0)
    st.session_state.setdefault("fx_from", "USD")
    st.session_state.setdefault("fx_to", "IDR")
    st.session_state.setdefault("fx_from_batch", "USD")
    st.session_state.setdefault("fx_to_batch", "IDR")
    st.session_state.setdefault("fx_batch_input", "")
    st.session_state.setdefault("fx_rates_refresh", 0)

    # --- Rates loader (cached + refresh) ---
    with st.spinner("Memuat kurs mata uang..."):
        snap = _load_rates_snapshot(int(st.session_state.get("fx_rates_refresh", 0)))

    kurs_idr = snap.kurs_idr
    mata_uang = list(kurs_idr.keys())

    # UI feedback (HCI: system status + trust)
    left, right = st.columns([3, 1])
    with left:
        st.caption(
            f"Sumber kurs: {snap.source}"
            + (f" • as of: {snap.as_of}" if snap.as_of else "")
        )
        if snap.warnings:
            st.caption("Catatan: " + " | ".join(snap.warnings))
    with right:
        if ui.secondary_button("Refresh kurs", key="fx_refresh_btn", help="Ambil ulang kurs terbaru"):
            st.session_state["fx_rates_refresh"] = int(st.session_state.get("fx_rates_refresh", 0)) + 1
            st.rerun()

    ui.views_panel(
        "fx",
        keys=[
            "app_page",
            "fx_view",
            "fx_amount",
            "fx_from",
            "fx_to",
            "fx_from_batch",
            "fx_to_batch",
            "fx_batch_input",
            "fx_rates_refresh",
        ],
        title="Tampilan tersimpan",
        expanded=False,
    )

    view = ui.section_nav(
        "Tampilan",
        options=["Konversi", "Batch", "Kurs"],
        key="fx_view",
        default="Konversi",
    )

    if view == "Konversi":
        with st.form("fx_single_form"):
            col1, col2 = st.columns(2)
            with col1:
                jumlah = st.number_input(
                    "Jumlah",
                    min_value=0.0,
                    value=float(st.session_state.get("fx_amount", 100.0) or 100.0),
                    step=0.01,
                    key="fx_amount",
                    help="Masukkan nilai yang ingin dikonversi.",
                )
            with col2:
                mata_uang_asal = ui.persisted_selectbox(
                    "Dari",
                    options=mata_uang,
                    key="fx_from",
                    default="USD" if "USD" in mata_uang else mata_uang[0],
                )

            mata_uang_tujuan = ui.persisted_selectbox(
                "Ke",
                options=mata_uang,
                key="fx_to",
                default="IDR" if "IDR" in mata_uang else mata_uang[0],
            )

            submitted = st.form_submit_button("Konversi", type="primary")

        ui.active_filters_bar(
            items={
                "Dari": mata_uang_asal,
                "Ke": mata_uang_tujuan,
            },
            reset_keys=["fx_amount", "fx_from", "fx_to"],
        )

        if submitted:
            if mata_uang_asal == mata_uang_tujuan:
                st.warning("Mata uang asal dan tujuan tidak boleh sama.")
            else:
                hasil = konversi_mata_uang(
                    float(jumlah),
                    str(mata_uang_asal),
                    str(mata_uang_tujuan),
                    kurs_idr=kurs_idr,
                )
                if hasil is None:
                    st.error("Terjadi kesalahan saat menghitung konversi.")
                else:
                    st.success(f"{jumlah:,.2f} {mata_uang_asal} = {hasil:,.2f} {mata_uang_tujuan}")

    elif view == "Batch":
        st.caption("Masukkan 1 nilai per baris. Baris yang tidak valid akan diabaikan.")

        with st.form("fx_batch_form"):
            col1, col2 = st.columns(2)
            with col1:
                mata_uang_asal_b = ui.persisted_selectbox(
                    "Dari",
                    options=mata_uang,
                    key="fx_from_batch",
                    default="USD" if "USD" in mata_uang else mata_uang[0],
                )
            with col2:
                mata_uang_tujuan_b = ui.persisted_selectbox(
                    "Ke",
                    options=mata_uang,
                    key="fx_to_batch",
                    default="IDR" if "IDR" in mata_uang else mata_uang[0],
                )

            batch_input = st.text_area(
                "Nilai (satu per baris)",
                placeholder="100\n200\n500",
                height=120,
                key="fx_batch_input",
            )
            batch_submitted = st.form_submit_button("Konversi Batch", type="primary")

        ui.active_filters_bar(
            items={
                "Dari": mata_uang_asal_b,
                "Ke": mata_uang_tujuan_b,
            },
            reset_keys=["fx_from_batch", "fx_to_batch", "fx_batch_input"],
        )

        if batch_submitted:
            if mata_uang_asal_b == mata_uang_tujuan_b:
                st.warning("Mata uang asal dan tujuan tidak boleh sama.")
            else:
                lines = [ln.strip() for ln in (batch_input or "").splitlines() if ln.strip()]
                hasil_batch = []
                for line in lines:
                    try:
                        nilai = float(line)
                    except Exception:
                        continue

                    hasil_konversi = konversi_mata_uang(
                        float(nilai),
                        str(mata_uang_asal_b),
                        str(mata_uang_tujuan_b),
                        kurs_idr=kurs_idr,
                    )
                    if hasil_konversi is None:
                        continue

                    hasil_batch.append({
                        'Asal': f"{nilai:,.2f} {mata_uang_asal_b}",
                        'Hasil': f"{hasil_konversi:,.2f} {mata_uang_tujuan_b}",
                    })

                if not hasil_batch:
                    st.error("Tidak ada baris valid yang bisa dikonversi.")
                else:
                    df_batch = pd.DataFrame(hasil_batch)
                    st.dataframe(df_batch, **ui.kw_full_width(st.dataframe))

    else:  # Kurs
        df_kurs = pd.DataFrame(
            [(k, v) for k, v in kurs_idr.items() if k != 'IDR'],
            columns=['Mata Uang', 'Kurs (1 unit = IDR)']
        ).sort_values('Mata Uang')
        st.dataframe(df_kurs, height=320, **ui.kw_full_width(st.dataframe))
