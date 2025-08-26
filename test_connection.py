#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрая проверка подключения к принтеру HP LaserJet Pro 400
Простой скрипт для тестирования сетевого соединения и базовых PJL команд
"""

import socket
import sys
import time


def test_printer_connection(ip_address: str, port: int = 9100, timeout: int = 5):
    """
    Тестирует подключение к принтеру и отправляет базовые PJL команды
    
    Args:
        ip_address: IP адрес принтера
        port: Порт подключения
        timeout: Таймаут подключения
    
    Returns:
        True если тест прошел успешно, False в противном случае
    """
    print(f"🔍 Тестирование подключения к {ip_address}:{port}")
    print("-" * 50)
    
    try:
        # Тест 1: Проверка TCP подключения
        print("1️⃣  Проверка TCP подключения...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((ip_address, port))
        if result == 0:
            print("   ✅ TCP подключение установлено")
        else:
            print("   ❌ TCP подключение не удалось")
            sock.close()
            return False
        
        # Тест 2: Отправка PJL команды INFO ID
        print("2️⃣  Отправка PJL команды INFO ID...")
        pjl_command = "\x1B%-12345X@PJL\r\n@PJL INFO ID\r\n@PJL EOJ\r\n\x1B%-12345X"
        
        sock.send(pjl_command.encode('ascii'))
        print("   📤 Команда отправлена")
        
        # Ожидаем ответ
        time.sleep(2)
        response = ""
        try:
            while True:
                data = sock.recv(1024).decode('ascii', errors='ignore')
                if not data:
                    break
                response += data
                time.sleep(0.1)
        except socket.timeout:
            pass
        
        if response.strip():
            print("   ✅ Получен ответ от принтера:")
            print(f"      📋 {response.strip()}")
        else:
            print("   ⚠️  Ответ от принтера не получен (возможно, нормально)")
        
        # Тест 3: Проверка поддержки команд счетчика
        print("3️⃣  Проверка команд счетчика...")
        counter_commands = [
            "@PJL INQUIRE SCANCOUNT",
            "@PJL INFO SCANCOUNT"
        ]
        
        counter_found = False
        for cmd in counter_commands:
            full_cmd = f"\x1B%-12345X@PJL\r\n{cmd}\r\n@PJL EOJ\r\n\x1B%-12345X"
            sock.send(full_cmd.encode('ascii'))
            time.sleep(1)
            
            try:
                response = sock.recv(1024).decode('ascii', errors='ignore')
                if response and "=" in response:
                    print(f"   ✅ Команда {cmd} поддерживается")
                    print(f"      📊 Ответ: {response.strip()}")
                    counter_found = True
                    break
            except:
                continue
        
        if not counter_found:
            print("   ⚠️  Команды счетчика не отвечают (может потребоваться другой подход)")
        
        sock.close()
        print("\n✅ Тест подключения завершен успешно")
        return True
        
    except socket.timeout:
        print(f"   ❌ Таймаут подключения ({timeout}s)")
        return False
    except socket.error as e:
        print(f"   ❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False


def main():
    """Главная функция"""
    print("🖨️  HP LaserJet Pro 400 - Тест подключения")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Использование: python test_connection.py <IP_принтера> [порт] [таймаут]")
        print("Примеры:")
        print("  python test_connection.py 192.168.1.100")
        print("  python test_connection.py 192.168.1.100 9100")
        print("  python test_connection.py 192.168.1.100 9100 10")
        sys.exit(1)
    
    ip_address = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9100
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    try:
        success = test_printer_connection(ip_address, port, timeout)
        
        if success:
            print(f"\n🎉 Принтер {ip_address} готов к работе!")
            print("💡 Можете использовать основной скрипт hp_scanner_counter.py")
        else:
            print(f"\n❌ Проблемы с подключением к {ip_address}")
            print("🔧 Рекомендации:")
            print("   • Проверьте IP адрес принтера")
            print("   • Убедитесь, что принтер включен и в сети")
            print("   • Проверьте настройки файрвола")
            print("   • Попробуйте другой порт (например, 9101 или 9102)")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
