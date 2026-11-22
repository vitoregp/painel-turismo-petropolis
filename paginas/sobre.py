import pandas as pd
import streamlit as st

from lib import dados
from lib import estilo as E

st.title("Sobre os dados")
st.caption("De onde vêm os números, como foram tratados e o que observar ao interpretá-los.")

c1, c2 = st.columns([1.5, 1], gap="large")
with c1:
    st.markdown(
        """
**Fonte.** Relatórios anuais *Desempenho do Turismo de Petrópolis* de 2015 a 2025, em PDF.
As tabelas foram extraídas com Python (`pdfplumber` para texto e OCR com `Tesseract` para as tabelas em imagem)
no notebook de ETL do Google Colab, que também padroniza, confere e gera esta base (`scripts/preparar_dados.py`).

**Rastreabilidade.** Toda linha dos dados guarda o relatório, a página e a tabela de origem
(`fonte_relatorio`, `fonte_pagina`, `fonte_tabela`), o que permite conferir qualquer número no PDF.

**Visitação anual.** Para cada atrativo e ano, o valor vem, em ordem de preferência, do
total publicado no relatório em texto (2023 e 2025), do total publicado lido por OCR (2022)
ou da soma dos meses disponíveis. A coluna `origem_valor` informa qual foi usado.

**Atrativos-âncora.** Seis atrativos aparecem em todos os relatórios (Museu Imperial, Casa de Santos Dumont,
Bohemia, Casa do Colono, Estação Nogueira e Casa Stefan Zweig). A soma deles é a base comparável
usada no Panorama, já que a lista de atrativos monitorados mudou ao longo dos anos.
"""
    )
with c2:
    st.markdown("**Cuidados na leitura**")
    st.markdown(
        """
- **Pandemia (2020–2021):** atrativos e CITs fechados ou com restrições durante boa parte do período.
- **OCR não conferido:** 2022 e 2023 trazem quadros em imagem; quando a soma dos meses não bateu
  com o total, o valor aparece com marcador vazado e pode ser excluído no filtro.
- **2025:** o relatório traz apenas totais anuais (sem meses, procedência por país/estado ou capacidade).
- **Regiões de hospedagem:** a divisão mudou em 2017 (7 → 8 regiões).
- **PARNASO:** as sedes Teresópolis e Guapimirim ficam fora do município; nos agregados de
  Petrópolis entra só a sede Petrópolis.
- **Inconsistências do próprio relatório** foram mantidas como publicadas (ex.: Casa do Colono 2025 aparece
  com 16.294 visitantes na tabela de indicadores e 16.234 na de turismo pedagógico).
"""
    )

st.divider()
st.markdown("### Conjuntos de dados")
dic = pd.DataFrame(dados.DICIONARIO, columns=["arquivo", "conteúdo", "colunas"])
dic["linhas"] = [len(dados.ler(n)) for n in dic["arquivo"]]
dic["arquivo"] = dic["arquivo"] + ".csv"
st.dataframe(dic[["arquivo", "conteúdo", "linhas", "colunas"]], hide_index=True, use_container_width=True)
st.download_button("Baixar todos os dados (.zip)", data=dados.zip_todos(), file_name="dados_turismo_petropolis.zip",
                   mime="application/zip", type="primary")
E.nota("Os CSVs do pacote usam vírgula como separador e ponto como decimal (padrão para Python/R). "
       "Os botões “Baixar CSV” de cada gráfico geram arquivos com ponto e vírgula, prontos para o Excel em português.")
