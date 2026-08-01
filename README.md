# 🎮 GameMaker Studio 2 — iOS Xcode & IPA Auto-Builder 🚀

[![Author](https://img.shields.io/badge/Author-yearningss-blue.svg)](https://github.com/yearningss)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-orange.svg)]()

Автоматический Python-скрипт для компиляции проектов **GameMaker Studio 2** в проект Xcode (VM & YYC) и автоматической сборки неподписанного `.ipa` файла через **GitHub Actions**!

Разработчик: **[yearningss](https://github.com/yearningss)**

---

## 🌟 Возможности

- 🔍 **Глубокий авто-поиск Igor CLI**: Автоматически находит Igor CLI, версии GameMaker Runtime и лицензию в системе.
- ⚡ **Поддержка VM & YYC**: Поддерживает компиляцию как в режиме **GMS2 VM (Interpreted)**, так и **GMS2 YYC (YoYo C++ Compiler)**.
- 📁 **Единая папка `Build_iOS`**: Все создаваемые файлы проекта Xcode изолированно складываются в чистую папку `Build_iOS`.
- ☁️ **Интеграция с GitHub Actions**: Автоматически создаёт файл рабочего процесса `.github/workflows/ios-build.yml` и загружает ресурсы через Git LFS.
- ⏳ **Гарантия 100% подтверждения загрузки**: Скрипт проверяет завершение передачи всех LFS-объектов и выверяет `git diff` с сервером GitHub.
- 🧹 **Авто-очистка кэша**: Очищает тяжелые промежуточные файлы компиляции сразу после успешной загрузки.
- 📲 **Инструкция по установке**: Выводит подробный гайд по скачиванию артефакта и установке файла `.ipa` на iPhone/iPad через **Sideloadly**.

---

## 🚀 Быстрый запуск

### 1. Требования
- Установленный **Python 3.x**
- Установленный **Git** (с поддержкой **Git LFS**)
- Установленный **GameMaker Studio 2**

### 2. Запуск скрипта
Скачайте `build_ios.py` и запустите его через консоль:

```bash
python build_ios.py
```

### 3. Следуйте шагам в консоли:
1. Введите путь к файлу вашего проекта GameMaker (`.yyp`).
2. Выберите режим компилятора (`1` — VM, `2` — YYC).
3. Скрипт соберет проект Xcode в папку `Build_iOS`.
4. При согласии на сборку `.ipa` укажите URL вашего чистого GitHub-репозитория.
5. Скрипт сам отправит проект на GitHub, проверит 100% подтверждение и откроет страницу сборки в браузере!

---

## 📲 Установка .ipa на iOS через Sideloadly

1. Откройте открывшуюся страницу **GitHub Actions**, выберите свежий запуск и в разделе **Artifacts** скачайте `Unsigned-iOS-IPA`.
2. Распакуйте архив — внутри будет `UnsignedApp.ipa`.
3. Запустите [Sideloadly](https://sideloadly.io), подключите iPhone/iPad через USB.
4. Перетащите `UnsignedApp.ipa` в окно Sideloadly, укажите ваш Apple ID и нажмите **Start**.
5. На устройстве перейдите в `Настройки -> Основные -> VPN и управление устройством` и нажмите **Доверять**.

---

## 👨‍💻 Автор
- **GitHub**: [yearningss](https://github.com/yearningss)
