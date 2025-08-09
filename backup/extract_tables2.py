import tabula
import pandas as pd
import os
import glob
from datetime import datetime
import PyPDF2
import logging
import re
import sqlite3

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_total_pages(pdf_path):
    """Obtém o número total de páginas de um PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            return len(pdf_reader.pages)
    except Exception as e:
        logging.warning(f"Erro ao contar páginas de {pdf_path}: {e}")
        return None

def clean_data(df):
    """Aplica tratamento nos dados do DataFrame."""
    df_clean = df.copy()
    
    # NH3: Remover 'ppm' e converter para inteiro
    df_clean['NH3'] = df_clean['NH3'].str.replace(r'\s*ppm', '', regex=True).str.strip()
    df_clean['NH3'] = pd.to_numeric(df_clean['NH3'], errors='coerce').astype('Int64')
    
    # Temperatura: Remover '°C' ou variações, substituir vírgula por ponto, converter para float
    logging.info("Valores brutos de Temperatura antes da limpeza:")
    logging.info(df_clean['Temperatura'].head(10).to_string())
    
    df_clean['Temperatura'] = df_clean['Temperatura'].str.replace(r'\s*[°℃]\s*C?', '', regex=True).str.strip()
    df_clean['Temperatura'] = df_clean['Temperatura'].str.replace(',', '.', regex=False)
    df_clean['Temperatura'] = pd.to_numeric(df_clean['Temperatura'], errors='coerce').astype(float)
    
    nan_temps = df_clean[df_clean['Temperatura'].isna()]['Temperatura'].index
    if not nan_temps.empty:
        logging.warning(f"Valores NaN encontrados em Temperatura nas linhas: {list(nan_temps)}")
        logging.warning(f"Valores brutos correspondentes: {df.loc[nan_temps, 'Temperatura'].to_dict()}")
    
    # Humedad: Remover '%' e converter para inteiro
    df_clean['Humedad'] = df_clean['Humedad'].str.replace(r'\s*%', '', regex=True).str.strip()
    df_clean['Humedad'] = pd.to_numeric(df_clean['Humedad'], errors='coerce').astype('Int64')
    
    return df_clean

def create_sqlite_db(df, db_dir, timestamp):
    """Cria um banco SQLite com os dados filtrados e views estatísticas."""
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, f"TESTE_DIATEX_{timestamp.strftime('%d_%m_%Y')}.db")
    logging.info(f"Criando banco SQLite: {db_file}")
    
    # Filtrar dados onde NH3 > 0
    df_filtered = df[df['NH3'] > 0].copy()
    if df_filtered.empty:
        logging.warning("Nenhum dado com NH3 > 0 para inserir no banco SQLite.")
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
            'Nome_Arquivo': 'TEXT'
        })
        
        # Criar views estatísticas com arredondamento
        cursor = conn.cursor()
        
        # View 1: Estatísticas por Data
        cursor.execute("""
        CREATE VIEW stats_por_data AS
        SELECT 
            Fecha,
            COUNT(*) as num_registros,
            ROUND(AVG(NH3), 1) as media_nh3,
            ROUND(MIN(NH3), 1) as min_nh3,
            ROUND(MAX(NH3), 1) as max_nh3,
            ROUND(AVG(Temperatura), 1) as media_temperatura,
            ROUND(MIN(Temperatura), 1) as min_temperatura,
            ROUND(MAX(Temperatura), 1) as max_temperatura,
            ROUND(AVG(Humedad), 1) as media_humedad,
            ROUND(MIN(Humedad), 1) as min_humedad,
            ROUND(MAX(Humedad), 1) as max_humedad
        FROM medicoes
        GROUP BY Fecha;
        """)
        
        # View 2: Estatísticas por Arquivo
        cursor.execute("""
        CREATE VIEW stats_por_arquivo AS
        SELECT 
            Nome_Arquivo,
            COUNT(*) as num_registros,
            ROUND(AVG(NH3), 1) as media_nh3,
            ROUND(MIN(NH3), 1) as min_nh3,
            ROUND(MAX(NH3), 1) as max_nh3,
            ROUND(AVG(Temperatura), 1) as media_temperatura,
            ROUND(MIN(Temperatura), 1) as min_temperatura,
            ROUND(MAX(Temperatura), 1) as max_temperatura,
            ROUND(AVG(Humedad), 1) as media_humedad,
            ROUND(MIN(Humedad), 1) as min_humedad,
            ROUND(MAX(Humedad), 1) as max_humedad
        FROM medicoes
        GROUP BY Nome_Arquivo;
        """)
        
        # View 3: Tendências por Hora
        cursor.execute("""
        CREATE VIEW tendencias_por_hora AS
        SELECT 
            SUBSTR(Hora, 1, 2) as hora_do_dia,
            COUNT(*) as num_registros,
            ROUND(AVG(NH3), 1) as media_nh3,
            ROUND(AVG(Temperatura), 1) as media_temperatura,
            ROUND(AVG(Humedad), 1) as media_humedad
        FROM medicoes
        GROUP BY hora_do_dia;
        """)
        
        # View 4: Alertas de NH3 Elevado (NH3 > 20 ppm, sem arredondamento)
        cursor.execute("""
        CREATE VIEW alertas_nh3_elevado AS
        SELECT 
            Fecha,
            Hora,
            NH3,
            Temperatura,
            Humedad,
            Nome_Arquivo
        FROM medicoes
        WHERE NH3 > 20
        ORDER BY Fecha, Hora;
        """)
        
        conn.commit()
        logging.info(f"Banco SQLite criado com sucesso: {db_file}")
        logging.info("Views criadas: stats_por_data, stats_por_arquivo, tendencias_por_hora, alertas_nh3_elevado")

def extract_tables_with_tabula(pdf_path, start_page=5):
    """Extrai todas as tabelas a partir da página 5 de um PDF."""
    logging.info(f"Iniciando extração do arquivo: {pdf_path}")
    
    total_pages = get_total_pages(pdf_path)
    pages = f"{start_page}-" if total_pages is None else f"{start_page}-{total_pages}"
    logging.info(f"Extraindo páginas: {pages} (total estimado: {total_pages or 'desconhecido'})")
    
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    all_data = []
    
    for method, params in [
        ("stream", {"stream": True, "guess": True}),
        ("lattice", {"lattice": True, "guess": True})
    ]:
        logging.info(f"Tentando extração com método: {method}")
        try:
            tables = tabula.read_pdf(
                pdf_path,
                pages=pages,
                multiple_tables=True,
                encoding='utf-8',
                java_options=["-Dfile.encoding=UTF-8"],
                **params
            )
            
            if tables:
                logging.info(f"Encontradas {len(tables)} tabelas com método {method}")
                for table in tables:
                    if len(table.columns) >= 8:
                        table.columns = ['Fecha', 'Hora', 'NH3', 'Rango_NH3', 'Temperatura', 
                                       'Rango_Temperatura', 'Humedad', 'Rango_Humedad']
                    else:
                        logging.warning(f"Tabela com {len(table.columns)} colunas encontrada, mantendo colunas originais")
                    table['Nome_Arquivo'] = file_name
                    all_data.append(table)
                break
            else:
                logging.warning(f"Nenhuma tabela encontrada com método {method}")
        
        except UnicodeDecodeError as e:
            logging.error(f"Erro de decodificação com método {method}: {e}")
            logging.info("Tentando com codificação alternativa (latin-1)...")
            try:
                tables = tabula.read_pdf(
                    pdf_path,
                    pages=pages,
                    multiple_tables=True,
                    encoding='latin-1',
                    java_options=["-Dfile.encoding=UTF-8"],
                    **params
                )
                
                if tables:
                    logging.info(f"Encontradas {len(tables)} tabelas com método {method} e latin-1")
                    for table in tables:
                        if len(table.columns) >= 8:
                            table.columns = ['Fecha', 'Hora', 'NH3', 'Rango_NH3', 'Temperatura', 
                                           'Rango_Temperatura', 'Humedad', 'Rango_Humedad']
                        table['Nome_Arquivo'] = file_name
                        all_data.append(table)
                    break
                else:
                    logging.warning(f"Nenhuma tabela encontrada com método {method} e latin-1")
            
            except Exception as e:
                logging.error(f"Erro ao tentar com latin-1 no método {method}: {e}")
        
        except Exception as e:
            logging.error(f"Erro com método {method}: {e}")
    
    if not all_data:
        logging.warning(f"Nenhum dado extraído de: {pdf_path}")
        return pd.DataFrame()
    
    df = pd.concat(all_data, ignore_index=True)
    df_clean = clean_data(df)
    
    logging.info(f"Dados extraídos de {pdf_path} após tratamento (primeiras 10 linhas):")
    logging.info("\n" + df_clean.head(10).to_string(index=False))
    
    return df_clean

def process_pdf_batch(pdf_dir, csv_dir, db_dir):
    """Processa todos os PDFs na pasta pdf_dir, salva em csv_dir e cria banco em db_dir."""
    logging.info(f"Processando PDFs na pasta: {pdf_dir}")
    
    os.makedirs(csv_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    if not pdf_files:
        logging.warning("Nenhum arquivo PDF encontrado na pasta.")
        return None
    
    logging.info(f"Encontrados {len(pdf_files)} arquivos PDF: {pdf_files}")
    
    all_dfs = []
    for pdf_path in pdf_files:
        df = extract_tables_with_tabula(pdf_path, start_page=5)
        if not df.empty:
            all_dfs.append(df)
        else:
            logging.warning(f"Nenhum dado extraído de: {pdf_path}")
    
    if not all_dfs:
        logging.warning("Nenhum dado extraído de qualquer arquivo.")
        return None
    
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Salvar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = os.path.join(csv_dir, f"dados_medicoes_nh3_{timestamp}.csv")
    final_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    logging.info(f"Dados salvos em: {csv_file}")
    
    # Criar banco SQLite
    create_sqlite_db(final_df, db_dir, datetime.now())
    
    logging.info(f"Resumo dos dados extraídos após tratamento (primeiras 10 linhas):")
    logging.info("\n" + final_df.head(10).to_string(index=False))
    
    return final_df

if __name__ == "__main__":
    pdf_dir = "pdf"
    csv_dir = "csv"
    db_dir = "database"
    
    logging.info("Iniciando extração em lote de PDFs...")
    df = process_pdf_batch(pdf_dir, csv_dir, db_dir)
    
    if df is not None:
        logging.info("Processamento concluído com sucesso.")
    else:
        logging.warning("Processamento concluído sem dados extraídos.")