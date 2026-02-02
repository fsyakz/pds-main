"""Programmatic smoke-test: GIS page renders without Streamlit exceptions.

Why this exists:
- The app uses custom navigation state (`app_page`) and multiple pages.
- We want a repeatable check that the GIS page can be opened end-to-end
  without raising `StreamlitAPIException` or other runtime errors.

How to run:
- From repo root:  python scripts/verify_gis_page.py

Exit code:
- 0 if the GIS page loads successfully
- 1 if any exception is raised while rendering
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn
import traceback

from streamlit.testing.v1 import AppTest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_FILE = REPO_ROOT / "src" / "app.py"
RUN_TIMEOUT_S = 30


def _fail(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if not APP_FILE.exists():
        _fail(f"App file not found: {APP_FILE}")

    at = AppTest.from_file(str(APP_FILE))

    # First run: load app, create widgets.
    at.run(timeout=RUN_TIMEOUT_S)
    try:
        exc_len = len(at.exception)
    except Exception:
        exc_len = 0

    if exc_len:
        _fail(f"Exception on initial app load: {at.exception}")

    def _sidebar_selectbox_by_label(label: str):
        for w in getattr(at.sidebar, "selectbox", []):
            if getattr(w, "label", None) == label:
                return w
        return None

    def _sidebar_radio_by_label(label: str):
        for w in getattr(at.sidebar, "radio", []):
            if getattr(w, "label", None) == label:
                return w
        return None

    cat = _sidebar_selectbox_by_label("Kategori")
    if cat is None:
        _fail("Sidebar selectbox 'Kategori' not found")
    try:
        cat.set_value("Inflasi")
    except Exception as e:
        opts = getattr(cat, "options", None)
        _fail(f"Failed to set sidebar selectbox 'Kategori' to 'Inflasi': {e}. options={opts}")

    nav = _sidebar_radio_by_label("Navigasi")
    if nav is None:
        _fail("Sidebar radio 'Navigasi' not found")
    try:
        nav.set_value("Analisis GIS Inflasi")
    except Exception as e:
        opts = getattr(nav, "options", None)
        _fail(f"Failed to set sidebar radio 'Navigasi' to GIS page: {e}. options={opts}")

    # Second run: render the GIS page.
    at.run(timeout=RUN_TIMEOUT_S)

    try:
        exc_len = len(at.exception)
    except Exception:
        exc_len = 0
    if exc_len:
        _fail(f"Exception while rendering GIS page: {at.exception}")

    # Flow B — new session: navigate via Dashboard quick button.
    # This path used to crash when it tried to mutate st.session_state['app_page']
    # after the sidebar widget had been instantiated.
    at2 = AppTest.from_file(str(APP_FILE))
    at2.run(timeout=RUN_TIMEOUT_S)
    try:
        exc_len = len(at2.exception)
    except Exception:
        exc_len = 0
    if exc_len:
        _fail(f"Exception while rendering Dashboard Utama (fresh session): {at2.exception}")

    # Find and click the 'Analisis GIS' button on the dashboard.
    try:
        candidates = []
        for b in getattr(at2, "button", []):
            label = getattr(b, "label", None)
            if label == "Analisis GIS":
                candidates.append(b)
        if not candidates:
            _fail("Dashboard button 'Analisis GIS' not found (UI changed?)")
        candidates[0].click()
        at2.run(timeout=RUN_TIMEOUT_S)
    except SystemExit:
        raise
    except Exception as e:
        _fail(f"Failed clicking dashboard button 'Analisis GIS': {e}")

    try:
        exc_len = len(at2.exception)
    except Exception:
        exc_len = 0
    if exc_len:
        _fail(f"Exception after clicking dashboard 'Analisis GIS': {at2.exception}")

    # Optional sanity signals: at least one plot/chart or dataframe should exist.
    # We keep these checks soft to avoid false negatives across Streamlit versions.
    n_plotly = len(getattr(at, "plotly_chart", []))
    n_df = len(getattr(at, "dataframe", []))
    n_warning = len(getattr(at, "warning", []))

    print("OK: GIS page rendered (sidebar + dashboard quick-nav)")
    print(f"Signals: plotly_chart={n_plotly}, dataframe={n_df}, warning={n_warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
