import pandas as pd
import streamlit as st

from lib import dados
from lib import estilo as E

st.title("Turismo em Petrópolis")
st.caption("Panorama anual dos principais indicadores do turismo no município, 2015–2025.")

anc = dados.ancoras_anual()
oc = dados.ocupacao_anual()
ci = dados.cits()
dq = dados.disque_anual().groupby("ano", as_index=False)["atendimentos"].sum()
cap = dados.capacidade_tipo().groupby("ano", as_index=False)[["mhs", "uhs", "leitos"]].sum()
atr = dados.atrativos_anual()
anos = sorted(set(anc["ano"]) | set(oc["ano"]) | set(ci["ano"]))

# ------------------------------------------------------------ filtro (uma linha)
f1, _ = st.columns([1, 3])
ano = f1.selectbox("Ano de referência", anos[::-1], index=0)


def valor(df: pd.DataFrame, col: str, a: int):
    s = df.loc[df["ano"] == a, col]
    return s.iloc[0] if len(s) else None


ant = ano - 1

# ------------------------------------------------------------------ indicadores
linha1 = st.columns(3)
linha2 = st.columns(3)

v, va = valor(anc, "visitantes", ano), valor(anc, "visitantes", ant)
linha1[0].metric(
    "Visitantes nos 6 atrativos-âncora", E.fmt_int(v), E.delta_pct(v, va), border=True,
    help="Soma dos atrativos presentes em todos os relatórios: " + ", ".join(dados.ANCORAS) + ".",
)
v, va = valor(oc, "taxa_media_pct", ano), valor(oc, "taxa_media_pct", ant)
linha1[1].metric("Ocupação hoteleira média", E.fmt_pct(v), E.delta_pp(v, va), border=True,
                 help="Média das 12 taxas mensais de ocupação (todos os distritos).")
v, va = valor(ci, "total", ano), valor(ci, "total", ant)
linha1[2].metric("Turistas atendidos nos CITs", E.fmt_int(v), E.delta_pct(v, va), border=True,
                 help="Turistas atendidos nos Centros de Informações Turísticas (nacionais + internacionais).")

v, va = valor(ci, "pct_internacionais", ano), valor(ci, "pct_internacionais", ant)
linha2[0].metric("Estrangeiros entre os atendidos nos CITs", E.fmt_pct(v), E.delta_pp(v, va),
                 delta_color="off", border=True)
v, va = valor(dq, "atendimentos", ano), valor(dq, "atendimentos", ant)
linha2[1].metric("Atendimentos do Disque Turismo", E.fmt_int(v), E.delta_pct(v, va), delta_color="off",
                 border=True, help="Telefone (0800) + WhatsApp (a partir de 2021).")
ano_cap = max([a for a in cap["ano"] if a <= ano], default=None)
v = valor(cap, "leitos", ano_cap) if ano_cap else None
va = valor(cap, "leitos", ano_cap - 1) if ano_cap else None
rot = "Leitos na rede de hospedagem" + ("" if ano_cap == ano else f" ({ano_cap})")
linha2[2].metric(rot, E.fmt_int(v), E.delta_pct(v, va), border=True,
                 help=None if ano_cap == ano else f"O relatório de {ano} não traz a capacidade hoteleira; "
                                                   f"exibindo o último ano disponível ({ano_cap}).")

base19 = valor(anc, "visitantes", 2019)
atual = valor(anc, "visitantes", ano)
if base19 and atual and ano > 2019:
    E.nota(f"Em {ano}, a visitação nos atrativos-âncora correspondeu a <b>{E.fmt_dec(100 * atual / base19, 0)}%</b> "
           f"do nível de 2019, último ano antes da pandemia.")

st.write("")

# ------------------------------------------------------------------- gráficos
c1, c2 = st.columns(2, gap="large")
with c1:
    E.titulo_grafico("Visitação nos 6 atrativos-âncora", "Visitantes por ano")
    fig = E.grafico_linhas(anc, "ano", "visitantes", None, E.DESTAQUE, pandemia=True, altura=320,
                           nome_serie="Visitantes")
    E.destacar_ponto(fig, ano, valor(anc, "visitantes", ano), E.fmt_int(valor(anc, "visitantes", ano)))
    E.mostrar(fig, "pan_anc")
    E.tabela(anc, "visitacao_atrativos_ancora.csv")
with c2:
    E.titulo_grafico("Ocupação hoteleira", "Taxa média anual (%)")
    fig = E.grafico_linhas(oc, "ano", "taxa_media_pct", None, E.DESTAQUE, fmt_y=",.0f", fmt_hover=",.1f",
                           sufixo="%", pandemia=True, altura=320, nome_serie="Ocupação média")
    E.destacar_ponto(fig, ano, valor(oc, "taxa_media_pct", ano), E.fmt_pct(valor(oc, "taxa_media_pct", ano)))
    E.mostrar(fig, "pan_oc")
    E.tabela(oc, "ocupacao_media_anual.csv")

c3, c4 = st.columns(2, gap="large")
with c3:
    E.titulo_grafico("Turistas atendidos nos CITs", "Nacionais e internacionais por ano")
    longo = ci.melt(id_vars="ano", value_vars=["nacionais", "internacionais"], var_name="origem", value_name="turistas")
    longo["origem"] = longo["origem"].map({"nacionais": "Nacionais", "internacionais": "Internacionais"})
    cores = {"Nacionais": E.CATEGORICA[0], "Internacionais": E.CATEGORICA[1]}
    fig = E.grafico_barras_empilhadas(longo, "ano", "turistas", "origem", cores, pandemia=True, altura=320,
                                      ordem=["Nacionais", "Internacionais"])
    E.mostrar(fig, "pan_cits")
    E.tabela(ci.drop(columns=["fonte_pagina", "fonte_tabela"]), "cits_nacionais_internacionais.csv")
with c4:
    E.titulo_grafico(f"Atrativos mais visitados em {ano}", "Dez maiores; inclui apenas a sede Petrópolis do PARNASO")
    top = atr[(atr["ano"] == ano) & ~atr["atrativo"].isin(dados.FORA_DO_MUNICIPIO)].nlargest(10, "visitantes").copy()
    if top.empty:
        st.info(f"Sem dados de visitação por atrativo para {ano}.")
    else:
        top["nome"] = top["atrativo"].map(E.curto)
        top["obs"] = top["origem_valor"].map(lambda o: f"Fonte do valor: {o}")
        fig = E.grafico_barras_h(top, "nome", "visitantes", altura=320, hover_extra="obs")
        E.mostrar(fig, "pan_top")
        E.tabela(top[["atrativo", "categoria", "visitantes", "origem_valor"]], f"atrativos_top10_{ano}.csv")
