#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование USB подключения к принтеру HP LaserJet Pro 400
Диагностический скрипт для проверки USB соединения и PJL команд
"""

import sys
import platform
import subprocess
from typing import List, Dict

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False


def test_system_info():
    """Выводит информацию о системе"""
    print("🖥️  Информация о системе:")
    print(f"   ОС: {platform.system()} {platform.release()}")
    print(f"   Python: {platform.python_version()}")
    print(f"   Архитектура: {platform.machine()}")
    print(f"   PyUSB доступен: {'✅ Да' if USB_AVAILABLE else '❌ Нет'}")
    print()


def test_usb_devices() -> List[Dict]:
    """Тестирует поиск USB устройств"""
    print("🔍 Поиск USB устройств...")
    devices = []
    
    if not USB_AVAILABLE:
        print("   ⚠️  PyUSB недоступен, используются системные методы")
        return test_system_usb()
    
    try:
        # HP Vendor ID
        HP_VENDOR_ID = 0x03f0
        
        print(f"   🔎 Поиск устройств HP (Vendor ID: 0x{HP_VENDOR_ID:04x})")
        
        # Поиск всех USB устройств
        all_devices = list(usb.core.find(find_all=True))
        print(f"   📊 Всего USB устройств: {len(all_devices)}")
        
        # Поиск HP устройств
        hp_devices = list(usb.core.find(find_all=True, idVendor=HP_VENDOR_ID))
        print(f"   📊 HP устройств: {len(hp_devices)}")
        
        for device in hp_devices:
            try:
                device_info = {
                    'vendor_id': device.idVendor,
                    'product_id': device.idProduct,
                    'bus': device.bus,
                    'address': device.address
                }
                
                try:
                    device_info['manufacturer'] = usb.util.get_string(device, device.iManufacturer) if device.iManufacturer else "Unknown"
                    device_info['product'] = usb.util.get_string(device, device.iProduct) if device.iProduct else "Unknown"
                except:
                    device_info['manufacturer'] = "Unknown"
                    device_info['product'] = "Unknown"
                
                # Проверяем интерфейсы
                device_info['interfaces'] = []
                try:
                    for cfg in device:
                        for intf in cfg:
                            device_info['interfaces'].append({
                                'class': intf.bInterfaceClass,
                                'subclass': intf.bInterfaceSubClass,
                                'protocol': intf.bInterfaceProtocol,
                                'is_printer': intf.bInterfaceClass == 7
                            })
                except:
                    pass
                
                devices.append(device_info)
                
            except Exception as e:
                print(f"   ⚠️  Ошибка получения информации об устройстве: {e}")
                continue
        
        return devices
        
    except Exception as e:
        print(f"   ❌ Ошибка поиска USB устройств: {e}")
        return []


def test_system_usb() -> List[Dict]:
    """Тестирует поиск принтеров через системные команды"""
    devices = []
    system = platform.system().lower()
    
    try:
        if system == "windows":
            print("   🖥️  Поиск принтеров в Windows...")
            
            # Поиск USB принтеров через wmic
            result = subprocess.run([
                'wmic', 'printer', 'where', 'PortName like "USB%"', 
                'get', 'Name,PortName,DriverName'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                for line in lines:
                    if line.strip() and ('HP' in line.upper() or 'HEWLETT' in line.upper()):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            devices.append({
                                'name': ' '.join(parts[:-2]) if len(parts) > 2 else parts[0],
                                'port': parts[-2] if len(parts) > 1 else 'USB',
                                'driver': parts[-1] if len(parts) > 2 else 'Unknown',
                                'system_method': True
                            })
            
            # Дополнительно ищем через USB порты
            print("   🔌 Проверка USB портов...")
            for port in ['USB001', 'USB002', 'USB003']:
                try:
                    result = subprocess.run([
                        'wmic', 'printer', 'where', f'PortName="{port}"', 'get', 'Name'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')[1:]
                        for line in lines:
                            if line.strip():
                                print(f"      ✓ Найден принтер на {port}: {line.strip()}")
                except:
                    continue
                    
        elif system == "linux":
            print("   🐧 Поиск принтеров в Linux...")
            
            # Поиск через lsusb
            try:
                result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'hewlett-packard' in line.lower() or 'hp' in line.lower():
                            devices.append({
                                'name': line.strip(),
                                'port': 'USB',
                                'system_method': True
                            })
            except:
                pass
            
            # Проверка устройств /dev/usb/lp*
            print("   📁 Проверка /dev/usb/lp* устройств...")
            import os
            for i in range(4):
                device_path = f'/dev/usb/lp{i}'
                if os.path.exists(device_path):
                    stat = os.stat(device_path)
                    print(f"      ✓ {device_path} существует (права: {oct(stat.st_mode)[-3:]})")
                else:
                    print(f"      ❌ {device_path} не найден")
            
            # Проверка cups принтеров
            try:
                result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("   🖨️  CUPS принтеры:")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            print(f"      📄 {line.strip()}")
            except:
                print("   ⚠️  CUPS недоступен")
                
    except Exception as e:
        print(f"   ❌ Ошибка системного поиска: {e}")
    
    return devices


def print_device_details(devices: List[Dict]):
    """Выводит подробную информацию об устройствах"""
    if not devices:
        print("❌ HP принтеры не найдены")
        return
    
    print(f"✅ Найдено HP устройств: {len(devices)}")
    print("-" * 60)
    
    for i, device in enumerate(devices, 1):
        print(f"\n{i}. Устройство:")
        
        if 'system_method' in device:
            print(f"   📄 Название: {device.get('name', 'Unknown')}")
            print(f"   🔌 Порт: {device.get('port', 'Unknown')}")
            if 'driver' in device:
                print(f"   💿 Драйвер: {device['driver']}")
            print("   🔧 Метод: Системные команды")
        else:
            print(f"   📄 Производитель: {device.get('manufacturer', 'Unknown')}")
            print(f"   📦 Продукт: {device.get('product', 'Unknown')}")
            print(f"   🔢 VID:PID: 0x{device['vendor_id']:04x}:0x{device['product_id']:04x}")
            print(f"   🚌 USB: Bus {device['bus']} Device {device['address']}")
            print("   🔧 Метод: Прямой USB доступ")
            
            if device.get('interfaces'):
                print("   🔌 Интерфейсы:")
                for intf in device['interfaces']:
                    class_name = "Принтер" if intf['is_printer'] else f"Класс {intf['class']}"
                    print(f"      • {class_name} (Класс: {intf['class']}, Подкласс: {intf['subclass']})")


def test_permissions():
    """Тестирует права доступа"""
    print("\n🔐 Проверка прав доступа...")
    
    system = platform.system().lower()
    
    if system == "windows":
        try:
            # Проверяем, запущен ли от администратора
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                print("   ✅ Запущено от имени администратора")
            else:
                print("   ⚠️  НЕ запущено от имени администратора")
                print("   💡 Для лучшей работы с USB запустите от администратора")
        except:
            print("   ❓ Не удалось определить права администратора")
            
    elif system == "linux":
        import os
        import grp
        
        user = os.getenv('USER', 'unknown')
        print(f"   👤 Пользователь: {user}")
        
        try:
            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            groups.append(grp.getgrgid(os.getgid()).gr_name)
            print(f"   👥 Группы: {', '.join(set(groups))}")
            
            if 'lp' in groups:
                print("   ✅ Пользователь в группе 'lp' - доступ к принтерам есть")
            else:
                print("   ⚠️  Пользователь НЕ в группе 'lp'")
                print("   💡 Выполните: sudo usermod -a -G lp $USER")
                
            if 'dialout' in groups:
                print("   ✅ Пользователь в группе 'dialout' - доступ к USB есть")
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки групп: {e}")


def test_dependencies():
    """Тестирует зависимости"""
    print("\n📦 Проверка зависимостей...")
    
    # Проверяем pyusb
    if USB_AVAILABLE:
        try:
            print(f"   ✅ PyUSB: {usb.__version__}")
        except:
            print("   ✅ PyUSB: установлен (версия неизвестна)")
    else:
        print("   ❌ PyUSB: не установлен")
        print("   💡 Установите: pip install pyusb")
    
    # Проверяем системные утилиты
    system = platform.system().lower()
    
    if system == "windows":
        utils = ['wmic']
    elif system == "linux":
        utils = ['lsusb', 'lpstat']
    else:
        utils = []
    
    for util in utils:
        try:
            result = subprocess.run([util, '--help'], 
                                  capture_output=True, timeout=5)
            print(f"   ✅ {util}: доступен")
        except:
            try:
                result = subprocess.run([util], capture_output=True, timeout=5)
                print(f"   ✅ {util}: доступен")
            except:
                print(f"   ❌ {util}: недоступен")


def main():
    """Главная функция тестирования"""
    print("🧪 HP LaserJet Pro 400 - Диагностика USB подключения")
    print("=" * 65)
    
    # Информация о системе
    test_system_info()
    
    # Проверка зависимостей
    test_dependencies()
    
    # Проверка прав доступа
    test_permissions()
    
    # Поиск USB устройств
    print("\n" + "=" * 65)
    devices = test_usb_devices()
    print_device_details(devices)
    
    # Рекомендации
    print("\n" + "=" * 65)
    print("💡 Рекомендации:")
    
    if not devices:
        print("   1. Убедитесь, что принтер включен")
        print("   2. Проверьте USB кабель")
        print("   3. Попробуйте другой USB порт")
        print("   4. Переустановите драйвер принтера")
        
        if not USB_AVAILABLE:
            print("   5. Установите pyusb: pip install pyusb")
            
    else:
        print(f"   ✅ Найдено {len(devices)} HP устройств")
        print("   💡 Можете использовать hp_scanner_counter_usb.py")
        
        if not USB_AVAILABLE:
            print("   📈 Для лучшей производительности установите pyusb")
    
    print("\n🎯 Следующие шаги:")
    print("   python hp_scanner_counter_usb.py --list")
    print("   python hp_scanner_counter_usb.py --get")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка диагностики: {e}")
        sys.exit(1)
