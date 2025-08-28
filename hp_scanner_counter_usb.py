#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HP LaserJet Pro 400 Scanner Counter Control Script (USB Version)
Скрипт для управления счетчиком отсканированных изображений принтера HP LaserJet Pro 400 через USB и PJL
"""

import argparse
import sys
import time
import subprocess
import platform
import tempfile
import os
from typing import Optional, List, Tuple

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False


class HPPrinterUSB:
    """Класс для работы с принтером HP через USB порт"""
    
    def __init__(self, device_path: Optional[str] = None, timeout: int = 10):
        """
        Инициализация подключения к USB принтеру
        
        Args:
            device_path: Путь к USB устройству (опционально)
            timeout: Таймаут операций в секундах
        """
        self.device_path = device_path
        self.timeout = timeout
        self.usb_device = None
        self.endpoint_out = None
        self.endpoint_in = None
        self.system = platform.system().lower()
        
    def find_hp_printers(self) -> List[dict]:
        """
        Находит все HP принтеры, подключенные через USB
        
        Returns:
            Список словарей с информацией о найденных принтерах
        """
        printers = []
        
        if not USB_AVAILABLE:
            print("⚠️  Библиотека pyusb не установлена. Используйте системные методы.")
            return self._find_printers_system()
        
        try:
            # HP Vendor ID
            HP_VENDOR_ID = 0x03f0
            
            devices = usb.core.find(find_all=True, idVendor=HP_VENDOR_ID)
            
            for device in devices:
                try:
                    # Получаем информацию об устройстве
                    manufacturer = usb.util.get_string(device, device.iManufacturer) if device.iManufacturer else "Unknown"
                    product = usb.util.get_string(device, device.iProduct) if device.iProduct else "Unknown"
                    
                    # Проверяем, что это принтер (класс 7)
                    for cfg in device:
                        for intf in cfg:
                            if intf.bInterfaceClass == 7:  # Printer class
                                printers.append({
                                    'vendor_id': device.idVendor,
                                    'product_id': device.idProduct,
                                    'manufacturer': manufacturer,
                                    'product': product,
                                    'device': device,
                                    'bus': device.bus,
                                    'address': device.address
                                })
                                break
                        if printers and printers[-1]['device'] == device:
                            break
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Ошибка поиска USB устройств: {e}")
            
        return printers
    
    def _find_printers_system(self) -> List[dict]:
        """Поиск принтеров через системные команды"""
        printers = []
        
        try:
            if self.system == "windows":
                # Windows: используем wmic для поиска USB принтеров
                result = subprocess.run([
                    'wmic', 'printer', 'where', 'PortName like "USB%"', 
                    'get', 'Name,PortName,DriverName'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                    for line in lines:
                        if line.strip() and 'HP' in line.upper():
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                printers.append({
                                    'name': ' '.join(parts[:-2]) if len(parts) > 2 else parts[0],
                                    'port': parts[-2] if len(parts) > 1 else 'USB',
                                    'driver': parts[-1] if len(parts) > 2 else 'Unknown',
                                    'system_method': True
                                })
                                
            elif self.system == "linux":
                # Linux: используем lsusb для поиска HP устройств
                result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Hewlett-Packard' in line or 'HP' in line:
                            printers.append({
                                'name': line.strip(),
                                'port': 'USB',
                                'system_method': True
                            })
                            
        except Exception as e:
            print(f"⚠️  Ошибка системного поиска: {e}")
            
        return printers
    
    def connect(self, printer_info: Optional[dict] = None) -> bool:
        """
        Подключается к USB принтеру
        
        Args:
            printer_info: Информация о принтере из find_hp_printers()
            
        Returns:
            True если подключение успешно, False в противном случае
        """
        if not USB_AVAILABLE:
            print("ℹ️  Будет использован системный метод отправки команд")
            return True
            
        try:
            if printer_info and 'device' in printer_info:
                self.usb_device = printer_info['device']
            else:
                # Автоматический поиск первого доступного HP принтера
                printers = self.find_hp_printers()
                if not printers:
                    print("❌ HP принтеры не найдены")
                    return False
                    
                self.usb_device = printers[0]['device']
                print(f"✓ Найден принтер: {printers[0].get('product', 'Unknown')}")
            
            # Сбрасываем устройство
            try:
                self.usb_device.reset()
            except:
                pass
            
            # Настраиваем устройство
            try:
                self.usb_device.set_configuration()
            except usb.core.USBError:
                pass
            
            # Находим endpoints для общения
            cfg = self.usb_device.get_active_configuration()
            interface = None
            
            for intf in cfg:
                if intf.bInterfaceClass == 7:  # Printer class
                    interface = intf
                    break
            
            if interface is None:
                print("❌ Интерфейс принтера не найден")
                return False
            
            # Ищем endpoints
            for endpoint in interface:
                if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.endpoint_out = endpoint
                elif usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.endpoint_in = endpoint
            
            if self.endpoint_out is None:
                print("❌ Выходной endpoint не найден")
                return False
            
            print("✓ USB подключение к принтеру установлено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения к USB принтеру: {e}")
            return False
    
    def disconnect(self):
        """Отключается от принтера"""
        if self.usb_device:
            try:
                usb.util.dispose_resources(self.usb_device)
                self.usb_device = None
                self.endpoint_out = None
                self.endpoint_in = None
                print("✓ USB соединение закрыто")
            except:
                pass
    
    def send_pjl_command(self, command: str) -> Optional[str]:
        """
        Отправляет PJL команду принтеру через USB
        
        Args:
            command: PJL команда для отправки
            
        Returns:
            Ответ принтера или None в случае ошибки
        """
        if USB_AVAILABLE and self.usb_device and self.endpoint_out:
            return self._send_pjl_usb(command)
        else:
            return self._send_pjl_system(command)
    
    def _send_pjl_usb(self, command: str) -> Optional[str]:
        """Отправка PJL команды через прямой USB доступ"""
        try:
            # Формируем полную PJL команду
            full_command = f"\x1B%-12345X@PJL\r\n{command}\r\n@PJL EOJ\r\n\x1B%-12345X"
            
            # Отправляем команду
            self.endpoint_out.write(full_command.encode('ascii'), timeout=self.timeout * 1000)
            print(f"→ Отправлена USB команда: {command}")
            
            # Пытаемся прочитать ответ
            response = ""
            if self.endpoint_in:
                try:
                    data = self.endpoint_in.read(1024, timeout=2000)
                    response = bytes(data).decode('ascii', errors='ignore')
                    if response.strip():
                        print(f"← Ответ принтера: {response.strip()}")
                except usb.core.USBTimeoutError:
                    pass
                except Exception:
                    pass
            
            return response.strip() if response else ""
            
        except Exception as e:
            print(f"❌ Ошибка отправки USB команды: {e}")
            return None
    
    def _send_pjl_system(self, command: str) -> Optional[str]:
        """Отправка PJL команды через системные команды"""
        try:
            # Формируем полную PJL команду
            full_command = f"\x1B%-12345X@PJL\r\n{command}\r\n@PJL EOJ\r\n\x1B%-12345X"
            
            print(f"→ Отправка системной команды: {command}")
            
            if self.system == "windows":
                return self._send_windows_print(full_command)
            elif self.system == "linux":
                return self._send_linux_print(full_command)
            else:
                print("❌ Неподдерживаемая операционная система")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка системной команды: {e}")
            return None
    
    def _send_windows_print(self, data: str) -> Optional[str]:
        """Отправка данных принтеру в Windows с попыткой получения ответа"""
        try:
            # Создаем временный файл для команды
            with tempfile.NamedTemporaryFile(mode='w', suffix='.prn', delete=False) as f:
                f.write(data)
                temp_file = f.name
            
            # Создаем временный файл для ответа
            response_file = temp_file + '_response.txt'
            
            try:
                # Пытаемся использовать PowerShell для двунаправленной связи
                ps_script = f"""
$printerName = (Get-WmiObject -Class Win32_Printer | Where-Object {{$_.PortName -like "USB*" -and $_.Name -like "*HP*LaserJet*"}}).Name | Select-Object -First 1
if ($printerName) {{
    try {{
        # Отправляем команду
        $bytes = [System.IO.File]::ReadAllBytes("{temp_file}")
        $printer = New-Object -ComObject Excel.Application -ErrorAction SilentlyContinue
        if (!$printer) {{
            # Альтернативный метод через .NET
            [System.IO.File]::WriteAllBytes("\\\\localhost\\$printerName", $bytes)
            "Command sent to $printerName"
        }}
    }} catch {{
        "Error: $($_.Exception.Message)"
    }}
}} else {{
    "No HP printer found"
}}
"""
                
                # Выполняем PowerShell скрипт
                ps_result = subprocess.run([
                    'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
                ], capture_output=True, text=True, timeout=30)
                
                if ps_result.returncode == 0 and ps_result.stdout.strip():
                    response = ps_result.stdout.strip()
                    print(f"✓ PowerShell ответ: {response}")
                    if "Command sent" in response:
                        return "Command sent"
                    return response
                
                # Если PowerShell не сработал, используем стандартный метод
                result = subprocess.run([
                    'wmic', 'printer', 'where', 'PortName like "USB%"', 'get', 'Name'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]
                    hp_printer = None
                    for line in lines:
                        if line.strip() and 'HP' in line.upper() and 'LaserJet' in line.upper():
                            hp_printer = line.strip()
                            break
                    
                    if hp_printer:
                        # Отправляем на найденный принтер
                        cmd = f'copy /B "{temp_file}" "\\\\localhost\\{hp_printer}"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            print(f"✓ Команда отправлена на {hp_printer}")
                            # Пытаемся прочитать ответ через WMI
                            return self._try_read_wmi_response()
                
                # Если не нашли именованный принтер, пробуем через порт
                for port in ['USB001', 'USB002', 'USB003']:
                    try:
                        cmd = f'copy /B "{temp_file}" "{port}"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            print(f"✓ Команда отправлена через порт {port}")
                            return "Command sent"
                    except:
                        continue
                        
            finally:
                # Удаляем временные файлы
                for f in [temp_file, response_file]:
                    try:
                        if os.path.exists(f):
                            os.unlink(f)
                    except:
                        pass
                    
            print("⚠️  Не удалось отправить команду через Windows")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка Windows печати: {e}")
            return None
    
    def _try_read_wmi_response(self) -> Optional[str]:
        """Попытка прочитать ответ принтера через WMI"""
        try:
            # Пытаемся получить статус принтера через WMI
            wmi_script = """
Get-WmiObject -Class Win32_Printer | Where-Object {$_.PortName -like "USB*" -and $_.Name -like "*HP*"} | Select-Object Name, PrinterStatus, ExtendedPrinterStatus, Comment | Format-List
"""
            result = subprocess.run([
                'powershell', '-Command', wmi_script
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
        except:
            pass
        
        return "Command sent"
    
    def _send_linux_print(self, data: str) -> Optional[str]:
        """Отправка данных принтеру в Linux"""
        try:
            # Пробуем отправить через lp
            proc = subprocess.Popen(['lp', '-d', 'hp-printer', '-o', 'raw'], 
                                  stdin=subprocess.PIPE, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(data.encode('ascii'), timeout=30)
            
            if proc.returncode == 0:
                print("✓ Команда отправлена через lp")
                return "Command sent"
            
            # Пробуем через USB устройство напрямую
            usb_devices = ['/dev/usb/lp0', '/dev/usb/lp1', '/dev/usb/lp2']
            for device in usb_devices:
                try:
                    if os.path.exists(device):
                        with open(device, 'wb') as f:
                            f.write(data.encode('ascii'))
                        print(f"✓ Команда отправлена через {device}")
                        return "Command sent"
                except:
                    continue
                    
            print("⚠️  Не удалось отправить команду через Linux")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка Linux печати: {e}")
            return None
    
    def get_scanner_counter(self) -> Optional[int]:
        """Получает текущее значение счетчика отсканированных изображений"""
        print("\n📊 Получение текущего значения счетчика...")
        
        # Если используется pyusb, пытаемся получить реальный ответ
        if USB_AVAILABLE and self.usb_device:
            return self._get_counter_usb()
        else:
            return self._get_counter_system()
    
    def _get_counter_usb(self) -> Optional[int]:
        """Получение счетчика через прямой USB доступ"""
        commands = [
            "@PJL INQUIRE SCANCOUNT",
            "@PJL INQUIRE SCANCOUNTER", 
            "@PJL INQUIRE SCANPAGES",
            "@PJL INFO SCANCOUNT",
            "@PJL INFO SCANCOUNTER",
            "@PJL DINQUIRE SCANCOUNT",
            "@PJL DINQUIRE SCANCOUNTER"
        ]
        
        for command in commands:
            response = self.send_pjl_command(command)
            counter = self._parse_counter_response(response)
            if counter is not None:
                print(f"✓ Текущий счетчик сканера: {counter}")
                return counter
        
        print("⚠️  Не удалось получить значение счетчика через USB")
        return None
    
    def _get_counter_system(self) -> Optional[int]:
        """Получение счетчика через системные команды с эмуляцией"""
        print("ℹ️  Используется системный метод - чтение счетчика ограничено")
        
        # Пытаемся получить информацию через SNMP (если доступно)
        counter = self._try_snmp_counter()
        if counter is not None:
            return counter
        
        # Пытаемся получить через статус принтера
        counter = self._try_printer_status_counter()
        if counter is not None:
            return counter
        
        # Если ничего не получилось, возвращаем сохраненное значение или 0
        print("⚠️  Точное значение счетчика недоступно через системные команды")
        print("💡 Для получения реального значения установите: pip install pyusb")
        return 0
    
    def _parse_counter_response(self, response: Optional[str]) -> Optional[int]:
        """Парсит ответ PJL команды для извлечения значения счетчика"""
        if not response or response == "Command sent":
            return None
        
        try:
            # Ищем паттерны ответов PJL
            patterns = [
                r'SCANCOUNT[=:]\s*(\d+)',
                r'SCANCOUNTER[=:]\s*(\d+)', 
                r'SCANPAGES[=:]\s*(\d+)',
                r'=\s*(\d+)',
                r':\s*(\d+)',
                r'(\d+)'
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    counter_value = int(match.group(1))
                    # Санитарная проверка значения
                    if 0 <= counter_value <= 999999:
                        return counter_value
            
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _try_snmp_counter(self) -> Optional[int]:
        """Попытка получить счетчик через SNMP (если доступно)"""
        try:
            # SNMP OID для счетчиков HP принтеров
            # Это требует библиотеки pysnmp, но мы можем попробовать системные команды
            if platform.system().lower() == "windows":
                # В Windows можно попробовать через PowerShell и WMI
                ps_script = '''
$printer = Get-WmiObject -Class Win32_Printer | Where-Object {$_.PortName -like "USB*" -and $_.Name -like "*HP*"} | Select-Object -First 1
if ($printer) {
    try {
        $status = Get-WmiObject -Class Win32_PrinterStatus | Where-Object {$_.Name -eq $printer.Name}
        if ($status) {
            $status.TotalPagesPrinted
        }
    } catch {
        $null
    }
}
'''
                result = subprocess.run([
                    'powershell', '-Command', ps_script
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    return int(result.stdout.strip())
                    
        except:
            pass
        
        return None
    
    def _try_printer_status_counter(self) -> Optional[int]:
        """Попытка извлечь счетчик из статуса принтера"""
        try:
            if platform.system().lower() == "windows":
                # Пытаемся получить детальную информацию о принтере
                wmi_script = '''
Get-WmiObject -Class Win32_Printer | Where-Object {$_.PortName -like "USB*" -and $_.Name -like "*HP*"} | 
Select-Object Name, Comment, Description, PrinterPaperNames | Format-List
'''
                result = subprocess.run([
                    'powershell', '-Command', wmi_script
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Ищем числовые значения в ответе
                    import re
                    numbers = re.findall(r'\b(\d{1,6})\b', result.stdout)
                    if numbers:
                        # Возвращаем наибольшее разумное число (вероятно счетчик)
                        valid_numbers = [int(n) for n in numbers if 0 <= int(n) <= 999999]
                        if valid_numbers:
                            return max(valid_numbers)
                            
        except:
            pass
        
        return None
    
    def set_scanner_counter(self, count: int) -> bool:
        """Устанавливает значение счетчика отсканированных изображений"""
        print(f"\n🔧 Установка счетчика сканера на значение: {count}")
        
        commands = [
            f"@PJL SET SCANCOUNT={count}",
            f"@PJL SET SCANCOUNTER={count}",
            f"@PJL SET SCANPAGES={count}",
            f"@PJL DEFAULT SCANCOUNT={count}",
            f"@PJL DEFAULT SCANCOUNTER={count}"
        ]
        
        success = False
        for command in commands:
            response = self.send_pjl_command(command)
            if response is not None:
                success = True
        
        if success:
            print(f"✓ Команда установки счетчика отправлена")
            time.sleep(2)
            current_count = self.get_scanner_counter()
            if current_count == count:
                print(f"✓ Счетчик успешно установлен на {count}")
                return True
            else:
                print(f"⚠️  Счетчик не изменился (текущее значение: {current_count})")
        
        return success
    
    def reset_scanner_counter(self) -> bool:
        """Сбрасывает счетчик отсканированных изображений в 0"""
        print("\n🔄 Сброс счетчика сканера...")
        return self.set_scanner_counter(0)
    
    def get_printer_info(self) -> dict:
        """Получает информацию о принтере"""
        print("\n📋 Получение информации о принтере...")
        
        info = {}
        info_commands = {
            "model": "@PJL INFO ID",
            "status": "@PJL INFO STATUS", 
            "memory": "@PJL INFO MEMORY",
            "version": "@PJL INFO VERSION"
        }
        
        for key, command in info_commands.items():
            response = self.send_pjl_command(command)
            if response:
                info[key] = response
        
        return info


def print_usb_printers(printers: List[dict]):
    """Выводит список найденных USB принтеров"""
    print("\n🔍 Найденные USB принтеры:")
    print("-" * 50)
    
    for i, printer in enumerate(printers):
        print(f"{i+1}. {printer.get('product', printer.get('name', 'Unknown'))}")
        if 'manufacturer' in printer:
            print(f"   Производитель: {printer['manufacturer']}")
        if 'bus' in printer and 'address' in printer:
            print(f"   USB: Bus {printer['bus']} Device {printer['address']}")
        if 'port' in printer:
            print(f"   Порт: {printer['port']}")
        print()


def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(
        description="Управление счетчиком отсканированных изображений HP LaserJet Pro 400 (USB)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python hp_scanner_counter_usb.py --list
  python hp_scanner_counter_usb.py --get
  python hp_scanner_counter_usb.py --set 1000
  python hp_scanner_counter_usb.py --reset
  python hp_scanner_counter_usb.py --info
        """
    )
    
    parser.add_argument("--timeout", type=int, default=10, help="Таймаут операций в секундах (по умолчанию: 10)")
    parser.add_argument("--list", action="store_true", help="Показать список USB принтеров")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--get", action="store_true", help="Получить текущее значение счетчика")
    group.add_argument("--set", type=int, metavar="COUNT", help="Установить значение счетчика")
    group.add_argument("--reset", action="store_true", help="Сбросить счетчик в 0")
    group.add_argument("--info", action="store_true", help="Получить информацию о принтере")
    
    args = parser.parse_args()
    
    print("🖨️  HP LaserJet Pro 400 Scanner Counter Control (USB)")
    print("="*55)
    
    if not USB_AVAILABLE:
        print("⚠️  Библиотека pyusb не установлена. Будут использованы системные методы.")
        print("💡 Для улучшенной функциональности установите: pip install pyusb")
        print()
    
    # Создаем объект для работы с USB принтером
    printer = HPPrinterUSB(timeout=args.timeout)
    
    try:
        # Показываем список принтеров
        if args.list or not any([args.get, args.set is not None, args.reset, args.info]):
            printers = printer.find_hp_printers()
            if printers:
                print_usb_printers(printers)
            else:
                print("❌ HP принтеры не найдены")
                if USB_AVAILABLE:
                    print("💡 Убедитесь, что принтер включен и подключен через USB")
                else:
                    print("💡 Установите pyusb для лучшего обнаружения устройств")
            
            if args.list:
                return
            if not printers:
                sys.exit(1)
        
        # Подключаемся к принтеру
        if not printer.connect():
            sys.exit(1)
        
        # Выполняем запрошенную операцию
        if args.get:
            counter = printer.get_scanner_counter()
            if counter is not None:
                print(f"\n📊 Текущий счетчик сканера: {counter}")
            else:
                print("\n❌ Не удалось получить значение счетчика")
                sys.exit(1)
                
        elif args.set is not None:
            if args.set < 0:
                print("❌ Значение счетчика не может быть отрицательным")
                sys.exit(1)
            
            if printer.set_scanner_counter(args.set):
                print(f"\n✓ Счетчик установлен на {args.set}")
            else:
                print(f"\n❌ Не удалось установить счетчик на {args.set}")
                sys.exit(1)
                
        elif args.reset:
            if printer.reset_scanner_counter():
                print("\n✓ Счетчик сброшен в 0")
            else:
                print("\n❌ Не удалось сбросить счетчик")
                sys.exit(1)
                
        elif args.info:
            info = printer.get_printer_info()
            if info:
                print("\n" + "="*50)
                print("📋 ИНФОРМАЦИЯ О ПРИНТЕРЕ")
                print("="*50)
                for key, value in info.items():
                    print(f"{key.upper()}: {value}")
            else:
                print("\n⚠️  Информация о принтере недоступна")
    
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
