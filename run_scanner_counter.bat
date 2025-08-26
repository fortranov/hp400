@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title HP LaserJet Pro 400 Scanner Counter Control

echo.
echo ======================================================
echo   HP LaserJet Pro 400 Scanner Counter Control
echo ======================================================
echo.

:: Проверяем, установлен ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден в системе!
    echo    Установите Python 3.6 или выше и добавьте его в PATH
    pause
    exit /b 1
)

:: Проверяем наличие основного скрипта
if not exist "hp_scanner_counter.py" (
    echo ❌ Файл hp_scanner_counter.py не найден!
    echo    Убедитесь, что вы запускаете скрипт из правильной папки
    pause
    exit /b 1
)

:main_menu
cls
echo.
echo ======================================================
echo   HP LaserJet Pro 400 Scanner Counter Control
echo ======================================================
echo.
echo 1. Получить текущее значение счетчика
echo 2. Установить значение счетчика
echo 3. Сбросить счетчик в 0
echo 4. Получить информацию о принтере
echo 5. Запустить демонстрацию
echo 6. Выход
echo.

set /p choice="Выберите действие (1-6): "

if "%choice%"=="1" goto get_counter
if "%choice%"=="2" goto set_counter  
if "%choice%"=="3" goto reset_counter
if "%choice%"=="4" goto printer_info
if "%choice%"=="5" goto demo
if "%choice%"=="6" goto exit
goto main_menu

:get_ip
if "%printer_ip%"=="" (
    set /p printer_ip="Введите IP адрес принтера: "
    if "!printer_ip!"=="" (
        echo ❌ IP адрес не может быть пустым!
        pause
        goto main_menu
    )
)
goto :eof

:get_counter
call :get_ip
echo.
echo 📊 Получение текущего значения счетчика...
echo.
python hp_scanner_counter.py %printer_ip% --get
echo.
pause
goto main_menu

:set_counter
call :get_ip
echo.
set /p counter_value="Введите новое значение счетчика: "
if "%counter_value%"=="" (
    echo ❌ Значение не может быть пустым!
    pause
    goto main_menu
)

echo.
echo 🔧 Установка счетчика на %counter_value%...
echo.
python hp_scanner_counter.py %printer_ip% --set %counter_value%
echo.
pause
goto main_menu

:reset_counter
call :get_ip
echo.
echo ⚠️  ВНИМАНИЕ: Счетчик будет сброшен в 0!
set /p confirm="Продолжить? (y/n): "
if /i not "%confirm%"=="y" goto main_menu

echo.
echo 🔄 Сброс счетчика...
echo.
python hp_scanner_counter.py %printer_ip% --reset
echo.
pause
goto main_menu

:printer_info
call :get_ip
echo.
echo 📋 Получение информации о принтере...
echo.
python hp_scanner_counter.py %printer_ip% --info
echo.
pause
goto main_menu

:demo
call :get_ip
echo.
echo 🚀 Запуск демонстрации...
echo.
python example_usage.py %printer_ip%
echo.
pause
goto main_menu

:exit
echo.
echo 👋 До свидания!
exit /b 0
