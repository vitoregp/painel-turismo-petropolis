"""
Gera a base usada pelo painel (pasta data/) a partir dos CSVs extraídos dos relatórios
"Desempenho do Turismo de Petrópolis".

Uso:
    python scripts/preparar_dados.py --entrada <pasta datasets> --saida data

A pasta de entrada tem a subpasta consolidado/ e uma subpasta por ano (2015/, 2016/, ...).
A saída são CSVs com separador vírgula e decimal ponto.

Principais tratamentos:
  - padroniza nomes de atrativos, países, estados e tipos de hospedagem;
  - classifica os atrativos (histórico-cultural, natural, entretenimento cultural);
  - define a visitação anual de cada atrativo: total publicado em texto, depois total lido
    por OCR e, por último, a soma dos meses;
  - marca os valores lidos por OCR que não conferem com o total (ocr_confere);
  - inclui séries que só existem nas pastas anuais (2015-2016 e relatórios só com totais anuais).
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# Util
def ler(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, sep=";", decimal=",", encoding="utf-8-sig")


def sem_acento(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", str(txt))
    return "".join(c for c in txt if not unicodedata.combining(c)).lower()


def salvar(df: pd.DataFrame, saida: Path, nome: str) -> None:
    df.to_csv(saida / nome, index=False, encoding="utf-8")
    print(f"  {nome:<34} {len(df):>5} linhas")


# Atrativos
def canon_atrativo(nome: str) -> str | None:
    s = sem_acento(nome)
    s = re.sub(r"[^a-z0-9 /&]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if "sarau" in s:
        return "Um Sarau Imperial"
    if "concerto" in s or "recita" in s:
        return "Concertos/Recitais – Casa de Petrópolis"
    if "parnaso" in s:
        if "geral" in s or "total" in s:
            return "PARNASO – total das 3 sedes"
        if "teres" in s:
            return "PARNASO – sede Teresópolis"
        if "guapi" in s:
            return "PARNASO – sede Guapimirim"
        if "petr" in s:
            return "PARNASO – sede Petrópolis"
        return None
    regras = [
        ("santos dumont", "Museu Casa de Santos Dumont"),
        ("colono", "Museu Casa do Colono"),
        ("zweig", "Casa Stefan Zweig"),
        ("bohemia", "Centro de Experiência Cervejeira Bohemia"),
        ("nogueira", "Centro Cultural Estação Nogueira"),
        ("luterana", "Igreja de Confissão Luterana"),
        ("brinquedo", "Museu dos Brinquedos"),
        ("princesa isabel", "Galeria Expositiva Princesa Isabel (Catedral)"),
        ("galeria", "Galeria Expositiva Princesa Isabel (Catedral)"),
        ("rio negro", "Palácio Rio Negro"),
        ("amarelo", "Palácio Amarelo (Câmara Municipal)"),
        ("camara municipal", "Palácio Amarelo (Câmara Municipal)"),
        ("som e luz", "Som e Luz"),
        ("quinha", "Parque Natural Municipal Padre Quinha"),
        ("merie", "Parque Crèmerie"),
        ("museu imperial", "Museu Imperial"),
    ]
    for chave, canonico in regras:
        if chave in s:
            return canonico
    if "casa de petr" in s and "cultura" in s:
        return "Casa de Petrópolis – Instituto de Cultura"
    return None


NATURAIS = {
    "PARNASO – total das 3 sedes", "PARNASO – sede Petrópolis", "PARNASO – sede Teresópolis",
    "PARNASO – sede Guapimirim", "Parque Crèmerie", "Parque Natural Municipal Padre Quinha",
}
ENTRETENIMENTO = {"Som e Luz", "Um Sarau Imperial", "Concertos/Recitais – Casa de Petrópolis"}

# Atrativos presentes em todos os anos (2015-2025): base comparável do Panorama.
ANCORAS = [
    "Museu Imperial", "Museu Casa de Santos Dumont", "Centro de Experiência Cervejeira Bohemia",
    "Museu Casa do Colono", "Centro Cultural Estação Nogueira", "Casa Stefan Zweig",
]


def categoria(atrativo: str) -> str:
    if atrativo in NATURAIS:
        return "Natural"
    if atrativo in ENTRETENIMENTO:
        return "Entretenimento cultural"
    return "Histórico-cultural"


def preparar_atrativos(ent: Path, saida: Path) -> pd.DataFrame:
    m = ler(ent / "consolidado" / "visitacao_atrativos_mensal.csv")
    m["atrativo"] = m["atrativo"].map(lambda x: canon_atrativo(x) or x)

    # 2023: garante a sede Teresópolis do PARNASO, caso a consolidação não a tenha incluído.
    f23 = ent / "2023" / "atrativos_naturais_mensal_ocr.csv"
    nat23 = ler(f23) if f23.exists() else pd.DataFrame(columns=["indicador"])
    nat23["atrativo"] = nat23["indicador"].map(canon_atrativo)
    ter = nat23[nat23["atrativo"] == "PARNASO – sede Teresópolis"].copy()
    if not ((m["ano"] == 2023) & (m["atrativo"] == "PARNASO – sede Teresópolis")).any() and len(ter):
        ter = ter.rename(columns={"valor": "visitantes"})
        ter["mes"] = ter["mes_num"].map(lambda n: MESES[int(n) - 1])
        m = pd.concat([m, ter[m.columns.intersection(ter.columns)]], ignore_index=True)

    # PARNASO: o total das 3 sedes deve ser a soma das sedes em cada mês. Quando bate,
    # os valores lidos por OCR são confirmados; quando não bate, ficam como não conferidos.
    sedes = ["PARNASO – sede Teresópolis", "PARNASO – sede Guapimirim", "PARNASO – sede Petrópolis"]
    p = m[m["atrativo"].str.startswith("PARNASO")].pivot_table(index=["ano", "mes_num"], columns="atrativo",
                                                               values="visitantes", aggfunc="first")
    if set(sedes + ["PARNASO – total das 3 sedes"]) <= set(p.columns):
        completos = p[sedes + ["PARNASO – total das 3 sedes"]].dropna()
        fecha = (completos[sedes].sum(axis=1) - completos["PARNASO – total das 3 sedes"]).abs() < 0.6
        m["ocr_confere"] = m["ocr_confere"].astype(object)
        for (ano, mes), ok in fecha.items():
            sel = (m["ano"] == ano) & (m["mes_num"] == mes) & m["atrativo"].str.startswith("PARNASO") \
                & m["ocr_confere"].notna()
            if sel.any():
                m.loc[sel, "ocr_confere"] = bool(ok)

    m["visitantes"] = m["visitantes"].round()
    m["mes_num"] = m["mes_num"].astype(int)
    m["categoria"] = m["atrativo"].map(categoria)
    m["ocr_confere"] = m["ocr_confere"].map({True: "sim", False: "não", "True": "sim", "False": "não"}).fillna("não se aplica")
    m = m[["ano", "mes_num", "mes", "atrativo", "categoria", "visitantes", "ocr_confere",
           "fonte_relatorio", "fonte_pagina", "fonte_tabela"]].sort_values(["ano", "atrativo", "mes_num"])
    salvar(m, saida, "atrativos_mensal.csv")

    # Anual
    g = (m.dropna(subset=["visitantes"])
         .groupby(["ano", "atrativo"])
         .agg(visitantes=("visitantes", "sum"),
              meses_com_dado=("visitantes", "count"),
              meses_ocr_nao_conferidos=("ocr_confere", lambda s: int((s == "não").sum())),
              fonte_pagina=("fonte_pagina", "first"), fonte_tabela=("fonte_tabela", "first"))
         .reset_index())
    g["origem_valor"] = "soma dos meses"
    g["confere"] = g["meses_ocr_nao_conferidos"].map(lambda n: "não" if n else "sim")

    oficiais = []
    # 2022, Quadro 1 (OCR, coluna Total)
    f = ent / "2022" / "indicadores_mensal_ocr.csv"
    w22 = ler(f) if f.exists() else pd.DataFrame()
    for _, r in w22.iterrows():
        a = canon_atrativo(r["indicador"])
        if a:
            oficiais.append(dict(ano=2022, atrativo=a, visitantes=float(r["total"]),
                                 origem_valor="total publicado (OCR)",
                                 confere="sim" if str(r["ocr_confere"]) == "True" else "não",
                                 fonte_pagina=r["fonte_pagina"], fonte_tabela=r["fonte_tabela"]))
    # 2023, Gráfico 1 (texto)
    f = ent / "2023" / "atrativos_total_anual.csv"
    g23 = ler(f) if f.exists() else pd.DataFrame()
    for _, r in g23.iterrows():
        a = canon_atrativo(r["atrativo"])
        if a:
            oficiais.append(dict(ano=2023, atrativo=a, visitantes=float(r["visitantes"]),
                                 origem_valor="total publicado", confere="sim",
                                 fonte_pagina=r["fonte_pagina"], fonte_tabela=r["fonte_tabela"]))
    # Relatórios só com totais anuais (2025, Tabela 1, e os seguintes no mesmo formato)
    anos_so_anuais = []
    for f in sorted(ent.glob("20[0-9][0-9]/indicadores_anual.csv")):
        ano_f = int(f.parent.name)
        anos_so_anuais.append(ano_f)
        for _, r in ler(f).dropna(subset=["total_anual"]).iterrows():
            a = canon_atrativo(r["indicador"])
            if a and float(r["total_anual"]) > 0:
                oficiais.append(dict(ano=ano_f, atrativo=a, visitantes=float(r["total_anual"]),
                                     origem_valor="total publicado", confere="sim",
                                     fonte_pagina=r["fonte_pagina"], fonte_tabela=r["fonte_tabela"]))
    of = pd.DataFrame(oficiais, columns=["ano", "atrativo", "visitantes", "origem_valor", "confere",
                                         "fonte_pagina", "fonte_tabela"])
    of = of[of["visitantes"] > 0]

    base = g.set_index(["ano", "atrativo"])
    of = of.set_index(["ano", "atrativo"])
    meses = base["meses_com_dado"]
    base = base.drop(index=of.index.intersection(base.index))
    anual = pd.concat([base, of]).reset_index()
    anual["meses_com_dado"] = [meses.get((a, t)) for a, t in zip(anual["ano"], anual["atrativo"])]
    sem_meses = [a for a in anos_so_anuais if not (m["ano"] == a).any()]
    anual.loc[anual["ano"].isin(sem_meses), "meses_com_dado"] = None
    anual = anual[anual["visitantes"].notna()]
    anual = anual[~((anual["origem_valor"] == "soma dos meses") & (anual["meses_com_dado"] == 0))]
    anual["categoria"] = anual["atrativo"].map(categoria)
    anual["ancora"] = anual["atrativo"].isin(ANCORAS)
    anual["fonte_relatorio"] = anual["ano"]
    anual = anual[["ano", "atrativo", "categoria", "ancora", "visitantes", "origem_valor", "confere",
                   "meses_com_dado", "fonte_relatorio", "fonte_pagina", "fonte_tabela"]]
    anual = anual.sort_values(["ano", "visitantes"], ascending=[True, False])
    anual["visitantes"] = anual["visitantes"].round().astype("Int64")
    anual["meses_com_dado"] = anual["meses_com_dado"].astype("Int64")
    salvar(anual, saida, "atrativos_anual.csv")
    return anual


# Hospedagem
def preparar_ocupacao(ent: Path, saida: Path) -> None:
    o = ler(ent / "consolidado" / "ocupacao_hoteleira_mensal.csv")
    o["mes_num"] = o["mes_num"].astype(int)
    o = o.rename(columns={"taxa_media": "taxa_media_pct", "distrito_1": "distrito_1_pct",
                          "distritos_2a5": "distritos_2a5_pct"})
    salvar(o.sort_values(["ano", "mes_num"]), saida, "ocupacao_mensal.csv")


TIPOS = {"HOTEL": "Hotel", "POUSADA": "Pousada", "RESORT": "Resort", "SPA": "Spa",
         "HOSTEL": "Hostel", "FLAT": "Flat", "CAMA & CAFÉ": "Cama & café"}


def preparar_capacidade(ent: Path, saida: Path) -> None:
    t = ler(ent / "consolidado" / "capacidade_por_tipo_anual.csv")
    t = t[t["tipo"].str.upper().str.strip() != "TOTAL"].copy()
    t["tipo"] = t["tipo"].str.strip().str.upper().map(TIPOS).fillna(t["tipo"].str.title())
    salvar(t, saida, "capacidade_tipo.csv")

    r = ler(ent / "consolidado" / "capacidade_por_regiao_anual.csv")
    r = r[~r["regiao"].str.upper().str.contains("TOTAL")].copy()
    r["divisao_regional"] = r["ano"].map(lambda a: "7 regiões (2015–2016)" if a <= 2016 else "8 regiões (2017 em diante)")
    salvar(r, saida, "capacidade_regiao.csv")


# Procedência
def preparar_cits(ent: Path, saida: Path) -> None:
    linhas = []
    for pasta in sorted(p for p in ent.iterdir() if p.is_dir() and p.name.isdigit()):
        f = pasta / "nacionais_internacionais.csv"
        if not f.exists():
            continue
        d = ler(f)
        d["k"] = d["origem"].map(sem_acento)
        nac = d.loc[d["k"].str.startswith("nacion"), "turistas"].sum()
        inter = d.loc[d["k"].str.startswith("internac"), "turistas"].sum()
        linhas.append(dict(ano=int(pasta.name), nacionais=int(nac), internacionais=int(inter),
                           total=int(nac + inter), pct_internacionais=round(100 * inter / (nac + inter), 2),
                           fonte_pagina=d["fonte_pagina"].iloc[0], fonte_tabela=d["fonte_tabela"].iloc[0]))
    salvar(pd.DataFrame(linhas), saida, "cits_origem_anual.csv")


UF_SIGLA = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA", "Ceará": "CE",
    "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO", "Maranhão": "MA",
    "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG", "Pará": "PA",
    "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE", "Tocantins": "TO",
    "Não informado": "N/I",
}
UF_FIX = {"Brasília": "Distrito Federal", "Parana": "Paraná", "Espirito Santo": "Espírito Santo",
          "Sao Paulo": "São Paulo", "Goias": "Goiás", "Para": "Pará", "Paraiba": "Paraíba"}


def _top10(ent: Path, ano: int, arquivo: str, col: str) -> pd.DataFrame:
    d = ler(ent / str(ano) / arquivo)
    d = d[d["ano_ref"] == ano]
    d = d[~d[col].map(sem_acento).isin(["outros", "total"])].copy()
    d["ano"] = ano
    d["cobertura"] = "10 principais"
    return d[["ano", col, "turistas", "pct", "cobertura", "fonte_relatorio", "fonte_pagina", "fonte_tabela"]]


def preparar_procedencia(ent: Path, saida: Path) -> None:
    for etapa in (_procedencia_estados, _procedencia_paises):   # uma série não depende da outra
        try:
            etapa(ent, saida)
        except FileNotFoundError as e:
            print(f"  {etapa.__name__.strip('_')}: pulado, falta o arquivo de origem {Path(e.filename).name}")


def _procedencia_estados(ent: Path, saida: Path) -> None:
    e = ler(ent / "consolidado" / "procedencia_estados_anual.csv")
    e["cobertura"] = "todos os estados"
    extra = [_top10(ent, a, "procedencia_estados_top10.csv", "uf") for a in (2015, 2016)
             if (ent / str(a) / "procedencia_estados_top10.csv").exists()]
    e = pd.concat(extra + [e], ignore_index=True)
    e["uf"] = e["uf"].str.strip().replace(UF_FIX)
    e["sigla"] = e["uf"].map(UF_SIGLA)
    e = e[["ano", "uf", "sigla", "turistas", "pct", "cobertura", "fonte_relatorio", "fonte_pagina", "fonte_tabela"]]
    salvar(e.sort_values(["ano", "turistas"], ascending=[True, False]), saida, "procedencia_estados.csv")


def _procedencia_paises(ent: Path, saida: Path) -> None:
    p = ler(ent / "consolidado" / "procedencia_paises_anual.csv")
    p["cobertura"] = "todos os países"
    if (ent / "2015" / "procedencia_paises_top10.csv").exists():
        p = pd.concat([_top10(ent, 2015, "procedencia_paises_top10.csv", "pais"), p], ignore_index=True)
    fix = {"Coréia do Sul": "Coreia do Sul", "Iran": "Irã", "Rep.Tcheca": "República Tcheca",
           "Rep. Tcheca": "República Tcheca", "Rep. Dominicana": "República Dominicana",
           "Rep. de Malta": "Malta", "Suiça": "Suíça", "Vietnam": "Vietnã",
           "Emirados": "Emirados Árabes Unidos", "Dubai": "Emirados Árabes Unidos"}
    p["pais"] = p["pais"].str.strip().replace(fix)
    p = (p.groupby(["ano", "pais", "cobertura", "fonte_relatorio", "fonte_pagina", "fonte_tabela"], as_index=False)
         [["turistas", "pct"]].sum())
    p = p[["ano", "pais", "turistas", "pct", "cobertura", "fonte_relatorio", "fonte_pagina", "fonte_tabela"]]
    salvar(p.sort_values(["ano", "turistas"], ascending=[True, False]), saida, "procedencia_paises.csv")


# Atendimento
def preparar_disque(ent: Path, saida: Path) -> None:
    d = ler(ent / "consolidado" / "disque_turismo_mensal.csv")
    d = d[d["canal"].isin(["0800", "WhatsApp"])].copy()
    d["canal"] = d["canal"].map({"0800": "Telefone (0800)", "WhatsApp": "WhatsApp"})
    d["mes_num"] = d["mes_num"].astype(int)
    d = d.rename(columns={"valor": "atendimentos"})
    salvar(d.sort_values(["ano", "canal", "mes_num"]), saida, "disque_turismo_mensal.csv")

    a = d.groupby(["ano", "canal"], as_index=False)["atendimentos"].sum()
    a["origem_valor"] = "soma dos meses"
    extra = []
    for ano in (2015, 2016):
        f = ent / str(ano) / "disque_turismo_total.csv"
        if f.exists():
            t = ler(f)
            extra.append(dict(ano=ano, canal="Telefone (0800)", atendimentos=float(t[f"v{ano}"].iloc[0]),
                              origem_valor="total publicado"))
    for f in sorted(ent.glob("20[0-9][0-9]/indicadores_anual.csv")):   # relatórios só com totais anuais
        ano_f = int(f.parent.name)
        if (d["ano"] == ano_f).any():
            continue
        for _, r in ler(f).iterrows():
            k = sem_acento(r["indicador"])
            if "disque" in k and "0800" in k:
                extra.append(dict(ano=ano_f, canal="Telefone (0800)", atendimentos=r["total_anual"], origem_valor="total publicado"))
            elif "disque" in k and "whats" in k:
                extra.append(dict(ano=ano_f, canal="WhatsApp", atendimentos=r["total_anual"], origem_valor="total publicado"))
    a = pd.concat([pd.DataFrame(extra), a], ignore_index=True).sort_values(["ano", "canal"])
    a["atendimentos"] = a["atendimentos"].round().astype("Int64")
    salvar(a, saida, "disque_turismo_anual.csv")


def preparar_estrada_real(ent: Path, saida: Path) -> None:
    e = ler(ent / "consolidado" / "estrada_real_mensal.csv")
    mapa = {"PASSAPORTE": "Passaporte emitido", "CARIMBO": "Carimbo no passaporte",
            "VIAJANTES": "Total de viajantes", "TOTAL": "Total de viajantes",
            "TOTAL DE VIAJANTES": "Total de viajantes"}
    e["indicador"] = e["indicador"].str.strip().str.upper().map(mapa)
    e = e.dropna(subset=["indicador"]).drop_duplicates(["ano", "mes_num", "indicador"])
    e["mes_num"] = e["mes_num"].astype(int)
    salvar(e.sort_values(["ano", "indicador", "mes_num"]), saida, "estrada_real_mensal.csv")


def preparar_pedagogico(ent: Path, saida: Path) -> None:
    t = ler(ent / "consolidado" / "turismo_pedagogico_anual.csv")
    t["atrativo"] = t["atrativo"].map(lambda x: canon_atrativo(x) or x)
    for c in ("visitacao_total", "visitacao_escolar", "pct_escolar", "pct_visitacao_escolar"):
        if c not in t:            # 2015-2016 só têm o percentual; 2017+ só as contagens
            t[c] = float("nan")
    t["pct_escolar"] = t["pct_escolar"].fillna(t["pct_visitacao_escolar"])
    t = t[~((t["visitacao_total"] == 0) & t["visitacao_escolar"].isna())]
    t["visitacao_nao_escolar"] = t["visitacao_total"] - t["visitacao_escolar"]
    t = t[["ano", "atrativo", "visitacao_total", "visitacao_escolar", "visitacao_nao_escolar", "pct_escolar",
           "fonte_relatorio", "fonte_pagina", "fonte_tabela"]]
    for c in ["visitacao_total", "visitacao_escolar", "visitacao_nao_escolar"]:
        t[c] = t[c].round().astype("Int64")
    salvar(t, saida, "turismo_pedagogico.csv")


# Main
def executar(entrada, saida) -> None:
    """Gera a base do painel a partir da pasta datasets/."""
    ent, saida = Path(entrada), Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    print(f"Lendo {ent} e gravando em {saida}")
    for etapa in (preparar_atrativos, preparar_ocupacao, preparar_capacidade, preparar_cits,
                  preparar_procedencia, preparar_disque, preparar_estrada_real, preparar_pedagogico):
        try:
            etapa(ent, saida)
        except FileNotFoundError as e:   # ex.: rodou só alguns anos e a série não existe ainda
            print(f"  {etapa.__name__}: pulado, falta o arquivo de origem {Path(e.filename).name}")
        except KeyError as e:
            print(f"  {etapa.__name__}: pulado, os anos extraídos não têm a coluna {e}")
    print("Pronto.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default="datasets", help="pasta 'datasets' gerada pelos notebooks")
    ap.add_argument("--saida", default=str(Path(__file__).resolve().parents[1] / "data"))
    a = ap.parse_args()
    executar(a.entrada, a.saida)


if __name__ == "__main__":
    main()
