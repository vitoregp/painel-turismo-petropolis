"""Painel do Turismo de Petrópolis - Projeto de Extensão (UCP).

Para rodar: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Turismo em Petrópolis",
    page_icon=":material/landscape:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from lib import estilo  # noqa: E402 - importado depois do set_page_config

estilo.css()

paginas = {
    "Indicadores": [
        st.Page("paginas/panorama.py", title="Panorama", icon=":material/dashboard:", default=True),
        st.Page("paginas/atrativos.py", title="Atrativos turísticos", icon=":material/museum:"),
        st.Page("paginas/hospedagem.py", title="Hospedagem", icon=":material/hotel:"),
        st.Page("paginas/procedencia.py", title="Procedência dos turistas", icon=":material/travel_explore:"),
        st.Page("paginas/atendimento.py", title="Atendimento ao turista", icon=":material/support_agent:"),
    ],
    "Projeto": [
        st.Page("paginas/sobre.py", title="Sobre os dados", icon=":material/info:"),
    ],
}

pg = st.navigation(paginas)

with st.sidebar:
    st.caption(
        "Dados extraídos dos relatórios anuais **Desempenho do Turismo de Petrópolis** "
        "(2015–2025). Projeto de Extensão — UCP."
    )

pg.run()
