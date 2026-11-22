import streamlit as st

from lib import dados
from lib import estilo as E

st.title("Hospedagem")
st.caption("Taxa de ocupação hoteleira (2015–2025) e capacidade da rede de hospedagem (2015–2024).")

oc = dados.ocupacao()
oc_anual = dados.ocupacao_anual()
tipo = dados.capacidade_tipo()
reg = dados.capacidade_regiao()

aba1, aba2 = st.tabs(["Ocupação hoteleira", "Capacidade da rede"])

RECORTES = {"Média geral": "taxa_media_pct", "1º distrito": "distrito_1_pct", "2º ao 5º distrito": "distritos_2a5_pct"}

# Ocupação
with aba1:
    anos_oc = sorted(oc["ano"].unique())
    f1, f2, _ = st.columns([4, 2.4, 1.6])
    anos_sel = f1.multiselect("Anos comparados (até 8)", anos_oc, default=[2019, 2023, 2024, 2025],
                              max_selections=8, key="oc_anos")
    recorte = f2.segmented_control("Recorte", list(RECORTES), default="Média geral", key="oc_recorte") or "Média geral"
    col = RECORTES[recorte]

    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        E.titulo_grafico("Taxa de ocupação mês a mês", f"{recorte} (%) nos anos escolhidos")
        if anos_sel:
            d = oc[oc["ano"].isin(anos_sel)].copy()
            d["ano_txt"] = d["ano"].astype(str)
            cores = E.cores_estaveis("oc_anos", [str(a) for a in sorted(anos_sel)])
            fig = E.grafico_linhas(d, "mes", col, "ano_txt", cores, fmt_y=",.0f", fmt_hover=",.1f", sufixo="%",
                                   anual=False, altura=380, ordem_x=E.MESES)
            fig.update_xaxes(type="category", categoryorder="array", categoryarray=E.MESES)
            E.mostrar(fig, "oc_linhas")
        else:
            st.info("Escolha ao menos um ano.")
    with c2:
        E.titulo_grafico("Mapa de calor da ocupação", f"{recorte} (%) — todos os anos")
        mat = oc.pivot_table(index="ano", columns="mes_num", values=col).reindex(columns=range(1, 13))
        mat.columns = E.MESES
        E.mostrar(E.mapa_calor(mat, fmt=",.0f", sufixo="%", titulo_escala="ocupação"), "oc_calor")

    E.tabela(oc.drop(columns=["fonte_relatorio"]), "ocupacao_hoteleira_mensal.csv")

    st.write("")
    E.titulo_grafico("Média anual por área do município", "1º distrito (centro histórico) × 2º ao 5º distrito (%)")
    longo = oc_anual.melt(id_vars="ano", value_vars=["distrito_1_pct", "distritos_2a5_pct"], var_name="area",
                          value_name="taxa")
    longo["area"] = longo["area"].map({"distrito_1_pct": "1º distrito", "distritos_2a5_pct": "2º ao 5º distrito"})
    cores = {"1º distrito": E.CATEGORICA[0], "2º ao 5º distrito": E.CATEGORICA[1]}
    fig = E.grafico_linhas(longo, "ano", "taxa", "area", cores, fmt_y=",.0f", fmt_hover=",.1f", sufixo="%",
                           pandemia=True, altura=340)
    E.mostrar(fig, "oc_distritos")
    E.tabela(oc_anual, "ocupacao_media_anual.csv", chave="dl_oc_anual")

# Capacidade
with aba2:
    MEDIDAS = {"Leitos": "leitos", "Unidades habitacionais (UHs)": "uhs", "Meios de hospedagem (MHs)": "mhs"}
    anos_cap = sorted(tipo["ano"].unique())
    f1, f2, _ = st.columns([3.2, 1.4, 3.4])
    medida = f1.segmented_control("Medida", list(MEDIDAS), default="Leitos", key="cap_medida") or "Leitos"
    ano = f2.selectbox("Ano", anos_cap[::-1], key="cap_ano")
    col = MEDIDAS[medida]

    tot = tipo.groupby("ano", as_index=False)[["mhs", "uhs", "leitos"]].sum()
    atual = tot[tot["ano"] == ano].iloc[0]
    ant = tot[tot["ano"] == ano - 1]
    k = st.columns(3)
    for i, (rot, c) in enumerate([("Meios de hospedagem", "mhs"), ("Unidades habitacionais", "uhs"), ("Leitos", "leitos")]):
        k[i].metric(rot, E.fmt_int(atual[c]), E.delta_pct(atual[c], ant[c].iloc[0]) if len(ant) else None, border=True)

    c1, c2 = st.columns([1.2, 1], gap="large")
    with c1:
        E.titulo_grafico(f"{medida} por tipo de hospedagem", "Evolução anual")
        tipos = [t for t in dados.TIPOS_HOSPEDAGEM if t in tipo["tipo"].unique()]
        cores = E.cores_fixas(dados.TIPOS_HOSPEDAGEM)
        fig = E.grafico_linhas(tipo, "ano", col, "tipo", cores, altura=400, pandemia=True)
        E.mostrar(fig, "cap_tipo")
    with c2:
        r = reg[reg["ano"] == ano].copy()
        E.titulo_grafico(f"{medida} por região em {ano}", r["divisao_regional"].iloc[0] if len(r) else None)
        if len(r):
            E.mostrar(E.grafico_barras_h(r, "regiao", col, altura=400), "cap_regiao")
    E.nota("A divisão regional mudou em 2017 (de 7 para 8 regiões). Compare regiões apenas dentro do mesmo período. "
           "Cama & café passou a ser contabilizado em 2019.")
    E.tabela(tipo.drop(columns=["fonte_relatorio"]), "capacidade_por_tipo.csv", rotulo="Ver dados por tipo",
             chave="dl_cap_tipo")
    E.tabela(reg.drop(columns=["fonte_relatorio"]), "capacidade_por_regiao.csv", rotulo="Ver dados por região",
             chave="dl_cap_reg")
