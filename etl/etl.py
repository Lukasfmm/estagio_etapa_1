"""
============================================================================
Módulo: etl.py
Projeto: Cockpit de Relatórios
Autor: Lucas Ferreira Mendes Moraes
Data: Outubro 2025
============================================================================

DESCRIÇÃO:
    Módulo de serviço responsável pela lógica de ETL (Extract, Transform, Load).
    Extrai dados do MySQL, transforma através de agregações Pandas e gera
    múltiplas visões em arquivos CSV para análise.

ARQUITETURA:
    - Uma única query SQL extrai dados no nível mais granular (por vendedor)
    - Pandas realiza todas as agregações necessárias em memória
    - Gera 7 arquivos CSV com diferentes níveis de agregação

VISÕES GERADAS:
    1. visao_vendedor.csv  - Nível mais detalhado (base para todas as outras)
    2. visao_pdv.csv       - Agregado por PDV/concessionária
    3. visao_regional.csv  - Agregado por região geográfica
    4. visao_grupo.csv     - Agregado por grupo empresarial
    5. visao_marca.csv     - Agregado por marca de veículo
    6. visao_setor.csv     - Agregado por setor comercial
    7. visao_nacional.csv  - Totais consolidados

DEPENDÊNCIAS:
    - pandas: Processamento e agregação de dados
    - jinja2: Template SQL dinâmico
    - sqlalchemy: Execução de queries
    - python-dotenv: Variáveis de ambiente
============================================================================
"""

# ============================================================================
# IMPORTAÇÕES
# ============================================================================
import os
import logging
from pathlib import Path
import pandas as pd
from jinja2 import Template
from sqlalchemy import text
from dotenv import load_dotenv
from config.connection_db import engine

# ============================================================================
# CONFIGURAÇÃO DE CAMINHOS E AMBIENTE
# ============================================================================
# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Define caminhos base do projeto
BASE_DIR = Path(__file__).resolve().parent          # Pasta etl/
CONFIG_DIR = BASE_DIR.parent / "config"             # Pasta config/

# Define pasta de saída dos CSVs
# NOTA: Esta variável é global para permitir que os testes a sobrescrevam
#       apontando para uma pasta temporária
output_dir = BASE_DIR.parent / "output" / "csv"

# ============================================================================
# CONFIGURAÇÃO DO SISTEMA DE LOGGING
# ============================================================================
def setup_logging():
    """
    Configura o logger para registrar eventos e erros em logs/etl.log.
    
    O logger registra todas as operações do ETL com timestamp, permitindo
    rastreamento completo do processamento de dados e diagnóstico de erros.
    
    Returns:
        logging.Logger: Instância configurada do logger
        
    Comportamento:
        - Cria a pasta logs/ se não existir
        - Registra em modo append (preserva logs anteriores)
        - Formato: YYYY-MM-DD HH:MM:SS - LEVEL - Mensagem
        - Evita duplicação de handlers
    """
    # Define pasta e arquivo de log
    log_dir = BASE_DIR.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "etl.log"
    
    # Cria logger específico para o ETL
    logger = logging.getLogger("etl_logger")
    logger.setLevel(logging.INFO)
    
    # Configura handler para escrever em arquivo
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    
    # Define formato dos logs: data/hora - nível - mensagem
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Adiciona handler apenas se ainda não existir (evita duplicação)
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger

# Instancia o logger globalmente
logger = setup_logging()

# ============================================================================
# FUNÇÕES PÚBLICAS (INTERFACE DO MÓDULO)
# ============================================================================

def get_eventos() -> list:
    """
    Lê o arquivo de mapeamento de eventos e retorna os dados.
    
    O arquivo eventos_db.csv contém o mapeamento entre eventos e seus
    respectivos bancos de dados. Cada linha representa um evento disponível
    para geração de relatórios.
    
    Returns:
        list[dict]: Lista de dicionários contendo informações dos eventos
            Cada dicionário contém:
                - db_name: Nome do banco de dados do evento
                - event_name: Nome amigável do evento
                - start_date: Data inicial do evento (formato dd/mm/aaaa)
                - end_date: Data final do evento (formato dd/mm/aaaa)
    
    Raises:
        FileNotFoundError: Se o arquivo eventos_db.csv não existir
        ValueError: Se o arquivo estiver vazio ou sem colunas obrigatórias
    
    Example:
        >>> eventos = get_eventos()
        >>> print(eventos[0])
        {
            'db_name': 'dexp_ram_agosto',
            'event_name': 'Liga RAM',
            'start_date': '01/08/2024',
            'end_date': '31/08/2024'
        }
    """
    logger.info("Lendo arquivo de mapeamento de eventos: config/eventos_db.csv")
    eventos_path = CONFIG_DIR / "eventos_db.csv"
    
    try:
        # Lê o arquivo CSV com pandas
        df_eventos = pd.read_csv(eventos_path)
        
        # Valida se o arquivo não está vazio
        if df_eventos.empty:
            raise ValueError("O arquivo config/eventos_db.csv está vazio.")
        
        # Valida se todas as colunas obrigatórias existem
        colunas_obrigatorias = ['db_name', 'event_name', 'start_date', 'end_date']
        for coluna in colunas_obrigatorias:
            if coluna not in df_eventos.columns:
                raise ValueError(
                    f"Coluna obrigatória '{coluna}' não encontrada no arquivo eventos_db.csv"
                )
        
        # Converte DataFrame para lista de dicionários
        return df_eventos.to_dict('records')
        
    except FileNotFoundError:
        logger.error(f"Arquivo de mapeamento de eventos '{eventos_path}' não encontrado.")
        raise

def executar_etl(db_evento_selecionado: str, data_inicio: str, data_fim: str):
    """
    Função principal do ETL: executa a query e gera todos os arquivos CSV.
    
    Esta função orquestra todo o pipeline de ETL:
    1. Carrega e renderiza o template SQL
    2. Executa a query no banco de dados
    3. Gera o arquivo mestre (visao_vendedor.csv)
    4. Realiza agregações para gerar as demais visões
    5. Salva todos os arquivos CSV na pasta output/
    
    Args:
        db_evento_selecionado (str): Nome do banco de dados do evento
            Ex: 'dexp_ram_agosto'
        data_inicio (str): Data inicial no formato YYYY-MM-DD
            Ex: '2024-08-01'
        data_fim (str): Data final no formato YYYY-MM-DD
            Ex: '2024-08-31'
    
    Raises:
        ValueError: Se a consulta não retornar nenhum registro
    
    Example:
        >>> executar_etl('dexp_ram_agosto', '2024-08-01', '2024-08-31')
        [INFO] INÍCIO DO PROCESSO DE ETL
        [INFO] Query executada com sucesso, 150 registros retornados
        [INFO] PROCESSO DE ETL CONCLUÍDO COM SUCESSO
    
    Fluxo de Execução:
        1. PREPARAÇÃO: Carrega template e prepara contexto
        2. EXTRAÇÃO: Executa query SQL e obtém dados brutos
        3. TRANSFORMAÇÃO: Realiza agregações em diferentes níveis
        4. CARGA: Salva 7 arquivos CSV
    """
    # ========================================================================
    # FASE 1: PREPARAÇÃO
    # ========================================================================
    logger.info("="*50)
    logger.info("INÍCIO DO PROCESSO DE ETL.")
    
    # Carrega o template SQL (query.sql)
    query_template = load_query_template()
    
    # Prepara o contexto para renderização do template Jinja2
    # Estes valores substituirão os placeholders {{}} no arquivo SQL
    context = {
        "DB_PDV": os.getenv("MYSQL_DB_PDV"),      # Banco de dados de PDVs
        "DB_EVENTO": db_evento_selecionado,        # Banco do evento selecionado
        "DATA_INICIO": f"'{data_inicio}'",         # Data inicial (com aspas para SQL)
        "DATA_FIM": f"'{data_fim}'"                # Data final (com aspas para SQL)
    }
    logger.info(f"Contexto de Execução do ETL: {context}")
    
    # ========================================================================
    # FASE 2: EXTRAÇÃO
    # ========================================================================
    # Renderiza o template SQL substituindo os placeholders pelos valores reais
    sql_final = query_template.render(**context)
    
    # Executa a query e obtém os dados no nível mais granular (por vendedor)
    # fillna(0) substitui valores nulos por zero para evitar problemas nas agregações
    df_vendedor = run_query(sql_final).fillna(0)
    
    # Valida se a consulta retornou dados
    if df_vendedor.empty:
        logger.warning("A consulta não retornou nenhum dado. O processo de ETL será interrompido.")
        raise ValueError("A consulta principal do ETL não retornou nenhum registro.")

    # ========================================================================
    # FASE 3: PREPARAÇÃO PARA TRANSFORMAÇÃO
    # ========================================================================
    # Cria pasta de saída se não existir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define as métricas que serão agregadas
    # IMPORTANTE: Esta ordem é mantida consistente em todos os arquivos
    metricas = [
        'qtd_vendedores',                    # Contador de vendedores
        'qtd_leads',                         # Total de leads cadastrados
        'leads_visualizado',                 # Leads visualizados pelo vendedor
        'convite_enviado',                   # Convites enviados
        'convite_pendente_confirmacao',      # Convites aguardando resposta
        'convite_declinado_confirmacao',     # Convites declinados
        'convite_confirmado',                # Convites confirmados
        'presenca',                          # Presenças no evento
        'testdrive',                         # Test-drives realizados
        'venda'                              # Vendas concretizadas
    ]
    
    # ========================================================================
    # FASE 4: TRANSFORMAÇÃO E CARGA - VISÃO VENDEDOR (ARQUIVO MESTRE)
    # ========================================================================
    # Esta é a visão mais detalhada, servindo de base para todas as outras
    # Mantém uma linha por vendedor com todas as suas métricas
    df_vendedor_reorganizado = reorganizar_colunas(
        df_vendedor, 
        'nome_comercial',  # Primeira coluna: nome do vendedor
        ['rid', 'sid', 'grupo', 'marca', 'pdv', 'prospector_id']  # Colunas de contexto
    )
    
    # Salva em CSV
    # encoding='utf-8-sig': Adiciona BOM (Byte Order Mark) para compatibilidade com Excel
    # index=False: Não salva o índice do DataFrame como coluna
    df_vendedor_reorganizado.to_csv(
        output_dir / "visao_vendedor.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão mestre 'visao_vendedor' salva (primeira coluna: nome_comercial).")

    # ========================================================================
    # FASE 5: TRANSFORMAÇÃO E CARGA - VISÃO PDV
    # ========================================================================
    # Agrega dados por PDV/concessionária
    # Soma todas as métricas dos vendedores de cada PDV
    colunas_pdv = ['rid', 'sid', 'grupo', 'marca', 'pdv']
    df_pdv = df_vendedor.groupby(colunas_pdv, as_index=False)[metricas].sum()
    
    # Reorganiza para que 'pdv' seja a primeira coluna
    df_pdv_reorganizado = reorganizar_colunas(
        df_pdv, 
        'pdv',  # Primeira coluna: nome do PDV
        ['rid', 'sid', 'grupo', 'marca']  # Colunas de contexto
    )
    
    df_pdv_reorganizado.to_csv(
        output_dir / "visao_pdv.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão agregada 'visao_pdv' salva (primeira coluna: pdv).")

    # ========================================================================
    # FASE 6: TRANSFORMAÇÃO E CARGA - VISÃO REGIONAL
    # ========================================================================
    # Agrega dados por região geográfica
    # Soma todas as métricas dos PDVs de cada região
    df_regional = df_pdv.groupby('rid', as_index=False)[metricas].sum()
    
    # Reorganiza para que 'rid' (regional ID) seja a primeira coluna
    df_regional_reorganizado = reorganizar_colunas(df_regional, 'rid')
    
    df_regional_reorganizado.to_csv(
        output_dir / "visao_regional.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão agregada 'visao_regional' salva (primeira coluna: rid).")

    # ========================================================================
    # FASE 7: TRANSFORMAÇÃO E CARGA - VISÃO GRUPO
    # ========================================================================
    # Agrega dados por grupo empresarial
    # Soma todas as métricas dos PDVs de cada grupo
    df_grupo = df_pdv.groupby('grupo', as_index=False)[metricas].sum()
    
    # Reorganiza para que 'grupo' seja a primeira coluna
    df_grupo_reorganizado = reorganizar_colunas(df_grupo, 'grupo')
    
    df_grupo_reorganizado.to_csv(
        output_dir / "visao_grupo.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão agregada 'visao_grupo' salva (primeira coluna: grupo).")

    # ========================================================================
    # FASE 8: TRANSFORMAÇÃO E CARGA - VISÃO MARCA
    # ========================================================================
    # Agrega dados por marca de veículo
    # Soma todas as métricas dos PDVs de cada marca
    df_marca = df_pdv.groupby('marca', as_index=False)[metricas].sum()
    
    # Reorganiza para que 'marca' seja a primeira coluna
    df_marca_reorganizado = reorganizar_colunas(df_marca, 'marca')
    
    df_marca_reorganizado.to_csv(
        output_dir / "visao_marca.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão agregada 'visao_marca' salva (primeira coluna: marca).")
    
    # ========================================================================
    # FASE 9: TRANSFORMAÇÃO E CARGA - VISÃO SETOR
    # ========================================================================
    # Agrega dados por setor comercial
    # Soma todas as métricas dos PDVs de cada setor
    df_setor = df_pdv.groupby('sid', as_index=False)[metricas].sum()
    
    # Reorganiza para que 'sid' (setor ID) seja a primeira coluna
    df_setor_reorganizado = reorganizar_colunas(df_setor, 'sid')
    
    df_setor_reorganizado.to_csv(
        output_dir / "visao_setor.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão agregada 'visao_setor' salva (primeira coluna: sid).")

    # ========================================================================
    # FASE 10: TRANSFORMAÇÃO E CARGA - VISÃO NACIONAL
    # ========================================================================
    # Agrega TODOS os dados em uma única linha com totais consolidados
    # Soma todas as métricas de todos os PDVs
    # .sum(): Soma cada coluna
    # .to_frame(): Converte Series em DataFrame
    # .T: Transpõe (transforma colunas em linha)
    df_nacional = df_pdv[metricas].sum().to_frame().T
    
    df_nacional.to_csv(
        output_dir / "visao_nacional.csv", 
        index=False, 
        encoding='utf-8-sig'
    )
    logger.info("Visão agregada 'visao_nacional' salva.")
    
    # ========================================================================
    # CONCLUSÃO DO ETL
    # ========================================================================
    logger.info("PROCESSO DE ETL CONCLUÍDO COM SUCESSO.")
    logger.info("="*50)

# ============================================================================
# FUNÇÕES PRIVADAS (USO INTERNO)
# ============================================================================

def load_query_template() -> Template:
    """
    Carrega o conteúdo do arquivo SQL como um template Jinja2.
    
    O arquivo query.sql contém placeholders como {{DB_EVENTO}} que são
    substituídos dinamicamente pelos valores corretos durante a execução.
    
    Returns:
        jinja2.Template: Objeto template pronto para renderização
        
    Example:
        >>> template = load_query_template()
        >>> sql = template.render(DB_EVENTO='dexp_ram_agosto', ...)
    """
    with open(BASE_DIR / "query.sql", "r", encoding="utf-8") as f:
        return Template(f.read())

def run_query(sql_query: str) -> pd.DataFrame:
    """
    Executa a consulta SQL no banco de dados e retorna os dados como DataFrame.
    
    Utiliza SQLAlchemy para executar a query e pandas para carregar os
    resultados diretamente em um DataFrame, facilitando a manipulação.
    
    Args:
        sql_query (str): Query SQL completa a ser executada
    
    Returns:
        pd.DataFrame: Dados retornados pela consulta
        
    Comportamento:
        - Abre uma conexão com o banco
        - Executa a query usando text() do SQLAlchemy
        - Carrega resultados diretamente em DataFrame
        - Fecha a conexão automaticamente (context manager)
    
    Example:
        >>> df = run_query("SELECT * FROM tabela WHERE data > '2024-01-01'")
        >>> print(len(df))
        150
    """
    logger.info("Executando query no banco de dados...")
    
    # Abre conexão e executa query
    # with garante que a conexão será fechada mesmo se houver erro
    with engine.connect() as conn:
        # text() permite executar SQL raw com SQLAlchemy
        df = pd.read_sql(text(sql_query), conn)
    
    logger.info(f"Query executada com sucesso, {len(df)} registros retornados.")
    return df

def reorganizar_colunas(df: pd.DataFrame, coluna_id: str, 
                       colunas_contexto: list = None) -> pd.DataFrame:
    """
    Reorganiza as colunas do DataFrame para garantir ordem consistente.
    
    A função garante que:
    1. A coluna identificadora seja sempre a primeira
    2. Colunas de contexto venham logo após
    3. Métricas apareçam sempre na mesma ordem
    4. Demais colunas apareçam ao final
    
    Esta padronização facilita a leitura dos CSVs e garante consistência
    entre diferentes visões.
    
    Args:
        df (pd.DataFrame): DataFrame a ser reorganizado
        coluna_id (str): Nome da coluna que deve ser a primeira
            Ex: 'nome_comercial', 'pdv', 'rid'
        colunas_contexto (list, optional): Lista de colunas de contexto
            que devem vir após a coluna_id
            Ex: ['rid', 'sid', 'grupo', 'marca']
    
    Returns:
        pd.DataFrame: DataFrame com colunas reorganizadas
        
    Lógica de Ordenação:
        1º: Coluna ID (ex: nome_comercial, pdv, rid)
        2º: Colunas de contexto fornecidas
        3º: Métricas na ordem padrão
        4º: Outras colunas não especificadas
    
    Example:
        >>> df = pd.DataFrame({
        ...     'venda': [10], 'nome': ['João'], 'rid': ['SUL'], 'qtd_leads': [50]
        ... })
        >>> df_org = reorganizar_colunas(df, 'nome', ['rid'])
        >>> list(df_org.columns)
        ['nome', 'rid', 'qtd_leads', 'venda']
    """
    # Define ordem padrão das métricas (sempre a mesma em todos os arquivos)
    metricas = [
        'qtd_vendedores', 'qtd_leads', 'leads_visualizado', 'convite_enviado', 
        'convite_pendente_confirmacao', 'convite_declinado_confirmacao', 
        'convite_confirmado', 'presenca', 'testdrive', 'venda'
    ]
    
    # Inicia a nova ordem com a coluna ID
    nova_ordem = [coluna_id]
    
    # Adiciona colunas de contexto (se fornecidas)
    if colunas_contexto:
        for col in colunas_contexto:
            # Adiciona apenas se existir no DataFrame e não for a coluna ID
            if col in df.columns and col != coluna_id:
                nova_ordem.append(col)
    
    # Adiciona métricas que existem no DataFrame
    for metrica in metricas:
        # Adiciona apenas se existir e ainda não foi adicionada
        if metrica in df.columns and metrica not in nova_ordem:
            nova_ordem.append(metrica)
    
    # Adiciona qualquer coluna restante que não foi incluída
    # Isso garante que nenhuma coluna seja perdida
    for col in df.columns:
        if col not in nova_ordem:
            nova_ordem.append(col)
    
    # Retorna DataFrame com colunas reordenadas
    return df[nova_ordem]

# ============================================================================
# PONTO DE ENTRADA PARA TESTES ISOLADOS
# ============================================================================
if __name__ == "__main__":
    """
    Este bloco só é executado se o script for chamado diretamente.
    Serve para testes isolados do módulo ou para exibir mensagem informativa.
    
    Uso:
        python etl/etl.py
    """
    print("Este é um módulo de serviço do ETL.")
    print("Execute o `main.py` para iniciar o pipeline completo.")
    pass