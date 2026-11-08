@echo off
setlocal
cd /d "%~dp0"
title Dijkstra Visualizer Pro - Iniciar
if not exist main.py (
 echo ERROR: Falta main.py. Extrae todo el contenido del ZIP antes de abrirlo.
 pause
 exit /b 1
)
set "PYTHON_CMD="
py -3 -c "import tkinter; import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
 python -c "import tkinter; import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
 if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
 echo.
 echo No encuentro Python 3.9 o posterior con Tkinter.
 echo Instala Python desde https://www.python.org/downloads/
 echo Durante la instalacion, activa 'Add Python to PATH'.
 echo.
 pause
 exit /b 1
)
rem Pillow permite suavizado real de bordes y exportacion de PNG 4K.
rem Se instala automaticamente una vez. Si no hay Internet, la GUI sigue abriendo
rem con los graficos vectoriales basicos de Tkinter, sin bloquear al usuario.
%PYTHON_CMD% -c "from PIL import Image, ImageDraw, ImageTk" >nul 2>&1
if errorlevel 1 (
 echo.
 echo Preparando graficos HD por primera vez...
 %PYTHON_CMD% -m pip install "Pillow>=10.2"
 if errorlevel 1 (
  echo.
  echo AVISO: No se pudo instalar Pillow. Abriendo modo compatible sin HD.
  echo Para activar HD mas adelante, conecta Internet y ejecuta este archivo de nuevo.
 )
)
%PYTHON_CMD% main.py
if errorlevel 1 (
 echo.
 echo El simulador no pudo iniciarse. Copia el error que aparece arriba.
 pause
 exit /b 1
)
exit /b 0
