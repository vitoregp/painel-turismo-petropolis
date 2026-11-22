import streamlit as st

from lib import dados
from lib import estilo as E

st.title("Procedência dos turistas")
st.caption("Turistas atendidos nos Centros de Informações Turísticas (CITs), por origem.")

ci = dados.cits()
est = dados.estados()
pai = dados.paises()

aba1, aba2, aba3 = st.tabs(["Nacionais × internacionais", "Estados de origem", "Países de origem"])

# Nacionais x internacionais
with aba1:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        E.titulo_grafico("Turistas atendidos nos CITs", "Por ano e origem")
        longo = ci.melt(id_vars="ano", value_vars=["nacionais", "internacionais"], var_name="origem",
                        value_name="turistas")
        longo["origem"] = longo["origem"].map({"nacionais": "Nacionais", "internacionais": "Internacionais"})
        cores = {"Nacionais": E.CATEGORICA[0], "Internacionais": E.CATEGORICA[1]}
        E.mostrar(E.grafico_barras_empilhadas(longo, "ano", "turistas", "origem", cores, pandemia=True,
                                              ordem=["Nacionais", "Internacionais"]), "proc_nacint")
    with c2:
        E.titulo_grafico("Participação de estrangeiros", "% dos turistas atendidos nos CITs")
        fig = E.grafico_linhas(ci, "ano", "pct_internacionais", None, E.CATEGORICA[1], fmt_y=",.0f",
                               fmt_hover=",.1f", sufixo="%", pandemia=True, nome_serie="Internacionais")
        ult = ci.iloc[-1]
        E.destacar_ponto(fig, ult["ano"], ult["pct_internacionais"], E.fmt_pct(ult["pct_internacionais"]),
                         cor=E.CATEGORICA[1])
        E.mostrar(fig, "proc_pctint")
    E.nota("Os números refletem quem procurou os CITs, não o total de turistas da cidade. Em 2020–2022 os postos "
           "funcionaram com restrições, o que explica a queda acentuada.")
    E.tabela(ci.drop(columns=["fonte_pagina", "fonte_tabela"]), "cits_origem_anual.csv")


def bloco_origem(df, coluna, rotulo, anos, padrao_evolucao, chave, excluir_rotulo=None, excluir_valor=None):
    """Ranking do ano e evolução da participação de cada origem."""
    f1, f2, f3, f4 = st.columns([1.2, 1.6, 3.6, 1.8])
    ano = f1.selectbox("Ano", anos[::-1], key=f"{chave}_ano")
    top_n = f2.slider("Quantos no ranking", 5, 15, 10, key=f"{chave}_n")
    opcoes = df.groupby(coluna)["turistas"].sum().sort_values(ascending=False).index.tolist()
    sel = f3.multiselect(f"{rotulo} na evolução (até 8)", opcoes,
                         default=[p for p in padrao_evolucao if p in opcoes], max_selections=8, key=f"{chave}_sel")
    excluir = f4.toggle(excluir_rotulo, value=False, key=f"{chave}_excl") if excluir_rotulo else False

    d = df[df["ano"] == ano]
    if excluir:
        d = d[d[coluna] != excluir_valor]
    d = d[d[coluna] != "Não informado"].nlargest(top_n, "turistas").copy()
    parcial = (d["cobertura"] == "10 principais").any()
    d["detalhe"] = d["pct"].map(lambda p: f"{E.fmt_pct(p, 2)} do total")

    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        E.titulo_grafico(f"{rotulo} com mais turistas em {ano}",
                         "O relatório deste ano lista só os 10 principais" if parcial else "Turistas atendidos nos CITs")
        E.mostrar(E.grafico_barras_h(d, coluna, "turistas", hover_extra="detalhe", altura=max(260, 30 * len(d) + 60)),
                  f"{chave}_rank")
    with c2:
        E.titulo_grafico("Evolução da participação", "% dos turistas da mesma origem (nacionais ou estrangeiros)")
        if sel:
            ev = df[df[coluna].isin(sel)]
            cores = E.cores_estaveis(chave, sel)
            fig = E.grafico_linhas(ev, "ano", "pct", coluna, cores, fmt_y=",.0f", fmt_hover=",.1f", sufixo="%",
                                   pandemia=True, altura=max(260, 30 * len(d) + 60))
            E.mostrar(fig, f"{chave}_evol")
        else:
            st.info("Escolha ao menos um item para ver a evolução.")
    E.tabela(df[df["ano"] == ano].drop(columns=["fonte_relatorio"]), f"procedencia_{chave}_{ano}.csv")
    E.tabela(df.pivot_table(index=coluna, columns="ano", values="turistas").reset_index(),
             f"procedencia_{chave}_serie.csv", rotulo="Ver série completa (turistas por ano)", chave=f"dl_{chave}_serie")


with aba2:
    bloco_origem(est, "uf", "Estados", sorted(est["ano"].unique()),
                 ["São Paulo", "Minas Gerais", "Espírito Santo", "Rio Grande do Sul"], "estados",
                 excluir_rotulo="Sem o Rio de Janeiro", excluir_valor="Rio de Janeiro")
    E.nota("O Rio de Janeiro responde por cerca de dois terços dos turistas brasileiros; retire-o do ranking para "
           "comparar melhor os demais estados. 2015–2016: apenas os 10 principais estados.")

with aba3:
    bloco_origem(pai, "pais", "Países", sorted(pai["ano"].unique()),
                 ["Argentina", "França", "Estados Unidos", "Chile"], "paises")
    E.nota("2015: apenas os 10 principais países. O relatório de 2025 não detalha os países de origem.")
