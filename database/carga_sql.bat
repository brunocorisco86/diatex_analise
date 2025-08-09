@echo off
setlocal

:: =========================================================
:: Script de carga SQL simplificado e direto
:: ATENÇÃO: Execute este .bat somente da pasta 'database'
:: Requer que o executável 'sqlite3' esteja no PATH do sistema.
:: =========================================================

set SOURCE_DB="TESTE_DIATEX.db"
set TARGET_DB="TESTE_DIATEX_PROD.db"

echo.
echo Executando scripts SQL na base: %TARGET_DB%
echo.

:: Passo 1: Criar uma copia do arquivo original antes de rodar os scripts SQL
if not exist %SOURCE_DB% (
    echo ERRO: Banco de dados original %SOURCE_DB% nao encontrado.
    pause
    exit /b
)
echo Copiando %SOURCE_DB% para %TARGET_DB%...
copy %SOURCE_DB% %TARGET_DB% > nul
if %errorlevel% neq 0 (
    echo ERRO: Falha ao criar a copia do banco de dados.
    pause
    exit /b
)

echo.
echo -- Executando 1_pop_tratamentos.sql na copia --
sqlite3 %TARGET_DB% < "1_pop_tratamentos.sql"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao executar 1_pop_tratamentos.sql
    pause
    exit /b
)

echo.
echo -- Executando 2_pop_medicoes_meta.sql na copia --
sqlite3 %TARGET_DB% < "2_pop_medicoes_meta.sql"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao executar 2_pop_medicoes_meta.sql
    pause
    exit /b
)

echo.
echo -- Executando 3_create_views.sql na copia --
sqlite3 %TARGET_DB% < "3_create_views.sql"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao executar 3_create_views.sql
    pause
    exit /b
)

echo.
echo =========================================================
echo == Verificando as 10 primeiras linhas da tabela medicoes ==
echo =========================================================

sqlite3 %TARGET_DB% ".headers on" ".mode column" "SELECT * FROM medicoes LIMIT 10;"

echo.
echo Carga SQL finalizada com sucesso! O banco de dados final e %TARGET_DB%.
pause

endlocal