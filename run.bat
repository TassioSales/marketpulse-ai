@echo off
chcp 65001 > nul
title MarketPulse AI - Inteligência Econômica & Dados
color 0A

echo ===================================================================
echo               📊 MARKETPULSE AI - DATA & GENAI ENGINE
echo       Plataforma de Análise Preditiva e Inteligência Econômica
echo                         Autor: Tássio Sales
echo ===================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando dependências Python...
python -c "import pandas, plotly, flask, requests" 2>nul
if %errorlevel% neq 0 (
    echo [!] Instalando bibliotecas necessárias...
    pip install -r requirements.txt
) else (
    echo [✓] Todas as dependências já estão instaladas.
)

echo.
echo [2/3] Abrindo interface no navegador padrão...
start http://localhost:8080

echo.
echo [3/3] Iniciando servidor MarketPulse AI em http://localhost:8080...
echo Pressione Ctrl+C para encerrar o servidor a qualquer momento.
echo.
python app.py

pause
