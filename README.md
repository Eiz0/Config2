Этот проект представляет собой инструмент командной строки, который:

Сканирует историю Git-репозитория и находит все коммиты, где упоминается файл (по его пути или хешу).
Строит граф зависимостей (commit → его родительские коммиты) для найденных коммитов, включая транзитивные зависимости.
Выводит код графа в формате Graphviz (DOT), который можно отобразить с помощью внешнего инструмента (dot, xdot, и т.д.).

Структура проекта
Config2/
├── tool.py                 # Основной скрипт (CLI) для визуализации
├── config.ini              # Конфигурационный файл
├── tests/
│   ├── test_git_deps.py
│   └── __init__.py
├── requirements.txt (опционально)
└── README.md               # Описание проекта
tool.py – содержит класс GitDepsVisualizer, который:

Считывает конфигурацию из INI-файла.
Вызывает git log и git show (или другие команды) через subprocess, чтобы построить список коммитов.
Генерирует DOT-код для визуализации графа.

config.ini – указывает пути и параметры для работы:
[VisualizerConfig]
graphviz_path = C:\Graphviz\bin\dot.exe
repo_path = C:\Users\ПК\Desktop\Config2
output_file = C:\Path\to\output.dot
target_file_hash = somefile.txt
tests/test_git_deps.py – содержит набор тестов на pytest, проверяющих:

Чтение config.ini.
Логику поиска коммитов, где фигурирует файл.
Построение графа зависимостей (парсинг родительских хэшей).
Генерацию DOT-кода.

Установка и запуск
pip install -r requirements.txt
(Возможно, потребуется pytest. Если вы планируете реальную работу с Git, нужно, чтобы в системе была установлена команда git.)

Проверьте/отредактируйте config.ini:
[VisualizerConfig]
graphviz_path = C:\Graphviz\bin\dot.exe
repo_path = C:\Users\ПК\Desktop\Config2
output_file = C:\Users\ПК\output.dot
target_file_hash = my_file.txt
repo_path должен указывать на реальный git-репозиторий.
target_file_hash – файл (или хеш), по которому вы хотите найти коммиты.
Запуск:
python tool.py --config config.ini
В результате вы увидите в консоли DOT-код графа вида:
digraph G {
    "abc123" -> "def456";
    "def456" -> "gh789a";
    ...
}
Также, если указано output_file, этот DOT-код будет сохранён в соответствующий файл.

Тестирование
Запуск тестов:
pytest -v
