@echo off
chcp 65001 >nul
setlocal

title Исправление обнаружения HP M425 MFP

echo.
echo ======================================================
echo   Диагностика и исправление обнаружения HP M425 MFP
echo ======================================================
echo.

echo 🔧 Этот скрипт поможет найти HP M425 MFP, подключенный по USB
echo.

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    pause
    exit /b 1
)

echo 📋 Выберите действие:
echo.
echo 1. 🔍 Полная диагностика M425 (рекомендуется)
echo 2. 🖨️  Быстрая проверка всех принтеров
echo 3. 🔌 Проверка USB портов
echo 4. 💻 Попробовать найти M425 улучшенным поиском
echo 5. ⚙️  Ручное указание USB порта
echo 6. 📖 Показать подсказки
echo 0. ❌ Выход
echo.

set /p choice="Ваш выбор (0-6): "

if "%choice%"=="1" goto full_diagnosis
if "%choice%"=="2" goto quick_check
if "%choice%"=="3" goto check_usb_ports
if "%choice%"=="4" goto improved_search
if "%choice%"=="5" goto manual_usb
if "%choice%"=="6" goto show_tips
if "%choice%"=="0" goto exit
goto main_menu

:full_diagnosis
echo.
echo 🔍 Запуск полной диагностики M425...
echo    Это может занять несколько минут
echo.
if exist "diagnose_m425.py" (
    python diagnose_m425.py
) else (
    echo ❌ Файл diagnose_m425.py не найден!
    echo 💡 Убедитесь, что все файлы находятся в одной папке
)
echo.
pause
goto main_menu

:quick_check
echo.
echo 🖨️  Быстрая проверка принтеров в системе...
echo.
echo === WMIC ПРИНТЕРЫ ===
wmic printer get Name,PortName,DriverName
echo.
echo === ПОИСК M425 ===
wmic printer where "Name like '%M425%' or Name like '%MFP%' or Name like '%400%'" get Name,PortName
echo.
echo === USB ПРИНТЕРЫ ===
wmic printer where "PortName like 'USB%'" get Name,PortName
echo.
pause
goto main_menu

:check_usb_ports
echo.
echo 🔌 Проверка USB портов...
echo.
for %%P in (USB001 USB002 USB003 USB004) do (
    echo Проверка порта %%P:
    wmic printer where "PortName='%%P'" get Name 2>nul
    echo.
)
echo.
pause
goto main_menu

:improved_search
echo.
echo 💻 Попробуем найти M425 улучшенным поиском...
echo.
if exist "hp_m425_scanner_counter.py" (
    echo 📋 Запуск поиска M425...
    python hp_m425_scanner_counter.py --list
    echo.
    echo 🎯 Попробуем интерактивный выбор...
    python hp_m425_scanner_counter.py --select
) else (
    echo ❌ Файл hp_m425_scanner_counter.py не найден!
)
echo.
pause
goto main_menu

:manual_usb
echo.
echo 🔌 Ручное указание USB порта для M425...
echo.
echo 💡 Обычно M425 MFP подключается к USB001
echo.
set /p usb_port="Введите USB порт (например, USB001): "
if "%usb_port%"=="" set usb_port=USB001

echo.
echo 🔧 Тестирование порта %usb_port%...
echo.

if exist "hp_m425_scanner_counter.py" (
    python hp_m425_scanner_counter.py --usb-port %usb_port% --info
) else (
    echo ❌ Файл hp_m425_scanner_counter.py не найден!
)
echo.
pause
goto main_menu

:show_tips
echo.
echo 📖 ПОДСКАЗКИ ПО ОБНАРУЖЕНИЮ M425 MFP
echo =======================================
echo.
echo 🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:
echo   1. M425 не установлен в системе как принтер
echo   2. M425 определился под другим именем
echo   3. USB кабель не подключен или неисправен
echo   4. M425 выключен или в режиме ожидания
echo   5. Нет драйверов M425 в системе
echo.
echo 🛠️  РЕШЕНИЯ:
echo   1. Установите официальный драйвер M425 с сайта HP
echo   2. Проверьте "Устройства и принтеры" в Windows
echo   3. Попробуйте другой USB кабель/порт
echo   4. Включите M425 и дождитесь готовности
echo   5. Переустановите M425 как принтер
echo.
echo 🔧 ДИАГНОСТИЧЕСКИЕ КОМАНДЫ:
echo   • wmic printer get Name,PortName
echo   • wmic printer where "PortName like 'USB%%'" get Name
echo   • devmgmt.msc (Диспетчер устройств)
echo.
echo 💡 АЛЬТЕРНАТИВЫ:
echo   • Используйте ручное указание порта: --usb-port USB001
echo   • Попробуйте сетевое подключение вместо USB
echo   • Проверьте M425 в веб-интерфейсе принтера
echo.
pause
goto main_menu

:main_menu
cls
goto choice

:exit
echo.
echo 📋 ИТОГИ ДИАГНОСТИКИ:
echo.
if exist "m425_counter_config.json" (
    echo ✅ Найдена конфигурация M425: m425_counter_config.json
) else (
    echo ❌ Конфигурация M425 не создана
)
echo.
echo 💡 ДАЛЬНЕЙШИЕ ДЕЙСТВИЯ:
echo   1. Если M425 найден - используйте hp_m425_scanner_counter.py
echo   2. Если не найден - установите драйвер M425 и повторите
echo   3. В крайнем случае используйте --usb-port USB001
echo.
echo 👋 Удачи с настройкой M425 MFP!
pause
