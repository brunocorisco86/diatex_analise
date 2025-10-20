#!/bin/bash

# =========================================================
# Script de carga SQL simplificado e direto
# ATENÇÃO: Execute este .sh somente da pasta 'database'
# Requer que o executável 'sqlite3' esteja no PATH do sistema.
# =========================================================

# O primeiro argumento e o caminho completo para o banco de dados de origem
SOURCE_DB_PATH="$1"

# Extrai apenas o nome do arquivo do caminho completo
SOURCE_DB_FILE=$(basename "$SOURCE_DB_PATH")

TARGET_DB_FILE="TESTE_DIATEX_PROD.db"

echo ""
echo "Executando scripts SQL na base: ${TARGET_DB_FILE}"
echo ""

# Passo 1: Criar uma copia do arquivo original antes de rodar os scripts SQL
if [ ! -f "${SOURCE_DB_PATH}" ]; then
    echo "ERRO: Banco de dados original ${SOURCE_DB_PATH} nao encontrado."
    read -p "Pressione Enter para continuar..."
    exit 1
fi
echo "Copiando ${SOURCE_DB_FILE} para ${TARGET_DB_FILE}..."
cp "${SOURCE_DB_PATH}" "${TARGET_DB_FILE}"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao criar a copia do banco de dados."
    read -p "Pressione Enter para continuar..."
    exit 1
fi

echo ""
echo "-- Executando 1_pop_tratamentos.sql na copia --"
sqlite3 "${TARGET_DB_FILE}" < "1_pop_tratamentos.sql"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao executar 1_pop_tratamentos.sql"
    read -p "Pressione Enter para continuar..."
    exit 1
fi

echo ""
echo "-- Executando 2_pop_medicoes_meta.sql na copia --"
sqlite3 "${TARGET_DB_FILE}" < "2_pop_medicoes_meta.sql"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao executar 2_pop_medicoes_meta.sql"
    read -p "Pressione Enter para continuar..."
    exit 1
fi

echo ""
echo "-- Executando 3_create_views.sql na copia --"
sqlite3 "${TARGET_DB_FILE}" < "3_create_views.sql"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao executar 3_create_views.sql"
    read -p "Pressione Enter para continuar..."
    exit 1
fi

echo ""
echo "========================================================="
echo "== Verificando as 10 primeiras linhas da tabela medicoes =="
echo "========================================================="

sqlite3 "${TARGET_DB_FILE}" ".headers on" ".mode column" "SELECT * FROM medicoes LIMIT 10;"

echo ""
echo "Carga SQL finalizada com sucesso! O banco de dados final e ${TARGET_DB_FILE}."
read -p "Pressione Enter para continuar..."
