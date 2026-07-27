# silver_transform.py
"""
Camada silver:
- limpa problemas de qualidade das planilhas
- normaliza nomes, datas e valores monetários
- constrói tabela de personagens a partir da SWAPI
- cruza com vendas por nome normalizado
- registra personagens não encontrados na SWAPI
"""

import os
import json
import pandas as pd

from utils import normalize_name, normalize_money, normalize_month_year

BRONZE_DIR = "bronze"
SILVER_DIR = "silver"


#------------------------
# Infra básica de pastas
#------------------------
def ensure_dirs():
    os.makedirs(SILVER_DIR, exist_ok=True)


#-------------------------
# Carrega dados da bronz
#-------------------------
def load_bronze():
    personagens = pd.read_csv(os.path.join(BRONZE_DIR, "personagens_solicitados_raw.csv"))
    vendas = pd.read_csv(os.path.join(BRONZE_DIR, "vendas_produtos_raw.csv"))

    with open(os.path.join(BRONZE_DIR, "swapi_people_raw.json"), encoding="utf-8") as f:
        people_raw = json.load(f)
    with open(os.path.join(BRONZE_DIR, "swapi_planets_raw.json"), encoding="utf-8") as f:
        planets_raw = json.load(f)
    with open(os.path.join(BRONZE_DIR, "swapi_species_raw.json"), encoding="utf-8") as f:
        species_raw = json.load(f)
    with open(os.path.join(BRONZE_DIR, "swapi_films_raw.json"), encoding="utf-8") as f:
        films_raw = json.load(f)
    with open(os.path.join(BRONZE_DIR, "swapi_starships_raw.json"), encoding="utf-8") as f:
        starships_raw = json.load(f)

    return personagens, vendas, people_raw, planets_raw, species_raw, films_raw, starships_raw


# ----------------------------------
# Limpeza da planilha de personagens
# ----------------------------------
def clean_personagens(personagens: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa a planilha de personagens:
    - mantém coluna original de nome
    - cria coluna de nome normalizado
    - remove linhas sem nome
    - remove duplicatas por nome normalizado
    """
    df = personagens.copy()

    # descarta linhas sem nome
    df = df[df["nome_personagem"].notna()]

    df["nome_personagem_original"] = df["nome_personagem"]
    df["nome_personagem_norm"] = df["nome_personagem"].astype(str).map(normalize_name)

    # remove duplicatas por nome normalizado (mantém primeira ocorrência)
    df = df.drop_duplicates(subset=["nome_personagem_norm"])

    return df


# -----------------------------
# Limpeza da planilha de vendas
# -----------------------------
def clean_vendas(vendas: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa a planilha de vendas:
    - normaliza nome de personagem
    - converte unidades_vendidas para número (tratando texto como "cem")
    - converte receita_reais para float (tratando R$, vírgula, ponto)
    - normaliza mes_referencia para datetime (mês/ano)
    """
    df = vendas.copy()

    df["nome_personagem_original"] = df["nome_personagem"]
    df["nome_personagem_norm"] = df["nome_personagem"].astype(str).map(normalize_name)
    df = df.drop_duplicates(subset=[
            "nome_personagem_original",
            "nome_personagem_norm",
            "produto",
            "unidades_vendidas",
            "receita_reais",
            "mes_referencia"
            ])

    # unidades_vendidas: tratar texto "cem" e nulos
    def parse_unidades(value):
        if pd.isna(value):
            return 0
        s = str(value).strip().lower()
        if s == "":
            return 0
        if s == "cem":
            return 100
        if s == "-5":
            return 5
        try:
            return int(s)
        except ValueError:
            # se não conseguir converter, assume 0 para padronizar
            return 0

    df["unidades_vendidas"] = df["unidades_vendidas"].map(parse_unidades).astype(int)

    # receita_reais: usar função normalize_money
    df["receita_reais"] = df["receita_reais"].map(normalize_money).astype(float)

    # mes_referencia: normalizar mês/ano
    df["mes_referencia"] = df["mes_referencia"].map(normalize_month_year)

    return df


# -----------------------------
# Construção da tabela de personagens a partir da SWAPI
# -----------------------------
def build_swapi_people_table(people_raw, planets_raw, species_raw, films_raw, starships_raw):
    """
    Constrói uma tabela de personagens a partir das respostas da SWAPI:
    - nome do personagem
    - nome de busca original
    - nome normalizado
    - altura, massa, gênero
    - planeta natal (nome)
    - espécie (nome)
    - quantidade de filmes
    - quantidade de naves distintas
    - Remove nomes duplicados (mantém apenas o primeiro)
    """
    rows = []
    nao_encontrados = []

    # conjunto para evitar duplicatas
    nomes_swapi_vistos = set()

    for entry in people_raw:
        original_name = entry["original_name"]
        norm_search = entry["normalized_search_name"]
        results = entry["response"].get("results", [])

        if not results:
            nao_encontrados.append({
                "nome_original": original_name,
                "nome_normalizado": norm_search,
                "motivo": "Não encontrado na SWAPI",
            })
            continue

        # assume o primeiro resultado como o mais relevante
        person = results[0]
        nome_swapi = person.get("name")

        #2 SE JÁ FOI INCLUÍDO, IGNORA
        if nome_swapi in nomes_swapi_vistos:
            continue

        # marca como visto
        nomes_swapi_vistos.add(nome_swapi)

        # planeta natal
        homeworld_name = None
        if person.get("homeworld"):
            planet = planets_raw.get(person["homeworld"])
            if planet:
                homeworld_name = planet.get("name")

        # espécies
        species_list = person.get("species", [])
        specie = "N/I"
        if species_list:
            specie_data = species_raw.get(species_list[0])
            if specie_data:
                specie = specie_data.get("name")
        # species_names = []
        # for sp_url in person.get("species", []):
        #     sp = species_raw.get(sp_url)
        #     if sp:
        #         species_names.append(sp.get("name"))
        # species_str = ", ".join(species_names) if species_names else None

        # contagem de filmes e naves distintas
        films_count = len(set(person.get("films", [])))
        starships_count = len(set(person.get("starships", [])))

        # FEAT - adicionado coluna de quantidade de solicitações internas por personagem.
        qtd_sol = 0
        for nome_original_bronze in personagens_raw["nome_personagem"]:
            print(normalize_name(nome_original_bronze)[:4])
            if normalize_name(nome_swapi)[:4] == normalize_name(nome_original_bronze)[:4]:
                qtd_sol += 1

        rows.append({
            "nome_personagem_swapi": nome_swapi,
            "nome_personagem_original": original_name,
            "nome_personagem_norm": normalize_name(nome_swapi),
            "altura": person.get("height"),
            "massa": person.get("mass"),
            "genero": person.get("gender"),
            "planeta_natal": homeworld_name,
            "especie": specie,
            "quantidade_filmes": films_count,
            "quantidade_naves": starships_count,
            "quantidade_solicitacoes": qtd_sol
        })

    df = pd.DataFrame(rows)
    df_nao_encontrados = pd.DataFrame(nao_encontrados)

    # conversão de tipos numéricos
    df["altura"] = pd.to_numeric(df["altura"], errors="coerce")
    df["massa"] = pd.to_numeric(df["massa"], errors="coerce")

    # tabela de não encontrados
    df_nao_encontrados = pd.DataFrame(nao_encontrados)

    return df, df_nao_encontrados


# -----------------------------
# Enriquecimento com vendas
# -----------------------------
def enrich_with_vendas(personagens_swapi: pd.DataFrame, vendas_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza personagens da SWAPI com vendas:
    - agrega vendas por nome normalizado
    - junta com tabela de personagens
    - define "sem vendas" como zero (unidades e receita)
    """
    vendas_agg = (
        vendas_clean
        .groupby("nome_personagem_norm", as_index=False)
        .agg({
            "unidades_vendidas": "sum",
            "receita_reais": "sum",
        })
    )

    df = personagens_swapi.merge(
        vendas_agg,
        on="nome_personagem_norm",
        how="left",
        suffixes=("", "_vendas"),
    )

    # sem vendas = 0.0
    df["unidades_vendidas"] = df["unidades_vendidas"].fillna(0).astype(int)
    df["receita_reais"] = df["receita_reais"].fillna(0.0)

    return df


if __name__ == "__main__":
    ensure_dirs()

    # carrega bronze
    personagens_raw, vendas_raw, people_raw, planets_raw, species_raw, films_raw, starships_raw = load_bronze()

    # limpa planilhas
    personagens_clean = clean_personagens(personagens_raw)
    vendas_clean = clean_vendas(vendas_raw)

    # salva silver intermediário
    personagens_clean.to_csv(os.path.join(SILVER_DIR, "personagens_silver.csv"), index=False)
    vendas_clean.to_csv(os.path.join(SILVER_DIR, "vendas_silver.csv"), index=False)

    # constrói tabela de personagens da SWAPI + não encontrados
    personagens_swapi, personagens_nao_encontrados = build_swapi_people_table(
        people_raw, planets_raw, species_raw, films_raw, starships_raw
    )

    # enriquece com vendas
    personagens_enriquecidos = enrich_with_vendas(personagens_swapi, vendas_clean)
    #remove duplicados


    # salva silver final
    personagens_swapi.to_csv(
        os.path.join(SILVER_DIR, "personagens_swapi_silver.csv"),
        index=False,
    )
    personagens_enriquecidos.to_csv(
        os.path.join(SILVER_DIR, "personagens_enriquecidos_silver.csv"),
        index=False,
    )
    personagens_nao_encontrados.to_csv(
        os.path.join(SILVER_DIR, "personagens_nao_encontrados_silver.csv"),
        index=False,
    )
