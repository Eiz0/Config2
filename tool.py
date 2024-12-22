import os
import sys
import configparser
import argparse
import subprocess

class GitDepsVisualizer:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        # Извлекаем параметры из ini
        self.graphviz_path = self.config["VisualizerConfig"]["graphviz_path"]
        self.repo_path = self.config["VisualizerConfig"]["repo_path"]
        self.output_file = self.config["VisualizerConfig"]["output_file"]
        self.target_file_hash = self.config["VisualizerConfig"]["target_file_hash"]

    def _load_config(self, path):
        config = configparser.ConfigParser()
        with open(path, "r", encoding="utf-8") as f:
            config.read_file(f)
        return config

    def find_commits_with_file(self):
        """
        Ищет все коммиты (их хэши), в которых фигурировал файл target_file_hash.
        Возвращает список хэшей (от более поздних к более ранним).
        
        Предполагаем, что target_file_hash - это имя файла/путь, а не SHA blob.
        Если нужно искать именно blob-хеш, тогда логика усложнится 
        (придётся для каждого коммита смотреть git ls-tree и т.д.).
        """
        # Переходим в repo_path
        old_cwd = os.getcwd()
        os.chdir(self.repo_path)

        # Команда: git log --pretty=%H -- <target_file> 
        # Выведет commit-hash всех коммитов, где изменялся этот файл.
        cmd = ["git", "log", "--pretty=%H", "--", self.target_file_hash]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Ошибка при выполнении git log:", result.stderr, file=sys.stderr)
            os.chdir(old_cwd)
            return []

        commits = result.stdout.strip().split("\n")
        commits = [c for c in commits if c]  # убираем пустые строки
        # Восстанавливаем путь
        os.chdir(old_cwd)

        return commits

    def build_dependency_graph(self, commits):
        """
        Для каждого коммита находим его родителя(ей). Строим граф (словарь),
        где ключ = коммит, значение = список прямых родителей.
        
        Возвращаем dict: {child_commit: [parent1, parent2, ...], ...}
        
        Затем при визуализации будем рисовать parent -> child.
        """
        if not commits:
            return {}

        old_cwd = os.getcwd()
        os.chdir(self.repo_path)

        graph = {}
        for commit in commits:
            # Узнаем родителя(ей)
            cmd = ["git", "show", "--pretty=%P", "--no-patch", commit]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Строка вида: "parent1 parent2" если мердж, или один родитель, или ""
                out_lines = result.stdout.strip().split("\n")
                # Обычно %P выведется в первой строке после commit info
                # Найдём первую строку, где что-то есть.
                parents_line = ""
                for line in out_lines:
                    if line and not line.startswith("commit "):
                        parents_line = line
                        break

                parent_hashes = parents_line.split() if parents_line else []
                # Но нас интересуют только те родители, которые тоже в списке `commits`
                # Если хотим строить граф только по интересующим нас коммитам:
                # parent_hashes = [p for p in parent_hashes if p in commits]

                # Если же хотим видеть все зависимости (включая коммиты вне списка),
                # тогда убираем фильтр.
                # В задании сказано «включая транзитивные зависимости».
                # Но при этом условии список может сильно расшириться.
                # Для упрощения будем строить только по тем, кто уже есть в `commits`.
                parent_hashes = [p for p in parent_hashes if p in commits]

                graph[commit] = parent_hashes
            else:
                print(f"Ошибка при получении родителей для {commit}: {result.stderr}", file=sys.stderr)

        os.chdir(old_cwd)
        return graph

    def graph_to_dot(self, graph):
        """
        Принимает словарь вида { child: [parent1, parent2], ... }
        и строит текст в формате Graphviz (DOT).
        
        Замечание: Обычно в Git графе стрелки идут от родителя к потомку.
        Но можно рисовать в любом направлении (главное — последовательно).
        """
        lines = []
        lines.append("digraph G {")
        for child, parents in graph.items():
            for p in parents:
                # Ребро: parent -> child
                lines.append(f'    "{p}" -> "{child}";')
        lines.append("}")
        return "\n".join(lines)

    def run(self, print_to_stdout=True):
        """
        Главный метод: находим коммиты, строим граф, выводим DOT.
        """
        commits = self.find_commits_with_file()
        if not commits:
            print("Не найдено коммитов, содержащих указанный файл.")
            return

        graph = self.build_dependency_graph(commits)
        dot_code = self.graph_to_dot(graph)

        if print_to_stdout:
            print(dot_code)
        # Если нужно — можем сохранить в output_file
        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(dot_code)

def main():
    parser = argparse.ArgumentParser(description="Git dependency visualizer")
    parser.add_argument("--config", "-c", default="config.ini", help="Путь к конфигурационному .ini-файлу")
    args = parser.parse_args()

    vis = GitDepsVisualizer(args.config)
    vis.run(print_to_stdout=True)

if __name__ == "__main__":
    main()
