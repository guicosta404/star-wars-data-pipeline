"""
Camada bronze:
- lê as duas planilhas originais da pasta data/
- salva como vieram em bronze/ (sem limpeza)
- chama a SWAPI para cada personagem solicitado
- salva respostas cruas da SWAPI em JSON na bronze/
"""

import os
import json
from datetime import datetime, timezone

import pandas as pd
import requests

from utils import normalize_name

BRONZE_DIR = "bronze"
DATA_DIR = "data"
SWAPI_BASE = "https://swapi.dev/api"


# -----------------------------
# Infra básica de pastas
# -----------------------------
def ensure_dirs():
    os.makedirs(BRONZE_DIR, exist_ok=True)


# -----------------------------
# Metadados de ingestão da planilha
# -----------------------------
def add_ingestion_metadata(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Adiciona colunas de metadados:
    - ingestion_source: nome da origem
    - ingestion_timestamp: timestamp UTC da ingestão
    """
    now = now = datetime.now(timezone.utc).isoformat()
    df["ingestion_source"] = source_name
    df["ingestion_timestamp"] = now
    return df


# -----------------------------
# Ingestão das planilhas CSV
# -----------------------------
def ingest_csvs():
    """
    Lê os CSVs originais da pasta data/ e salva na bronze/ sem transformação,
    apenas adicionando metadados de ingestão.
    """
    # personagens_solicitados
    personagens = pd.read_csv(os.path.join(DATA_DIR, "personagens_solicitados.csv"))
    personagens = add_ingestion_metadata(personagens, "personagens_solicitados.csv")
    personagens.to_csv(
        os.path.join(BRONZE_DIR, "personagens_solicitados_raw.csv"),
        index=False,
    )

    # vendas_produtos
    vendas = pd.read_csv(os.path.join(DATA_DIR, "vendas_produtos.csv"))
    vendas = add_ingestion_metadata(vendas, "vendas_produtos.csv")
    vendas.to_csv(
        os.path.join(BRONZE_DIR, "vendas_produtos_raw.csv"),
        index=False,
    )


# -----------------------------
# SWAPI: busca por personagem
# -----------------------------
def fetch_swapi_people_by_name(name: str):
    """
    Usa o endpoint de busca da SWAPI:
    https://swapi.dev/api/people/?search=<nome>

    Retorna o json da resposta.
    """
    url = f"{SWAPI_BASE}/people/?search={name}"
    resp = requests.get(url, timeout=10)
    #Se a resposta for vazia (Não encontrado), tenta buscar só a primeira parte do nome, primeiras 4 caracteres e checa se o nome bate
    #Se o inicio do nome não for igual ignora e dá como não encontrado.
    if len(resp.json().get("results")) == 0:
        url = f"{SWAPI_BASE}/people/?search={name[:4]}"
        resp1 = requests.get(url, timeout=10)
        if len(resp1.json().get("results")) > 0:
            if resp1.json().get("results")[0]['name'][:4] == name[:4]:
                resp = resp1
    resp.raise_for_status()
    return resp.json()


def ingest_swapi():
    """
    Lê a lista de personagens solicitados e faz uma busca na SWAPI
    para cada nome (original), salvando:

    - swapi_people_raw.json: lista de buscas e respostas
    - swapi_planets_raw.json: mapa URL -> JSON de planetas
    - swapi_species_raw.json: mapa URL -> JSON de espécies
    - swapi_films_raw.json: mapa URL -> JSON de filmes
    - swapi_starships_raw.json: mapa URL -> JSON de naves
    """
    personagens = pd.read_csv(os.path.join(DATA_DIR, "personagens_solicitados.csv"))

    # lista de nomes únicos (ignorando nulos)
    nomes_unicos = (
        personagens["nome_personagem"]
        .dropna()
        .astype(str)
        .unique()
    )

    people_data = []
    planets_data = {}
    species_data = {}
    films_data = {}
    starships_data = {}
    now = now = datetime.now(timezone.utc).isoformat()

    for nome in nomes_unicos:
        result = fetch_swapi_people_by_name(nome)

        # guarda a resposta crua, junto com o nome original e normalizado e metadados de hora e ingestão
        people_data.append({
            "original_name": nome,
            "normalized_search_name": normalize_name(nome),
            "ingestion_timestamp": now,
            "source": f"https://swapi.dev/api/people/?search={nome}",
            "response": result,
        })

        # coleta URLs de recursos relacionados para buscar depois
        for person in result.get("results", []):
            # homeworld
            if person.get("homeworld"):
                planets_data.setdefault(person["homeworld"], None)
            # species
            for sp in person.get("species", []):
                species_data.setdefault(sp, None)
            # films
            for film in person.get("films", []):
                films_data.setdefault(film, None)
            # starships
            for ship in person.get("starships", []):
                starships_data.setdefault(ship, None)

    # função auxiliar para buscar cada URL única
    def fetch_url_map(url_map: dict):
        for url in list(url_map.keys()):
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            url_map[url] = resp.json()

    # busca planetas, espécies, filmes, naves
    fetch_url_map(planets_data)
    fetch_url_map(species_data)
    fetch_url_map(films_data)
    fetch_url_map(starships_data)

    # salva JSONs na bronze
    with open(os.path.join(BRONZE_DIR, "swapi_people_raw.json"), "w", encoding="utf-8") as f:
        json.dump(people_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(BRONZE_DIR, "swapi_planets_raw.json"), "w", encoding="utf-8") as f:
        json.dump(planets_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(BRONZE_DIR, "swapi_species_raw.json"), "w", encoding="utf-8") as f:
        json.dump(species_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(BRONZE_DIR, "swapi_films_raw.json"), "w", encoding="utf-8") as f:
        json.dump(films_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(BRONZE_DIR, "swapi_starships_raw.json"), "w", encoding="utf-8") as f:
        json.dump(starships_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    ensure_dirs()
    ingest_csvs()
    ingest_swapi()
