#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GameMaker iOS Xcode & IPA Auto-Builder Script
=============================================
Developer / Author: yearningss (https://github.com/yearningss)
GitHub: https://github.com/yearningss

Автоматический скрипт компиляции проектов GameMaker Studio 2 в проект Xcode
и отправки на GitHub Actions для автоматической сборки неподписанного .ipa файла.
Поддерживает режим VM (GMS2 VM) и YYC (GMS2 YYC), глубокий поиск Igor CLI,
создание единой папки Build_iOS и авто-очистку временных файлов!
"""

__author__ = "yearningss"
__url__ = "https://github.com/yearningss"

import os
import sys
import glob
import subprocess
import shutil
import webbrowser

# Настройка кодировки для Windows консоли
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WORKFLOW_TEMPLATE = """name: Build Unsigned iOS App (.ipa)

on:
  push:
    branches: [ "main", "master" ]
  workflow_dispatch:

jobs:
  build-ios:
    runs-on: macos-14

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          lfs: true

      - name: Build Unsigned App with xcodebuild
        run: |
          XCODE_PROJ=$(find . -maxdepth 4 -name "*.xcodeproj" | head -n 1)
          XCODE_SPACE=$(find . -maxdepth 4 -name "*.xcworkspace" | head -n 1)
          
          echo "Found Xcode Project: $XCODE_PROJ"
          echo "Found Xcode Workspace: $XCODE_SPACE"
          
          mkdir -p build/DerivedData

          if [ -n "$XCODE_SPACE" ]; then
            SCHEME_NAME=$(xcodebuild -workspace "$XCODE_SPACE" -list | grep -A 1 "Schemes:" | tail -n 1 | xargs)
            echo "Building scheme $SCHEME_NAME from workspace $XCODE_SPACE..."
            xcodebuild clean build \\
              -workspace "$XCODE_SPACE" \\
              -scheme "$SCHEME_NAME" \\
              -sdk iphoneos \\
              -configuration Release \\
              -derivedDataPath build/DerivedData \\
              CODE_SIGNING_ALLOWED=NO \\
              CODE_SIGNING_REQUIRED=NO \\
              CODE_SIGN_IDENTITY=""
          elif [ -n "$XCODE_PROJ" ]; then
            SCHEME_NAME=$(xcodebuild -project "$XCODE_PROJ" -list | grep -A 1 "Schemes:" | tail -n 1 | xargs)
            echo "Building scheme $SCHEME_NAME from project $XCODE_PROJ..."
            xcodebuild clean build \\
              -project "$XCODE_PROJ" \\
              -scheme "$SCHEME_NAME" \\
              -sdk iphoneos \\
              -configuration Release \\
              -derivedDataPath build/DerivedData \\
              CODE_SIGNING_ALLOWED=NO \\
              CODE_SIGNING_REQUIRED=NO \\
              CODE_SIGN_IDENTITY=""
          else
            echo "Error: Xcode project file (.xcodeproj / .xcworkspace) not found in repository!"
            exit 1
          fi

      - name: Package Unsigned .ipa
        run: |
          mkdir -p Payload
          APP_PATH=$(find build/DerivedData -name "*.app" | head -n 1)
          if [ -d "$APP_PATH" ]; then
            cp -r "$APP_PATH" Payload/
            zip -r UnsignedApp.ipa Payload
            echo "IPA successfully created!"
          else
            echo "Error: .app bundle not found!"
            exit 1
          fi

      - name: Upload IPA Artifact
        uses: actions/upload-artifact@v4
        with:
          name: Unsigned-iOS-IPA
          path: UnsignedApp.ipa
"""

GITATTRIBUTES_TEMPLATE = """*.ios filter=lfs diff=lfs merge=lfs -text
*.dat filter=lfs diff=lfs merge=lfs -text
*.a filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.yyz filter=lfs diff=lfs merge=lfs -text
*.cpp filter=lfs diff=lfs merge=lfs -text
*.h filter=lfs diff=lfs merge=lfs -text
"""

GITIGNORE_TEMPLATE = """# GameMaker & OS files
*.yyz
.DS_Store
Thumbs.db
*.user
*.config
*.log
cache/
build/
"""

def print_banner():
    print("=" * 65)
    print("   GameMaker iOS Xcode & IPA Auto-Builder (VM & YYC)")
    print("   Developer: yearningss (https://github.com/yearningss)")
    print("=" * 65)

def print_sideloadly_instructions(actions_url):
    print("\n" + "=" * 65)
    print("🎉 УСПЕХ! Проект загружен и собирается на GitHub Actions!")
    print("=" * 65)
    print("👨‍💻 Разработчик скрипта: yearningss (https://github.com/yearningss)")
    print(f"🔗 Ссылка на статус сборки: {actions_url}")
    print("\n-----------------------------------------------------------------")
    print("📥 КАК СКАЧАТЬ ГОТОВЫЙ .IPA ФАЙЛ:")
    print("1. Перейдите по ссылке выше (страница откроется автоматически).")
    print("2. Кликните на самый верхний (свежий) запуск сборки.")
    print("3. Прокрутите вниз страницы до раздела 'Artifacts' (Артефакты).")
    print("4. Нажмите на 'Unsigned-iOS-IPA' для скачивания архива с вашей игрой.")
    print("5. Распакуйте скачанный архив — внутри будет файл 'UnsignedApp.ipa'.")
    print("-----------------------------------------------------------------")
    print("📲 КАК УСТАНОВИТЬ ИГРУ НА IPHONE / IPAD ЧЕРЕЗ SIDELOADLY:")
    print("1. Скачайте программу Sideloadly с официального сайта: https://sideloadly.io")
    print("2. Подключите ваш iPhone / iPad к компьютеру через USB-кабель.")
    print("3. Запустите Sideloadly и перетащите файл 'UnsignedApp.ipa' в окно программы.")
    print("4. В поле 'Apple ID' укажите вашу учетную запись Apple.")
    print("5. Нажмите кнопку 'Start' для установки игры на устройство.")
    print("6. На iPhone откройте: Настройки -> Основные -> VPN и управление устройством.")
    print("7. Нажмите на ваш Apple ID и выберите 'Доверять'. Готово! 🎮")
    print("=" * 65 + "\n")

def run_command(cmd, cwd=None):
    print(f"\n[EXEC] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    return res.returncode == 0

def find_gamemaker_paths():
    """ Глубокий поиск путей к Igor CLI, Runtime, Prefabs и профилю пользователя """
    igor_path = None
    runtime_path = None
    prefabs_path = None
    user_dir = None
    licence_file = None

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        programdata = os.environ.get("PROGRAMDATA", "C:\\ProgramData")

        # 1. Поиск Runtime & Igor.exe
        rt_patterns = [
            os.path.join(programdata, "GameMakerStudio2*", "Cache", "runtimes", "runtime-*"),
            os.path.join(localappdata, "GameMakerStudio2*", "Cache", "runtimes", "runtime-*"),
            os.path.join(appdata, "GameMakerStudio2*", "Cache", "runtimes", "runtime-*"),
            "C:\\ProgramData\\GameMakerStudio2*\\Cache\\runtimes\\runtime-*",
            "C:\\Program Files\\GameMaker*\\runtimes\\runtime-*",
            "C:\\Program Files (x86)\\GameMaker*\\runtimes\\runtime-*"
        ]
        runtimes = []
        for pat in rt_patterns:
            runtimes.extend(glob.glob(pat))

        if runtimes:
            runtimes.sort(reverse=True)
            runtime_path = runtimes[0]
            igor_path = os.path.join(runtime_path, "bin", "igor", "windows", "x64", "Igor.exe")
            if not os.path.exists(igor_path):
                igor_path = os.path.join(runtime_path, "bin", "igor", "windows", "x86", "Igor.exe")

        # Глубокий поиск Igor.exe если стандартные пути не сработали
        if not igor_path or not os.path.exists(igor_path):
            deep_search = (
                glob.glob(os.path.join(programdata, "**", "Igor.exe"), recursive=True) +
                glob.glob(os.path.join(localappdata, "**", "Igor.exe"), recursive=True) +
                glob.glob(os.path.join(appdata, "**", "Igor.exe"), recursive=True)
            )
            if deep_search:
                igor_path = deep_search[0]
                runtime_path = os.path.abspath(os.path.join(os.path.dirname(igor_path), "..", "..", ".."))

        # 2. Поиск Prefabs
        prefab_patterns = [
            os.path.join(programdata, "GameMakerStudio2*", "Prefabs"),
            os.path.join(localappdata, "GameMakerStudio2*", "Prefabs"),
            os.path.join(appdata, "GameMakerStudio2*", "Prefabs")
        ]
        for pat in prefab_patterns:
            matches = glob.glob(pat)
            if matches:
                prefabs_path = matches[0]
                break

        # 3. Поиск профиля пользователя
        user_patterns = [
            os.path.join(appdata, "GameMakerStudio2*"),
            os.path.join(localappdata, "GameMakerStudio2*")
        ]
        for pat in user_patterns:
            matches = glob.glob(pat)
            if matches:
                user_dir = matches[0]
                break

    else:
        # macOS
        runtimes = glob.glob("/Users/Shared/GameMakerStudio2/Cache/runtimes/runtime-*")
        if runtimes:
            runtimes.sort(reverse=True)
            runtime_path = runtimes[0]
            igor_path = os.path.join(runtime_path, "bin", "igor", "osx", "arm64", "Igor")
            if not os.path.exists(igor_path):
                igor_path = os.path.join(runtime_path, "bin", "igor", "osx", "x86", "Igor")

        user_dir = os.path.expanduser("~/Library/Application Support/GameMakerStudio2")

    if user_dir:
        lic_files = glob.glob(os.path.join(user_dir, "**", "licence.plist"), recursive=True)
        if lic_files:
            licence_file = lic_files[0]

    return igor_path, runtime_path, prefabs_path, user_dir, licence_file

def main():
    print_banner()

    # 1. Запрос пути к проекту .yyp
    yyp_input = input("\n[1] Введите путь к файлу проекта (.yyp) или перетащите его сюда: ").strip(' "\'')

    if not yyp_input:
        print("[!] Путь не указан. Выход.")
        return

    if os.path.isdir(yyp_input):
        yyp_files = glob.glob(os.path.join(yyp_input, "*.yyp"))
        if not yyp_files:
            print("[!] Ошибка: В указанной папке не найден файл .yyp!")
            return
        yyp_path = yyp_files[0]
    else:
        yyp_path = yyp_input

    if not os.path.exists(yyp_path) or not yyp_path.endswith(".yyp"):
        print(f"[!] Ошибка: Файл '{yyp_path}' не существует или не является проектом .yyp!")
        return

    project_dir = os.path.dirname(os.path.abspath(yyp_path))
    print(f"[+] Проект найден: {yyp_path}")

    # 2. Выбор режима компилятора (VM vs YYC)
    print("\n[2] Выберите режим компилятора Output:")
    print("  1. GMS2 VM  (Interpreted / Виртуальная машина)")
    print("  2. GMS2 YYC (YoYo C++ Compiler)")
    mode_input = input("Выберите режим (1 или 2) [по умолчанию 1]: ").strip()

    is_yyc = (mode_input == "2")
    mode_str = "GMS2 YYC (C++)" if is_yyc else "GMS2 VM (Interpreted)"
    print(f"[+] Выбран режим: {mode_str}")

    # 3. Глубокий поиск GameMaker окружения
    print("\n[3] Глубокий поиск установленного Igor CLI и окружения GameMaker...")
    igor_path, runtime_path, prefabs_path, user_dir, licence_file = find_gamemaker_paths()

    if not igor_path or not os.path.exists(igor_path):
        igor_path = input("[?] Igor CLI не найден автоматически. Укажите путь к Igor.exe / Igor: ").strip(' "\'')

    if not runtime_path or not os.path.exists(runtime_path):
        runtime_path = input("[?] Путь к GameMaker Runtime не найден. Укажите путь (папка runtime-X.X.X): ").strip(' "\'')

    print(f"  * Igor CLI: {igor_path}")
    print(f"  * Runtime: {runtime_path}")
    if prefabs_path:
        print(f"  * Prefabs: {prefabs_path}")
    if licence_file:
        print(f"  * Лицензия: {licence_file}")

    # 4. Компиляция в единую папку Build_iOS через Igor
    output_xcode_dir = os.path.join(project_dir, "Build_iOS")
    os.makedirs(output_xcode_dir, exist_ok=True)

    print(f"\n[4] Запуск компиляции в папку Build_iOS ({mode_str})...")

    runtime_flag = "-r=YYC" if is_yyc else "-r=VM"

    cmd_parts = [
        f'"{igor_path}"',
        '-v',
        f'--project="{yyp_path}"',
        '--config="Default"',
        f'--runtimePath="{runtime_path}"',
        f'--of="{output_xcode_dir}"',
        runtime_flag
    ]

    if user_dir:
        cmd_parts.append(f'--user="{user_dir}"')
    if licence_file:
        cmd_parts.append(f'--licencefile="{licence_file}"')
    if prefabs_path and os.path.exists(prefabs_path):
        cmd_parts.append(f'--prefabs="{prefabs_path}"')

    cmd_parts.extend(['ios', 'Compile'])
    compile_cmd = " ".join(cmd_parts)

    success = run_command(compile_cmd, cwd=project_dir)

    if not success:
        print("[!] Ошибка при компиляции проекта через Igor CLI!")
        return

    print("\n[+] Сборка Xcode проекта в папке Build_iOS завершена успешно!")

    # Поиск созданного .xcodeproj
    xcode_proj_dirs = glob.glob(os.path.join(output_xcode_dir, "**", "*.xcodeproj"), recursive=True)
    if xcode_proj_dirs:
        target_export_folder = os.path.dirname(xcode_proj_dirs[0])
        print(f"[+] Проект Xcode готов в: {target_export_folder}")
        try:
            if sys.platform == "win32":
                os.startfile(target_export_folder)
            else:
                subprocess.run(["open", target_export_folder])
        except Exception:
            pass
    else:
        target_export_folder = output_xcode_dir
        print(f"[+] Папка сборки: {output_xcode_dir}")

    # 5. Вопрос про отправку на GitHub для сборки .ipa
    answer = input("\n[5] Хотите собрать .ipa файл через GitHub Actions? (д/н | y/n): ").strip().lower()

    if answer not in ['y', 'yes', 'д', 'да']:
        print("[+] Готовый проект Xcode сохранен локально в папке Build_iOS!")
        return

    # 6. Проверка Git и Git LFS
    print("\n[6] Проверка установленного Git и авторизации...")

    git_check = subprocess.run("git --version", shell=True, capture_output=True, text=True)
    if git_check.returncode != 0:
        print("[!] Ошибка: Git не установлен на вашем компьютере!")
        print(" -> Пожалуйста, установите Git с официального сайта: https://git-scm.com/")
        webbrowser.open("https://git-scm.com/downloads")
        return
    print(f"  * {git_check.stdout.strip()}")

    lfs_check = subprocess.run("git lfs --version", shell=True, capture_output=True, text=True)
    if lfs_check.returncode != 0:
        print("[!] Предупреждение: Git LFS не обнаружен. Устанавливаем Git LFS...")
        run_command("git lfs install")
    else:
        print(f"  * {lfs_check.stdout.strip()}")

    git_user = subprocess.run("git config user.name", shell=True, capture_output=True, text=True).stdout.strip()
    git_email = subprocess.run("git config user.email", shell=True, capture_output=True, text=True).stdout.strip()

    if not git_user or not git_email:
        print("\n[!] Внимание: У вас не настроено имя/email в Git.")
        new_name = input("Введите ваше имя для Git: ").strip()
        new_email = input("Введите ваш Email для Git: ").strip()
        run_command(f'git config --global user.name "{new_name}"')
        run_command(f'git config --global user.email "{new_email}"')

    # 7. Запрос ссылки на GitHub репозиторий с рекомендацией создать новый
    print("\n[7] Настройка GitHub репозитория...")
    print("=" * 65)
    print("⚠️  НАСТОЯТЕЛЬНО РЕКОМЕНДУЕТСЯ СОЗДАТЬ НОВЫЙ ЧИСТЫЙ РЕПОЗИТОРИЙ НА GITHUB!")
    print("    Это защитит ваш основной репозиторий с исходниками от загрязнения.")
    print("    Создайте новый публичный/приватный репозиторий на https://github.com/new")
    print("    Пример ссылки: https://github.com/username/my-app-ios-build.git")
    print("=" * 65)

    repo_url = input("\nВведите URL вашего нового GitHub репозитория: ").strip()

    if not repo_url.startswith("http") and not repo_url.startswith("git@"):
        print("[!] Ошибка: Введен некорректный URL репозитория!")
        return

    # 8. Подготовка структуры файлов для загрузки на GitHub
    print("\n[8] Подготовка репозитория и файлов сборки...")

    workflow_dir = os.path.join(target_export_folder, ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)

    with open(os.path.join(workflow_dir, "ios-build.yml"), "w", encoding="utf-8") as f:
        f.write(WORKFLOW_TEMPLATE)

    with open(os.path.join(target_export_folder, ".gitattributes"), "w", encoding="utf-8") as f:
        f.write(GITATTRIBUTES_TEMPLATE)

    with open(os.path.join(target_export_folder, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(GITIGNORE_TEMPLATE)

    run_command("git init", cwd=target_export_folder)
    run_command("git lfs install", cwd=target_export_folder)
    run_command("git lfs track \"*.ios\"", cwd=target_export_folder)
    run_command("git lfs track \"*.dat\"", cwd=target_export_folder)
    run_command("git lfs track \"*.a\"", cwd=target_export_folder)
    run_command("git lfs track \"*.cpp\"", cwd=target_export_folder)
    run_command("git lfs track \"*.h\"", cwd=target_export_folder)
    
    # Сброс и привязка remote
    run_command("git remote remove origin", cwd=target_export_folder)
    run_command(f'git remote add origin "{repo_url}"', cwd=target_export_folder)
    run_command("git branch -M main", cwd=target_export_folder)

    print("\n[9] Индексация файлов локально (git add .)...")
    run_command("git add .", cwd=target_export_folder)
    run_command(f'git commit -m "Auto-generated Xcode project ({mode_str}) with GitHub Actions iOS build workflow by yearningss"', cwd=target_export_folder)
    
    print("\n[10] Загрузка ресурсов Git LFS на сервер GitHub (может занять 1-3 минуты)...")
    print("⏳ Пожалуйста, подождите полного завершения загрузки LFS-объектов...")
    lfs_push_success = run_command("git lfs push origin main --all", cwd=target_export_folder)

    print("\n[11] Синхронизация ветки с GitHub (git push origin main)...")
    push_success = run_command("git push -u origin main --force", cwd=target_export_folder)

    # 12. Проверка подтверждения на сервере (git fetch)
    print("\n[12] Проверка подтверждения наличия коммита на сервере GitHub...")
    fetch_success = run_command("git fetch origin main", cwd=target_export_folder)

    # 13. Авто-очистка промежуточных кэшей
    print("\n[13] Очистка временных файлов компиляции...")
    temp_cache = os.path.join(project_dir, "cache")
    if os.path.exists(temp_cache):
        try:
            shutil.rmtree(temp_cache)
            print("  * Удалены промежуточные файлы кэша (cache/)")
        except Exception:
            pass
    
    actions_url = repo_url.rstrip(".git") + "/actions"
    
    # Показ подробной инструкции по скачиванию и установке через Sideloadly
    print_sideloadly_instructions(actions_url)
    webbrowser.open(actions_url)

if __name__ == "__main__":
    main()
