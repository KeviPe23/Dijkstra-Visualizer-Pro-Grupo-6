@echo off
cd /d "%~dp0"
title Dijkstra Visualizer Pro - Pruebas
set "PYTHON_CMD=python"
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"
%PYTHON_CMD% -m unittest discover -s pruebas -p "test_*.py" -v
if errorlevel 1 (
 echo.
 echo Hay pruebas que no han pasado. Consulta los mensajes superiores.
) else (
 echo.
 echo PRUEBAS TERMINADAS. Para la GUI, utiliza ABRIR_SIMULADOR.bat.
)
pause
