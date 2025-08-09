@echo off
setlocal

:: =========================================================
:: carga.bat
:: Script principal de orquestracao
:: =========================================================

set dbname=TESTE_DIATEX
set dbfile=%dbname%.db

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set DB_PATH="%SCRIPT_DIR%%dbfile%"
set PYTHON_SCRIPT="%PROJECT_ROOT%extract_tables2.py"

echo =========================================================
echo == Passo 1: Executando script Python de extracao de dados ==
echo =========================================================
echo Diretorio de execucao: "%PROJECT_ROOT%"
cd "%PROJECT_ROOT%"
python extract_tables2.py

if %errorlevel% neq 0 (
    echo.
    echo ERRO: Falha na execucao do script Python.
    pause
    exit /b
)

:: Retorna ao diretorio do script .bat para chamar carga_sql.bat
cd "%SCRIPT_DIR%"

:: Verifica se o arquivo .db existe apos a execucao do Python
if not exist %DB_PATH% (
    echo.
    echo ERRO: O arquivo %DB_PATH% nao foi criado. Verifique os logs do script Python.
    pause
    exit /b
)

:: Chama o script de carga SQL, passando o caminho do DB
call carga_sql.bat %DB_PATH%
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Falha na execucao de carga_sql.bat.
    pause
    exit /b
)

echo.
echo =========================================================
echo == Sucesso: Todos os scripts foram executados com sucesso! ==
echo =========================================================
pause

endlocal