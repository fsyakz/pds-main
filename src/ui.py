"""UI helpers.



Tujuan:

- Konsisten antar halaman (HCI: hierarki, feedback sistem, pencegahan error)

- Minim HTML custom agar tampilan terasa natural (tidak 'template')

- Clean code: helper kecil, mudah diuji/dirawat

"""



from __future__ import annotations



from typing import Any, Callable, Iterable, Optional

import inspect

import json

import base64

import zlib



import streamlit as st





def get_streamlit_theme_base(*, default: str = "light") -> str:

    """Best-effort read Streamlit's configured theme base.



    Catatan:

    - Streamlit menyediakan pengaturan tema melalui menu UI *Choose app theme*

      (Light/Dark/Custom).

    - API yang stabil untuk membaca pilihan user di browser tidak dijamin.

      Namun, opsi config `theme.base` biasanya tersedia untuk *Custom theme*.

    """



    try:

        base = st.get_option("theme.base")

    except Exception:

        base = None



    base = str(base).lower().strip() if base is not None else ""

    if base in {"light", "dark"}:

        return base

    return "dark" if str(default).lower().strip() == "dark" else "light"





def kw_plotly_chart() -> dict[str, Any]:

    """Kwargs for st.plotly_chart (version-tolerant full width).



    Kita sengaja tidak memaksa template/theme Plotly di sini.

    Biarkan Streamlit yang mengatur sesuai *Choose app theme*.

    """



    return dict(kw_full_width(st.plotly_chart))





def kw_full_width(fn: Callable[..., object]) -> dict[str, Any]:

    """Return kwargs for 'full width' rendering across Streamlit versions.



    Streamlit is deprecating `use_container_width` in favor of `width`.

    To keep the app compatible with both older and newer versions, we detect

    which kwarg is supported by the target function.

    """



    try:

        params = inspect.signature(fn).parameters

        if "width" in params:

            return {"width": "stretch"}

        if "use_container_width" in params:

            return {"use_container_width": True}

    except Exception:

        pass

    return {}





def _kw_button_type(fn: Callable[..., object], btn_type: str | None) -> dict[str, Any]:

    """Return kwargs for button type across Streamlit versions.



    Streamlit versions differ on whether `st.button` accepts `type=`.

    We detect support via signature inspection.

    """



    if not btn_type:

        return {}

    try:

        params = inspect.signature(fn).parameters

        if "type" in params:

            return {"type": btn_type}

    except Exception:

        pass

    return {}





def button(

    label: str,

    *,

    key: str,

    kind: str | None = None,

    full_width: bool = True,

    disabled: bool = False,

    help: str | None = None,

) -> bool:

    """Wrapper untuk st.button yang version-tolerant + konsisten."""



    kwargs: dict[str, Any] = {}

    if full_width:

        kwargs.update(kw_full_width(st.button))

    kwargs.update(_kw_button_type(st.button, kind))

    return bool(st.button(label, key=key, disabled=disabled, help=help, **kwargs))





def secondary_button(

    label: str,

    *,

    key: str,

    full_width: bool = True,

    disabled: bool = False,

    help: str | None = None,

) -> bool:

    """Secondary action button (visual hierarchy)."""



    clicked = button(

        label,

        key=key,

        kind="secondary",

        full_width=full_width,

        disabled=disabled,

        help=help,

    )

    return clicked





def danger_button(

    label: str,

    *,

    key: str,

    full_width: bool = True,

    disabled: bool = False,

    help: str | None = None,

) -> bool:

    """Destructive action button (error prevention)."""



    # Streamlit belum punya type="danger". Untuk sekarang, gunakan secondary

    # + konfirmasi checkbox (sudah ada di views_panel). Styling warna bisa

    # ditingkatkan jika diperlukan lewat selector DOM yang stabil.

    clicked = button(

        label,

        key=key,

        kind="secondary",

        full_width=full_width,

        disabled=disabled,

        help=help,

    )

    return clicked





def request_navigation(page_label: str, *, key: str = "app_page") -> None:

    """Minta navigasi ke halaman tertentu dengan aman.



    Kenapa perlu helper ini?

    Streamlit melarang mengubah `st.session_state[<widget_key>]` setelah widget

    dengan key tersebut dibuat pada run yang sama.



    Solusi: simpan target ke key pending, lalu `src/app.py` akan mengaplikasikannya

    sebelum widget navigasi dibuat.

    """



    pending_key = f"_{key}_pending"

    st.session_state[pending_key] = str(page_label)

    st.rerun()





def _json_default(obj: object):

    """Best-effort JSON serializer for common UI state types."""

    # datetime/date/Timestamp-like

    try:

        iso = getattr(obj, "isoformat", None)

        if callable(iso):

            return iso()

    except Exception:

        pass



    if isinstance(obj, (set, tuple)):

        return list(obj)



    return str(obj)





def reset_state(keys: list[str]) -> None:

    """Hapus key tertentu dari session_state (untuk reset filter/view)."""

    for k in keys:

        if k in st.session_state:

            del st.session_state[k]





def active_filters_bar(

    *,

    title: str = "Filter aktif",

    items: dict[str, object],

    reset_keys: list[str] | None = None,

    help: str | None = None,

) -> None:

    """Tampilkan ringkasan filter aktif + tombol reset yang konsisten.



    Disengaja sederhana (native Streamlit) agar tidak terasa 'template'.

    """



    def _is_empty(v: object) -> bool:

        if v is None:

            return True

        if isinstance(v, str) and (v.strip() == "" or v.strip().lower() == "semua"):

            return True

        if isinstance(v, list) and len(v) == 0:

            return True

        return False



    active = {k: v for k, v in items.items() if not _is_empty(v)}



    col1, col2 = st.columns([3, 1])

    with col1:

        if not active:

            st.caption(f"{title}: (default)")

        else:

            parts = []

            for k, v in active.items():

                if isinstance(v, list):

                    vv = ", ".join(map(str, v[:6])) + ("" if len(v) > 6 else "")

                else:

                    vv = str(v)

                parts.append(f"{k}: {vv}")

            st.caption(f"{title}: " + "  ".join(parts))

        if help:

            st.caption(help)



    with col2:

        if reset_keys:

            # Hindari key collision jika helper ini dipanggil >1x pada halaman yang sama.

            # (Umumnya 1x per halaman, tapi lebih aman dibuat deterministik.)

            try:

                _rk = tuple(reset_keys)

            except Exception:

                _rk = ("reset",)

            reset_btn_key = f"_reset_{title}_{abs(hash(_rk)) % 1_000_000_000}"

            if secondary_button("Reset", key=reset_btn_key, help="Kembalikan ke default"):

                reset_state(reset_keys)

                st.rerun()





def section_nav(

    label: str,

    *,

    options: list[str],

    key: str,

    default: str | None = None,

) -> str:

    """Navigasi section pengganti st.tabs yang bisa dipersist/share.



    Menggunakan segmented_control jika tersedia, fallback ke radio horizontal.

    """



    # Pastikan default valid

    if default is None or default not in options:

        default = options[0] if options else ""



    # Reuse persisted logic: pastikan state ada/valid

    if key in st.session_state and st.session_state.get(key) not in options:

        st.session_state[key] = default

    elif key not in st.session_state:

        st.session_state[key] = default



    segmented_control = getattr(st, "segmented_control", None)

    if callable(segmented_control):

        value = segmented_control(

            label,

            options=options,

            key=key,

        )

        # Type stub bisa menganggap return Optional[str]; amankan untuk runtime.

        if isinstance(value, str):

            return value

        return default



    value = st.radio(

        label,

        options=options,

        key=key,

        horizontal=True,

    )

    return value if isinstance(value, str) else default





def _encode_url_state(payload: dict) -> str:

    """Encode dict -> compact URL-safe string.



    Format: base64url(zlib(json))

    """



    raw = json.dumps(

        payload,

        ensure_ascii=False,

        separators=(",", ":"),

        default=_json_default,

    ).encode("utf-8")

    comp = zlib.compress(raw, level=9)

    return base64.urlsafe_b64encode(comp).decode("ascii")





def _decode_url_state(token: str) -> dict | None:

    try:

        comp = base64.urlsafe_b64decode(token.encode("ascii"))

        raw = zlib.decompress(comp)

        payload = json.loads(raw.decode("utf-8"))

        return payload if isinstance(payload, dict) else None

    except Exception:

        return None





def _get_query_params() -> dict:

    """Get query params in a version-tolerant way."""

    qp = getattr(st, "query_params", None)

    if qp is not None:

        try:

            # Streamlit modern API

            return dict(qp)

        except Exception:

            pass



    try:

        return st.experimental_get_query_params()  # type: ignore[attr-defined]

    except Exception:

        return {}





def _set_query_params(params: dict) -> None:

    """Set query params in a version-tolerant way."""

    qp = getattr(st, "query_params", None)

    if qp is not None:

        try:

            # Streamlit modern API

            qp.clear()

            for k, v in params.items():

                qp[k] = v

            return

        except Exception:

            pass



    try:

        st.experimental_set_query_params(**params)  # type: ignore[attr-defined]

    except Exception:

        # Ignore if environment does not support query params

        return





def sync_state_from_url(

    namespace: str,

    *,

    keys: list[str],

    param: str = "state",

    coercers: dict[str, Callable[[object], object]] | None = None,

) -> None:

    """Hydrate session_state from URL query param once per session.



    - Tidak menimpa value user jika sudah ada di session_state

    - Aman kalau payload tidak valid

    """



    flag = f"_url_state_loaded_{namespace}"

    if st.session_state.get(flag):

        return



    qp = _get_query_params()

    token = qp.get(param)



    # experimental_get_query_params mengembalikan list[str]

    if isinstance(token, list):

        token = token[0] if token else None



    if isinstance(token, str) and token.strip():

        payload = _decode_url_state(token.strip())

        if isinstance(payload, dict):

            for k in keys:

                if k in payload and k not in st.session_state:

                    v = payload[k]

                    if coercers and k in coercers:

                        try:

                            v = coercers[k](v)

                        except Exception:

                            pass

                    st.session_state[k] = v



    st.session_state[flag] = True





def build_share_query(

    *,

    keys: list[str],

    param: str = "state",

) -> str:

    payload = {k: st.session_state.get(k) for k in keys}

    token = _encode_url_state(payload)

    return f"?{param}={token}"





def coerce_iso_date(value: object) -> object:

    """Coerce 'YYYY-MM-DD' string -> datetime.date.



    Dipakai untuk date_input keys saat state datang dari URL/JSON.

    """



    try:

        import datetime as _dt



        if isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):

            return value

        if isinstance(value, _dt.datetime):

            return value.date()

        if isinstance(value, str):

            s = value.strip()

            if len(s) >= 10:

                return _dt.date.fromisoformat(s[:10])

    except Exception:

        pass

    return value





def _index_of(options: list, value) -> int | None:

    try:

        return options.index(value)

    except Exception:

        return None





def persisted_selectbox(

    label: str,

    *,

    options: list,

    key: str,

    default=None,

    help: str | None = None,

    disabled: bool = False,

) -> object:

    """Selectbox dengan default yang stabil + persist antar halaman.



    Jika value sebelumnya ada di session_state dan masih valid di options,

    maka value tersebut dipakai. Kalau tidak, pakai `default` jika tersedia,

    lalu fallback ke item pertama.

    """



    idx = None

    if key in st.session_state:

        idx = _index_of(options, st.session_state.get(key))

    if idx is None and default is not None:

        idx = _index_of(options, default)

    if idx is None:

        idx = 0



    return st.selectbox(

        label,

        options=options,

        index=idx,

        key=key,

        help=help,

        disabled=disabled,

    )





def persisted_multiselect(

    label: str,

    *,

    options: list,

    key: str,

    default: list | None = None,

    help: str | None = None,

    disabled: bool = False,

) -> list:

    """Multiselect dengan default stabil + persist antar halaman."""



    effective_default = default or []

    if key in st.session_state:

        # Filter nilai lama agar tetap valid jika options berubah.

        prior = st.session_state.get(key)

        if isinstance(prior, list):

            effective_default = [v for v in prior if v in options]

            # Jika ada item invalid, sanitasi state yang sudah ada.

            if effective_default != prior:

                st.session_state[key] = list(effective_default)

        elif isinstance(prior, str):

            # Kadang state bisa korup (mis. string tunggal). Buang agar widget pakai default.

            try:

                del st.session_state[key]

            except Exception:

                pass

            effective_default = default or []

        else:

            # Tipe tidak dikenal -> buang agar tidak memicu "content ... is not in list".

            try:

                del st.session_state[key]

            except Exception:

                pass

            effective_default = default or []



    return st.multiselect(

        label,

        options=options,

        default=effective_default,

        key=key,

        help=help,

        disabled=disabled,

    )





def persisted_radio(

    label: str,

    *,

    options: list,

    key: str,

    default=None,

    horizontal: bool = False,

    help: str | None = None,

    disabled: bool = False,

) -> object:

    """Radio dengan default stabil + persist antar halaman."""



    idx = None

    if key in st.session_state:

        idx = _index_of(options, st.session_state.get(key))

    if idx is None and default is not None:

        idx = _index_of(options, default)

    if idx is None:

        idx = 0



    return st.radio(

        label,

        options=options,

        index=idx,

        horizontal=horizontal,

        key=key,

        help=help,

        disabled=disabled,

    )





def views_panel(

    namespace: str,

    *,

    keys: list[str],

    title: str = "Tampilan tersimpan",

    expanded: bool = False,

    coercers: dict[str, Callable[[object], object]] | None = None,

) -> None:

    """Panel kecil untuk menyimpan/memanggil set filter berbasis session_state.



    - Tidak butuh database

    - Aman jika options berubah (persisted widgets akan fallback)

    - Bisa export/import JSON untuk dipindah (mis. kirim ke rekan kerja)

    """



    store_key = f"_views_{namespace}"

    if store_key not in st.session_state or not isinstance(st.session_state.get(store_key), dict):

        st.session_state[store_key] = {}



    views: dict = st.session_state[store_key]



    active_key = f"{store_key}__active"

    notice_key = f"{store_key}__notice"

    confirm_key = f"{store_key}__confirm_delete"



    def _apply_payload(payload: dict) -> None:

        """Apply saved view payload safely.



        Note: Never directly mutate widget-bound navigation keys after instantiation.

        For `app_page`, we store a pending request for `src/app.py` to consume.

        """



        for k in keys:

            if k not in payload:

                continue

            v = payload[k]

            if coercers and k in coercers:

                try:

                    v = coercers[k](v)

                except Exception:

                    pass

            if k == "app_page":

                # Safe navigation: apply before widget is created on next run.

                st.session_state["_app_page_pending"] = str(v)

                continue

            st.session_state[k] = v



    with st.expander(title, expanded=expanded):

        notice = st.session_state.pop(notice_key, None)

        if isinstance(notice, str) and notice.strip():

            st.success(notice)



        active_name = st.session_state.get(active_key)

        if isinstance(active_name, str) and active_name.strip():

            st.caption(f"Tampilan aktif: **{active_name}**")



        col_a, col_b = st.columns([2, 1])



        with col_a:

            name_key = f"{store_key}__name"

            view_name = st.text_input(

                "Nama tampilan",

                key=name_key,

                placeholder="Contoh: 2025  Jawa Barat  Tren",

            ).strip()



            export_payload = {k: st.session_state.get(k) for k in keys}



            can_save = bool(view_name)

            exists = view_name in views if view_name else False

            if exists:

                st.caption("Nama sudah ada. Menyimpan akan **menimpa** tampilan tersebut.")



            btn_cols = st.columns(2)

            with btn_cols[0]:

                if button(

                    "Simpan",

                    key=f"{store_key}__save",

                    kind="primary",

                    disabled=not can_save,

                ):

                    views[view_name] = export_payload

                    st.session_state[store_key] = views

                    st.session_state[active_key] = view_name

                    st.session_state[notice_key] = "Tampilan tersimpan."

                    st.rerun()



            with btn_cols[1]:

                if secondary_button(

                    "Reset filter",

                    key=f"{store_key}__reset",

                    help="Kembalikan filter ke default",

                ):

                    for k in keys:

                        if k in st.session_state:

                            del st.session_state[k]

                    st.session_state[notice_key] = "Filter di-reset."

                    st.rerun()



            st.divider()



            # Progressive disclosure: advanced share/export/import

            with st.expander("Bagikan / Export / Import", expanded=False):

                export_text = json.dumps(export_payload, ensure_ascii=False, indent=2, default=_json_default)

                st.caption("Bagikan konfigurasi filter tanpa screenshot.")



                st.text_area(

                    "Export JSON",

                    value=export_text,

                    height=140,

                    key=f"{store_key}__export",

                )



                st.text_input(

                    "Link (tambahkan ke URL saat ini)",

                    value=build_share_query(keys=keys),

                    key=f"{store_key}__share_link",

                )



                import_text = st.text_area(

                    "Import JSON",

                    value="",

                    height=120,

                    key=f"{store_key}__import",

                    placeholder="Paste JSON di sini.",

                )



                if secondary_button(

                    "Import",

                    key=f"{store_key}__import_btn",

                    disabled=not bool(import_text.strip()),

                    help="Terapkan konfigurasi dari JSON.",

                ):

                    try:

                        payload = json.loads(import_text)

                        if not isinstance(payload, dict):

                            raise ValueError("payload bukan object JSON")

                        _apply_payload(payload)

                        st.session_state[notice_key] = "Konfigurasi berhasil di-import."

                        st.rerun()

                    except Exception:

                        st.error("JSON tidak valid.")



        with col_b:

            names = sorted(views.keys())

            selected = st.selectbox(

                "Pilih tampilan",

                options=["(pilih)"] + names,

                index=0,

                key=f"{store_key}__selected",

            )



            can_apply = selected != "(pilih)"

            if button(

                "Terapkan",

                key=f"{store_key}__apply",

                kind="primary",

                disabled=not can_apply,

            ):

                _apply_payload(views.get(selected, {}))

                st.session_state[active_key] = selected

                st.session_state[notice_key] = f"Tampilan diterapkan: {selected}" if can_apply else ""

                st.rerun()



            st.checkbox(

                "Konfirmasi hapus",

                key=confirm_key,

                value=False,

                disabled=not can_apply,

                help="Centang dulu sebelum menghapus tampilan.",

            )

            confirm = bool(st.session_state.get(confirm_key))



            if danger_button(

                "Hapus",

                key=f"{store_key}__delete",

                disabled=(not can_apply) or (not confirm),

                help="Aksi ini tidak bisa dibatalkan.",

            ):

                if selected in views:

                    del views[selected]

                    st.session_state[store_key] = views

                    if st.session_state.get(active_key) == selected:

                        st.session_state.pop(active_key, None)

                    st.session_state[confirm_key] = False

                    st.session_state[notice_key] = "Tampilan dihapus."

                    st.rerun()





def page_title(title: str, caption: str | None = None) -> None:

    """Render judul halaman + caption opsional."""

    st.title(title)

    if caption:

        st.caption(caption)

    st.divider()





def empty_data_state(

    message: str,

    checks: Optional[Iterable[str]] = None,

) -> None:

    """Tampilkan empty-state yang actionable."""

    st.warning(message)

    if checks:

        st.caption("Periksa: " + "  ".join(checks))





def format_int(n: int) -> str:

    """Format integer untuk UI."""

    try:

        return f"{int(n):,}"

    except Exception:

        return str(n)



