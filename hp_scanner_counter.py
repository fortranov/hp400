#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HP LaserJet Pro 400 Scanner Counter Control Script
Скрипт для управления счетчиком отсканированных изображений принтера HP LaserJet Pro 400 через PJL
"""

import socket
import argparse
import sys
import time
from typing import Optional, Tuple


class HPPrinterPJL:
    """Класс для работы с принтером HP через протокол PJL"""
    
    def __init__(self, ip_address: str, port: int = 9100, timeout: int = 10):
        """
        Инициализация подключения к принтеру
        
        Args:
            ip_address: IP адрес принтера
            port: Порт подключения (по умолчанию 9100 для HP LaserJet)
            timeout: Таймаут подключения в секундах
        """
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.socket = None
    
    def connect(self) -> bool:
        """
        Устанавливает соединение с принтером
        
        Returns:
            True если соединение установлено успешно, False в противном случае
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.ip_address, self.port))
            print(f"✓ Соединение с принтером {self.ip_address}:{self.port} установлено")
            return True
        except socket.error as e:
            print(f"✗ Ошибка подключения к принтеру: {e}")
            return False
    
    def disconnect(self):
        """Закрывает соединение с принтером"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("✓ Соединение с принтером закрыто")
    
    def send_pjl_command(self, command: str) -> Optional[str]:
        """
        Отправляет PJL команду принтеру
        
        Args:
            command: PJL команда для отправки
            
        Returns:
            Ответ принтера или None в случае ошибки
        """
        if not self.socket:
            print("✗ Нет соединения с принтером")
            return None
        
        try:
            # Формируем полную PJL команду
            full_command = f"\x1B%-12345X@PJL\r\n{command}\r\n@PJL EOJ\r\n\x1B%-12345X"
            
            # Отправляем команду
            self.socket.send(full_command.encode('ascii'))
            print(f"→ Отправлена команда: {command}")
            
            # Ждем ответ
            time.sleep(1)
            response = ""
            try:
                while True:
                    data = self.socket.recv(1024).decode('ascii', errors='ignore')
                    if not data:
                        break
                    response += data
                    time.sleep(0.1)
            except socket.timeout:
                pass
            
            if response.strip():
                print(f"← Ответ принтера: {response.strip()}")
                return response.strip()
            
            return ""
            
        except socket.error as e:
            print(f"✗ Ошибка отправки команды: {e}")
            return None
    
    def get_scanner_counter(self) -> Optional[int]:
        """
        Получает текущее значение счетчика отсканированных изображений
        
        Returns:
            Текущее значение счетчика или None в случае ошибки
        """
        print("\n📊 Получение текущего значения счетчика...")
        
        # Различные варианты PJL команд для получения счетчика сканера
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
            if response and "=" in response:
                try:
                    # Извлекаем значение из ответа
                    value = response.split("=")[-1].strip()
                    counter_value = int(value)
                    print(f"✓ Текущий счетчик сканера: {counter_value}")
                    return counter_value
                except (ValueError, IndexError):
                    continue
        
        print("⚠ Не удалось получить значение счетчика сканера")
        return None
    
    def set_scanner_counter(self, count: int) -> bool:
        """
        Устанавливает значение счетчика отсканированных изображений
        
        Args:
            count: Новое значение счетчика
            
        Returns:
            True если команда выполнена успешно, False в противном случае
        """
        print(f"\n🔧 Установка счетчика сканера на значение: {count}")
        
        # Различные варианты PJL команд для установки счетчика сканера
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
            
            # Проверяем, установилось ли значение
            time.sleep(2)
            current_count = self.get_scanner_counter()
            if current_count == count:
                print(f"✓ Счетчик успешно установлен на {count}")
                return True
            else:
                print(f"⚠ Счетчик не изменился (текущее значение: {current_count})")
        
        return success
    
    def reset_scanner_counter(self) -> bool:
        """
        Сбрасывает счетчик отсканированных изображений в 0
        
        Returns:
            True если команда выполнена успешно, False в противном случае
        """
        print("\n🔄 Сброс счетчика сканера...")
        return self.set_scanner_counter(0)
    
    def get_printer_info(self) -> dict:
        """
        Получает основную информацию о принтере
        
        Returns:
            Словарь с информацией о принтере
        """
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


def print_printer_info(info: dict):
    """Выводит информацию о принтере в читаемом виде"""
    print("\n" + "="*50)
    print("📋 ИНФОРМАЦИЯ О ПРИНТЕРЕ")
    print("="*50)
    
    for key, value in info.items():
        print(f"{key.upper()}: {value}")


def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(
        description="Управление счетчиком отсканированных изображений HP LaserJet Pro 400",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python hp_scanner_counter.py 192.168.1.100 --get
  python hp_scanner_counter.py 192.168.1.100 --set 1000
  python hp_scanner_counter.py 192.168.1.100 --reset
  python hp_scanner_counter.py 192.168.1.100 --info
        """
    )
    
    parser.add_argument("ip", help="IP адрес принтера")
    parser.add_argument("--port", type=int, default=9100, help="Порт подключения (по умолчанию: 9100)")
    parser.add_argument("--timeout", type=int, default=10, help="Таймаут подключения в секундах (по умолчанию: 10)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--get", action="store_true", help="Получить текущее значение счетчика")
    group.add_argument("--set", type=int, metavar="COUNT", help="Установить значение счетчика")
    group.add_argument("--reset", action="store_true", help="Сбросить счетчик в 0")
    group.add_argument("--info", action="store_true", help="Получить информацию о принтере")
    
    args = parser.parse_args()
    
    print("🖨️  HP LaserJet Pro 400 Scanner Counter Control")
    print("="*50)
    
    # Создаем объект для работы с принтером
    printer = HPPrinterPJL(args.ip, args.port, args.timeout)
    
    try:
        # Подключаемся к принтеру
        if not printer.connect():
            sys.exit(1)
        
        # Выполняем запрошенную операцию
        if args.get:
            counter = printer.get_scanner_counter()
            if counter is not None:
                print(f"\n📊 Текущий счетчик сканера: {counter}")
            else:
                print("\n✗ Не удалось получить значение счетчика")
                sys.exit(1)
                
        elif args.set is not None:
            if args.set < 0:
                print("✗ Значение счетчика не может быть отрицательным")
                sys.exit(1)
            
            if printer.set_scanner_counter(args.set):
                print(f"\n✓ Счетчик установлен на {args.set}")
            else:
                print(f"\n✗ Не удалось установить счетчик на {args.set}")
                sys.exit(1)
                
        elif args.reset:
            if printer.reset_scanner_counter():
                print("\n✓ Счетчик сброшен в 0")
            else:
                print("\n✗ Не удалось сбросить счетчик")
                sys.exit(1)
                
        elif args.info:
            info = printer.get_printer_info()
            print_printer_info(info)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        sys.exit(1)
    finally:
        printer.disconnect()


if __name__ == "__main__":
    main()
