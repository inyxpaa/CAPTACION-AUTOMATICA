@echo off
chcp 65001 > nul
title ORESNA CAPTADOR — Panel de Control B2B

echo.
echo  ================================================
echo    ORESNA CAPTADOR — Plataforma de Captacion B2B
echo  ================================================
echo.

:: Ir a la carpeta del proyecto
cd /d "%~dp0"

:: Verificar si existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo  [INFO] Creando entorno virtual Python...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] No se pudo crear el entorno virtual.
        echo          Asegurate de tener Python 3.11+ instalado.
        pause
        exit /b 1
    )
    echo  [OK] Entorno virtual creado.
)

:: Activar entorno virtual
call venv\Scripts\activate.bat

:: Verificar si las dependencias estan instaladas
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo  [INFO] Instalando dependencias ^(primera vez, puede tardar unos minutos^)...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo  [ERROR] Fallo al instalar dependencias.
        pause
        exit /b 1
    )
    
    echo  [INFO] Instalando Playwright y navegadores...
    playwright install chromium --quiet
    echo  [OK] Dependencias instaladas correctamente.
)

:: Verificar que existe el .env
if not exist ".env" (
    echo  [INFO] Copiando archivo de configuracion de ejemplo...
    copy ".env.example" ".env" > nul
    echo.
    echo  [IMPORTANTE] Se ha creado el archivo .env
    echo  Por favor, edita el archivo .env con tus claves API antes de continuar.
    echo  Claves necesarias:
    echo    - GROQ_API_KEY o OPENAI_API_KEY ^(para la IA^)
    echo    - RESEND_API_KEY ^(opcional, para enviar emails^)
    echo.
    start notepad ".env"
    pause
)

echo.
echo  [INFO] Iniciando ORESNA CAPTADOR...
echo  [INFO] El panel se abrira en tu navegador en: http://localhost:8501
echo.

:: Arrancar el sistema
python main.py

:: Si falla, mostrar error
if errorlevel 1 (
    echo.
    echo  [ERROR] El sistema se ha detenido con errores.
    echo  Revisa el mensaje de error de arriba.
    pause
)
