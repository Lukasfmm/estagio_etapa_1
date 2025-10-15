"""
============================================================================
Módulo: main.py
Projeto: Cockpit de Relatórios
Autor: Lucas Ferreira Mendes Moraes
Data: Outubro 2025
============================================================================

DESCRIÇÃO:
    Ponto de entrada principal e orquestrador de navegação interativa do sistema.
    Implementa uma máquina de estados para gerenciar o fluxo de geração de
    relatórios através de menus interativos no terminal.

FUNCIONALIDADES:
    - Sistema de menus interativos com navegação completa (avançar/voltar)
    - Validação robusta de datas em múltiplas camadas
    - Conversão automática entre formatos de data (BR ↔ MySQL)
    - Orquestração de chamadas aos módulos ETL e build_report
    - Tratamento de erros e logging centralizado
    - Interface amigável via terminal (CLI)

MÁQUINA DE ESTADOS:
    SELECIONAR_EVENTO → SELECIONAR_DATAS → EXECUTAR_ETL → 
    SELECIONAR_TIPO_RELATORIO → [SELECIONAR_ESPECIFICIDADE] → 
    [SELECIONAR_ITEM_ESPECIFICO] → GERAR_RELATORIO → FINALIZAR

DEPENDÊNCIAS:
    - etl.py: Funções get_eventos() e executar_etl()
    - build_report.py: Funções de geração de relatórios
============================================================================
"""

# ============================================================================
# IMPORTAÇÕES
# ============================================================================
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ============================================================================
# CONFIGURAÇÃO DO PATH E AMBIENTE
# ============================================================================
# Adiciona diretório atual ao path para permitir importações relativas
sys.path.append('.')

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Importa funções dos módulos de serviço
from etl.etl import get_eventos, executar_etl
from report.build_report import (
    carregar_dados, 
    gerar_relatorio, 
    get_tipos_relatorio, 
    get_opcoes_especificas
)

# ============================================================================
# CONFIGURAÇÃO DO SISTEMA DE LOGGING
# ============================================================================
def setup_logging():
    """
    Configura o logger principal para registrar o fluxo do sistema.
    
    O logger registra todas as transições de estado, escolhas do usuário
    e erros que ocorrem durante a execução do sistema.
    
    Returns:
        logging.Logger: Instância configurada do logger
    """
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "system.log"
    
    logger = logging.getLogger("main_orchestrator")
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# ============================================================================
# FUNÇÕES DE MENU (INTERFACE COM USUÁRIO)
# ============================================================================

def _clear_screen():
    """
    Limpa a tela do terminal de forma multiplataforma.
    
    Detecta o sistema operacional e executa o comando apropriado:
    - Windows: cls
    - Linux/Mac: clear
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def _display_menu(titulo: str, opcoes: list, special_option_zero: str = None) -> int:
    """
    Exibe um menu interativo e retorna a escolha do usuário.
    
    Esta função centraliza toda a lógica de exibição e validação de menus,
    garantindo uma experiência consistente em toda a aplicação.
    
    Args:
        titulo (str): Título do menu a ser exibido
        opcoes (list): Lista de opções disponíveis
        special_option_zero (str, optional): Texto para opção [0]
            Se fornecido, adiciona opção especial no índice 0
            Ex: "Voltar", "Sair"
    
    Returns:
        int: Número da opção escolhida pelo usuário
            Retorna 0 se a opção especial for selecionada
            Retorna 1-N para as opções regulares
    
    Example:
        >>> escolha = _display_menu(
        ...     "Selecione o Evento",
        ...     ["Liga RAM", "Liga JEEP"],
        ...     "Sair"
        ... )
        --- Selecione o Evento ---
        [1] Liga RAM
        [2] Liga JEEP
        [0] Sair
        
        Digite o número da sua escolha: 1
    """
    # Cria dicionário de opções numeradas (começa em 1)
    opcoes_dict = {i + 1: val for i, val in enumerate(opcoes)}
    valid_choices = list(opcoes_dict.keys())
    
    # Adiciona opção especial [0] se fornecida
    if special_option_zero:
        valid_choices.append(0)

    # Loop até receber entrada válida
    while True:
        _clear_screen()
        print(f"--- {titulo} ---")
        
        # Exibe opções numeradas
        for num, texto in opcoes_dict.items():
            print(f"[{num}] {texto}")
        
        # Exibe opção especial [0] se existir
        if special_option_zero:
            print(f"[0] {special_option_zero}")
        
        try:
            # Solicita e valida entrada do usuário
            escolha = int(input("\nDigite o número da sua escolha: "))
            
            if escolha in valid_choices:
                return escolha
            else:
                input("\nOpção inválida. Pressione Enter para tentar novamente.")
                
        except ValueError:
            input("\nEntrada inválida. Por favor, digite um número. Pressione Enter.")

# ============================================================================
# FUNÇÕES DE VALIDAÇÃO E CONVERSÃO DE DATAS
# ============================================================================

def converter_data_br_para_mysql(data_br: str) -> str:
    """
    Converte uma data do formato brasileiro para formato MySQL.
    
    Args:
        data_br (str): Data no formato dd/mm/aaaa
            Ex: '15/08/2024'
    
    Returns:
        str: Data no formato YYYY-MM-DD
            Ex: '2024-08-15'
    
    Raises:
        ValueError: Se a data estiver em formato inválido
    
    Example:
        >>> converter_data_br_para_mysql('15/08/2024')
        '2024-08-15'
    """
    try:
        data_obj = datetime.strptime(data_br, '%d/%m/%Y')
        return data_obj.strftime('%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Data '{data_br}' está em formato inválido. Use dd/mm/aaaa")

def validar_data_no_escopo(data_str: str, start_date_str: str, end_date_str: str) -> bool:
    """
    Verifica se uma data está dentro do período permitido (escopo do evento).
    
    Args:
        data_str (str): Data a validar (formato dd/mm/aaaa)
        start_date_str (str): Data mínima permitida (formato dd/mm/aaaa)
        end_date_str (str): Data máxima permitida (formato dd/mm/aaaa)
    
    Returns:
        bool: True se a data estiver dentro do escopo, False caso contrário
    
    Example:
        >>> validar_data_no_escopo('15/08/2024', '01/08/2024', '31/08/2024')
        True
        >>> validar_data_no_escopo('15/09/2024', '01/08/2024', '31/08/2024')
        False
    """
    try:
        data = datetime.strptime(data_str, '%d/%m/%Y')
        start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
        end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
        return start_date <= data <= end_date
    except ValueError:
        return False

def solicitar_data(prompt: str, start_date: str, end_date: str, data_minima: str = None) -> str:
    """
    Solicita uma data ao usuário com validação em múltiplas camadas.
    
    Esta função implementa três níveis de validação:
    1. Formato correto (dd/mm/aaaa)
    2. Data dentro do escopo do evento
    3. Lógica de negócio (data_fim >= data_inicio)
    
    Args:
        prompt (str): Mensagem a exibir ao usuário
        start_date (str): Data mínima do escopo do evento (dd/mm/aaaa)
        end_date (str): Data máxima do escopo do evento (dd/mm/aaaa)
        data_minima (str, optional): Data mínima adicional para validação
            Usado para garantir que data_fim >= data_inicio
    
    Returns:
        str: Data validada no formato dd/mm/aaaa
    
    Example:
        >>> data_inicio = solicitar_data(
        ...     "Digite a DATA DE INÍCIO:",
        ...     "01/08/2024",
        ...     "31/08/2024"
        ... )
        >>> data_fim = solicitar_data(
        ...     "Digite a DATA DE FIM:",
        ...     "01/08/2024",
        ...     "31/08/2024",
        ...     data_minima=data_inicio
        ... )
    """
    while True:
        print(f"\n{prompt}")
        print(f"Período válido: {start_date} até {end_date}")
        data_digitada = input("Data (dd/mm/aaaa): ").strip()
        
        # ====================================================================
        # CAMADA 1: VALIDAÇÃO DE FORMATO
        # ====================================================================
        try:
            datetime.strptime(data_digitada, '%d/%m/%Y')
        except ValueError:
            print("❌ Formato inválido! Use dd/mm/aaaa (ex: 15/01/2025)")
            input("Pressione Enter para tentar novamente...")
            continue
        
        # ====================================================================
        # CAMADA 2: VALIDAÇÃO DE ESCOPO
        # ====================================================================
        if not validar_data_no_escopo(data_digitada, start_date, end_date):
            print(f"❌ Data fora do período permitido! Deve estar entre {start_date} e {end_date}")
            input("Pressione Enter para tentar novamente...")
            continue
        
        # ====================================================================
        # CAMADA 3: VALIDAÇÃO DE LÓGICA DE NEGÓCIO
        # ====================================================================
        if data_minima:
            data_dig_obj = datetime.strptime(data_digitada, '%d/%m/%Y')
            data_min_obj = datetime.strptime(data_minima, '%d/%m/%Y')
            if data_dig_obj < data_min_obj:
                print(f"❌ A data final deve ser maior ou igual à data inicial ({data_minima})")
                input("Pressione Enter para tentar novamente...")
                continue
        
        # Data válida em todas as camadas
        return data_digitada

# ============================================================================
# FUNÇÃO PRINCIPAL - ORQUESTRADOR
# ============================================================================

def main():
    """
    Gerencia o estado e a navegação da aplicação de relatórios.
    
    Esta função implementa uma máquina de estados que controla todo o fluxo
    da aplicação, desde a seleção do evento até a geração final do relatório.
    
    ESTADOS POSSÍVEIS:
        - SELECIONAR_EVENTO: Menu de seleção de evento
        - SELECIONAR_DATAS: Entrada de período de análise
        - EXECUTAR_ETL: Processamento de dados
        - SELECIONAR_TIPO_RELATORIO: Menu de tipos de relatório
        - SELECIONAR_ESPECIFICIDADE: Menu acumulado vs específico
        - SELECIONAR_ITEM_ESPECIFICO: Menu de item específico
        - GERAR_RELATORIO: Geração dos arquivos
        - FINALIZAR: Encerramento bem-sucedido
        - SAIR: Encerramento por cancelamento do usuário
    
    CONTEXTO (dicionário de estado):
        - evento: Informações do evento selecionado
        - data_inicio_mysql: Data inicial em formato MySQL
        - data_fim_mysql: Data final em formato MySQL
        - data_inicio_br: Data inicial em formato brasileiro
        - data_fim_br: Data final em formato brasileiro
        - dados: DataFrames carregados do ETL
        - tipo_relatorio: Tipo selecionado
        - valor_filtro: Filtro específico (opcional)
    """
    logger.info("="*60)
    logger.info("INICIANDO O PIPELINE DE GERAÇÃO DE RELATÓRIOS")
    logger.info("="*60)

    # ========================================================================
    # INICIALIZAÇÃO
    # ========================================================================
    estado = "SELECIONAR_EVENTO"  # Estado inicial
    contexto = {}                  # Dicionário para compartilhar dados entre estados

    # ========================================================================
    # LOOP PRINCIPAL DA MÁQUINA DE ESTADOS
    # ========================================================================
    while True:
        try:
            # ================================================================
            # ESTADO: SELECIONAR_EVENTO
            # ================================================================
            if estado == "SELECIONAR_EVENTO":
                # Carrega lista de eventos disponíveis
                eventos = get_eventos()
                opcoes_evento = [e['event_name'] for e in eventos]
                
                # Exibe menu e captura escolha
                escolha_num = _display_menu(
                    "Selecione o Evento", 
                    opcoes_evento, 
                    special_option_zero="Sair"
                )
                
                if escolha_num == 0:
                    estado = "SAIR"
                    continue

                # Armazena evento selecionado no contexto
                contexto['evento'] = eventos[escolha_num - 1]
                logger.info(f"Evento selecionado: {contexto['evento']['event_name']}")
                
                estado = "SELECIONAR_DATAS"

            # ================================================================
            # ESTADO: SELECIONAR_DATAS
            # ================================================================
            elif estado == "SELECIONAR_DATAS":
                _clear_screen()
                print("="*60)
                print(f"EVENTO SELECIONADO: {contexto['evento']['event_name']}")
                print("="*60)
                
                start_date = contexto['evento']['start_date']
                end_date = contexto['evento']['end_date']
                
                # Solicita data de início
                data_inicio_br = solicitar_data(
                    "📅 Digite a DATA DE INÍCIO do período de análise:",
                    start_date,
                    end_date
                )
                
                # Solicita data de fim (deve ser >= data_inicio)
                data_fim_br = solicitar_data(
                    "📅 Digite a DATA DE FIM do período de análise:",
                    start_date,
                    end_date,
                    data_minima=data_inicio_br
                )
                
                # Converte para formato MySQL e armazena no contexto
                contexto['data_inicio_mysql'] = converter_data_br_para_mysql(data_inicio_br)
                contexto['data_fim_mysql'] = converter_data_br_para_mysql(data_fim_br)
                contexto['data_inicio_br'] = data_inicio_br
                contexto['data_fim_br'] = data_fim_br
                
                logger.info(f"Período selecionado: {data_inicio_br} até {data_fim_br}")
                print(f"\n✅ Período confirmado: {data_inicio_br} até {data_fim_br}")
                input("\nPressione Enter para continuar...")
                
                estado = "EXECUTAR_ETL"

            # ================================================================
            # ESTADO: EXECUTAR_ETL
            # ================================================================
            elif estado == "EXECUTAR_ETL":
                logger.info("[ETAPA 1/3] Executando o processo de ETL...")
                
                # Executa pipeline de extração e transformação
                executar_etl(
                    db_evento_selecionado=contexto['evento']['db_name'],
                    data_inicio=contexto['data_inicio_mysql'],
                    data_fim=contexto['data_fim_mysql']
                )
                
                logger.info("[ETAPA 1/3] Processo de ETL concluído.")
                logger.info("[ETAPA 2/3] Carregando dados para geração do relatório...")
                
                # Carrega dados processados em memória
                contexto['dados'] = carregar_dados()
                
                estado = "SELECIONAR_TIPO_RELATORIO"

            # ================================================================
            # ESTADO: SELECIONAR_TIPO_RELATORIO
            # ================================================================
            elif estado == "SELECIONAR_TIPO_RELATORIO":
                opcoes_tipo = get_tipos_relatorio()
                
                escolha_num = _display_menu(
                    "Qual tipo de relatório você deseja gerar?", 
                    opcoes_tipo, 
                    special_option_zero="Voltar"
                )
                
                if escolha_num == 0:
                    estado = "SELECIONAR_EVENTO"
                    continue

                contexto['tipo_relatorio'] = opcoes_tipo[escolha_num - 1]
                logger.info(f"Tipo de relatório selecionado: {contexto['tipo_relatorio']}")
                
                # Nacional não precisa de especificidade
                if contexto['tipo_relatorio'] == "Nacional":
                    contexto['valor_filtro'] = None
                    estado = "GERAR_RELATORIO"
                else:
                    estado = "SELECIONAR_ESPECIFICIDADE"

            # ================================================================
            # ESTADO: SELECIONAR_ESPECIFICIDADE
            # ================================================================
            elif estado == "SELECIONAR_ESPECIFICIDADE":
                tipo_simples = contexto['tipo_relatorio'].replace('Por ', '')
                
                opcoes_espec = [
                    f"Todos os dados da categoria {tipo_simples} (Acumulado)", 
                    f"Um {tipo_simples} Específico"
                ]
                
                escolha_num = _display_menu(
                    f"Relatório {contexto['tipo_relatorio']}", 
                    opcoes_espec, 
                    special_option_zero="Voltar"
                )

                if escolha_num == 0:
                    estado = "SELECIONAR_TIPO_RELATORIO"
                    continue
                
                if "Específico" in opcoes_espec[escolha_num - 1]:
                    estado = "SELECIONAR_ITEM_ESPECIFICO"
                else:  # Acumulado
                    contexto['valor_filtro'] = None
                    logger.info(f"Selecionado: {tipo_simples} Acumulado")
                    estado = "GERAR_RELATORIO"

            # ================================================================
            # ESTADO: SELECIONAR_ITEM_ESPECIFICO
            # ================================================================
            elif estado == "SELECIONAR_ITEM_ESPECIFICO":
                # Busca opções disponíveis nos dados
                opcoes_item = get_opcoes_especificas(
                    contexto['tipo_relatorio'], 
                    contexto['dados']
                )
                tipo_simples = contexto['tipo_relatorio'].replace('Por ', '')
                
                escolha_num = _display_menu(
                    f"Selecione o {tipo_simples}", 
                    opcoes_item, 
                    special_option_zero="Voltar"
                )

                if escolha_num == 0:
                    estado = "SELECIONAR_ESPECIFICIDADE"
                    continue
                
                contexto['valor_filtro'] = opcoes_item[escolha_num - 1]
                logger.info(f"Item específico selecionado: {contexto['valor_filtro']}")
                
                estado = "GERAR_RELATORIO"

            # ================================================================
            # ESTADO: GERAR_RELATORIO
            # ================================================================
            elif estado == "GERAR_RELATORIO":
                logger.info("[ETAPA 3/3] Iniciando a geração do arquivo do relatório...")
                
                # Gera relatório DOCX e PDF
                gerar_relatorio(
                    tipo=contexto['tipo_relatorio'],
                    dados=contexto['dados'],
                    contexto_evento=contexto['evento'],
                    valor_filtro=contexto.get('valor_filtro'),
                    data_inicio_br=contexto['data_inicio_br'],
                    data_fim_br=contexto['data_fim_br']
                )
                
                estado = "FINALIZAR"

            # ================================================================
            # ESTADO: FINALIZAR
            # ================================================================
            elif estado == "FINALIZAR":
                logger.info("="*60)
                logger.info("PIPELINE FINALIZADO COM SUCESSO!")
                logger.info("="*60)
                break

            # ================================================================
            # ESTADO: SAIR
            # ================================================================
            elif estado == "SAIR":
                logger.info("Processo interrompido pelo usuário.")
                logger.info("PIPELINE FINALIZADO.")
                print("\nSaindo do programa. Até logo!")
                break

        # ====================================================================
        # TRATAMENTO DE EXCEÇÕES
        # ====================================================================
        except (SystemExit, KeyboardInterrupt):
            # Usuário pressionou Ctrl+C
            estado = "SAIR"
            
        except Exception as e:
            # Erro inesperado durante execução
            logger.critical("="*60)
            logger.critical(f"Ocorreu um erro crítico que interrompeu o pipeline: {e}", exc_info=True)
            logger.critical("PIPELINE FINALIZADO COM ERRO.")
            print(f"\nOcorreu um erro fatal: {e}")
            break

# ============================================================================
# PONTO DE ENTRADA DO PROGRAMA
# ============================================================================
if __name__ == "__main__":
    """
    Ponto de entrada quando o script é executado diretamente.
    
    Uso:
        python main.py
    """
    main()