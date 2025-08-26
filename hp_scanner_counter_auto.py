#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HP LaserJet Pro 400 Scanner Counter Control (Universal Version)
Автоматически определяет тип подключения (USB или сеть) и использует соответствующий метод
"""

import argparse
import sys
import time
import socket
import subprocess
import platform
from typing import Optional, List, Dict, Union

# Импортируем классы из наших модулей
try:
    from hp_scanner_counter import HPPrinterPJL
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False

try:
    from hp_scanner_counter_usb import HPPrinterUSB
    USB_MODULE_AVAILABLE = True
except ImportError:
    USB_MODULE_AVAILABLE = False

try:
    import usb.core
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False


class HPPrinterAuto:
    """Универсальный класс для работы с принтером через любое подключение"""
    
    def __init__(self, ip_address: Optional[str] = None, timeout: int = 10):
        """
        Инициализация
        
        Args:
            ip_address: IP адрес для сетевого подключения (опционально)
            timeout: Таймаут операций
        """
        self.ip_address = ip_address
        self.timeout = timeout
        self.connection_type = None
        self.printer = None
        
    def detect_connection_type(self) -> str:
        """
        Автоматически определяет доступный тип подключения
        
        Returns:
            'network', 'usb' или 'none'
        """
        print("🔍 Автоматическое определение типа подключения...")
        
        # Сначала проверяем сетевое подключение, если указан IP
        if self.ip_address:
            if self._test_network_connection():
                print("✅ Обнаружено сетевое подключение")
                return 'network'
            else:
                print("❌ Сетевое подключение недоступно")
        
        # Проверяем USB подключение
        if self._test_usb_connection():
            print("✅ Обнаружено USB подключение")
            return 'usb'
        else:
            print("❌ USB подключение недоступно")
        
        print("❌ Принтер не найден")
        return 'none'
    
    def _test_network_connection(self) -> bool:
        """Тестирует сетевое подключение"""
        if not self.ip_address or not NETWORK_AVAILABLE:
            return False
            
        try:
            print(f"   🌐 Проверка сетевого подключения к {self.ip_address}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.ip_address, 9100))
            sock.close()
            return result == 0
        except:
            return False
    
    def _test_usb_connection(self) -> bool:
        """Тестирует USB подключение"""
        if not USB_MODULE_AVAILABLE:
            return False
            
        try:
            print("   🔌 Проверка USB подключения...")
            
            # Создаем временный объект для проверки
            usb_printer = HPPrinterUSB(timeout=3)
            printers = usb_printer.find_hp_printers()
            return len(printers) > 0
        except:
            return False
    
    def connect(self) -> bool:
        """
        Подключается к принтеру, автоматически определяя тип подключения
        
        Returns:
            True если подключение успешно
        """
        if not self.connection_type:
            self.connection_type = self.detect_connection_type()
        
        if self.connection_type == 'network':
            return self._connect_network()
        elif self.connection_type == 'usb':
            return self._connect_usb()
        else:
            print("❌ Не удалось найти доступное подключение к принтеру")
            return False
    
    def _connect_network(self) -> bool:
        """Подключение через сеть"""
        if not NETWORK_AVAILABLE:
            print("❌ Модуль сетевого подключения недоступен")
            return False
            
        print("🌐 Подключение через сеть...")
        self.printer = HPPrinterPJL(self.ip_address, timeout=self.timeout)
        return self.printer.connect()
    
    def _connect_usb(self) -> bool:
        """Подключение через USB"""
        if not USB_MODULE_AVAILABLE:
            print("❌ Модуль USB подключения недоступен")
            return False
            
        print("🔌 Подключение через USB...")
        self.printer = HPPrinterUSB(timeout=self.timeout)
        return self.printer.connect()
    
    def disconnect(self):
        """Отключение от принтера"""
        if self.printer:
            self.printer.disconnect()
            self.printer = None
    
    def get_scanner_counter(self) -> Optional[int]:
        """Получает текущее значение счетчика сканера"""
        if not self.printer:
            print("❌ Нет подключения к принтеру")
            return None
        return self.printer.get_scanner_counter()
    
    def set_scanner_counter(self, count: int) -> bool:
        """Устанавливает значение счетчика сканера"""
        if not self.printer:
            print("❌ Нет подключения к принтеру")
            return False
        return self.printer.set_scanner_counter(count)
    
    def reset_scanner_counter(self) -> bool:
        """Сбрасывает счетчик сканера в 0"""
        if not self.printer:
            print("❌ Нет подключения к принтеру")
            return False
        return self.printer.reset_scanner_counter()
    
    def get_printer_info(self) -> dict:
        """Получает информацию о принтере"""
        if not self.printer:
            print("❌ Нет подключения к принтеру")
            return {}
        return self.printer.get_printer_info()


def scan_for_printers() -> Dict[str, List]:
    """Сканирует все доступные принтеры"""
    result = {
        'network': [],
        'usb': []
    }
    
    print("🔍 Поиск всех доступных принтеров...")
    print("-" * 50)
    
    # Поиск сетевых принтеров (сканирование подсети)
    print("🌐 Поиск сетевых принтеров...")
    try:
        # Получаем локальную подсеть
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        subnet = '.'.join(local_ip.split('.')[:-1]) + '.'
        
        print(f"   📡 Сканирование подсети {subnet}0/24...")
        
        # Быстрое сканирование популярных IP адресов принтеров
        common_ips = [f"{subnet}{i}" for i in [100, 101, 102, 110, 150, 200, 250]]
        
        for ip in common_ips:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((ip, 9100)) == 0:
                    result['network'].append(ip)
                    print(f"   ✅ Найден сетевой принтер: {ip}")
                sock.close()
            except:
                continue
                
    except Exception as e:
        print(f"   ⚠️  Ошибка поиска сетевых принтеров: {e}")
    
    # Поиск USB принтеров
    print("\n🔌 Поиск USB принтеров...")
    if USB_MODULE_AVAILABLE:
        try:
            usb_printer = HPPrinterUSB()
            usb_devices = usb_printer.find_hp_printers()
            result['usb'] = usb_devices
            
            for device in usb_devices:
                name = device.get('product', device.get('name', 'Unknown'))
                print(f"   ✅ Найден USB принтер: {name}")
                
        except Exception as e:
            print(f"   ⚠️  Ошибка поиска USB принтеров: {e}")
    else:
        print("   ⚠️  Модуль USB недоступен")
    
    return result


def print_scan_results(results: Dict[str, List]):
    """Выводит результаты сканирования"""
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ")
    print("=" * 60)
    
    total_found = len(results['network']) + len(results['usb'])
    
    if total_found == 0:
        print("❌ Принтеры не найдены")
        print("\n💡 Рекомендации:")
        print("   • Убедитесь, что принтер включен")
        print("   • Проверьте подключение (USB кабель или сеть)")
        print("   • Для USB: запустите от администратора")
        print("   • Для сети: проверьте IP адрес принтера")
        return
    
    print(f"✅ Найдено принтеров: {total_found}")
    
    if results['network']:
        print(f"\n🌐 Сетевые принтеры ({len(results['network'])}):")
        for i, ip in enumerate(results['network'], 1):
            print(f"   {i}. {ip}")
    
    if results['usb']:
        print(f"\n🔌 USB принтеры ({len(results['usb'])}):")
        for i, device in enumerate(results['usb'], 1):
            name = device.get('product', device.get('name', 'Unknown'))
            print(f"   {i}. {name}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description="Универсальное управление счетчиком HP LaserJet Pro 400 (авто-определение подключения)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python hp_scanner_counter_auto.py --scan
  python hp_scanner_counter_auto.py --get
  python hp_scanner_counter_auto.py --get --ip 192.168.1.100
  python hp_scanner_counter_auto.py --set 1000
  python hp_scanner_counter_auto.py --reset
        """
    )
    
    parser.add_argument("--ip", help="IP адрес принтера (для принудительного сетевого подключения)")
    parser.add_argument("--timeout", type=int, default=10, help="Таймаут операций (по умолчанию: 10)")
    parser.add_argument("--scan", action="store_true", help="Сканировать все доступные принтеры")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--get", action="store_true", help="Получить текущее значение счетчика")
    group.add_argument("--set", type=int, metavar="COUNT", help="Установить значение счетчика")
    group.add_argument("--reset", action="store_true", help="Сбросить счетчик в 0")
    group.add_argument("--info", action="store_true", help="Получить информацию о принтере")
    
    args = parser.parse_args()
    
    print("🖨️  HP LaserJet Pro 400 Scanner Counter Control (Universal)")
    print("=" * 65)
    
    # Проверяем доступность модулей
    if not NETWORK_AVAILABLE and not USB_MODULE_AVAILABLE:
        print("❌ Ни один модуль подключения не доступен!")
        print("💡 Убедитесь, что файлы hp_scanner_counter.py и hp_scanner_counter_usb.py находятся в той же папке")
        sys.exit(1)
    
    # Показываем доступные методы
    methods = []
    if NETWORK_AVAILABLE:
        methods.append("Сеть")
    if USB_MODULE_AVAILABLE:
        methods.append("USB")
    
    print(f"📡 Доступные методы подключения: {', '.join(methods)}")
    if USB_AVAILABLE:
        print("🔌 PyUSB доступен - улучшенная поддержка USB")
    elif USB_MODULE_AVAILABLE:
        print("🔌 USB поддерживается через системные команды")
    
    print()
    
    # Сканирование принтеров
    if args.scan or not any([args.get, args.set is not None, args.reset, args.info]):
        results = scan_for_printers()
        print_scan_results(results)
        
        if args.scan:
            return
        
        # Если не нашли принтеров, завершаем
        total_found = len(results['network']) + len(results['usb'])
        if total_found == 0:
            sys.exit(1)
        
        # Если нашли только один тип, используем его
        if results['network'] and not results['usb'] and not args.ip:
            args.ip = results['network'][0]
            print(f"\n💡 Автоматически выбран сетевой принтер: {args.ip}")
    
    # Создаем универсальный принтер
    printer = HPPrinterAuto(args.ip, args.timeout)
    
    try:
        # Подключаемся
        if not printer.connect():
            sys.exit(1)
        
        # Выполняем операцию
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
            if info:
                print("\n" + "="*50)
                print("📋 ИНФОРМАЦИЯ О ПРИНТЕРЕ")
                print("="*50)
                print(f"🔗 Тип подключения: {printer.connection_type.upper()}")
                if printer.connection_type == 'network':
                    print(f"🌐 IP адрес: {printer.ip_address}")
                print()
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
