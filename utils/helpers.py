# utils/helpers.py

# Dicionário com palavras-chave para categorizar o setor econômico
sector_keywords = {
    "Indústria": ["indústria", "produção", "fábrica"],
    "Comércio": ["vendas", "comércio", "loja"],
    "Serviços Gerais": ["serviços gerais", "limpeza", "manutenção"],
    "Saúde": ["saúde", "hospital", "clínica"],
    "Construção Civil": ["construção", "construtor", "obra"]
}

# Taxa média de informalidade por setor
informality_rate_mapping = {
    "Indústria": 10,
    "Comércio": 40,
    "Serviços Gerais": 50,
    "Saúde": 15,
    "Construção Civil": 30,
    "Outros": 20
}

def categorize_sector(job_title: str, snippet: str) -> str:
    """
    Classifica a vaga em um setor econômico com base no título e resumo.
    
    :param job_title: Título da vaga
    :param snippet: Resumo ou descrição da vaga
    :return: Nome do setor econômico
    """
    text = f"{job_title} {snippet}".lower()
    for sector, keywords in sector_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return sector
    return "Outros"
