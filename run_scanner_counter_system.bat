@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title HP LaserJet Pro 400 Scanner Counter (Системные методы)

echo.
echo ======================================================
echo   HP LaserJet Pro 400 Scanner Counter
echo   ТОЛЬКО СИСТЕМНЫЕ МЕТОДЫ (без внешних библиотек)
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

:: Проверяем наличие системного скрипта
if not exist "hp_scanner_counter_system.py" (
    echo ❌ Файл hp_scanner_counter_system.py не найден!
    echo    Убедитесь, что вы запускаете скрипт из правильной папки
    pause
    exit /b 1
)

echo ℹ️  Особенности системной версии:
echo   • Не требует установки pyusb
echo   • Использует только встроенные команды Windows/Linux
echo   • Сохраняет значения счетчика в файл конфигурации
echo   • Пытается получить реальные значения через WMI/CUPS
echo.

:main_menu
cls
echo.
echo ======================================================
echo   HP Scanner Counter (Системные методы)
echo ======================================================
echo.
echo 1. Показать список принтеров
echo 2. Выбрать принтер интерактивно
echo 3. Указать USB порт вручную
echo 4. Получить текущее значение счетчика
echo 5. Установить значение счетчика
echo 6. Сбросить счетчик в 0
echo 7. Получить информацию о принтере
echo 8. Показать историю команд
echo 9. Очистить конфигурацию
echo 0. Выход
echo.

set /p choice="Выберите действие (0-9): "

if "%choice%"=="1" goto list_printers
if "%choice%"=="2" goto select_printer
if "%choice%"=="3" goto manual_usb_port
if "%choice%"=="4" goto get_counter
if "%choice%"=="5" goto set_counter  
if "%choice%"=="6" goto reset_counter
if "%choice%"=="7" goto printer_info
if "%choice%"=="8" goto show_history
if "%choice%"=="9" goto clear_config
if "%choice%"=="0" goto exit
goto main_menu

:list_printers
echo.
echo 🔍 Поиск принтеров через системные команды...
echo.
python hp_scanner_counter_system.py --list
echo.
pause
goto main_menu

:select_printer
echo.
echo 🎯 Интерактивный выбор принтера...
echo    Будет показан список доступных принтеров для выбора
echo.
python hp_scanner_counter_system.py --select
echo.
pause
goto main_menu

:manual_usb_port
echo.
echo 🔌 Указание USB порта вручную...
echo.
set /p usb_port="Введите USB порт (например, USB001, 1, USB002): "
if "%usb_port%"=="" (
    echo ❌ USB порт не может быть пустым!
    pause
    goto main_menu
)

echo.
echo 🔧 Проверка USB порта %usb_port%...
echo.
python hp_scanner_counter_system.py --usb-port %usb_port% --info
if errorlevel 1 (
    echo.
    echo ❌ Ошибка подключения к USB порту %usb_port%
    echo 💡 Проверьте правильность порта и подключение принтера
) else (
    echo.
    echo ✅ USB порт %usb_port% настроен успешно
)
echo.
pause
goto main_menu

:get_counter
echo.
echo 📊 Получение текущего значения счетчика...
echo.
echo 🔍 Попытка использовать сохраненный принтер...
python hp_scanner_counter_system.py --use-saved --get
if errorlevel 1 (
    echo.
    echo ⚠️  Сохраненный принтер не найден или не работает
    echo 🎯 Запуск интерактивного выбора...
    echo.
    python hp_scanner_counter_system.py --interactive --get
)
echo.
echo ℹ️  Примечание: Значение может быть получено из:
echo    • Реального статуса принтера (через WMI/CUPS)
echo    • Сохраненной конфигурации (если реальное недоступно)
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
echo 🔍 Попытка использовать сохраненный принтер...
python hp_scanner_counter_system.py --use-saved --set %counter_value%
if errorlevel 1 (
    echo.
    echo ⚠️  Сохраненный принтер не найден или не работает
    echo 🎯 Запуск интерактивного выбора...
    echo.
    python hp_scanner_counter_system.py --interactive --set %counter_value%
)
echo.
echo ℹ️  Значение сохранено в конфигурации для последующего использования
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
python hp_scanner_counter_system.py --reset
echo.
pause
goto main_menu

:printer_info
echo.
echo 📋 Получение информации о принтере...
echo.
python hp_scanner_counter_system.py --info
echo.
pause
goto main_menu

:show_history
echo.
echo 📜 История команд...
echo.
python hp_scanner_counter_system.py --history
echo.
pause
goto main_menu

:clear_config
echo.
echo ⚠️  ВНИМАНИЕ: Это удалит файл конфигурации со всеми сохраненными данными!
set /p confirm="Продолжить? (y/n): "
if /i not "%confirm%"=="y" goto main_menu

if exist "printer_counter_config.json" (
    del "printer_counter_config.json"
    echo ✅ Файл конфигурации удален
) else (
    echo ℹ️  Файл конфигурации не найден
)
echo.
pause
goto main_menu

:exit
echo.
echo 📋 Информация о конфигурации:
if exist "printer_counter_config.json" (
    echo ✅ Конфигурация сохранена в: printer_counter_config.json
    echo    Этот файл содержит ваши настройки и историю команд
) else (
    echo ℹ️  Файл конфигурации не создан
)
echo.
echo 👋 До свидания!
exit /b 0
