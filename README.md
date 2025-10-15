# 📊 Cockpit de Relatórios

> Sistema interativo para geração automática de relatórios de performance de eventos automotivos

## 📑 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Documentação](#-documentação)
- [Testes](#-testes)
- [Licença](#-licença)

---

## 🎯 Visão Geral

O **Cockpit de Relatórios** é um sistema desenvolvido em Python que automatiza a geração de relatórios de performance para eventos automotivos. O sistema extrai dados de um banco MySQL, processa através de um pipeline ETL e gera relatórios profissionais em DOCX e PDF.

**Projeto desenvolvido como parte do plano de atividades de estágio:**
- **Desenvolvedor:** Lucas Ferreira Mendes Moraes
- **Instituição:** Universidade São Francisco (USF) - Campus Campinas Swift
- **Curso:** Engenharia de Computação
- **Empresa:** SIMPLE SOLUÇÕES DE MARKETING E TECNOLOGIA LTDA
- **Ano:** 2025

### Características Principais

- 🔄 **Pipeline ETL Robusto**: Extração, transformação e carga de dados otimizada
- 🎨 **Relatórios Customizáveis**: Templates profissionais facilmente editáveis
- 📊 **Múltiplas Visões**: Nacional, Regional, por Setor, Grupo, Marca e PDV
- 🖥️ **Interface Interativa**: Sistema de menus intuitivo via terminal
- ✅ **Testes Automatizados**: Suíte completa com pytest
- 📝 **Sistema de Logs**: Rastreamento completo de operações

---

## ✨ Funcionalidades

### Pipeline de ETL
- Extração de dados de múltiplas tabelas MySQL
- Transformação e agregação em 7 níveis diferentes
- Geração automática de arquivos CSV estruturados
- Query SQL otimizada com CTEs

### Geração de Relatórios
- Seleção interativa de evento e período de análise
- 6 tipos de relatório disponíveis
- Opções acumuladas e específicas
- Cálculo automático de métricas e percentuais
- Saída dual em DOCX e PDF

### Métricas Incluídas
- Total de contatos e vendedores cadastrados
- Convites enviados, confirmados e declinados
- Taxa de conversão em cada etapa do funil
- Presenças, test-drives e vendas
- Análises percentuais detalhadas por categoria

---

## 📋 Requisitos

### Software Necessário

- **Python**: 3.9 ou superior
- **MySQL**: 5.7 ou superior
- **Microsoft Word** (Windows) ou **LibreOffice** (Linux/Mac) para conversão PDF

### Bibliotecas Python

```txt
pandas>=2.0.0
jinja2>=3.1.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
python-dotenv>=1.0.0
python-docx>=0.8.11
docx2pdf>=0.1.8
pytest>=7.0.0
```

---

## 🚀 Instalação

### 1. Clone o Repositório

```bash
git clone <url_do_repositorio>
cd relatorio_cockpit
```

### 2. Crie o Ambiente Virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### 1. Configure as Credenciais do Banco

Crie o arquivo `config/.env` com suas credenciais:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
MYSQL_DB_PDV=pdv_automotive
```

⚠️ **Importante:** Nunca versione o arquivo `.env` com credenciais reais!

### 2. Configure os Eventos Disponíveis

Edite o arquivo `config/eventos_db.csv`:

```csv
db_name,event_name,start_date,end_date
dexp_ram_agosto,Liga RAM Agosto 2024,01/08/2024,31/08/2024
dexp_jeep_setembro,Liga JEEP Setembro 2024,01/09/2024,30/09/2024
```

| Coluna | Descrição | Formato |
|--------|-----------|---------|
| `db_name` | Nome do banco de dados do evento | String |
| `event_name` | Nome amigável do evento | String |
| `start_date` | Data inicial do evento | dd/mm/aaaa |
| `end_date` | Data final do evento | dd/mm/aaaa |

### 3. Verifique o Template de Relatório

Certifique-se de que o arquivo `report/templates/template.docx` existe e contém os placeholders necessários:

- `{{nome_evento}}`
- `{{data_inicio}}` / `{{data_fim}}`
- `{{tipo_visao}}`
- `{{total_contatos}}`, `{{total_enviados}}`, etc.

### 4. Teste a Conexão

```bash
python -c "from config.connection_db import test_connection; test_connection()"
```

---

## 💻 Uso

### Execução Básica

```bash
python main.py
```

### Fluxo de Uso

1. **Selecione o Evento**: Escolha o evento da lista disponível
2. **Defina o Período**: Informe datas de início e fim (dd/mm/aaaa)
3. **Aguarde o ETL**: O sistema processará os dados automaticamente
4. **Escolha o Tipo de Relatório**: Nacional, Regional, Por Setor, etc.
5. **Especifique o Filtro**: Dados acumulados ou item específico
6. **Relatório Gerado**: Arquivos DOCX e PDF salvos em `output/`

### Exemplo de Sessão

```
--- Selecione o Evento ---
[1] Liga RAM Agosto 2024
[2] Liga JEEP Setembro 2024
[0] Sair

Digite o número da sua escolha: 1

📅 Digite a DATA DE INÍCIO do período de análise:
Período válido: 01/08/2024 até 31/08/2024
Data (dd/mm/aaaa): 01/08/2024

📅 Digite a DATA DE FIM do período de análise:
Período válido: 01/08/2024 até 31/08/2024
Data (dd/mm/aaaa): 15/08/2024

✅ Período confirmado: 01/08/2024 até 15/08/2024

[ETAPA 1/3] Executando o processo de ETL...
[ETAPA 2/3] Carregando dados para geração do relatório...
[ETAPA 3/3] Iniciando a geração do arquivo do relatório...

Relatório gerado com sucesso!
```

### Tipos de Relatório Disponíveis

1. **Nacional**: Visão consolidada de todos os dados
2. **Regional**: Dados agrupados por região (RID)
3. **Por Setor**: Dados agrupados por setor (SID)
4. **Por Grupo**: Dados agrupados por grupo empresarial
5. **Por Marca**: Dados agrupados por marca automotiva
6. **Por PDV**: Dados detalhados por Ponto de Venda

---

## 📁 Estrutura do Projeto

``` text
relatorio_cockpit/
│
├── config/                      # Configurações
│   ├── connection_db.py        # Gerenciador de conexão MySQL
│   ├── eventos_db.csv          # Mapeamento de eventos
│   └── .env                    # Credenciais (não versionado)
│
├── etl/                        # Pipeline de dados
│   ├── etl.py                  # Lógica de ETL
│   └── query.sql               # Query SQL mestre
│
├── report/                     # Geração de relatórios
│   ├── build_report.py         # Lógica de geração
│   └── templates/              
│       └── template.docx       # Template visual
│
├── tests/                      # Testes automatizados
│   ├── test_connection_db.py   # Testes de conexão
│   ├── test_etl.py             # Testes do ETL
│   ├── test_build_report.py    # Testes de relatórios
│   └── tests.log               # Log dos testes
│
├── logs/                       # Arquivos de log
│   ├── system.log              # Log do orquestrador
│   ├── etl.log                 # Log do ETL
│   └── build_report.log        # Log de relatórios
│
├── output/                     # Saída do sistema
│   ├── csv/                    # CSVs gerados pelo ETL
│   ├── *.docx                  # Relatórios DOCX gerados
│   └── *.pdf                   # Relatórios PDF gerados
│
├── main.py                     # Ponto de entrada principal
├── pytest.ini                  # Configuração do pytest
├── requirements.txt            # Dependências Python
├── LICENSE                     # Licença do projeto
├── .gitignore                  # Arquivos ignorados pelo Git
└── README.md                   # Este arquivo
```

---

## 📚 Documentação

### Arquitetura

O sistema segue uma arquitetura de **Service-Oriented Architecture (SOA)** modular:

- **main.py**: Orquestrador principal e interface CLI
- **etl.py**: Serviço de processamento de dados (ETL)
- **build_report.py**: Serviço de geração de relatórios
- **connection_db.py**: Serviço de persistência e conexão

### Padrões de Design Utilizados

- **State Machine Pattern**: Controle de navegação no `main.py`
- **Template Method Pattern**: Templates SQL (Jinja2) e DOCX
- **Service Layer Pattern**: Módulos independentes e reutilizáveis

### Fluxo de Dados

```
MySQL → ETL (query.sql) → Pandas (agregações) → 7 CSVs →
build_report.py → Template DOCX → Relatório Final (DOCX + PDF)
```

### Sistema de Logs

Todos os eventos são registrados em três logs distintos:

- `logs/system.log`: Navegação e orquestração geral
- `logs/etl.log`: Processamento ETL e queries
- `logs/build_report.log`: Geração de relatórios

---

## 🧪 Testes

### Executando Todos os Testes

```bash
pytest
```

### Executando Testes Específicos

```bash
# Testes de conexão
pytest tests/test_connection_db.py

# Testes do ETL
pytest tests/test_etl.py

# Testes de relatórios
pytest tests/test_build_report.py
```

### Testes com Verbose e Detalhes

```bash
pytest -v
```

### Visualizar Logs Durante Testes

```bash
pytest -v --log-cli-level=INFO
```

### Cobertura de Testes (Opcional)

```bash
pip install pytest-cov
pytest --cov=etl --cov=report --cov=config --cov-report=html
```

### Tipos de Testes Implementados

- ✅ **Unitários**: Validação de funções isoladas (`safe_division`, agregações)
- ✅ **Integração**: Validação do pipeline completo ETL
- ✅ **Fixtures**: Dados de teste reutilizáveis (monkeypatch, tmp_path)
- ✅ **Mocks**: Simulação de conexões e queries ao banco

---

## 📄 Licença

Este projeto está sob **Licença de Uso Restrito - Acadêmico e Corporativo Interno**.

**Uso permitido para:**
- ✅ Fins acadêmicos e educacionais (Universidade São Francisco)
- ✅ Uso interno da SIMPLE SOLUÇÕES DE MARKETING E TECNOLOGIA LTDA
- ✅ Avaliação por professores e orientadores da USF
- ✅ Apresentação em portfólio acadêmico do autor

**Restrições:**
- ❌ Proibida redistribuição pública ou comercialização
- ❌ Proibido uso por terceiros sem autorização expressa
- ❌ Proibido uso comercial por outras organizações

Para outras formas de uso, entre em contato com o autor.

Consulte o arquivo [LICENSE](LICENSE) para detalhes completos.

---

## 📞 Suporte

### Problemas Comuns

**❌ Erro de Conexão com MySQL**
```bash
# Verifique as credenciais no .env
# Teste a conexão
python -c "from config.connection_db import test_connection; test_connection()"
```

**❌ Erro ao Converter para PDF**
- **Windows**: Certifique-se de que o Microsoft Word está instalado
- **Linux**: `sudo apt install libreoffice`
- **Mac**: Instale o LibreOffice via Homebrew

**❌ Consulta ETL Retorna Dados Vazios**
- Verifique se o período selecionado contém dados
- Confirme o nome do banco em `eventos_db.csv`
- Consulte `logs/etl.log` para mensagens de erro detalhadas

**❌ Template DOCX não encontrado**
```bash
# Verifique se o arquivo existe
ls report/templates/template.docx
```

### Verificando Logs

Em caso de erro, sempre consulte os arquivos de log:

```bash
# Log principal
cat logs/system.log

# Log do ETL
cat logs/etl.log

# Log de relatórios
cat logs/build_report.log
```

---

## 🔄 Changelog

### Versão 1.0.0 (Outubro 2025)

**Funcionalidades Implementadas:**
- ✅ Pipeline ETL completo com 7 níveis de agregação
- ✅ Geração de 6 tipos diferentes de relatórios
- ✅ Interface interativa CLI com navegação completa
- ✅ Validação de datas com escopo do evento
- ✅ Sistema de logs modular e detalhado
- ✅ Suíte de testes automatizados (pytest)
- ✅ Documentação técnica completa

**Melhorias de Qualidade:**
- ✅ Reorganização de colunas nos CSVs (coluna ID sempre primeira)
- ✅ Formatação automática de células nas tabelas DOCX
- ✅ Conversão automática de formatos de data (dd/mm/aaaa ↔ YYYY-MM-DD)
- ✅ Tratamento robusto de erros e exceções

---

**Desenvolvido com 💙 por Lucas Ferreira Mendes Moraes - 2025**