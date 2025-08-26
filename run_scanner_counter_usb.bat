@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title HP LaserJet Pro 400 Scanner Counter Control (USB)

echo.
echo ======================================================
echo   HP LaserJet Pro 400 Scanner Counter Control (USB)
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
if not exist "hp_scanner_counter_usb.py" (
    echo ❌ Файл hp_scanner_counter_usb.py не найден!
    echo    Убедитесь, что вы запускаете скрипт из правильной папки
    pause
    exit /b 1
)

:: Проверяем права администратора
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️  ВНИМАНИЕ: Запущено НЕ от имени администратора
    echo    Для лучшей работы с USB рекомендуется запуск от администратора
    echo.
    set /p continue="Продолжить? (y/n): "
    if /i not "!continue!"=="y" exit /b 1
    echo.
)

:main_menu
cls
echo.
echo ======================================================
echo   HP LaserJet Pro 400 Scanner Counter Control (USB)
echo ======================================================
echo.
echo 1. Показать список USB принтеров
echo 2. Получить текущее значение счетчика
echo 3. Установить значение счетчика
echo 4. Сбросить счетчик в 0
echo 5. Получить информацию о принтере
echo 6. Диагностика USB подключения
echo 7. Установить pyusb (улучшает работу)
echo 8. Выход
echo.

set /p choice="Выберите действие (1-8): "

if "%choice%"=="1" goto list_printers
if "%choice%"=="2" goto get_counter
if "%choice%"=="3" goto set_counter  
if "%choice%"=="4" goto reset_counter
if "%choice%"=="5" goto printer_info
if "%choice%"=="6" goto diagnostics
if "%choice%"=="7" goto install_pyusb
if "%choice%"=="8" goto exit
goto main_menu

:list_printers
echo.
echo 🔍 Поиск USB принтеров...
echo.
python hp_scanner_counter_usb.py --list
echo.
pause
goto main_menu

:get_counter
echo.
echo 📊 Получение текущего значения счетчика...
echo.
python hp_scanner_counter_usb.py --get
echo.
pause
goto main_menu

:set_counter
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
python hp_scanner_counter_usb.py --set %counter_value%
echo.
pause
goto main_menu

:reset_counter
echo.
echo ⚠️  ВНИМАНИЕ: Счетчик будет сброшен в 0!
set /p confirm="Продолжить? (y/n): "
if /i not "%confirm%"=="y" goto main_menu

echo.
echo 🔄 Сброс счетчика...
echo.
python hp_scanner_counter_usb.py --reset
echo.
pause
goto main_menu

:printer_info
echo.
echo 📋 Получение информации о принтере...
echo.
python hp_scanner_counter_usb.py --info
echo.
pause
goto main_menu

:diagnostics
echo.
echo 🧪 Запуск диагностики USB подключения...
echo.
python test_connection_usb.py
echo.
pause
goto main_menu

:install_pyusb
echo.
echo 📦 Установка pyusb...
echo    Это может занять несколько минут...
echo.
pip install pyusb
if errorlevel 1 (
    echo.
    echo ❌ Ошибка установки pyusb!
    echo 💡 Попробуйте:
    echo    1. Обновить pip: python -m pip install --upgrade pip
    echo    2. Установить вручную: pip install --user pyusb
    echo    3. Установить через conda: conda install pyusb
) else (
    echo.
    echo ✅ pyusb успешно установлен!
    echo 💡 Теперь доступны расширенные функции USB
)
echo.
pause
goto main_menu

:exit
echo.
echo 👋 До свидания!
exit /b 0
