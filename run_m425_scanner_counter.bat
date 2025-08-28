@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title HP LaserJet Pro 400 MFP M425 PCL Scanner Counter

echo.
echo ======================================================
echo   HP LaserJet Pro 400 MFP M425 PCL Scanner Counter
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

:: Проверяем наличие M425 скрипта
if not exist "hp_m425_scanner_counter.py" (
    echo ❌ Файл hp_m425_scanner_counter.py не найден!
    echo    Убедитесь, что вы запускаете скрипт из правильной папки
    pause
    exit /b 1
)

echo ℹ️  Специализированная версия для M425 MFP:
echo   • Оптимизировано для многофункционального устройства
echo   • Поддерживает: сканер, копир, принтер, факс
echo   • Специфичные PJL команды для M425
echo   • Расширенная диагностика MFP функций
echo.

:main_menu
cls
echo.
echo ======================================================
echo   HP M425 MFP Scanner Counter Control
echo ======================================================
echo.
echo 1. Найти M425 MFP принтеры
echo 2. Выбрать M425 принтер интерактивно
echo 3. Указать USB порт для M425
echo 4. Получить счетчик сканера M425
echo 5. Установить счетчик сканера M425
echo 6. Сбросить счетчик сканера M425
echo 7. Информация о M425 MFP
echo 8. История команд M425
echo 9. Очистить конфигурацию M425
echo 0. Выход
echo.

set /p choice="Выберите действие (0-9): "

if "%choice%"=="1" goto list_m425
if "%choice%"=="2" goto select_m425
if "%choice%"=="3" goto manual_m425_usb
if "%choice%"=="4" goto get_m425_counter
if "%choice%"=="5" goto set_m425_counter  
if "%choice%"=="6" goto reset_m425_counter
if "%choice%"=="7" goto m425_info
if "%choice%"=="8" goto show_m425_history
if "%choice%"=="9" goto clear_m425_config
if "%choice%"=="0" goto exit
goto main_menu

:list_m425
echo.
echo 🔍 Поиск HP M425 MFP принтеров...
echo.
python hp_m425_scanner_counter.py --list
echo.
pause
goto main_menu

:select_m425
echo.
echo 🎯 Интерактивный выбор M425 MFP принтера...
echo    Будет показан список найденных M425 принтеров
echo.
python hp_m425_scanner_counter.py --select
echo.
pause
goto main_menu

:manual_m425_usb
echo.
echo 🔌 Указание USB порта для M425 MFP...
echo.
set /p usb_port="Введите USB порт для M425 (например, USB001, 1): "
if "%usb_port%"=="" (
    echo ❌ USB порт не может быть пустым!
    pause
    goto main_menu
)

echo.
echo 🔧 Проверка подключения M425 к порту %usb_port%...
echo.
python hp_m425_scanner_counter.py --usb-port %usb_port% --info
if errorlevel 1 (
    echo.
    echo ❌ Ошибка подключения к M425 через USB порт %usb_port%
    echo 💡 Проверьте:
    echo    • Правильность порта (обычно USB001)
    echo    • Подключение M425 MFP к компьютеру
    echo    • Включен ли M425 MFP
) else (
    echo.
    echo ✅ M425 MFP успешно подключен к порту %usb_port%
)
echo.
pause
goto main_menu

:get_m425_counter
echo.
echo 📊 Получение счетчика сканера M425 MFP...
echo.
echo 🔍 Попытка использовать сохраненный M425...
python hp_m425_scanner_counter.py --use-saved --get
if errorlevel 1 (
    echo.
    echo ⚠️  Сохраненный M425 не найден или недоступен
    echo 🎯 Запуск интерактивного выбора M425...
    echo.
    python hp_m425_scanner_counter.py --interactive --get
)
echo.
echo ℹ️  Примечание для M425 MFP:
echo    • Значение может быть получено из статистики WMI/CUPS
echo    • Поддерживаются специфичные команды MFP
echo    • Сохраняется в конфигурации m425_counter_config.json
echo.
pause
goto main_menu

:set_m425_counter
echo.
set /p counter_value="Введите новое значение счетчика сканера M425: "
if "%counter_value%"=="" (
    echo ❌ Значение не может быть пустым!
    pause
    goto main_menu
)

echo.
echo 🔧 Установка счетчика сканера M425 на %counter_value%...
echo.
echo 🔍 Попытка использовать сохраненный M425...
python hp_m425_scanner_counter.py --use-saved --set %counter_value%
if errorlevel 1 (
    echo.
    echo ⚠️  Сохраненный M425 не найден или недоступен
    echo 🎯 Запуск интерактивного выбора M425...
    echo.
    python hp_m425_scanner_counter.py --interactive --set %counter_value%
)
echo.
echo ℹ️  Отправлены специфичные команды M425 MFP:
echo    • @PJL SET SCANCOUNTER
echo    • @PJL SET MFPSCANCOUNT
echo    • @PJL DEFAULT SCANCOUNTER
echo    • Значение сохранено в конфигурации
echo.
pause
goto main_menu

:reset_m425_counter
echo.
echo ⚠️  ВНИМАНИЕ: Счетчик сканера M425 MFP будет сброшен в 0!
set /p confirm="Продолжить? (y/n): "
if /i not "%confirm%"=="y" goto main_menu

echo.
echo 🔄 Сброс счетчика сканера M425 MFP...
echo.
echo 🔍 Попытка использовать сохраненный M425...
python hp_m425_scanner_counter.py --use-saved --reset
if errorlevel 1 (
    echo.
    echo ⚠️  Сохраненный M425 не найден или недоступен
    echo 🎯 Запуск интерактивного выбора M425...
    echo.
    python hp_m425_scanner_counter.py --interactive --reset
)
echo.
pause
goto main_menu

:m425_info
echo.
echo 📋 Получение информации о M425 MFP...
echo.
echo 🔍 Попытка использовать сохраненный M425...
python hp_m425_scanner_counter.py --use-saved --info
if errorlevel 1 (
    echo.
    echo ⚠️  Сохраненный M425 не найден или недоступен
    echo 🎯 Запуск интерактивного выбора M425...
    echo.
    python hp_m425_scanner_counter.py --interactive --info
)
echo.
pause
goto main_menu

:show_m425_history
echo.
echo 📜 История команд M425 MFP...
echo.
python hp_m425_scanner_counter.py --history
echo.
pause
goto main_menu

:clear_m425_config
echo.
echo ⚠️  ВНИМАНИЕ: Это удалит конфигурационный файл M425 со всеми данными!
set /p confirm="Продолжить? (y/n): "
if /i not "%confirm%"=="y" goto main_menu

if exist "m425_counter_config.json" (
    del "m425_counter_config.json"
    echo ✅ Конфигурационный файл M425 удален
) else (
    echo ℹ️  Конфигурационный файл M425 не найден
)
echo.
pause
goto main_menu

:exit
echo.
echo 📋 Информация о конфигурации M425:
if exist "m425_counter_config.json" (
    echo ✅ Конфигурация M425 сохранена в: m425_counter_config.json
    echo    Этот файл содержит настройки M425 MFP и историю команд
) else (
    echo ℹ️  Конфигурационный файл M425 не создан
)
echo.
echo 💡 Для M425 MFP также доступны:
echo    • Управление через системные команды
echo    • Специфичные PJL команды для MFP
echo    • Расширенная диагностика многофункционального устройства
echo.
echo 👋 До свидания!
exit /b 0
