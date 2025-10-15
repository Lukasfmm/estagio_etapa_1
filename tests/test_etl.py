# Arquivo: tests/test_etl.py

import pandas as pd
from pandas.testing import assert_frame_equal
import logging

# Importa a função que queremos testar (com o caminho corrigido)
from etl.etl import executar_etl

def test_agregacao_regional():
    """
    Testa se a lógica de agrupar por região funciona como esperado.
    """
    logging.info("Iniciando teste: test_agregacao_regional")
    
    # 1. Criação de dados de teste
    dados_teste = {
        'rid': ['SUL', 'SUDESTE', 'SUL'],
        'qtd_leads': [10, 20, 5],
        'venda': [1, 2, 0]
    }
    df_detalhado = pd.DataFrame(dados_teste)
    
    metricas_teste = ['qtd_leads', 'venda']

    # 2. Execução da lógica de agregação
    df_regional_calculado = df_detalhado.groupby('rid', as_index=False)[metricas_teste].sum()

    # 3. Criação do resultado esperado
    dados_esperados = {
        'rid': ['SUL', 'SUDESTE'],
        'qtd_leads': [15, 20],
        'venda': [1, 2]
    }
    df_regional_esperado = pd.DataFrame(dados_esperados)

    # 4. Ordena ambos os DataFrames para garantir uma comparação consistente
    df_regional_calculado = df_regional_calculado.sort_values(by='rid').reset_index(drop=True)
    df_regional_esperado = df_regional_esperado.sort_values(by='rid').reset_index(drop=True)

    # 5. Verificação final
    assert_frame_equal(df_regional_calculado, df_regional_esperado)
    logging.info("Teste finalizado com sucesso.")

def test_executar_etl_gera_todos_os_csvs(monkeypatch, tmp_path):
    """
    Teste de integração para a função executar_etl.
    Verifica se todos os arquivos CSV são criados corretamente.
    """
    logging.info("Iniciando teste de integração: test_executar_etl_gera_todos_os_csvs")

    # 1. Preparação (Setup)
    dados_teste_completos = {
        'rid': ['SUL', 'SUDESTE'], 'sid': [10, 20], 'grupo': ['Grupo A', 'Grupo B'],
        'marca': ['Marca X', 'Marca Y'], 'pdv': ['PDV A', 'PDV B'],
        'prospector_id': [101, 202], 'nome_comercial': ['Vendedor 1', 'Vendedor 2'],
        'qtd_vendedores': [1, 1], 'qtd_leads': [10, 20], 'leads_visualizado': [8, 18],
        'convite_enviado': [7, 15], 'convite_pendente_confirmacao': [1, 1],
        'convite_declinado_confirmacao': [2, 3], 'convite_confirmado': [4, 11],
        'presenca': [3, 9], 'testdrive': [1, 5], 'venda': [1, 2]
    }
    df_fake_db_return = pd.DataFrame(dados_teste_completos)

    # Cria uma função "mock" (falsa) que substituirá a 'run_query' real
    def mock_run_query(sql_query: str):
        logging.info("CHAMADA MOCK: run_query foi interceptada e retornou dados de teste.")
        return df_fake_db_return

    # Usa o monkeypatch para substituir a função real pela nossa versão falsa
    monkeypatch.setattr('etl.etl.run_query', mock_run_query)

    # Usa o monkeypatch para redirecionar a saída para uma pasta temporária
    output_dir_teste = tmp_path / "csv"
    monkeypatch.setattr('etl.etl.output_dir', output_dir_teste)

    # 2. Execução
    executar_etl(db_evento_selecionado="banco_de_teste")

    # 3. Verificação (Asserts)
    logging.info(f"Verificando arquivos na pasta temporária: {output_dir_teste}")
    assert (output_dir_teste / "visao_vendedor.csv").exists()
    assert (output_dir_teste / "visao_pdv.csv").exists()
    assert (output_dir_teste / "visao_regional.csv").exists()
    assert (output_dir_teste / "visao_grupo.csv").exists()
    assert (output_dir_teste / "visao_marca.csv").exists()
    assert (output_dir_teste / "visao_setor.csv").exists()
    assert (output_dir_teste / "visao_nacional.csv").exists()
    logging.info("Teste de integração finalizado com sucesso. Todos os arquivos foram criados.")