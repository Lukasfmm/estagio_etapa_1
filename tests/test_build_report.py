# Arquivo: tests/test_build_report.py

import pandas as pd
import logging

# Importamos as funções que queremos testar (note o _ antes de _preparar_contexto_relatorio)
from report.build_report import safe_division, _preparar_contexto_relatorio

# --- Testes para safe_division ---
def test_safe_division_por_zero():
    """Verifica se a divisão por zero retorna 0.0."""
    logging.info("Executando teste: test_safe_division_por_zero")
    assert safe_division(10, 0) == 0.0

def test_safe_division_normal():
    """Verifica se uma divisão normal funciona."""
    logging.info("Executando teste: test_safe_division_normal")
    assert safe_division(10, 2) == 5.0

# --- Novo Teste para a Lógica de Cálculo ---
def test_preparar_contexto_relatorio_nacional():
    """
    Testa se os cálculos e seleções de dados para o relatório Nacional estão corretos.
    """
    logging.info("Executando teste: test_preparar_contexto_relatorio_nacional")

    # 1. Criação de Dados Falsos (simulando os arquivos CSV)
    dados_falsos = {
        "visao_nacional": pd.DataFrame([{
            'qtd_leads': 1000, 'leads_visualizado': 800, 'convite_enviado': 500,
            'convite_declinado_confirmacao': 100, 'convite_confirmado': 100,
            'presenca': 80, 'testdrive': 40, 'venda': 20, 'qtd_vendedores': 50
        }]),
        "visao_regional": pd.DataFrame([
            {'rid': 'SUL', 'venda': 5},
            {'rid': 'SUDESTE', 'venda': 15}
        ])
    }
    contexto_evento_falso = {"event_name": "Evento de Teste"}

    # 2. Execução da função que queremos testar
    contexto, df_pa, mapa_pa = _preparar_contexto_relatorio(
        tipo="Nacional",
        dados=dados_falsos,
        contexto_evento=contexto_evento_falso
    )

    # 3. Verificações (Asserts)
    # Verifica se os valores diretos estão corretos
    assert contexto["{{tipo_visao}}"] == "Nacional"
    assert contexto["{{nome_evento}}"] == "Evento de Teste"
    assert contexto["{{total_contatos}}"] == "1.000"
    
    # Verifica se os CÁLCULOS estão corretos
    assert contexto["{{total_sem_resposta}}"] == "300" # 500 enviados - 100 confirmados - 100 declinados
    assert contexto["{{perc_confirmados_presencas}}"] == "80,00" # 80 presenças / 100 confirmados * 100
    
    # Verifica se os dados para os Pontos de Atenção foram selecionados corretamente
    assert df_pa.shape[0] == 2 # Deve ter encontrado as 2 regiões
    assert 'rid' in mapa_pa # O mapa de colunas deve ser para 'rid'