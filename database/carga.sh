#!/bin/bash

# =========================================================
# carga.sh
# Script principal de orquestracao
# =========================================================

DB_NAME="TESTE_DIATEX"
DB_FILE="${DB_NAME}.db"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DB_PATH="${SCRIPT_DIR}/${DB_FILE}"
PYTHON_SCRIPT="${PROJECT_ROOT}/src/extract_tables2.py" # Assuming extract_tables2.py is in src/

echo "========================================================="
echo "== Passo 1: Executando script Python de extracao de dados =="
echo "========================================================="
echo "Executando script Python: "${PYTHON_SCRIPT}""
python3 "${PYTHON_SCRIPT}"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERRO: Falha na execucao do script Python."
    read -p "Pressione Enter para continuar..."
    exit 1
fi

# Retorna ao diretorio do script .sh para chamar carga_sql.sh
cd "${SCRIPT_DIR}" || exit 1

# Verifica se o arquivo .db existe apos a execucao do Python
if [ ! -f "${DB_PATH}" ]; then
    echo ""
    echo "ERRO: O arquivo ${DB_PATH} nao foi criado. Verifique os logs do script Python."
    read -p "Pressione Enter para continuar..."
    exit 1
fi

# Chama o script de carga SQL, passando o caminho do DB
chmod +x "${SCRIPT_DIR}/carga_sql.sh" # Ensure carga_sql.sh is executable
"${SCRIPT_DIR}/carga_sql.sh" "${DB_PATH}"
if [ $? -ne 0 ]; then
    echo ""
    echo "ERRO: Falha na execucao de carga_sql.sh."
    read -p "Pressione Enter para continuar..."
    exit 1
fi

echo ""
echo "========================================================="
echo "== Sucesso: Todos os scripts foram executados com sucesso! =="
echo "========================================================="
read -p "Pressione Enter para continuar..."
