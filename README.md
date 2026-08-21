# ald_win_user_adder_client

Клиентское ПО для синхронизации локальных пользователей и групп Windows с доменом FreeIPA.

Для работы необходима настроенная серверная часть:  
[ald_win_user_adder_server](https://github.com/gorg8100/ald_win_user_adder_server)

---

## Требования

Для работы:

- **Windows**

Для сборки из исходников:

- **Python 3.14.0+**
- Python утилита [PyInstaller](https://pyinstaller.org/) 6.22.0+

---

## Загрузка

### Скачивание готовой сборки

Перейдите в раздел [Releases](https://github.com/gorg8100/ald_win_user_adder_client/releases) и скачайте последний архив
`.zip`. Внутри архива находится исполняемый файл `.exe`.

### Компиляция из исходников

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/gorg8100/ald_win_user_adder_client.git
   ```
2. Установите PyInstaller (если ещё не установлен):
   ```bash
   pip install pyinstaller
   ```
3. Запустите скрипт сборки:
   ```bash
   python build_project.py
   ```
4. Готовый `.exe` будет находиться в папке `compilation_data/bin/`.

---

## Использование

### Запуск

Программа принимает один аргумент командной строки:

- `--settings_file` (или `-s`) — путь к файлу настроек в формате JSON.

Если аргумент не указан, программа будет искать файл `settings.json` в папке, из которой она запущена.

**Пример запуска:**

```cmd
ald_win_user_adder_client.exe --settings_file C:\config\my_settings.json
```

### Конфигурация

Настройки хранятся в файле формата JSON. Пример:

```json
{
  "log_file_path": "log.txt",
  "sources": [
    "http://127.0.0.1:400/data.json"
  ],
  "local_data": {
    "test": "a"
  }
}
```

#### Параметры конфигурации:

- **`log_file_path`** (строка) — путь к файлу для записи логов. Если файл не существует, он будет создан. Логи пишутся
  только при возникновении ошибок.

- **`sources`** (массив строк) — список источников, из которых загружается JSON-манифест для синхронизации пользователей
  и групп.
    - Если строка начинается с `http://` или `https://`, она интерпретируется как URL.
    - В противном случае — как путь к локальному файлу.
    - Перед опросом источники перемешиваются в случайном порядке. Программа последовательно пытается получить манифест
      из каждого источника; если ни один не доступен, выбрасывается ошибка.

- **`local_data`** (объект) — словарь с ключами-строками и значениями произвольного типа. Эти данные передаются в
  обработчик правил фильтрации (получаемых из JSON-магифеста и описанных в серверной части) и могут использоваться для условной синхронизации.

---

## Примечания

- Для корректной работы убедитесь, что серверная часть доступна и возвращает валидный JSON-манифест.
- Программа предназначена для работы в среде Windows с учётом ограничений безопасности (требуются права администратора
  для управления пользователями и группами).

---

## Лицензия

```
MIT License

Copyright (c) 2026 gorg8100

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
