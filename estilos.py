import streamlit as st

_CSS_GLOBAL = """
<style>
.main {
    background-color: #111;
}

.stMetric {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #c00000;
}
div[data-testid="stMetricValue"] {
    color: #f0f0f0;
}

/* Barra lateral sempre visível */
[data-testid="sidebar-button"]                        { display: none !important; }
[data-testid="stSidebar"][aria-expanded="false"]      { margin-left: 0 !important; display: block !important; }
[data-testid="stSidebarResizerProxy"]                 { display: none !important; }
</style>
"""


def aplicar_estilos() -> None:
    st.markdown(_CSS_GLOBAL, unsafe_allow_html=True)
