# HP LaserJet Pro 400 MFP M425 PCL Scanner Counter

**Специализированная версия для HP LaserJet Pro 400 MFP M425 PCL**

## 🎯 Особенности для M425 MFP

### ✨ **Оптимизировано для многофункционального устройства:**
- 📊 **Специфичные PJL команды** для M425 MFP
- 🔍 **Улучшенное обнаружение** M425 в системе
- ⚙️ **Поддержка MFP функций**: сканер, копир, принтер, факс
- 💾 **Отдельная конфигурация** `m425_counter_config.json`
- ⏱️ **Увеличенные таймауты** для MFP операций

## 📁 Основной файл

**`hp_m425_scanner_counter.py`** - специализированный скрипт для M425

## 🚀 Использование

### Базовые команды
```bash
# Поиск M425 принтеров
python hp_m425_scanner_counter.py --list

# Получить счетчик сканера M425
python hp_m425_scanner_counter.py --get

# Установить счетчик сканера M425
python hp_m425_scanner_counter.py --set 1000

# Сбросить счетчик сканера M425
python hp_m425_scanner_counter.py --reset

# Информация о M425 MFP
python hp_m425_scanner_counter.py --info
```

### Интерактивный режим
```bash
# Выбрать M425 принтер интерактивно
python hp_m425_scanner_counter.py --select

# Интерактивная работа с M425
python hp_m425_scanner_counter.py --interactive --get
python hp_m425_scanner_counter.py -i --set 1500
```

### USB подключение для M425
```bash
# Прямое указание USB порта
python hp_m425_scanner_counter.py --usb-port USB001 --get
python hp_m425_scanner_counter.py -p 1 --set 2000

# Автоматическая нормализация для M425
# 1 → USB001, 2 → USB002, и т.д.
```

### GUI для Windows
```bash
# Специальный интерфейс для M425
run_m425_scanner_counter.bat
```

## 🔧 Специфичные команды для M425

### PJL команды сканера M425:
```
@PJL INQUIRE SCANCOUNTER          # Получить счетчик
@PJL INQUIRE MFPSCANCOUNT         # MFP-специфичный счетчик
@PJL SET SCANCOUNTER=<значение>   # Установить счетчик
@PJL SET MFPSCANCOUNT=<значение>  # MFP установка
@PJL DEFAULT SCANCOUNTER=<значение> # По умолчанию
@PJL USTATUS DEVICE               # Статус устройства MFP
@PJL INFO SCANSTATUS              # Статус сканера
```

### Дополнительные MFP команды:
```
@PJL COMMENT M425 MFP SCANNER COMMAND  # Комментарий для M425
@PJL INFO ID                           # Идентификация устройства
@PJL INFO STATUS                       # Общий статус
@PJL INFO MEMORY                       # Память устройства
```

## 🔍 Обнаружение M425 в системе

### Windows (расширенный поиск):
```powershell
# Поиск по имени M425
wmic printer where "Name like '%M425%' or Name like '%400 MFP%'"

# Поиск по драйверу M425
wmic printer where "DriverName like '%M425%'"

# Поиск через WMI с фильтрацией MFP
Get-WmiObject -Class Win32_Printer | Where-Object {$_.Name -like "*M425*"}
```

### Linux (CUPS и USB):
```bash
# Поиск M425 в CUPS
lpstat -p | grep -i "m425\|400.*mfp"

# Поиск M425 через USB
lsusb | grep -i "hewlett.*m425\|hp.*m425"
```

## 📊 Конфигурация M425

Файл `m425_counter_config.json`:
```json
{
  "scanner_counter": 1234,
  "last_updated": "2024-01-01T12:00:00",
  "printer_model": "HP LaserJet Pro 400 MFP M425",
  "selected_printer": {
    "name": "HP LaserJet Pro 400 MFP M425dn",
    "port": "USB001",
    "type": "USB",
    "model": "M425 MFP"
  },
  "mfp_features": {
    "scan_enabled": true,
    "copy_enabled": true,
    "fax_enabled": true
  },
  "command_history": [...]
}
```

## 🎮 Интерактивное меню M425

При запуске `--interactive` отображается специализированное меню:

```
📋 Найденные HP M425 MFP принтеры:
────────────────────────────────────────────────────────────
1. HP LaserJet Pro 400 MFP M425dn
   Модель: M425 MFP
   Тип: USB
   Порт: USB001
   Драйвер: HP LaserJet Pro 400 MFP M425 PCL 6
   Статус: Ready

2. HP LaserJet Pro 400 MFP M425dw
   Модель: M425 MFP
   Тип: Network  
   Порт: IP_192.168.1.100

3. Указать USB порт вручную
4. Отмена

Выберите M425 принтер (1-4):
```

## ⚡ Оптимизации для M425

### Увеличенные таймауты:
- **Подключение**: 15 секунд (вместо 10)
- **PJL команды**: 30 секунд для Windows, 25 для Linux
- **Задержки между командами**: 0.7 секунд

### Специфичная обработка:
- **MFP-статус**: проверка всех функций устройства
- **Расширенная диагностика**: WMI запросы для M425
- **Множественные команды**: отправка нескольких вариантов PJL

## 🔄 Алгоритм работы с M425

### Получение счетчика:
```
1. Отправка специфичных M425 команд:
   - @PJL INQUIRE SCANCOUNTER
   - @PJL INQUIRE MFPSCANCOUNT
   - @PJL USTATUS DEVICE

2. Попытка получения через систему:
   - Windows: WMI запросы для M425
   - Linux: CUPS статистика M425

3. Fallback на кэшированное значение
```

### Установка счетчика:
```
1. Отправка команд установки:
   - @PJL SET SCANCOUNTER=<значение>
   - @PJL SET MFPSCANCOUNT=<значение>
   - @PJL DEFAULT SCANCOUNTER=<значение>

2. Добавление MFP комментария:
   - @PJL COMMENT M425 MFP SCANNER COUNTER

3. Сохранение в конфигурации M425
```

## 📝 Примеры использования M425

### Сценарий 1: Первое подключение M425
```bash
# 1. Найти M425 принтеры
python hp_m425_scanner_counter.py --list

# 2. Выбрать M425 интерактивно
python hp_m425_scanner_counter.py --select

# 3. Работать с выбранным M425
python hp_m425_scanner_counter.py --use-saved --get
```

### Сценарий 2: Быстрая работа с M425
```bash
# Прямое подключение к M425 через USB001
python hp_m425_scanner_counter.py --usb-port USB001 --get
python hp_m425_scanner_counter.py -p 1 --set 3000
```

### Сценарий 3: Мониторинг M425
```bash
# Получение расширенной информации о M425
python hp_m425_scanner_counter.py --info

# История операций с M425
python hp_m425_scanner_counter.py --history
```

## 🛠️ Диагностика M425

### Проблема: M425 не найден
```bash
# Проверьте подключение M425
python hp_m425_scanner_counter.py --list

# Если не найден, попробуйте ручной порт
python hp_m425_scanner_counter.py --usb-port USB001 --info
```

### Проблема: Команды не работают
- ✅ M425 MFP может требовать больше времени для обработки
- ✅ Попробуйте увеличить таймаут: `--timeout 30`
- ✅ Убедитесь, что M425 не занят сканированием/копированием

### Проблема: Счетчик не обновляется
- ✅ M425 может кэшировать значения
- ✅ Попробуйте перезагрузить M425 MFP
- ✅ Проверьте файл `m425_counter_config.json`

## 🆚 Отличия от обычной версии

| Функция | M425 версия | Обычная версия |
|---------|-------------|----------------|
| **PJL команды** | M425-специфичные | Стандартные |
| **Обнаружение** | Поиск MFP устройств | Поиск принтеров |
| **Таймауты** | Увеличенные для MFP | Стандартные |
| **Диагностика** | MFP статус | Принтер статус |
| **Конфигурация** | `m425_counter_config.json` | `printer_counter_config.json` |

## 💡 Советы для M425

### Оптимальная работа:
1. **Используйте USB001** - обычно первый порт для M425
2. **Запускайте от администратора** в Windows
3. **Не прерывайте операции** M425 MFP
4. **Ждите завершения** сканирования/копирования

### Устранение неполадок:
1. **Перезагрузите M425** при зависании
2. **Проверьте USB кабель** - MFP требует качественного соединения
3. **Обновите драйверы** M425 в системе
4. **Используйте --interactive** для выбора правильного M425

## 📄 Лицензия

Специализированная версия для HP LaserJet Pro 400 MFP M425 PCL.
Предоставляется "как есть" без гарантий.
