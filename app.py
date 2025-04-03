import os
import base64
import re
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()
API_KEY = os.getenv("SERPER_API_KEY")

# Configuração da página e definição do tema
st.set_page_config(page_title="TrampoLocal - Radar de Oportunidades", layout="centered")
st.markdown(
    """
    <style>
    .stApp {
        background-color: #444444; /* Fundo escuro */
        color: #FFFFFF;            /* Texto branco */
    }
    a {
        color: #61dafb; /* Cor dos links */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Exibir logo utilizando base64
logo_filename = "logo_trampolocal.png"
current_dir = os.path.dirname(__file__)
logo_path = os.path.join(current_dir, "assets", logo_filename)

if os.path.exists(logo_path):
    try:
        with open(logo_path, "rb") as image_file:
            encoded_logo = base64.b64encode(image_file.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style='text-align: center;'>
                <img src="data:image/png;base64,{encoded_logo}" width="200">
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Erro ao carregar a logo: {e}")
else:
    st.error(f"Arquivo de logo não encontrado: {logo_path}")

# Título e subtítulo
st.title("TrampoLocal - Radar de Oportunidades")
st.subheader("Mapa digital das áreas com mais empregos no município (dados em tempo real)")

# Dicionários para categorização e taxa de informalidade
sector_keywords = {
    "Indústria": ["indústria", "produção", "fábrica"],
    "Comércio": ["vendas", "comércio", "loja"],
    "Serviços Gerais": ["serviços gerais", "limpeza", "manutenção"],
    "Saúde": ["saúde", "hospital", "clínica"],
    "Construção Civil": ["construção", "construtor", "obra"]
}
informality_rate_mapping = {
    "Indústria": 10,
    "Comércio": 40,
    "Serviços Gerais": 50,
    "Saúde": 15,
    "Construção Civil": 30,
    "Outros": 20
}

# Função para categorizar o setor econômico baseado no título e resumo da vaga
def categorize_sector(job_title, snippet):
    text = f"{job_title} {snippet}".lower()
    for sector, keywords in sector_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return sector
    return "Outros"

# Função para limpar e padronizar salários (placeholder, pois a API não fornece salário)
def parse_salary(salary_str):
    salary_str = salary_str.replace(" ", "").replace(",", ".")
    match = re.search(r'(\d+(\.\d+)?)', salary_str)
    if match:
        return float(match.group(1))
    return None

# Função para buscar vagas utilizando a API Serper.dev
def fetch_jobs_serper(query):
    if not API_KEY:
        st.error("A chave da API não foi encontrada. Verifique se o arquivo .env está configurado corretamente.")
        return None

    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "gl": "br",
        "hl": "pt-BR"
    }
    
    try:
        response = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
        if response.status_code == 200:
            results = response.json().get("organic", [])
            data = []
            for item in results:
                job_title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                
                # Categorização automática do setor econômico
                economic_sector = categorize_sector(job_title, snippet)
                informality_rate = informality_rate_mapping.get(economic_sector, 20)
                
                # Placeholder para salário (a API não fornece essa informação)
                salary = "Não informado"
                
                data.append({
                    "Neighborhood": "Centro",  # Valor fixo por enquanto; aprimorável com dados reais
                    "Economic Sector": economic_sector,
                    "Job Count": 1,
                    "Informality Rate (%)": informality_rate,
                    "Job Title": job_title,
                    "Snippet": snippet,
                    "Link": link,
                    "Salary": salary
                })
            df_jobs = pd.DataFrame(data)
            # Remover vagas duplicadas com base em Título e Resumo
            df_jobs.drop_duplicates(subset=["Job Title", "Snippet"], inplace=True)
            return df_jobs
        else:
            st.error(f"Erro ao buscar dados da API. Status Code: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# Cache dos resultados para evitar requisições repetidas
@st.cache_data(show_spinner=False)
def get_jobs(query):
    return fetch_jobs_serper(query)

# Busca automática dos dados
st.info("Buscando vagas reais de Jardim Alegre e região...")
query_string = "vagas de emprego Jardim Alegre PR OR Ivaiporã site:bne.com.br OR site:portaljulianobarbosa.com.br"
df = get_jobs(query_string)

# Filtros personalizados na barra lateral
if df is not None and not df.empty:
    st.sidebar.header("Filtros de Busca")
    sectors = ["Todos"] + sorted(df["Economic Sector"].unique().tolist())
    selected_sector = st.sidebar.selectbox("Setor Econômico", sectors)
    neighborhoods = ["Todos"] + sorted(df["Neighborhood"].unique().tolist())
    selected_neighborhood = st.sidebar.selectbox("Bairro", neighborhoods)
    title_filter = st.sidebar.text_input("Buscar por Cargo/Título")
    
    # Aplicar filtros
    df_filtered = df.copy()
    if selected_sector != "Todos":
        df_filtered = df_filtered[df_filtered["Economic Sector"] == selected_sector]
    if selected_neighborhood != "Todos":
        df_filtered = df_filtered[df_filtered["Neighborhood"] == selected_neighborhood]
    if title_filter:
        df_filtered = df_filtered[df_filtered["Job Title"].str.contains(title_filter, case=False)]
else:
    df_filtered = df

# Exibir dados carregados
if df_filtered is not None and not df_filtered.empty:
    st.markdown("### Dados Carregados")
    st.dataframe(df_filtered)
    
    # Análise por setor econômico
    st.markdown("## Setores que mais empregam")
    df_sector = df_filtered.groupby("Economic Sector")["Job Count"].sum().reset_index()
    df_sector = df_sector.sort_values(by="Job Count", ascending=False)
    
    fig_bar = px.bar(
        df_sector,
        x="Economic Sector",
        y="Job Count",
        title="Gráfico de Barras - Número de Vagas por Setor",
        labels={"Job Count": "Número de Vagas", "Economic Sector": "Setor Econômico"}
    )
    st.plotly_chart(fig_bar)
    
    # Gráfico de pizza para distribuição por setor
    st.markdown("## Distribuição dos Empregos por Setor")
    fig_pie = px.pie(
        df_sector,
        names="Economic Sector",
        values="Job Count",
        title="Gráfico de Pizza - Distribuição por Setor"
    )
    st.plotly_chart(fig_pie)
    
    # Informalidade por bairro
    st.markdown("## Informalidade por Bairro")
    df_neighborhood = df_filtered.groupby("Neighborhood")["Informality Rate (%)"].mean().reset_index()
    df_neighborhood = df_neighborhood.sort_values(by="Informality Rate (%)", ascending=False)
    st.dataframe(df_neighborhood)
    
    # Exibir detalhes das vagas com informações, contatos e links (abrir em nova aba)
    st.markdown("## Detalhes das Vagas")
    for idx, row in df_filtered.iterrows():
        st.markdown(f"**Título:** {row['Job Title']}")
        st.markdown(f"**Setor Econômico:** {row['Economic Sector']}")
        st.markdown(f"**Taxa de Informalidade:** {row['Informality Rate (%)']}%")
        st.markdown(f"**Resumo:** {row['Snippet']}")
        st.markdown(f"**Salário:** {row['Salary']}")
        st.markdown(f"[Acessar Vaga ➚]({row['Link']})", unsafe_allow_html=True)
        st.markdown("---")
    
    # Ranking de Vagas - Top 5 (exemplo simples: primeiras 5 vagas)
    st.markdown("## Top 5 Vagas")
    top5 = df_filtered.head(5)
    for idx, row in top5.iterrows():
        st.markdown(f"**Título:** {row['Job Title']}")
        st.markdown(f"**Setor:** {row['Economic Sector']}")
        st.markdown(f"[Acessar Vaga ➚]({row['Link']})", unsafe_allow_html=True)
        st.markdown("---")
else:
    st.warning("Nenhuma vaga encontrada no momento. Tente novamente mais tarde.")

# Rodapé com informações do Talento Tech
st.markdown("---")
st.markdown(
    "<div style='text-align: center;'>Desenvolvido por alunos do Talento Tech – UEPG | Eixo: Emprego e Economia | Área: Desenvolvimento de Software | 2025</div>",
    unsafe_allow_html=True
)
