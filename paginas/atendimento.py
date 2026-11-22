import streamlit as st

from lib import dados
from lib import estilo as E

st.title("Atendimento ao turista")
st.caption("Disque Turismo, passaporte da Estrada Real e turismo pedagógico nos museus.")

dqa = dados.disque_anual()
dqm = dados.disque_mensal()
er = dados.estrada_real()
ped = dados.pedagogico()

aba1, aba2, aba3 = st.tabs(["Disque Turismo", "Estrada Real", "Turismo pedagógico"])
CORES_CANAL = {"Telefone (0800)": E.CATEGORICA[0], "WhatsApp": E.CATEGORICA[2]}

# ----------------------------------------------------------------- disque
with aba1:
    f1, _ = st.columns([1.2, 6.8])
    anos_m = sorted(dqm["ano"].unique())
    ano = f1.selectbox("Ano (gráfico mensal)", anos_m[::-1], key="dq_ano")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        E.titulo_grafico("Atendimentos por ano", "Telefone (0800) e WhatsApp (a partir de 2021)")
        E.mostrar(E.grafico_barras_empilhadas(dqa, "ano", "atendimentos", "canal", CORES_CANAL, pandemia=True,
                                              ordem=dados.CANAIS), "dq_anual")
    with c2:
        E.titulo_grafico(f"Atendimentos por mês em {ano}", "Por canal")
        d = dqm[dqm["ano"] == ano]
        fig = E.grafico_linhas(d, "mes", "atendimentos", "canal", CORES_CANAL, anual=False, ordem_x=E.MESES)
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=E.MESES)
        E.mostrar(fig, "dq_mensal")
    E.tabela(dqa, "disque_turismo_anual.csv")
    E.tabela(dqm.drop(columns=["fonte_relatorio"]), "disque_turismo_mensal.csv", rotulo="Ver dados mensais",
             chave="dl_dq_m")

# ------------------------------------------------------------ estrada real
with aba2:
    f1, _ = st.columns([1.2, 6.8])
    anos_e = sorted(er["ano"].unique())
    ano_e = f1.selectbox("Ano", anos_e[::-1], key="er_ano")
    tot = er[er["indicador"] == "Total de viajantes"].groupby("ano", as_index=False)["quantidade"].sum()
    k = st.columns(3)
    atual = tot.loc[tot["ano"] == ano_e, "quantidade"]
    ant = tot.loc[tot["ano"] == ano_e - 1, "quantidade"]
    k[0].metric("Viajantes atendidos", E.fmt_int(atual.iloc[0]) if len(atual) else "—",
                E.delta_pct(atual.iloc[0], ant.iloc[0]) if len(atual) and len(ant) else None, border=True)
    for i, ind in enumerate(["Passaporte emitido", "Carimbo no passaporte"], start=1):
        v = er[(er["ano"] == ano_e) & (er["indicador"] == ind)]["quantidade"].sum()
        k[i].metric(ind, E.fmt_int(v), border=True)

    E.titulo_grafico(f"Passaportes da Estrada Real por mês em {ano_e}", "Emitidos e carimbados no posto de Petrópolis")
    d = er[(er["ano"] == ano_e) & (er["indicador"] != "Total de viajantes")]
    cores = {"Passaporte emitido": E.CATEGORICA[0], "Carimbo no passaporte": E.CATEGORICA[1]}
    fig = E.grafico_barras_empilhadas(d, "mes", "quantidade", "indicador", cores, anual=False,
                                      ordem=["Passaporte emitido", "Carimbo no passaporte"], ordem_x=E.MESES)
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=E.MESES)
    E.mostrar(fig, "er_mensal")
    E.tabela(er.drop(columns=["fonte_relatorio"]), "estrada_real_mensal.csv")

# -------------------------------------------------------------- pedagógico
with aba3:
    anos_p = sorted(ped.dropna(subset=["visitacao_escolar"])["ano"].unique())
    f1, _ = st.columns([1.2, 6.8])
    ano_p = f1.selectbox("Ano (ranking)", anos_p[::-1], key="ped_ano")
    museus = ped.groupby("atrativo")["pct_escolar"].count().sort_values(ascending=False).index.tolist()
    cores = E.cores_fixas(museus)
    nomes = {m: E.curto(m) for m in museus}

    c1, c2 = st.columns([1.2, 1], gap="large")
    with c1:
        E.titulo_grafico("Participação de estudantes na visitação", "% da visitação total que veio de escolas")
        d = ped.dropna(subset=["pct_escolar"]).copy()
        d["nome"] = d["atrativo"].map(nomes)
        fig = E.grafico_linhas(d, "ano", "pct_escolar", "nome", {nomes[k]: v for k, v in cores.items()},
                               fmt_y=",.0f", fmt_hover=",.1f", sufixo="%", pandemia=True, altura=400)
        E.mostrar(fig, "ped_pct")
    with c2:
        d = ped[(ped["ano"] == ano_p)].dropna(subset=["visitacao_escolar"]).copy()
        d["nome"] = d["atrativo"].map(nomes)
        d["detalhe"] = d["pct_escolar"].map(lambda p: f"{E.fmt_pct(p)} da visitação do museu")
        E.titulo_grafico(f"Estudantes recebidos em {ano_p}", "Visitação escolar por museu")
        E.mostrar(E.grafico_barras_h(d, "nome", "visitacao_escolar", hover_extra="detalhe", altura=400), "ped_rank")
    E.nota("2015–2016: os relatórios trazem apenas o percentual de visitação escolar. "
           "2020–2021: escolas sem visitas presenciais durante boa parte do ano.")
    E.tabela(ped.drop(columns=["fonte_relatorio"]), "turismo_pedagogico.csv")
