# Painel do Turismo de Petrópolis

Dashboard interativo (Streamlit + Plotly) com os dados extraídos dos relatórios anuais
**Desempenho do Turismo de Petrópolis** (2015–2025). Projeto de Extensão — UCP.

## O que tem no painel

| Página | Conteúdo |
|---|---|
| **Panorama** | Indicadores do ano (com variação sobre o ano anterior), visitação nos 6 atrativos-âncora, ocupação hoteleira, turistas nos CITs e ranking de atrativos |
| **Atrativos turísticos** | Evolução anual (escala linear, log ou índice 2019 = 100), sazonalidade, mapa de calor mensal, ranking e variação anual |
| **Hospedagem** | Ocupação mês a mês e por distrito; capacidade (leitos, UHs, MHs) por tipo e por região |
| **Procedência dos turistas** | Nacionais × internacionais, ranking e evolução por estado e por país |
| **Atendimento ao turista** | Disque Turismo (0800 e WhatsApp), passaporte da Estrada Real, turismo pedagógico |
| **Sobre os dados** | Fonte, tratamento, cuidados de leitura, dicionário e download de todos os CSVs |

Todo gráfico tem a versão em tabela logo abaixo, com botão para baixar o CSV (formato do Excel em português).

## Estrutura

```
painel_turismo_petropolis/
├── app.py                  ← ponto de entrada (navegação)
├── paginas/                ← uma página por arquivo
├── lib/
│   ├── dados.py            ← leitura dos CSVs (com cache)
│   └── estilo.py           ← cores, formatação pt-BR e funções de gráfico
├── data/                   ← CSVs limpos usados pelo app
├── scripts/
│   └── preparar_dados.py   ← gera data/ a partir da pasta datasets (o notebook de ETL usa o mesmo script)
├── .streamlit/config.toml  ← tema
└── requirements.txt
```

## Rodar no seu computador

Requer Python 3.10 a 3.12.

```bash
cd painel_turismo_petropolis
python -m venv .venv
# Windows: .venv\Scripts\activate    |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O painel abre em `http://localhost:8501`.

## Publicar online (grátis) — Streamlit Community Cloud

1. **Crie um repositório no GitHub** (pode ser público) e envie o conteúdo desta pasta.
   Pelo site: *New repository* → *uploading an existing file* → arraste todos os arquivos e pastas
   (inclusive a pasta oculta `.streamlit`). Ou pelo terminal:
   ```bash
   git init
   git add .
   git commit -m "Painel do turismo de Petrópolis"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/painel-turismo-petropolis.git
   git push -u origin main
   ```
2. Acesse **https://share.streamlit.io**, entre com a conta do GitHub e clique em **Create app**.
3. Escolha o repositório, a branch `main` e o arquivo principal `app.py`.
4. Em **Advanced settings**, selecione **Python 3.12**.
5. (Opcional) Defina um endereço, por exemplo `turismo-petropolis.streamlit.app`.
6. Clique em **Deploy**. Em 2–3 minutos o painel estará no ar; cada `git push` atualiza o site sozinho.

> Se o repositório for privado, o app também pode ser restrito a convidados em *Settings → Sharing*.

## Atualizar os dados (ex.: chegou o relatório de 2026)

1. No Google Colab, rode o notebook **`ETL_Turismo_Petropolis_completo.ipynb`** (extração, consolidação,
   base analítica, checagens de qualidade e banco SQLite, tudo em sequência).
2. A base do painel sai em `MyDrive/UCP_turismo/datasets/analitico/`. Para publicar, ligue a opção
   `ATUALIZAR_GITHUB` do notebook (envia os CSVs para a pasta `data/` deste repositório) ou copie os arquivos à mão.
3. O painel publicado se atualiza sozinho depois do envio ao GitHub.

O script `scripts/preparar_dados.py` é o mesmo usado pelo notebook e também roda sozinho:
`python scripts/preparar_dados.py --entrada <pasta datasets> --saida data`.

## Decisões de tratamento (resumo)

* **Visitação anual**: total publicado em texto > total publicado lido por OCR > soma dos meses (coluna `origem_valor`).
* **Valores lidos por OCR (2022–2023)**: cada linha é conferida (soma dos meses = total e total ÷ meses = média
  impressa; no PARNASO, também sedes = total). Na base atual todos os meses de atrativos conferem; se algum não
  conferir numa nova extração, ele aparece com marcador vazado e pode ser excluído pelo filtro *Incluir não conferidos*.
* **Atrativos-âncora**: Museu Imperial, Casa de Santos Dumont, Bohemia, Casa do Colono, Estação Nogueira e
  Casa Stefan Zweig — os únicos presentes em todos os anos; a soma deles é a série comparável do Panorama.
* **PARNASO**: as sedes Teresópolis e Guapimirim (e o total das 3 sedes) ficam fora dos agregados do município.
* **2025**: o relatório traz só totais anuais; não há dados mensais de atrativos, procedência detalhada nem capacidade.
* **Regiões de hospedagem**: divisão mudou em 2017 (7 → 8 regiões).

## Personalizar

* Cores e fontes: `lib/estilo.py` (paleta categórica de 8 cores em ordem fixa, validada para daltonismo) e
  `.streamlit/config.toml`.
* Novas páginas: crie `paginas/minha_pagina.py` e registre em `app.py` com `st.Page(...)`.
