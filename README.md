# wellbe_rpa_pipeline

Pipeline ETL + RPA para:

1. Extrair filmes da página Movie Search no RPA Challenge.
2. Transformar e normalizar os dados.
3. Carregar no MySQL com estratégia de upsert.
4. Gerar artefatos de saída (CSV, JSON, SQL dump).
5. Executar a etapa de Invoice Extraction (download dos invoices 2 e 4 + ZIP final).

<p align="center">
  <img width="800" height="450" alt="Dashboard final" src="https://github.com/user-attachments/assets/fe25364a-7bb7-4fb7-a170-7d767a7c80a1" />
</p>
<p align="center"><sub><em>Dashboard final gerado no wellbe_rpa_pipeline.ipynb</em></sub></p>

## Sumário

- [Visão geral da arquitetura](#visão-geral-da-arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Criação do banco de dados](#criação-do-banco-de-dados)
- [Como executar o notebook no Jupyter](#como-executar-o-notebook-no-jupyter)
- [Como executar o pipeline completo sem o Jupyter](#como-executar-o-pipeline-completo-sem-o-jupyter)
- [Saídas geradas](#saídas-geradas)
- [Troubleshooting](#troubleshooting)

## Visão geral da arquitetura

Fluxo principal:

1. EXTRACT (Selenium): abre o site, entra em Movie Search e coleta nome + descrição dos filmes.
2. TRANSFORM (Pandas): limpeza de strings, remoção de nulos/vazios e deduplicação.
3. LOAD (MySQL): cria schema (se necessario) e aplica upsert para evitar duplicidade.
4. OUTPUTS: grava CSV/JSON e dump SQL versionado.
5. INVOICE EXTRACTION: navega para a página de invoices, baixa os índices 2 e 4 e cria ZIP.

## Estrutura do projeto

```text
wellbe_rpa_pipeline/
  data/
  outputs/
  sql/
    init_database.sql
    dump_template.sql
  src/
    config.py
    scraper.py
    invoice_extraction.py
    database.py
    utils.py
    pipeline.py
  .env.example
  main.py
  run_scraper_debug.py
  requirements.txt
  wellbe_rpa_pipeline.ipynb
```

## Pré-requisitos

- Python 3.10+
- MySQL 8+
- Google Chrome instalado
- Conexão com internet (sites do RPA Challenge)

Observação: o Selenium 4 usa Selenium Manager para resolver o driver automaticamente na maioria dos cenários.

## Instalação

### 1) Criar e ativar ambiente virtual

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3) (Opcional) Instalar Jupyter para executar o notebook

```bash
pip install notebook
```

Ou, se preferir usar o JupyterLab:

```bash
pip install jupyterlab
```

## Variáveis de ambiente

Crie o arquivo .env a partir do exemplo:

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Variáveis disponiveis:

- BASE_URL: url base do RPA Challenge.
- MOVIE_SEARCH_PATH: rota da página de filmes.
- MOVIE_QUERY: termo de busca (padrão: Avengers).
- INVOICE_URL: url da página de Invoice Extraction.
- INVOICE_TABLE_ID: id da tabela de invoices.
- INVOICE_TARGET_INDICES: índices para download (padrão: 2,4).
- TIMEOUT_SECONDS: timeout geral do Selenium.
- HEADLESS: true/false para executar sem/ com browser visível.
- MYSQL_HOST / MYSQL_PORT / MYSQL_DATABASE / MYSQL_USER / MYSQL_PASSWORD: conexão MySQL.

Importante: altere os campos de conexão do MySQL de acordo com a configuração da sua máquina/servidor.
Os valores de exemplo podem não funcionar no seu ambiente.

Exemplo de valores (já no .env.example):

```env
BASE_URL=https://rpachallenge.com/
MOVIE_SEARCH_PATH=/movieSearch
MOVIE_QUERY=Avengers
INVOICE_URL=https://rpachallengeocr.azurewebsites.net/
INVOICE_TABLE_ID=tableSandbox
INVOICE_TARGET_INDICES=2,4
TIMEOUT_SECONDS=15
HEADLESS=true

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=db_wellbe_movies
MYSQL_USER=root
MYSQL_PASSWORD=root
```

## Criação do banco de dados

Este projeto possui script de bootstrap em sql/init_database.sql.

### Opção A: via cliente mysql

```bash
mysql -u root -p < sql/init_database.sql
```

### Opção B: dentro do prompt mysql

```sql
SOURCE sql/init_database.sql;
```

### Opção C: pela interface gráfica do MySQL Workbench

<p align="center">
  <img width="1017" height="785" alt="MySQL Workbench - script init_database.sql" src="https://github.com/user-attachments/assets/c2165c0d-2b86-42b0-93f3-6cae50b4ce56" />
</p>
<p align="center"><sub><em>Script init_database.sql no MySQL Workbench</em></sub></p>

1. Abra o MySQL Workbench e conecte na instância desejada.
2. Vá em File > Open SQL Script e selecione sql/init_database.sql, ou simplesmente copie e cole o conteúdo.
3. Clique no botão de execução (ícone de raio) para rodar o script.

Exemplo de execução no Workbench:

<p align="center">
  <img width="800" height="450" alt="MySQL Workbench - execução" src="https://github.com/user-attachments/assets/d61aa9d4-4b2f-4677-a229-c16189042e85" />
</p>
<p align="center"><sub><em>Execução do script no Workbench</em></sub></p>

O script faz:

1. CREATE DATABASE IF NOT EXISTS db_wellbe_movies
2. USE db_wellbe_movies
3. CREATE TABLE IF NOT EXISTS movies

## Como executar o notebook no Jupyter

Arquivo principal: wellbe_rpa_pipeline.ipynb

### 1) Iniciar o Jupyter

```bash
jupyter notebook
```

Se você instalou JupyterLab, também pode iniciar com:

```bash
jupyter lab
```

### 2) Abrir o arquivo

No navegador, abra wellbe_rpa_pipeline.ipynb.

### 3) Selecionar kernel

Selecione o kernel Python do ambiente virtual onde as dependências foram instaladas.

### 4) Executar as células em ordem

Recomendação:

1. Célula 4 (Setup)
2. Célula 6 (Extract)
3. Célula 8 (Transform)
4. Célula 10 (Load)
5. Célula 12 (Dump SQL)
6. Célula 15 (Invoice Extraction + download + zip)
7. Célula 17 (Resultados)

Se você alterar codigo em src/, reinicie o kernel e rode novamente desde o setup.

## Como executar o pipeline completo sem o Jupyter

Com ambiente virtual ativo e .env configurado:

```bash
python main.py
```

Esse comando chama src.pipeline.run_pipeline(load_to_database=True) e executa:

1. Extração dos filmes
2. Transformação
3. Carga no MySQL
4. Geração de dump SQL
5. Etapa de Invoice Extraction (download + zip)

Ao final, um resumo com paths de saída é impresso no terminal.

## Saídas geradas

Arquivos esperados:

- data/movies_raw.csv
- outputs/movies_avengers_`<timestamp>`.csv
- outputs/movies_avengers_`<timestamp>`.json
- sql/movies_dump_`<timestamp>`.sql
- outputs/invoices/invoice_2.jpg
- outputs/invoices/invoice_4.jpg
- outputs/invoices.zip

## Troubleshooting

1. Erro de conexão MySQL
- Verifique se o serviço MySQL está ativo.
- Confirme MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD e MYSQL_DATABASE no .env.
- Execute novamente sql/init_database.sql.

2. Não baixou invoices
- Verifique conectividade com https://rpachallengeocr.azurewebsites.net/
- Confirme INVOICE_TABLE_ID e INVOICE_TARGET_INDICES no .env.

3. Selenium não abre navegador
- Atualize dependências: pip install -r requirements.txt --upgrade
- Confirme instalação do Google Chrome.

4. Notebook com import não resolvido
- Verifique se o kernel selecionado é o mesmo ambiente virtual.
- Instale dependências no mesmo ambiente do kernel.

5. Resultados diferentes entre notebook e script
- Reinicie o kernel do notebook e execute novamente desde a célula de setup.
- Use run_scraper_debug.py para validar o scraping isoladamente.

## Observações finais

- O pipeline foi estruturado para facilitar manutenção e reexecução.
- A etapa de Invoice Extraction é configurável por variável de ambiente.
- Para ambiente de produção, recomenda-se guardar dados sensíveis fora de .env e adicionar observabilidade centralizada.
