import os
import sys

def find_project_root(current_path):
    """Finds the project root by looking for the .git directory."""
    while current_path != os.path.dirname(current_path):
        if os.path.isdir(os.path.join(current_path, '.git')):
            return current_path
        current_path = os.path.dirname(current_path)
    return None # .git not found

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = find_project_root(script_dir)

if project_root:
    sys.path.insert(0, project_root)
else:
    # Fallback if .git is not found, assume script_dir is within project_root
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    sys.path.insert(0, project_root)

from tabula import read_pdf
import pandas as pd
import os
import glob
from datetime import datetime
import PyPDF2
import logging
import re
import sqlite3
from src.utils.logger import setup_logger

# Configurar logging
logger = setup_logger('extract_tables2')

def get_total_pages(pdf_path):
    """Obtém o número total de páginas de um PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            return len(pdf_reader.pages)
    except Exception as e:
        logger.warning(f"Erro ao contar páginas de {pdf_path}: {e}")
        return None

def clean_data(df):
    """Aplica tratamento nos dados do DataFrame."""
    df_clean = df.copy()

    # NH3: Remover 'ppm' e converter para inteiro
    df_clean['NH3'] = df_clean['NH3'].str.replace(r'\s*ppm', '', regex=True).str.strip()
    df_clean['NH3'] = pd.to_numeric(df_clean['NH3'], errors='coerce').astype('Int64')

    # Temperatura: Remover '°C' ou variações, substituir vírgula por ponto, converter para float
    logger.info("Valores brutos de Temperatura antes da limpeza:")
    logger.info(df_clean['Temperatura'].head(10).to_string())

    df_clean['Temperatura'] = df_clean['Temperatura'].str.replace(r'\s*[°℃]\s*C?', '', regex=True).str.strip()
    df_clean['Temperatura'] = df_clean['Temperatura'].str.replace(',', '.', regex=False)
    df_clean['Temperatura'] = pd.to_numeric(df_clean['Temperatura'], errors='coerce').astype(float)

    nan_temps = df_clean[df_clean['Temperatura'].isna()]['Temperatura'].index
    if not nan_temps.empty:
        logger.warning(f"Valores NaN encontrados em Temperatura nas linhas: {list(nan_temps)}")
        logger.warning(f"Valores brutos correspondentes: {df.loc[nan_temps, 'Temperatura'].to_dict()}")

    # Humedad: Remover '%' e converter para inteiro
    df_clean['Humedad'] = df_clean['Humedad'].str.replace(r'\s*%', '', regex=True).str.strip()
    df_clean['Humedad'] = pd.to_numeric(df_clean['Humedad'], errors='coerce').astype('Int64')

    # Fecha: Converter DD/MM/YYYY para YYYY-MM-DD
    try:
        df_clean['Fecha'] = pd.to_datetime(df_clean['Fecha'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
    except Exception as e:
        logger.warning(f"Erro ao converter Fecha para DATE: {e}")
        logger.warning(f"Valores brutos de Fecha: {df_clean['Fecha'].head(10).to_string()}")

    return df_clean

def get_aviario_id_from_filename(filename):
    """
    Extrai o ID do aviário do nome do arquivo usando regex.
    """
    match = re.search(r'(aviario_\d+|galpao_\d+)', filename.lower())
    if match:
        return match.group(1)
    else:
        return os.path.splitext(filename)[0]

def create_sqlite_db(df, db_dir):
    """Cria um banco SQLite com os dados filtrados e a tabela medicoes."""
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, "TESTE_DIATEX.db")
    logger.info(f"Criando banco SQLite e tabela 'medicoes': {db_file}")

    # Filtrar dados onde NH3 > 0
    df_filtered = df[df['NH3'] > 0].copy()
    if df_filtered.empty:
        logger.warning("Nenhum dado com NH3 > 0 para inserir no banco SQLite.")
        return

    # Conectar ao banco SQLite
    with sqlite3.connect(db_file) as conn:
        # Criar tabela medicoes
        df_filtered.to_sql('medicoes', conn, if_exists='replace', index=False, dtype={
            'Fecha': 'TEXT',
            'Hora': 'TEXT',
            'NH3': 'INTEGER',
            'Rango_NH3': 'TEXT',
            'Temperatura': 'REAL',
            'Rango_Temperatura': 'TEXT',
            'Humedad': 'INTEGER',
            'Rango_Humedad': 'TEXT',
            'Nome_Arquivo': 'TEXT',
            'ID_Aviario': 'TEXT'
        })
        conn.commit()
    logger.info(f"Tabela 'medicoes' criada e dados inseridos com sucesso em: {db_file}")

def extract_tables_with_tabula(pdf_path, start_page=5):
    """Extrai todas as tabelas a partir da página 5 de um PDF."""
    logger.info(f"Iniciando extração do arquivo: {pdf_path}")

    total_pages = get_total_pages(pdf_path)
    pages = f"{start_page}-" if total_pages is None else f"{start_page}-{total_pages}"
    logger.info(f"Extraindo páginas: {pages} (total estimado: {total_pages or 'desconhecido'})")

    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    aviario_id = get_aviario_id_from_filename(file_name)
    all_data = []

    for method, params in [
        ("stream", {"stream": True, "guess": True}),
        ("lattice", {"lattice": True, "guess": True})
    ]:
        logger.info(f"Tentando extração com método: {method}")
        try:
            tables = read_pdf(
                pdf_path,
                pages=pages,
                multiple_tables=True,
                encoding='utf-8',
                **params
            )
            # ... (restante da lógica de extração e tratamento permanece inalterada) ...
            if tables:
                logger.info(f"Encontradas {len(tables)} tabelas com método {method}")
                for table in tables:
                    if len(table.columns) >= 8:
                        table.columns = ['Fecha', 'Hora', 'NH3', 'Rango_NH3', 'Temperatura',
                                         'Rango_Temperatura', 'Humedad', 'Rango_Humedad']
                    else:
                        logger.warning(f"Tabela com {len(table.columns)} colunas encontrada, mantendo colunas originais")
                    
                    table['Nome_Arquivo'] = file_name
                    table['ID_Aviario'] = aviario_id
                    all_data.append(table)
                break
            else:
                logger.warning(f"Nenhuma tabela encontrada com método {method}")
        except Exception as e:
            logger.error(f"Erro com método {method}: {e}")

    if not all_data:
        logger.warning(f"Nenhum dado extraído de: {pdf_path}")
        return pd.DataFrame()

    df = pd.concat(all_data, ignore_index=True)
    df_clean = clean_data(df)

    logger.info(f"Dados extraídos de {pdf_path} após tratamento (primeiras 10 linhas):")
    logger.info("\n" + df_clean.head(10).to_string(index=False))

    return df_clean

def process_pdf_batch(pdf_dir, csv_dir, db_dir):
    """Processa todos os PDFs na pasta pdf_dir, salva em csv_dir e cria banco em db_dir."""
    logger.info(f"Processando PDFs na pasta: {pdf_dir}")

    os.makedirs(csv_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    if not pdf_files:
        logger.warning("Nenhum arquivo PDF encontrado na pasta.")
        return None

    logger.info(f"Encontrados {len(pdf_files)} arquivos PDF: {pdf_files}")

    all_dfs = []
    for pdf_path in pdf_files:
        df = extract_tables_with_tabula(pdf_path, start_page=5)
        if not df.empty:
            all_dfs.append(df)
        else:
            logger.warning(f"Nenhum dado extraído de: {pdf_path}")

    if not all_dfs:
        logger.warning("Nenhum dado extraído de qualquer arquivo.")
        return None

    final_df = pd.concat(all_dfs, ignore_index=True)

    # Salvar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = os.path.join(csv_dir, f"dados_medicoes_nh3_{timestamp}.csv")
    final_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    logger.info(f"Dados salvos em: {csv_file}")

    # Criar banco SQLite e a tabela `medicoes`
    create_sqlite_db(final_df, db_dir)

    logger.info(f"Resumo dos dados extraídos após tratamento (primeiras 10 linhas):")
    logger.info("\n" + final_df.head(10).to_string(index=False))

    return final_df

if __name__ == "__main__":
    pdf_dir = os.path.join(project_root, "data", "raw", "pdf")
    csv_dir = os.path.join(project_root, "data", "raw", "csv")
    db_dir = os.path.join(project_root, "database")

    logger.info("Iniciando extração em lote de PDFs...")
    df = process_pdf_batch(pdf_dir, csv_dir, db_dir)

    if df is not None:
        logger.info("Processamento concluído com sucesso.")
    else:
        logger.warning("Processamento concluído sem dados extraídos.")
