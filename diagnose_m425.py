#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика HP LaserJet MFP M425 USB подключения
Подробная диагностика для поиска M425 принтера
"""

import subprocess
import platform
import sys
import os
import re
from typing import List, Dict


def print_section(title: str):
    """Выводит заголовок секции"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def run_command(command: List[str], description: str = "", timeout: int = 15) -> tuple:
    """Выполняет команду и возвращает результат"""
    print(f"\n🔍 {description}")
    print(f"📝 Команда: {' '.join(command)}")
    print("-" * 40)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -2, "", str(e)


def diagnose_windows_m425():
    """Диагностика M425 в Windows"""
    print_section("ДИАГНОСТИКА M425 В WINDOWS")
    
    # 1. Базовый поиск принтеров
    print("\n1️⃣ БАЗОВЫЙ ПОИСК ПРИНТЕРОВ")
    code, stdout, stderr = run_command([
        'wmic', 'printer', 'get', 'Name,PortName,DriverName,Status'
    ], "Получение списка всех принтеров")
    
    if code == 0:
        print("✅ Результат:")
        lines = stdout.strip().split('\n')
        found_hp = False
        for line in lines[1:]:  # Пропускаем заголовок
            if line.strip():
                print(f"   📄 {line.strip()}")
                if any(term in line.upper() for term in ['HP', 'HEWLETT', 'LASER', 'M425', 'MFP']):
                    found_hp = True
                    print(f"      ⭐ Потенциальный HP принтер!")
        
        if not found_hp:
            print("   ❌ HP принтеры не найдены в базовом поиске")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    # 2. Поиск M425 по имени
    print("\n2️⃣ ПОИСК M425 ПО ИМЕНИ")
    m425_queries = [
        'Name like "%M425%"',
        'Name like "%400%" and Name like "%MFP%"',
        'Name like "%LaserJet%" and Name like "%400%"',
        'Name like "%HP%" and Name like "%MFP%"'
    ]
    
    for i, query in enumerate(m425_queries, 1):
        code, stdout, stderr = run_command([
            'wmic', 'printer', 'where', query, 'get', 'Name,PortName,DriverName'
        ], f"Поиск {i}: {query}")
        
        if code == 0 and stdout.strip():
            lines = stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    print(f"   ✅ Найден: {line.strip()}")
        else:
            print(f"   ❌ Не найден")
    
    # 3. Поиск по драйверу
    print("\n3️⃣ ПОИСК ПО ДРАЙВЕРУ")
    driver_queries = [
        'DriverName like "%M425%"',
        'DriverName like "%400%"',
        'DriverName like "%MFP%"',
        'DriverName like "%LaserJet%"'
    ]
    
    for i, query in enumerate(driver_queries, 1):
        code, stdout, stderr = run_command([
            'wmic', 'printer', 'where', query, 'get', 'Name,DriverName'
        ], f"Поиск драйвера {i}: {query}")
        
        if code == 0 and stdout.strip():
            lines = stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    print(f"   ✅ Найден драйвер: {line.strip()}")
    
    # 4. Поиск USB принтеров
    print("\n4️⃣ ПОИСК USB ПРИНТЕРОВ")
    usb_queries = [
        'PortName like "USB%"',
        'PortName="USB001"',
        'PortName="USB002"',
        'PortName="USB003"'
    ]
    
    for i, query in enumerate(usb_queries, 1):
        code, stdout, stderr = run_command([
            'wmic', 'printer', 'where', query, 'get', 'Name,PortName'
        ], f"USB поиск {i}: {query}")
        
        if code == 0 and stdout.strip():
            lines = stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    print(f"   ✅ USB принтер: {line.strip()}")
    
    # 5. Проверка USB портов
    print("\n5️⃣ ПРОВЕРКА USB ПОРТОВ")
    for port in ['USB001', 'USB002', 'USB003', 'USB004']:
        code, stdout, stderr = run_command([
            'wmic', 'path', 'Win32_Printer', 'where', f'PortName="{port}"', 'get', 'Name'
        ], f"Проверка порта {port}")
        
        if code == 0 and stdout.strip():
            lines = stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip():
                    print(f"   ✅ Порт {port}: {line.strip()}")
        else:
            print(f"   ❌ Порт {port}: пустой")
    
    # 6. PowerShell диагностика
    print("\n6️⃣ POWERSHELL ДИАГНОСТИКА")
    ps_script = '''
Write-Output "=== Поиск HP принтеров ==="
Get-WmiObject -Class Win32_Printer | Where-Object {
    $_.Name -like "*HP*" -or 
    $_.Name -like "*Hewlett*" -or
    $_.DriverName -like "*HP*" -or
    $_.DriverName -like "*M425*"
} | Select-Object Name, PortName, DriverName, Status | Format-Table -AutoSize

Write-Output "=== Поиск USB устройств ==="
Get-WmiObject -Class Win32_PnPEntity | Where-Object {
    $_.Name -like "*HP*" -and $_.Name -like "*USB*"
} | Select-Object Name, DeviceID, Status | Format-Table -AutoSize

Write-Output "=== Детальный поиск M425 ==="
Get-WmiObject -Class Win32_Printer | Where-Object {
    $_.Name -like "*M425*" -or
    $_.Name -like "*400*MFP*" -or
    $_.DriverName -like "*M425*"
} | Select-Object * | Format-List
'''
    
    code, stdout, stderr = run_command([
        'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
    ], "PowerShell детальная диагностика")
    
    if code == 0:
        print("✅ PowerShell результат:")
        print(stdout)
    else:
        print(f"❌ PowerShell ошибка: {stderr}")


def diagnose_linux_m425():
    """Диагностика M425 в Linux"""
    print_section("ДИАГНОСТИКА M425 В LINUX")
    
    # 1. lsusb диагностика
    print("\n1️⃣ USB УСТРОЙСТВА")
    code, stdout, stderr = run_command(['lsusb'], "Список USB устройств")
    
    if code == 0:
        print("✅ USB устройства:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"   📄 {line}")
                if any(term.lower() in line.lower() for term in ['hp', 'hewlett', 'laser', 'm425']):
                    print(f"      ⭐ Потенциальный HP!")
    
    # 2. CUPS принтеры
    print("\n2️⃣ CUPS ПРИНТЕРЫ")
    code, stdout, stderr = run_command(['lpstat', '-p'], "CUPS принтеры")
    
    if code == 0:
        print("✅ CUPS принтеры:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"   📄 {line}")
    
    # 3. Детальная CUPS информация
    print("\n3️⃣ ДЕТАЛЬНАЯ CUPS ИНФОРМАЦИЯ")
    code, stdout, stderr = run_command(['lpstat', '-l', '-p'], "Детальная информация CUPS")
    
    if code == 0:
        print("✅ Детальная CUPS информация:")
        print(stdout[:1000] + "..." if len(stdout) > 1000 else stdout)
    
    # 4. USB устройства принтеров
    print("\n4️⃣ USB ПРИНТЕРЫ")
    for i in range(4):
        device = f'/dev/usb/lp{i}'
        if os.path.exists(device):
            print(f"   ✅ Найден: {device}")
            try:
                stat = os.stat(device)
                print(f"      Права: {oct(stat.st_mode)[-3:]}")
            except:
                pass
        else:
            print(f"   ❌ Не найден: {device}")


def diagnose_usb_hardware():
    """Диагностика USB оборудования"""
    print_section("ДИАГНОСТИКА USB ОБОРУДОВАНИЯ")
    
    system = platform.system().lower()
    
    if system == "windows":
        # Проверка USB контроллеров
        print("\n1️⃣ USB КОНТРОЛЛЕРЫ")
        code, stdout, stderr = run_command([
            'wmic', 'path', 'Win32_USBController', 'get', 'Name,Status'
        ], "USB контроллеры")
        
        if code == 0:
            for line in stdout.strip().split('\n')[1:]:
                if line.strip():
                    print(f"   📄 {line.strip()}")
        
        # Проверка USB хабов
        print("\n2️⃣ USB ХАБЫ")
        code, stdout, stderr = run_command([
            'wmic', 'path', 'Win32_USBHub', 'get', 'Name,Status'
        ], "USB хабы")
        
        if code == 0:
            for line in stdout.strip().split('\n')[1:]:
                if line.strip():
                    print(f"   📄 {line.strip()}")
        
        # PnP устройства HP
        print("\n3️⃣ HP PNP УСТРОЙСТВА")
        code, stdout, stderr = run_command([
            'wmic', 'path', 'Win32_PnPEntity', 'where', 'Name like "%HP%" or Name like "%Hewlett%"',
            'get', 'Name,Status,DeviceID'
        ], "HP PnP устройства")
        
        if code == 0:
            for line in stdout.strip().split('\n')[1:]:
                if line.strip():
                    print(f"   📄 {line.strip()}")
    
    elif system == "linux":
        # dmesg для USB
        print("\n1️⃣ DMESG USB СОБЫТИЯ")
        code, stdout, stderr = run_command([
            'dmesg', '|', 'grep', '-i', 'usb.*hp'
        ], "USB события HP", timeout=10)
        
        if code == 0 and stdout:
            for line in stdout.split('\n')[-10:]:  # Последние 10 строк
                if line.strip():
                    print(f"   📄 {line}")


def check_drivers():
    """Проверка драйверов"""
    print_section("ПРОВЕРКА ДРАЙВЕРОВ")
    
    system = platform.system().lower()
    
    if system == "windows":
        print("\n1️⃣ УСТАНОВЛЕННЫЕ ДРАЙВЕРЫ HP")
        code, stdout, stderr = run_command([
            'wmic', 'path', 'Win32_SystemDriver', 'where', 'Name like "%HP%" or Name like "%hewlett%"',
            'get', 'Name,State,Status'
        ], "Системные драйверы HP")
        
        if code == 0:
            for line in stdout.strip().split('\n')[1:]:
                if line.strip():
                    print(f"   📄 {line.strip()}")
        
        # Драйверы принтеров
        print("\n2️⃣ ДРАЙВЕРЫ ПРИНТЕРОВ")
        code, stdout, stderr = run_command([
            'wmic', 'path', 'Win32_PrinterDriver', 'where', 'Name like "%M425%" or Name like "%400%" or Name like "%MFP%"',
            'get', 'Name,Version'
        ], "Драйверы принтеров")
        
        if code == 0:
            for line in stdout.strip().split('\n')[1:]:
                if line.strip():
                    print(f"   📄 {line.strip()}")


def suggest_solutions():
    """Предлагает решения"""
    print_section("РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ")
    
    print("\n🔧 ВОЗМОЖНЫЕ ПРИЧИНЫ И РЕШЕНИЯ:")
    print("\n1️⃣ ПРИНТЕР НЕ УСТАНОВЛЕН В СИСТЕМЕ:")
    print("   • Установите драйвер M425 с сайта HP")
    print("   • Подключите принтер и дождитесь автоматической установки")
    print("   • Попробуйте 'Добавить принтер' в настройках")
    
    print("\n2️⃣ ПРИНТЕР УСТАНОВЛЕН, НО НЕПРАВИЛЬНО:")
    print("   • Проверьте имя принтера в системе")
    print("   • Убедитесь, что M425 не определился как обычный принтер")
    print("   • Переустановите драйвер с поддержкой MFP функций")
    
    print("\n3️⃣ USB ПОДКЛЮЧЕНИЕ:")
    print("   • Попробуйте другой USB кабель")
    print("   • Используйте другой USB порт")
    print("   • Убедитесь, что M425 включен и готов")
    
    print("\n4️⃣ ПРАВА ДОСТУПА:")
    print("   • Запустите скрипт от администратора")
    print("   • Проверьте права доступа к USB устройствам")
    
    print("\n5️⃣ АЛЬТЕРНАТИВНЫЕ МЕТОДЫ:")
    print("   • Используйте ручное указание порта:")
    print("     python hp_m425_scanner_counter.py --usb-port USB001 --info")
    print("   • Попробуйте разные порты: USB001, USB002, USB003")
    
    print("\n6️⃣ ДИАГНОСТИЧЕСКИЕ КОМАНДЫ:")
    print("   • Проверьте конкретный порт:")
    print("     wmic printer where PortName=\"USB001\" get Name")
    print("   • Найдите все HP устройства:")
    print("     wmic printer where \"Name like '%HP%'\" get Name,PortName")


def main():
    """Основная функция диагностики"""
    print("🔧 Диагностика HP LaserJet MFP M425 USB подключения")
    print("=" * 60)
    
    system = platform.system().lower()
    print(f"🖥️  Операционная система: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    
    if system == "windows":
        diagnose_windows_m425()
    elif system == "linux":
        diagnose_linux_m425()
    else:
        print(f"❌ Неподдерживаемая ОС: {system}")
        return
    
    diagnose_usb_hardware()
    check_drivers()
    suggest_solutions()
    
    print("\n" + "=" * 60)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)
    
    print("\n💡 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Проанализируйте результаты выше")
    print("2. Если M425 найден - запомните точное имя и порт")
    print("3. Если не найден - следуйте рекомендациям")
    print("4. Попробуйте ручное указание порта")
    print("5. Обратитесь за помощью с результатами диагностики")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка диагностики: {e}")
        sys.exit(1)
