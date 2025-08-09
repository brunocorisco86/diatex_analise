DROP TABLE IF EXISTS tratamentos;

CREATE TABLE tratamentos (
    aviario VARCHAR(512) NOT NULL,
    lote_composto VARCHAR(512) UNIQUE NOT NULL,
	bateria_teste INT, -- ordinal do teste
    data_alojamento TEXT NOT NULL,  -- Usando TEXT para formato YYYY-MM-DD, consistente com Fecha
	data_retirada TEXT, --INSERIR A DATA DE RETIRADA AO FINAL DO LOTE
    linhagem VARCHAR(512),
    teste VARCHAR(512),
    produtor VARCHAR(512),
	n_cama INT,
	aves_alojadas INT,
	vazio INT,
	peso_alojamento INT, --peso em gramas
	peso_7d INT, --peso em gramas
	peso_14d INT, -- peso em gramas
	peso_21d INT, --peso em gramas
	peso_28d INT, -- peso em gramas
    peso_35d INT, -- peso em gramas
    peso_42d INT, -- peso em gramas
	peso_abate INT, -- peso em gramas
	idade_matriz INT, --idade em numero inteiro
	matriz_alojada VARCHAR(512), --identificacao matriz
	origem VARCHAR(512),
	tipo_aviario VARCHAR(512),
	pc_cond_pes FLOAT, --percentual de condenacao por pes
	pc_cond_aero FLOAT, -- percentual de condena em aerossaculite
	id_sensor VARCHAR(512) --nome do sensor
);

-- Adicionar abaixo os dados do lote

-- DARLAN SIMON
-- lote 1203-24
INSERT INTO tratamentos (aviario,lote_composto,bateria_teste,data_alojamento,data_retirada,linhagem,teste,produtor,n_cama,aves_alojadas,vazio,peso_alojamento,peso_7d,peso_14d,peso_21d,peso_28d,peso_35d,peso_42d,peso_abate,idade_matriz,matriz_alojada,origem,tipo_aviario,pc_cond_pes,pc_cond_aero,id_sensor) 
VALUES ('aviario_1203','1203-24',1,'2025-05-12','2025-06-28','ROSS','DIATEX','DARLAN SIMON',6,33900, 14,47,185,480,970,1480,2300,3000,3307,45,'0100066776-16224','PLUSVAL-IPORA','ISOTERMICO','',14.49,'24M0004');

-- lote 1204-24
INSERT INTO tratamentos (aviario,lote_composto,bateria_teste,data_alojamento,data_retirada,linhagem,teste,produtor,n_cama,aves_alojadas,vazio,peso_alojamento,peso_7d,peso_14d,peso_21d,peso_28d,peso_35d,peso_42d,peso_abate,idade_matriz,matriz_alojada,origem,tipo_aviario,pc_cond_pes,pc_cond_aero,id_sensor)
VALUES ('aviario_1204','1204-24',1,'2025-05-12','2025-06-28','ROSS','TESTEMUNHA','DARLAN SIMON',6,33900, 14,46,190,470,960,1460,2250,2950,3260,50,'0100066776-16224','PLUSVAL-IPORA','ISOTERMICO','',4.73,'24M0003');

-- lote 1203-25 (lote 2)
INSERT INTO tratamentos (aviario,lote_composto,bateria_teste,data_alojamento,data_retirada,linhagem,teste,produtor,n_cama,aves_alojadas,vazio,peso_alojamento,peso_7d,peso_14d,peso_21d,peso_28d,peso_35d,peso_42d,peso_abate,idade_matriz,matriz_alojada,origem,tipo_aviario,pc_cond_pes,pc_cond_aero,id_sensor) 
VALUES ('aviario_1203','1203-25',2,'2025-07-17','2025-08-08','ROSS','DIATEX','DARLAN SIMON',7,'','','','','','','','','','','','','','','','','24M0004');

-- lote 1204-25 (lote 2)
INSERT INTO tratamentos (aviario,lote_composto,bateria_teste,data_alojamento,data_retirada,linhagem,teste,produtor,n_cama,aves_alojadas,vazio,peso_alojamento,peso_7d,peso_14d,peso_21d,peso_28d,peso_35d,peso_42d,peso_abate,idade_matriz,matriz_alojada,origem,tipo_aviario,pc_cond_pes,pc_cond_aero,id_sensor)
VALUES ('aviario_1204','1204-25',2,'2025-07-17','2025-08-08','ROSS','TESTEMUNHA','DARLAN SIMON',7,'','','','','','','','','','','','','','','','','24M0003');

-- lote 1263-19
INSERT INTO tratamentos (aviario,lote_composto,bateria_teste,data_alojamento,data_retirada,linhagem,teste,produtor,n_cama,aves_alojadas,vazio,peso_alojamento,peso_7d,peso_14d,peso_21d,peso_28d,peso_35d,peso_42d,peso_abate,idade_matriz,matriz_alojada,origem,tipo_aviario,pc_cond_pes,pc_cond_aero,id_sensor)
VALUES ('aviario_1263','1263-19',1,'2025-07-09','2025-08-08','MISTO','TESTEMUNHA','FAMILIA BELTRAMIN',7, 32600, '','','','','','','','','','','','','','','','24M0002');

-- lote 1262-19
INSERT INTO tratamentos (aviario,lote_composto,bateria_teste,data_alojamento,data_retirada,linhagem,teste,produtor,n_cama,aves_alojadas,vazio,peso_alojamento,peso_7d,peso_14d,peso_21d,peso_28d,peso_35d,peso_42d,peso_abate,idade_matriz,matriz_alojada,origem,tipo_aviario,pc_cond_pes,pc_cond_aero,id_sensor)
VALUES ('aviario_1262','1262-19',1,'2025-07-09','2025-08-08','COBB MALE','DIATEX','FAMILIA BELTRAMIN',7,32600,'','','','','','','','','','','','','','','','24M0009');

-- Adicionar o fator de ganho dos lotes
-- Criar colunas
ALTER TABLE tratamentos ADD COLUMN fator_ganho_7d REAL;
ALTER TABLE tratamentos ADD COLUMN fator_ganho_14d REAL;
ALTER TABLE tratamentos ADD COLUMN fator_ganho_21d REAL;
ALTER TABLE tratamentos ADD COLUMN fator_ganho_28d REAL;
ALTER TABLE tratamentos ADD COLUMN fator_ganho_35d REAL;
ALTER TABLE tratamentos ADD COLUMN fator_ganho_42d REAL;


-- Calcular os valores do fator de ganho
UPDATE tratamentos
SET fator_ganho_7d = CASE
                        WHEN peso_alojamento != 0 AND peso_7d IS NOT NULL AND peso_7d != ''
                        THEN ROUND(CAST(peso_7d AS REAL) / peso_alojamento, 3)
                        ELSE NULL
                     END,
    fator_ganho_14d = CASE
                         WHEN peso_alojamento != 0 AND peso_14d IS NOT NULL AND peso_14d != ''
                         THEN ROUND(CAST(peso_14d AS REAL) / peso_alojamento, 3)
                         ELSE NULL
                      END,
    fator_ganho_21d = CASE
                         WHEN peso_alojamento != 0 AND peso_21d IS NOT NULL AND peso_21d != ''
                         THEN ROUND(CAST(peso_21d AS REAL) / peso_alojamento, 3)
                         ELSE NULL
                      END,
	fator_ganho_28d = CASE
                         WHEN peso_alojamento != 0 AND peso_28d IS NOT NULL AND peso_28d != ''
                         THEN ROUND(CAST(peso_28d AS REAL) / peso_alojamento, 3)
                         ELSE NULL
                      END,
    fator_ganho_35d = CASE
                         WHEN peso_alojamento != 0 AND peso_35d IS NOT NULL AND peso_35d != ''
                         THEN ROUND(CAST(peso_35d AS REAL) / peso_alojamento, 3)
                         ELSE NULL
                      END,
    fator_ganho_42d = CASE
                         WHEN peso_alojamento != 0 AND peso_42d IS NOT NULL AND peso_42d != ''
                         THEN ROUND(CAST(peso_42d AS REAL) / peso_alojamento, 3)
                         ELSE NULL
                      END;
					  
					  
/*
-- CRIAR UM ALTER TABLE PARA INCLUIR A COLUNA DE LOTE COMPOSTO NA TABELA MEDICOES

ALTER TABLE medicoes ADD COLUMN lote_composto VARCHAR(512);

UPDATE medicoes
SET lote_composto = (
    SELECT t.lote_composto
    FROM tratamentos t
    WHERE t.aviario = medicoes.Nome_Arquivo
    AND medicoes.Fecha >= t.data_alojamento
    AND (medicoes.Fecha <= t.data_retirada OR t.data_retirada IS NULL OR t.data_retirada = '')
);

*/

-- TRECHO AJUSTADO

ALTER TABLE medicoes ADD COLUMN lote_composto VARCHAR(512);

ALTER TABLE medicoes ADD COLUMN teste VARCHAR(512);

UPDATE medicoes
SET
    lote_composto = (
        SELECT t.lote_composto
        FROM tratamentos t
        WHERE
            t.aviario = medicoes.Nome_Arquivo
            AND medicoes.Fecha BETWEEN t.data_alojamento AND COALESCE(t.data_retirada, '9999-12-31')
    ),
    teste = (
        SELECT t.teste
        FROM tratamentos t
        WHERE
            t.aviario = medicoes.Nome_Arquivo
            AND medicoes.Fecha BETWEEN t.data_alojamento AND COALESCE(t.data_retirada, '9999-12-31')
    );

/*
-- 	INSERIR UMA COLUNA PARA O TRATAMENTO NA TABELA MEDIÇÕES

ALTER TABLE medicoes ADD COLUMN teste VARCHAR(512);

UPDATE medicoes
SET teste = (
    SELECT t.teste
    FROM tratamentos t
    WHERE t.lote_composto = medicoes.lote_composto
);
*/
