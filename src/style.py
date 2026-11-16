"""Design system HexaRoute pour Streamlit."""
import streamlit as st


def apply_style():
    st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --hero:#0D1428; --line:#263753; --muted:#8FA1BD; --cyan:#62DCE8; --yellow:#F8CA7A; }
    html, body, [class*="css"], [data-testid="stApp"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #090E19; color: #EBF1FF; }
    .block-container { padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1490px; }
    [data-testid="stSidebar"] { background: #11192B; border-right: 1px solid #27344D; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #B4C4DE; }
    [data-testid="stMetric"] { background: #131D30; border:1px solid #293955; border-radius: 16px; padding: 17px 21px; }
    [data-testid="stMetricLabel"] { color:#A5B7D4; font-weight:600; }
    [data-testid="stMetricValue"] { font-family:'Space Grotesk', sans-serif; letter-spacing:-.04em; }
    [data-testid="stTabs"] button { font-size:.95rem; font-weight:600; }
    [data-testid="stDataFrame"] { border: 1px solid #293955; border-radius:12px; }
    .hero { border:1px solid #344C69; border-radius:22px; padding:30px 34px;
      margin-bottom:16px; background:radial-gradient(circle at 86% 20%, #173E4A 0, transparent 34%),
      linear-gradient(115deg,#101B2E 0%, #172443 65%, #132A38 100%); }
    .eyebrow {font-size:.76rem; letter-spacing:.17em; font-weight:800; color:#82E3E8; text-transform:uppercase; }
    .hero h1 {font-family:'Space Grotesk', sans-serif; font-size:2.65rem; margin:.25rem 0 .2rem; letter-spacing:-.055em; color:#F5F8FF; }
    .hero p {color:#B6C5E0; font-size:1.04rem; max-width:920px; margin-bottom:0; }
    .section {font-size:1.25rem; font-weight:800; margin:22px 0 13px; font-family:'Space Grotesk',sans-serif; }
    .captionline {color:#8C9DB9; font-size:.82rem; margin:4px 0 14px; }
    .tag {display:inline-block; background:#24364D; color:#A9E9EE; padding:5px 11px;
          border-radius:20px; font-weight:700; font-size:.76rem; margin-right:6px; }
    .callout {padding:17px 21px; border:1px solid #30445C; border-radius:13px;
        background:#121E30; color:#B8C6DF; line-height:1.65; margin:12px 0 21px; }
    .smallsource {font-size:.75rem; color:#8B9AB5; }
    .insight {min-height:155px; background:linear-gradient(145deg,#142237,#111A2C);
       border:1px solid #2B4561; border-top:3px solid #68D9E4; border-radius:15px;
       padding:20px 22px; margin-bottom:8px;}
    .insight-label {color:#8EADC1; font-size:.70rem; font-weight:800; letter-spacing:.10em;}
    .insight-value {font-family:'Space Grotesk',sans-serif; color:#F0F8FF;
       font-size:2rem; font-weight:700; line-height:1.25; margin:11px 0 5px;}
    .insight p {color:#B1C1D8; font-size:.84rem; margin:0;}
    [data-testid="stTabs"] [role="tablist"] {border-bottom:1px solid #2B3D57; gap:.35rem;}
    [data-testid="stTabs"] button[aria-selected="true"] {color:#79E1E9;}
    h1,h2,h3 {font-family:'Space Grotesk', sans-serif; }
    a {color:#6FD9E2!important;}
    </style>''', unsafe_allow_html=True)


def hero():
    st.markdown('''<div class="hero">
      <div class="eyebrow">HEXAROUTE / DATA INTELLIGENCE · FRANCE</div>
      <h1>Les routes, en données.</h1>
      <p>Observatoire interactif des accidents corporels de la circulation, construit à partir des
      données ouvertes du ministère de l’Intérieur et de l’ONISR. Analyse géographique,
      temporelle et des usagers, sans données simulées.</p>
      <div style="margin-top:16px"><span class="tag">Données officielles</span>
      <span class="tag">BAAC 2023–2025</span><span class="tag">DuckDB-ready / Snowflake</span></div>
    </div>''', unsafe_allow_html=True)


def section(text: str, caption: str | None = None):
    st.markdown(f'<div class="section">{text}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="captionline">{caption}</div>', unsafe_allow_html=True)

# Note : styles de synthèse ajoutés dans apply_style ci-dessus.
