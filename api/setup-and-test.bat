@echo off
REM Script completo: Poblar BD + Analisis de Seguridad

echo ========================================
echo SETUP Y ANALISIS DE SEGURIDAD
echo ========================================
echo.

REM ========================================
REM PASO 1: Poblar base de datos
REM ========================================

echo [Paso 1/3] Poblando base de datos...
echo.

node populate-db.js

if errorlevel 1 (
    echo ERROR: No se pudo poblar la base de datos
    pause
    exit /b 1
)

echo.
echo OK: Base de datos poblada correctamente
echo.
pause

REM ========================================
REM PASO 2: Verificar servidor
REM ========================================

echo [Paso 2/3] Verificando que el servidor este corriendo...
echo.

curl -s http://localhost:3000/health >nul 2>&1
if errorlevel 1 (
    echo ERROR: El servidor no esta corriendo
    echo.
    echo Por favor ejecuta en otra terminal:
    echo   npm start
    echo.
    pause
    exit /b 1
)

echo OK: Servidor activo en http://localhost:3000
echo.

REM ========================================
REM PASO 3: Ejecutar analisis
REM ========================================

echo [Paso 3/3] Ejecutando analisis de seguridad...
echo.
pause

REM SAST
echo ========================================
echo PARTE 1: SAST - Analisis Estatico
echo ========================================
echo.

python detect-sqli.py

echo.
pause

REM DAST
echo ========================================
echo PARTE 2: DAST - Analisis Dinamico
echo ========================================
echo.

python test-dast.py

REM ========================================
REM RESUMEN FINAL
REM ========================================

echo.
echo ========================================
echo RESUMEN FINAL
echo ========================================
echo.

if exist sast-results.txt (
    echo [SAST] Analisis estatico:
    find /c "Línea" sast-results.txt
    echo.
)

if exist dast-results.txt (
    echo [DAST] Analisis dinamico:
    find /c "VULNERABLE" dast-results.txt
    echo.
)

echo Archivos generados:
dir /B sast-results.* dast-results.* 2>nul

echo.
echo ========================================
echo ANALISIS COMPLETADO EXITOSAMENTE
echo ========================================
echo.

echo.
echo Para ver detalles:
echo   type sast-results.txt
echo   type dast-results.txt
echo.

pause