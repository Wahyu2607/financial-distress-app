import streamlit as st


def inject_css(theme: str | None = None):
    current_theme = theme or st.session_state.get("theme", "light")
    is_light = (current_theme == "light")
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

        :root {
            /* Palette Dark Obsidian & Ambient FinTech Tokens */
            --canvas-bg: #070a12;
            --surface-glass: rgba(15, 23, 42, 0.72);
            --surface-glass-card: rgba(18, 27, 49, 0.85);
            --surface-neu-inset: rgba(10, 15, 26, 0.85);
            --border-specular: rgba(255, 255, 255, 0.08);
            --border-focus: #6366f1;

            /* Semantic Signals */
            --safe-teal: #14b8a6;
            --safe-teal-glow: rgba(20, 184, 166, 0.4);
            --safe-emerald: #10b981;
            --warn-amber: #f59e0b;
            --warn-amber-glow: rgba(245, 158, 11, 0.4);
            --danger-coral: #f43f5e;
            --danger-coral-glow: rgba(244, 63, 94, 0.45);
            --ai-violet: #8b5cf6;
            --ai-violet-glow: rgba(139, 92, 246, 0.4);
            --empirical-cyan: #06b6d4;
            --empirical-cyan-glow: rgba(6, 182, 212, 0.4);

            /* Typography */
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
        }

        /* 1. TIPOGRAFI GLOBAL & PERLINDUNGAN WARNA KONTRAS */
        html, body, .stApp, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, input, select, textarea {
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
            letter-spacing: -0.012em;
            color: #f8fafc;
            hyphens: none !important;
            -webkit-hyphens: none !important;
            word-break: normal !important;
        }

        /* Teks Markdown agar selalu terang dan kontras tinggi terhadap wadah/frame gelap */
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] span,
        div[data-testid="stMarkdownContainer"] li {
            color: #cbd5e1 !important;
        }
        div[data-testid="stMarkdownContainer"] strong,
        div[data-testid="stMarkdownContainer"] b {
            color: #ffffff !important;
        }
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4,
        div[data-testid="stMarkdownContainer"] h5,
        div[data-testid="stMarkdownContainer"] h6 {
            color: #ffffff !important;
        }

        /* Formula KaTeX / LaTeX Matematika agar putih cerah (bukan hitam default) */
        .katex, .katex-display, .katex *, [data-testid="stLatexContainer"], [data-testid="stLatexContainer"] * {
            color: #f8fafc !important;
        }

        .mono-num, code, .metric-value, [data-testid="stMetricValue"], .font-mono-num {
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums;
            color: #f8fafc !important;
        }

        /* PERLINDUNGAN IKON STREAMLIT & MATERIAL SYMBOLS */
        [data-testid*="Icon"],
        [data-testid="stIconMaterial"],
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-symbols-sharp,
        .material-icons,
        [class*="material-symbols"],
        [class*="material-icons"],
        div[data-testid="stExpander"] [data-testid="stIconMaterial"] {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
            font-size: 20px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* PERLINDUNGAN UTAMA TOMBOL SHOW/HIDE PASSWORD STREAMLIT (NATIVE & BASEWEB) */
        div[data-baseweb="base-input"] {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            position: relative !important;
            width: 100% !important;
        }

        div[data-baseweb="base-input"] > input {
            flex: 1 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }

        div[data-baseweb="input"] button,
        div[data-baseweb="base-input"] button,
        button[data-testid*="stTextInputPasswordToggle"],
        [data-testid="stTextInputPasswordToggle"],
        button[aria-label*="password" i],
        button[aria-label*="visibility" i] {
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            align-items: center !important;
            justify-content: center !important;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            cursor: pointer !important;
            pointer-events: auto !important;
            width: 34px !important;
            min-width: 34px !important;
            max-width: 34px !important;
            height: 34px !important;
            min-height: 34px !important;
            padding: 0 !important;
            margin: 0 4px 0 0 !important;
            color: #94a3b8 !important;
            flex-shrink: 0 !important;
            z-index: 10 !important;
            transition: color 0.2s ease, transform 0.15s ease !important;
        }

        div[data-baseweb="input"] button:hover,
        div[data-baseweb="base-input"] button:hover,
        button[data-testid*="stTextInputPasswordToggle"]:hover,
        button[aria-label*="password" i]:hover,
        button[aria-label*="visibility" i]:hover {
            color: #38bdf8 !important;
            transform: scale(1.08) !important;
        }

        div[data-baseweb="input"] button svg,
        div[data-baseweb="base-input"] button svg,
        button[data-testid*="stTextInputPasswordToggle"] svg,
        [data-testid="stTextInputPasswordToggle"] svg,
        button[aria-label*="password" i] svg,
        button[aria-label*="visibility" i] svg {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 20px !important;
            height: 20px !important;
            min-width: 20px !important;
            min-height: 20px !important;
            fill: currentColor !important;
            color: inherit !important;
            stroke: none !important;
        }

        div[data-baseweb="input"] button *,
        div[data-baseweb="base-input"] button *,
        button[aria-label*="password" i] *,
        button[aria-label*="visibility" i] * {
            visibility: visible !important;
            opacity: 1 !important;
        }

        /* 2. LATAR BELAKANG KANVAS UTAMA (UNIFIED DARK MODE WITH AMBIENT EMERALD GLOW) */
        .stApp, .stAppViewContainer, [data-testid="stAppViewContainer"] {
            background-color: #030806 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(16, 185, 129, 0.18) 0px, transparent 55%),
                radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(5, 20, 14, 0.8) 0px, transparent 75%),
                radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.12) 0px, transparent 45%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.08) 0px, transparent 45%) !important;
            background-attachment: fixed !important;
            color: #f8fafc !important;
        }

        /* Sembunyikan header default Streamlit */
        header.stAppHeader, [data-testid="stHeader"], [data-testid="stDecoration"], #stDecoration, [data-testid="stToolbar"], #MainMenu, .stDeployButton {
            display: none !important;
        }

        /* HILANGKAN SEMUA ANCHOR LINK ICON / HOVER LINK PADA SEMUA JUDUL & KONTEN */
        [data-testid="stHeaderActionElements"],
        div[data-testid="stHeadingWithActionElements"] > div,
        .stHeadingWithActionElements [data-testid="stHeaderActionElements"],
        a.anchorjs-link,
        .anchorjs-link,
        .stHeadingWithActionElements a,
        h1 a, h2 a, h3 a, h4 a, h5 a, h6 a,
        h1 a.anchor-link, h2 a.anchor-link, h3 a.anchor-link,
        [data-testid="stMarkdownContainer"] h1 a,
        [data-testid="stMarkdownContainer"] h2 a,
        [data-testid="stMarkdownContainer"] h3 a,
        [data-testid="stMarkdownContainer"] h4 a,
        [data-testid="stMarkdownContainer"] h5 a,
        [data-testid="stMarkdownContainer"] h6 a {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Pastikan container judul Streamlit tidak menggeser posisi teks */
        div[data-testid="stHeadingWithActionElements"] {
            display: block !important;
            width: 100% !important;
        }

        section.stMain .block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
            padding-top: 0.6rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.6rem !important;
            padding-right: 1.25rem !important;
            max-width: 1720px !important;
            overflow: visible !important;
        }

        [data-testid="stMainBlockContainer"] > div,
        [data-testid="stMainBlockContainer"] > div [data-testid="stHorizontalBlock"]:first-of-type {
            overflow: visible !important;
            align-items: flex-start !important;
        }

        /* ========================================================================== */
        /* 1. EDGE-TO-EDGE FLUSH LEFT FIXED FULL-HEIGHT SIDEBAR (LEFT-0 TOP-0 H-SCREEN) */
        /* ========================================================================== */
        /* Pastikan Streamlit Main Container Menempel Sempurna Tanpa Padding Kiri */
        [data-testid="stMainBlockContainer"],
        .main .block-container {
            padding-top: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
        }

        /* ========================================================================== */
        /* 1. DESKTOP VIEWPORT (MIN-WIDTH: 992PX): FIXED EDGE-TO-EDGE LEFT SIDEBAR    */
        /* ========================================================================== */
        @media (min-width: 992px) {
            div[data-testid="stHorizontalBlock"]:has(.sidebar-vault-container) {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: stretch !important;
                gap: 0 !important;
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            /* Sidebar Menempel Rapat Tanpa Celah di Sisi Paling Kiri Layar (Edge-to-Edge) */
            div[data-testid="column"]:has(.sidebar-vault-container),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                bottom: 0 !important;
                height: 100vh !important;
                min-height: 100vh !important;
                max-height: 100vh !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
                z-index: 9999 !important;
                scrollbar-width: none !important;
                -ms-overflow-style: none !important;

                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-start !important;
                align-items: stretch !important;

                /* Sidebar Permanen Terbuka: Lebar Tetap 270px, Menempel Sisi Kiri & Warna Abu-abu Gelap Kebiruan Elegan */
                flex: 0 0 270px !important;
                width: 270px !important;
                min-width: 270px !important;
                max-width: 270px !important;
                padding: 14px 14px 14px 14px !important;
                padding-top: 14px !important;
                margin-top: 0 !important;
                box-sizing: border-box !important;

                /* Latar Belakang Khusus: Abu-abu Gelap Kebiruan yang Elegan (Refined Deep Slate Navy) */
                background: #141726 !important;
                background-color: #141726 !important;
                border: none !important;
                border-right: 1.5px solid rgba(148, 163, 184, 0.16) !important;
                border-radius: 0 !important;
                box-shadow: 6px 0 28px rgba(0, 0, 0, 0.5) !important;
                transform: translateX(0) !important;
                opacity: 1 !important;
                visibility: visible !important;
                pointer-events: auto !important;
            }

            /* Kolom Konten Utama di Sebelah Kanan Mengisi Sisa Lebar Layar (margin-left: 270px) */
            div[data-testid="column"]:has(.sidebar-vault-container) ~ div[data-testid="column"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) ~ div[data-testid="stColumn"],
            div[data-testid="column"]:has(.sidebar-vault-container) + div[data-testid="column"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) + div[data-testid="stColumn"] {
                margin-left: 270px !important;
                flex: 1 1 calc(100% - 270px) !important;
                min-width: 0 !important;
                width: calc(100% - 270px) !important;
                max-width: calc(100% - 270px) !important;
                padding: 0 24px 32px 24px !important;
                box-sizing: border-box !important;
            }

            .mobile-top-bar,
            .mobile-top-bar-spacer,
            .mobile-drawer-backdrop,
            .mobile-drawer-close-row {
                display: none !important;
                visibility: hidden !important;
                pointer-events: none !important;
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        }

        div[data-testid="column"]:has(.sidebar-vault-container)::-webkit-scrollbar,
        div[data-testid="stColumn"]:has(.sidebar-vault-container)::-webkit-scrollbar {
            display: none !important;
        }

        /* HILANGKAN ELEMEN MARKER TEKNIS AGAR TIDAK MEMAKAN RUANG ATAU MENAMBAH GAP FLEX */
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-vault-container),
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-vault-container),
        .sidebar-vault-container {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            position: absolute !important;
            pointer-events: none !important;
        }

        /* Marker Jangkar Puncak Halaman (Top-of-Page Anchor) untuk Auto-Scroll Menu */
        #vault-view-top-anchor {
            scroll-margin-top: 0 !important;
            position: relative !important;
            top: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* Iframe Scroll Manager Komponen Tersembunyi (0-Height Tanpa Gap Layout) */
        iframe[height="0"],
        div[data-testid="stCustomComponentV1"]:has(iframe[height="0"]),
        div[data-testid="element-container"]:has(iframe[height="0"]),
        div[data-testid="stElementContainer"]:has(iframe[height="0"]) {
            display: block !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            overflow: hidden !important;
            position: absolute !important;
            pointer-events: none !important;
        }

        /* STRUKTUR TATA LETAK UTAMA: FLEXBOX VERTIKAL - ELEMEN ATAS SELALU MENEMPEL DI PUNCAK (TOP-0) */
        div[data-testid="column"]:has(.sidebar-vault-container) > div,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) > div,
        div[data-testid="column"]:has(.sidebar-vault-container) > [data-testid="stVerticalBlock"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) > [data-testid="stVerticalBlock"],
        div[data-testid="column"]:has(.sidebar-vault-container) > div > [data-testid="stVerticalBlock"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) > div > [data-testid="stVerticalBlock"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            padding: 0 !important;
            padding-top: 0 !important;
            margin: 0 !important;
            margin-top: 0 !important;
            height: 100% !important;
            min-height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            align-items: stretch !important;
            flex: 1 1 100% !important;
            width: 100% !important;
            gap: 0 !important;
        }

        /* Pastikan elemen anak pertama (Logo Header) menempel rapat di puncak tanpa margin atas */
        div[data-testid="column"]:has(.sidebar-vault-container) > [data-testid="stVerticalBlock"] > div:first-child,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) > [data-testid="stVerticalBlock"] > div:first-child,
        div[data-testid="column"]:has(.sidebar-vault-container) > div > [data-testid="stVerticalBlock"] > div:first-child,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) > div > [data-testid="stVerticalBlock"] > div:first-child,
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-logo-header),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-logo-header),
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-logo-header),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-logo-header) {
            margin: 0 !important;
            margin-top: 0 !important;
            padding: 0 !important;
            padding-top: 0 !important;
            flex: 0 0 auto !important;
        }

        /* 1. DYNAMIC FLEX SPACER: MENYERAP RUANG KOSONG DI TENGAH SECARA MAKSIMAL */
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-spacer),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-spacer),
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-spacer),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-spacer),
        .sidebar-spacer {
            display: flex !important;
            flex: 1 1 auto !important;
            flex-grow: 1 !important;
            flex-shrink: 1 !important;
            min-height: 24px !important;
            height: auto !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
            pointer-events: none !important;
        }

        /* 2. BAGIAN AKUN DI DASAR SIDEBAR (DIPOSISIKAN MENEMPEL DI BAWAH VIA MARGIN-TOP: AUTO) */
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-account-label),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(.sidebar-account-label),
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-account-label),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(.sidebar-account-label) {
            margin-top: auto !important;
            margin-bottom: 2px !important;
            padding: 0 !important;
            flex: 0 0 auto !important;
        }

        /* ISOLASI TOTAL KOLOM KONTEN / NESTED COLUMNS (TIDAK BOLEH MEMILIKI GAYA SIDEBAR) */
        div[data-testid="column"] div[data-testid="column"],
        div[data-testid="column"] div[data-testid="stColumn"],
        div[data-testid="stColumn"] div[data-testid="column"],
        div[data-testid="stColumn"] div[data-testid="stColumn"] {
            position: static !important;
            top: auto !important;
            align-self: auto !important;
            max-height: none !important;
            overflow: visible !important;
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            z-index: auto !important;
        }

        /* STANDALONE LOGO HEADER DENGAN NAMA BRAND "DISTRESS PREDICTION" (POSISI NAIK KE ATAS - TOP 0) */
        .sidebar-logo-header {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 12px !important;
            margin: 0 0 10px 0 !important;
            padding: 0 !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }

        .sidebar-logo-icon {
            width: 46px !important;
            height: 46px !important;
            min-width: 46px !important;
            max-width: 46px !important;
            border-radius: 14px !important;
            background: linear-gradient(135deg, #1b2137 0%, #293254 100%) !important;
            border: 1px solid rgba(148, 163, 184, 0.25) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45) !important;
            color: #ffffff !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }

        .sidebar-logo-icon:hover {
            border-color: rgba(255, 255, 255, 0.35) !important;
            transform: scale(1.03) !important;
        }

        .sidebar-logo-icon svg {
            width: 24px !important;
            height: 24px !important;
            display: block !important;
        }

        /* PERMANEN: TEKS LOGO "DISTRESS PREDICTION" SELALU DITAMPILKAN TETAP */
        .sidebar-logo-text-col {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            max-width: 180px !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            overflow: hidden !important;
            white-space: nowrap !important;
        }

        .sidebar-logo-title {
            font-size: 15px !important;
            font-weight: 850 !important;
            color: #ffffff !important;
            letter-spacing: 0.3px !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .sidebar-logo-subtitle {
            font-size: 10px !important;
            color: #94a3b8 !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            margin-top: 2px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* LABEL KATEGORI / SECTION (TAMPIL JELAS DAN TEGAS TANPA TERTUTUPI) */
        .sidebar-section-label {
            font-size: 10px !important;
            font-weight: 800 !important;
            color: #7b8ea6 !important;
            letter-spacing: 1.2px !important;
            text-transform: uppercase !important;
            margin: 8px 0 10px 4px !important;
            display: block !important;
            line-height: 1.4 !important;
            height: auto !important;
            max-height: none !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 5 !important;
        }

        /* ITEM MENU NAVIGASI: RADIO BUTTONS - LEBAR PENUH 100% FLUSH EDGE-TO-EDGE */
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(div[data-testid="stRadio"]),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="element-container"]:has(div[data-testid="stRadio"]),
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(div[data-testid="stRadio"]),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stElementContainer"]:has(div[data-testid="stRadio"]),
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            margin: 0 !important;
            margin-top: 10px !important; /* Memberikan jarak vertikal yang nyaman agar tidak menutupi tulisan analisis dan prediksi */
            padding: 0 !important;
            padding-top: 0 !important;
        }
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label[data-testid="stWidgetLabel"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label[data-testid="stWidgetLabel"] {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
            justify-content: flex-start !important;
            gap: 8px !important;
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
            transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        /* Item Menu Default (Expanded): Lebar Penuh 100% Stretch tanpa ruang kosong di kanan */
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            align-self: stretch !important;
            flex: 1 1 100% !important;
            height: 50px !important;
            min-height: 50px !important;
            max-height: 50px !important;
            margin: 0 !important;
            padding: 0 !important;
            border-radius: 15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            background: #1b2136 !important;
            border: 1px solid #283150 !important;
            color: #94a3b8 !important;
            overflow: hidden !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-sizing: border-box !important;
            position: relative !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label *,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label * {
            color: inherit !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:hover,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
            background: #232b47 !important;
            border-color: rgba(148, 163, 184, 0.35) !important;
            color: #ffffff !important;
            transform: none !important;
        }

        /* Struktur Internal Label Radio dalam Keadaan Default Expanded */
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"],
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:last-child,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:last-child,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-testid="stMarkdownContainer"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            height: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: flex-start !important;
            font-size: 20px !important;
            line-height: 1 !important;
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            height: 100% !important;
            text-align: left !important;
            padding: 0 16px !important;
            margin: 0 !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p strong,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p strong {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: static !important;
            width: auto !important;
            height: auto !important;
            margin-left: 12px !important;
            font-size: 13.5px !important;
            font-weight: 650 !important;
            letter-spacing: 0.1px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            flex: 1 1 auto !important;
            min-width: 0 !important;
            line-height: 1.3 !important;
        }



        /* 3. Active Radio Item: Frame Putih Bersih dengan Ikon & Teks Gelap Kontras Tinggi */
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked),
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            align-self: stretch !important;
            flex: 1 1 100% !important;
            box-sizing: border-box !important;
            background: #ffffff !important;
            color: #09090b !important;
            font-weight: 850 !important;
            border-radius: 15px !important;
            border: 1px solid #ffffff !important;
            box-shadow: 0 8px 24px -2px rgba(0, 0, 0, 0.45), 0 0 16px rgba(255, 255, 255, 0.25) !important;
            transform: none !important;
            animation: none !important;
        }
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) *,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) *,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p strong,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p strong,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) span,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) span {
            color: #09090b !important;
            font-weight: 850 !important;
        }

        /* LOGIKA VISUAL SINGLE-SELECT RADIO BUTTONS (AREA UTAMA/NON-SIDEBAR) */
        /* Opsi TIDAK TERPILIH (UNCHECKED): Hapus total lingkaran hijau, aksen hijau, dan glow */
        div[data-testid="stRadio"] label:not(:has(input:checked)),
        div[data-testid="stRadio"] label[data-checked="false"] {
            border-color: transparent !important;
            box-shadow: none !important;
            animation: none !important;
        }
        div[data-testid="stRadio"] label:not(:has(input:checked)) [data-baseweb="radio"] > div:first-child,
        div[data-testid="stRadio"] label[data-checked="false"] [data-baseweb="radio"] > div:first-child {
            border: 1.5px solid #64748b !important;
            background-color: transparent !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        div[data-testid="stRadio"] label:not(:has(input:checked)) [data-baseweb="radio"] > div:first-child *,
        div[data-testid="stRadio"] label[data-checked="false"] [data-baseweb="radio"] > div:first-child * {
            display: none !important;
            opacity: 0 !important;
            background: transparent !important;
        }

        /* Opsi TERPILIH (CHECKED): Tepat SATU indikator lingkaran hijau menyala yang aktif */
        div[data-testid="stRadio"]:not(:has(.sidebar-vault-container)) label:has(input:checked) [data-baseweb="radio"] > div:first-child,
        div[data-testid="stRadio"]:not(:has(.sidebar-vault-container)) label[data-checked="true"] [data-baseweb="radio"] > div:first-child {
            border: 2px solid #10b981 !important;
            background-color: #10b981 !important;
            background: #10b981 !important;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.8), 0 0 4px rgba(16, 185, 129, 0.4) !important;
        }
        div[data-testid="stRadio"]:not(:has(.sidebar-vault-container)) label:has(input:checked) [data-baseweb="radio"] > div:first-child div,
        div[data-testid="stRadio"]:not(:has(.sidebar-vault-container)) label[data-checked="true"] [data-baseweb="radio"] > div:first-child div {
            background-color: #ffffff !important;
            background: #ffffff !important;
            display: block !important;
            opacity: 1 !important;
        }
        /* HILANGKAN SEMUA BULATAN RADIO STREAMLIT SECARA TOTAL (TAMPILAN MODERN PILL LIST) */
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:not(:last-child),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:not(:last-child),
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label > div > div:first-child,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label > div > div:first-child,
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label > div:first-child:not(:has([data-testid="stMarkdownContainer"])),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label > div:first-child:not(:has([data-testid="stMarkdownContainer"])),
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] input[type="radio"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] input[type="radio"],
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [aria-hidden="true"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [aria-hidden="true"],
        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] svg,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] svg {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] {
            align-items: center !important;
            gap: 0 !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:last-child,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] > div:last-child {
            width: 100% !important;
            padding: 0 !important;
        }



        /* ========================================================================== */
        /* 2. PROFIL PENGGUNA (BAGIAN PALING BAWAH SIDEBAR)                           */
        /* ========================================================================== */
        /* Container Kartu Profil: Default Expanded (Lebar Penuh dengan Avatar, Nama, Email, dan Tombol) */
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block),
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: space-between !important;
            background: #1b2136 !important;
            background-color: #1b2136 !important;
            border: 1px solid #283150 !important;
            border-radius: 16px !important;
            padding: 7px 12px 7px 7px !important;
            margin: 0 !important;
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            height: auto !important;
            min-height: 56px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
            gap: 10px !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block):hover,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block):hover {
            background: #232b47 !important;
            background-color: #232b47 !important;
            border-color: rgba(148, 163, 184, 0.35) !important;
        }

        /* Hilangkan Margin / Padding Default Streamlit di Dalam Profil Card */
        [data-testid="stHorizontalBlock"]:has(.sidebar-user-block),
        [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) * {
            box-sizing: border-box !important;
        }

        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) div[data-testid="column"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) div[data-testid="stColumn"],
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) [data-testid="stVerticalBlock"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) [data-testid="stVerticalBlock"],
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) [data-testid="element-container"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) [data-testid="element-container"],
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) [data-testid="stMarkdownContainer"],
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) [data-testid="stMarkdownContainer"],
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) p,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
        }

        /* Struktur Internal User Block & Avatar */
        .sidebar-user-block {
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 10px !important;
            width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            position: relative !important;
        }

        .user-avatar-wrapper {
            position: relative !important;
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            min-height: 38px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            padding: 0 !important;
            flex-shrink: 0 !important;
        }

        .user-avatar-img {
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            min-height: 38px !important;
            border-radius: 50% !important;
            object-fit: cover !important;
            display: block !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
        }

        .user-status-dot {
            position: absolute !important;
            bottom: 0px !important;
            right: 0px !important;
            width: 10px !important;
            height: 10px !important;
            border-radius: 50% !important;
            background: #10b981 !important;
            border: 2px solid #171820 !important;
            box-shadow: 0 0 6px #10b981 !important;
            z-index: 2 !important;
        }

        /* Default (Expanded): Kolom Teks Nama & Role Terlihat Jelas */
        .user-meta-col {
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            justify-content: center !important;
            width: auto !important;
            opacity: 1 !important;
            min-width: 0 !important;
            overflow: hidden !important;
        }

        .user-name-bold {
            font-size: 13.5px !important;
            font-weight: 800 !important;
            color: #f8fafc !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.2 !important;
        }

        .user-email-text {
            font-size: 11px !important;
            font-weight: 500 !important;
            color: #94a3b8 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.2 !important;
            margin-top: 2px !important;
        }



        /* TOMBOL IKON PENA CEPAT EDIT (QUICK EDIT PEN BUTTON) */
        .st-key-btn_quick_edit_profile,
        .st-key-btn_quick_edit_profile > div,
        .st-key-btn_quick_edit_profile button,
        button[data-testid*="btn_quick_edit_profile"],
        div[data-testid*="btn_quick_edit_profile"] button {
            background: rgba(255, 255, 255, 0.06) !important;
            background-color: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            outline: none !important;
            width: 28px !important;
            height: 28px !important;
            min-width: 28px !important;
            max-width: 28px !important;
            min-height: 28px !important;
            max-height: 28px !important;
            padding: 0 !important;
            margin: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            color: #94a3b8 !important;
            font-size: 13px !important;
            line-height: 1 !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        .st-key-btn_quick_edit_profile button:hover,
        button[data-testid*="btn_quick_edit_profile"]:hover,
        div[data-testid*="btn_quick_edit_profile"] button:hover {
            background: rgba(37, 99, 235, 0.2) !important;
            background-color: rgba(37, 99, 235, 0.2) !important;
            border-color: rgba(37, 99, 235, 0.5) !important;
            color: #ffffff !important;
            transform: scale(1.08) !important;
            box-shadow: 0 0 10px rgba(37, 99, 235, 0.35) !important;
        }

        .st-key-btn_quick_edit_profile button p,
        .st-key-btn_quick_edit_profile button span,
        .st-key-btn_quick_edit_profile button div {
            color: inherit !important;
            font-size: 13px !important;
            line-height: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* PEMBATAS DAN TOMBOL LOGOUT DINONAKTIFKAN (DISEMBUNYIKAN PENUH) */
        .sidebar-logout-spacer,
        div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_sidebar_logout_bottom,
        div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_sidebar_logout_bottom > div,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_sidebar_logout_bottom,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_sidebar_logout_bottom > div,
        button[data-testid*="btn_sidebar_logout_bottom"],
        div[data-testid*="btn_sidebar_logout_bottom"] button {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }



        @keyframes fadeInMenu {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* TOMBOL HAMBURGER RESPOCONSIF DI HEADER UTAMA */
        button[data-testid*="btn_hamburger_main"] {
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
            border-radius: 14px !important;
            background: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            color: #f8fafc !important;
            font-size: 20px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 !important;
            cursor: pointer !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }

        button[data-testid*="btn_hamburger_main"]:hover {
            background: rgba(16, 185, 129, 0.25) !important;
            border-color: rgba(16, 185, 129, 0.5) !important;
            color: #ffffff !important;
            transform: scale(1.05) !important;
        }

        button[data-testid*="btn_hamburger_main"] p,
        button[data-testid*="btn_hamburger_main"] span {
            font-size: 20px !important;
            line-height: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
            color: inherit !important;
        }

        /* PERATAAN VERTIKAL UNTUK BLOK USER ACCOUNT ROW */
        div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"] {
            align-items: center !important;
            gap: 6px !important;
        }

        /* ========================================================================== */
        /* RESPONSIVITAS DEVICE & UKURAN LAYAR LAPTOP                                 */
        /* Sidebar Tetap Permanen Terbuka Lebar 270px dengan Skala Proporsional      */
        /* ========================================================================== */
        @media (min-width: 992px) {
            /* Laptop / Desktop: Sidebar Terbuka Permanen 270px */
            div[data-testid="column"]:has(.sidebar-vault-container),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                width: 270px !important;
                min-width: 270px !important;
                max-width: 270px !important;
                flex: 0 0 270px !important;
            }
        }

        @media (max-height: 840px) {
            div[data-testid="column"]:has(.sidebar-vault-container),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                padding: 12px 12px 14px 12px !important;
            }

            .sidebar-logo-header {
                margin: 0 0 10px 0 !important;
            }

            .sidebar-logo-icon {
                width: 42px !important;
                height: 42px !important;
                min-width: 42px !important;
                max-width: 42px !important;
                border-radius: 12px !important;
            }

            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] {
                gap: 6px !important;
            }

            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label {
                height: 46px !important;
                min-height: 46px !important;
                max-height: 46px !important;
                border-radius: 14px !important;
            }

            .sidebar-bottom-spacer {
                min-height: 12px !important;
            }
        }

        /* ========================================================================== */
        /* RESPONSIVITAS HANDPHONE, TABLET, DAN TRANSISI PERGANTIAN PERANGKAT        */
        /* (MOBILE-FIRST ADAPTIVE LAYOUT & TOUCH-OPTIMIZED CONTROLS)                  */
        /* ========================================================================== */
        @media (max-width: 991px) {
            /* 1. Mencegah horizontal viewport overflow */
            html, body, .stApp, section.stMain, [data-testid="stMainBlockContainer"], .stMainBlockContainer {
                overflow-x: hidden !important;
                max-width: 100vw !important;
            }

            /* 2. Container blok layout utama Streamlit menjadi full width */
            div[data-testid="stHorizontalBlock"]:has(.sidebar-vault-container) {
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            /* 3. Konten Utama Mengisi 100% Lebar Layar Mobile tanpa Margin Kiri Desktop */
            div[data-testid="column"]:has(.sidebar-vault-container) ~ div[data-testid="column"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) ~ div[data-testid="stColumn"],
            div[data-testid="column"]:has(.sidebar-vault-container) + div[data-testid="column"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) + div[data-testid="stColumn"],
            div[data-testid="column"]:has(.vault-canvas-header),
            div[data-testid="stColumn"]:has(.vault-canvas-header) {
                margin-left: 0 !important;
                margin-top: 0 !important;
                flex: 1 1 100% !important;
                width: 100% !important;
                max-width: 100% !important;
                padding: 8px 12px 36px 12px !important;
                box-sizing: border-box !important;
            }

            /* 4. Sidebar Menjadi Slide-Out Drawer Mengambang (Off-Canvas Drawer) */
            div[data-testid="column"]:has(.sidebar-vault-container),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                bottom: 0 !important;
                width: 290px !important;
                max-width: 86vw !important;
                height: 100vh !important;
                min-height: 100vh !important;
                max-height: 100vh !important;
                z-index: 9999999 !important;
                overflow-y: auto !important;
                overflow-x: hidden !important;
                padding: 14px 14px 24px 14px !important;
                box-sizing: border-box !important;

                background: #141726 !important;
                background-color: #141726 !important;
                border: none !important;
                border-right: 1.5px solid rgba(148, 163, 184, 0.25) !important;
                border-radius: 0 20px 20px 0 !important;
                box-shadow: 20px 0 60px rgba(0, 0, 0, 0.85) !important;

                /* Default: Tertutup di Luar Layar Sebelah Kiri */
                transform: translateX(-105%) !important;
                opacity: 0 !important;
                visibility: hidden !important;
                pointer-events: none !important;
                transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease, visibility 0.28s !important;
            }

            /* Terbuka Saat body memiliki class mobile-nav-open */
            body.mobile-nav-open div[data-testid="column"]:has(.sidebar-vault-container),
            body.mobile-nav-open div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                transform: translateX(0) !important;
                opacity: 1 !important;
                visibility: visible !important;
                pointer-events: auto !important;
            }

            /* 5. Mobile Drawer Backdrop Gelap */
            .mobile-drawer-backdrop {
                display: block !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(3, 7, 18, 0.72) !important;
                backdrop-filter: blur(5px) !important;
                -webkit-backdrop-filter: blur(5px) !important;
                z-index: 9999990 !important;
                opacity: 0 !important;
                pointer-events: none !important;
                visibility: hidden !important;
                transition: opacity 0.25s ease, visibility 0.25s ease !important;
            }

            body.mobile-nav-open .mobile-drawer-backdrop {
                opacity: 1 !important;
                pointer-events: auto !important;
                visibility: visible !important;
            }

            /* 6. Mobile Top Navigation Bar (Fixed Always-On-Top Header) */
            .mobile-top-bar {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 10px !important;
                height: 52px !important;
                min-height: 52px !important;
                max-height: 52px !important;
                padding: 0 16px !important;
                background: rgba(15, 23, 42, 0.95) !important;
                backdrop-filter: blur(20px) !important;
                -webkit-backdrop-filter: blur(20px) !important;
                border: none !important;
                border-bottom: 1.5px solid rgba(148, 163, 184, 0.22) !important;
                border-radius: 0 0 16px 16px !important;
                box-shadow: 0 4px 22px rgba(0, 0, 0, 0.5) !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                z-index: 999990 !important;
                pointer-events: auto !important;
            }

            .mobile-top-bar-spacer {
                display: block !important;
                width: 100% !important;
                height: 54px !important;
                min-height: 54px !important;
                max-height: 54px !important;
                margin: 0 0 10px 0 !important;
                padding: 0 !important;
                pointer-events: none !important;
                visibility: hidden !important;
            }

            .mobile-hamburger-btn {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 6px !important;
                height: 36px !important;
                padding: 0 11px !important;
                border-radius: 9px !important;
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
                border: 1px solid rgba(148, 163, 184, 0.3) !important;
                color: #ffffff !important;
                font-size: 12px !important;
                font-weight: 750 !important;
                cursor: pointer !important;
                user-select: none !important;
                -webkit-user-select: none !important;
                transition: all 0.2s ease !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
                flex-shrink: 0 !important;
            }

            .mobile-hamburger-btn:hover,
            .mobile-hamburger-btn:active {
                background: #2563eb !important;
                border-color: #3b82f6 !important;
                color: #ffffff !important;
                transform: scale(0.96) !important;
            }

            .hamburger-icon {
                font-size: 16px !important;
                line-height: 1 !important;
            }

            .mobile-brand-pill {
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                overflow: hidden !important;
            }

            .mobile-brand-logo {
                width: 26px !important;
                height: 26px !important;
                border-radius: 7px !important;
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                font-size: 13px !important;
                color: #ffffff !important;
                flex-shrink: 0 !important;
                box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4) !important;
            }

            .mobile-brand-title {
                font-size: 12.5px !important;
                font-weight: 800 !important;
                color: #f8fafc !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                letter-spacing: -0.2px !important;
            }

            .mobile-page-indicator {
                display: flex !important;
                align-items: center !important;
                justify-content: flex-end !important;
                flex-shrink: 0 !important;
            }

            .mobile-page-badge {
                font-size: 10.5px !important;
                font-weight: 750 !important;
                color: #38bdf8 !important;
                background: rgba(56, 189, 248, 0.12) !important;
                border: 1px solid rgba(56, 189, 248, 0.3) !important;
                padding: 3px 8px !important;
                border-radius: 7px !important;
                white-space: nowrap !important;
                max-width: 110px !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }

            /* Tombol Tutup di Dalam Drawer */
            .mobile-drawer-close-row {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                padding: 0 0 10px 0 !important;
                margin-bottom: 8px !important;
                border-bottom: 1px solid rgba(148, 163, 184, 0.15) !important;
                width: 100% !important;
            }

            .mobile-drawer-title {
                font-size: 10px !important;
                font-weight: 800 !important;
                color: #94a3b8 !important;
                letter-spacing: 1px !important;
                text-transform: uppercase !important;
            }

            .mobile-drawer-close-btn {
                display: inline-flex !important;
                align-items: center !important;
                gap: 5px !important;
                background: rgba(239, 68, 68, 0.15) !important;
                border: 1px solid rgba(239, 68, 68, 0.35) !important;
                color: #fca5a5 !important;
                border-radius: 7px !important;
                padding: 4px 10px !important;
                font-size: 11px !important;
                font-weight: 750 !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }

            .mobile-drawer-close-btn:hover,
            .mobile-drawer-close-btn:active {
                background: #ef4444 !important;
                color: #ffffff !important;
            }

            /* 7. Header Konten Responsif */
            .vault-canvas-header {
                flex-direction: column !important;
                align-items: stretch !important;
                gap: 10px !important;
                padding: 12px 14px !important;
                border-radius: 16px !important;
                margin-bottom: 14px !important;
            }

            .header-main-h1 {
                font-size: 19px !important;
                line-height: 1.25 !important;
                letter-spacing: -0.3px !important;
            }

            .header-sub-text {
                font-size: 11px !important;
                flex-wrap: wrap !important;
                gap: 4px 6px !important;
            }

            .header-datetime-box {
                width: 100% !important;
                justify-content: center !important;
                font-size: 11px !important;
                padding: 6px 10px !important;
                margin-top: 2px !important;
            }
        }

        /* ========================================================================== */
        /* RESPONSIVITAS MULTI-FRAME, KOLOM, DAN KONTROL TOUCH (max-width: 991px)     */
        /* (ANTI-BERTUMPUK: KOLOM MENJADI FULL-WIDTH VERTICAL STACK DENGAN JARAK RAPI) */
        /* ========================================================================== */
        @media (max-width: 991px) {
            /* 1. Stacking Vertikal Bersih untuk Seluruh Multi-Kolom Konten dengan Jarak Pemisah Nyaman */
            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) {
                display: flex !important;
                flex-direction: column !important;
                flex-wrap: wrap !important;
                width: 100% !important;
                max-width: 100% !important;
                gap: 16px !important;
                margin-top: 6px !important;
                margin-bottom: 22px !important;
            }

            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) > div[data-testid="stColumn"] {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                flex: 1 1 100% !important;
                margin-left: 0 !important;
                margin-right: 0 !important;
                margin-bottom: 16px !important;
                box-sizing: border-box !important;
            }

            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) > div[data-testid="column"]:last-child,
            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) > div[data-testid="stColumn"]:last-child {
                margin-bottom: 0 !important;
            }

            /* 2. Grid Responsif untuk Metric Cards (2 Kolom di Tablet & Ponsel Landscape) */
            div[data-testid="stHorizontalBlock"]:has(.hud-metric-card) {
                display: grid !important;
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 16px !important;
                row-gap: 16px !important;
                column-gap: 16px !important;
                width: 100% !important;
                max-width: 100% !important;
                margin-top: 8px !important;
                margin-bottom: 24px !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.hud-metric-card) > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:has(.hud-metric-card) > div[data-testid="stColumn"] {
                width: 100% !important;
                min-width: 0 !important;
                max-width: 100% !important;
                flex: 1 1 100% !important;
                box-sizing: border-box !important;
                margin-bottom: 16px !important;
            }

            .hud-metric-card {
                height: auto !important;
                min-height: 130px !important;
                max-height: none !important;
                padding: 14px 16px !important;
                gap: 10px !important;
                margin-bottom: 16px !important;
            }

            .metric-card-val {
                font-size: 20px !important;
                line-height: 1.2 !important;
                word-break: break-word !important;
            }

            .metric-trend-pill {
                white-space: normal !important;
                font-size: 10px !important;
                line-height: 1.3 !important;
                padding: 3px 8px !important;
            }

            /* 3. Frame & Container Border Wrapper Responsif (Jarak Pemisah Nyaman & Anti-Tumpang Tindih) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                margin-top: 10px !important;
                margin-bottom: 26px !important;
                border: none !important;
                background: transparent !important;
                background-color: transparent !important;
                box-shadow: none !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                padding: 18px 18px !important;
                border-radius: 18px !important;
                height: auto !important;
                max-height: none !important;
                margin-bottom: 0 !important;
                overflow: visible !important;
            }

            /* Jarak pemisah pada expander dan box peringatan (Alerts) */
            div[data-testid="stExpander"] {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                margin-top: 10px !important;
                margin-bottom: 20px !important;
                border-radius: 16px !important;
            }

            div[data-testid="stAlert"] {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                margin-top: 10px !important;
                margin-bottom: 20px !important;
                border-radius: 14px !important;
            }

            /* Jarak pemisah antar Tab Group */
            div[data-testid="stTabs"] {
                margin-top: 12px !important;
                margin-bottom: 24px !important;
            }

            /* 4. Tab bar responsif dapat digeser halus (Touch Swipe Scrolling) */
            div[role="tablist"] {
                display: flex !important;
                flex-wrap: nowrap !important;
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
                scrollbar-width: none !important;
                gap: 6px !important;
                padding-bottom: 6px !important;
                margin-bottom: 12px !important;
                width: 100% !important;
                max-width: 100% !important;
            }

            div[role="tablist"]::-webkit-scrollbar {
                display: none !important;
            }

            button[data-baseweb="tab"] {
                flex: 0 0 auto !important;
                white-space: nowrap !important;
                padding: 8px 14px !important;
                font-size: 12px !important;
                border-radius: 10px !important;
            }

            /* 5. Grafik Interaktif Plotly & Meteran Gauge Penuh Tanpa Terpotong */
            div[data-testid="stPlotlyChart"],
            div[data-testid="stPlotlyChart"] > div,
            .js-plotly-plot,
            .plotly .svg-container {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }

            .plotly .svg-container svg {
                max-width: 100% !important;
            }

            /* 6. Formulir & Tombol Ramah Sentuhan (Touch Target Friendly) */
            .stButton > button,
            button[kind="primary"],
            button[kind="secondary"] {
                min-height: 42px !important;
                font-size: 13px !important;
                border-radius: 11px !important;
                width: 100% !important;
            }

            div[data-baseweb="input"] input,
            div[data-baseweb="base-input"] input,
            div[data-baseweb="select"] input {
                min-height: 40px !important;
                font-size: 13px !important;
            }

            /* 7. Tabel responsif dengan horizontal touch scrolling */
            div[data-testid="stDataFrame"],
            div[data-testid="stTable"],
            div[data-testid="stCustomComponentV1"]:has(table) {
                width: 100% !important;
                max-width: 100% !important;
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
            }

            /* 8. Judul Section & Subjudul */
            .section-title-text {
                font-size: 15px !important;
            }
            .section-desc-text {
                font-size: 11.5px !important;
            }
        }

        /* Responsivitas Layar Handphone Portrait Sempit (max-width: 560px) */
        @media (max-width: 560px) {
            /* Metric Cards 1 Kolom Penuh di Layar Sempit */
            div[data-testid="stHorizontalBlock"]:has(.hud-metric-card) {
                grid-template-columns: 1fr !important;
                gap: 16px !important;
                row-gap: 16px !important;
                margin-bottom: 24px !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.hud-metric-card) > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:has(.hud-metric-card) > div[data-testid="stColumn"] {
                margin-bottom: 16px !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                margin-top: 8px !important;
                margin-bottom: 22px !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                padding: 15px 14px !important;
                margin-bottom: 0 !important;
            }

            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:not(:has(.sidebar-vault-container)):not(:has(.sidebar-user-block)):not(:has(.clock-content)):not(:has(.hud-metric-card)) > div[data-testid="stColumn"] {
                margin-bottom: 16px !important;
            }

            .section-title-text {
                font-size: 14px !important;
            }
            .section-desc-text {
                font-size: 11px !important;
            }
        }

        /* USER ACCOUNT BLOCK (DI PALING BAWAH: TIDAK TERPOTONG / UNCLIPPED) */
        .sidebar-user-block {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 0 !important;
            margin: 0 !important;
            min-width: 0 !important;
            overflow: visible !important;
        }
        .user-avatar-wrapper {
            position: relative !important;
            width: 38px !important;
            height: 38px !important;
            min-width: 38px !important;
            min-height: 38px !important;
            flex-shrink: 0 !important;
            overflow: visible !important;
            cursor: pointer !important;
        }
        .user-avatar-img {
            width: 38px !important;
            height: 38px !important;
            border-radius: 50% !important;
            object-fit: cover !important;
            border: 1.5px solid rgba(255, 255, 255, 0.18) !important;
            display: block !important;
            transition: all 0.2s ease !important;
        }
        .user-avatar-wrapper:hover .user-avatar-img {
            border-color: #10b981 !important;
            transform: scale(1.05) !important;
        }
        .user-status-dot {
            position: absolute !important;
            bottom: -1px !important;
            right: -1px !important;
            width: 9px !important;
            height: 9px !important;
            background-color: #10b981 !important;
            border: 2px solid #030e0a !important;
            border-radius: 50% !important;
        }
        .user-avatar-edit-badge {
            position: absolute !important;
            top: -3px !important;
            right: -3px !important;
            width: 15px !important;
            height: 15px !important;
            background: rgba(16, 185, 129, 0.95) !important;
            border: 1.5px solid #030e0a !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 8px !important;
            color: #ffffff !important;
            opacity: 0.85 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important;
        }
        .user-avatar-wrapper:hover .user-avatar-edit-badge {
            opacity: 1 !important;
            transform: scale(1.15) !important;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.7) !important;
        }
        .user-meta-col {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            overflow: hidden !important;
            min-width: 0 !important;
        }
        .user-name-bold {
            font-size: 13px !important;
            font-weight: 750 !important;
            color: #ffffff !important;
            line-height: 1.25 !important;
            letter-spacing: -0.01em !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        .user-role-thin {
            font-size: 11px !important;
            font-weight: 450 !important;
            color: #94a3b8 !important;
            line-height: 1.2 !important;
            margin-top: 2px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* 4. KONTEN UTAMA: UNIFIED DARK GLASS CARDS */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            margin-top: 8px !important;
            margin-bottom: 24px !important;
            border: none !important;
            background: transparent !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            width: 100% !important;
            box-sizing: border-box !important;
            background: rgba(15, 23, 42, 0.78) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 18px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45), inset 0 1px 0 0 rgba(255, 255, 255, 0.08) !important;
            color: #f8fafc !important;
            padding: 1.35rem 1.45rem !important;
            margin-bottom: 0 !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        div[data-testid="stExpander"] {
            margin-top: 8px !important;
            margin-bottom: 20px !important;
            border-radius: 16px !important;
        }
        div[data-testid="stAlert"] {
            margin-top: 8px !important;
            margin-bottom: 20px !important;
            border-radius: 14px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
            border-color: rgba(99, 102, 241, 0.3) !important;
            box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.55), inset 0 1px 0 0 rgba(255, 255, 255, 0.12) !important;
        }

        /* METRIC CARDS NATIVE STREAMLIT (KONTRAS TINGGI TERHADAP FRAME GELAP) */
        [data-testid="stMetric"] {
            background: rgba(13, 19, 33, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 14px !important;
            padding: 12px 16px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        }
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricLabel"] div {
            color: #94a3b8 !important;
            font-size: 11.5px !important;
            font-weight: 750 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] div {
            color: #ffffff !important;
            font-size: 24px !important;
            font-weight: 900 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        [data-testid="stMetricDelta"],
        [data-testid="stMetricDelta"] div {
            font-size: 12px !important;
            font-weight: 750 !important;
        }

        /* 5. TOP COMMAND DECK (HEADER ATAS KONTEN) */
        .vault-canvas-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 22px;
            padding: 16px 24px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(10, 15, 30, 0.94) 100%);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.04);
            flex-wrap: nowrap;
        }
        .header-title-column {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
            flex: 1;
        }
        .header-main-h1 {
            font-size: 24px;
            font-weight: 900;
            letter-spacing: -0.5px;
            color: #ffffff !important;
            margin: 0;
            line-height: 1.25;
        }
        .header-sub-text {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 5px;
            font-size: 12.5px;
            line-height: 1.4;
        }
        .header-platform-tag {
            background: rgba(37, 99, 235, 0.18);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.35);
            padding: 2.5px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .header-sub-desc {
            color: #94a3b8;
            font-weight: 550;
            font-size: 12px;
            white-space: nowrap;
        }
        .header-sub-sep {
            color: #475569;
            font-weight: 700;
            font-size: 11px;
        }
        .header-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 2px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 750;
            white-space: nowrap;
        }
        .header-status-pill.standby-pill {
            background: rgba(148, 163, 184, 0.12);
            color: #cbd5e1;
            border: 1px solid rgba(148, 163, 184, 0.25);
        }
        .header-status-pill.active-pill {
            background: rgba(16, 185, 129, 0.16);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .header-emiten-pill {
            background: rgba(37, 99, 235, 0.2);
            border: 1px solid rgba(96, 165, 250, 0.4);
            padding: 2px 9px;
            border-radius: 7px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
        }
        .emiten-pill-ticker {
            color: #60a5fa;
            font-weight: 900;
            letter-spacing: 0.3px;
        }
        .emiten-pill-year {
            color: #cbd5e1;
            font-weight: 700;
        }
        .header-company-name {
            color: #94a3b8;
            font-weight: 600;
            font-size: 12px;
            max-width: 280px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .header-search-box {
            flex: 1;
            max-width: 360px;
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(10, 15, 26, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            padding: 7px 16px;
            box-shadow: inset 1px 1px 4px rgba(0, 0, 0, 0.6);
        }
        .header-search-box span {
            color: #94a3b8;
            font-size: 13px;
        }
        .header-search-box input {
            border: none;
            outline: none;
            background: transparent;
            font-size: 12px;
            color: #f8fafc;
            width: 100%;
        }
        .header-actions-cluster {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: auto;
            flex-wrap: nowrap;
        }

        /* Live Header Clock (Real-Time) - Terkunci Permanen di Kanan Tanpa Bergeser */
        .header-datetime-box {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(10, 15, 26, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            padding: 7px 18px;
            box-shadow: inset 1px 1px 4px rgba(0, 0, 0, 0.6);
            white-space: nowrap;
            margin-left: auto;
            margin-right: 0;
            flex-shrink: 0;
            box-sizing: border-box;
        }
        .clock-live-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 10.5px;
            font-weight: 800;
            color: #34d399;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.35);
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }
        .clock-pulse-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: clockPulseAnim 2s infinite ease-in-out;
            display: inline-block;
            flex-shrink: 0;
        }
        @keyframes clockPulseAnim {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.35; transform: scale(0.85); }
        }
        .clock-icon {
            font-size: 14px;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            flex-shrink: 0;
        }
        .clock-content {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            white-space: nowrap;
        }
        .clock-time {
            font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-weight: 800;
            color: #f8fafc;
            font-size: 12px;
            font-variant-numeric: tabular-nums;
            letter-spacing: 0.2px;
            display: inline-block;
            min-width: 88px;
            text-align: center;
            flex-shrink: 0;
        }
        .clock-sep {
            color: #475569;
            font-size: 11px;
            font-weight: 700;
            flex-shrink: 0;
        }
        .clock-date {
            font-weight: 600;
            color: #94a3b8;
            font-size: 12px;
            white-space: nowrap;
            flex-shrink: 0;
        }


        /* Executive Report Export Dropdown Feature */
        .header-export-dropdown {
            position: relative;
            display: inline-block;
        }
        .header-export-btn {
            background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
            color: #ffffff !important;
            font-size: 11px !important;
            font-weight: 750 !important;
            border-radius: 999px !important;
            padding: 5px 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 5px !important;
            box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4) !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            outline: none !important;
            white-space: nowrap !important;
        }
        .header-export-btn:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 22px rgba(16, 185, 129, 0.6) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
        }
        .header-export-btn .export-icon {
            font-size: 13px;
            line-height: 1;
        }
        .header-export-btn .export-text {
            font-size: 11px;
            font-weight: 750;
            white-space: nowrap;
        }
        .header-export-btn span.export-arrow {
            font-size: 9px;
            margin-left: 1px;
            transition: transform 0.2s ease;
        }
        .header-export-dropdown:hover .header-export-btn span.export-arrow {
            transform: rotate(180deg);
        }
        .header-export-menu {
            display: none;
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            width: 330px;
            background: #0b1120;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            padding: 10px;
            box-shadow: 0 20px 48px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.05);
            z-index: 99999;
            flex-direction: column;
            gap: 6px;
        }
        .header-export-dropdown:hover .header-export-menu,
        .header-export-dropdown:focus-within .header-export-menu {
            display: flex;
            animation: exportDropdownEnter 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes exportDropdownEnter {
            from { opacity: 0; transform: translateY(-8px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .export-menu-header {
            padding: 8px 12px 6px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 4px;
        }
        .export-menu-title {
            font-size: 10px;
            font-weight: 850;
            letter-spacing: 0.8px;
            color: #64748b;
            text-transform: uppercase;
        }
        .export-menu-sub {
            font-size: 12px;
            font-weight: 700;
            color: #38bdf8;
            margin-top: 2px;
        }
        .export-menu-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 9px 12px;
            border-radius: 10px;
            text-decoration: none !important;
            transition: all 0.15s ease;
            background: transparent;
            border: 1px solid transparent;
            cursor: pointer;
        }
        .export-menu-item:hover {
            background: rgba(30, 41, 59, 0.85);
            border-color: rgba(56, 189, 248, 0.3);
            transform: translateX(3px);
        }
        .export-item-icon {
            font-size: 18px;
            line-height: 1.2;
        }
        .export-item-body {
            flex: 1;
        }
        .export-item-title {
            font-size: 12px;
            font-weight: 750;
            color: #f8fafc;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .export-item-sub {
            font-size: 10.5px;
            color: #94a3b8;
            margin-top: 2px;
            line-height: 1.35;
        }
        .export-item-badge {
            font-size: 9.5px;
            font-weight: 800;
            padding: 1px 6px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.18);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .export-menu-standby {
            padding: 16px 14px;
            text-align: center;
            border-radius: 10px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px dashed rgba(255, 255, 255, 0.15);
            color: #94a3b8;
            font-size: 11.5px;
            line-height: 1.5;
        }

        .header-action-icon-circle {
            width: 38px;
            height: 38px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            color: #cbd5e1;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .header-action-icon-circle:hover {
            border-color: rgba(99, 102, 241, 0.5);
            background: rgba(30, 41, 59, 0.9);
            color: #ffffff;
            transform: translateY(-1px);
        }
        .header-primary-black-pill {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
            color: #ffffff !important;
            font-size: 11px !important;
            font-weight: 750 !important;
            border-radius: 999px !important;
            padding: 5px 14px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 5px !important;
            box-shadow: 0 4px 16px rgba(99, 102, 241, 0.45) !important;
            cursor: pointer !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .header-primary-black-pill:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.65) !important;
        }

        /* 6. HUD METRIC CARDS (KARTU STATISTIK DENGAN AKSEN BERBEDA & UKURAN PRESISI TETAP) */
        .hud-metric-card {
            border-radius: 18px !important;
            padding: 16px 18px !important;
            min-height: 140px !important;
            height: auto !important;
            max-height: none !important;
            width: 100% !important;
            margin-bottom: 18px !important;
            box-sizing: border-box !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            position: relative !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35) !important;
            transform: none !important;
            overflow: hidden !important;
            user-select: none !important;
            -webkit-user-select: none !important;
            -webkit-user-drag: none !important;
            cursor: default !important;
        }
        .hud-metric-card:hover {
            transform: none !important;
            box-shadow: 0 10px 32px rgba(0, 0, 0, 0.45) !important;
        }
        .metric-card-top {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            height: 36px !important;
            flex-shrink: 0 !important;
        }
        .metric-icon-square {
            width: 36px !important;
            height: 36px !important;
            border-radius: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 17px !important;
            font-weight: 800 !important;
            flex-shrink: 0 !important;
        }
        .metric-arrow {
            font-size: 15px !important;
            font-weight: 700 !important;
            flex-shrink: 0 !important;
        }
        .metric-card-middle {
            margin: 4px 0 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            flex: 1 !important;
            overflow: hidden !important;
            flex-shrink: 0 !important;
        }
        .metric-card-title {
            font-size: 10.5px !important;
            font-weight: 800 !important;
            letter-spacing: 0.8px !important;
            text-transform: uppercase !important;
            color: #94a3b8 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.2 !important;
        }
        .metric-card-val {
            font-size: 25px !important;
            font-weight: 900 !important;
            letter-spacing: -0.5px !important;
            margin-top: 2px !important;
            font-family: 'JetBrains Mono', monospace !important;
            line-height: 1.15 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            text-align: right !important;
            justify-content: flex-end !important;
            display: flex !important;
        }
        .metric-card-bottom {
            margin-top: auto !important;
            width: 100% !important;
            overflow: hidden !important;
            flex-shrink: 0 !important;
        }
        .metric-trend-pill {
            display: inline-flex !important;
            align-items: center !important;
            gap: 5px !important;
            padding: 4px 10px !important;
            border-radius: 999px !important;
            font-size: 10.5px !important;
            font-weight: 750 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            line-height: 1.2 !important;
        }

        /* 7. FORM INPUTS & SELECTORS (NEUMORPHIC INSET WELLS) */
        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        div[data-baseweb="textarea"],
        div[data-baseweb="select"] > div {
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            background: rgba(10, 15, 26, 0.9) !important;
            box-shadow: inset 1px 1px 4px rgba(0, 0, 0, 0.6) !important;
            color: #f8fafc !important;
            transition: all 0.2s ease !important;
        }
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="base-input"]:focus-within,
        div[data-baseweb="textarea"]:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.35), inset 1px 1px 3px rgba(0, 0, 0, 0.4) !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="textarea"] textarea {
            color: #f8fafc;
            background: transparent !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
            color: #f8fafc;
        }
        div[data-baseweb="input"] input::placeholder,
        div[data-baseweb="textarea"] textarea::placeholder {
            color: #64748b;
        }
        label[data-testid="stWidgetLabel"],
        label[data-testid="stWidgetLabel"] p,
        label[data-testid="stWidgetLabel"] span {
            color: #cbd5e1;
            font-weight: 700 !important;
            font-size: 12px !important;
        }

        /* Dropdown Popovers */
        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"] {
            background: #0d1321 !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7) !important;
        }
        li[role="option"] {
            color: #cbd5e1;
            background: transparent !important;
        }
        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {
            background: rgba(99, 102, 241, 0.3) !important;
            color: #ffffff !important;
        }

        /* 8. TOMBOL (PRIMARY & SECONDARY) */
        .stButton button,
        button[data-testid="baseButton-secondary"],
        button[data-testid="baseButton-primary"] {
            border-radius: 12px !important;
            font-size: 13px !important;
            font-weight: 750 !important;
            padding: 8px 20px !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        button[data-testid="baseButton-primary"],
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        }
        button[data-testid="baseButton-primary"]:hover,
        .stButton button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
            color: #ffffff !important;
        }
        .stButton:not(.st-key-btn_hide_sidebar_top):not(.st-key-btn_account_settings_trigger) button[data-testid="baseButton-secondary"],
        .stButton:not(.st-key-btn_hide_sidebar_top):not(.st-key-btn_account_settings_trigger) button[kind="secondary"] {
            background: rgba(30, 41, 59, 0.75) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            color: #f8fafc !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        }
        .stButton:not(.st-key-btn_hide_sidebar_top):not(.st-key-btn_account_settings_trigger) button[data-testid="baseButton-secondary"]:hover,
        .stButton:not(.st-key-btn_hide_sidebar_top):not(.st-key-btn_account_settings_trigger) button[kind="secondary"]:hover {
            background: rgba(51, 65, 85, 0.85) !important;
            border-color: rgba(99, 102, 241, 0.4) !important;
            transform: translateY(-1px) !important;
            color: #ffffff !important;
        }

        /* Dashboard & Top Navigation Quick Nav Buttons (Lega, Rapi, Tengah & Anti-Berdempetan) */
        .st-key-btn_goto_dl_from_dash,
        .st-key-btn_goto_pred_from_adm_dash,
        .st-key-btn_goto_eval_from_adm_dash,
        .st-key-btn_goto_api_from_dash,
        .st-key-btn_goto_rh_from_pe,
        .st-key-btn_goto_dash_from_pe,
        .st-key-btn_goto_dl_from_rh,
        .st-key-btn_goto_dash_from_rh,
        .st-key-btn_prof_goto_dash,
        .st-key-btn_prof_goto_results,
        .st-key-btn_prof_top_single_logout {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-btn_goto_dl_from_dash button,
        .st-key-btn_goto_pred_from_adm_dash button,
        .st-key-btn_goto_eval_from_adm_dash button,
        .st-key-btn_goto_api_from_dash button,
        .st-key-btn_goto_rh_from_pe button,
        .st-key-btn_goto_dash_from_pe button,
        .st-key-btn_goto_dl_from_rh button,
        .st-key-btn_goto_dash_from_rh button,
        .st-key-btn_prof_goto_dash button,
        .st-key-btn_prof_goto_results button {
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            padding: 0 8px !important;
            font-size: 11.5px !important;
            font-weight: 750 !important;
            letter-spacing: -0.15px !important;
            border-radius: 9px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            white-space: nowrap !important;
            box-sizing: border-box !important;
            width: 100% !important;
            background: rgba(30, 41, 59, 0.75) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            color: #f8fafc !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.18s ease !important;
        }
        .st-key-btn_goto_dl_from_dash button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_pred_from_adm_dash button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_eval_from_adm_dash button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_api_from_dash button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_rh_from_pe button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_dash_from_pe button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_dl_from_rh button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_dash_from_rh button div[data-testid="stMarkdownContainer"],
        .st-key-btn_prof_goto_dash button div[data-testid="stMarkdownContainer"],
        .st-key-btn_prof_goto_results button div[data-testid="stMarkdownContainer"],
        .st-key-btn_goto_dl_from_dash button div,
        .st-key-btn_goto_pred_from_adm_dash button div,
        .st-key-btn_goto_eval_from_adm_dash button div,
        .st-key-btn_goto_api_from_dash button div,
        .st-key-btn_goto_rh_from_pe button div,
        .st-key-btn_goto_dash_from_pe button div,
        .st-key-btn_goto_dl_from_rh button div,
        .st-key-btn_goto_dash_from_rh button div,
        .st-key-btn_prof_goto_dash button div,
        .st-key-btn_prof_goto_results button div {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            width: 100% !important;
            margin: 0 auto !important;
        }
        .st-key-btn_goto_dl_from_dash button p,
        .st-key-btn_goto_pred_from_adm_dash button p,
        .st-key-btn_goto_eval_from_adm_dash button p,
        .st-key-btn_goto_api_from_dash button p,
        .st-key-btn_goto_rh_from_pe button p,
        .st-key-btn_goto_dash_from_pe button p,
        .st-key-btn_goto_dl_from_rh button p,
        .st-key-btn_goto_dash_from_rh button p,
        .st-key-btn_prof_goto_dash button p,
        .st-key-btn_prof_goto_results button p {
            font-size: 11.5px !important;
            font-weight: 750 !important;
            white-space: nowrap !important;
            margin: 0 auto !important;
            padding: 0 !important;
            line-height: 1 !important;
            text-align: center !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }
        .st-key-btn_goto_dl_from_dash button:hover,
        .st-key-btn_goto_pred_from_adm_dash button:hover,
        .st-key-btn_goto_eval_from_adm_dash button:hover,
        .st-key-btn_goto_api_from_dash button:hover,
        .st-key-btn_goto_rh_from_pe button:hover,
        .st-key-btn_goto_dash_from_pe button:hover,
        .st-key-btn_goto_dl_from_rh button:hover,
        .st-key-btn_goto_dash_from_rh button:hover,
        .st-key-btn_prof_goto_dash button:hover,
        .st-key-btn_prof_goto_results button:hover {
            background: rgba(51, 65, 85, 0.9) !important;
            border-color: rgba(99, 102, 241, 0.5) !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25) !important;
        }

        /* Radio & Checkbox Labels */
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label {
            color: #cbd5e1 !important;
        }
        div[data-testid="stRadio"] label p,
        div[data-testid="stCheckbox"] label p {
            color: #cbd5e1 !important;
        }
        div[data-testid="stRadio"] label:hover p,
        div[data-testid="stCheckbox"] label:hover p {
            color: #ffffff !important;
        }

        /* 9. TABS SEGMENTED CONTROL */
        div[data-baseweb="tab-list"] {
            background: rgba(10, 15, 26, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 14px !important;
            padding: 4px !important;
            gap: 4px !important;
        }
        button[data-baseweb="tab"] {
            border-radius: 10px !important;
            font-size: 12.5px !important;
            font-weight: 700 !important;
            color: #94a3b8 !important;
            padding: 7px 18px !important;
            background: transparent !important;
            border: none !important;
            transition: all 0.2s ease !important;
        }
        button[data-baseweb="tab"]:hover {
            color: #f8fafc !important;
            background: rgba(255, 255, 255, 0.04) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
        }

        /* 10. TABEL & DATAFRAME */
        div[data-testid="stDataFrame"] {
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            overflow: hidden !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
            background: rgba(13, 19, 33, 0.85) !important;
        }
        div[data-testid="stTable"] {
            background: rgba(13, 19, 33, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 14px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
            overflow: hidden !important;
        }
        div[data-testid="stTable"] table {
            background: rgba(13, 19, 33, 0.85) !important;
            color: #f8fafc !important;
            border-collapse: collapse !important;
            width: 100% !important;
        }
        div[data-testid="stTable"] thead tr th,
        div[data-testid="stTable"] th {
            background: rgba(30, 41, 59, 0.95) !important;
            color: #f8fafc !important;
            font-weight: 800 !important;
            border-bottom: 2px solid rgba(255, 255, 255, 0.15) !important;
            padding: 10px 14px !important;
        }
        div[data-testid="stTable"] tbody tr td,
        div[data-testid="stTable"] td {
            background: rgba(15, 23, 42, 0.85) !important;
            color: #f1f5f9 !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
            padding: 8px 14px !important;
        }
        div[data-testid="stTable"] tbody tr:nth-child(even) td {
            background: rgba(15, 23, 42, 0.55) !important;
        }
        div[data-testid="stTable"] tbody tr:hover td {
            background: rgba(255, 255, 255, 0.04) !important;
        }

        /* Generic HTML Tables & Numeric Alignment */
        table td.text-right, table th.text-right,
        table td.num, table th.num,
        table td.numeric, table th.numeric,
        table td[align="right"], table th[align="right"],
        table td[style*="text-align:right"], table td[style*="text-align: right"],
        table th[style*="text-align:right"], table th[style*="text-align: right"],
        .table-numeric, .table-num,
        div[data-testid="stTable"] td.text-right,
        div[data-testid="stTable"] th.text-right,
        div[data-testid="stTable"] td[align="right"],
        div[data-testid="stTable"] th[align="right"],
        div[data-testid="stTable"] td:has(.font-mono-num),
        div[data-testid="stTable"] td:has(.mono-num) {
            text-align: right !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums !important;
        }

        /* Metric & Number Inputs Right Alignment */
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] > div {
            text-align: right !important;
            justify-content: flex-end !important;
            display: flex !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums !important;
        }
        div[data-testid="stMetricDelta"],
        div[data-testid="stMetricDelta"] > div {
            text-align: right !important;
            justify-content: flex-end !important;
            display: flex !important;
        }
        input[type="number"],
        div[data-baseweb="input"] input[type="number"],
        div[data-testid="stNumberInput"] input {
            text-align: right !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums !important;
        }
        .kv-table {
            border-radius: 14px !important;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            overflow: hidden !important;
            background: rgba(13, 19, 33, 0.55) !important;
            backdrop-filter: blur(14px) !important;
            -webkit-backdrop-filter: blur(14px) !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25) !important;
            margin: 4px 0 !important;
        }
        .kv-row {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            padding: 11px 16px !important;
            font-size: 12.5px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            transition: background 0.15s ease !important;
        }
        .kv-row:last-child {
            border-bottom: none !important;
        }
        .kv-row:hover {
            background: rgba(255, 255, 255, 0.03) !important;
        }
        .kv-label,
        .kv-row div:first-child {
            color: #94a3b8 !important;
            font-size: 12.5px !important;
            font-weight: 600 !important;
            letter-spacing: 0.1px !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }
        .kv-val,
        .kv-row div:last-child {
            color: #f8fafc !important;
            font-weight: 800 !important;
            font-size: 13px !important;
            text-align: right !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-variant-numeric: tabular-nums !important;
            letter-spacing: -0.2px !important;
            padding: 3px 9px !important;
            background: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            border-radius: 7px !important;
            min-width: 80px !important;
            box-sizing: border-box !important;
        }

        /* EXPANDER */
        div[data-testid="stExpander"] {
            border-radius: 16px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: rgba(15, 23, 42, 0.65) !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
            overflow: hidden !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 750 !important;
            color: #f8fafc !important;
            padding: 12px 18px !important;
            font-size: 13px !important;
        }
        div[data-testid="stExpander"] summary:hover {
            color: #60a5fa !important;
        }
        div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            color: #cbd5e1 !important;
            padding: 14px 18px !important;
        }
        div[data-testid="stExpander"] [data-testid="stExpanderDetails"] p {
            color: #cbd5e1 !important;
        }

        /* 11. STREAMLIT ALERTS (NOTIFIKASI KONTRAS TINGGI) */
        div[data-testid="stAlert"] {
            border-radius: 14px !important;
            backdrop-filter: blur(12px) !important;
            padding: 12px 18px !important;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35) !important;
            background: rgba(15, 23, 42, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
        }
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] div {
            color: #f8fafc !important;
        }
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong,
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] b {
            color: #ffffff !important;
        }

        /* CAPTION TEXT */
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] p,
        .stCaption,
        .stCaption p {
            color: #94a3b8 !important;
            font-size: 12px !important;
            font-weight: 500 !important;
        }

        /* ===================================================================== */
        /* COOL FINTECH SPINNER & LOADING ANIMATION (GLOBAL KEYFRAMES & DARK)   */
        /* ===================================================================== */
        @keyframes spin-clockwise {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes spin-counter {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(-360deg); }
        }
        @keyframes pulse-scale {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
        }
        @keyframes blink-dot {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.25; }
        }
        @keyframes shimmer-bar {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        @keyframes spinner-scanline {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        @keyframes glow-pulse {
            0%, 100% { opacity: 0.85; filter: drop-shadow(0 0 6px rgba(56,189,248,0.5)); }
            50% { opacity: 1; filter: drop-shadow(0 0 14px rgba(56,189,248,0.85)); }
        }
        @keyframes cyber-radar-sweep {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Streamlit Spinner Container (Glassmorphic FinTech HUD) */
        div[data-testid="stSpinner"],
        .stSpinner {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(30, 41, 59, 0.92) 100%) !important;
            border: 1px solid rgba(56, 189, 248, 0.35) !important;
            border-radius: 16px !important;
            padding: 16px 24px !important;
            box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5), 0 0 25px rgba(56, 189, 248, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
            backdrop-filter: blur(16px) !important;
            margin: 14px 0 !important;
            position: relative !important;
            overflow: hidden !important;
        }
        div[data-testid="stSpinner"]::before,
        .stSpinner::before {
            content: "" !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 2.5px !important;
            background: linear-gradient(90deg, transparent, #38bdf8, #818cf8, #10b981, transparent) !important;
            animation: spinner-scanline 1.8s linear infinite !important;
        }
        div[data-testid="stSpinner"] > div {
            display: flex !important;
            align-items: center !important;
            gap: 16px !important;
        }
        div[data-testid="stSpinner"] svg,
        .stSpinner svg {
            width: 30px !important;
            height: 30px !important;
            color: #38bdf8 !important;
            stroke: #38bdf8 !important;
            filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.75)) drop-shadow(0 0 18px rgba(99, 102, 241, 0.4)) !important;
            animation: spin-clockwise 1.1s cubic-bezier(0.4, 0, 0.2, 1) infinite !important;
        }
        div[data-testid="stSpinner"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stSpinner"] span,
        div[data-testid="stSpinner"] div {
            font-weight: 750 !important;
            font-size: 14px !important;
            color: #f8fafc !important;
            letter-spacing: -0.2px !important;
        }

        /* DATE INPUT & GELEMBUNG KALENDER INTERAKTIF (DARK MODE) */
        div[data-testid="stDateInput"] {
            width: 100% !important;
        }
        div[data-testid="stDateInput"] [data-baseweb="input"] {
            background: rgba(15, 23, 42, 0.75) !important;
            border: 1.5px solid rgba(255, 255, 255, 0.14) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stDateInput"] [data-baseweb="input"]:focus-within {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
        }
        div[data-testid="stDateInput"] input {
            color: #f8fafc !important;
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        div[data-testid="stDateInput"] svg,
        div[data-testid="stDateInput"] button {
            color: #38bdf8 !important;
            fill: #38bdf8 !important;
        }
        div[data-baseweb="popover"]:has(div[data-baseweb="calendar"]) {
            border-radius: 16px !important;
            overflow: hidden !important;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.7), 0 0 0 1.5px rgba(255, 255, 255, 0.14) !important;
        }
        div[data-baseweb="calendar"] {
            background: #0f172a !important;
            background-color: #0f172a !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 16px !important;
            padding: 10px !important;
            color: #f8fafc !important;
        }
        div[data-baseweb="calendar"] header {
            background: transparent !important;
            color: #f8fafc !important;
            padding: 4px 6px !important;
        }
        div[data-baseweb="calendar"] header button {
            color: #38bdf8 !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="calendar"] header select {
            color: #f8fafc !important;
            background: rgba(30, 41, 59, 0.85) !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            font-weight: 700 !important;
        }
        div[data-baseweb="calendar"] div[role="columnheader"] {
            color: #94a3b8 !important;
            font-weight: 800 !important;
            font-size: 11px !important;
        }
        div[data-baseweb="calendar"] div[role="gridcell"] {
            color: #cbd5e1 !important;
            border-radius: 8px !important;
            font-weight: 650 !important;
            transition: all 0.15s ease !important;
        }
        div[data-baseweb="calendar"] div[role="gridcell"]:hover {
            background: rgba(56, 189, 248, 0.22) !important;
            color: #38bdf8 !important;
        }
        div[data-baseweb="calendar"] div[aria-selected="true"],
        div[data-baseweb="calendar"] div[aria-selected="true"] * {
            background: #2563eb !important;
            background-color: #2563eb !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 850 !important;
            box-shadow: 0 2px 10px rgba(37, 99, 235, 0.5) !important;
        }

        /* SECTION HEADER DI DALAM KONTEN */
        .canvas-section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 4px;
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .section-title-text {
            font-size: 17px;
            font-weight: 850;
            color: #f8fafc;
            letter-spacing: -0.2px;
            line-height: 1.25;
        }
        .section-desc-text {
            font-size: 11.5px;
            color: #94a3b8;
            font-weight: 500;
        }

        /* CUSTOM SCROLLBAR */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(10, 15, 26, 0.6);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.25);
            border-radius: 999px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(99, 102, 241, 0.6);
        }

        /* RESPONSIVE DESIGN */
        @media (max-width: 992px) {
            .vault-canvas-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .header-search-box {
                max-width: 100%;
                width: 100%;
            }
        }
        
        /* FINAL ABSOLUTE OVERRIDE: GHOST & ACCENT BUTTONS DI SIDEBAR */
        .st-key-btn_hide_sidebar_top button,
        div.st-key-btn_hide_sidebar_top button,
        div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_hide_sidebar_top button,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_hide_sidebar_top button {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            border-color: transparent !important;
            box-shadow: none !important;
            outline: none !important;
            border-radius: 8px !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        .st-key-btn_hide_sidebar_top button:hover {
            background: rgba(255, 255, 255, 0.08) !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            border: none !important;
            box-shadow: none !important;
            transform: scale(1.1) !important;
        }

        .st-key-btn_quick_edit_profile button,
        div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile button,
        div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile button {
            border-radius: 8px !important;
            padding: 0 !important;
            margin: 0 !important;
            min-height: 28px !important;
            max-height: 28px !important;
            height: 28px !important;
            min-width: 28px !important;
            max-width: 28px !important;
            width: 28px !important;
            line-height: 1 !important;
        }

        /* Profile Page Logout Menu & Action Buttons (Dark Mode) */
        .st-key-btn_prof_top_single_logout {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        .st-key-btn_prof_top_single_logout button,
        .st-key-btn_logout_prof_card button,
        .st-key-btn_prof_nav_logout button,
        .st-key-btn_logout_prof_form button,
        .st-key-btn_confirm_logout_yes button {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
            background-color: #dc2626 !important;
            color: #ffffff !important;
            border: 1px solid rgba(248, 113, 113, 0.45) !important;
            box-shadow: 0 4px 14px rgba(220, 38, 38, 0.35) !important;
            font-weight: 800 !important;
            border-radius: 9px !important;
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            padding: 0 10px !important;
            font-size: 11.5px !important;
            letter-spacing: -0.15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            white-space: nowrap !important;
            box-sizing: border-box !important;
            width: 100% !important;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .st-key-btn_prof_top_single_logout button:hover,
        .st-key-btn_logout_prof_card button:hover,
        .st-key-btn_prof_nav_logout button:hover,
        .st-key-btn_logout_prof_form button:hover,
        .st-key-btn_confirm_logout_yes button:hover {
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
            border-color: rgba(248, 113, 113, 0.8) !important;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.55) !important;
            transform: translateY(-1px) !important;
            color: #ffffff !important;
        }
        .st-key-btn_prof_top_single_logout button *,
        .st-key-btn_prof_top_single_logout button p,
        .st-key-btn_prof_top_single_logout button span {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 750 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if is_light:
        st.markdown(
            """
            <style>
            /* ===================================================================== */
            /* LIGHT MODE COMPREHENSIVE DESIGN SYSTEM OVERRIDE (ROYAL BLUE & WHITE)  */
            /* ===================================================================== */
            :root {
                --canvas-bg: #f8fafc;
                --surface-glass: #ffffff;
                --surface-glass-card: #ffffff;
                --surface-neu-inset: #f1f5f9;
                --border-specular: #e2e8f0;
                --border-focus: #2563eb;
                --safe-teal: #0d9488;
                --safe-teal-glow: rgba(13, 148, 136, 0.2);
                --safe-emerald: #059669;
                --warn-amber: #d97706;
                --warn-amber-glow: rgba(217, 119, 6, 0.2);
                --danger-coral: #dc2626;
                --danger-coral-glow: rgba(220, 38, 38, 0.2);
                --ai-violet: #2563eb;
                --ai-violet-glow: rgba(37, 99, 235, 0.25);
                --empirical-cyan: #0284c7;
                --empirical-cyan-glow: rgba(2, 132, 199, 0.25);
                --text-primary: #0f172a;
                --text-secondary: #1e293b;
                --text-muted: #334155;
                --text-dim: #475569;
            }

            /* 1. Global Background Canvas & Base Typography */
            body, .stApp, section.stMain, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            .stApp p, .stApp span, .stApp div, .stApp label,
            .stApp input, .stApp select, .stApp textarea,
            .stApp li, .stApp td, .stApp th {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
                font-weight: 850 !important;
            }

            /* Sembunyikan semua anchor link pada judul dalam Light Mode */
            [data-testid="stHeaderActionElements"],
            div[data-testid="stHeadingWithActionElements"] > div,
            .stHeadingWithActionElements [data-testid="stHeaderActionElements"],
            a.anchorjs-link,
            .anchorjs-link,
            .stHeadingWithActionElements a,
            h1 a, h2 a, h3 a, h4 a, h5 a, h6 a,
            h1 a.anchor-link, h2 a.anchor-link, h3 a.anchor-link,
            [data-testid="stMarkdownContainer"] h1 a,
            [data-testid="stMarkdownContainer"] h2 a,
            [data-testid="stMarkdownContainer"] h3 a,
            [data-testid="stMarkdownContainer"] h4 a,
            [data-testid="stMarkdownContainer"] h5 a,
            [data-testid="stMarkdownContainer"] h6 a {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
                width: 0 !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            div[data-testid="stHeadingWithActionElements"] {
                display: block !important;
                width: 100% !important;
            }
            .stApp [data-testid="stCaptionContainer"] p,
            .stCaption, caption, .header-sub-caption {
                color: #334155 !important;
                -webkit-text-fill-color: #334155 !important;
                font-weight: 600 !important;
            }
            label[data-testid="stWidgetLabel"],
            label[data-testid="stWidgetLabel"] p,
            label[data-testid="stWidgetLabel"] span {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
                font-weight: 750 !important;
            }

            /* 2. Sidebar Desktop Permanen: Soft Cool Blue-Gray Surface Kontras (#edf2f8) */
            @media (min-width: 992px) {
                div[data-testid="column"]:has(.sidebar-vault-container),
                div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                    background: #edf2f8 !important;
                    background-color: #edf2f8 !important;
                    border: none !important;
                    border-right: 1.5px solid #cbd5e1 !important;
                    flex: 0 0 270px !important;
                    width: 270px !important;
                    min-width: 270px !important;
                    max-width: 270px !important;
                    padding: 14px 14px 14px 14px !important;
                    padding-top: 14px !important;
                    margin-top: 0 !important;
                    box-sizing: border-box !important;
                }
            }

            /* 2b. Light Mode Mobile Drawer & Top Bar Overrides */
            @media (max-width: 991px) {
                div[data-testid="column"]:has(.sidebar-vault-container),
                div[data-testid="stColumn"]:has(.sidebar-vault-container) {
                    background: #ffffff !important;
                    background-color: #ffffff !important;
                    border-right: 1.5px solid #cbd5e1 !important;
                    box-shadow: 16px 0 50px rgba(15, 23, 42, 0.22) !important;
                }
                .mobile-top-bar {
                    background: rgba(255, 255, 255, 0.96) !important;
                    border: none !important;
                    border-bottom: 1.5px solid #cbd5e1 !important;
                    border-radius: 0 0 16px 16px !important;
                    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.1) !important;
                }
                .mobile-brand-title {
                    color: #0f172a !important;
                }
                .mobile-hamburger-btn {
                    background: #f1f5f9 !important;
                    border: 1px solid #cbd5e1 !important;
                    color: #0f172a !important;
                }
                .mobile-hamburger-btn:hover,
                .mobile-hamburger-btn:active {
                    background: #2563eb !important;
                    border-color: #1d4ed8 !important;
                    color: #ffffff !important;
                }
                .mobile-page-badge {
                    color: #0284c7 !important;
                    background: #f0f9ff !important;
                    border: 1px solid #bae6fd !important;
                }
                .mobile-drawer-backdrop {
                    background: rgba(15, 23, 42, 0.55) !important;
                }
                .mobile-drawer-close-row {
                    border-bottom-color: #e2e8f0 !important;
                }
                .mobile-drawer-title {
                    color: #475569 !important;
                }
            }

            /* Sidebar Logo */
            .sidebar-logo-icon {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
                border: 1px solid rgba(37, 99, 235, 0.4) !important;
                box-shadow: 0 4px 18px rgba(37, 99, 235, 0.35) !important;
                color: #ffffff !important;
            }
            .sidebar-logo-title {
                color: #0f172a !important;
                font-weight: 850 !important;
            }
            .sidebar-logo-subtitle {
                color: #2563eb !important;
                font-weight: 750 !important;
            }
            .sidebar-section-label {
                color: #475569 !important;
                font-weight: 800 !important;
            }

            /* Sidebar Navigation Menu Items (Radio) - Lebar Penuh 100% Tanpa Space Kosong di Kanan */
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"],
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                align-items: stretch !important;
                box-sizing: border-box !important;
            }

            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label,
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label,
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"],
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] [data-baseweb="radio"] {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                align-self: stretch !important;
                flex: 1 1 100% !important;
                box-sizing: border-box !important;
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1px solid #d1d9e6 !important;
                color: #1e293b !important;
                box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
            }
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label *,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label * {
                color: #1e293b !important;
            }
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:hover,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:hover,
            div[data-testid="column"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] div[role="radiogroup"] label:hover,
            div[data-testid="stColumn"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
                background: #eff6ff !important;
                background-color: #eff6ff !important;
                border-color: #93c5fd !important;
                color: #1d4ed8 !important;
            }
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:hover *,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:hover * {
                color: #1d4ed8 !important;
            }

            /* Active Menu Item: Kartu Putih Bergaris Aksen Royal Blue yang Kontras di atas #edf2f8 */
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked),
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
            div[data-testid="column"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] label:has(input:checked),
            div[data-testid="stColumn"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] label:has(input:checked),
            div[data-testid="column"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
            div[data-testid="stColumn"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
                width: 100% !important;
                min-width: 100% !important;
                max-width: 100% !important;
                align-self: stretch !important;
                flex: 1 1 100% !important;
                box-sizing: border-box !important;
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #1d4ed8 !important;
                font-weight: 850 !important;
                border-radius: 15px !important;
                border: 2px solid #2563eb !important;
                box-shadow: 0 4px 16px rgba(37, 99, 235, 0.22) !important;
            }
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) *,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) *,
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p,
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p strong,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) p strong,
            div[data-testid="column"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) span,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) div[data-testid="stRadio"] label:has(input:checked) span,
            div[data-testid="column"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] label:has(input:checked) *,
            div[data-testid="stColumn"]:has(.sidebar-vault-container):hover div[data-testid="stRadio"] label:has(input:checked) * {
                color: #1d4ed8 !important;
            }

            /* 3. Sidebar Account / Profile Card (Refined Color Scheme) */
            div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block),
            div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) {
                background: linear-gradient(135deg, #f0f7ff 0%, #e0effe 100%) !important;
                background-color: #f0f7ff !important;
                border: 1.5px solid #bfdbfe !important;
                border-radius: 16px !important;
                box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12) !important;
                margin: 0 auto !important;
            }
            div[data-testid="column"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) div,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) div {
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }
            div[data-testid="column"]:has(.sidebar-vault-container):hover [data-testid="stHorizontalBlock"]:has(.sidebar-user-block),
            div[data-testid="stColumn"]:has(.sidebar-vault-container):hover [data-testid="stHorizontalBlock"]:has(.sidebar-user-block) {
                background: linear-gradient(135deg, #f0f7ff 0%, #dbeafe 100%) !important;
                background-color: #f0f7ff !important;
                border-color: #93c5fd !important;
                box-shadow: 0 6px 20px rgba(37, 99, 235, 0.18) !important;
            }
            .user-name-bold {
                color: #0f172a !important;
                font-weight: 850 !important;
            }
            .user-email-text {
                color: #475569 !important;
            }
            .user-role-thin {
                color: #1d4ed8 !important;
                font-weight: 750 !important;
            }
            .user-avatar-img {
                border: 2px solid #2563eb !important;
            }
            .user-status-dot {
                background: #10b981 !important;
                box-shadow: 0 0 6px #10b981 !important;
                border: 2px solid #ffffff !important;
            }
            .st-key-btn_quick_edit_profile,
            .st-key-btn_quick_edit_profile > div,
            .st-key-btn_quick_edit_profile button,
            div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile,
            div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile > div,
            div[data-testid="column"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile button,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile > div,
            div[data-testid="stColumn"]:has(.sidebar-vault-container) .st-key-btn_quick_edit_profile button {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #bfdbfe !important;
                color: #1d4ed8 !important;
                box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15) !important;
            }
            .st-key-btn_quick_edit_profile button:hover {
                background: #2563eb !important;
                background-color: #2563eb !important;
                border-color: #1d4ed8 !important;
                color: #ffffff !important;
                transform: scale(1.08) !important;
            }

            /* Single Logout Button in Profile Page Top Bar (Light Mode) */
            .st-key-btn_prof_top_single_logout {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            .st-key-btn_prof_top_single_logout button,
            .st-key-btn_prof_top_single_logout > button,
            .st-key-btn_prof_top_single_logout div > button,
            div.st-key-btn_prof_top_single_logout button {
                height: 38px !important;
                min-height: 38px !important;
                max-height: 38px !important;
                padding: 0 10px !important;
                font-size: 11.5px !important;
                font-weight: 750 !important;
                letter-spacing: -0.15px !important;
                border-radius: 9px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
                width: 100% !important;
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
                background-color: #dc2626 !important;
                border: 1px solid #b91c1c !important;
                color: #ffffff !important;
                box-shadow: 0 2px 8px rgba(220, 38, 38, 0.28) !important;
                transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }
            .st-key-btn_prof_top_single_logout button:hover,
            .st-key-btn_prof_top_single_logout > button:hover,
            .st-key-btn_prof_top_single_logout div > button:hover,
            div.st-key-btn_prof_top_single_logout button:hover {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
                background-color: #ef4444 !important;
                border-color: #dc2626 !important;
                box-shadow: 0 4px 14px rgba(239, 68, 68, 0.45) !important;
                color: #ffffff !important;
                transform: translateY(-1px) !important;
            }
            .st-key-btn_prof_top_single_logout button:active,
            .st-key-btn_prof_top_single_logout > button:active,
            div.st-key-btn_prof_top_single_logout button:active {
                transform: translateY(0) !important;
                box-shadow: 0 1px 4px rgba(220, 38, 38, 0.25) !important;
            }
            .st-key-btn_prof_top_single_logout button div[data-testid="stMarkdownContainer"],
            .st-key-btn_prof_top_single_logout button div,
            .st-key-btn_prof_top_single_logout button p,
            .st-key-btn_prof_top_single_logout button span,
            .st-key-btn_prof_top_single_logout button * {
                background: transparent !important;
                background-color: transparent !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-weight: 750 !important;
                font-size: 11.5px !important;
                line-height: 1 !important;
                white-space: nowrap !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 !important;
                padding: 0 !important;
            }




            /* 4. Top Command Deck (Header) */
            .vault-canvas-header {
                background: linear-gradient(180deg, #ffffff 0%, #fcfdfe 100%) !important;
                background-color: #ffffff !important;
                border: 1.5px solid #e2e8f0 !important;
                box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.03) !important;
                align-items: center !important;
                justify-content: space-between !important;
                padding: 16px 24px !important;
                gap: 16px !important;
                flex-wrap: nowrap !important;
                border-radius: 20px !important;
            }
            .header-title-column {
                min-width: 0 !important;
                flex: 1 !important;
            }
            .header-main-h1 {
                font-size: 24px !important;
                font-weight: 900 !important;
                letter-spacing: -0.5px !important;
                color: #0f172a !important;
                margin: 0 !important;
                line-height: 1.25 !important;
            }
            .header-sub-text {
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                flex-wrap: wrap !important;
                margin-top: 5px !important;
                font-size: 12.5px !important;
                line-height: 1.4 !important;
            }
            .header-platform-tag {
                background: #eff6ff !important;
                color: #1d4ed8 !important;
                border: 1px solid #bfdbfe !important;
                padding: 2.5px 8px !important;
                border-radius: 6px !important;
                font-size: 10px !important;
                font-weight: 800 !important;
                letter-spacing: 0.6px !important;
                text-transform: uppercase !important;
                white-space: nowrap !important;
            }
            .header-sub-desc {
                color: #475569 !important;
                font-weight: 600 !important;
                font-size: 12px !important;
                white-space: nowrap !important;
            }
            .header-sub-sep {
                color: #94a3b8 !important;
                font-weight: 700 !important;
                font-size: 11px !important;
            }
            .header-status-pill {
                display: inline-flex !important;
                align-items: center !important;
                gap: 5px !important;
                padding: 2px 9px !important;
                border-radius: 999px !important;
                font-size: 11px !important;
                font-weight: 750 !important;
                white-space: nowrap !important;
            }
            .header-status-pill.standby-pill {
                background: #f1f5f9 !important;
                color: #475569 !important;
                border: 1px solid #cbd5e1 !important;
            }
            .header-status-pill.active-pill {
                background: #ecfdf5 !important;
                color: #065f46 !important;
                border: 1px solid #a7f3d0 !important;
            }
            .header-emiten-pill {
                background: #eff6ff !important;
                border: 1px solid #93c5fd !important;
                padding: 2px 9px !important;
                border-radius: 7px !important;
                display: inline-flex !important;
                align-items: center !important;
                gap: 5px !important;
                font-size: 12px !important;
            }
            .emiten-pill-ticker {
                color: #1d4ed8 !important;
                font-weight: 900 !important;
                letter-spacing: 0.3px !important;
            }
            .emiten-pill-year {
                color: #334155 !important;
                font-weight: 700 !important;
            }
            .header-company-name {
                color: #334155 !important;
                font-weight: 650 !important;
                font-size: 12px !important;
                max-width: 280px !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                white-space: nowrap !important;
            }
            .header-search-box {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
                border: 1.5px solid #cbd5e1 !important;
                color: #0f172a !important;
            }
            .header-search-box input {
                color: #0f172a !important;
            }
            .header-search-box input::placeholder {
                color: #64748b !important;
            }

            /* Light Mode Live Header Clock (Real-Time) - Terkunci Permanen di Kanan Tanpa Bergeser */
            .header-datetime-box {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
                border: 1.5px solid #cbd5e1 !important;
                box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
                color: #0f172a !important;
                padding: 7px 18px !important;
                gap: 10px !important;
                margin-left: auto !important;
                margin-right: 0 !important;
                flex-shrink: 0 !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
            }
            .clock-icon {
                font-size: 14px !important;
                line-height: 1;
                display: inline-flex;
                align-items: center;
                flex-shrink: 0 !important;
            }
            .clock-live-indicator {
                display: inline-flex !important;
                align-items: center !important;
                gap: 6px !important;
                padding: 2px 8px !important;
                border-radius: 999px !important;
                font-size: 10.5px !important;
                font-weight: 800 !important;
                color: #065f46 !important;
                background: #ecfdf5 !important;
                border: 1px solid #a7f3d0 !important;
                letter-spacing: 0.5px !important;
                flex-shrink: 0 !important;
            }
            .clock-pulse-dot {
                width: 7px !important;
                height: 7px !important;
                border-radius: 50% !important;
                background: #059669 !important;
                box-shadow: 0 0 8px #059669 !important;
                animation: clockPulseAnim 2s infinite ease-in-out !important;
                display: inline-block !important;
                flex-shrink: 0 !important;
            }
            .clock-content {
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                font-size: 12px !important;
                white-space: nowrap !important;
            }
            .clock-time {
                color: #0f172a !important;
                font-weight: 850 !important;
                font-size: 12px !important;
                font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
                font-variant-numeric: tabular-nums !important;
                display: inline-block !important;
                min-width: 88px !important;
                text-align: center !important;
                flex-shrink: 0 !important;
            }
            .clock-sep {
                color: #94a3b8 !important;
                font-size: 11px !important;
                flex-shrink: 0 !important;
            }
            .clock-date {
                color: #475569 !important;
                font-weight: 650 !important;
                font-size: 12px !important;
                white-space: nowrap !important;
                flex-shrink: 0 !important;
            }

            /* Light Mode Actions Cluster */
            .header-actions-cluster {
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                margin-left: auto !important;
                flex-wrap: nowrap !important;
                margin-top: 2px !important;
            }

            /* Light Mode Executive Report Export Dropdown */
            .header-export-btn {
                background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
                color: #ffffff !important;
                border: 1px solid #047857 !important;
                box-shadow: 0 4px 16px rgba(5, 150, 105, 0.3) !important;
                padding: 5px 12px !important;
                font-size: 11px !important;
                gap: 5px !important;
                white-space: nowrap !important;
            }
            .header-export-btn:hover {
                background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
                box-shadow: 0 6px 20px rgba(5, 150, 105, 0.45) !important;
            }
            .header-export-menu {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12) !important;
            }
            .export-menu-header {
                border-bottom: 1px solid #e2e8f0 !important;
            }
            .export-menu-title {
                color: #64748b !important;
            }
            .export-menu-sub {
                color: #0369a1 !important;
            }
            .export-menu-item {
                color: #0f172a !important;
            }
            .export-menu-item:hover {
                background: #f1f5f9 !important;
                border-color: #cbd5e1 !important;
            }
            .export-item-title {
                color: #0f172a !important;
            }
            .export-item-sub {
                color: #475569 !important;
            }
            .export-item-badge {
                background: #e0f2fe !important;
                color: #0284c7 !important;
                border: 1px solid #bae6fd !important;
            }
            .export-menu-standby {
                background: #f8fafc !important;
                border: 1.5px dashed #cbd5e1 !important;
                color: #475569 !important;
            }
            .header-action-icon-circle {
                background: #f8fafc !important;
                border: 1.5px solid #cbd5e1 !important;
                color: #334155 !important;
            }
            .header-action-icon-circle:hover {
                background: #e2e8f0 !important;
                border-color: #94a3b8 !important;
                color: #0f172a !important;
            }

            .header-secondary-btn {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                border: 1.5px solid #cbd5e1 !important;
                color: #1e293b !important;
            }
            .header-secondary-btn:hover {
                background: #e2e8f0 !important;
                background-color: #e2e8f0 !important;
                border-color: #94a3b8 !important;
                color: #0f172a !important;
            }
            .header-primary-black-pill {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
                border: 1px solid #1d4ed8 !important;
                color: #ffffff !important;
                box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35) !important;
                padding: 5px 14px !important;
                font-size: 11px !important;
                gap: 5px !important;
            }
            .header-primary-black-pill:hover {
                background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
                box-shadow: 0 6px 22px rgba(37, 99, 235, 0.5) !important;
            }

            /* 5. Main Content Cards, Containers & Frames (ZERO DARK RESIDUES) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] > div,
            div[data-testid="stVerticalBlock"] > div[style*="border"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #e2e8f0 !important;
                border-radius: 18px !important;
                box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05), 0 1px 3px rgba(15, 23, 42, 0.02) !important;
                color: #0f172a !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
                border-color: #93c5fd !important;
                box-shadow: 0 8px 28px rgba(37, 99, 235, 0.1) !important;
            }

            /* Elimination of all inline dark card backgrounds across all HTML tags */
            *[style*="background: rgba(15,"], *[style*="background:rgba(15,"],
            *[style*="background: rgba(15, "], *[style*="background:rgba(15, "],
            *[style*="background: rgba(10,"], *[style*="background:rgba(10,"],
            *[style*="background: rgba(10, "], *[style*="background:rgba(10, "],
            *[style*="background: rgba(13,"], *[style*="background:rgba(13,"],
            *[style*="background: rgba(13, "], *[style*="background:rgba(13, "],
            *[style*="background: rgba(18,"], *[style*="background:rgba(18,"],
            *[style*="background: rgba(18, "], *[style*="background:rgba(18, "],
            *[style*="background: rgba(30,"], *[style*="background:rgba(30,"],
            *[style*="background: rgba(30, "], *[style*="background:rgba(30, "],
            *[style*="background: #0f172a"], *[style*="background:#0f172a"],
            *[style*="background: #111216"], *[style*="background:#111216"],
            *[style*="background: #141519"], *[style*="background:#141519"],
            *[style*="background: #171820"], *[style*="background:#171820"],
            *[style*="background: #0d0e12"], *[style*="background:#0d0e12"],
            *[style*="background: #070a12"], *[style*="background:#070a12"],
            *[style*="background: #131418"], *[style*="background:#131418"],
            *[style*="background: #0b0c10"], *[style*="background:#0b0c10"],
            *[style*="background: #1a1d24"], *[style*="background:#1a1d24"],
            *[style*="background: #1e293b"], *[style*="background:#1e293b"],
            *[style*="background: #1e1e24"], *[style*="background:#1e1e24"],
            *[style*="background: #09090b"], *[style*="background:#09090b"],
            *[style*="background: #18181b"], *[style*="background:#18181b"],
            *[style*="background: #1f2937"], *[style*="background:#1f2937"],
            *[style*="background: #111827"], *[style*="background:#111827"],
            *[style*="background: rgba(17, 24, 39"], *[style*="background:rgba(17, 24, 39"],
            *[style*="background: rgba(17,24,39"], *[style*="background:rgba(17,24,39"],
            *[style*="background: rgba(11, 17, 32"], *[style*="background:rgba(11, 17, 32"],
            *[style*="background: rgba(11,17,32"], *[style*="background:rgba(11,17,32"],
            *[style*="background: linear-gradient(180deg, rgba(17, 24, 39"], *[style*="background:linear-gradient(180deg, rgba(17, 24, 39"],
            *[style*="background: linear-gradient(135deg, rgba(15, 23, 42"], *[style*="background:linear-gradient(135deg, rgba(15, 23, 42"],
            *[style*="background: linear-gradient(135deg, rgba(15,23,42"], *[style*="background:linear-gradient(135deg, rgba(15,23,42"],
            *[style*="background: linear-gradient(135deg, rgba(30, 41, 59"], *[style*="background:linear-gradient(135deg, rgba(30, 41, 59"],
            *[style*="background: linear-gradient(135deg, rgba(30,41,59"], *[style*="background:linear-gradient(135deg, rgba(30,41,59"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border-color: #e2e8f0 !important;
                color: #0f172a !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05) !important;
            }

            /* Sub-panels with dark overlays to crisp light cards */
            *[style*="background: rgba(0,0,0"], *[style*="background:rgba(0,0,0"],
            *[style*="background: rgba(0, 0, 0"], *[style*="background:rgba(0, 0, 0"],
            *[style*="background: rgba(255, 255, 255, 0.0"], *[style*="background:rgba(255, 255, 255, 0.0"],
            *[style*="background: rgba(255,255,255,0.0"], *[style*="background:rgba(255,255,255,0.0"] {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
                border-color: #cbd5e1 !important;
                color: #0f172a !important;
            }

            /* Elimination of white specular border lines from dark mode */
            *[style*="border: 1px solid rgba(255, 255, 255"],
            *[style*="border:1px solid rgba(255, 255, 255"],
            *[style*="border: 1px solid rgba(255,255,255"],
            *[style*="border:1px solid rgba(255,255,255"],
            *[style*="border: 1.5px solid rgba(255, 255, 255"],
            *[style*="border:1.5px solid rgba(255, 255, 255"],
            *[style*="border: 1.5px solid rgba(255,255,255"],
            *[style*="border:1.5px solid rgba(255,255,255"] {
                border-color: #cbd5e1 !important;
            }

            /* Metric Cards & HUD Metrik */
            [data-testid="stMetric"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #e2e8f0 !important;
                border-radius: 14px !important;
                margin-bottom: 16px !important;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04) !important;
            }
            .hud-metric-card {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #e2e8f0 !important;
                margin-bottom: 18px !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
            }
            .metric-card-val {
                color: #0f172a !important;
                font-weight: 900 !important;
                text-align: right !important;
                justify-content: flex-end !important;
                display: flex !important;
                font-family: 'JetBrains Mono', monospace !important;
                font-variant-numeric: tabular-nums !important;
            }
            div[data-testid="stMetricValue"],
            div[data-testid="stMetricValue"] > div {
                text-align: right !important;
                justify-content: flex-end !important;
                display: flex !important;
                font-family: 'JetBrains Mono', monospace !important;
                font-variant-numeric: tabular-nums !important;
            }
            div[data-testid="stMetricDelta"],
            div[data-testid="stMetricDelta"] > div {
                text-align: right !important;
                justify-content: flex-end !important;
                display: flex !important;
            }
            input[type="number"],
            div[data-baseweb="input"] input[type="number"],
            div[data-testid="stNumberInput"] input {
                text-align: right !important;
                font-family: 'JetBrains Mono', monospace !important;
                font-variant-numeric: tabular-nums !important;
            }
            .metric-card-title {
                color: #1e293b !important;
                font-weight: 800 !important;
                letter-spacing: 0.5px !important;
            }


            /* 6. Comprehensive Tables & DataFrames (ZERO BLACK TABLES) */
            /* Streamlit DataFrame & Glide Data Grid */
            div[data-testid="stDataFrame"],
            div[data-testid="stDataFrameResizable"],
            div[data-testid="stDataFrame"] > div,
            div[data-testid="stDataFrameResizable"] > div,
            div[data-testid="stDataFrame"] [data-testid="glide-data-grid"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 14px !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05) !important;
                overflow: hidden !important;
            }
            div[data-testid="stDataFrame"] * {
                color: #0f172a !important;
            }

            /* Glide Data Grid HTML5 Canvas: Native clean white canvas tanpa filter inversi */
            div[data-testid="stDataFrame"] canvas,
            div[data-testid="stDataFrameResizable"] canvas,
            .dvn-canvas,
            .dvn-scroller canvas {
                filter: none !important;
                background: #ffffff !important;
                background-color: #ffffff !important;
            }

            /* Streamlit Dataframe Glide Grid Tokens: Pure White Cells, Light Slate Headers, Dark Navy Text */
            div[data-testid="stDataFrame"],
            div[data-testid="stDataFrameResizable"] {
                --gdg-bg-cell: #ffffff !important;
                --gdg-bg-cell-medium: #f8fafc !important;
                --gdg-bg-header: #f1f5f9 !important;
                --gdg-bg-header-has-focus: #e2e8f0 !important;
                --gdg-bg-header-hovered: #e2e8f0 !important;
                --gdg-text-dark: #0f172a !important;
                --gdg-text-medium: #1e293b !important;
                --gdg-text-light: #475569 !important;
                --gdg-accent-color: #2563eb !important;
                --gdg-accent-light: #eff6ff !important;
                --gdg-line-color: #cbd5e1 !important;
                --gdg-header-bottom-border-color: #cbd5e1 !important;
            }

            /* Native Streamlit Table */
            div[data-testid="stTable"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 14px !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
                overflow: hidden !important;
            }
            div[data-testid="stTable"] table {
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #0f172a !important;
                border-collapse: collapse !important;
                width: 100% !important;
            }
            div[data-testid="stTable"] thead tr th,
            div[data-testid="stTable"] th {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                color: #0f172a !important;
                font-weight: 800 !important;
                border-bottom: 2px solid #cbd5e1 !important;
                padding: 10px 14px !important;
            }
            div[data-testid="stTable"] tbody tr td,
            div[data-testid="stTable"] td {
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #1e293b !important;
                border-bottom: 1px solid #e2e8f0 !important;
                padding: 8px 14px !important;
            }
            div[data-testid="stTable"] tbody tr:nth-child(even) td {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
            }
            div[data-testid="stTable"] tbody tr:hover td {
                background: #eff6ff !important;
                background-color: #eff6ff !important;
            }

            /* Generic HTML / Markdown Tables */
            table {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 12px !important;
                color: #0f172a !important;
                border-collapse: collapse !important;
                width: 100% !important;
                overflow: hidden !important;
            }
            thead tr th, table th {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                color: #0f172a !important;
                font-weight: 800 !important;
                border-bottom: 2px solid #cbd5e1 !important;
                padding: 9px 12px !important;
            }
            tbody tr td, table td {
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #1e293b !important;
                border-bottom: 1px solid #e2e8f0 !important;
                padding: 8px 12px !important;
            }
            tbody tr:nth-child(even) td {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
            }
            tbody tr:hover td {
                background: #eff6ff !important;
                background-color: #eff6ff !important;
            }

            /* Numeric Right Alignment for Tables */
            table td.text-right, table th.text-right,
            table td.num, table th.num,
            table td.numeric, table th.numeric,
            table td[align="right"], table th[align="right"],
            table td[style*="text-align:right"], table td[style*="text-align: right"],
            table th[style*="text-align:right"], table th[style*="text-align: right"],
            .table-numeric, .table-num,
            div[data-testid="stTable"] td.text-right,
            div[data-testid="stTable"] th.text-right,
            div[data-testid="stTable"] td[align="right"],
            div[data-testid="stTable"] th[align="right"],
            div[data-testid="stTable"] td:has(.font-mono-num),
            div[data-testid="stTable"] td:has(.mono-num) {
                text-align: right !important;
                font-family: 'JetBrains Mono', monospace !important;
                font-variant-numeric: tabular-nums !important;
            }

            /* Minimalist Key-Value Tables (.kv-table) */
            .kv-table {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 14px !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04) !important;
                overflow: hidden !important;
            }
            .kv-row {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border-bottom: 1px solid #e2e8f0 !important;
            }
            .kv-row:nth-child(even) {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
            }
            .kv-row:hover {
                background: #eff6ff !important;
                background-color: #eff6ff !important;
            }
            .kv-label, .kv-row div:first-child, .kv-row span:first-child {
                color: #1e293b !important;
                font-weight: 700 !important;
            }
            .kv-val, .kv-row div:last-child, .kv-row span:last-child {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                border: 1px solid #cbd5e1 !important;
                color: #0f172a !important;
                font-weight: 850 !important;
            }

            /* 7. Markdown & Global Typography Contrast Enforcement */
            div[data-testid="stMarkdownContainer"] p,
            div[data-testid="stMarkdownContainer"] span,
            div[data-testid="stMarkdownContainer"] li,
            div[data-testid="stMarkdownContainer"] td,
            div[data-testid="stMarkdownContainer"] th,
            div[data-testid="stMarkdownContainer"] label,
            div[data-testid="stMarkdownContainer"] div {
                color: #1e293b !important;
            }
            div[data-testid="stMarkdownContainer"] strong,
            div[data-testid="stMarkdownContainer"] b {
                color: #0f172a !important;
                font-weight: 800 !important;
            }
            div[data-testid="stMarkdownContainer"] h1,
            div[data-testid="stMarkdownContainer"] h2,
            div[data-testid="stMarkdownContainer"] h3,
            div[data-testid="stMarkdownContainer"] h4,
            div[data-testid="stMarkdownContainer"] h5,
            div[data-testid="stMarkdownContainer"] h6 {
                color: #0f172a !important;
                font-weight: 850 !important;
                hyphens: none !important;
                -webkit-hyphens: none !important;
                word-break: normal !important;
            }

            /* Formula KaTeX / LaTeX Matematika agar hitam pekat di mode terang */
            .katex, .katex-display, .katex *, [data-testid="stLatexContainer"], [data-testid="stLatexContainer"] * {
                color: #0f172a !important;
            }

            /* Captions & Keterangan */
            div[data-testid="stCaptionContainer"],
            div[data-testid="stCaptionContainer"] p,
            div[data-testid="stCaptionContainer"] span,
            .stCaption,
            .stCaption p {
                color: #334155 !important;
                font-weight: 650 !important;
            }

            /* Streamlit Widget Labels & Metrics (Bold & Sharp in Light Mode) */
            [data-testid="stWidgetLabel"] p,
            [data-testid="stWidgetLabel"] span,
            [data-testid="stWidgetLabel"] label,
            div[data-testid="stMetricLabel"] p,
            div[data-testid="stMetricLabel"] span,
            div[data-testid="stMetricLabel"] div {
                color: #0f172a !important;
                font-weight: 750 !important;
            }
            div[data-testid="stMetricValue"] div {
                color: #0f172a !important;
                font-weight: 900 !important;
            }

            /* Streamlit Alert Boxes */
            div[data-testid="stAlert"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05) !important;
            }
            div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
            div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
            div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] div {
                color: #0f172a !important;
                font-weight: 600 !important;
            }

            /* High-Contrast Text Overrides (NO BLURRY / FAINT GRAY OR TRANSPARENT WHITE TEXT) */
            *[style*="color:#94a3b8"], *[style*="color: #94a3b8"],
            *[style*="color:#cbd5e1"], *[style*="color: #cbd5e1"],
            *[style*="color:#64748b"], *[style*="color: #64748b"],
            *[style*="color:#9ca3af"], *[style*="color: #9ca3af"],
            *[style*="color:#a1a1aa"], *[style*="color: #a1a1aa"],
            *[style*="color:#6b7280"], *[style*="color: #6b7280"],
            *[style*="color:#4b5563"], *[style*="color: #4b5563"],
            *[style*="color:#778397"], *[style*="color: #778397"],
            *[style*="color:#7b8495"], *[style*="color: #7b8495"],
            *[style*="color:#888"], *[style*="color: #888"],
            *[style*="color:#999"], *[style*="color: #999"],
            *[style*="color:#aaa"], *[style*="color: #aaa"],
            *[style*="color:#bbb"], *[style*="color: #bbb"],
            *[style*="color:#ccc"], *[style*="color: #ccc"],
            *[style*="color: rgba(255, 255, 255"], *[style*="color:rgba(255, 255, 255"],
            *[style*="color: rgba(255,255,255"], *[style*="color:rgba(255,255,255"] {
                color: #1e293b !important;
                font-weight: 650 !important;
            }
            *[style*="color:#f8fafc"], *[style*="color: #f8fafc"],
            *[style*="color:#f1f5f9"], *[style*="color: #f1f5f9"] {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            *[style*="color:#ffffff"]:not(.header-primary-black-pill *):not(.badge-active *):not(button[kind="primary"] *):not(.sidebar-logo-icon *):not(.st-key-btn_apply_theme_light *):not(.st-key-btn_apply_theme_dark *):not([role="radiogroup"] label:has(input:checked) *):not(.metric-icon-square *):not(.user-status-dot *):not(.st-key-btn_save_edit_account_form *):not(.metric-card-val):not(.badge-distress *):not(.badge-safe *):not(.theme-chip-white),
            *[style*="color: #ffffff"]:not(.header-primary-black-pill *):not(.badge-active *):not(button[kind="primary"] *):not(.sidebar-logo-icon *):not(.st-key-btn_apply_theme_light *):not(.st-key-btn_apply_theme_dark *):not([role="radiogroup"] label:has(input:checked) *):not(.metric-icon-square *):not(.user-status-dot *):not(.st-key-btn_save_edit_account_form *):not(.metric-card-val):not(.badge-distress *):not(.badge-safe *):not(.theme-chip-white),
            *[style*="color:white"]:not(.header-primary-black-pill *):not(.badge-active *):not(button[kind="primary"] *):not(.sidebar-logo-icon *):not(.st-key-btn_apply_theme_light *):not(.st-key-btn_apply_theme_dark *):not([role="radiogroup"] label:has(input:checked) *):not(.metric-icon-square *):not(.user-status-dot *):not(.st-key-btn_save_edit_account_form *):not(.metric-card-val):not(.badge-distress *):not(.badge-safe *):not(.theme-chip-white),
            *[style*="color: white"]:not(.header-primary-black-pill *):not(.badge-active *):not(button[kind="primary"] *):not(.sidebar-logo-icon *):not(.st-key-btn_apply_theme_light *):not(.st-key-btn_apply_theme_dark *):not([role="radiogroup"] label:has(input:checked) *):not(.metric-icon-square *):not(.user-status-dot *):not(.st-key-btn_save_edit_account_form *):not(.metric-card-val):not(.badge-distress *):not(.badge-safe *):not(.theme-chip-white),
            *[style*="color:#fff"]:not(.header-primary-black-pill *):not(.badge-active *):not(button[kind="primary"] *):not(.sidebar-logo-icon *):not(.st-key-btn_apply_theme_light *):not(.st-key-btn_apply_theme_dark *):not([role="radiogroup"] label:has(input:checked) *):not(.metric-icon-square *):not(.user-status-dot *):not(.st-key-btn_save_edit_account_form *):not(.metric-card-val):not(.badge-distress *):not(.badge-safe *):not(.theme-chip-white),
            *[style*="color: #fff"]:not(.header-primary-black-pill *):not(.badge-active *):not(button[kind="primary"] *):not(.sidebar-logo-icon *):not(.st-key-btn_apply_theme_light *):not(.st-key-btn_apply_theme_dark *):not([role="radiogroup"] label:has(input:checked) *):not(.metric-icon-square *):not(.user-status-dot *):not(.st-key-btn_save_edit_account_form *):not(.metric-card-val):not(.badge-distress *):not(.badge-safe *):not(.theme-chip-white) {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }

            /* 8. Form Inputs, Selectors, Tabs, Buttons & Expanders */
            .stTextInput input, .stNumberInput input, .stTextArea textarea,
            [data-baseweb="input"] input, [data-baseweb="base-input"] input,
            div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input,
            div[data-testid="stTextArea"] textarea {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
                font-weight: 600 !important;
            }
            .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus,
            [data-baseweb="input"]:focus-within, [data-baseweb="base-input"]:focus-within {
                border-color: #2563eb !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
            }
            .stTextInput input::placeholder, .stNumberInput input::placeholder,
            .stTextArea textarea::placeholder, [data-baseweb="input"] input::placeholder,
            [data-baseweb="base-input"] input::placeholder,
            [data-baseweb="select"] input::placeholder,
            div[data-testid="stSelectbox"] input::placeholder {
                color: #64748b !important;
                -webkit-text-fill-color: #64748b !important;
            }

            /* Light Mode Streamlit Password Toggle Button Protection */
            div[data-baseweb="input"] button,
            div[data-baseweb="base-input"] button,
            button[data-testid*="stTextInputPasswordToggle"],
            [data-testid="stTextInputPasswordToggle"],
            button[aria-label*="password" i],
            button[aria-label*="visibility" i] {
                color: #475569 !important;
                background: transparent !important;
                background-color: transparent !important;
            }
            div[data-baseweb="input"] button:hover,
            div[data-baseweb="base-input"] button:hover,
            button[data-testid*="stTextInputPasswordToggle"]:hover,
            button[aria-label*="password" i]:hover,
            button[aria-label*="visibility" i]:hover {
                color: #2563eb !important;
            }
            div[data-baseweb="input"] button svg,
            div[data-baseweb="base-input"] button svg,
            button[data-testid*="stTextInputPasswordToggle"] svg,
            [data-testid="stTextInputPasswordToggle"] svg,
            button[aria-label*="password" i] svg,
            button[aria-label*="visibility" i] svg {
                fill: currentColor !important;
                color: inherit !important;
            }

            /* Selectbox, MultiSelect & BaseWeb Dropdown Selectors */
            [data-baseweb="select"],
            [data-baseweb="select"] > div,
            div[data-testid="stSelectbox"] > div,
            div[data-testid="stMultiSelect"] > div {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 12px !important;
            }
            [data-baseweb="select"]:focus-within > div,
            div[data-testid="stSelectbox"]:focus-within > div,
            div[data-testid="stMultiSelect"]:focus-within > div {
                border-color: #2563eb !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
            }
            /* Selected Value Text in Selectbox: Target ALL descendants */
            [data-baseweb="select"] *,
            [data-baseweb="select"] div,
            [data-baseweb="select"] span,
            [data-baseweb="select"] input,
            div[data-testid="stSelectbox"] *,
            div[data-testid="stSelectbox"] div,
            div[data-testid="stSelectbox"] span,
            div[data-testid="stSelectbox"] input,
            div[data-testid="stSelectbox"] [data-baseweb="select"] *,
            div[data-testid="stSelectbox"] [data-baseweb="select"] div,
            div[data-testid="stSelectbox"] [data-baseweb="select"] span,
            div[data-testid="stSelectbox"] [data-baseweb="select"] input,
            div[data-testid="stMultiSelect"] *,
            div[data-testid="stMultiSelect"] div,
            div[data-testid="stMultiSelect"] span,
            div[data-testid="stMultiSelect"] input {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            /* Dropdown icon (arrow) and clear icon */
            [data-baseweb="select"] svg,
            div[data-testid="stSelectbox"] svg,
            div[data-testid="stMultiSelect"] svg {
                color: #0f172a !important;
                fill: #0f172a !important;
            }

            /* Dropdown Popover Menus & Options List */
            [data-baseweb="popover"],
            [data-baseweb="menu"],
            ul[role="listbox"],
            div[data-baseweb="popover"] > div,
            div[data-baseweb="popover"] ul {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #e2e8f0 !important;
                box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1) !important;
                border-radius: 12px !important;
            }
            li[role="option"],
            [data-baseweb="menu"] li,
            ul[role="listbox"] li {
                background: transparent !important;
                background-color: transparent !important;
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            li[role="option"] *,
            [data-baseweb="menu"] li *,
            ul[role="listbox"] li * {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            li[role="option"]:hover,
            li[role="option"]:hover *,
            [data-baseweb="menu"] li:hover,
            [data-baseweb="menu"] li:hover *,
            ul[role="listbox"] li:hover,
            ul[role="listbox"] li:hover *,
            li[role="option"][aria-selected="true"],
            li[role="option"][aria-selected="true"] * {
                background: #eff6ff !important;
                background-color: #eff6ff !important;
                color: #1d4ed8 !important;
                -webkit-text-fill-color: #1d4ed8 !important;
            }

            /* MultiSelect Tag Chips in Light Mode */
            [data-baseweb="tag"] {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                border: 1px solid #cbd5e1 !important;
            }
            [data-baseweb="tag"] span,
            [data-baseweb="tag"] div {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            [data-baseweb="tag"] svg {
                fill: #64748b !important;
            }

            /* Date & Calendar Picker Bubble in Light Mode */
            div[data-testid="stDateInput"] {
                width: 100% !important;
            }
            div[data-testid="stDateInput"] [data-baseweb="input"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 12px !important;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
            }
            div[data-testid="stDateInput"] [data-baseweb="input"]:focus-within {
                border-color: #2563eb !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
            }
            div[data-testid="stDateInput"] input {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
                font-weight: 700 !important;
                font-family: 'JetBrains Mono', monospace !important;
            }
            div[data-testid="stDateInput"] svg,
            div[data-testid="stDateInput"] button {
                color: #2563eb !important;
                fill: #2563eb !important;
            }
            div[data-baseweb="popover"]:has(div[data-baseweb="calendar"]) {
                border-radius: 16px !important;
                overflow: hidden !important;
                box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12), 0 0 0 1.5px #cbd5e1 !important;
            }
            div[data-baseweb="calendar"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 16px !important;
                padding: 10px !important;
                color: #0f172a !important;
            }
            div[data-baseweb="calendar"] * {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            div[data-baseweb="calendar"] header button {
                color: #2563eb !important;
                border-radius: 8px !important;
            }
            div[data-baseweb="calendar"] header select {
                color: #0f172a !important;
                background: #f1f5f9 !important;
                border-radius: 8px !important;
                border: 1px solid #cbd5e1 !important;
                font-weight: 700 !important;
            }
            div[data-baseweb="calendar"] div[role="columnheader"] {
                color: #475569 !important;
                font-weight: 800 !important;
                font-size: 11px !important;
            }
            div[data-baseweb="calendar"] div[role="gridcell"] {
                color: #1e293b !important;
                border-radius: 8px !important;
                font-weight: 650 !important;
                transition: all 0.15s ease !important;
            }
            div[data-baseweb="calendar"] div[role="gridcell"]:hover {
                background: #eff6ff !important;
                color: #2563eb !important;
            }
            div[data-baseweb="calendar"] div[aria-selected="true"],
            div[data-baseweb="calendar"] div[aria-selected="true"] * {
                background: #2563eb !important;
                background-color: #2563eb !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-weight: 850 !important;
                box-shadow: 0 2px 10px rgba(37, 99, 235, 0.4) !important;
            }

            /* File Uploader in Light Mode */
            [data-testid="stFileUploader"] section {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px dashed #cbd5e1 !important;
            }
            [data-testid="stFileUploader"] section * {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            [data-testid="stFileUploader"] section small {
                color: #64748b !important;
                -webkit-text-fill-color: #64748b !important;
            }

            /* Primary & Secondary Buttons */
            .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
                border: 1px solid #1d4ed8 !important;
                color: #ffffff !important;
                box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
            }
            .stButton button[kind="primary"]:hover, .stDownloadButton button[kind="primary"]:hover {
                background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
                box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
                color: #ffffff !important;
            }
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button) {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                color: #0f172a !important;
                font-weight: 750 !important;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05) !important;
            }
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button) *,
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button) p,
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button) span {
                color: #0f172a !important;
                font-weight: 750 !important;
            }
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button):hover {
                background: #f8fafc !important;
                background-color: #f8fafc !important;
                border-color: #2563eb !important;
                color: #1d4ed8 !important;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
            }
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button):hover *,
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button):hover p,
            .stButton button:not([kind="primary"]):not(.st-key-btn_quick_edit_profile button):not(.st-key-btn_sidebar_logout_bottom button):not(.st-key-btn_prof_top_single_logout button):not(.st-key-btn_logout_prof_card button):not(.st-key-btn_prof_nav_logout button):not(.st-key-btn_logout_prof_form button):not(.st-key-btn_confirm_logout_yes button):hover span {
                color: #1d4ed8 !important;
            }

            /* Light Mode Top Navigation Quick Nav Buttons (Pintasan Navigasi: Rapi, Lega, Tengah & Anti-Berdempetan) */
            .st-key-btn_goto_dl_from_dash,
            .st-key-btn_goto_pred_from_adm_dash,
            .st-key-btn_goto_eval_from_adm_dash,
            .st-key-btn_goto_api_from_dash,
            .st-key-btn_goto_rh_from_pe,
            .st-key-btn_goto_dash_from_pe,
            .st-key-btn_goto_dl_from_rh,
            .st-key-btn_goto_dash_from_rh,
            .st-key-btn_prof_goto_dash,
            .st-key-btn_prof_goto_results,
            .st-key-btn_prof_top_single_logout {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            .st-key-btn_goto_dl_from_dash button,
            .st-key-btn_goto_pred_from_adm_dash button,
            .st-key-btn_goto_eval_from_adm_dash button,
            .st-key-btn_goto_api_from_dash button,
            .st-key-btn_goto_rh_from_pe button,
            .st-key-btn_goto_dash_from_pe button,
            .st-key-btn_goto_dl_from_rh button,
            .st-key-btn_goto_dash_from_rh button,
            .st-key-btn_prof_goto_dash button,
            .st-key-btn_prof_goto_results button {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                color: #0f172a !important;
                box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05) !important;
                height: 38px !important;
                min-height: 38px !important;
                max-height: 38px !important;
                padding: 0 8px !important;
                font-size: 11.5px !important;
                font-weight: 750 !important;
                letter-spacing: -0.15px !important;
                border-radius: 9px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
                width: 100% !important;
                transition: all 0.18s ease !important;
            }
            .st-key-btn_goto_dl_from_dash button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_pred_from_adm_dash button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_eval_from_adm_dash button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_api_from_dash button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_rh_from_pe button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_dash_from_pe button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_dl_from_rh button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_dash_from_rh button div[data-testid="stMarkdownContainer"],
            .st-key-btn_prof_goto_dash button div[data-testid="stMarkdownContainer"],
            .st-key-btn_prof_goto_results button div[data-testid="stMarkdownContainer"],
            .st-key-btn_goto_dl_from_dash button div,
            .st-key-btn_goto_pred_from_adm_dash button div,
            .st-key-btn_goto_eval_from_adm_dash button div,
            .st-key-btn_goto_api_from_dash button div,
            .st-key-btn_goto_rh_from_pe button div,
            .st-key-btn_goto_dash_from_pe button div,
            .st-key-btn_goto_dl_from_rh button div,
            .st-key-btn_goto_dash_from_rh button div,
            .st-key-btn_prof_goto_dash button div,
            .st-key-btn_prof_goto_results button div {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                width: 100% !important;
                margin: 0 auto !important;
            }
            .st-key-btn_goto_dl_from_dash button p,
            .st-key-btn_goto_pred_from_adm_dash button p,
            .st-key-btn_goto_eval_from_adm_dash button p,
            .st-key-btn_goto_api_from_dash button p,
            .st-key-btn_goto_rh_from_pe button p,
            .st-key-btn_goto_dash_from_pe button p,
            .st-key-btn_goto_dl_from_rh button p,
            .st-key-btn_goto_dash_from_rh button p,
            .st-key-btn_prof_goto_dash button p,
            .st-key-btn_prof_goto_results button p {
                font-size: 11.5px !important;
                font-weight: 750 !important;
                white-space: nowrap !important;
                color: #0f172a !important;
                margin: 0 auto !important;
                padding: 0 !important;
                line-height: 1 !important;
                text-align: center !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
            }
            .st-key-btn_goto_dl_from_dash button:hover,
            .st-key-btn_goto_pred_from_adm_dash button:hover,
            .st-key-btn_goto_eval_from_adm_dash button:hover,
            .st-key-btn_goto_api_from_dash button:hover,
            .st-key-btn_goto_rh_from_pe button:hover,
            .st-key-btn_goto_dash_from_pe button:hover,
            .st-key-btn_goto_dl_from_rh button:hover,
            .st-key-btn_goto_dash_from_rh button:hover,
            .st-key-btn_prof_goto_dash button:hover,
            .st-key-btn_prof_goto_results button:hover {
                background: #eff6ff !important;
                background-color: #eff6ff !important;
                border-color: #2563eb !important;
                color: #1d4ed8 !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12) !important;
            }
            .st-key-btn_goto_dl_from_dash button:hover *,
            .st-key-btn_goto_pred_from_adm_dash button:hover *,
            .st-key-btn_goto_eval_from_adm_dash button:hover *,
            .st-key-btn_goto_api_from_dash button:hover *,
            .st-key-btn_goto_rh_from_pe button:hover *,
            .st-key-btn_goto_dash_from_pe button:hover *,
            .st-key-btn_goto_dl_from_rh button:hover *,
            .st-key-btn_goto_dash_from_rh button:hover *,
            .st-key-btn_prof_goto_dash button:hover *,
            .st-key-btn_prof_goto_results button:hover * {
                color: #1d4ed8 !important;
            }

            /* Tabs & Expanders */
            [data-baseweb="tab-list"] {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                border-radius: 12px !important;
                padding: 4px !important;
                border: 1.5px solid #e2e8f0 !important;
            }
            [data-baseweb="tab"] {
                color: #334155 !important;
                font-weight: 750 !important;
            }
            [data-baseweb="tab"]:hover {
                color: #1d4ed8 !important;
            }
            [data-baseweb="tab"][aria-selected="true"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                color: #1d4ed8 !important;
                font-weight: 850 !important;
                box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
            }

            /* Light Mode Spinner Styling (Glassmorphic White FinTech) */
            div[data-testid="stSpinner"],
            .stSpinner {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(241, 245, 249, 0.96) 100%) !important;
                border: 1px solid rgba(37, 99, 235, 0.3) !important;
                box-shadow: 0 12px 32px rgba(37, 99, 235, 0.12), 0 2px 8px rgba(0, 0, 0, 0.05) !important;
            }
            div[data-testid="stSpinner"]::before,
            .stSpinner::before {
                background: linear-gradient(90deg, transparent, #2563eb, #38bdf8, #059669, transparent) !important;
            }
            div[data-testid="stSpinner"] svg,
            .stSpinner svg {
                color: #2563eb !important;
                stroke: #2563eb !important;
                filter: drop-shadow(0 0 6px rgba(37, 99, 235, 0.45)) !important;
            }
            div[data-testid="stSpinner"] [data-testid="stMarkdownContainer"] p,
            div[data-testid="stSpinner"] span,
            div[data-testid="stSpinner"] div {
                color: #0f172a !important;
                font-weight: 750 !important;
            }

            div[data-testid="stExpander"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1.5px solid #e2e8f0 !important;
                border-radius: 14px !important;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03) !important;
            }
            div[data-testid="stExpander"] summary {
                color: #0f172a !important;
                font-weight: 750 !important;
            }
            div[data-testid="stExpander"] summary:hover {
                color: #1d4ed8 !important;
            }
            div[data-testid="stExpander"] [data-testid="stExpanderDetails"],
            div[data-testid="stExpander"] [data-testid="stExpanderDetails"] p,
            div[data-testid="stExpander"] [data-testid="stExpanderDetails"] span,
            div[data-testid="stExpander"] [data-testid="stExpanderDetails"] li {
                color: #1e293b !important;
            }

            /* Radio & Checkbox Labels */
            div[data-testid="stRadio"] label,
            div[data-testid="stRadio"] label p,
            div[data-testid="stRadio"] label span,
            div[data-testid="stCheckbox"] label,
            div[data-testid="stCheckbox"] label p,
            div[data-testid="stCheckbox"] label span {
                color: #0f172a !important;
                font-weight: 650 !important;
            }

            /* Select single-radio buttons in main area */
            div[data-testid="stRadio"]:not(:has(.sidebar-vault-container)) label:has(input:checked) [data-baseweb="radio"] > div:first-child,
            div[data-testid="stRadio"]:not(:has(.sidebar-vault-container)) label[data-checked="true"] [data-baseweb="radio"] > div:first-child {
                border: 2px solid #2563eb !important;
                background-color: #2563eb !important;
                background: #2563eb !important;
                box-shadow: 0 0 10px rgba(37, 99, 235, 0.4) !important;
            }

            /* Code Blocks */
            code, pre, pre code, div[data-testid="stCodeBlock"] {
                background: #f1f5f9 !important;
                background-color: #f1f5f9 !important;
                border: 1px solid #cbd5e1 !important;
                color: #0f172a !important;
                font-weight: 650 !important;
            }

            /* Profile Page Logout Menu & Action Buttons (Light Mode) */
            .st-key-btn_prof_top_single_logout {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            .st-key-btn_prof_top_single_logout button,
            .st-key-btn_logout_prof_card button,
            .st-key-btn_prof_nav_logout button,
            .st-key-btn_logout_prof_form button,
            .st-key-btn_confirm_logout_yes button {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
                background-color: #dc2626 !important;
                color: #ffffff !important;
                border: 1px solid #b91c1c !important;
                box-shadow: 0 4px 14px rgba(220, 38, 38, 0.28) !important;
                font-weight: 800 !important;
                border-radius: 9px !important;
                height: 38px !important;
                min-height: 38px !important;
                max-height: 38px !important;
                padding: 0 10px !important;
                font-size: 11.5px !important;
                letter-spacing: -0.15px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
                width: 100% !important;
                transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }
            .st-key-btn_prof_top_single_logout button:hover,
            .st-key-btn_logout_prof_card button:hover,
            .st-key-btn_prof_nav_logout button:hover,
            .st-key-btn_logout_prof_form button:hover,
            .st-key-btn_confirm_logout_yes button:hover {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
                border-color: #dc2626 !important;
                box-shadow: 0 6px 20px rgba(220, 38, 38, 0.42) !important;
                transform: translateY(-1px) !important;
                color: #ffffff !important;
            }
            .st-key-btn_prof_top_single_logout button *,
            .st-key-btn_prof_top_single_logout button p,
            .st-key-btn_prof_top_single_logout button span,
            .st-key-btn_logout_prof_card button *,
            .st-key-btn_prof_nav_logout button *,
            .st-key-btn_logout_prof_form button *,
            .st-key-btn_confirm_logout_yes button * {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-weight: 750 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            /* ===================================================================== */
            /* DARK MODE: HARMONIZATION WITH SOFT GLOWING NEON BLUE ACCENTS         */
            /* ===================================================================== */
            :root {
                --border-focus: #38bdf8;
                --ai-violet: #60a5fa;
                --ai-violet-glow: rgba(56, 189, 248, 0.35);
            }
            div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
                border-color: rgba(56, 189, 248, 0.35) !important;
                box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.55), 0 0 20px rgba(56, 189, 248, 0.12), inset 0 1px 0 0 rgba(255, 255, 255, 0.12) !important;
            }
            .header-primary-black-pill {
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5), 0 0 16px rgba(56, 189, 248, 0.25) !important;
            }
            .header-primary-black-pill:hover {
                border-color: rgba(56, 189, 248, 0.5) !important;
                box-shadow: 0 6px 24px rgba(56, 189, 248, 0.35) !important;
            }
            .sidebar-logo-icon:hover {
                border-color: rgba(56, 189, 248, 0.4) !important;
                box-shadow: 0 6px 22px rgba(56, 189, 248, 0.25) !important;
            }

            /* Dark Mode Typography & Form Controls */
            html, body, .stApp, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, input, select, textarea {
                color: #f8fafc !important;
                -webkit-text-fill-color: #f8fafc !important;
            }
            div[data-testid="stMarkdownContainer"] p,
            div[data-testid="stMarkdownContainer"] span,
            div[data-testid="stMarkdownContainer"] li {
                color: #cbd5e1 !important;
                -webkit-text-fill-color: #cbd5e1 !important;
            }
            div[data-testid="stMarkdownContainer"] strong,
            div[data-testid="stMarkdownContainer"] b {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }
            div[data-baseweb="input"] input,
            div[data-baseweb="base-input"] input,
            div[data-baseweb="textarea"] textarea {
                color: #f8fafc !important;
                -webkit-text-fill-color: #f8fafc !important;
            }
            div[data-baseweb="select"] span,
            div[data-baseweb="select"] div,
            div[data-baseweb="select"] input {
                color: #f8fafc !important;
                -webkit-text-fill-color: #f8fafc !important;
            }
            label[data-testid="stWidgetLabel"],
            label[data-testid="stWidgetLabel"] p,
            label[data-testid="stWidgetLabel"] span {
                color: #cbd5e1 !important;
                -webkit-text-fill-color: #cbd5e1 !important;
            }
            li[role="option"] {
                color: #cbd5e1 !important;
                -webkit-text-fill-color: #cbd5e1 !important;
            }
            li[role="option"]:hover,
            li[role="option"][aria-selected="true"] {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }

            /* Dark Mode Glide Data Grid: Invert light canvas ke obsidian dark palette */
            div[data-testid="stDataFrame"] canvas,
            div[data-testid="stDataFrameResizable"] canvas,
            .dvn-canvas,
            .dvn-scroller canvas {
                filter: invert(1) hue-rotate(180deg) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )