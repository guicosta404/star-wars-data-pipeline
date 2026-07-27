"""
Camada gold:
- recebe tabela de personagens enriquecidos (silver)
- garante tipos corretos
- renomeia colunas para nomes amigáveis ao BI
- dropa colunas desnecessárias
- gera tabela principal para o dashboard
- gera agregações bônus (por planeta, espécie, gênero)
"""

import os
import pandas as pd

SILVER_DIR = "silver"
GOLD_DIR = "gold"


def ensure_dirs():
    os.makedirs(GOLD_DIR, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()

    # carrega tabela enriquecida da silver
    df = pd.read_csv(os.path.join(SILVER_DIR, "personagens_enriquecidos_silver.csv"))
    
    # renomeia colunas e dropa colunas desnecessárias
    
    df_gold = (
        df
        .drop(columns=["nome_personagem_original", "nome_personagem_norm"])
        .rename(columns={
            "nome_personagem_swapi": "nome_personagem",
            "planeta_natal": "planeta_natal",
            "especie": "especie",
            "genero": "genero",
            "altura": "altura_cm",
            "massa": "massa_kg",
            "quantidade_filmes": "qtd_filmes",
            "quantidade_naves": "qtd_naves_distintas",
            "quantidade_solicitacoes": "qtd_solicitacoes",
            "unidades_vendidas": "unidades_vendidas_total",
            "receita_reais": "receita_total_reais",
        })
    )

    # garantir tipos numéricos consistentes
    df_gold["altura_cm"] = pd.to_numeric(df_gold["altura_cm"], errors="coerce")
    df_gold["massa_kg"] = pd.to_numeric(df_gold["massa_kg"], errors="coerce")
    df_gold["qtd_filmes"] = df_gold["qtd_filmes"].astype(int)
    df_gold["qtd_naves_distintas"] = df_gold["qtd_naves_distintas"].astype(int)
    df_gold["qtd_solicitacoes"] = df_gold["qtd_solicitacoes"].astype(int)
    df_gold["unidades_vendidas_total"] = df_gold["unidades_vendidas_total"].astype(int)
    df_gold["receita_total_reais"] = df_gold["receita_total_reais"].astype(float)
    
    # tabela principal gold
    df_gold.to_csv(os.path.join(GOLD_DIR, "personagens_dashboard_gold.csv"), index=False)

    # agregações bônus para o analista de BI
    resumo_planeta = df_gold.groupby("planeta_natal").size().reset_index(name="qtd_personagens")
    resumo_especie = df_gold.groupby("especie").size().reset_index(name="qtd_personagens")
    resumo_genero = df_gold.groupby("genero").size().reset_index(name="qtd_personagens")

    resumo_planeta.to_csv(os.path.join(GOLD_DIR, "resumo_por_planeta.csv"), index=False)
    resumo_especie.to_csv(os.path.join(GOLD_DIR, "resumo_por_especie.csv"), index=False)
    resumo_genero.to_csv(os.path.join(GOLD_DIR, "resumo_por_genero.csv"), index=False)
