import streamlit as st
import base64
import os
from config.style import DARK_THEME_CSS
from services.api import fetch_jobs_serper

# Configuração da página
st.set_page_config(page_title="TrampoLocal - Radar de Oportunidades", layout="centered")

# Aplica o tema escuro
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Exibe a logo (centralizado via base64)
def load_logo():
    logo_path = os.path.join("assets", "logo_trampolocal.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img:
            encoded = base64.b64encode(img.read()).decode()
            st.markdown(f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded}' width='200'></div>", unsafe_allow_html=True)
    else:
        st.warning("Logo não encontrada.")

load_logo()

st.title("TrampoLocal - Radar de Oportunidades")
st.subheader("Mapa digital das áreas com mais empregos no município (dados em tempo real)")

@st.cache_data(show_spinner=False)
def get_jobs():
    query = "vagas de emprego Jardim Alegre PR OR Ivaiporã site:bne.com.br OR site:portaljulianobarbosa.com.br"
    return fetch_jobs_serper(query)

st.info("Buscando vagas reais de Jardim Alegre e região...")
df = get_jobs()

# Filtros personalizados na barra lateral
if df is not None and not df.empty:
    st.sidebar.header("🎯 Filtros de Busca")

    sectors = ["Todos"] + sorted(df["Economic Sector"].unique())
    selected_sector = st.sidebar.selectbox("Setor Econômico", sectors)

    neighborhoods = ["Todos"] + sorted(df["Neighborhood"].unique())
    selected_neighborhood = st.sidebar.selectbox("Bairro", neighborhoods)

    title_filter = st.sidebar.text_input("Buscar por Cargo/Título")

    # Aplicar os filtros
    df_filtered = df.copy()
    if selected_sector != "Todos":
        df_filtered = df_filtered[df_filtered["Economic Sector"] == selected_sector]
    if selected_neighborhood != "Todos":
        df_filtered = df_filtered[df_filtered["Neighborhood"] == selected_neighborhood]
    if title_filter:
        df_filtered = df_filtered[df_filtered["Job Title"].str.contains(title_filter, case=False)]
else:
    df_filtered = df

# Exibição dos dados filtrados
if df_filtered is not None and not df_filtered.empty:
    st.markdown("## 📋 Dados Carregados")
    st.dataframe(df_filtered)

    # Gráfico de barras por setor
    st.markdown("## 📊 Setores que mais empregam")
    import plotly.express as px
    df_sector = df_filtered.groupby("Economic Sector")["Job Count"].sum().reset_index()
    df_sector = df_sector.sort_values(by="Job Count", ascending=False)
    fig_bar = px.bar(df_sector, x="Economic Sector", y="Job Count", title="Número de Vagas por Setor")
    st.plotly_chart(fig_bar)

    # Gráfico de pizza
    st.markdown("## 🥧 Distribuição dos Empregos por Setor")
    fig_pie = px.pie(df_sector, names="Economic Sector", values="Job Count", title="Distribuição por Setor")
    st.plotly_chart(fig_pie)

    # Informalidade por bairro
    st.markdown("## ⚠️ Informalidade por Bairro")
    df_neighborhood = df_filtered.groupby("Neighborhood")["Informality Rate (%)"].mean().reset_index()
    st.dataframe(df_neighborhood)

    # Top 5 vagas
    st.markdown("## ⭐ Top 5 Vagas")
    top5 = df_filtered.head(5)
    for idx, row in top5.iterrows():
        st.markdown(f"**Título:** {row['Job Title']}")
        st.markdown(f"**Setor:** {row['Economic Sector']}")
        st.markdown

# Rodapé institucional
st.markdown("---")
st.markdown(
    "<div style='text-align: center;'>Desenvolvido por alunos do Talento Tech – UEPG | Eixo: Emprego e Economia | Área: Desenvolvimento de Software | 2025</div>",
    unsafe_allow_html=True
)
