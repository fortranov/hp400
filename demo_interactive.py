#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация интерактивного выбора принтера и USB портов
Показывает новые возможности системной версии скрипта
"""

import sys
import time
import os

def print_header(title: str):
    """Выводит заголовок секции"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_command(description: str, command: str):
    """Выводит описание и команду"""
    print(f"\n💡 {description}")
    print(f"📝 Команда: {command}")
    print("-" * 40)

def run_demo_command(command: str, description: str = ""):
    """Запускает демонстрационную команду"""
    if description:
        print(f"\n🚀 {description}")
    
    print(f"▶️  Выполняется: {command}")
    print("-" * 50)
    
    # Запускаем команду
    os.system(command)
    
    input("\n⏸️  Нажмите Enter для продолжения...")

def main():
    """Основная функция демонстрации"""
    print("🎯 Демонстрация интерактивного выбора принтера")
    print("HP LaserJet Pro 400 Scanner Counter (Системная версия)")
    print("=" * 60)
    
    print("""
🆕 Новые возможности:
  ✅ Интерактивный выбор принтера из списка
  ✅ Указание USB порта вручную  
  ✅ Сохранение выбранного принтера
  ✅ Автоматическое обнаружение USB портов
  ✅ Нормализация ввода USB портов
    """)
    
    # Проверяем наличие скрипта
    if not os.path.exists("hp_scanner_counter_system.py"):
        print("❌ Файл hp_scanner_counter_system.py не найден!")
        print("   Убедитесь, что вы запускаете демо из правильной папки")
        sys.exit(1)
    
    print("🔍 Доступные команды для демонстрации:")
    
    demos = [
        {
            "title": "1. Просмотр списка принтеров",
            "command": "python hp_scanner_counter_system.py --list",
            "description": "Показывает все найденные HP принтеры в системе"
        },
        {
            "title": "2. Интерактивный выбор принтера",
            "command": "python hp_scanner_counter_system.py --select",
            "description": "Позволяет выбрать принтер из списка и сохранить выбор"
        },
        {
            "title": "3. Указание USB порта напрямую",
            "command": "python hp_scanner_counter_system.py --usb-port USB001 --info",
            "description": "Подключается к конкретному USB порту"
        },
        {
            "title": "4. Нормализация USB портов",
            "command": "python hp_scanner_counter_system.py --usb-port 1 --info",
            "description": "Автоматически преобразует '1' в 'USB001'"
        },
        {
            "title": "5. Использование сохраненного принтера",
            "command": "python hp_scanner_counter_system.py --use-saved --get",
            "description": "Использует принтер, выбранный ранее"
        },
        {
            "title": "6. Интерактивное получение счетчика",
            "command": "python hp_scanner_counter_system.py --interactive --get",
            "description": "Показывает меню выбора принтера и получает счетчик"
        },
        {
            "title": "7. Интерактивная установка счетчика",
            "command": "python hp_scanner_counter_system.py --interactive --set 1234",
            "description": "Выбор принтера и установка значения счетчика"
        }
    ]
    
    # Выводим список команд
    for i, demo in enumerate(demos, 1):
        print(f"\n{i}. {demo['title'][3:]}")
        print(f"   📝 {demo['command']}")
        print(f"   💡 {demo['description']}")
    
    print(f"\n8. Запустить все демо подряд")
    print(f"9. Показать справку по параметрам")
    print(f"0. Выход")
    
    while True:
        try:
            choice = input("\nВыберите демонстрацию (0-9): ").strip()
            
            if choice == "0":
                print("\n👋 Демонстрация завершена!")
                break
            elif choice == "8":
                # Запускаем все демо подряд
                print_header("ПОЛНАЯ ДЕМОНСТРАЦИЯ")
                for demo in demos:
                    run_demo_command(demo['command'], demo['title'])
                break
            elif choice == "9":
                # Показываем справку
                print_header("СПРАВКА ПО ПАРАМЕТРАМ")
                os.system("python hp_scanner_counter_system.py --help")
                input("\n⏸️  Нажмите Enter для продолжения...")
            elif choice.isdigit() and 1 <= int(choice) <= 7:
                # Запускаем конкретное демо
                demo = demos[int(choice) - 1]
                print_header(demo['title'])
                run_demo_command(demo['command'], demo['description'])
            else:
                print("❌ Некорректный выбор. Введите число от 0 до 9")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Демонстрация прервана пользователем")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
    
    print("\n📋 Дополнительная информация:")
    print("  • Конфигурация сохраняется в: printer_counter_config.json")
    print("  • История команд доступна через: --history")
    print("  • Интерактивный GUI: run_scanner_counter_system.bat")
    print("  • Документация: README_SYSTEM.md")

if __name__ == "__main__":
    main()
