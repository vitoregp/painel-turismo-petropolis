"""Cores, formatação no padrão brasileiro e funções de gráfico (Plotly) do painel."""
from __future__ import annotations

import io
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Cores e fontes
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
FONTE = '"Source Sans Pro", "Source Sans 3", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

# Paleta de 8 cores em ordem fixa (testada para daltonismo).
CATEGORICA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
# Tons de azul, do claro ao escuro, para os mapas de calor.
SEQUENCIAL = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
              "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
DESTAQUE = CATEGORICA[0]
DIVERGENTE_POS = "#2a78d6"  # alta
DIVERGENTE_NEG = "#e34948"  # queda
NEUTRO = "#c9c7bf"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

CONFIG_PLOTLY = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d", "toggleSpikelines"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

NOME_CURTO = {
    "Museu Casa de Santos Dumont": "Casa de Santos Dumont",
    "Centro de Experiência Cervejeira Bohemia": "Bohemia",
    "Museu Casa do Colono": "Casa do Colono",
    "Centro Cultural Estação Nogueira": "Estação Nogueira",
    "Casa de Petrópolis – Instituto de Cultura": "Casa de Petrópolis",
    "Concertos/Recitais – Casa de Petrópolis": "Concertos/Recitais",
    "Galeria Expositiva Princesa Isabel (Catedral)": "Galeria Princesa Isabel",
    "Igreja de Confissão Luterana": "Igreja Luterana",
    "PARNASO – sede Petrópolis": "PARNASO Petrópolis",
    "PARNASO – sede Teresópolis": "PARNASO Teresópolis",
    "PARNASO – sede Guapimirim": "PARNASO Guapimirim",
    "PARNASO – total das 3 sedes": "PARNASO (3 sedes)",
    "Palácio Amarelo (Câmara Municipal)": "Palácio Amarelo",
    "Parque Natural Municipal Padre Quinha": "Parque Padre Quinha",
}


def curto(nome: str) -> str:
    return NOME_CURTO.get(nome, nome)


# Formatação
def _br(txt: str) -> str:
    return txt.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_int(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v):
        return "—"
    return _br(f"{float(v):,.0f}")


def fmt_dec(v, casas: int = 1) -> str:
    if v is None or pd.isna(v):
        return "—"
    return _br(f"{float(v):,.{casas}f}")


def fmt_pct(v, casas: int = 1) -> str:
    return "—" if v is None or pd.isna(v) else f"{fmt_dec(v, casas)}%"


def delta_pct(atual, anterior) -> str | None:
    """Variação percentual como texto para st.metric (o sinal define a cor)."""
    if atual is None or anterior is None or pd.isna(atual) or pd.isna(anterior) or anterior == 0:
        return None
    v = 100 * (atual / anterior - 1)
    return f"{'+' if v >= 0 else '-'}{fmt_dec(abs(v), 1)}%"


def delta_pp(atual, anterior) -> str | None:
    """Variação em pontos percentuais."""
    if atual is None or anterior is None or pd.isna(atual) or pd.isna(anterior):
        return None
    v = atual - anterior
    return f"{'+' if v >= 0 else '-'}{fmt_dec(abs(v), 1)} p.p."


# CSS
def css() -> None:
    st.markdown(
        """
        <style>
          .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1320px;}
          [data-testid="stMetricValue"] {font-size: 1.85rem; font-weight: 600;}
          [data-testid="stMetricLabel"] p {color: #52514e; font-size: 0.92rem;}
          [data-testid="stCaptionContainer"] {color: #6b6a65;}
          h1 {font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.01em;}
          h3 {font-size: 1.12rem !important; font-weight: 600 !important; margin-bottom: 0 !important;}
          .nota {font-size: 0.86rem; color: #52514e; border-left: 3px solid #e1e0d9; padding: 0.15rem 0 0.15rem 0.7rem; margin: 0.2rem 0 0.8rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def nota(texto: str) -> None:
    st.markdown(f'<div class="nota">{texto}</div>', unsafe_allow_html=True)


def titulo_grafico(titulo: str, subtitulo: str | None = None) -> None:
    st.markdown(f"### {titulo}")
    if subtitulo:
        st.caption(subtitulo)


# Cores estáveis
def cores_estaveis(chave: str, itens: list[str]) -> dict[str, str]:
    """Mantém a mesma cor para cada item enquanto ele estiver selecionado."""
    mapa: dict[str, int] = st.session_state.setdefault(f"_cores_{chave}", {})
    for k in list(mapa):
        if k not in itens:
            del mapa[k]
    livres = [i for i in range(len(CATEGORICA)) if i not in mapa.values()]
    for it in itens:
        if it not in mapa and livres:
            mapa[it] = livres.pop(0)
    return {it: CATEGORICA[mapa[it]] for it in itens if it in mapa}


def cores_fixas(itens: list[str]) -> dict[str, str]:
    return {it: CATEGORICA[i] for i, it in enumerate(itens[: len(CATEGORICA)])}


# Layout base
def layout(fig: go.Figure, altura: int = 360, legenda: bool = True, hover: str = "x unified",
           margem_direita: int = 16) -> go.Figure:
    fig.update_layout(
        height=altura,
        margin=dict(l=8, r=margem_direita, t=36 if legenda else 12, b=8),
        paper_bgcolor=SUPERFICIE,
        plot_bgcolor=SUPERFICIE,
        font=dict(family=FONTE, size=13, color=TINTA_2),
        separators=",.",
        hovermode=hover,
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRADE, font=dict(family=FONTE, size=13, color=TINTA)),
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title=dict(text=""),
                    font=dict(size=12, color=TINTA_2), itemclick="toggle", itemdoubleclick="toggleothers"),
        bargap=0.35,
        barcornerradius=4,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor=GRADE, linewidth=1,
                     ticks="outside", tickcolor=GRADE, ticklen=4, tickfont=dict(color=TINTA_FRACA, size=12),
                     title_font=dict(color=TINTA_2, size=12))
    fig.update_yaxes(showgrid=True, gridcolor=GRADE, gridwidth=1, zeroline=False, showline=False,
                     tickfont=dict(color=TINTA_FRACA, size=12), title_font=dict(color=TINTA_2, size=12))
    return fig


def mostrar(fig: go.Figure, chave: str | None = None) -> None:
    st.plotly_chart(fig, use_container_width=True, theme=None, config=CONFIG_PLOTLY, key=chave)


def faixa_pandemia(fig: go.Figure, x0: float = 2019.5, x1: float = 2021.5) -> None:
    fig.add_vrect(x0=x0, x1=x1, fillcolor=TINTA_FRACA, opacity=0.07, line_width=0, layer="below",
                  annotation_text="pandemia", annotation_position="top left",
                  annotation_font=dict(size=11, color=TINTA_FRACA))


def eixo_anos(fig: go.Figure, anos) -> None:
    anos = sorted(set(int(a) for a in anos))
    fig.update_xaxes(tickmode="array", tickvals=anos, ticktext=[str(a) for a in anos],
                     range=[min(anos) - 0.4, max(anos) + 0.4] if anos else None)


def rotulos_diretos(fig: go.Figure, pontos: list[tuple[str, float, float, str]], log: bool = False,
                    eixo: tuple[float, float] | None = None, altura: int = 360) -> None:
    """Escreve o nome de cada série no fim da linha, sem deixar os nomes se sobreporem.

    pontos: lista de (texto, x, y, cor).
    eixo: mínimo e máximo do eixo y, usados para calcular o espaço entre os nomes.
    """
    if not pontos:
        return
    tr = (lambda v: math.log10(max(v, 1e-9))) if log else (lambda v: v)
    ys = [tr(p[2]) for p in pontos]
    lo, hi = (tr(eixo[0]), tr(eixo[1])) if eixo else (min(ys), max(ys))
    vao = (hi - lo) or 1
    passo = vao * 16 / max(altura - 80, 120)  # ~16 px entre rótulos
    ordem = sorted(range(len(pontos)), key=lambda i: ys[i])
    pos: dict[int, float] = {}
    ultimo = None
    for i in ordem:
        pos[i] = ys[i] if ultimo is None else max(ys[i], ultimo + passo)
        ultimo = pos[i]
    excesso = pos[ordem[-1]] - hi
    if excesso > 0:  # não deixar o último rótulo sair por cima do gráfico
        for i in ordem:
            pos[i] -= excesso
    for i, (texto, x, _y, cor) in enumerate(pontos):
        # no eixo log, o Plotly usa a posição da anotação em log10
        fig.add_annotation(x=x, y=pos[i], xref="x", yref="y",
                           text=f'<span style="color:{cor}">━</span> {texto}', showarrow=False,
                           xanchor="left", xshift=10, font=dict(size=12, color=TINTA_2), align="left")


def destacar_ponto(fig: go.Figure, x, y, texto: str, cor: str = DESTAQUE) -> None:
    """Destaca o ponto do ano escolhido, com marcador maior e o valor."""
    if y is None or pd.isna(y):
        return
    fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(size=12, color=cor, line=dict(width=2, color=SUPERFICIE))))
    fig.add_annotation(x=x, y=y, text=f"<b>{texto}</b>", showarrow=False, yshift=16,
                       font=dict(size=12, color=TINTA), bgcolor=SUPERFICIE)


# Gráficos
def grafico_linhas(df: pd.DataFrame, x: str, y: str, serie: str | None, cores: dict[str, str] | str,
                   fmt_y: str = ",.0f", sufixo: str = "", titulo_y: str = "", anual: bool = True,
                   pandemia: bool = False, log: bool = False, altura: int = 360, direto: bool = True,
                   marcadores: bool = True, aberto: str | None = None, hover_extra: str | None = None,
                   nomes: dict[str, str] | None = None, ordem_x: list | None = None,
                   nome_serie: str | None = None, fmt_hover: str | None = None) -> go.Figure:
    """Gráfico de linhas, com legenda e o nome no fim de cada linha (até 4 séries).

    aberto: coluna booleana; quando verdadeira, o ponto é vazado (dado parcial ou não conferido).
    """
    fig = go.Figure()
    grupos = [(None, df)] if serie is None else list(df.groupby(serie, sort=False))
    ultimos = []
    for nome, d in grupos:
        d = d.sort_values(x) if ordem_x is None else d.set_index(x).reindex(ordem_x).reset_index()
        cor = cores if isinstance(cores, str) else cores.get(nome, NEUTRO)
        rotulo = (nomes or {}).get(nome, nome) if nome is not None else (nome_serie or titulo_y or y)
        simbolos = None
        if aberto and aberto in d:
            simbolos = ["circle-open" if bool(v) else "circle" for v in d[aberto].fillna(False)]
        extra = f"<br>%{{customdata}}" if hover_extra else ""
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], name=str(rotulo), mode="lines+markers" if marcadores else "lines",
            line=dict(color=cor, width=2),
            marker=dict(size=8, color=cor, symbol=simbolos or "circle", line=dict(width=2, color=SUPERFICIE) if not simbolos else dict(width=2, color=cor)),
            customdata=d[hover_extra] if hover_extra else None,
            hovertemplate=f"<b>{rotulo}</b>: %{{y:{fmt_hover or fmt_y}}}{sufixo}{extra}<extra></extra>",
            connectgaps=False,
        ))
        dd = d.dropna(subset=[y])
        if len(dd):
            ultimos.append((str(rotulo), dd[x].iloc[-1], float(dd[y].iloc[-1]), cor))
    n = len(grupos)
    direita = 16
    if direto and 1 <= n <= 4 and serie is not None:
        direita = 12 + 7 * max(len(p[0]) for p in ultimos) if ultimos else 16
        vals = pd.to_numeric(df[y], errors="coerce").dropna()
        eixo = (max(vals.min(), 1e-9), vals.max()) if log else (min(0, vals.min()), vals.max() * 1.05)
        rotulos_diretos(fig, ultimos, log=log, eixo=eixo, altura=altura)
    layout(fig, altura=altura, legenda=(serie is not None and n >= 2), margem_direita=min(direita, 200))
    fig.update_yaxes(title_text=titulo_y, tickformat=fmt_y if not log else None, ticksuffix=sufixo,
                     type="log" if log else "linear", rangemode="tozero" if not log else None)
    if anual:
        eixo_anos(fig, df[x].dropna().unique())
    if pandemia:
        faixa_pandemia(fig)
    return fig


def grafico_barras_h(df: pd.DataFrame, rotulo: str, valor: str, fmt: str = ",.0f", sufixo: str = "",
                     cor: str = DESTAQUE, altura: int | None = None, rotular_topo: bool = True,
                     titulo_x: str = "", hover_extra: str | None = None, fmt_texto=None) -> go.Figure:
    """Ranking em barras horizontais, com o valor escrito só na maior barra."""
    d = df.sort_values(valor, ascending=True)
    fmt_texto = fmt_texto or fmt_int
    textos = [""] * len(d)
    if rotular_topo and len(d):
        textos[-1] = fmt_texto(d[valor].iloc[-1]) + sufixo
    extra = "<br>%{customdata}" if hover_extra else ""
    fig = go.Figure(go.Bar(
        x=d[valor], y=d[rotulo], orientation="h", marker=dict(color=cor, cornerradius=4),
        text=textos, textposition="outside", cliponaxis=False,
        textfont=dict(color=TINTA_2, size=12),
        customdata=d[hover_extra] if hover_extra else None,
        hovertemplate=f"<b>%{{y}}</b>: %{{x:{fmt}}}{sufixo}{extra}<extra></extra>",
    ))
    layout(fig, altura=altura or max(220, 30 * len(d) + 60), legenda=False, hover="closest", margem_direita=70)
    fig.update_xaxes(showgrid=True, gridcolor=GRADE, showline=False, ticks="", tickformat=fmt,
                     ticksuffix=sufixo, title_text=titulo_x, rangemode="tozero")
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA_2, size=12.5), ticks="")
    fig.update_layout(bargap=0.3)
    return fig


def grafico_barras_empilhadas(df: pd.DataFrame, x: str, y: str, serie: str, cores: dict[str, str],
                              fmt: str = ",.0f", titulo_y: str = "", anual: bool = True,
                              pandemia: bool = False, altura: int = 360, ordem: list[str] | None = None,
                              ordem_x: list | None = None) -> go.Figure:
    fig = go.Figure()
    for nome in ordem or list(df[serie].unique()):
        d = df[df[serie] == nome]
        if ordem_x is not None:
            d = d.set_index(x).reindex(ordem_x).reset_index()
        fig.add_trace(go.Bar(
            x=d[x], y=d[y], name=str(nome),
            marker=dict(color=cores.get(nome, NEUTRO), line=dict(width=2, color=SUPERFICIE)),
            hovertemplate=f"{nome}: %{{y:{fmt}}}<extra></extra>",
        ))
    layout(fig, altura=altura, legenda=True)
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text=titulo_y, tickformat=fmt, rangemode="tozero")
    if anual:
        eixo_anos(fig, df[x].dropna().unique())
    if pandemia:
        faixa_pandemia(fig)
    return fig


def mapa_calor(matriz: pd.DataFrame, fmt: str = ",.0f", sufixo: str = "", titulo_escala: str = "",
               altura: int | None = None) -> go.Figure:
    """Mapa de calor por ano e mês, em tons de azul."""
    escala = [[i / (len(SEQUENCIAL) - 1), c] for i, c in enumerate(SEQUENCIAL)]
    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=list(matriz.columns), y=[str(i) for i in matriz.index],
        colorscale=escala, xgap=2, ygap=2, hoverongaps=False,
        colorbar=dict(title=dict(text=titulo_escala, side="right", font=dict(size=12, color=TINTA_2)),
                      thickness=10, outlinewidth=0, tickformat=fmt, ticksuffix=sufixo,
                      tickfont=dict(size=11, color=TINTA_FRACA)),
        hovertemplate=f"%{{x}}/%{{y}}: <b>%{{z:{fmt}}}{sufixo}</b><extra></extra>",
    ))
    layout(fig, altura=altura or max(260, 28 * len(matriz) + 70), legenda=False, hover="closest")
    fig.update_xaxes(showline=False, ticks="", side="top", tickfont=dict(color=TINTA_2))
    fig.update_yaxes(showgrid=False, autorange="reversed", type="category", tickfont=dict(color=TINTA_2))
    return fig


def grafico_variacao(df: pd.DataFrame, rotulo: str, valor: str, altura: int | None = None,
                     titulo_x: str = "Variação (%)") -> go.Figure:
    """Barras de variação: azul para alta, vermelho para queda."""
    d = df.sort_values(valor, ascending=True)
    cores = [DIVERGENTE_POS if v >= 0 else DIVERGENTE_NEG for v in d[valor]]
    fig = go.Figure(go.Bar(
        x=d[valor], y=d[rotulo], orientation="h", marker=dict(color=cores, cornerradius=4),
        hovertemplate="<b>%{y}</b>: %{x:+,.1f}%<extra></extra>",
    ))
    layout(fig, altura=altura or max(220, 30 * len(d) + 60), legenda=False, hover="closest")
    fig.add_vline(x=0, line_width=1, line_color=TINTA_FRACA)
    fig.update_xaxes(showgrid=True, gridcolor=GRADE, showline=False, ticks="", ticksuffix="%", title_text=titulo_x)
    fig.update_yaxes(showgrid=False, tickfont=dict(color=TINTA_2, size=12.5), ticks="")
    return fig


# Tabela
def _csv_br(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False, sep=";", decimal=",")
    return buf.getvalue().encode("utf-8-sig")


NAO_FORMATAR = {"ano", "mes_num", "fonte_relatorio", "fonte_pagina", "ranking"}


def estilo_tabela(df: pd.DataFrame):
    """Formata números no padrão brasileiro (1.234,56) sem mexer em colunas de ano/página."""
    est = df.style.format(na_rep="—")
    for c in df.columns:
        if c in NAO_FORMATAR or not pd.api.types.is_numeric_dtype(df[c]) or pd.api.types.is_bool_dtype(df[c]):
            continue
        vals = pd.to_numeric(df[c], errors="coerce").dropna()
        inteiro = bool(len(vals)) and bool((vals.round() == vals).all())
        est = est.format(na_rep="—", thousands=".", decimal=",", precision=0 if inteiro else 2, subset=[c])
    return est


def tabela(df: pd.DataFrame, nome_arquivo: str, rotulo: str = "Ver dados em tabela", aberto: bool = False,
           chave: str | None = None) -> None:
    """Tabela com os dados do gráfico e botão para baixar o CSV no formato do Excel em português."""
    with st.expander(rotulo, expanded=aberto):
        st.dataframe(estilo_tabela(df), hide_index=True, use_container_width=True)
        st.download_button("Baixar CSV", data=_csv_br(df), file_name=nome_arquivo, mime="text/csv",
                           key=chave or f"dl_{nome_arquivo}")
