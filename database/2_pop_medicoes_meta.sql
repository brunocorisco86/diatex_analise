-- -----------------------------------------------------------
-- 2_pop_medicoes_meta.sql
-- Adiciona e popula colunas meta na tabela medicoes
-- -----------------------------------------------------------

-- As colunas idade_lote e n_cama sao adicionadas aqui
ALTER TABLE medicoes ADD COLUMN idade_lote INTEGER;
ALTER TABLE medicoes ADD COLUMN n_cama INT;

-- Adiciona a coluna bateria_teste
ALTER TABLE medicoes ADD COLUMN bateria_teste VARCHAR(512);


-- Passo 1: Popula as colunas lote_composto e teste usando ID_Aviario e o período do tratamento.
-- Este UPDATE foi mantido para garantir que os dados estejam corretos, mesmo que as colunas já existam.
UPDATE medicoes
SET
    lote_composto = (
        SELECT t.lote_composto
        FROM tratamentos t
        WHERE
            t.aviario = medicoes.ID_Aviario
            AND medicoes.Fecha BETWEEN t.data_alojamento AND COALESCE(t.data_retirada, '9999-12-31')
    ),
    teste = (
        SELECT t.teste
        FROM tratamentos t
        WHERE
            t.aviario = medicoes.ID_Aviario
            AND medicoes.Fecha BETWEEN t.data_alojamento AND COALESCE(t.data_retirada, '9999-12-31')
    )
WHERE EXISTS (
    SELECT 1
    FROM tratamentos t
    WHERE
        t.aviario = medicoes.ID_Aviario
        AND medicoes.Fecha BETWEEN t.data_alojamento AND COALESCE(t.data_retirada, '9999-12-31')
);


-- Passo 2: Popula as colunas idade_lote, n_cama e bateria_teste usando a coluna lote_composto preenchida.
UPDATE medicoes
SET
    idade_lote = (
        SELECT CASE
                   WHEN t.data_alojamento IS NULL OR t.data_alojamento = ''
                   THEN -1
                   ELSE ROUND(JULIANDAY(medicoes.Fecha) - JULIANDAY(t.data_alojamento))
               END
        FROM tratamentos t
        WHERE t.lote_composto = medicoes.lote_composto
    ),
    n_cama = (
        SELECT t.n_cama
        FROM tratamentos t
        WHERE t.lote_composto = medicoes.lote_composto
    ),
    bateria_teste = (
        SELECT t.bateria_teste
        FROM tratamentos t
        WHERE t.lote_composto = medicoes.lote_composto
    )
WHERE medicoes.lote_composto IS NOT NULL;