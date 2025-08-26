#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования HP Scanner Counter Control Script
Демонстрирует различные сценарии работы со счетчиком сканера
"""

import sys
import time
from hp_scanner_counter import HPPrinterPJL


def demo_scanner_operations(printer_ip: str):
    """
    Демонстрация основных операций со счетчиком сканера
    
    Args:
        printer_ip: IP адрес принтера
    """
    print("🖨️  Демонстрация работы со счетчиком сканера HP LaserJet Pro 400")
    print("="*70)
    
    # Создаем объект для работы с принтером
    printer = HPPrinterPJL(printer_ip)
    
    try:
        # Подключаемся к принтеру
        if not printer.connect():
            print("❌ Не удалось подключиться к принтеру")
            return False
        
        print("\n1️⃣  Получение информации о принтере...")
        info = printer.get_printer_info()
        if info:
            print("✅ Информация получена:")
            for key, value in info.items():
                print(f"   📋 {key.upper()}: {value}")
        
        print("\n2️⃣  Получение текущего значения счетчика...")
        original_count = printer.get_scanner_counter()
        if original_count is not None:
            print(f"✅ Исходное значение счетчика: {original_count}")
        else:
            print("⚠️  Не удалось получить значение счетчика")
            return False
        
        print("\n3️⃣  Установка тестового значения счетчика...")
        test_value = 12345
        if printer.set_scanner_counter(test_value):
            print(f"✅ Счетчик установлен на {test_value}")
            
            # Проверяем установленное значение
            time.sleep(2)
            current_count = printer.get_scanner_counter()
            if current_count == test_value:
                print(f"✅ Проверка пройдена: счетчик = {current_count}")
            else:
                print(f"⚠️  Счетчик показывает {current_count}, ожидалось {test_value}")
        else:
            print(f"❌ Не удалось установить счетчик на {test_value}")
        
        print("\n4️⃣  Восстановление исходного значения...")
        if printer.set_scanner_counter(original_count):
            print(f"✅ Исходное значение восстановлено: {original_count}")
        else:
            print(f"⚠️  Не удалось восстановить исходное значение")
        
        print("\n5️⃣  Демонстрация сброса счетчика...")
        user_input = input("Хотите сбросить счетчик в 0? (y/n): ").lower().strip()
        if user_input == 'y':
            if printer.reset_scanner_counter():
                print("✅ Счетчик сброшен в 0")
                
                # Восстанавливаем исходное значение
                time.sleep(2)
                if printer.set_scanner_counter(original_count):
                    print(f"✅ Исходное значение восстановлено: {original_count}")
            else:
                print("❌ Не удалось сбросить счетчик")
        else:
            print("⏭️  Сброс счетчика пропущен")
        
        print("\n✅ Демонстрация завершена успешно!")
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Демонстрация прервана пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка во время демонстрации: {e}")
        return False
    finally:
        printer.disconnect()


def batch_operations_example(printer_ip: str, values: list):
    """
    Пример пакетных операций со счетчиком
    
    Args:
        printer_ip: IP адрес принтера
        values: Список значений для установки
    """
    print(f"\n🔄 Пакетная установка значений: {values}")
    print("-" * 50)
    
    printer = HPPrinterPJL(printer_ip)
    
    try:
        if not printer.connect():
            return False
        
        # Сохраняем исходное значение
        original_count = printer.get_scanner_counter()
        print(f"💾 Сохранено исходное значение: {original_count}")
        
        # Устанавливаем каждое значение из списка
        for i, value in enumerate(values, 1):
            print(f"\n📝 Операция {i}/{len(values)}: установка {value}")
            if printer.set_scanner_counter(value):
                print(f"   ✅ Установлено: {value}")
                time.sleep(1)
            else:
                print(f"   ❌ Ошибка установки: {value}")
        
        # Восстанавливаем исходное значение
        print(f"\n🔙 Восстановление исходного значения: {original_count}")
        printer.set_scanner_counter(original_count)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка пакетной операции: {e}")
        return False
    finally:
        printer.disconnect()


def main():
    """Главная функция примера"""
    if len(sys.argv) != 2:
        print("Использование: python example_usage.py <IP_принтера>")
        print("Пример: python example_usage.py 192.168.1.100")
        sys.exit(1)
    
    printer_ip = sys.argv[1]
    
    try:
        # Основная демонстрация
        print("🚀 Запуск демонстрации основных функций...")
        if demo_scanner_operations(printer_ip):
            
            # Пример пакетных операций
            print("\n" + "="*70)
            test_values = [100, 500, 1000, 2500]
            user_input = input(f"Хотите запустить пакетные операции с значениями {test_values}? (y/n): ").lower().strip()
            
            if user_input == 'y':
                batch_operations_example(printer_ip, test_values)
            else:
                print("⏭️  Пакетные операции пропущены")
        
        print(f"\n🎉 Все операции завершены!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Программа прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
