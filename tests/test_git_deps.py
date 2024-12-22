import pytest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from tool import GitDepsVisualizer

@pytest.fixture
def temp_config():
    """
    Создаёт временный config.ini, возвращает путь к нему.
    После теста удаляется.
    """
    test_dir = tempfile.mkdtemp(prefix="test_config_")
    config_path = os.path.join(test_dir, "test_config.ini")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("[VisualizerConfig]\n")
        f.write("graphviz_path = /usr/bin/dot\n")
        f.write("repo_path = /path/to/repo\n")
        f.write("output_file = /path/to/output.dot\n")
        f.write("target_file_hash = my_file.txt\n")
    yield config_path
    shutil.rmtree(test_dir)

def test_load_config(temp_config):
    vis = GitDepsVisualizer(temp_config)
    assert vis.graphviz_path == "/usr/bin/dot"
    assert vis.repo_path == "/path/to/repo"
    assert vis.output_file == "/path/to/output.dot"
    assert vis.target_file_hash == "my_file.txt"

@patch("subprocess.run")
def test_find_commits_with_file(mock_run, temp_config):
    # Мокаем ответ git log
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "abc123\ndef456\n"
    mock_run.return_value = mock_process

    vis = GitDepsVisualizer(temp_config)
    commits = vis.find_commits_with_file()

    assert len(commits) == 2
    assert commits == ["abc123", "def456"]

@patch("os.chdir", return_value=None)
@patch("subprocess.run")
def test_find_commits_with_file(mock_run, mock_chdir, temp_config):
    # Задаём, как будто git log вернул два коммита
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "abc123\ndef456\n"
    mock_run.return_value = mock_process

    vis = GitDepsVisualizer(temp_config)
    commits = vis.find_commits_with_file()

    assert commits == ["abc123", "def456"]
    # Проверяем, что os.chdir хоть раз вызывался
    mock_chdir.assert_called()

    # Заметьте, мы фильтруем только тех родителей, что есть в commits.
    # parent_of_abc не в commits => отбрасываем.
    # "abc" в commits => оставляем
    # "def" в commits => оставляем
    # "abc" в commits => оставляем
    assert graph == {
        "abc": [],      # parent_of_abc отброшен
        "def": ["abc"], # у def родитель abc
        "ghi": ["def", "abc"]
    }

def test_graph_to_dot(temp_config):
    vis = GitDepsVisualizer(temp_config)
    graph = {
        "def": ["abc"],
        "ghi": ["def", "abc"],
        "abc": []
    }
    dot = vis.graph_to_dot(graph)

    # Проверяем, что есть строки вида: "abc" -> "def", "abc" -> "ghi", "def" -> "ghi"
    # Порядок может быть другой, проверяем вольным образом
    assert 'digraph G' in dot
    assert '"abc" -> "def";' in dot
    assert '"def" -> "ghi";' in dot
    assert '"abc" -> "ghi";' in dot

