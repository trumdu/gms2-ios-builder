# 🎮 GameMaker Studio 2 — iOS Xcode & IPA Auto-Builder 🚀

[![Author](https://img.shields.io/badge/Author-yearningss-blue.svg)](https://github.com/yearningss)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-orange.svg)]()

An automated Python tool to compile **GameMaker Studio 2** projects into Xcode projects (VM & YYC) and automatically build unsigned `.ipa` packages via **GitHub Actions**!

Developer: **[yearningss](https://github.com/yearningss)**

---

## 🌟 Key Features

- 🔍 **Deep Igor CLI Auto-Discovery**: Automatically locates Igor CLI, GameMaker Runtimes, and licenses across your system.
- ⚡ **VM & YYC Support**: Supports both **GMS2 VM (Interpreted)** and **GMS2 YYC (YoYo C++ Compiler)** output modes.
- 📁 **Isolated `Build_iOS` Directory**: Keeps all generated Xcode project files isolated in a single `Build_iOS` folder.
- ☁️ **GitHub Actions Integration**: Automatically creates `.github/workflows/ios-build.yml` and manages Git LFS tracking for large assets.
- ⏳ **100% Upload Verification**: Verifies Git LFS uploads and checks `git diff` against remote `origin/main` before completing.
- 🧹 **Auto Cache Cleanup**: Automatically removes heavy temporary build caches after successful upload.
- 📲 **Sideloadly & Installation Guide**: Displays step-by-step instructions for downloading artifacts and installing `.ipa` files on iOS devices using **Sideloadly**.

---

## 🚀 Quick Start Guide

### 1. Requirements
- **Python 3.x**
- **Git** (with **Git LFS**)
- **GameMaker Studio 2**

### 2. Run the Script
Download `build_ios.py` and run it from your terminal:

```bash
python build_ios.py
```

### 3. Follow the Prompts:
1. Enter the path to your GameMaker project (`.yyp` file).
2. Choose your compiler mode (`1` for VM, `2` for YYC).
3. The script compiles your project into an Xcode project under `Build_iOS`.
4. When prompted to build `.ipa`, enter your clean GitHub repository URL.
5. The script handles Git LFS tracking, commits, pushes, and opens the GitHub Actions workflow page in your browser!

---

## 📲 How to Install .ipa on iOS via Sideloadly

1. Go to the opened **GitHub Actions** page, click the top workflow run, and download **`Unsigned-iOS-IPA`** from the **Artifacts** section.
2. Unzip the downloaded file to get `UnsignedApp.ipa`.
3. Launch [Sideloadly](https://sideloadly.io) and connect your iPhone/iPad via USB.
4. Drag & drop `UnsignedApp.ipa` into Sideloadly.
5. Enter your Apple ID and click **Start**.
6. On your iOS device, go to `Settings -> General -> VPN & Device Management` and tap **Trust <Your Apple ID>**.

---

## 👨‍💻 Author
- **GitHub**: [yearningss](https://github.com/yearningss)
