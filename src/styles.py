def get_custom_css() -> str:
    """Return small, theme-neutral CSS tweaks.

    Prinsip:
    - Mengandalkan *Choose app theme* bawaan Streamlit (Light/Dark/Custom).
    - Tidak meng-overwrite warna background/text global.
    - Hanya memperbaiki spacing, radius, dan sedikit “polish” yang aman.
    """

    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
            /* Biarkan browser menyesuaikan kontrol native utk light/dark */
            color-scheme: light dark;

            /* Streamlit sets these CSS variables (fallbacks keep things safe) */
            --pds-primary: var(--primary-color, #7C3AED);
            --pds-bg: var(--background-color, #FFFFFF);
            --pds-surface: var(--secondary-background-color, #F1F5F9);
            --pds-text: var(--text-color, #111827);
            --pds-font: var(--font, 'Inter', sans-serif);

            --pds-radius-lg: 16px;
            --pds-radius-md: 12px;
            --pds-shadow: 0 8px 18px rgba(0, 0, 0, 0.10);

            /* Purple accent, but restrained */
            --pds-border: 1px solid rgba(124, 58, 237, 0.16);
            --pds-accent-weak: rgba(124, 58, 237, 0.14);
            --pds-accent-strong: rgba(124, 58, 237, 0.28);
        }

        html, body {
            font-family: var(--pds-font);
        }

        /* Main container spacing */
        [data-testid="stMainBlockContainer"],
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Sidebar: subtle separation without forcing background */
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(124, 58, 237, 0.10);
        }

        /* Typography polish: make headings feel “designed” without being loud */
        [data-testid="stMainBlockContainer"] h1 {
            letter-spacing: -0.02em;
            line-height: 1.18;
            padding-left: 0.75rem;
            border-left: 4px solid var(--pds-primary);
        }

        [data-testid="stMainBlockContainer"] h2 {
            letter-spacing: -0.01em;
        }

        /* Divider: faint purple tint (very subtle) */
        [data-testid="stMainBlockContainer"] hr {
            border: 0;
            height: 1px;
            background: linear-gradient(
                90deg,
                transparent,
                var(--pds-accent-weak),
                transparent
            );
        }

        /* Widgets: only radius/typography (colors follow Streamlit theme) */
        [data-testid="stButton"] button,
        [data-testid="stDownloadButton"] button,
        [data-testid="stFormSubmitButton"] button {
            font-family: var(--pds-font);
            border-radius: var(--pds-radius-md);
            font-weight: 600;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stSelectbox [role="combobox"],
        .stMultiSelect [role="combobox"] {
            border-radius: var(--pds-radius-md);
            font-family: var(--pds-font);
        }

        /* Focus ring: accessible + on-brand (without overriding base colors) */
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus,
        .stSelectbox [role="combobox"]:focus-within,
        .stMultiSelect [role="combobox"]:focus-within,
        [data-testid="stButton"] button:focus-visible,
        [data-testid="stDownloadButton"] button:focus-visible,
        [data-testid="stFormSubmitButton"] button:focus-visible {
            outline: none !important;
            box-shadow: 0 0 0 3px var(--pds-accent-weak) !important;
        }

        /* Segmented control / Tabs: keep shape consistent */
        [data-testid="stSegmentedControl"] button,
        [data-testid="stTabs"] [role="tab"] {
            border-radius: 10px;
        }

        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            border-bottom: 2px solid var(--pds-primary);
        }

        [data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] span {
            color: var(--pds-primary) !important;
            font-weight: 600;
        }

        /* Segmented control active button (attributes vary by Streamlit version) */
        [data-testid="stSegmentedControl"] button[aria-pressed="true"],
        [data-testid="stSegmentedControl"] button[aria-selected="true"] {
            box-shadow: 0 0 0 3px var(--pds-accent-weak) !important;
        }

        /* Charts & tables: consistent “card” look, without recoloring */
        [data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border-radius: var(--pds-radius-lg);
            overflow: hidden;
            border: var(--pds-border);
            box-shadow: var(--pds-shadow);
        }

        /* Links: lean on theme but nudge to purple for coherence */
        [data-testid="stMainBlockContainer"] a {
            color: var(--pds-primary);
            text-decoration-thickness: 1px;
            text-underline-offset: 2px;
        }

        [data-testid="stMainBlockContainer"] a:hover {
            text-decoration: underline;
        }

        /* Avoid overly large bottom spacing between elements */
        .element-container {
            margin-bottom: 0.75rem;
        }

        /* Mobile */
        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"],
            .block-container {
                padding-top: 1.25rem;
                padding-bottom: 1.25rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }

        /* A11y: reduce motion */
        @media (prefers-reduced-motion: reduce) {
            * {
                transition: none !important;
                scroll-behavior: auto !important;
            }
        }
    </style>
    """
