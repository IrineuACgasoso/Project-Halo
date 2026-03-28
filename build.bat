@echo off
echo ======================================================
echo           PROJECT HALO - REPARO TOTAL 3.13
echo ======================================================
echo.

:: Limpeza profunda
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [1/2] Criando executavel...

:: Adicionamos --clean para limpar o cache do PyInstaller
:: Adicionamos --collect-all pygame para garantir que o som/imagem funcionem
pyinstaller --noconsole --onedir --clean ^
 --add-data "assets;assets" ^
 --add-data "source;source" ^
 --collect-all pygame ^
 --paths "source" ^
 --exclude-module tkinter ^
 --icon="ha.ico" ^
 main.py

echo.
echo [2/2] Limpando rastros...
if exist main.spec del /q main.spec

echo.
echo ======================================================
echo   TESTE AGORA: dist/main/main.exe
echo ======================================================
pause