"""
============================================================================
Módulo: connection_db.py
Projeto: Cockpit de Relatórios
Autor: Lucas Ferreira Mendes Moraes
Data: Outubro 2025
============================================================================

DESCRIÇÃO:
    Gerencia a conexão com o banco de dados MySQL utilizando SQLAlchemy.
    Este módulo configura o engine de conexão que será utilizado pelos
    outros módulos do sistema para executar consultas SQL.

CARACTERÍSTICAS:
    - Carrega credenciais de forma segura através de variáveis de ambiente
    - Cria conexão ao servidor MySQL (sem banco específico)
    - Fornece função de teste de conectividade
    - Utiliza SQLAlchemy para abstração do banco de dados

OBSERVAÇÕES:
    - A URL de conexão NÃO especifica um banco de dados, pois o sistema
      trabalha com múltiplos bancos (um para cada evento)
    - O nome do banco é especificado dinamicamente nas queries SQL
    - Nunca versione o arquivo .env com credenciais reais
============================================================================
"""

# ============================================================================
# IMPORTAÇÕES
# ============================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# ============================================================================
# CARREGAMENTO DE VARIÁVEIS DE AMBIENTE
# ============================================================================
# Carrega as variáveis do arquivo .env para as variáveis de ambiente do SO
load_dotenv()

# ============================================================================
# OBTENÇÃO DAS CREDENCIAIS
# ============================================================================
# Obtém as informações de conexão das variáveis de ambiente
DB_HOST = os.getenv('DB_HOST')          # Ex: localhost ou IP do servidor
DB_PORT = os.getenv('DB_PORT')          # Ex: 3306 (porta padrão do MySQL)
DB_USER = os.getenv('DB_USER')          # Usuário do banco de dados
DB_PASSWORD = os.getenv('DB_PASSWORD')  # Senha do usuário

# ============================================================================
# CONSTRUÇÃO DA URL DE CONEXÃO
# ============================================================================
# Formato: mysql+pymysql://usuario:senha@host:porta
# IMPORTANTE: Não inclui o nome do banco, apenas conecta ao servidor
# O banco específico será selecionado nas queries através do template Jinja2
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"

# ============================================================================
# CRIAÇÃO DO ENGINE SQLALCHEMY
# ============================================================================
# Engine: objeto que gerencia as conexões com o banco de dados
# echo=False: desabilita logs verbosos do SQLAlchemy (deixa logs mais limpos)
engine = create_engine(DATABASE_URL, echo=False)

# ============================================================================
# CONFIGURAÇÃO DA SESSÃO (PARA USO FUTURO)
# ============================================================================
# SessionLocal: fábrica de sessões para operações futuras com ORM
# Atualmente não é utilizada, mas mantida para expansões futuras do sistema
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# FUNÇÃO DE TESTE DE CONEXÃO
# ============================================================================
def test_connection():
    """
    Testa a conectividade com o servidor MySQL.
    
    Esta função tenta estabelecer uma conexão com o servidor e imprime
    uma mensagem de sucesso ou erro. Útil para validar as credenciais
    e a disponibilidade do servidor antes de executar o sistema.
    
    Uso:
        >>> from config.connection_db import test_connection
        >>> test_connection()
        Conexão com o servidor MySQL bem-sucedida!
    
    Raises:
        Exception: Qualquer erro de conexão é capturado e exibido
    """
    try:
        # Tenta abrir uma conexão temporária
        with engine.connect() as conn:
            print("Conexão com o servidor MySQL bem-sucedida!")
    except Exception as e:
        # Captura e exibe qualquer erro de conexão
        print(f"Falha na conexão com o servidor MySQL: {e}")

# ============================================================================
# PONTO DE ENTRADA PARA TESTES ISOLADOS
# ============================================================================
if __name__ == "__main__":
    """
    Permite testar a conexão executando este arquivo diretamente.
    
    Uso:
        python config/connection_db.py
    """
    print("Testando conexão com o banco de dados...")
    test_connection()