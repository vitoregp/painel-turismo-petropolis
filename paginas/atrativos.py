import pandas as pd
import streamlit as st

from lib import dados
from lib import estilo as E

st.title("Atrativos turísticos")
st.caption("Visitação anual e mensal dos atrativos monitorados nos relatórios, 2015–2025.")

anual = dados.atrativos_anual()
mensal = dados.atrativos_mensal()
anos = sorted(anual["ano"].unique())

# ------------------------------------------------------------ filtros (uma linha)
f1, f2, f3, f4, f5 = st.columns([1.7, 1.5, 3.4, 2.3, 1.5])
periodo = f1.select_slider("Período", options=anos, value=(anos[0], anos[-1]))
categoria = f2.selectbox("Categoria", ["Todas"] + dados.CATEGORIAS)

base = anual if categoria == "Todas" else anual[anual["categoria"] == categoria]
no_periodo = base[base["ano"].between(*periodo)]
# opções fixas por categoria (não dependem do período, para a seleção não ser reiniciada)
ordem = (base[base["atrativo"] != "PARNASO – total das 3 sedes"]
         .groupby("atrativo")["visitantes"].sum().sort_values(ascending=False).index.tolist())
if "PARNASO – total das 3 sedes" in base["atrativo"].values:
    ordem.append("PARNASO – total das 3 sedes")
padrao = [a for a in ordem if a not in dados.FORA_DO_MUNICIPIO][:4]
selecionados = f3.multiselect(
    "Atrativos (até 8)", ordem, default=padrao, max_selections=8, format_func=E.curto,
    key=f"atr_sel_{categoria}",
)
escala = f4.segmented_control("Escala", ["Linear", "Log", "Índice 2019 = 100"], default="Linear") or "Linear"
incluir_nc = f5.toggle("Incluir não conferidos", value=True,
                       help="Valores lidos por OCR cuja soma não bateu com o total do relatório.")

if not selecionados:
    st.info("Escolha ao menos um atrativo no filtro acima.")
    st.stop()

cores = E.cores_estaveis("atrativos", selecionados)
sel = no_periodo[no_periodo["atrativo"].isin(selecionados)].copy()
if not incluir_nc:
    sel = sel[sel["confere"] != "não"]
sel["nome"] = sel["atrativo"].map(E.curto)
sel["detalhe"] = [
    f"{o}" + (f" · {int(m)} meses com dado" if pd.notna(m) and o == "soma dos meses" else "")
    + (" · OCR não conferido" if c == "não" else "")
    for o, m, c in zip(sel["origem_valor"], sel["meses_com_dado"], sel["confere"])
]
cores_nome = {E.curto(k): v for k, v in cores.items()}

aba1, aba2, aba3, aba4 = st.tabs(["Evolução anual", "Sazonalidade", f"Ranking de {periodo[1]}", "Dados"])

# ----------------------------------------------------------------- evolução
with aba1:
    serie = sel.copy()
    titulo_y, fmt, log = "Visitantes", ",.0f", False
    if escala.startswith("Índice"):
        b19 = anual[anual["ano"] == 2019].set_index("atrativo")["visitantes"]
        sem_base = [E.curto(a) for a in selecionados if a not in b19.index]
        serie = serie[serie["atrativo"].isin(b19.index)]
        serie["visitantes"] = 100 * serie["visitantes"] / serie["atrativo"].map(b19)
        titulo_y, fmt = "Índice (2019 = 100)", ",.0f"
        if sem_base:
            E.nota("Sem dado de 2019 (fora do índice): " + ", ".join(sem_base) + ".")
    elif escala == "Log":
        log = True
    E.titulo_grafico("Visitantes por ano", "Marcador vazado = ano com meses faltando ou valor de OCR não conferido")
    fig = E.grafico_linhas(serie, "ano", "visitantes", "nome", cores_nome, fmt_y=fmt, titulo_y=titulo_y,
                           pandemia=periodo[0] <= 2020 <= periodo[1], log=log, altura=430, aberto="parcial",
                           hover_extra="detalhe")
    if escala.startswith("Índice"):
        fig.add_hline(y=100, line_width=1, line_color=E.TINTA_FRACA)
    E.mostrar(fig, "atr_evol")
    larga = serie.pivot_table(index="ano", columns="nome", values="visitantes").round(1).reset_index()
    larga.columns.name = None
    E.tabela(larga, "atrativos_evolucao_anual.csv")

# ------------------------------------------------------------- sazonalidade
with aba2:
    m = mensal[mensal["atrativo"].isin(selecionados) & mensal["ano"].between(*periodo)].copy()
    if not incluir_nc:
        m = m[m["ocr_confere"] != "não"]
    completos = m.dropna(subset=["visitantes"]).groupby(["atrativo", "ano"])["mes_num"].transform("count") == 12
    m_ok = m.dropna(subset=["visitantes"])[completos]
    m_ok = m_ok[~m_ok["ano"].isin([2020, 2021])]
    if m_ok.empty:
        st.info("Não há anos completos (12 meses) para os atrativos e o período escolhidos. "
                "O relatório de 2025 traz apenas totais anuais.")
    else:
        m_ok["pct"] = 100 * m_ok["visitantes"] / m_ok.groupby(["atrativo", "ano"])["visitantes"].transform("sum")
        perfil = m_ok.groupby(["atrativo", "mes_num"], as_index=False)["pct"].mean()
        perfil["mes"] = perfil["mes_num"].map(lambda n: E.MESES[n - 1])
        perfil["nome"] = perfil["atrativo"].map(E.curto)
        E.titulo_grafico("Distribuição da visitação ao longo do ano",
                         "Média da participação de cada mês no total anual (%) — anos completos, sem 2020–2021")
        fig = E.grafico_linhas(perfil, "mes", "pct", "nome", cores_nome, fmt_y=",.0f", fmt_hover=",.1f",
                               sufixo="%", anual=False, altura=380, ordem_x=E.MESES)
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=E.MESES)
        E.mostrar(fig, "atr_saz")
        t = perfil.pivot_table(index="mes_num", columns="nome", values="pct").round(2).reset_index()
        t.insert(1, "mes", t["mes_num"].map(lambda n: E.MESES[n - 1]))
        t.columns.name = None
        E.tabela(t, "atrativos_sazonalidade.csv")

    st.write("")
    c1, _ = st.columns([2, 3])
    alvo = c1.selectbox("Mapa de calor do atrativo", selecionados, format_func=E.curto, key="atr_calor")
    mm = m[m["atrativo"] == alvo]
    if mm["visitantes"].notna().any():
        mat = mm.pivot_table(index="ano", columns="mes_num", values="visitantes").reindex(columns=range(1, 13))
        mat.columns = E.MESES
        E.titulo_grafico(f"{E.curto(alvo)}: visitantes por mês", "Células vazias = mês sem dado")
        E.mostrar(E.mapa_calor(mat, titulo_escala="visitantes"), "atr_calor_fig")
        E.tabela(mat.reset_index(), f"mensal_{E.curto(alvo)}.csv".replace(" ", "_"))
    else:
        st.info("Sem dados mensais para este atrativo no período.")

# ------------------------------------------------------------------ ranking
with aba3:
    ano_r = periodo[1]
    r = base[(base["ano"] == ano_r) & (base["atrativo"] != "PARNASO – total das 3 sedes")].copy()
    if not incluir_nc:
        r = r[r["confere"] != "não"]
    if r.empty:
        st.info(f"Sem dados para {ano_r}.")
    else:
        r["nome"] = r["atrativo"].map(E.curto)
        r["detalhe"] = r["origem_valor"]
        c1, c2 = st.columns(2, gap="large")
        with c1:
            E.titulo_grafico(f"Visitantes em {ano_r}", "Categoria: " + categoria.lower())
            E.mostrar(E.grafico_barras_h(r, "nome", "visitantes", hover_extra="detalhe"), "atr_rank")
        with c2:
            ant = base[(base["ano"] == ano_r - 1)].set_index("atrativo")["visitantes"]
            r["variacao"] = 100 * (r["visitantes"] / r["atrativo"].map(ant) - 1)
            v = r.dropna(subset=["variacao"])
            E.titulo_grafico(f"Variação {ano_r - 1} → {ano_r}", "Azul = alta · vermelho = queda")
            if v.empty:
                st.info(f"Sem dados de {ano_r - 1} para comparar.")
            else:
                E.mostrar(E.grafico_variacao(v, "nome", "variacao", altura=max(220, 30 * len(r) + 60)), "atr_var")
        E.tabela(r[["atrativo", "categoria", "visitantes", "variacao", "origem_valor", "confere"]]
                 .sort_values("visitantes", ascending=False), f"ranking_atrativos_{ano_r}.csv")
        E.nota("O total das 3 sedes do PARNASO fica fora do ranking para não contar a visitação em dobro; "
               "as sedes Teresópolis e Guapimirim ficam fora do município, mas aparecem nos relatórios.")

# -------------------------------------------------------------------- dados
with aba4:
    st.markdown("**Visitação anual** (atrativos e período filtrados)")
    E.tabela(sel.drop(columns=["nome", "detalhe", "parcial", "ancora"]), "atrativos_anual_filtrado.csv",
             rotulo="Tabela anual", aberto=True, chave="dl_anual")
    st.markdown("**Visitação mensal**")
    mm = mensal[mensal["atrativo"].isin(selecionados) & mensal["ano"].between(*periodo)]
    E.tabela(mm, "atrativos_mensal_filtrado.csv", rotulo="Tabela mensal", chave="dl_mensal")
