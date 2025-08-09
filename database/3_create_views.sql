-- -----------------------------------------------------------
-- Views para análise da ambiência do aviário (Tabela medicoes)
-- -----------------------------------------------------------

DROP VIEW IF EXISTS stats_por_data;
CREATE VIEW stats_por_data AS
SELECT
    DATE(Fecha) as Fecha,
    COUNT(*) as num_registros,
    ROUND(AVG(NH3), 1) as media_nh3,
    ROUND(MIN(NH3), 1) as min_nh3,
    ROUND(MAX(NH3), 1) as max_nh3,
    ROUND(AVG(Temperatura), 1) as media_temperatura,
    ROUND(MIN(Temperatura), 1) as min_temperatura,
    ROUND(MAX(Temperatura), 1) as max_temperatura,
    ROUND(AVG(Humedad), 1) as media_humedad,
    ROUND(MIN(Humedad), 1) as min_humedad,
    ROUND(MAX(Humedad), 1) as max_humedad
FROM medicoes
GROUP BY DATE(Fecha);


DROP VIEW IF EXISTS stats_por_arquivo;
CREATE VIEW stats_por_arquivo AS
SELECT
    Nome_Arquivo,
    COUNT(*) as num_registros,
    ROUND(AVG(NH3), 1) as media_nh3,
    ROUND(MIN(NH3), 1) as min_nh3,
    ROUND(MAX(NH3), 1) as max_nh3,
    ROUND(AVG(Temperatura), 1) as media_temperatura,
    ROUND(MIN(Temperatura), 1) as min_temperatura,
    ROUND(MAX(Temperatura), 1) as max_temperatura,
    ROUND(AVG(Humedad), 1) as media_humedad,
    ROUND(MIN(Humedad), 1) as min_humedad,
    ROUND(MAX(Humedad), 1) as max_humedad
FROM medicoes
GROUP BY Nome_Arquivo;


DROP VIEW IF EXISTS tendencias_por_hora;
CREATE VIEW tendencias_por_hora AS
SELECT
    SUBSTR(Hora, 1, 2) as hora_do_dia,
    COUNT(*) as num_registros,
    ROUND(AVG(NH3), 1) as media_nh3,
    ROUND(AVG(Temperatura), 1) as media_temperatura,
    ROUND(AVG(Humedad), 1) as media_humedad
FROM medicoes
GROUP BY hora_do_dia;


DROP VIEW IF EXISTS tendencias_por_hora_aviario;
CREATE VIEW tendencias_por_hora_aviario AS
SELECT
    SUBSTR(Hora, 1, 2) as hora_do_dia,
    ID_Aviario,
    COUNT(*) as num_registros,
    ROUND(AVG(NH3), 1) as media_nh3,
    ROUND(AVG(Temperatura), 1) as media_temperatura,
    ROUND(AVG(Humedad), 1) as media_humedad
FROM medicoes
GROUP BY hora_do_dia, ID_Aviario;


DROP VIEW IF EXISTS alertas_nh3_elevado;
CREATE VIEW alertas_nh3_elevado AS
SELECT
    DATE(Fecha) as Fecha,
    Hora,
    NH3,
    Temperatura,
    Humedad,
    ID_Aviario,
    Nome_Arquivo
FROM medicoes
WHERE NH3 > 20
ORDER BY DATE(Fecha), Hora;

-- -----------------------------------------------------------
-- Views de correlação e desempenho (combinando medicoes e tratamentos)
-- -----------------------------------------------------------

DROP VIEW IF EXISTS comparacao_tratamentos_linhagem;
CREATE VIEW comparacao_tratamentos_linhagem AS
SELECT
    t.linhagem,
    COUNT(*) as num_registros,
    ROUND(AVG(m.NH3), 1) as media_nh3,
    ROUND(MIN(m.NH3), 1) as min_nh3,
    ROUND(MAX(m.NH3), 1) as max_nh3,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura,
    ROUND(MIN(m.Temperatura), 1) as min_temperatura,
    ROUND(MAX(m.Temperatura), 1) as max_temperatura,
    ROUND(AVG(m.Humedad), 1) as media_humedad,
    ROUND(MIN(m.Humedad), 1) as min_humedad,
    ROUND(MAX(m.Humedad), 1) as max_humedad
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY t.linhagem;


DROP VIEW IF EXISTS comparacao_tratamentos_por_idade_lote;
CREATE VIEW comparacao_tratamentos_por_idade_lote AS
SELECT
    t.teste,
    m.idade_lote,
    COUNT(*) as num_registros,
    ROUND(AVG(m.NH3), 1) as media_nh3,
    ROUND(MIN(m.NH3), 1) as min_nh3,
    ROUND(MAX(m.NH3), 1) as max_nh3,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura,
    ROUND(MIN(m.Temperatura), 1) as min_temperatura,
    ROUND(MAX(m.Temperatura), 1) as max_temperatura,
    ROUND(AVG(m.Humedad), 1) as media_humedad,
    ROUND(MIN(m.Humedad), 1) as min_humedad,
    ROUND(MAX(m.Humedad), 1) as max_humedad
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY t.teste, m.idade_lote
ORDER BY t.teste, m.idade_lote;


DROP VIEW IF EXISTS comparacao_tratamentos_por_data;
CREATE VIEW comparacao_tratamentos_por_data AS
SELECT
    DATE(m.Fecha) as Fecha,
    t.teste,
    COUNT(*) as num_registros,
    ROUND(AVG(m.NH3), 1) as media_nh3,
    ROUND(MIN(m.NH3), 1) as min_nh3,
    ROUND(MAX(m.NH3), 1) as max_nh3,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura,
    ROUND(MIN(m.Temperatura), 1) as min_temperatura,
    ROUND(MAX(m.Temperatura), 1) as max_temperatura,
    ROUND(AVG(m.Humedad), 1) as media_humedad,
    ROUND(MIN(m.Humedad), 1) as min_humedad,
    ROUND(MAX(m.Humedad), 1) as max_humedad
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY DATE(m.Fecha), t.teste;


DROP VIEW IF EXISTS comparacao_tratamentos_por_hora;
CREATE VIEW comparacao_tratamentos_por_hora AS
SELECT
    SUBSTR(m.Hora, 1, 2) as hora_do_dia,
    t.teste,
    COUNT(*) as num_registros,
    ROUND(AVG(m.NH3), 1) as media_nh3,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura,
    ROUND(AVG(m.Humedad), 1) as media_humedad
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY hora_do_dia, t.teste;


DROP VIEW IF EXISTS comparacao_tratamentos_geral;
CREATE VIEW comparacao_tratamentos_geral AS
SELECT
    t.teste,
    COUNT(*) as num_registros,
    ROUND(AVG(m.NH3), 1) as media_nh3,
    ROUND(MIN(m.NH3), 1) as min_nh3,
    ROUND(MAX(m.NH3), 1) as max_nh3,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura,
    ROUND(MIN(m.Temperatura), 1) as min_temperatura,
    ROUND(MAX(m.Temperatura), 1) as max_temperatura,
    ROUND(AVG(m.Humedad), 1) as media_humedad,
    ROUND(MIN(m.Humedad), 1) as min_humedad,
    ROUND(MAX(m.Humedad), 1) as max_humedad
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY t.teste;


DROP VIEW IF EXISTS comparacao_condenacoes_por_ambiencia;
CREATE VIEW comparacao_condenacoes_por_ambiencia AS
SELECT
    t.lote_composto,
    t.teste,
    t.linhagem,
    t.pc_cond_pes,
    t.pc_cond_aero,
    ROUND(AVG(m.NH3), 1) as media_nh3_lote,
    ROUND(AVG(m.Humedad), 1) as media_humedad_lote
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY t.lote_composto;


DROP VIEW IF EXISTS tendencias_medias_semanais;
CREATE VIEW tendencias_medias_semanais AS
SELECT
    t.lote_composto,
    t.teste,
    m.idade_lote / 7 AS semana_do_lote,
    COUNT(*) as num_registros,
    ROUND(AVG(m.NH3), 1) as media_nh3,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura,
    ROUND(AVG(m.Humedad), 1) as media_humedad
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY t.lote_composto, semana_do_lote
ORDER BY t.lote_composto, semana_do_lote;


DROP VIEW IF EXISTS analise_ganho_peso_ambiencia;
CREATE VIEW analise_ganho_peso_ambiencia AS
SELECT
    t.lote_composto,
    t.teste,
    t.fator_ganho_28d,
    t.fator_ganho_42d,
    ROUND(AVG(m.NH3), 1) as media_nh3_lote,
    ROUND(AVG(m.Humedad), 1) as media_humedad_lote,
    ROUND(AVG(m.Temperatura), 1) as media_temperatura_lote
FROM medicoes m
JOIN tratamentos t ON m.lote_composto = t.lote_composto
GROUP BY t.lote_composto;