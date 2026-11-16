"""Adaptateur pour HTML+JS local : st.iframe récent ou composant historique."""
from __future__ import annotations

import streamlit as st


def render_html_frame(html: str, height: int) -> None:
    # Les versions récentes de Streamlit utilisent st.iframe pour le JS isolé.
    # Fallback pour les versions 1.36–1.55 encore possibles avec requirements.
    if hasattr(st, 'iframe'):
        st.iframe(html, width='stretch', height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height, scrolling=False)
