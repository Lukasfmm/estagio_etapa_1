/*
============================================================================
Arquivo: query.sql
Projeto: Cockpit de Relatórios
Autor: Lucas Ferreira Mendes Moraes
Data: Outubro 2025
============================================================================

DESCRIÇÃO:
    Query SQL mestre que extrai todos os dados de performance de eventos
    no nível mais granular (por vendedor). Esta query utiliza CTEs
    (Common Table Expressions) para organizar a lógica de extração e
    agregação de dados de múltiplas fontes.

ESTRUTURA:
    - 8 CTEs organizadas por domínio de dados
    - SELECT principal com agregação no nível de vendedor
    - Filtro temporal aplicado em todas as subconsultas relevantes

TEMPLATE JINJA2:
    Este arquivo utiliza placeholders que são substituídos dinamicamente:
    - {{DB_PDV}}: Nome do banco de dados de PDVs
    - {{DB_EVENTO}}: Nome do banco de dados do evento específico
    - {{DATA_INICIO}}: Data inicial do período (formato: 'YYYY-MM-DD')
    - {{DATA_FIM}}: Data final do período (formato: 'YYYY-MM-DD')

FONTES DE DADOS:
    - {{DB_PDV}}.view_pdv_automotive: Dados dos PDVs
    - {{DB_EVENTO}}.concessionaria: Status e objetivos dos PDVs no evento
    - {{DB_EVENTO}}.prospectores: Dados dos vendedores
    - {{DB_EVENTO}}.leads: Informações dos leads
    - {{DB_EVENTO}}.atividades: Registros de atividades realizadas

RESULTADO:
    Dataset com uma linha por vendedor contendo:
    - Identificação: rid, sid, grupo, marca, pdv, prospector_id, nome_comercial
    - Métricas: qtd_vendedores, qtd_leads, leads_visualizado, convite_enviado,
               convite_pendente_confirmacao, convite_declinado_confirmacao,
               convite_confirmado, presenca, testdrive, venda
============================================================================
*/

-- ============================================================================
-- CTE 1: DADOS DO PDV
-- ============================================================================
-- Combina informações cadastrais dos PDVs com dados específicos do evento
WITH cte_pdv AS (
    SELECT
        c.dealer_id,                    -- ID único do dealer/PDV
        c.pdv,                          -- Nome do PDV
        c.marca,                        -- Marca de veículos
        c.grupo,                        -- Grupo empresarial
        c.`mid`,                        -- ID da marca
        c.rid,                          -- ID da região
        c.sid,                          -- ID do setor
        c.coordenadas,                  -- Coordenadas geográficas
        dexp.objetivo,                  -- Objetivo definido para o evento
        UCASE(CONCAT(                   -- Nome do gerente formatado (MAIÚSCULAS)
            SUBSTRING_INDEX(dexp.nome_gerente, ' ', 1), 
            ' ', 
            SUBSTRING_INDEX(dexp.nome_gerente, ' ', -1)
        )) AS nome_gerente,
        dexp.status,                    -- Status do PDV
        dexp.status_evento              -- Status específico do evento
    FROM {{ DB_PDV }}.view_pdv_automotive c
    INNER JOIN {{ DB_EVENTO }}.concessionaria dexp
        ON dexp.dealer_id = c.dealer_id
),

-- ============================================================================
-- CTE 2: DADOS DO VENDEDOR
-- ============================================================================
-- Informações dos vendedores (prospectores) e participação em games
cte_vendedores AS (
    SELECT
        p.prospector_id,                -- ID único do vendedor
        p.dealer_id,                    -- ID do PDV ao qual pertence
        p.nome_comercial,               -- Nome do vendedor
        p.telefone,                     -- Telefone de contato
        p.simplecard_link,              -- Link do cartão digital
        
        -- Contadores de participação em games (atividades gamificadas)
        (SELECT COUNT(*) FROM {{ DB_EVENTO }}.atividades a 
         WHERE p.prospector_id = a.prospector_id AND a.tipo_atividade_id = 3) AS game_1,
        (SELECT COUNT(*) FROM {{ DB_EVENTO }}.atividades a 
         WHERE p.prospector_id = a.prospector_id AND a.tipo_atividade_id = 4) AS game_2,
        (SELECT COUNT(*) FROM {{ DB_EVENTO }}.atividades a 
         WHERE p.prospector_id = a.prospector_id AND a.tipo_atividade_id = 5) AS game_3,
        (SELECT COUNT(*) FROM {{ DB_EVENTO }}.atividades a 
         WHERE p.prospector_id = a.prospector_id AND a.tipo_atividade_id = 6) AS game_4,
        (SELECT COUNT(*) FROM {{ DB_EVENTO }}.atividades a 
         WHERE p.prospector_id = a.prospector_id AND a.tipo_atividade_id = 7) AS game_5,
        (SELECT COUNT(*) FROM {{ DB_EVENTO }}.atividades a 
         WHERE p.prospector_id = a.prospector_id AND a.tipo_atividade_id = 8) AS game_6
    FROM {{ DB_EVENTO }}.prospectores p
),

-- ============================================================================
-- CTE 3: LEAD - INFORMAÇÕES BÁSICAS
-- ============================================================================
-- Dados fundamentais de cada lead cadastrado
cte_lead_info AS (
    SELECT
        l.lead_id,                      -- ID único do lead
        l.dealer_id,                    -- PDV responsável
        l.prospector_id,                -- Vendedor responsável
        CONCAT(l.nome, ' ', l.sobrenome) AS cliente  -- Nome completo do cliente
    FROM {{ DB_EVENTO }}.leads l
),

-- ============================================================================
-- CTE 4: LEAD - REGISTRO
-- ============================================================================
-- Contabiliza leads registrados no período de análise
cte_lead_registro AS (
    SELECT
        l.lead_id,
        1 AS registro,                  -- Flag de registro (sempre 1 para leads registrados)
        l.registro_data                 -- Data de registro
    FROM {{ DB_EVENTO }}.leads l
    WHERE l.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
),

-- ============================================================================
-- CTE 5: LEAD - VISUALIZAÇÃO
-- ============================================================================
-- Rastreia se o lead foi visualizado pelo vendedor
cte_lead_visualizacao AS (
    SELECT
        l.lead_id,
        l.visualizado,                  -- Flag booleano de visualização
        CAST(JSON_UNQUOTE(JSON_EXTRACT(l.custom, '$.visualizado_data')) AS date) AS registro_data
    FROM {{ DB_EVENTO }}.leads l
    WHERE l.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
),

-- ============================================================================
-- CTE 6: LEAD - ENVIO DE CONVITE
-- ============================================================================
-- Rastreia envio de convites para o evento
cte_lead_convite AS (
    SELECT
        l.lead_id,
        -- Converte string JSON 'true'/'false' para 1/0
        IF(JSON_UNQUOTE(JSON_EXTRACT(l.custom, '$.contacted')) = 'true', 1, 0) AS convite_enviado,
        CAST(JSON_UNQUOTE(JSON_EXTRACT(l.custom, '$.contacted_at')) AS date) AS registro_data
    FROM {{ DB_EVENTO }}.leads l
    WHERE l.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
),

-- ============================================================================
-- CTE 7: LEAD - CONFIRMAÇÃO
-- ============================================================================
-- Status de confirmação do convite (pendente, declinado, confirmado)
cte_lead_confirmacao AS (
    SELECT
        l.lead_id,
        -- lead_presence pode ser: 0 (pendente), -1 (declinado), 1 (confirmado)
        IF(l.lead_presence = 0, 1, 0) AS convite_pendente,
        IF(l.lead_presence = -1, 1, 0) AS convite_declinado,
        IF(l.lead_presence = 1, 1, 0) AS convite_confirmado,
        DATE(l.confirmado_data) AS registro_data
    FROM {{ DB_EVENTO }}.leads l
    WHERE l.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
),

-- ============================================================================
-- CTE 8: LEAD - ATIVIDADES (PRESENÇA, TEST-DRIVE, VENDA)
-- ============================================================================
-- Contabiliza atividades de conversão realizadas
cte_lead_atividades AS (
    SELECT
        l.lead_id,
        
        -- Presença no evento (tipo_atividade_id = 10)
        (SELECT COUNT(*) 
         FROM {{ DB_EVENTO }}.atividades a 
         WHERE a.lead_id = l.lead_id 
           AND a.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
           AND a.tipo_atividade_id IN (10)
        ) AS presenca,
        
        -- Test-drive realizado (tipo_atividade_id = 11)
        (SELECT COUNT(*) 
         FROM {{ DB_EVENTO }}.atividades a 
         WHERE a.lead_id = l.lead_id 
           AND a.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
           AND a.tipo_atividade_id IN (11)
        ) AS testdrive,
        
        -- Venda concretizada (tipo_atividade_id = 2 ou 14)
        (SELECT COUNT(*) 
         FROM {{ DB_EVENTO }}.atividades a 
         WHERE a.lead_id = l.lead_id 
           AND a.registro_data BETWEEN {{ DATA_INICIO }} AND {{ DATA_FIM }}
           AND a.tipo_atividade_id IN (2, 14)
        ) AS venda
        
    FROM {{ DB_EVENTO }}.leads l
)

-- ============================================================================
-- CONSULTA PRINCIPAL
-- ============================================================================
-- Combina todas as CTEs e agrega dados no nível de vendedor
SELECT
    -- Identificação e contexto
    pdv.rid,                            -- Região
    pdv.sid,                            -- Setor
    pdv.grupo,                          -- Grupo empresarial
    pdv.marca,                          -- Marca
    pdv.pdv,                            -- Nome do PDV
    p.prospector_id,                    -- ID do vendedor
    p.nome_comercial,                   -- Nome do vendedor
    
    -- Métricas agregadas
    1 AS qtd_vendedores,                -- Sempre 1 (usado para contagem em agregações futuras)
    SUM(r.registro) AS qtd_leads,       -- Total de leads registrados
    SUM(v.visualizado) AS leads_visualizado,  -- Leads visualizados
    SUM(c.convite_enviado) AS convite_enviado,  -- Convites enviados
    SUM(co.convite_pendente) AS convite_pendente_confirmacao,  -- Convites pendentes
    SUM(co.convite_declinado) AS convite_declinado_confirmacao,  -- Convites declinados
    SUM(co.convite_confirmado) AS convite_confirmado,  -- Convites confirmados
    SUM(a.presenca) AS presenca,        -- Presenças registradas
    SUM(a.testdrive) AS testdrive,      -- Test-drives realizados
    SUM(a.venda) AS venda               -- Vendas concretizadas

FROM cte_pdv pdv
    -- LEFT JOINs preservam todos os vendedores, mesmo sem atividade
    LEFT JOIN cte_vendedores p ON pdv.dealer_id = p.dealer_id
    LEFT JOIN cte_lead_info i ON p.prospector_id = i.prospector_id
    LEFT JOIN cte_lead_registro r ON i.lead_id = r.lead_id
    LEFT JOIN cte_lead_visualizacao v ON i.lead_id = v.lead_id
    LEFT JOIN cte_lead_convite c ON i.lead_id = c.lead_id
    LEFT JOIN cte_lead_confirmacao co ON i.lead_id = co.lead_id
    LEFT JOIN cte_lead_atividades a ON i.lead_id = a.lead_id

WHERE 
    -- Filtra apenas vendedores válidos (com ID)
    p.prospector_id IS NOT NULL
    
GROUP BY 
    -- Agrupa por vendedor individual
    pdv.rid,
    pdv.sid,
    pdv.grupo,
    pdv.marca,
    pdv.pdv,
    p.prospector_id,
    p.nome_comercial
;