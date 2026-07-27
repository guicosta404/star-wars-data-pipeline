# utils.py
"""
Funções utilitárias de normalização e limpeza de dados:
- nomes de personagens
- valores monetários
- datas (mês/ano em formatos variados)
"""

import unicodedata
import re
import pandas as pd


# -----------------------------
# Normalização de nomes
# -----------------------------
def normalize_name(name: str) -> str:
    """
    Normaliza nomes de personagens para servir como chave de integração:
    - strip de espaços
    - lowercase
    - remoção de acentos
    - remoção de pontuação
    - colapso de múltiplos espaços

    Ex.: "  Han  Solo  " -> "han solo"
         "LUKE SKYWALKER" -> "luke skywalker"
         "Chewbaca" -> "chewbaca" (mantém erro, mas padronizado)
    """
    if not isinstance(name, str):
        return ""

    s = name.strip().lower()

    # remove acentos
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

    # remove pontuação
    s = re.sub(r"[^a-z0-9 ]", "", s)

    # colapsa espaços
    s = re.sub(r"\s+", " ", s)

    return s


# -----------------------------
# Normalização de valores monetários
# -----------------------------
def normalize_money(value):
    """
    Converte valores monetários em float, tratando:
    - "R$ 3.456,00"
    - "675,00"
    - "1234.56"
    - "1234"
    - "$ 1234.56"

    Regras:
    - se houver ponto e vírgula, o ponto é separador de milhar e a vírgula é decimal
    - se houver apenas um separador (., ou ,), ele é o separador decimal
    """
    if value is None:
        return 0.0

    s = str(value).strip()

    if s == "":
        return 0.0

    # remove símbolos de moeda
    s = s.replace("R$", "").replace("$", "").strip()

    # remove espaços internos
    s = s.replace(" ", "")

    # remove hifen -
    s = s.replace("-", "")

    # ponto separa milhar e vírgula separa decimais
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    # se tiver vírgula e não tiver ponto -> vírgula é decimal
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    # se tiver ponto e não tiver vírgula -> ponto é decimal (mantém)
    elif "." in s and "," not in s:
        pass
    # se não tiver nenhum separador -> inteiro
    else:
        pass

    try:
        return float(s)
    except ValueError:
        # em caso de erro, retorna 0.0 para tornar padrão
        return 0.0


# -----------------------------
# Normalização de datas (mês/ano)
# -----------------------------
MESES = {
    "janeiro": "01", "jan": "01",
    "fevereiro": "02", "fev": "02",
    "março": "03", "mar": "03",
    "abril": "04", "abr": "04",
    "maio": "05", "mai": "05",
    "junho": "06", "jun": "06",
    "julho": "07", "jul": "07",
    "agosto": "08", "ago": "08",
    "setembro": "09", "set": "09",
    "outubro": "10", "out": "10",
    "novembro": "11", "nov": "11",
    "dezembro": "12", "dez": "12",
}


def normalize_month_year(value: str):
    """
    Normaliza datas de referência de vendas (mês/ano) em um datetime:

    Exemplos de entrada:
    - "2026-01"
    - "01/2026"
    - "Janeiro/2026"
    - "01/2026"
    - "2026-03"
    - "01/2026"
    - "2026-01"
    - "Janeiro/2026"

    Saída: pandas.Timestamp (primeiro dia do mês), ou NaT se não conseguir.
    """
    if not isinstance(value, str):
        return pd.NaT

    s = value.strip().lower()

    if s == "":
        return pd.NaT

    # troca nomes de meses por números
    for nome, num in MESES.items():
        s = re.sub(nome, num, s)

    # troca separadores comuns por "/"
    s = re.sub(r"[-\. ]", "/", s)

    # agora tenta converter em dois formatos: mm/yyyy e yyyy/mm
    # exemplo: "01/2026" ou "2026/01"
    dt = pd.to_datetime(s, format="%m/%Y", errors="coerce")
    if pd.isna(dt):
        dt = pd.to_datetime(s, format="%Y/%m", errors="coerce")

    return dt
