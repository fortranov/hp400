@echo off
chcp 65001 >nul
setlocal

title HP Scanner Counter Test - Проверка исправления

echo.
echo ======================================================
echo   Тестирование исправления проблемы "Command sent"
echo ======================================================
echo.

echo 🧪 Этот скрипт проверит разные методы получения счетчика
echo.

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    pause
    exit /b 1
)

echo 📋 Доступные методы тестирования:
echo.
echo 1. Улучшенная версия (hp_scanner_counter_improved.py)
echo 2. USB версия с исправлениями (hp_scanner_counter_usb.py)  
echo 3. Автоматическая версия (hp_scanner_counter_auto.py)
echo 4. Сетевая версия (требует IP)
echo 5. Запустить все тесты подряд
echo.

set /p choice="Выберите метод тестирования (1-5): "

if "%choice%"=="1" goto test_improved
if "%choice%"=="2" goto test_usb
if "%choice%"=="3" goto test_auto
if "%choice%"=="4" goto test_network
if "%choice%"=="5" goto test_all
goto end

:test_improved
echo.
echo 🚀 Тестирование улучшенной версии...
echo    Эта версия должна возвращать числовые значения вместо "Command sent"
echo.
python hp_scanner_counter_improved.py --scan
echo.
echo 📊 Получение счетчика:
python hp_scanner_counter_improved.py --get
echo.
pause
goto end

:test_usb
echo.
echo 🔌 Тестирование USB версии с исправлениями...
echo.
python hp_scanner_counter_usb.py --list
echo.
echo 📊 Получение счетчика:
python hp_scanner_counter_usb.py --get
echo.
pause
goto end

:test_auto
echo.
echo 🤖 Тестирование автоматической версии...
echo.
python hp_scanner_counter_auto.py --scan
echo.
echo 📊 Получение счетчика:
python hp_scanner_counter_auto.py --get
echo.
pause
goto end

:test_network
echo.
set /p ip="Введите IP адрес принтера: "
if "%ip%"=="" (
    echo ❌ IP адрес не может быть пустым
    pause
    goto end
)
echo.
echo 🌐 Тестирование сетевой версии...
echo.
python hp_scanner_counter.py %ip% --get
echo.
pause
goto end

:test_all
echo.
echo 🔄 Запуск всех тестов...
echo.

echo ================================
echo 1️⃣  УЛУЧШЕННАЯ ВЕРСИЯ
echo ================================
python hp_scanner_counter_improved.py --get
echo.

echo ================================  
echo 2️⃣  USB ВЕРСИЯ
echo ================================
python hp_scanner_counter_usb.py --get
echo.

echo ================================
echo 3️⃣  АВТОМАТИЧЕСКАЯ ВЕРСИЯ  
echo ================================
python hp_scanner_counter_auto.py --get
echo.

echo ================================
echo 📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ
echo ================================
echo.
echo Проверьте результаты выше:
echo • Если видите числовые значения - проблема исправлена ✅
echo • Если видите "Command sent" - нужна дополнительная настройка ⚠️
echo • Если ошибки - проверьте подключение принтера ❌
echo.

:end
echo.
echo 💡 Рекомендации для лучшей работы:
echo   • Установите pyusb: pip install pyusb
echo   • Запускайте от администратора для USB
echo   • Используйте hp_scanner_counter_improved.py
echo.
pause
