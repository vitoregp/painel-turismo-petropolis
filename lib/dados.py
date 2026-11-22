"""Leitura (com cache) dos CSVs preparados por scripts/preparar_dados.py."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

PASTA = Path(__file__).resolve().parents[1] / "data"

ANCORAS = [
    "Museu Imperial", "Museu Casa de Santos Dumont", "Centro de Experiência Cervejeira Bohemia",
    "Museu Casa do Colono", "Centro Cultural Estação Nogueira", "Casa Stefan Zweig",
]
# Sedes do PARNASO fora de Petrópolis e o total das três sedes não entram nos agregados do município.
FORA_DO_MUNICIPIO = {"PARNASO – sede Teresópolis", "PARNASO – sede Guapimirim", "PARNASO – total das 3 sedes"}
CATEGORIAS = ["Histórico-cultural", "Natural", "Entretenimento cultural"]
TIPOS_HOSPEDAGEM = ["Hotel", "Pousada", "Hostel", "Resort", "Spa", "Flat", "Cama & café"]
CANAIS = ["Telefone (0800)", "WhatsApp"]


@st.cache_data(show_spinner=False)
def ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(PASTA / f"{nome}.csv")


def atrativos_anual() -> pd.DataFrame:
    d = ler("atrativos_anual").copy()
    d["parcial"] = (d["confere"] == "não") | (d["meses_com_dado"].notna() & (d["meses_com_dado"] < 12)
                                              & (d["origem_valor"] == "soma dos meses"))
    return d


def atrativos_mensal() -> pd.DataFrame:
    return ler("atrativos_mensal")


def ocupacao() -> pd.DataFrame:
    return ler("ocupacao_mensal")


def ocupacao_anual() -> pd.DataFrame:
    o = ocupacao()
    return (o.groupby("ano", as_index=False)[["taxa_media_pct", "distrito_1_pct", "distritos_2a5_pct"]]
            .mean().round(2))


def cits() -> pd.DataFrame:
    return ler("cits_origem_anual")


def estados() -> pd.DataFrame:
    return ler("procedencia_estados")


def paises() -> pd.DataFrame:
    return ler("procedencia_paises")


def capacidade_tipo() -> pd.DataFrame:
    return ler("capacidade_tipo")


def capacidade_regiao() -> pd.DataFrame:
    return ler("capacidade_regiao")


def disque_mensal() -> pd.DataFrame:
    return ler("disque_turismo_mensal")


def disque_anual() -> pd.DataFrame:
    return ler("disque_turismo_anual")


def estrada_real() -> pd.DataFrame:
    return ler("estrada_real_mensal")


def pedagogico() -> pd.DataFrame:
    return ler("turismo_pedagogico")


def ancoras_anual() -> pd.DataFrame:
    """Soma anual dos 6 atrativos presentes em todos os relatórios (base comparável)."""
    a = atrativos_anual()
    a = a[a["atrativo"].isin(ANCORAS)]
    g = a.groupby("ano").agg(visitantes=("visitantes", "sum"), n=("atrativo", "nunique")).reset_index()
    return g[g["n"] == len(ANCORAS)].drop(columns="n")


@st.cache_data(show_spinner=False)
def zip_todos() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PASTA.glob("*.csv")):
            z.write(f, f.name)
    return buf.getvalue()


DICIONARIO = [
    ("atrativos_mensal", "Visitantes por atrativo e mês (2015–2024).",
     "ano, mes_num, mes, atrativo, categoria, visitantes, ocr_confere, fonte_*"),
    ("atrativos_anual", "Visitantes por atrativo e ano (2015–2025): total publicado ou soma dos meses.",
     "ano, atrativo, categoria, ancora, visitantes, origem_valor, confere, meses_com_dado, fonte_*"),
    ("ocupacao_mensal", "Taxa de ocupação hoteleira mensal (%), geral e por distrito (2015–2025).",
     "ano, mes_num, mes, distrito_1_pct, distritos_2a5_pct, taxa_media_pct, fonte_*"),
    ("capacidade_tipo", "Meios de hospedagem (MHs), unidades habitacionais (UHs) e leitos por tipo (2015–2024).",
     "ano, tipo, mhs, pct_mhs, uhs, pct_uhs, leitos, pct_leitos, fonte_*"),
    ("capacidade_regiao", "Capacidade por região do município (2015–2024).",
     "ano, regiao, mhs, uhs, leitos (+ %), divisao_regional, fonte_*"),
    ("cits_origem_anual", "Turistas atendidos nos CITs: nacionais × internacionais (2015–2025).",
     "ano, nacionais, internacionais, total, pct_internacionais, fonte_*"),
    ("procedencia_estados", "Turistas brasileiros atendidos nos CITs por estado de origem (2015–2023).",
     "ano, uf, sigla, turistas, pct, cobertura, fonte_*"),
    ("procedencia_paises", "Turistas estrangeiros atendidos nos CITs por país (2015–2024).",
     "ano, pais, turistas, pct, cobertura, fonte_*"),
    ("disque_turismo_mensal", "Atendimentos do Disque Turismo por canal e mês (2017–2024).",
     "ano, mes_num, mes, canal, atendimentos, fonte_*"),
    ("disque_turismo_anual", "Atendimentos do Disque Turismo por canal e ano (2015–2025).",
     "ano, canal, atendimentos, origem_valor"),
    ("estrada_real_mensal", "Passaportes da Estrada Real emitidos/carimbados em Petrópolis (2021–2024).",
     "ano, mes_num, mes, indicador, quantidade, fonte_*"),
    ("turismo_pedagogico", "Visitação escolar nos museus (2015–2025; 2015–2016 só o percentual).",
     "ano, atrativo, visitacao_total, visitacao_escolar, visitacao_nao_escolar, pct_escolar, fonte_*"),
]
