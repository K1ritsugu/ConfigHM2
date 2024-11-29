import subprocess
import os
import argparse
from typing import List, Tuple, Dict


def get_git_commits(repo_path: str) -> List[Tuple[str, List[str]]]:
    """Получение всех коммитов и их родительских коммитов в репозитории."""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%h %p"],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=True
        )
        commits = []
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            commit_hash = parts[0]
            parent_hashes = parts[1:] if len(parts) > 1 else []
            commits.append((commit_hash, parent_hashes))
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при получении коммитов: {e}")
        return []


def get_commit_diff(repo_path: str, commit_hash: str) -> Tuple[List[str], List[str]]:
    """Получение файлов и папок, изменённых в коммите."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
            cwd=repo_path,
            text=True,
            capture_output=True,
            check=True
        )
        changed_files = result.stdout.strip().splitlines()

        folders = set()
        files = set()
        for file in changed_files:
            files.add(file)
            folder = os.path.dirname(file)
            if folder:
                folders.add(folder)
        return list(folders), list(files)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при получении изменений для коммита {commit_hash}: {e}")
        return [], []


def generate_mermaid_graph(commits: List[Tuple[str, List[str]]], repo_path: str) -> str:
    """Генерация графа зависимостей в формате Mermaid."""

    mermaid_graph = "graph TD\n"
    commit_data: Dict[str, Dict] = {}

    for commit_hash, parent_hashes in commits:
        folders, files = get_commit_diff(repo_path, commit_hash)
        commit_data[commit_hash] = {
            'parents': parent_hashes,
            'folders': folders,
            'files': files
        }

    for commit_hash, data in commit_data.items():

        changed_items = []

        if data['folders']:
            folder_list = "<br>".join(data['folders'])
            changed_items.append(f"Папки:<br>{folder_list}")
        if data['files']:
            file_list = "<br>".join(data['files'])
            changed_items.append(f"Файлы:<br>{file_list}")
        commit_text = "<br>".join(changed_items) if changed_items else "Нет изменений"

        commit_text = commit_text.replace('"', '\\"').replace("'", "\\'")

        mermaid_graph += f'  {commit_hash}["{commit_hash}<br>{commit_text}"]\n'

        for parent_hash in data['parents']:
            mermaid_graph += f"  {parent_hash} --> {commit_hash}\n"

    return mermaid_graph


def generate_png_from_mermaid(mermaid_graph: str, output_path: str, visualizer_path: str):
    """Генерация PNG файла из графа Mermaid с использованием mermaid-cli."""
    try:
        with open("temp.mmd", "w", encoding='utf-8') as f:
            f.write(mermaid_graph)

        subprocess.run(
            [visualizer_path, "-i", "temp.mmd", "-o", output_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании PNG: {e}")
    finally:
        # Удаляем временный файл
        if os.path.exists("temp.mmd"):
            os.remove("temp.mmd")


def main():

    parser = argparse.ArgumentParser(description="Визуализатор зависимостей для git-репозитория.")

    parser.add_argument("--repo", required=True, help="Путь к анализируемому git-репозиторию")
    parser.add_argument("--visualizer", required=True, help="Путь к программе для визуализации графов (mermaid-cli)")
    parser.add_argument("--output", required=True, help="Путь для сохранения файла изображения графа зависимостей (png)")

    args = parser.parse_args()

    commits = get_git_commits(args.repo)
    if not commits:
        print("Не удалось получить коммиты из репозитория.")
        return

    mermaid_graph = generate_mermaid_graph(commits, args.repo)

    generate_png_from_mermaid(mermaid_graph, args.output, args.visualizer)

    print("Визуализация зависимостей успешно завершена.")


if __name__ == "__main__":
    main()
