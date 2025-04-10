import streamlit as st
import pandas as pd
import plotly.express as px

# Mova st.set_page_config para o início do script
st.set_page_config(layout="wide")

# CSS customizado com cores da identidade visual
st.markdown("""
    <style>
        .main, .stApp {
            background-color: #F7F9FA;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #19286E;
        }
        .stTabs [role="tab"] {
            background-color: #00B3A7;
            color: white;
            border-radius: 5px 5px 0 0;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background-color: #19286E;
            color: white;
        }
        .stMetricLabel, .stMetricValue {
            color: #19286E;
        }
        .css-1d391kg {  /* sidebar header */
            color: #4B7BF5 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Paleta de Cores da Editora
cores_marca = ['#93C83D', '#00B3A7', '#19286E', '#4B7BF5']

colunas_mapping = {
    'ano_censo': 'Ano do Censo',
    'regiao': 'Região',
    'uf': 'UF',
    'municipio': 'Município',
    'co_entidade': 'Código da Escola',
    'dependencia': 'Dependência Administrativa',
    'categoria_escola_privada': 'Categoria Escola Privada',
    'local_func_socioeducativo': 'Local Func. Socioeducativo',
    'esola_sistema_s': 'Escola Sistema S',
    'acesso_internet_alunos_computador': 'Acesso Internet Alunos',
    'qt_docentes_total': 'Total Docentes',
    'alunado_total_edb': 'Total Alunos Educação Básica',
    'qt_docentes_educacao_infantil': 'Docentes Educação Infantil',
    'qt_docentes_ensino_fundamental': 'Docentes Ensino Fundamental',
    'qt_docentes_ensino_medio': 'Docentes Ensino Médio',
    'qt_mat_educacao_infantil': 'Matrículas Educação Infantil',
    'qt_mat_ensino_fundamental_anos_iniciais': 'Matrículas Fund. Anos Iniciais',
    'qt_mat_ensino_fundamental_anos_finais': 'Matrículas Fund. Anos Finais',
    'qt_mat_ensino_medio': 'Matrículas Ensino Médio'
}

# Função para transformar colunas binárias (assumindo que já estão em 0 e 1)
def transformar_binario_em_sim_nao(df, colunas):
    for coluna in colunas:
        if coluna in df.columns:
            df[coluna] = df[coluna].replace({1: 'Sim', 0: 'Não'})
    return df

@st.cache_data

def carregar_dados(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep=";", encoding="latin1")
        df.rename(columns=colunas_mapping, inplace=True)

        colunas_binarias = ['Local Func. Socioeducativo', 'Escola Sistema S', 'Acesso Internet Alunos']
        df = transformar_binario_em_sim_nao(df, colunas_binarias)
        return df
    else:
        return pd.DataFrame()

# Upload do arquivo via Streamlit
uploaded_file = st.sidebar.file_uploader("📁 Envie sua base de dados (.csv)", type=["csv"])
df = carregar_dados(uploaded_file)

if df.empty:
    st.warning("Por favor, envie um arquivo CSV para começar.")
    st.stop()

# Filtros laterais
st.sidebar.header("Filtros")
regioes = st.sidebar.multiselect("Região", options=df["Região"].unique())
ufs = st.sidebar.multiselect("UF", options=df["UF"].unique())
municipios = st.sidebar.multiselect("Município", options=df["Município"].unique())
dependencias = st.sidebar.multiselect("Dependência Administrativa", options=df["Dependência Administrativa"].unique())
categoria_privada = st.sidebar.multiselect("Categoria Escola Privada", options=df["Categoria Escola Privada"].unique())

# Aplicar filtros
df_filtrado = df.copy()
if regioes:
    df_filtrado = df_filtrado[df_filtrado["Região"].isin(regioes)]
if ufs:
    df_filtrado = df_filtrado[df_filtrado["UF"].isin(ufs)]
if municipios:
    df_filtrado = df_filtrado[df_filtrado["Município"].isin(municipios)]
if dependencias:
    df_filtrado = df_filtrado[df_filtrado["Dependência Administrativa"].isin(dependencias)]
if categoria_privada:
    df_filtrado = df_filtrado[df_filtrado["Categoria Escola Privada"].isin(categoria_privada)]

# Painel
st.title("Análise do Censo Escolar")

aba1, aba2, aba3 = st.tabs(["Escolas", "Alunado", "Docentes"])

with aba1:
    st.header("Número de Escolas por Região")
    escolas_por_regiao = df_filtrado.groupby("Região")["Código da Escola"].nunique().reset_index()
    fig_bar = px.bar(escolas_por_regiao, x="Região", y="Código da Escola",
                    title="Total de Escolas por Região",
                    labels={"Código da Escola": "Número de Escolas"},
                    color_discrete_sequence=[cores_marca[2]])
    st.plotly_chart(fig_bar, use_container_width=True)

    regioes_coords = {
        'Norte': (-3.07, -60.02),
        'Nordeste': (-9.65, -35.71),
        'Sudeste': (-22.90, -43.20),
        'Sul': (-27.60, -48.55),
        'Centro-Oeste': (-15.60, -56.10)
    }
    escolas_por_regiao['lat'] = escolas_por_regiao['Região'].map(lambda x: regioes_coords.get(x, (0, 0))[0])
    escolas_por_regiao['lon'] = escolas_por_regiao['Região'].map(lambda x: regioes_coords.get(x, (0, 0))[1])

    fig_mapa = px.density_mapbox(escolas_por_regiao, lat='lat', lon='lon', z='Código da Escola', radius=60,
                                 center=dict(lat=-15.5, lon=-51.0), zoom=3.5,
                                 mapbox_style="carto-positron",
                                 title="Mapa de Calor - Número de Escolas por Região")
    st.plotly_chart(fig_mapa, use_container_width=True)

with aba2:
    st.header("Distribuição do Alunado por Nível de Ensino")

    if "Total Alunos Educação Básica" in df_filtrado.columns:
        total_alunos = df_filtrado["Total Alunos Educação Básica"].sum()
        st.metric("Total de Alunos da Educação Básica", f"{total_alunos:,}".replace(",", "."))

    niveis = {
        'Matrículas Educação Infantil': 'Educação Infantil',
        'Matrículas Fund. Anos Iniciais': 'Fundamental - Iniciais',
        'Matrículas Fund. Anos Finais': 'Fundamental - Finais',
        'Matrículas Ensino Médio': 'Ensino Médio'
    }
    mat_df = df_filtrado[list(niveis.keys())].sum().rename(niveis).reset_index(name='Matrículas')
    fig = px.pie(mat_df, names='index', values='Matrículas', title="Distribuição por Nível de Ensino", hole=0.3,
                 color_discrete_sequence=cores_marca)
    st.plotly_chart(fig, use_container_width=True)

    if "Total Alunos Educação Básica" in df_filtrado.columns:
        alunos_uf = df_filtrado.groupby("UF")["Total Alunos Educação Básica"].sum().reset_index()
        fig_uf = px.bar(alunos_uf, x="UF", y="Total Alunos Educação Básica",
                        title="Total de Alunos da Educação Básica por UF",
                        labels={"Total Alunos Educação Básica": "Total de Alunos"},
                        color_discrete_sequence=[cores_marca[0]])
        st.plotly_chart(fig_uf, use_container_width=True)

with aba3:
    st.header("Perfil dos Docentes")
    niveis_doc = {
        'Docentes Educação Infantil': 'Educação Infantil',
        'Docentes Ensino Fundamental': 'Fundamental',
        'Docentes Ensino Médio': 'Ensino Médio'
    }
    doc_df = df_filtrado[list(niveis_doc.keys())].sum().rename(niveis_doc).reset_index(name='Docentes')
    fig = px.bar(doc_df, x='index', y='Docentes', title="Total de Docentes por Etapa",
                 labels={'index': 'Etapa de Ensino', 'Docentes': 'Quantidade'},
                 color_discrete_sequence=[cores_marca[1]])
    st.plotly_chart(fig, use_container_width=True)

    if 'Total Docentes' in df_filtrado.columns:
        total_doc = df_filtrado['Total Docentes'].sum()
        st.metric("Total de Docentes na Amostra", f"{total_doc:,}".replace(",", "."))

