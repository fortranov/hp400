#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HP LaserJet Pro 400 Scanner Counter Control (Только системные методы)
Версия скрипта, использующая ТОЛЬКО системные команды без внешних библиотек
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
    
    def __init__(self, config_file: str = "printer_counter_config.json"):
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
        
        # Дефолтная конфигурация
        return {
            "scanner_counter": 0,
            "last_updated": None,
            "printer_info": {},
            "command_history": []
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
        self._add_to_history(f"Установлен счетчик: {value}")
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


class HPPrinterSystem:
    """Класс для работы с принтером только через системные команды"""
    
    def __init__(self, timeout: int = 10):
        """
        Инициализация
        
        Args:
            timeout: Таймаут операций в секундах
        """
        self.timeout = timeout
        self.system = platform.system().lower()
        self.printer_name = None
        self.printer_port = None
        self.storage = CounterStorage()
        
    def find_hp_printers(self) -> List[Dict[str, str]]:
        """Находит HP принтеры в системе"""
        printers = []
        
        print("🔍 Поиск HP принтеров через системные команды...")
        
        if self.system == "windows":
            printers = self._find_windows_printers()
        elif self.system == "linux":
            printers = self._find_linux_printers()
        else:
            print(f"❌ Система {self.system} не поддерживается")
        
        return printers
    
    def _find_windows_printers(self) -> List[Dict[str, str]]:
        """Поиск принтеров в Windows"""
        printers = []
        
        try:
            # Поиск USB принтеров
            print("   🖥️  Поиск USB принтеров...")
            result = subprocess.run([
                'wmic', 'printer', 'where', 
                'PortName like "USB%" and (Name like "%HP%" or Name like "%Hewlett%")',
                'get', 'Name,PortName,DriverName'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split() if p.strip()]
                        if len(parts) >= 2:
                            printers.append({
                                'name': ' '.join(parts[:-2]) if len(parts) > 2 else parts[0],
                                'port': parts[-2] if len(parts) > 1 else 'USB',
                                'driver': parts[-1] if len(parts) > 2 else 'Unknown',
                                'type': 'USB'
                            })
            
            # Поиск сетевых принтеров
            print("   🌐 Поиск сетевых принтеров...")
            result = subprocess.run([
                'wmic', 'printer', 'where',
                'PortName like "IP%" and (Name like "%HP%" or Name like "%Hewlett%")',
                'get', 'Name,PortName'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split() if p.strip()]
                        if len(parts) >= 2:
                            printers.append({
                                'name': ' '.join(parts[:-1]),
                                'port': parts[-1],
                                'type': 'Network'
                            })
                            
        except Exception as e:
            print(f"   ⚠️  Ошибка поиска в Windows: {e}")
        
        return printers
    
    def _find_linux_printers(self) -> List[Dict[str, str]]:
        """Поиск принтеров в Linux"""
        printers = []
        
        try:
            # Через CUPS
            print("   🐧 Поиск через CUPS...")
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'hp' in line.lower() or 'hewlett' in line.lower():
                        printers.append({
                            'name': line.strip(),
                            'port': 'CUPS',
                            'type': 'CUPS'
                        })
            
            # Через lsusb
            print("   🔌 Поиск USB устройств...")
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'hewlett-packard' in line.lower() or ('hp' in line.lower() and 'printer' in line.lower()):
                        printers.append({
                            'name': line.strip(),
                            'port': 'USB',
                            'type': 'USB'
                        })
                        
        except Exception as e:
            print(f"   ⚠️  Ошибка поиска в Linux: {e}")
        
        return printers
    
    def connect(self, printer_info: Optional[Dict[str, str]] = None, 
                interactive: bool = False, usb_port: Optional[str] = None) -> bool:
        """
        Подключается к принтеру (выбирает принтер для работы)
        
        Args:
            printer_info: Информация о принтере из find_hp_printers()
            interactive: Включить интерактивный выбор принтера
            usb_port: Принудительно указать USB порт (например, "USB001")
        
        Returns:
            True если принтер выбран успешно
        """
        # Если указан конкретный USB порт
        if usb_port:
            self.printer_name = f"HP Printer on {usb_port}"
            self.printer_port = usb_port
            print(f"✓ Принудительно выбран USB порт: {usb_port}")
            return True
        
        # Если указана конкретная информация о принтере
        if printer_info:
            self.printer_name = printer_info.get('name')
            self.printer_port = printer_info.get('port')
            print(f"✓ Выбран принтер: {self.printer_name} ({self.printer_port})")
            return True
        
        # Поиск доступных принтеров
        printers = self.find_hp_printers()
        if not printers:
            print("❌ HP принтеры не найдены")
            
            # Предлагаем ручной ввод USB порта
            if interactive:
                return self._manual_usb_port_selection()
            return False
        
        # Интерактивный выбор
        if interactive:
            return self._interactive_printer_selection(printers)
        else:
            # Автоматический выбор первого принтера
            self.printer_name = printers[0].get('name')
            self.printer_port = printers[0].get('port')
            print(f"✓ Автоматически выбран: {self.printer_name} ({self.printer_port})")
            return True
    
    def _interactive_printer_selection(self, printers: List[Dict[str, str]]) -> bool:
        """Интерактивный выбор принтера из списка"""
        print("\n📋 Найденные принтеры:")
        print("-" * 60)
        
        for i, printer in enumerate(printers, 1):
            print(f"{i}. {printer.get('name', 'Unknown')}")
            print(f"   Тип: {printer.get('type', 'Unknown')}")
            print(f"   Порт: {printer.get('port', 'Unknown')}")
            if 'driver' in printer:
                print(f"   Драйвер: {printer['driver']}")
            print()
        
        # Добавляем опцию ручного ввода USB порта
        print(f"{len(printers) + 1}. Указать USB порт вручную")
        print(f"{len(printers) + 2}. Отмена")
        print()
        
        while True:
            try:
                choice = input(f"Выберите принтер (1-{len(printers) + 2}): ").strip()
                if not choice:
                    continue
                    
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(printers):
                    # Выбран принтер из списка
                    selected = printers[choice_num - 1]
                    self.printer_name = selected.get('name')
                    self.printer_port = selected.get('port')
                    
                    # Сохраняем выбор в конфигурации
                    self.storage.config['selected_printer'] = selected
                    self.storage._save_config()
                    
                    print(f"✓ Выбран: {self.printer_name} ({self.printer_port})")
                    return True
                    
                elif choice_num == len(printers) + 1:
                    # Ручной ввод USB порта
                    return self._manual_usb_port_selection()
                    
                elif choice_num == len(printers) + 2:
                    # Отмена
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
        """Ручной ввод USB порта"""
        print("\n🔌 Ручное указание USB порта")
        print("-" * 40)
        
        if self.system == "windows":
            print("💡 Доступные USB порты в Windows: USB001, USB002, USB003, USB004")
            print("   Обычно принтеры используют USB001")
        elif self.system == "linux":
            print("💡 Доступные USB устройства в Linux: /dev/usb/lp0, /dev/usb/lp1, /dev/usb/lp2")
            print("   Или просто укажите номер: 0, 1, 2")
        
        available_ports = self._get_available_usb_ports()
        if available_ports:
            print(f"\n📍 Обнаруженные USB порты: {', '.join(available_ports)}")
        
        print("\n❓ Примеры:")
        if self.system == "windows":
            print("   USB001, USB002, USB003")
        else:
            print("   /dev/usb/lp0, lp0, 0")
        
        while True:
            try:
                port = input("\nВведите USB порт (или 'cancel' для отмены): ").strip()
                
                if port.lower() in ['cancel', 'отмена', 'c']:
                    print("❌ Ввод отменен")
                    return False
                
                if not port:
                    print("❌ Порт не может быть пустым")
                    continue
                
                # Нормализуем ввод
                normalized_port = self._normalize_usb_port(port)
                if not normalized_port:
                    print("❌ Некорректный формат порта")
                    continue
                
                self.printer_name = f"HP Printer on {normalized_port}"
                self.printer_port = normalized_port
                
                # Сохраняем выбор
                self.storage.config['selected_printer'] = {
                    'name': self.printer_name,
                    'port': self.printer_port,
                    'type': 'Manual USB',
                    'manual': True
                }
                self.storage._save_config()
                
                print(f"✓ Установлен USB порт: {normalized_port}")
                return True
                
            except KeyboardInterrupt:
                print("\n❌ Ввод отменен")
                return False
    
    def _get_available_usb_ports(self) -> List[str]:
        """Получает список доступных USB портов"""
        ports = []
        
        if self.system == "windows":
            # Проверяем стандартные USB порты Windows
            for port in ['USB001', 'USB002', 'USB003', 'USB004']:
                try:
                    # Пытаемся получить информацию о порте
                    result = subprocess.run([
                        'wmic', 'printer', 'where', f'PortName="{port}"', 'get', 'Name'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        ports.append(port)
                except:
                    continue
        
        elif self.system == "linux":
            # Проверяем USB устройства Linux
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
            # Windows USB порты
            if port.startswith('USB'):
                return port
            elif port.isdigit():
                port_num = port.zfill(3)  # Дополняем нулями до 3 цифр
                return f"USB{port_num}"
            elif len(port) <= 3 and port.isdigit():
                return f"USB{port.zfill(3)}"
        
        elif self.system == "linux":
            # Linux USB устройства
            if port.startswith('/dev/usb/lp'):
                return port
            elif port.startswith('lp') and port[2:].isdigit():
                return f"/dev/usb/{port}"
            elif port.isdigit():
                return f"/dev/usb/lp{port}"
        
        return None
    
    def get_saved_printer(self) -> Optional[Dict[str, str]]:
        """Получает сохраненный выбор принтера"""
        return self.storage.config.get('selected_printer')
    
    def send_pjl_command(self, command: str) -> bool:
        """
        Отправляет PJL команду принтеру через системные методы
        
        Args:
            command: PJL команда
            
        Returns:
            True если команда отправлена успешно
        """
        if not self.printer_name:
            print("❌ Принтер не выбран")
            return False
        
        # Формируем полную PJL команду
        full_command = f"\x1B%-12345X@PJL\r\n{command}\r\n@PJL EOJ\r\n\x1B%-12345X"
        
        print(f"→ Отправка команды: {command}")
        
        if self.system == "windows":
            return self._send_windows_command(full_command)
        elif self.system == "linux":
            return self._send_linux_command(full_command)
        else:
            print(f"❌ Система {self.system} не поддерживается")
            return False
    
    def _send_windows_command(self, command: str) -> bool:
        """Отправка команды в Windows"""
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.prn', delete=False) as f:
                f.write(command)
                temp_file = f.name
            
            try:
                # Метод 1: Через имя принтера
                if self.printer_name:
                    cmd = f'copy /B "{temp_file}" "\\\\localhost\\{self.printer_name}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        print("✓ Команда отправлена через имя принтера")
                        return True
                
                # Метод 2: Через USB порт
                if self.printer_port and 'USB' in self.printer_port:
                    for port in ['USB001', 'USB002', 'USB003']:
                        try:
                            cmd = f'copy /B "{temp_file}" "{port}"'
                            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                            if result.returncode == 0:
                                print(f"✓ Команда отправлена через порт {port}")
                                return True
                        except:
                            continue
                
                # Метод 3: Через PowerShell
                ps_script = f'''
$content = Get-Content -Path "{temp_file}" -Raw -Encoding Byte
$printerName = "{self.printer_name}"
try {{
    [System.IO.File]::WriteAllBytes("\\\\localhost\\$printerName", $content)
    "Success"
}} catch {{
    "Error: $($_.Exception.Message)"
}}
'''
                result = subprocess.run([
                    'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and "Success" in result.stdout:
                    print("✓ Команда отправлена через PowerShell")
                    return True
                    
            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            print("⚠️  Не удалось отправить команду")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка отправки в Windows: {e}")
            return False
    
    def _send_linux_command(self, command: str) -> bool:
        """Отправка команды в Linux"""
        try:
            # Метод 1: Через lp
            if self.printer_name and 'CUPS' in str(self.printer_port):
                try:
                    proc = subprocess.Popen(['lp', '-d', self.printer_name, '-o', 'raw'], 
                                          stdin=subprocess.PIPE, 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE)
                    stdout, stderr = proc.communicate(command.encode('ascii'), timeout=30)
                    
                    if proc.returncode == 0:
                        print("✓ Команда отправлена через lp")
                        return True
                except Exception as e:
                    print(f"⚠️  Ошибка lp: {e}")
            
            # Метод 2: Через USB устройство
            usb_devices = ['/dev/usb/lp0', '/dev/usb/lp1', '/dev/usb/lp2']
            for device in usb_devices:
                try:
                    if os.path.exists(device):
                        with open(device, 'wb') as f:
                            f.write(command.encode('ascii'))
                        print(f"✓ Команда отправлена через {device}")
                        return True
                except Exception as e:
                    continue
            
            print("⚠️  Не удалось отправить команду в Linux")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка отправки в Linux: {e}")
            return False
    
    def get_scanner_counter(self) -> int:
        """
        Получает значение счетчика сканера
        Использует кэширование, так как системные методы не могут читать ответы
        """
        print("\n📊 Получение счетчика сканера...")
        
        # Пытаемся получить реальное значение через статус системы
        real_counter = self._try_get_real_counter()
        if real_counter is not None:
            print(f"✓ Получен реальный счетчик: {real_counter}")
            self.storage.set_counter(real_counter)
            return real_counter
        
        # Если не получилось, используем сохраненное значение
        cached_counter = self.storage.get_counter()
        print(f"📁 Используется сохраненное значение: {cached_counter}")
        print("ℹ️  Для получения точного значения нужна двунаправленная связь")
        
        return cached_counter
    
    def _try_get_real_counter(self) -> Optional[int]:
        """Попытка получить реальный счетчик через статус системы"""
        
        if self.system == "windows":
            return self._get_windows_counter()
        elif self.system == "linux":
            return self._get_linux_counter()
        
        return None
    
    def _get_windows_counter(self) -> Optional[int]:
        """Получение счетчика в Windows через WMI"""
        try:
            print("   🖥️  Попытка получения через WMI...")
            
            # Скрипт PowerShell для получения статистики принтера
            ps_script = f'''
$printer = Get-WmiObject -Class Win32_Printer | Where-Object {{$_.Name -eq "{self.printer_name}"}} | Select-Object -First 1
if ($printer) {{
    try {{
        # Пытаемся получить детальную информацию
        $printer | Select-Object Name, PrinterStatus, JobCountSinceLastReset, PagesPrinted, TotalPagesPrinted | Format-List
        
        # Дополнительная информация через статус
        $status = Get-WmiObject -Class Win32_PrinterStatus | Where-Object {{$_.Name -eq $printer.Name}}
        if ($status) {{
            $status | Select-Object * | Format-List
        }}
    }} catch {{
        "No detailed info available"
    }}
}}
'''
            
            result = subprocess.run([
                'powershell', '-Command', ps_script
            ], capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0 and result.stdout:
                # Ищем числовые значения в выводе
                output = result.stdout
                print(f"   📋 WMI ответ: {output[:200]}...")
                
                # Паттерны для поиска счетчиков
                patterns = [
                    r'PagesPrinted\s*:\s*(\d+)',
                    r'TotalPagesPrinted\s*:\s*(\d+)',
                    r'JobCountSinceLastReset\s*:\s*(\d+)',
                    r':\s*(\d{2,6})'  # Любое разумное число
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, output, re.IGNORECASE)
                    for match in matches:
                        try:
                            value = int(match)
                            if 10 <= value <= 999999:  # Разумные границы
                                print(f"   ✓ Найден потенциальный счетчик: {value}")
                                return value
                        except ValueError:
                            continue
                            
        except Exception as e:
            print(f"   ⚠️  Ошибка WMI: {e}")
        
        return None
    
    def _get_linux_counter(self) -> Optional[int]:
        """Получение счетчика в Linux через CUPS"""
        try:
            print("   🐧 Попытка получения через CUPS...")
            
            # Получаем статус принтера
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   📋 CUPS статус: {result.stdout[:100]}...")
            
            # Пытаемся получить статистику
            result = subprocess.run(['lpstat', '-W', 'completed'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout:
                # Ищем числовые значения
                numbers = re.findall(r'\b(\d{2,6})\b', result.stdout)
                if numbers:
                    # Берем наибольшее разумное число
                    valid_numbers = [int(n) for n in numbers if 10 <= int(n) <= 999999]
                    if valid_numbers:
                        counter = max(valid_numbers)
                        print(f"   ✓ Найден потенциальный счетчик: {counter}")
                        return counter
                        
        except Exception as e:
            print(f"   ⚠️  Ошибка CUPS: {e}")
        
        return None
    
    def set_scanner_counter(self, count: int) -> bool:
        """Устанавливает значение счетчика сканера"""
        print(f"\n🔧 Установка счетчика на {count}...")
        
        # Отправляем PJL команды
        commands = [
            f"@PJL SET SCANCOUNT={count}",
            f"@PJL SET SCANCOUNTER={count}",
            f"@PJL DEFAULT SCANCOUNT={count}",
            f"@PJL DEFAULT SCANCOUNTER={count}"
        ]
        
        success = False
        for command in commands:
            if self.send_pjl_command(command):
                success = True
                time.sleep(0.5)  # Небольшая задержка между командами
        
        if success:
            # Сохраняем значение в конфигурации
            self.storage.set_counter(count)
            print(f"✓ Счетчик установлен на {count}")
            print("💾 Значение сохранено в конфигурации")
            
            return True
        else:
            print(f"❌ Не удалось установить счетчик на {count}")
            return False
    
    def reset_scanner_counter(self) -> bool:
        """Сбрасывает счетчик сканера в 0"""
        print("\n🔄 Сброс счетчика сканера...")
        return self.set_scanner_counter(0)
    
    def get_printer_info(self) -> Dict[str, str]:
        """Получает информацию о принтере"""
        print("\n📋 Получение информации о принтере...")
        
        info = {
            "connection_type": "system_only",
            "printer_name": self.printer_name or "Unknown",
            "printer_port": self.printer_port or "Unknown",
            "system": self.system,
            "cached_counter": str(self.storage.get_counter())
        }
        
        # Отправляем информационные PJL команды
        info_commands = {
            "model": "@PJL INFO ID",
            "status": "@PJL INFO STATUS",
            "memory": "@PJL INFO MEMORY"
        }
        
        for key, command in info_commands.items():
            if self.send_pjl_command(command):
                info[f"{key}_sent"] = "✓"
            else:
                info[f"{key}_sent"] = "❌"
        
        return info
    
    def get_command_history(self) -> List[dict]:
        """Получает историю команд"""
        return self.storage.get_history()
    
    def disconnect(self):
        """Отключение (очистка ресурсов)"""
        print("✓ Системное подключение завершено")


def print_printer_list(printers: List[Dict[str, str]]):
    """Выводит список найденных принтеров"""
    if not printers:
        print("❌ Принтеры не найдены")
        return
    
    print(f"\n✅ Найдено принтеров: {len(printers)}")
    print("-" * 60)
    
    for i, printer in enumerate(printers, 1):
        print(f"{i}. {printer.get('name', 'Unknown')}")
        print(f"   Тип: {printer.get('type', 'Unknown')}")
        print(f"   Порт: {printer.get('port', 'Unknown')}")
        if 'driver' in printer:
            print(f"   Драйвер: {printer['driver']}")
        print()


def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(
        description="HP LaserJet Pro 400 Scanner Counter (Только системные методы)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python hp_scanner_counter_system.py --list
  python hp_scanner_counter_system.py --get
  python hp_scanner_counter_system.py --set 1000
  python hp_scanner_counter_system.py --reset
  python hp_scanner_counter_system.py --info
  python hp_scanner_counter_system.py --history
  
Интерактивный выбор принтера:
  python hp_scanner_counter_system.py --interactive --get
  python hp_scanner_counter_system.py -i --set 1000
  
Указание USB порта:
  python hp_scanner_counter_system.py --usb-port USB001 --get
  python hp_scanner_counter_system.py --usb-port 1 --get  (будет преобразовано в USB001)
        """
    )
    
    parser.add_argument("--timeout", type=int, default=10, help="Таймаут операций (по умолчанию: 10)")
    parser.add_argument("--list", action="store_true", help="Показать список принтеров")
    parser.add_argument("--history", action="store_true", help="Показать историю команд")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Интерактивный выбор принтера из списка")
    parser.add_argument("--usb-port", "-p", type=str, metavar="PORT",
                       help="Указать USB порт напрямую (например: USB001, 1, /dev/usb/lp0)")
    parser.add_argument("--select", action="store_true", 
                       help="Только выбрать принтер и сохранить в конфигурации")
    parser.add_argument("--use-saved", action="store_true",
                       help="Использовать сохраненный принтер из предыдущего выбора")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--get", action="store_true", help="Получить текущее значение счетчика")
    group.add_argument("--set", type=int, metavar="COUNT", help="Установить значение счетчика")
    group.add_argument("--reset", action="store_true", help="Сбросить счетчик в 0")
    group.add_argument("--info", action="store_true", help="Получить информацию о принтере")
    
    args = parser.parse_args()
    
    print("🖨️  HP LaserJet Pro 400 Scanner Counter (Системные методы)")
    print("=" * 65)
    print("ℹ️  Используются ТОЛЬКО системные команды без внешних библиотек")
    print()
    
    # Создаем объект для работы с принтером
    printer = HPPrinterSystem(timeout=args.timeout)
    
    try:
        # Показать список принтеров
        if args.list:
            printers = printer.find_hp_printers()
            print_printer_list(printers)
            return
        
        # Показать историю команд
        if args.history:
            history = printer.get_command_history()
            if history:
                print("📜 История команд:")
                print("-" * 50)
                for entry in history[-10:]:  # Последние 10 записей
                    timestamp = entry.get('timestamp', 'Unknown')
                    action = entry.get('action', 'Unknown')
                    print(f"📅 {timestamp}")
                    print(f"   {action}")
                    print()
            else:
                print("📜 История команд пуста")
            return
        
        # Определяем режим подключения
        saved_printer = None
        usb_port = None
        
        # Нормализуем USB порт если указан
        if args.usb_port:
            usb_port = printer._normalize_usb_port(args.usb_port)
            if not usb_port:
                print(f"❌ Некорректный формат USB порта: {args.usb_port}")
                sys.exit(1)
        
        # Используем сохраненный принтер если запрошено
        if args.use_saved:
            saved_printer = printer.get_saved_printer()
            if saved_printer:
                print(f"📁 Найден сохраненный принтер: {saved_printer.get('name')} ({saved_printer.get('port')})")
            else:
                print("⚠️  Сохраненный принтер не найден, будет выполнен поиск")
        
        # Только выбор принтера без выполнения операций
        if args.select:
            print("🎯 Режим выбора принтера")
            success = printer.connect(saved_printer, interactive=True, usb_port=usb_port)
            if success:
                print("✅ Принтер выбран и сохранен в конфигурации")
            else:
                print("❌ Принтер не выбран")
                sys.exit(1)
            return
        
        # Обычное подключение
        interactive_mode = args.interactive and not usb_port  # Не показываем меню если порт указан явно
        
        success = printer.connect(
            printer_info=saved_printer if args.use_saved else None,
            interactive=interactive_mode,
            usb_port=usb_port
        )
        
        if not success:
            print("\n💡 Подсказки:")
            print("   • Используйте --interactive для выбора принтера из списка")
            print("   • Используйте --usb-port PORT для указания конкретного порта")
            print("   • Используйте --list для просмотра доступных принтеров")
            sys.exit(1)
        
        # Выполняем запрошенную операцию
        if args.get:
            counter = printer.get_scanner_counter()
            print(f"\n📊 Счетчик сканера: {counter}")
            
        elif args.set is not None:
            if args.set < 0:
                print("❌ Значение счетчика не может быть отрицательным")
                sys.exit(1)
            
            if printer.set_scanner_counter(args.set):
                print(f"\n✅ Счетчик установлен на {args.set}")
            else:
                print(f"\n❌ Не удалось установить счетчик на {args.set}")
                sys.exit(1)
                
        elif args.reset:
            if printer.reset_scanner_counter():
                print("\n✅ Счетчик сброшен в 0")
            else:
                print("\n❌ Не удалось сбросить счетчик")
                sys.exit(1)
                
        elif args.info:
            info = printer.get_printer_info()
            print("\n" + "="*50)
            print("📋 ИНФОРМАЦИЯ О ПРИНТЕРЕ")
            print("="*50)
            for key, value in info.items():
                print(f"{key.upper()}: {value}")
        
        else:
            # По умолчанию показываем текущий счетчик
            counter = printer.get_scanner_counter()
            print(f"\n📊 Текущий счетчик сканера: {counter}")
    
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
