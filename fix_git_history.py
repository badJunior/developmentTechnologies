import subprocess
import os
import shutil


def run(cmd, check=True):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(f"STDERR: {result.stderr.strip()}")
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


print("=== Шаг 1. Подготовка ===")
run("git checkout main")
run("git pull origin main")

# Удаляем старую backup-ветку, если она есть
run("git branch -D backup/current-state", check=False)

# Создаём backup
run("git checkout -b backup/current-state")
run("git add .")
run('git commit -m "backup: current state before history rewrite"', check=False)
run("git push -u origin backup/current-state --force")

print("\n=== Шаг 2. Очистка main ===")
run("git checkout main")

# Удаляем всё, кроме .git
for item in os.listdir("."):
    if item in [".git", ".venv", "fix_git_history.py"]:
        continue
    if os.path.isdir(item):
        shutil.rmtree(item)
    else:
        os.remove(item)

# Создаём пустой коммит
open(".gitkeep", "w").close()
run("git add .gitkeep")
run('git commit -m "chore: initialize empty project"')

print("\n=== Шаг 3. Создание веток ===")

labs = {
    "lab-1-requirements": [
        "docs/requirements.md", "docs/process.md", "docs/CHANGELOG.md",
        "docs/roadmap.md", "docs/gantt.md", "docs/customer-journey-map.md",
        "docs/user-story-map.md", "docs/traceability.md"
    ],
    "lab-1-repo": [
        "README.md", "CONTRIBUTING.md", "LICENSE", ".gitignore",
        ".editorconfig", ".pre-commit-config.yaml", ".markdownlint-cli2.yaml",
        ".github/workflows/ci.yml"
    ],
    "lab-2-domain": [
        "docs/adr/", "docs/architecture/", "docs/domain/", "docs/api/"
    ],
    "lab-3-service": [
        "src/booking/config.py", "src/booking/app.py", "src/booking/logging.py",
        "src/booking/api/", "src/booking/domain/", "src/booking/services/",
        "src/booking/ports/", "src/booking/adapters/", "tests/"
    ],
    "lab-4-data": [
        "migrations/", "seeds/"
    ],
    "lab-5-testing": [
        "docs/testing/"
    ],
    "lab-6-async": [
        "src/booking/domain/events.py", "src/booking/ports/event_bus.py",
        "src/booking/workers/", "docs/architecture/async-decisions.md"
    ],
    "lab-7-observability": [
        "src/booking/observability/", "src/booking/api/ready.py",
        "docs/slo.md", "docs/runbooks/", "observability/"
    ],
    "lab-8-frontend": [
        "frontend/"
    ],
    "lab-9-audit": [
        "docs/antipatterns/", "docs/architecture-review.md",
        "docs/retrospective.md", "docs/coursework.md",
        "docs/adr/0009-architectural-refactoring.md"
    ]
}

for lab_name, files in labs.items():
    print(f"\n--- Ветка {lab_name} ---")

    # Удаляем старую ветку, если есть
    run(f"git branch -D {lab_name}", check=False)

    # Создаём новую ветку
    run(f"git checkout -b {lab_name}")

    # Копируем файлы из backup
    for file in files:
        result = run(f'git checkout backup/current-state -- {file}', check=False)
        if result.returncode != 0:
            print(f"⚠️ {file} не найден, пропускаем")

    # Коммитим
    run("git add .")
    run(f'git commit -m "feat: add {lab_name} artifacts"')

    # Возвращаемся в main и сливаем
    run("git checkout main")
    run(f'git merge --no-ff {lab_name} -m "Merge branch {lab_name}: {lab_name} completed"')

print("\n=== Шаг 4. Публикация ===")
run("git push origin main")
run("git push origin --all")

print("\n✅ Всё готово! Теперь на GitHub создайте Pull Requests для каждой ветки.")