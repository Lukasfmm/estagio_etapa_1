# Arquivo: tests/test_connection_db.py

import importlib
import logging
from config import connection_db

def test_database_url_creation(monkeypatch):
    """
    Testa se a DATABASE_URL é montada corretamente a partir das variáveis de ambiente.
    """
    logging.info("Iniciando teste: test_database_url_creation")
    
    # 1. Define variáveis de ambiente falsas
    monkeypatch.setenv("DB_HOST", "fake_host")
    monkeypatch.setenv("DB_PORT", "1234")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")

    # 2. Recarrega o módulo para usar as novas variáveis
    importlib.reload(connection_db)

    # 3. Define o resultado esperado
    expected_url = "mysql+pymysql://test_user:test_pass@fake_host:1234"

    # 4. Verifica se a URL gerada é a esperada
    assert connection_db.DATABASE_URL == expected_url
    logging.info("Teste finalizado com sucesso.")