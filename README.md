# Pipeline de Dados Star Wars

Projeto desenvolvido para um teste técnico de estágio em Engenharia de Dados.

A proposta foi construir um pequeno pipeline que reúne uma lista de personagens de Star Wars, dados de vendas e informações da API pública [SWAPI](https://swapi.dev/). O resultado final é uma tabela limpa e pronta para ser utilizada por um analista em uma ferramenta de BI.

O foco da solução está na organização das etapas e no tratamento das inconsistências dos dados, seguindo o fluxo:

```text
Dados originais → Bronze → Silver → Gold
```

## Objetivo

Preparar uma tabela com uma linha por personagem, contendo informações como:

- nome, planeta natal, espécie e gênero;
- altura e massa;
- quantidade de filmes e naves;
- total de unidades vendidas;
- receita total em reais.

## Como o pipeline funciona

### Bronze — dados de entrada

A camada Bronze guarda os dados próximos de seu formato original:

- copia as duas planilhas da pasta `data/`;
- acrescenta a origem e o horário da ingestão;
- consulta os personagens na SWAPI;
- salva em JSON as respostas da API e os recursos relacionados, como planetas, espécies, filmes e naves.

Os arquivos são sobrescritos a cada execução. Dessa forma, executar o pipeline novamente não acumula registros duplicados de execuções anteriores.

### Silver — limpeza e cruzamento

Na camada Silver, os dados são preparados para poderem ser relacionados:

- os nomes são normalizados, removendo diferenças de espaços, letras maiúsculas, acentos e pontuação;
- solicitações repetidas após a normalização são consolidadas;
- valores de unidades, moedas e datas são convertidos para formatos consistentes;
- os dados dos personagens são enriquecidos com as informações da SWAPI;
- as vendas são somadas por personagem e ligadas pelo nome normalizado;
- personagens não encontrados são registrados em um arquivo separado.

### Gold — dados para o dashboard

A camada Gold contém o principal resultado do projeto. Nela, as colunas recebem nomes mais amigáveis e os tipos numéricos são ajustados para facilitar o uso em ferramentas de BI.

Também são gerados três resumos simples com a quantidade de personagens por planeta, espécie e gênero.

## Principais decisões

- **Chave de ligação:** usei o nome normalizado para cruzar as fontes, pois os arquivos apresentam diferenças de escrita e formatação.
- **Nomes repetidos:** quando uma mesma solicitação aparece mais de uma vez após a normalização, mantenho apenas a primeira ocorrência.
- **Busca na API:** primeiro faço a busca pelo nome informado. Quando não há resultado, tento os quatro primeiros caracteres e verifico se o começo do nome encontrado é igual ao pesquisado. O primeiro resultado válido é utilizado.
- **Vendas:** as linhas são consideradas movimentações válidas e são somadas por personagem. Registros idênticos na planilha de vendas não são removidos automaticamente.
- **Valores inconsistentes:** entradas conhecidas, como `cem` e números negativos, são padronizadas; símbolos de moeda e separadores decimais simples também são tratados.
- **Sem vendas:** personagens sem registros de venda recebem zero em unidades e receita.
- **Não encontrados:** nomes sem correspondência na SWAPI ficam registrados em `silver/personagens_nao_encontrados_silver.csv`.

## Estrutura do projeto

```text
case-maxxi/
├── data/                  # Planilhas originais
├── bronze/                # Dados ingeridos e respostas da SWAPI
├── silver/                # Dados limpos e enriquecidos
├── gold/                  # Tabela final e resumos para BI
├── bronze_ingest.py       # Ingestão dos CSVs e da API
├── silver_transform.py    # Limpeza, normalização e cruzamentos
├── gold_build.py          # Construção dos arquivos finais
├── utils.py               # Funções auxiliares de normalização
├── pipeline.py            # Execução das três camadas em sequência
└── pyproject.toml         # Configuração e dependências do projeto
```

## Tecnologias utilizadas

- Python 3.12 ou superior;
- pandas para leitura, limpeza e cruzamento dos dados;
- requests para as consultas à SWAPI;
- uv para instalar as dependências e executar o projeto.

## Como executar

É necessário ter o [uv](https://docs.astral.sh/uv/) instalado e acesso à internet, pois a camada Bronze consulta a SWAPI.

Na raiz do projeto, instale as dependências:

```bash
uv sync
```

Depois, execute o pipeline completo:

```bash
uv run python pipeline.py
```

O `pipeline.py` executa as camadas Bronze, Silver e Gold nessa ordem. Se alguma etapa apresentar erro, o processo é interrompido.

## Arquivos gerados

O principal entregável é:

```text
gold/personagens_dashboard_gold.csv
```

Esse arquivo possui uma linha por personagem encontrado e pode ser importado diretamente em uma ferramenta de BI.

Arquivos complementares:

- `gold/resumo_por_planeta.csv`;
- `gold/resumo_por_especie.csv`;
- `gold/resumo_por_genero.csv`;
- `silver/personagens_nao_encontrados_silver.csv`.

Na execução atual, a tabela Gold contém **12 personagens**. Outros **4 nomes** foram registrados como não encontrados na SWAPI.

## Limitações

- A correção de erros de digitação é simples e pode não reconhecer todos os nomes escritos incorretamente.
- A busca utiliza o primeiro resultado retornado pela SWAPI, o que pode exigir validação em casos de nomes parecidos.
- A execução depende da disponibilidade e do conteúdo atual da API.(Personagens atuais não encontrados por exemplo)
- Alguns formatos inesperados de valores podem ser convertidos para zero quando não for possível interpretá-los.

