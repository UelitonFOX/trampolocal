import os
import requests
import pandas as pd
from dotenv import load_dotenv
from utils.helpers import categorize_sector, informality_rate_mapping

# Carrega variáveis de ambiente
load_dotenv()
API_KEY = os.getenv("SERPER_API_KEY")

def fetch_jobs_serper(query: str) -> pd.DataFrame:
    """
    Consulta a API da Serper.dev e retorna vagas formatadas em um DataFrame.
    
    :param query: Texto da busca (ex: "vagas de emprego Jardim Alegre")
    :return: DataFrame com as vagas formatadas
    """
    if not API_KEY:
        raise ValueError("❌ API key não encontrada. Verifique o arquivo .env.")

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
        response.raise_for_status()
        results = response.json().get("organic", [])

        data = []
        for item in results:
            job_title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")

            sector = categorize_sector(job_title, snippet)
            rate = informality_rate_mapping.get(sector, 20)

            data.append({
                "Neighborhood": "Centro",  # por enquanto fixo
                "Economic Sector": sector,
                "Job Count": 1,
                "Informality Rate (%)": rate,
                "Job Title": job_title,
                "Snippet": snippet,
                "Link": link,
                "Salary": "Não informado"
            })

        df = pd.DataFrame(data)
        df.drop_duplicates(subset=["Job Title", "Snippet"], inplace=True)
        return df

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erro ao acessar a API Serper.dev: {e}")
