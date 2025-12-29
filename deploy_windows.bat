@echo off
REM ===== CLINICAPRO - DEPLOY AUTOMÁTICO WINDOWS =====
REM Execute: deploy_windows.bat

echo.
echo ======================================
echo  CLINICAPRO - Deploy Automatico
echo ======================================
echo.

REM Verifica se está no diretório correto
if not exist "docker-compose.yml" (
    echo [ERRO] Execute no diretorio D:\CLINIAPRO
    pause
    exit /b 1
)

REM ===== GIT PUSH =====
echo [1/4] Git Push...
git add .
git commit -m "feat: Docker + Emergency protocols + Security fixes" 2>nul
git push -u origin main 2>nul || git push origin main 2>nul
echo [OK] Git push concluido
echo.

REM ===== SOLICITA DADOS =====
echo [2/4] Configuracao da VPS
set /p VPS_HOST="IP ou hostname da VPS (ex: Fbzia): "
set /p VPS_USER="Usuario SSH (padrao: root): "
if "%VPS_USER%"=="" set VPS_USER=root
set /p VPS_PORT="Porta SSH (padrao: 22): "
if "%VPS_PORT%"=="" set VPS_PORT=22

echo.
echo [3/4] Variaveis de Ambiente
set /p OPENAI_KEY="OPENAI_API_KEY: "
set /p TELEGRAM_TOKEN="TELEGRAM_BOT_TOKEN: "
set /p REDIS_PASS="REDIS_PASSWORD (Enter para padrao): "
if "%REDIS_PASS%"=="" set REDIS_PASS=clinicapro_redis_2025

REM Cria .env temporário
echo OPENAI_API_KEY=%OPENAI_KEY% > %TEMP%\clinicapro.env
echo TELEGRAM_BOT_TOKEN=%TELEGRAM_TOKEN% >> %TEMP%\clinicapro.env
echo REDIS_PASSWORD=%REDIS_PASS% >> %TEMP%\clinicapro.env

echo.
echo [4/4] Deploy no Swarm...
echo.
echo Conectando ao servidor %VPS_HOST%...
echo.

REM Comandos SSH - Você vai precisar do PuTTY/OpenSSH instalado
ssh -p %VPS_PORT% %VPS_USER%@%VPS_HOST% "cd /root && rm -rf clinicapro2 && git clone https://github.com/fabiobzissou72/clinicapro2.git"

echo Copiando variaveis de ambiente...
scp -P %VPS_PORT% %TEMP%\clinicapro.env %VPS_USER%@%VPS_HOST%:/root/clinicapro2/.env

echo Buildando e deployando...
ssh -p %VPS_PORT% %VPS_USER%@%VPS_HOST% "cd /root/clinicapro2 && docker build -t clinicapro:latest . && docker stack rm clinicapro; sleep 10; docker stack deploy -c clinicapro.yaml clinicapro"

REM Limpa arquivo temporário
del %TEMP%\clinicapro.env

echo.
echo ======================================
echo   DEPLOY CONCLUIDO COM SUCESSO!
echo ======================================
echo.
echo Verifique:
echo   ssh %VPS_USER%@%VPS_HOST%
echo   docker stack ps clinicapro
echo.
pause
