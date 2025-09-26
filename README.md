# Análise de Dados do Experimento DIATEX

Este projeto analisa a eficácia do produto DIATEX na redução da volatilização de amônia (NH3) em aviários de frangos de corte. Ele compara dados de aviários que utilizaram o produto (DIATEX) com aviários de controle (TESTEMUNHA).

O sistema completo inclui a extração de dados de relatórios em PDF, o processamento e armazenamento desses dados em um banco de dados SQLite, e a análise e visualização dos resultados através de um Jupyter Notebook e de uma aplicação web interativa.

## Funcionalidades

- **Extração de Dados de PDFs**: O script `extract_tables2.py` utiliza a biblioteca `tabula-py` para extrair tabelas de dados de relatórios em formato PDF.
- **Processamento e Limpeza de Dados**: Os dados extraídos são limpos e processados para garantir a consistência e a qualidade.
- **Armazenamento de Dados**: Os dados são armazenados em um banco de dados SQLite para facilitar o acesso e a análise.
- **Análise de Dados**: O Jupyter Notebook `analise_diatex.ipynb` realiza uma análise exploratória dos dados, com estatísticas descritivas e visualizações.
- **Dashboard Interativo**: A aplicação `app_cloud.py`, desenvolvida com Streamlit, oferece um dashboard interativo para visualizar os dados, aplicar filtros e comparar os resultados dos tratamentos.

## Tecnologias Utilizadas

- **Python 3**
- **Bibliotecas de Análise de Dados**: Pandas, NumPy, SciPy
- **Extração de PDF**: tabula-py, PyPDF2
- **Banco de Dados**: SQLite
- **Visualização de Dados**: Matplotlib, Seaborn, Plotly
- **Aplicação Web**: Streamlit

## Como Utilizar

### Pré-requisitos

- Python 3.8 ou superior
- Java (necessário para o `tabula-py`)

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Execução

1. **Extrair os dados dos PDFs (se necessário)**:
   Coloque os arquivos PDF na pasta `data/raw/pdf` (seguindo o padrão de nomes documentado em `docs/padrao_nomes_pdf.md`) e execute o script:
   ```bash
   python src/extract_tables2.py
   ```
   Isso irá gerar os arquivos CSV na pasta `data/raw/csv` e o banco de dados `TESTE_DIATEX.db` na pasta `database`.

2. **Executar a aplicação web**:
   ```bash
   streamlit run app_cloud.py
   ```
   A aplicação estará disponível em `http://localhost:8501`.

3. **Analisar os dados no Jupyter Notebook**:
   Inicie o Jupyter Notebook e abra o arquivo `analise_diatex.ipynb`:
   ```bash
   jupyter notebook
   ```

## Estrutura do Projeto

```
.
├── analise_diatex.ipynb      # Notebook para análise de dados
├── app_cloud.py              # Aplicação web com Streamlit
├── requirements.txt          # Dependências do projeto
├── src/
│   ├── extract_tables2.py    # Script para extrair dados dos PDFs
│   └── utils/
│       └── logger.py         # Módulo de configuração de logger
├── database/                   # Arquivos de banco de dados e scripts SQL
│   ├── TESTE_DIATEX.db       # Banco de dados SQLite
│   └── ...
├── data/
│   ├── raw/
│   │   ├── csv/              # Arquivos CSV com dados brutos extraídos
│   │   └── pdf/              # Relatórios em PDF (ver padrão de nomes em docs/padrao_nomes_pdf.md)
│   └── processed/            # Dados processados
├── docs/
│   └── padrao_nomes_pdf.md   # Documentação sobre o padrão de nomes dos arquivos PDF
└── README.md                   # Este arquivo
```

## Licença

Este projeto está licenciado sob a Licença Pública Geral GNU v3.0. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
