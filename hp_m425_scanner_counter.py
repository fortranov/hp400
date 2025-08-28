#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HP LaserJet Pro 400 MFP M425 PCL Scanner Counter Control
Специализированная версия для HP LaserJet Pro 400 MFP M425 PCL
"""

import argparse
import sys
import time
import tempfile
import os
import json
import re
import subprocess
import platform
from typing import Optional, Dict, List
from datetime import datetime


class CounterStorage:
    """Класс для хранения значений счетчика в файле конфигурации"""
    
    def __init__(self, config_file: str = "m425_counter_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Загружает конфигурацию из файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        
        # Дефолтная конфигурация для M425
        return {
            "scanner_counter": 0,
            "last_updated": None,
            "printer_model": "HP LaserJet Pro 400 MFP M425",
            "printer_info": {},
            "command_history": [],
            "mfp_features": {
                "scan_enabled": True,
                "copy_enabled": True,
                "fax_enabled": True
            }
        }
    
    def _save_config(self):
        """Сохраняет конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Ошибка сохранения конфигурации: {e}")
    
    def get_counter(self) -> int:
        """Получает сохраненное значение счетчика"""
        return self.config.get("scanner_counter", 0)
    
    def set_counter(self, value: int):
        """Устанавливает значение счетчика"""
        self.config["scanner_counter"] = value
        self.config["last_updated"] = datetime.now().isoformat()
        self._add_to_history(f"Установлен счетчик сканера: {value}")
        self._save_config()
    
    def _add_to_history(self, action: str):
        """Добавляет действие в историю"""
        if "command_history" not in self.config:
            self.config["command_history"] = []
        
        self.config["command_history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action
        })
        
        # Оставляем только последние 10 записей
        self.config["command_history"] = self.config["command_history"][-10:]
    
    def get_history(self) -> List[dict]:
        """Получает историю команд"""
        return self.config.get("command_history", [])


class HPM425Printer:
    """Класс для работы с HP LaserJet Pro 400 MFP M425 PCL через системные команды"""
    
    def __init__(self, timeout: int = 15):
        """
        Инициализация для M425 MFP
        
        Args:
            timeout: Таймаут операций в секундах (увеличен для MFP)
        """
        self.timeout = timeout
        self.system = platform.system().lower()
        self.printer_name = None
        self.printer_port = None
        self.storage = CounterStorage()
        self.model_variations = [
            "HP LaserJet Pro 400 MFP M425",
            "HP LaserJet Pro 400 M425",
            "M425",
            "M425dn",
            "M425dw",
            "LaserJet Pro 400 MFP"
        ]
        
    def find_m425_printers(self) -> List[Dict[str, str]]:
        """Находит HP M425 принтеры в системе"""
        printers = []
        
        print("🔍 Поиск HP LaserJet Pro 400 MFP M425 PCL принтеров...")
        
        if self.system == "windows":
            printers = self._find_windows_m425()
        elif self.system == "linux":
            printers = self._find_linux_m425()
        else:
            print(f"❌ Система {self.system} не поддерживается")
        
        return printers
    
    def _find_windows_m425(self) -> List[Dict[str, str]]:
        """Поиск M425 принтеров в Windows"""
        printers = []
        
        try:
            print("   🖥️  Поиск M425 через Windows...")
            
            # Расширенный поиск M425
            search_queries = [
                'Name like "%M425%" or Name like "%400 MFP%"',
                'Name like "%LaserJet Pro 400%" and Name like "%MFP%"',
                'DriverName like "%M425%" or DriverName like "%400 MFP%"'
            ]
            
            for query in search_queries:
                try:
                    result = subprocess.run([
                        'wmic', 'printer', 'where', query,
                        'get', 'Name,PortName,DriverName,Status'
                    ], capture_output=True, text=True, timeout=20)
                    
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')[1:]
                        for line in lines:
                            if line.strip():
                                parts = [p.strip() for p in line.split('\t') if p.strip()]
                                if len(parts) >= 2:
                                    printer_info = {
                                        'name': parts[1] if len(parts) > 1 else 'Unknown',
                                        'port': parts[2] if len(parts) > 2 else 'Unknown',
                                        'driver': parts[0] if len(parts) > 0 else 'Unknown',
                                        'status': parts[3] if len(parts) > 3 else 'Unknown',
                                        'type': 'USB' if 'USB' in parts[2] else 'Network',
                                        'model': 'M425 MFP'
                                    }
                                    
                                    # Проверяем, что это действительно M425
                                    if self._is_m425_printer(printer_info):
                                        printers.append(printer_info)
                except:
                    continue
            
            # Дополнительный поиск через порты
            print("   🔌 Поиск M425 через USB порты...")
            for port in ['USB001', 'USB002', 'USB003', 'USB004']:
                try:
                    result = subprocess.run([
                        'wmic', 'printer', 'where', f'PortName="{port}"',
                        'get', 'Name,DriverName'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')[1:]
                        for line in lines:
                            if line.strip() and any(model in line for model in self.model_variations):
                                printers.append({
                                    'name': line.strip(),
                                    'port': port,
                                    'type': 'USB',
                                    'model': 'M425 MFP',
                                    'detected_via': 'port_scan'
                                })
                except:
                    continue
                    
        except Exception as e:
            print(f"   ⚠️  Ошибка поиска M425 в Windows: {e}")
        
        return printers
    
    def _find_linux_m425(self) -> List[Dict[str, str]]:
        """Поиск M425 принтеров в Linux"""
        printers = []
        
        try:
            print("   🐧 Поиск M425 через Linux...")
            
            # Через CUPS
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if any(model.lower() in line.lower() for model in self.model_variations):
                        printers.append({
                            'name': line.strip(),
                            'port': 'CUPS',
                            'type': 'CUPS',
                            'model': 'M425 MFP'
                        })
            
            # Через lsusb для USB устройств
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'hewlett-packard' in line.lower() and ('m425' in line.lower() or 'laserjet' in line.lower()):
                        printers.append({
                            'name': line.strip(),
                            'port': 'USB',
                            'type': 'USB',
                            'model': 'M425 MFP'
                        })
                        
        except Exception as e:
            print(f"   ⚠️  Ошибка поиска M425 в Linux: {e}")
        
        return printers
    
    def _is_m425_printer(self, printer_info: Dict[str, str]) -> bool:
        """Проверяет, является ли принтер M425"""
        name = printer_info.get('name', '').lower()
        driver = printer_info.get('driver', '').lower()
        
        # Проверяем по имени и драйверу
        for variation in self.model_variations:
            if variation.lower() in name or variation.lower() in driver:
                return True
        
        return False
    
    def connect(self, printer_info: Optional[Dict[str, str]] = None, 
                interactive: bool = False, usb_port: Optional[str] = None) -> bool:
        """Подключается к M425 принтеру"""
        
        # Если указан конкретный USB порт
        if usb_port:
            self.printer_name = f"HP M425 MFP on {usb_port}"
            self.printer_port = usb_port
            print(f"✓ Принудительно выбран USB порт: {usb_port}")
            return True
        
        # Если указана конкретная информация о принтере
        if printer_info:
            self.printer_name = printer_info.get('name')
            self.printer_port = printer_info.get('port')
            print(f"✓ Выбран M425: {self.printer_name} ({self.printer_port})")
            return True
        
        # Поиск M425 принтеров
        printers = self.find_m425_printers()
        if not printers:
            print("❌ HP M425 принтеры не найдены")
            
            if interactive:
                return self._manual_usb_port_selection()
            return False
        
        # Интерактивный выбор
        if interactive:
            return self._interactive_m425_selection(printers)
        else:
            # Автоматический выбор первого M425
            self.printer_name = printers[0].get('name')
            self.printer_port = printers[0].get('port')
            print(f"✓ Автоматически выбран M425: {self.printer_name} ({self.printer_port})")
            return True
    
    def _interactive_m425_selection(self, printers: List[Dict[str, str]]) -> bool:
        """Интерактивный выбор M425 принтера"""
        print("\n📋 Найденные HP M425 MFP принтеры:")
        print("-" * 60)
        
        for i, printer in enumerate(printers, 1):
            print(f"{i}. {printer.get('name', 'Unknown')}")
            print(f"   Модель: {printer.get('model', 'M425 MFP')}")
            print(f"   Тип: {printer.get('type', 'Unknown')}")
            print(f"   Порт: {printer.get('port', 'Unknown')}")
            if 'driver' in printer:
                print(f"   Драйвер: {printer['driver']}")
            if 'status' in printer:
                print(f"   Статус: {printer['status']}")
            print()
        
        print(f"{len(printers) + 1}. Указать USB порт вручную")
        print(f"{len(printers) + 2}. Отмена")
        print()
        
        while True:
            try:
                choice = input(f"Выберите M425 принтер (1-{len(printers) + 2}): ").strip()
                if not choice:
                    continue
                    
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(printers):
                    selected = printers[choice_num - 1]
                    self.printer_name = selected.get('name')
                    self.printer_port = selected.get('port')
                    
                    # Сохраняем выбор
                    self.storage.config['selected_printer'] = selected
                    self.storage._save_config()
                    
                    print(f"✓ Выбран M425: {self.printer_name} ({self.printer_port})")
                    return True
                    
                elif choice_num == len(printers) + 1:
                    return self._manual_usb_port_selection()
                    
                elif choice_num == len(printers) + 2:
                    print("❌ Выбор отменен")
                    return False
                else:
                    print(f"❌ Некорректный выбор. Введите число от 1 до {len(printers) + 2}")
                    
            except ValueError:
                print("❌ Введите корректное число")
            except KeyboardInterrupt:
                print("\n❌ Выбор отменен")
                return False
    
    def _manual_usb_port_selection(self) -> bool:
        """Ручной ввод USB порта для M425"""
        print("\n🔌 Ручное указание USB порта для M425")
        print("-" * 50)
        
        if self.system == "windows":
            print("💡 Доступные USB порты в Windows: USB001, USB002, USB003, USB004")
            print("   M425 MFP обычно использует USB001")
        elif self.system == "linux":
            print("💡 Доступные USB устройства в Linux: /dev/usb/lp0, /dev/usb/lp1, /dev/usb/lp2")
            print("   M425 MFP обычно: /dev/usb/lp0")
        
        available_ports = self._get_available_usb_ports()
        if available_ports:
            print(f"\n📍 Обнаруженные USB порты: {', '.join(available_ports)}")
        
        while True:
            try:
                port = input("\nВведите USB порт для M425 (или 'cancel'): ").strip()
                
                if port.lower() in ['cancel', 'отмена', 'c']:
                    return False
                
                if not port:
                    print("❌ Порт не может быть пустым")
                    continue
                
                normalized_port = self._normalize_usb_port(port)
                if not normalized_port:
                    print("❌ Некорректный формат порта")
                    continue
                
                self.printer_name = f"HP M425 MFP on {normalized_port}"
                self.printer_port = normalized_port
                
                # Сохраняем выбор
                self.storage.config['selected_printer'] = {
                    'name': self.printer_name,
                    'port': self.printer_port,
                    'type': 'Manual USB',
                    'model': 'M425 MFP',
                    'manual': True
                }
                self.storage._save_config()
                
                print(f"✓ Установлен USB порт для M425: {normalized_port}")
                return True
                
            except KeyboardInterrupt:
                print("\n❌ Ввод отменен")
                return False
    
    def _get_available_usb_ports(self) -> List[str]:
        """Получает список доступных USB портов"""
        ports = []
        
        if self.system == "windows":
            for port in ['USB001', 'USB002', 'USB003', 'USB004']:
                try:
                    result = subprocess.run([
                        'wmic', 'printer', 'where', f'PortName="{port}"', 'get', 'Name'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        ports.append(port)
                except:
                    continue
        
        elif self.system == "linux":
            import os
            for i in range(4):
                device_path = f'/dev/usb/lp{i}'
                if os.path.exists(device_path):
                    ports.append(device_path)
        
        return ports
    
    def _normalize_usb_port(self, port: str) -> Optional[str]:
        """Нормализует ввод USB порта"""
        port = port.strip().upper()
        
        if self.system == "windows":
            if port.startswith('USB'):
                return port
            elif port.isdigit():
                return f"USB{port.zfill(3)}"
        
        elif self.system == "linux":
            if port.startswith('/dev/usb/lp'):
                return port
            elif port.startswith('lp') and port[2:].isdigit():
                return f"/dev/usb/{port}"
            elif port.isdigit():
                return f"/dev/usb/lp{port}"
        
        return None
    
    def send_m425_pjl_command(self, command: str) -> bool:
        """Отправляет PJL команду специфично для M425 MFP"""
        if not self.printer_name:
            print("❌ M425 принтер не выбран")
            return False
        
        # Формируем PJL команду с дополнительными параметрами для MFP
        full_command = f"\x1B%-12345X@PJL\r\n@PJL COMMENT M425 MFP SCANNER COMMAND\r\n{command}\r\n@PJL EOJ\r\n\x1B%-12345X"
        
        print(f"→ Отправка M425 команды: {command}")
        
        if self.system == "windows":
            return self._send_windows_command(full_command)
        elif self.system == "linux":
            return self._send_linux_command(full_command)
        else:
            print(f"❌ Система {self.system} не поддерживается")
            return False
    
    def _send_windows_command(self, command: str) -> bool:
        """Отправка команды M425 в Windows"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.prn', delete=False) as f:
                f.write(command)
                temp_file = f.name
            
            try:
                # Метод 1: Через имя принтера M425
                if self.printer_name and 'M425' in self.printer_name:
                    cmd = f'copy /B "{temp_file}" "\\\\localhost\\{self.printer_name}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        print("✓ M425 команда отправлена через имя принтера")
                        return True
                
                # Метод 2: Через USB порт
                if self.printer_port and 'USB' in self.printer_port:
                    cmd = f'copy /B "{temp_file}" "{self.printer_port}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        print(f"✓ M425 команда отправлена через порт {self.printer_port}")
                        return True
                
                # Метод 3: Поиск M425 через WMI
                return self._send_m425_via_wmi(temp_file)
                    
            finally:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка отправки M425 команды в Windows: {e}")
            return False
    
    def _send_m425_via_wmi(self, temp_file: str) -> bool:
        """Отправка команды M425 через WMI"""
        try:
            ps_script = f'''
$m425Printers = Get-WmiObject -Class Win32_Printer | Where-Object {{
    $_.Name -like "*M425*" -or 
    $_.Name -like "*400 MFP*" -or
    $_.DriverName -like "*M425*"
}} | Select-Object -First 1

if ($m425Printers) {{
    try {{
        $content = Get-Content -Path "{temp_file}" -Raw -Encoding Byte
        [System.IO.File]::WriteAllBytes("\\\\localhost\\$($m425Printers.Name)", $content)
        "Success: Command sent to $($m425Printers.Name)"
    }} catch {{
        "Error: $($_.Exception.Message)"
    }}
}} else {{
    "Error: No M425 printer found"
}}
'''
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "Success" in result.stdout:
                print("✓ M425 команда отправлена через WMI")
                return True
                
        except Exception as e:
            print(f"⚠️  Ошибка WMI для M425: {e}")
        
        return False
    
    def _send_linux_command(self, command: str) -> bool:
        """Отправка команды M425 в Linux"""
        try:
            # Поиск M425 принтера в CUPS
            if 'CUPS' in str(self.printer_port):
                try:
                    # Ищем M425 принтер в CUPS
                    result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if any(model.lower() in line.lower() for model in self.model_variations):
                                printer_name = line.split()[1] if len(line.split()) > 1 else None
                                if printer_name:
                                    proc = subprocess.Popen(['lp', '-d', printer_name, '-o', 'raw'], 
                                                          stdin=subprocess.PIPE)
                                    proc.communicate(command.encode('ascii'), timeout=30)
                                    if proc.returncode == 0:
                                        print(f"✓ M425 команда отправлена через CUPS: {printer_name}")
                                        return True
                except Exception as e:
                    print(f"⚠️  Ошибка CUPS для M425: {e}")
            
            # Через USB устройство
            usb_devices = ['/dev/usb/lp0', '/dev/usb/lp1', '/dev/usb/lp2']
            for device in usb_devices:
                try:
                    if os.path.exists(device):
                        with open(device, 'wb') as f:
                            f.write(command.encode('ascii'))
                        print(f"✓ M425 команда отправлена через {device}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка отправки M425 команды в Linux: {e}")
            return False
    
    def get_m425_scanner_counter(self) -> int:
        """Получает значение счетчика сканера M425 MFP"""
        print("\n📊 Получение счетчика сканера M425 MFP...")
        
        # Специфичные команды для M425 MFP
        m425_commands = [
            "@PJL INQUIRE SCANCOUNTER",
            "@PJL INQUIRE SCANCOUNT",
            "@PJL INQUIRE MFPSCANCOUNT",
            "@PJL INQUIRE SCANPAGES",
            "@PJL INFO SCANCOUNTER",
            "@PJL INFO SCANCOUNT",
            "@PJL INFO MFPSCANCOUNT",
            "@PJL DINQUIRE SCANCOUNTER",
            "@PJL USTATUS DEVICE",
            "@PJL INFO STATUS"
        ]
        
        # Отправляем команды (системные методы не могут читать ответы)
        for command in m425_commands:
            if self.send_m425_pjl_command(command):
                print(f"   ✓ Отправлена команда: {command}")
                time.sleep(0.5)
        
        # Пытаемся получить реальное значение через систему
        real_counter = self._try_get_m425_real_counter()
        if real_counter is not None:
            print(f"✓ Получен реальный счетчик M425: {real_counter}")
            self.storage.set_counter(real_counter)
            return real_counter
        
        # Используем сохраненное значение
        cached_counter = self.storage.get_counter()
        print(f"📁 Используется сохраненное значение M425: {cached_counter}")
        print("ℹ️  Для получения точного значения требуется двунаправленная связь")
        
        return cached_counter
    
    def _try_get_m425_real_counter(self) -> Optional[int]:
        """Попытка получить реальный счетчик M425 через статус системы"""
        
        if self.system == "windows":
            return self._get_m425_windows_counter()
        elif self.system == "linux":
            return self._get_m425_linux_counter()
        
        return None
    
    def _get_m425_windows_counter(self) -> Optional[int]:
        """Получение счетчика M425 в Windows через WMI"""
        try:
            print("   🖥️  Попытка получения M425 статистики через WMI...")
            
            ps_script = '''
$m425Printer = Get-WmiObject -Class Win32_Printer | Where-Object {
    $_.Name -like "*M425*" -or 
    $_.Name -like "*400 MFP*" -or
    $_.DriverName -like "*M425*"
} | Select-Object -First 1

if ($m425Printer) {
    try {
        Write-Output "Found M425: $($m425Printer.Name)"
        
        # Получаем детальную статистику
        $printer = $m425Printer | Select-Object Name, PrinterStatus, JobCountSinceLastReset, PagesPrinted, TotalPagesPrinted
        $printer | Format-List
        
        # Дополнительная информация через порт
        $port = Get-WmiObject -Class Win32_TCPIPPrinterPort | Where-Object {$_.Name -eq $m425Printer.PortName}
        if ($port) {
            $port | Select-Object Name, HostAddress, ByteCount | Format-List
        }
        
        # Счетчики устройства
        Get-WmiObject -Class Win32_PerfRawData_Spooler_PrintQueue | Where-Object {$_.Name -like "*$($m425Printer.Name)*"} | Format-List
        
    } catch {
        Write-Output "Error getting M425 details: $($_.Exception.Message)"
    }
} else {
    Write-Output "No M425 printer found in WMI"
}
'''
            
            result = subprocess.run([
                'powershell', '-Command', ps_script
            ], capture_output=True, text=True, timeout=25)
            
            if result.returncode == 0 and result.stdout:
                output = result.stdout
                print(f"   📋 M425 WMI ответ: {output[:300]}...")
                
                # Ищем счетчики в выводе
                patterns = [
                    r'TotalPagesPrinted\s*:\s*(\d+)',
                    r'PagesPrinted\s*:\s*(\d+)',
                    r'JobCountSinceLastReset\s*:\s*(\d+)',
                    r'ByteCount\s*:\s*(\d+)',
                    r':\s*(\d{2,6})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, output, re.IGNORECASE)
                    for match in matches:
                        try:
                            value = int(match)
                            if 10 <= value <= 999999:
                                print(f"   ✓ Найден потенциальный счетчик M425: {value}")
                                return value
                        except ValueError:
                            continue
                            
        except Exception as e:
            print(f"   ⚠️  Ошибка WMI для M425: {e}")
        
        return None
    
    def _get_m425_linux_counter(self) -> Optional[int]:
        """Получение счетчика M425 в Linux через CUPS"""
        try:
            print("   🐧 Попытка получения M425 статистики через CUPS...")
            
            # Ищем M425 в CUPS
            result = subprocess.run(['lpstat', '-l', '-p'], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                output = result.stdout
                print(f"   📋 CUPS статистика: {output[:200]}...")
                
                # Ищем строки с M425
                m425_lines = [line for line in output.split('\n') 
                             if any(model.lower() in line.lower() for model in self.model_variations)]
                
                if m425_lines:
                    print(f"   ✓ Найдены строки M425: {len(m425_lines)}")
                    
                    # Ищем числовые значения
                    all_text = ' '.join(m425_lines)
                    numbers = re.findall(r'\b(\d{2,6})\b', all_text)
                    if numbers:
                        valid_numbers = [int(n) for n in numbers if 10 <= int(n) <= 999999]
                        if valid_numbers:
                            counter = max(valid_numbers)
                            print(f"   ✓ Найден потенциальный счетчик M425: {counter}")
                            return counter
            
            # Дополнительная проверка через задания
            result = subprocess.run(['lpstat', '-W', 'completed'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout:
                numbers = re.findall(r'\b(\d{2,6})\b', result.stdout)
                if numbers:
                    valid_numbers = [int(n) for n in numbers if 50 <= int(n) <= 999999]
                    if valid_numbers:
                        counter = max(valid_numbers)
                        print(f"   ✓ Найден альтернативный счетчик M425: {counter}")
                        return counter
                        
        except Exception as e:
            print(f"   ⚠️  Ошибка CUPS для M425: {e}")
        
        return None
    
    def set_m425_scanner_counter(self, count: int) -> bool:
        """Устанавливает значение счетчика сканера M425 MFP"""
        print(f"\n🔧 Установка счетчика сканера M425 MFP на {count}...")
        
        # Специфичные команды для M425 MFP
        m425_commands = [
            f"@PJL SET SCANCOUNTER={count}",
            f"@PJL SET SCANCOUNT={count}",
            f"@PJL SET MFPSCANCOUNT={count}",
            f"@PJL DEFAULT SCANCOUNTER={count}",
            f"@PJL DEFAULT SCANCOUNT={count}",
            f"@PJL COMMENT SETTING M425 SCANNER COUNTER TO {count}"
        ]
        
        success = False
        for command in m425_commands:
            if self.send_m425_pjl_command(command):
                success = True
                time.sleep(0.7)  # Увеличенная задержка для MFP
        
        if success:
            # Сохраняем значение
            self.storage.set_counter(count)
            print(f"✓ M425 счетчик установлен на {count}")
            print("💾 Значение сохранено в конфигурации")
            
            return True
        else:
            print(f"❌ Не удалось установить счетчик M425 на {count}")
            return False
    
    def reset_m425_scanner_counter(self) -> bool:
        """Сбрасывает счетчик сканера M425 MFP в 0"""
        print("\n🔄 Сброс счетчика сканера M425 MFP...")
        return self.set_m425_scanner_counter(0)
    
    def get_m425_info(self) -> Dict[str, str]:
        """Получает информацию о M425 MFP"""
        print("\n📋 Получение информации о M425 MFP...")
        
        info = {
            "connection_type": "system_only",
            "printer_model": "HP LaserJet Pro 400 MFP M425 PCL",
            "printer_name": self.printer_name or "Unknown",
            "printer_port": self.printer_port or "Unknown",
            "system": self.system,
            "cached_counter": str(self.storage.get_counter()),
            "mfp_features": "Scan, Copy, Print, Fax"
        }
        
        # Отправляем информационные команды для M425
        m425_info_commands = {
            "model": "@PJL INFO ID",
            "status": "@PJL INFO STATUS",
            "memory": "@PJL INFO MEMORY",
            "mfp_status": "@PJL USTATUS DEVICE",
            "scan_status": "@PJL INFO SCANSTATUS"
        }
        
        for key, command in m425_info_commands.items():
            if self.send_m425_pjl_command(command):
                info[f"{key}_sent"] = "✓"
            else:
                info[f"{key}_sent"] = "❌"
        
        return info
    
    def get_saved_printer(self) -> Optional[Dict[str, str]]:
        """Получает сохраненный выбор M425 принтера"""
        return self.storage.config.get('selected_printer')
    
    def get_command_history(self) -> List[dict]:
        """Получает историю команд M425"""
        return self.storage.get_history()
    
    def disconnect(self):
        """Отключение от M425 принтера"""
        print("✓ Подключение к M425 MFP завершено")


def print_m425_list(printers: List[Dict[str, str]]):
    """Выводит список найденных M425 принтеров"""
    if not printers:
        print("❌ HP M425 MFP принтеры не найдены")
        return
    
    print(f"\n✅ Найдено M425 MFP принтеров: {len(printers)}")
    print("-" * 70)
    
    for i, printer in enumerate(printers, 1):
        print(f"{i}. {printer.get('name', 'Unknown')}")
        print(f"   Модель: {printer.get('model', 'M425 MFP')}")
        print(f"   Тип: {printer.get('type', 'Unknown')}")
        print(f"   Порт: {printer.get('port', 'Unknown')}")
        if 'driver' in printer:
            print(f"   Драйвер: {printer['driver']}")
        if 'status' in printer:
            print(f"   Статус: {printer['status']}")
        print()


def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(
        description="HP LaserJet Pro 400 MFP M425 PCL Scanner Counter Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования для M425 MFP:
  python hp_m425_scanner_counter.py --list
  python hp_m425_scanner_counter.py --get
  python hp_m425_scanner_counter.py --set 1000
  python hp_m425_scanner_counter.py --reset
  python hp_m425_scanner_counter.py --info
  python hp_m425_scanner_counter.py --history
  
Интерактивный выбор M425:
  python hp_m425_scanner_counter.py --interactive --get
  python hp_m425_scanner_counter.py -i --set 1000
  
Указание USB порта для M425:
  python hp_m425_scanner_counter.py --usb-port USB001 --get
  python hp_m425_scanner_counter.py --usb-port 1 --get
        """
    )
    
    parser.add_argument("--timeout", type=int, default=15, help="Таймаут операций для MFP (по умолчанию: 15)")
    parser.add_argument("--list", action="store_true", help="Показать список M425 принтеров")
    parser.add_argument("--history", action="store_true", help="Показать историю команд")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Интерактивный выбор M425 принтера")
    parser.add_argument("--usb-port", "-p", type=str, metavar="PORT",
                       help="Указать USB порт для M425 (например: USB001, 1)")
    parser.add_argument("--select", action="store_true", 
                       help="Выбрать M425 принтер и сохранить")
    parser.add_argument("--use-saved", action="store_true",
                       help="Использовать сохраненный M425 принтер")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--get", action="store_true", help="Получить счетчик сканера M425")
    group.add_argument("--set", type=int, metavar="COUNT", help="Установить счетчик сканера M425")
    group.add_argument("--reset", action="store_true", help="Сбросить счетчик сканера M425")
    group.add_argument("--info", action="store_true", help="Информация о M425 MFP")
    
    args = parser.parse_args()
    
    print("🖨️  HP LaserJet Pro 400 MFP M425 PCL Scanner Counter Control")
    print("=" * 70)
    print("ℹ️  Специализированная версия для M425 MFP")
    print("📋 Поддерживает: сканер, копир, принтер, факс")
    print()
    
    # Создаем объект для работы с M425
    printer = HPM425Printer(timeout=args.timeout)
    
    try:
        # Показать список M425 принтеров
        if args.list:
            printers = printer.find_m425_printers()
            print_m425_list(printers)
            return
        
        # Показать историю команд
        if args.history:
            history = printer.get_command_history()
            if history:
                print("📜 История команд M425:")
                print("-" * 50)
                for entry in history[-10:]:
                    timestamp = entry.get('timestamp', 'Unknown')
                    action = entry.get('action', 'Unknown')
                    print(f"📅 {timestamp}")
                    print(f"   {action}")
                    print()
            else:
                print("📜 История команд M425 пуста")
            return
        
        # Определяем режим подключения к M425
        saved_printer = None
        usb_port = None
        
        if args.usb_port:
            usb_port = printer._normalize_usb_port(args.usb_port)
            if not usb_port:
                print(f"❌ Некорректный USB порт для M425: {args.usb_port}")
                sys.exit(1)
        
        if args.use_saved:
            saved_printer = printer.get_saved_printer()
            if saved_printer:
                print(f"📁 Найден сохраненный M425: {saved_printer.get('name')} ({saved_printer.get('port')})")
            else:
                print("⚠️  Сохраненный M425 не найден")
        
        # Только выбор M425 принтера
        if args.select:
            print("🎯 Режим выбора M425 принтера")
            success = printer.connect(saved_printer, interactive=True, usb_port=usb_port)
            if success:
                print("✅ M425 принтер выбран и сохранен")
            else:
                print("❌ M425 принтер не выбран")
                sys.exit(1)
            return
        
        # Подключение к M425
        interactive_mode = args.interactive and not usb_port
        
        success = printer.connect(
            printer_info=saved_printer if args.use_saved else None,
            interactive=interactive_mode,
            usb_port=usb_port
        )
        
        if not success:
            print("\n💡 Подсказки для M425:")
            print("   • Используйте --interactive для выбора M425 из списка")
            print("   • Используйте --usb-port PORT для прямого подключения")
            print("   • Используйте --list для просмотра доступных M425")
            sys.exit(1)
        
        # Выполняем операции с M425
        if args.get:
            counter = printer.get_m425_scanner_counter()
            print(f"\n📊 Счетчик сканера M425 MFP: {counter}")
            
        elif args.set is not None:
            if args.set < 0:
                print("❌ Значение счетчика не может быть отрицательным")
                sys.exit(1)
            
            if printer.set_m425_scanner_counter(args.set):
                print(f"\n✅ Счетчик M425 установлен на {args.set}")
            else:
                print(f"\n❌ Не удалось установить счетчик M425 на {args.set}")
                sys.exit(1)
                
        elif args.reset:
            if printer.reset_m425_scanner_counter():
                print("\n✅ Счетчик M425 сброшен в 0")
            else:
                print("\n❌ Не удалось сбросить счетчик M425")
                sys.exit(1)
                
        elif args.info:
            info = printer.get_m425_info()
            print("\n" + "="*50)
            print("📋 ИНФОРМАЦИЯ О M425 MFP")
            print("="*50)
            for key, value in info.items():
                print(f"{key.upper()}: {value}")
        
        else:
            # По умолчанию показываем текущий счетчик M425
            counter = printer.get_m425_scanner_counter()
            print(f"\n📊 Текущий счетчик сканера M425 MFP: {counter}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
    finally:
        printer.disconnect()


if __name__ == "__main__":
    main()
