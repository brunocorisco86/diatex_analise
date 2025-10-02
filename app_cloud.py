import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import os
import tempfile
from scipy import stats
import datetime
from datetime import timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Análise DIATEX - Dashboard Avançado",
    page_icon="🐔",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/seu-usuario/testeDiatexCama',
        'Report a bug': "https://github.com/seu-usuario/testeDiatexCama/issues",
        'About': "Dashboard para análise de eficácia do produto DIATEX em aviários"
    }
)

# Função para carregar os dados do banco SQLite
@st.cache_data
def carregar_dados(caminho_db):
    # Conectar ao banco de dados
    conn = sqlite3.connect(caminho_db)
    
    # Carregar dados da tabela medicoes com join na tabela tratamentos
    query = """
    SELECT 
        m.Fecha, m.Hora, m.NH3, m.Temperatura, m.Humedad, 
        m.Nome_Arquivo, m.lote_composto, m.idade_lote, m.n_cama, m.teste,
        t.produtor, t.linhagem, t.bateria_teste
    FROM medicoes m
    LEFT JOIN tratamentos t ON m.lote_composto = t.lote_composto
    WHERE m.teste IS NOT NULL AND m.teste != ''
    """
    df = pd.read_sql_query(query, conn)
    
    # Fechar conexão
    conn.close()
    
    # Verificar se temos dados
    if len(df) == 0:
        st.error("Nenhum dado encontrado com tratamentos válidos!")
        st.stop()
    
    # Converter colunas de data e hora
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['data_hora'] = pd.to_datetime(df['Fecha'].astype(str) + ' ' + df['Hora'])
    
    # Criar coluna de semana de vida
    df['semana_vida'] = (df['idade_lote'] // 7) + 1
    
    # Criar coluna de aviário (extrair do nome do arquivo)
    df['aviario'] = df['Nome_Arquivo'].str.extract(r'(\d+)').astype(str)
    
    return df

# Função para criar gráficos comparativos (refatorada)
def criar_grafico_comparativo(df, variavel, agrupar_por='dia'):
    dados = df.copy()
    
    # Definir agrupamento
    if agrupar_por == 'dia':
        dados['grupo'] = dados['Fecha'].dt.date
    elif agrupar_por == 'semana':
        dados['grupo'] = dados['semana_vida']
    else:  # hora
        dados['grupo'] = dados['data_hora'].dt.floor('H')
    
    # Agrupar dados
    dados_agrupados = dados.groupby(['grupo', 'teste'])[variavel].mean().reset_index()
    
    # Criar gráfico com Plotly
    fig = px.line(
        dados_agrupados, 
        x='grupo', 
        y=variavel, 
        color='teste',
        markers=True,
        title=f'Comparativo de {variavel} entre tratamentos',
        labels={'grupo': 'Período', variavel: variavel, 'teste': 'Tratamento'},
        color_discrete_map={'DIATEX': '#1f77b4', 'TESTEMUNHA': '#ff7f0e'}
    )
    
    # Adicionar estatísticas no título
    media_diatex = dados[dados['teste'] == 'DIATEX'][variavel].mean()
    media_testemunha = dados[dados['teste'] == 'TESTEMUNHA'][variavel].mean()
    
    fig.update_layout(
        title=f'Comparativo de {variavel} entre tratamentos<br><sup>Média DIATEX: {media_diatex:.2f} | Média TESTEMUNHA: {media_testemunha:.2f}</sup>',
        xaxis_title='Período',
        yaxis_title=variavel,
        legend_title='Tratamento',
        hovermode='x unified'
    )
    
    return fig

# Função para calcular métricas de desempenho
def calcular_metricas_desempenho(df):
    """Calcula métricas de desempenho do produto DIATEX"""
    metricas = {}
    
    for tratamento in ['DIATEX', 'TESTEMUNHA']:
        dados_trat = df[df['teste'] == tratamento]
        
        if len(dados_trat) > 0:  # Verificar se há dados para o tratamento
            metricas[tratamento] = {
                'nh3_media': dados_trat['NH3'].mean(),
                'nh3_std': dados_trat['NH3'].std(),
                'nh3_min': dados_trat['NH3'].min(),
                'nh3_max': dados_trat['NH3'].max(),
                'temp_media': dados_trat['Temperatura'].mean(),
                'umid_media': dados_trat['Humedad'].mean(),
                'n_medicoes': len(dados_trat),
                'dias_monitoramento': dados_trat['Fecha'].nunique()
            }
    
    # Calcular eficácia relativa apenas se ambos os tratamentos existirem
    if 'DIATEX' in metricas and 'TESTEMUNHA' in metricas:
        if metricas['TESTEMUNHA']['nh3_media'] > 0:  # Evitar divisão por zero
            metricas['eficacia_nh3'] = ((metricas['TESTEMUNHA']['nh3_media'] - metricas['DIATEX']['nh3_media']) / 
                                       metricas['TESTEMUNHA']['nh3_media']) * 100
        
        if metricas['TESTEMUNHA']['nh3_std'] > 0:  # Evitar divisão por zero
            metricas['reducao_variabilidade'] = ((metricas['TESTEMUNHA']['nh3_std'] - metricas['DIATEX']['nh3_std']) / 
                                               metricas['TESTEMUNHA']['nh3_std']) * 100
    
    return metricas

# Função para análise de tendências temporais
def analisar_tendencias(df, variavel):
    """Analisa tendências temporais dos dados"""
    resultados = {}
    
    for tratamento in ['DIATEX', 'TESTEMUNHA']:
        dados_trat = df[df['teste'] == tratamento].copy()
        if len(dados_trat) > 10:  # Mínimo de pontos para análise
            dados_trat = dados_trat.sort_values('data_hora')
            dados_trat['tempo_numerico'] = (dados_trat['data_hora'] - dados_trat['data_hora'].min()).dt.total_seconds()
            
            # Regressão linear simples
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                dados_trat['tempo_numerico'], dados_trat[variavel]
            )
            
            resultados[tratamento] = {
                'slope': slope,
                'r_squared': r_value**2,
                'p_value': p_value,
                'tendencia': 'crescente' if slope > 0 else 'decrescente' if slope < 0 else 'estável',
                'significativa': p_value < 0.05
            }
    
    return resultados

# Função para análise PCA
def realizar_pca(df):
    """Realiza análise de componentes principais"""
    try:
        # Preparar dados para PCA
        variaveis = ['NH3', 'Temperatura', 'Humedad', 'idade_lote']
        dados_pca = df[variaveis + ['teste']].dropna()
        
        if len(dados_pca) == 0:
            return None, None
        
        # Separar por tratamento
        X_diatex = dados_pca[dados_pca['teste'] == 'DIATEX'][variaveis]
        X_testemunha = dados_pca[dados_pca['teste'] == 'TESTEMUNHA'][variaveis]
        
        if len(X_diatex) > 10 and len(X_testemunha) > 10:
            # Padronizar dados
            scaler = StandardScaler()
            X_combined = pd.concat([X_diatex, X_testemunha])
            X_scaled = scaler.fit_transform(X_combined)
            
            # Aplicar PCA
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Criar DataFrame com resultados
            df_pca = pd.DataFrame(X_pca, columns=['PC1', 'PC2'])
            df_pca['teste'] = dados_pca['teste'].values
            
            return df_pca, pca.explained_variance_ratio_
        else:
            return None, None
    except Exception as e:
        st.error(f"Erro na análise PCA: {str(e)}")
        return None, None

# Função para alertas e recomendações
def gerar_alertas(df):
    """Gera alertas baseados nos dados"""
    alertas = []
    
    # Verificar níveis críticos de NH3
    nh3_critico = 25  # ppm - limite considerado alto
    medicoes_criticas = df[df['NH3'] > nh3_critico]
    
    if len(medicoes_criticas) > 0:
        # Filtrar valores não nulos na coluna teste
        tratamentos_afetados = medicoes_criticas['teste'].dropna().unique()
        tratamentos_str = ', '.join(tratamentos_afetados) if len(tratamentos_afetados) > 0 else 'Não especificado'
        
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Níveis Críticos de Amônia',
            'mensagem': f'{len(medicoes_criticas)} medições acima de {nh3_critico} ppm detectadas.',
            'detalhes': f"Tratamentos afetados: {tratamentos_str}"
        })
    
    # Verificar eficácia do produto
    metricas = calcular_metricas_desempenho(df)
    if 'eficacia_nh3' in metricas:
        if metricas['eficacia_nh3'] > 10:
            alertas.append({
                'tipo': 'success',
                'titulo': 'Eficácia Comprovada',
                'mensagem': f'DIATEX apresenta redução de {metricas["eficacia_nh3"]:.1f}% nos níveis de NH3.',
                'detalhes': 'Resultado estatisticamente significativo'
            })
        elif metricas['eficacia_nh3'] < -5:
            alertas.append({
                'tipo': 'error',
                'titulo': 'Eficácia Questionável',
                'mensagem': f'DIATEX apresenta aumento de {abs(metricas["eficacia_nh3"]):.1f}% nos níveis de NH3.',
                'detalhes': 'Recomenda-se revisar aplicação do produto'
            })
    
    # Verificar variabilidade dos dados
    for tratamento in ['DIATEX', 'TESTEMUNHA']:
        dados_trat = df[df['teste'] == tratamento]
        if len(dados_trat) > 0:  # Verificar se há dados para o tratamento
            cv_nh3 = (dados_trat['NH3'].std() / dados_trat['NH3'].mean()) * 100
            
            if cv_nh3 > 50:  # Coeficiente de variação alto
                alertas.append({
                    'tipo': 'info',
                    'titulo': f'Alta Variabilidade - {tratamento}',
                    'mensagem': f'Coeficiente de variação de NH3: {cv_nh3:.1f}%',
                    'detalhes': 'Considerar fatores ambientais que podem estar influenciando'
                })
    
    return alertas
def realizar_teste_t(df, variavel):
    # Separar dados por tratamento
    diatex = df[df['teste'] == 'DIATEX'][variavel].dropna()
    testemunha = df[df['teste'] == 'TESTEMUNHA'][variavel].dropna()
    
    # Verificar se há dados suficientes
    if len(diatex) < 2 or len(testemunha) < 2:
        return {
            'estatistica': None,
            'p_valor': None,
            'significativo': None,
            'interpretacao': 'Dados insuficientes para análise'
        }
    
    # Realizar teste T
    estatistica, p_valor = stats.ttest_ind(diatex, testemunha, equal_var=False)
    
    # Interpretar resultado
    significativo = p_valor < 0.05
    
    if significativo:
        if diatex.mean() > testemunha.mean():
            interpretacao = f"Há diferença significativa (p={p_valor:.4f}). DIATEX apresenta valores de {variavel} MAIORES que TESTEMUNHA."
        else:
            interpretacao = f"Há diferença significativa (p={p_valor:.4f}). DIATEX apresenta valores de {variavel} MENORES que TESTEMUNHA."
    else:
        interpretacao = f"Não há diferença significativa (p={p_valor:.4f}) entre os tratamentos para {variavel}."
    
    return {
        'estatistica': estatistica,
        'p_valor': p_valor,
        'significativo': significativo,
        'interpretacao': interpretacao
    }

# Função para criar matriz de correlação (refatorada)
def criar_matriz_correlacao(df, tratamento=None):
    dados = df.copy()
    
    if tratamento:
        dados = dados[dados['teste'] == tratamento]
    
    # Calcular correlação
    corr = dados[['NH3', 'Temperatura', 'Humedad', 'idade_lote']].corr()
    
    # Criar gráfico com Plotly
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        title=f'Matriz de Correlação {tratamento if tratamento else "Geral"}',
        zmin=-1, zmax=1
    )
    
    return fig

# Título principal
st.title('🐔 Dashboard de Análise DIATEX - Eficácia em Aviários')
st.markdown("""
### Sistema Avançado de Monitoramento e Análise
Este dashboard oferece análise estatística completa da eficácia do produto DIATEX na redução de amônia em aviários.
**DIATEX** é um produto inovador desenvolvido para reduzir a volatilização de amônia durante a criação de frangos de corte.
""")

# Caminho para o banco de dados local no repositório
caminho_db = os.path.join("database", "TESTE_DIATEX_PROD.db")

# Verificar se o arquivo existe
if not os.path.exists(caminho_db):
    st.error(f"Arquivo de banco de dados não encontrado em {caminho_db}.")
    st.info("Verifique se o arquivo está na pasta 'database' do repositório.")
    st.stop()

# Carregar dados
with st.spinner('Carregando dados...'):
    df = carregar_dados(caminho_db)

# Adicionar métricas na sidebar
st.sidebar.markdown("## 📊 Métricas Rápidas")

# Calcular métricas gerais
total_medicoes = len(df)
periodo_total = (df['Fecha'].max() - df['Fecha'].min()).days
aviarios_monitorados = df['aviario'].nunique()
produtores_envolvidos = df['produtor'].nunique()

st.sidebar.metric("Total de Medições", f"{total_medicoes:,}")
st.sidebar.metric("Período (dias)", periodo_total)
st.sidebar.metric("Aviários Monitorados", aviarios_monitorados)
st.sidebar.metric("Produtores", produtores_envolvidos)

# Métricas de eficácia
metricas = calcular_metricas_desempenho(df)
if 'eficacia_nh3' in metricas and metricas['eficacia_nh3'] is not None:
    st.sidebar.metric(
        "Eficácia NH3", 
        f"{metricas['eficacia_nh3']:.1f}%",
        delta=f"{metricas['eficacia_nh3']:.1f}% vs controle"
    )
else:
    st.sidebar.info("Eficácia NH3: Dados insuficientes")

# Exibir informação sobre o arquivo carregado
st.sidebar.markdown("---")
st.sidebar.info(f"📁 **Arquivo:** {os.path.basename(caminho_db)}")
st.sidebar.info(f"🕒 **Última atualização:** {datetime.datetime.fromtimestamp(os.path.getmtime(caminho_db)).strftime('%d/%m/%Y %H:%M')}")

# Sidebar para filtros
st.sidebar.title('Filtros')

# Filtro de produtor
produtores = ['Todos'] + sorted(df['produtor'].dropna().unique().tolist())
filtro_produtor = st.sidebar.selectbox('Produtor', produtores)
if filtro_produtor == 'Todos':
    filtro_produtor = None

# Filtro de linhagem
linhagens = ['Todas'] + sorted(df['linhagem'].dropna().unique().tolist())
filtro_linhagem = st.sidebar.selectbox('Linhagem', linhagens)
if filtro_linhagem == 'Todas':
    filtro_linhagem = None

# Filtro de bateria
baterias = ['Todas'] + sorted(df['bateria_teste'].dropna().unique().tolist())
filtro_bateria = st.sidebar.selectbox('Bateria', baterias)
if filtro_bateria == 'Todas':
    filtro_bateria = None

# Filtro de lote
lotes = ['Todos'] + sorted(df['lote_composto'].dropna().unique().tolist())
filtro_lote = st.sidebar.selectbox('Lote', lotes)
if filtro_lote == 'Todos':
    filtro_lote = None

# Filtro de aviário
aviarios = ['Todos'] + sorted(df['aviario'].dropna().unique().tolist())
filtro_aviario = st.sidebar.selectbox('Aviário', aviarios)
if filtro_aviario == 'Todos':
    filtro_aviario = None

# Filtro de período
min_data = df['Fecha'].min().date()
max_data = df['Fecha'].max().date()
filtro_periodo = st.sidebar.date_input(
    'Período',
    value=(min_data, max_data),
    min_value=min_data,
    max_value=max_data
)

# Aplicar filtro de período
if len(filtro_periodo) == 2:
    df_filtrado_periodo = df[(df['Fecha'].dt.date >= filtro_periodo[0]) & 
                             (df['Fecha'].dt.date <= filtro_periodo[1])]
else:
    df_filtrado_periodo = df

# Filtro de idade com slider
min_idade = int(df['idade_lote'].min())
max_idade = int(df['idade_lote'].max())
st.sidebar.subheader('Idade (dias)')
filtro_idade_range = st.sidebar.slider(
    'Selecione o intervalo de idade',
    min_value=min_idade,
    max_value=max_idade,
    value=(min_idade, max_idade)
)
# Verificar se o slider está no intervalo completo
if filtro_idade_range == (min_idade, max_idade):
    filtro_idade_min, filtro_idade_max = None, None
else:
    filtro_idade_min, filtro_idade_max = filtro_idade_range

# Filtro de semana de vida com slider
min_semana = int(df['semana_vida'].min())
max_semana = int(df['semana_vida'].max())
st.sidebar.subheader('Semana de vida')
filtro_semana_range = st.sidebar.slider(
    'Selecione o intervalo de semanas',
    min_value=min_semana,
    max_value=max_semana,
    value=(min_semana, max_semana)
)
# Verificar se o slider está no intervalo completo
if filtro_semana_range == (min_semana, max_semana):
    filtro_semana_min, filtro_semana_max = None, None
else:
    filtro_semana_min, filtro_semana_max = filtro_semana_range

# Filtro de tratamento para análises específicas
tratamentos = ['Todos', 'DIATEX', 'TESTEMUNHA']
filtro_tratamento_especifico = st.sidebar.selectbox('Tratamento (para análises específicas)', tratamentos)
if filtro_tratamento_especifico == 'Todos':
    filtro_tratamento_especifico = None

# Opção de agrupamento
opcoes_agrupamento = ['dia', 'semana', 'hora']
agrupamento = st.sidebar.radio('Agrupar por', opcoes_agrupamento)

# Exibir estatísticas gerais
st.header('Estatísticas Gerais')

# Aplicar todos os filtros de forma centralizada
dados_filtrados = df_filtrado_periodo.copy()

if filtro_produtor:
    dados_filtrados = dados_filtrados[dados_filtrados['produtor'] == filtro_produtor]
if filtro_linhagem:
    dados_filtrados = dados_filtrados[dados_filtrados['linhagem'] == filtro_linhagem]
if filtro_bateria:
    dados_filtrados = dados_filtrados[dados_filtrados['bateria_teste'] == filtro_bateria]
if filtro_lote:
    dados_filtrados = dados_filtrados[dados_filtrados['lote_composto'] == filtro_lote]
if filtro_aviario:
    dados_filtrados = dados_filtrados[dados_filtrados['aviario'] == filtro_aviario]
if filtro_idade_min is not None and filtro_idade_max is not None:
    dados_filtrados = dados_filtrados[(dados_filtrados['idade_lote'] >= filtro_idade_min) & 
                                     (dados_filtrados['idade_lote'] <= filtro_idade_max)]
if filtro_semana_min is not None and filtro_semana_max is not None:
    dados_filtrados = dados_filtrados[(dados_filtrados['semana_vida'] >= filtro_semana_min) & 
                                     (dados_filtrados['semana_vida'] <= filtro_semana_max)]

# Exibir contagem de registros
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Registros", f"{len(dados_filtrados):,}")
with col2:
    registros_diatex = len(dados_filtrados[dados_filtrados['teste'] == 'DIATEX'])
    st.metric("Registros DIATEX", f"{registros_diatex:,}")
with col3:
    registros_testemunha = len(dados_filtrados[dados_filtrados['teste'] == 'TESTEMUNHA'])
    st.metric("Registros TESTEMUNHA", f"{registros_testemunha:,}")

# Exibir estatísticas descritivas
st.subheader('Estatísticas Descritivas por Tratamento')
estatisticas = dados_filtrados.groupby('teste')[['NH3', 'Temperatura', 'Humedad']].describe()
st.dataframe(estatisticas)

# Seção de Alertas e Recomendações
st.header('🚨 Alertas e Recomendações')
alertas = gerar_alertas(dados_filtrados)

if alertas:
    for alerta in alertas:
        if alerta['tipo'] == 'success':
            st.success(f"**{alerta['titulo']}**: {alerta['mensagem']}")
            st.info(alerta['detalhes'])
        elif alerta['tipo'] == 'warning':
            st.warning(f"**{alerta['titulo']}**: {alerta['mensagem']}")
            st.info(alerta['detalhes'])
        elif alerta['tipo'] == 'error':
            st.error(f"**{alerta['titulo']}**: {alerta['mensagem']}")
            st.info(alerta['detalhes'])
        else:
            st.info(f"**{alerta['titulo']}**: {alerta['mensagem']}")
            if 'detalhes' in alerta:
                st.caption(alerta['detalhes'])
else:
    st.info("Nenhum alerta identificado nos dados atuais.")

# Gráficos comparativos
st.header('Gráficos Comparativos')

# Abas para diferentes variáveis
tab1, tab2, tab3 = st.tabs(["Amônia (NH3)", "Temperatura", "Umidade"])

with tab1:
    st.plotly_chart(
        criar_grafico_comparativo(dados_filtrados, 'NH3', agrupar_por=agrupamento),
        width='stretch'
    )
    resultado_teste_t = realizar_teste_t(dados_filtrados, 'NH3')
    st.subheader('Análise Estatística - Teste T')
    st.write(resultado_teste_t['interpretacao'])
    if resultado_teste_t['p_valor'] is not None:
        fig_box = px.box(dados_filtrados, x='semana_vida', y='NH3', color='teste',
                         title='Distribuição de NH3 por Semana de Vida',
                         labels={'semana_vida': 'Semana de Vida', 'NH3': 'NH3 (ppm)', 'teste': 'Tratamento'},
                         color_discrete_map={'DIATEX': '#1f77b4', 'TESTEMUNHA': '#ff7f0e'})
        st.plotly_chart(fig_box, width='stretch')

with tab2:
    st.plotly_chart(
        criar_grafico_comparativo(dados_filtrados, 'Temperatura', agrupar_por=agrupamento),
        width='stretch'
    )
    resultado_teste_t = realizar_teste_t(dados_filtrados, 'Temperatura')
    st.subheader('Análise Estatística - Teste T')
    st.write(resultado_teste_t['interpretacao'])
    if resultado_teste_t['p_valor'] is not None:
        fig_box = px.box(dados_filtrados, x='semana_vida', y='Temperatura', color='teste',
                         title='Distribuição de Temperatura por Semana de Vida',
                         labels={'semana_vida': 'Semana de Vida', 'Temperatura': 'Temperatura (°C)', 'teste': 'Tratamento'},
                         color_discrete_map={'DIATEX': '#1f77b4', 'TESTEMUNHA': '#ff7f0e'})
        st.plotly_chart(fig_box, width='stretch')

with tab3:
    st.plotly_chart(
        criar_grafico_comparativo(dados_filtrados, 'Humedad', agrupar_por=agrupamento),
        width='stretch'
    )
    resultado_teste_t = realizar_teste_t(dados_filtrados, 'Humedad')
    st.subheader('Análise Estatística - Teste T')
    st.write(resultado_teste_t['interpretacao'])
    if resultado_teste_t['p_valor'] is not None:
        fig_box = px.box(dados_filtrados, x='semana_vida', y='Humedad', color='teste',
                         title='Distribuição de Umidade por Semana de Vida',
                         labels={'semana_vida': 'Semana de Vida', 'Humedad': 'Umidade (%)', 'teste': 'Tratamento'},
                         color_discrete_map={'DIATEX': '#1f77b4', 'TESTEMUNHA': '#ff7f0e'})
        st.plotly_chart(fig_box, width='stretch')

# Análises exploratórias adicionais
st.header('Análises Exploratórias Adicionais')

# Análises Avançadas
st.subheader('📈 Análises Avançadas')

# Criar tabs para diferentes análises
tab_tend, tab_pca, tab_perf = st.tabs(["Análise de Tendências", "Análise PCA", "Métricas de Desempenho"])

with tab_tend:
    st.markdown("#### Análise de Tendências Temporais")
    variavel_tendencia = st.selectbox("Selecione a variável para análise de tendência:", ['NH3', 'Temperatura', 'Humedad'])
    
    tendencias = analisar_tendencias(dados_filtrados, variavel_tendencia)
    
    if tendencias:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'DIATEX' in tendencias:
                tend_diatex = tendencias['DIATEX']
                st.metric(
                    "Tendência DIATEX",
                    tend_diatex['tendencia'].title(),
                    delta=f"R² = {tend_diatex['r_squared']:.3f}"
                )
                if tend_diatex['significativa']:
                    st.success("Tendência estatisticamente significativa")
                else:
                    st.info("Tendência não significativa")
        
        with col2:
            if 'TESTEMUNHA' in tendencias:
                tend_teste = tendencias['TESTEMUNHA']
                st.metric(
                    "Tendência TESTEMUNHA",
                    tend_teste['tendencia'].title(),
                    delta=f"R² = {tend_teste['r_squared']:.3f}"
                )
                if tend_teste['significativa']:
                    st.success("Tendência estatisticamente significativa")
                else:
                    st.info("Tendência não significativa")

with tab_pca:
    st.markdown("#### Análise de Componentes Principais (PCA)")
    st.markdown("Análise multivariada para identificar padrões nos dados.")
    
    df_pca, variance_ratio = realizar_pca(dados_filtrados)
    
    if df_pca is not None:
        fig_pca = px.scatter(
            df_pca, x='PC1', y='PC2', color='teste',
            title='Análise PCA - Separação entre Tratamentos',
            labels={'PC1': f'PC1 ({variance_ratio[0]:.1%} da variância)', 
                   'PC2': f'PC2 ({variance_ratio[1]:.1%} da variância)'},
            color_discrete_map={'DIATEX': '#1f77b4', 'TESTEMUNHA': '#ff7f0e'}
        )
        fig_pca.update_layout(height=500)
        st.plotly_chart(fig_pca, width='stretch')
        
        st.info(f"Os dois primeiros componentes explicam {(variance_ratio[0] + variance_ratio[1]):.1%} da variância total dos dados.")
    else:
        st.warning("Dados insuficientes para análise PCA.")

with tab_perf:
    st.markdown("#### Métricas Detalhadas de Desempenho")
    
    metricas_detalhadas = calcular_metricas_desempenho(dados_filtrados)
    
    if 'DIATEX' in metricas_detalhadas and 'TESTEMUNHA' in metricas_detalhadas:
        # Métricas de NH3
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Redução Média NH3",
                f"{metricas_detalhadas.get('eficacia_nh3', 0):.1f}%",
                delta=f"{metricas_detalhadas['TESTEMUNHA']['nh3_media'] - metricas_detalhadas['DIATEX']['nh3_media']:.2f} ppm"
            )
        
        with col2:
            st.metric(
                "Redução Variabilidade",
                f"{metricas_detalhadas.get('reducao_variabilidade', 0):.1f}%",
                delta=f"{metricas_detalhadas['TESTEMUNHA']['nh3_std'] - metricas_detalhadas['DIATEX']['nh3_std']:.2f} ppm"
            )
        
        with col3:
            st.metric(
                "Comparação Medições",
                f"{metricas_detalhadas['DIATEX']['n_medicoes']:,}",
                delta=f"vs {metricas_detalhadas['TESTEMUNHA']['n_medicoes']:,} controle"
            )
        
        # Tabela comparativa detalhada
        st.markdown("##### Comparação Detalhada")
        df_comparacao = pd.DataFrame({
            'Métrica': ['NH3 Média (ppm)', 'NH3 Desvio Padrão', 'NH3 Mínimo', 'NH3 Máximo', 
                       'Temperatura Média (°C)', 'Umidade Média (%)', 'Número de Medições', 'Dias de Monitoramento'],
            'DIATEX': [
                f"{metricas_detalhadas['DIATEX']['nh3_media']:.2f}",
                f"{metricas_detalhadas['DIATEX']['nh3_std']:.2f}",
                f"{metricas_detalhadas['DIATEX']['nh3_min']:.2f}",
                f"{metricas_detalhadas['DIATEX']['nh3_max']:.2f}",
                f"{metricas_detalhadas['DIATEX']['temp_media']:.1f}",
                f"{metricas_detalhadas['DIATEX']['umid_media']:.1f}",
                f"{metricas_detalhadas['DIATEX']['n_medicoes']:,}",
                f"{metricas_detalhadas['DIATEX']['dias_monitoramento']}"
            ],
            'TESTEMUNHA': [
                f"{metricas_detalhadas['TESTEMUNHA']['nh3_media']:.2f}",
                f"{metricas_detalhadas['TESTEMUNHA']['nh3_std']:.2f}",
                f"{metricas_detalhadas['TESTEMUNHA']['nh3_min']:.2f}",
                f"{metricas_detalhadas['TESTEMUNHA']['nh3_max']:.2f}",
                f"{metricas_detalhadas['TESTEMUNHA']['temp_media']:.1f}",
                f"{metricas_detalhadas['TESTEMUNHA']['umid_media']:.1f}",
                f"{metricas_detalhadas['TESTEMUNHA']['n_medicoes']:,}",
                f"{metricas_detalhadas['TESTEMUNHA']['dias_monitoramento']}"
            ]
        })
        st.dataframe(df_comparacao, width='stretch')

# Matriz de correlação
st.subheader('Matriz de Correlação')
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(
        criar_matriz_correlacao(dados_filtrados, tratamento='DIATEX'),
        width='stretch'
    )

with col2:
    st.plotly_chart(
        criar_matriz_correlacao(dados_filtrados, tratamento='TESTEMUNHA'),
        width='stretch'
    )

# Análise por idade/semana
st.subheader('Análise por Idade/Semana')

visualizacao = st.radio('Visualizar por:', ['Idade (dias)', 'Semana de vida'])

if visualizacao == 'Idade (dias)':
    dados_por_idade = dados_filtrados.groupby(['idade_lote', 'teste'])[['NH3', 'Temperatura', 'Humedad']].mean().reset_index()
    fig = make_subplots(rows=3, cols=1, subplot_titles=('NH3 por Idade', 'Temperatura por Idade', 'Umidade por Idade'),
                        shared_xaxes=True, vertical_spacing=0.1)
    for i, var in enumerate(['NH3', 'Temperatura', 'Humedad']):
        for tratamento in ['DIATEX', 'TESTEMUNHA']:
            dados_trat = dados_por_idade[dados_por_idade['teste'] == tratamento]
            fig.add_trace(go.Scatter(x=dados_trat['idade_lote'], y=dados_trat[var], mode='lines+markers',
                                     name=f'{tratamento} - {var}',
                                     line=dict(color='#1f77b4' if tratamento == 'DIATEX' else '#ff7f0e'),
                                     legendgroup=tratamento, showlegend=(i==0)), row=i+1, col=1)
    fig.update_layout(height=800, title_text='Variáveis por Idade das Aves', legend_title_text='Tratamento')
    st.plotly_chart(fig, width='stretch')
    
else:  # Semana de vida
    dados_por_semana = dados_filtrados.groupby(['semana_vida', 'teste'])[['NH3', 'Temperatura', 'Humedad']].mean().reset_index()
    fig = make_subplots(rows=3, cols=1, subplot_titles=('NH3 por Semana', 'Temperatura por Semana', 'Umidade por Semana'),
                        shared_xaxes=True, vertical_spacing=0.1)
    for i, var in enumerate(['NH3', 'Temperatura', 'Humedad']):
        for tratamento in ['DIATEX', 'TESTEMUNHA']:
            dados_trat = dados_por_semana[dados_por_semana['teste'] == tratamento]
            fig.add_trace(go.Scatter(x=dados_trat['semana_vida'], y=dados_trat[var], mode='lines+markers',
                                     name=f'{tratamento} - {var}',
                                     line=dict(color='#1f77b4' if tratamento == 'DIATEX' else '#ff7f0e'),
                                     legendgroup=tratamento, showlegend=(i==0)), row=i+1, col=1)
    fig.update_layout(height=800, title_text='Variáveis por Semana de Vida das Aves', legend_title_text='Tratamento')
    st.plotly_chart(fig, width='stretch')

# Conclusões e Relatório Final
st.header('📋 Conclusões e Relatório Final')

# Aplicar filtro de tratamento específico para conclusões
dados_conclusoes = dados_filtrados.copy()
if filtro_tratamento_especifico:
    dados_conclusoes = dados_conclusoes[dados_conclusoes['teste'] == filtro_tratamento_especifico]

# Análises estatísticas completas
medias_nh3 = dados_conclusoes.groupby('teste')['NH3'].mean()
medias_temp = dados_conclusoes.groupby('teste')['Temperatura'].mean()
medias_umid = dados_conclusoes.groupby('teste')['Humedad'].mean()

resultado_nh3 = realizar_teste_t(dados_conclusoes, 'NH3')
resultado_temp = realizar_teste_t(dados_conclusoes, 'Temperatura')
resultado_umid = realizar_teste_t(dados_conclusoes, 'Humedad')

if 'DIATEX' in medias_nh3 and 'TESTEMUNHA' in medias_nh3:
    # Métricas principais
    diff_nh3 = ((medias_nh3['DIATEX'] - medias_nh3['TESTEMUNHA']) / medias_nh3['TESTEMUNHA']) * 100
    diff_temp = ((medias_temp['DIATEX'] - medias_temp['TESTEMUNHA']) / medias_temp['TESTEMUNHA']) * 100
    diff_umid = ((medias_umid['DIATEX'] - medias_umid['TESTEMUNHA']) / medias_umid['TESTEMUNHA']) * 100
    
    # Dashboard de métricas finais
    st.subheader("📊 Resumo Executivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Eficácia NH3",
            f"{abs(diff_nh3):.1f}%",
            delta=f"{'Redução' if diff_nh3 < 0 else 'Aumento'}"
        )
    
    with col2:
        st.metric(
            "Diferença Temperatura",
            f"{abs(diff_temp):.1f}%",
            delta=f"{'Menor' if diff_temp < 0 else 'Maior'}"
        )
    
    with col3:
        st.metric(
            "Diferença Umidade", 
            f"{abs(diff_umid):.1f}%",
            delta=f"{'Menor' if diff_umid < 0 else 'Maior'}"
        )
    
    # Análise detalhada
    st.subheader("📈 Análise Detalhada")
    
    st.markdown(f"""
    ### 🎯 Resultados Principais
    
    #### **Amônia (NH3) - Variável Principal**
    - **DIATEX**: {medias_nh3['DIATEX']:.2f} ppm (média)
    - **TESTEMUNHA**: {medias_nh3['TESTEMUNHA']:.2f} ppm (média)
    - **Diferença**: {diff_nh3:.2f}% ({medias_nh3['DIATEX'] - medias_nh3['TESTEMUNHA']:.2f} ppm)
    - **Análise Estatística**: {resultado_nh3['interpretacao']}
    
    #### **Temperatura**
    - **DIATEX**: {medias_temp['DIATEX']:.1f}°C (média)
    - **TESTEMUNHA**: {medias_temp['TESTEMUNHA']:.1f}°C (média)
    - **Diferença**: {diff_temp:.2f}%
    - **Análise Estatística**: {resultado_temp['interpretacao']}
    
    #### **Umidade**
    - **DIATEX**: {medias_umid['DIATEX']:.1f}% (média)
    - **TESTEMUNHA**: {medias_umid['TESTEMUNHA']:.1f}% (média)
    - **Diferença**: {diff_umid:.2f}%
    - **Análise Estatística**: {resultado_umid['interpretacao']}
    """)
    
    # Conclusão final baseada em critérios rigorosos
    st.subheader("🏆 Conclusão Final")
    
    # Critérios de avaliação
    eficacia_significativa = resultado_nh3['significativo'] and diff_nh3 < -5  # Redução de pelo menos 5%
    eficacia_moderada = resultado_nh3['significativo'] and -5 <= diff_nh3 < 0
    ineficaz = resultado_nh3['significativo'] and diff_nh3 >= 0
    inconclusivo = not resultado_nh3['significativo']
    
    if eficacia_significativa:
        st.success(f"""
        ### ✅ DIATEX DEMONSTRA EFICÁCIA SIGNIFICATIVA
        
        **Principais achados:**
        - Redução estatisticamente significativa de {abs(diff_nh3):.1f}% nos níveis de NH3
        - P-valor: {resultado_nh3['p_valor']:.4f} (< 0.05)
        - Benefício claro para o ambiente aviário
        
        **Recomendação:** Implementação do produto DIATEX é recomendada.
        """)
    elif eficacia_moderada:
        st.warning(f"""
        ### ⚠️ DIATEX APRESENTA EFICÁCIA MODERADA
        
        **Principais achados:**
        - Redução estatisticamente significativa de {abs(diff_nh3):.1f}% nos níveis de NH3
        - P-valor: {resultado_nh3['p_valor']:.4f} (< 0.05)
        - Benefício presente, mas limitado
        
        **Recomendação:** Considerar implementação com monitoramento contínuo.
        """)
    elif ineficaz:
        st.error(f"""
        ### ❌ DIATEX NÃO DEMONSTRA EFICÁCIA
        
        **Principais achados:**
        - Aumento de {abs(diff_nh3):.1f}% nos níveis de NH3 vs controle
        - P-valor: {resultado_nh3['p_valor']:.4f} (< 0.05)
        - Produto não atende aos objetivos
        
        **Recomendação:** Não implementar o produto. Revisar formulação ou aplicação.
        """)
    else:
        st.info(f"""
        ### 🤔 RESULTADOS INCONCLUSIVOS
        
        **Principais achados:**
        - Diferença de {diff_nh3:.1f}% nos níveis de NH3 (não significativa)
        - P-valor: {resultado_nh3['p_valor']:.4f} (≥ 0.05)
        - Dados insuficientes para conclusão definitiva
        
        **Recomendação:** Coletar mais dados ou revisar protocolo experimental.
        """)
    
    # Contexto adicional
    st.subheader("📋 Considerações Adicionais")
    n_total = len(dados_conclusoes)
    periodo_estudo = (dados_conclusoes['Fecha'].max() - dados_conclusoes['Fecha'].min()).days
    
    st.markdown(f"""
    - **Tamanho da amostra**: {n_total:,} medições
    - **Período de estudo**: {periodo_estudo} dias
    - **Aviários monitorados**: {dados_conclusoes['aviario'].nunique()}
    - **Produtores envolvidos**: {dados_conclusoes['produtor'].nunique()}
    - **Linhagens testadas**: {dados_conclusoes['linhagem'].nunique()}
    """)
    
else:
    st.warning("❌ **Dados insuficientes para conclusões finais.**")
    st.markdown("*Requer dados de ambos os tratamentos (DIATEX e TESTEMUNHA) para análise comparativa.*")

# Rodapé aprimorado
agora_gmt3 = datetime.datetime.now() - timedelta(hours=3)
st.markdown("---")

# Seção de exportação de dados
st.subheader("📁 Exportar Dados")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Exportar Dados Filtrados"):
        csv = dados_filtrados.to_csv(index=False)
        st.download_button(
            label="Baixar CSV",
            data=csv,
            file_name=f"dados_diatex_filtrados_{datetime.date.today()}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📈 Exportar Estatísticas"):
        stats_csv = estatisticas.to_csv()
        st.download_button(
            label="Baixar Estatísticas CSV",
            data=stats_csv,
            file_name=f"estatisticas_diatex_{datetime.date.today()}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("📋 Gerar Relatório"):
        st.info("Funcionalidade de relatório em PDF será implementada em breve.")

# Informações do sistema
st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-top: 20px;">
<h4>ℹ️ Informações do Sistema</h4>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
<div>
<strong>📊 Dados:</strong><br>
• Última atualização: {agora_gmt3.strftime('%d/%m/%Y %H:%M')} (GMT-3)<br>
• Banco de dados: {os.path.basename(caminho_db)}<br>
• Total de registros: {len(df):,}<br>
• Período de dados: {df['Fecha'].min().strftime('%d/%m/%Y')} a {df['Fecha'].max().strftime('%d/%m/%Y')}
</div>

<div>
<strong>🔧 Tecnologias:</strong><br>
• Streamlit {st.__version__}<br>
• Python para análise estatística<br>
• Plotly para visualizações interativas<br>
• SQLite para persistência de dados
</div>
</div>

<div style="text-align: center; margin-top: 15px; color: #666;">
<strong>Dashboard de Análise DIATEX</strong> - Sistema de monitoramento de eficácia em aviários<br>
Desenvolvido para análise científica e tomada de decisões baseada em dados
</div>
</div>
""", unsafe_allow_html=True)

# Sidebar com informações adicionais
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Funcionalidades")
st.sidebar.markdown("""
**✅ Análises Disponíveis:**
- Estatísticas descritivas
- Testes de significância (Teste T)
- Análise de tendências temporais
- Análise PCA multivariada
- Correlações entre variáveis
- Alertas automáticos

**📊 Visualizações:**
- Gráficos de linha temporais
- Box plots por semana
- Scatter plots PCA
- Matrizes de correlação
- Métricas de desempenho
""")

st.sidebar.markdown("---")
st.sidebar.info("""
**💡 Versão Aprimorada**

Esta versão inclui:
• Análises estatísticas avançadas
• Sistema de alertas inteligente  
• Métricas de desempenho detalhadas
• Interface melhorada
• Exportação de dados

Acesse os dados diretamente do repositório GitHub.
""")

# Link para documentação (se disponível)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Recursos")
st.sidebar.markdown("""
- [Documentação](https://github.com/seu-usuario/testeDiatexCama)
- [Reportar Bug](https://github.com/seu-usuario/testeDiatexCama/issues)
- [Código Fonte](https://github.com/seu-usuario/testeDiatexCama)
""")