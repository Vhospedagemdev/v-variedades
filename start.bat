@echo off
title V Variedades - Servidor de Afiliados
:: Garante que o terminal execute sempre dentro da pasta do projeto
cd /d "%~dp0"

echo ========================================================
echo       Iniciando Landing Page V Variedades
echo ========================================================
echo Pasta atual: %CD%
echo.
echo Vitrine Publica:       http://127.0.0.1:8000
echo Painel Administrativo:  http://127.0.0.1:8000/admin
echo Usuario padrao:         admin
echo Senha padrao:           admin123
echo.
echo Pressione CTRL+C para encerrar o servidor.
echo ========================================================
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
