# Painel do Turismo de Petrópolis

Dashboard interativo (Streamlit + Plotly) com os dados extraídos dos relatórios anuais
**Desempenho do Turismo de Petrópolis** (2015–2025). Projeto de Extensão — UCP.

Acesse: https://painel-turismo-petropolis.streamlit.app

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
painel-turismo-petropolis/
├── app.py ← ponto de entrada (navegação)
├── paginas/ ← uma página por arquivo
├── lib/
│ ├── dados.py ← leitura dos CSVs (com cache)
│ └── estilo.py ← cores, formatação pt-BR e funções de gráfico
├── data/ ← CSVs limpos usados pelo app
├── scripts/
│ └── preparar_dados.py ← gera data/ a partir da pasta datasets (o notebook de ETL usa o mesmo script)
├── .streamlit/config.toml ← tema
└── requirements.txt
```

## Rodar no seu computador

Requer Python 3.10 a 3.12.

```bash
git clone https://github.com/vitoregp/painel-turismo-petropolis.git
cd painel-turismo-petropolis
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O painel abre em `http://localhost:8501`.
