#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GameMaker Studio 2 — iOS Xcode & IPA Auto-Builder Script
========================================================
Developer / Author: yearningss (https://github.com/yearningss)
GitHub: https://github.com/yearningss

An automated CLI tool to compile GameMaker Studio 2 projects into Xcode projects
(VM & YYC) and push to GitHub Actions for automated unsigned .ipa packaging.
"""

__author__ = "yearningss"
__url__ = "https://github.com/yearningss"

import os
import sys
import glob
import subprocess
import shutil
import webbrowser

# Enable UTF-8 encoding for Windows Console
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
    # Yandex/VGSLFundamentals needs SendableMetatype (Xcode 26 / Swift 6.2+).
    runs-on: macos-15

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          lfs: true

      - name: Select Xcode 26 (Swift SendableMetatype)
        run: |
          set -euo pipefail
          echo "Available Xcode apps:"
          ls /Applications | grep -i Xcode || true
          # VGSLFundamentals (Yandex) needs SendableMetatype / Swift 6.2 → Xcode 26+
          sudo xcode-select -s /Applications/Xcode_26.3.app/Contents/Developer \\
            || sudo xcode-select -s /Applications/Xcode_26.2.app/Contents/Developer \\
            || sudo xcode-select -s /Applications/Xcode_26.1.app/Contents/Developer \\
            || sudo xcode-select -s /Applications/Xcode_26.0.app/Contents/Developer \\
            || sudo xcode-select -s /Applications/Xcode_16.4.app/Contents/Developer \\
            || sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
          xcodebuild -version

      - name: Setup CocoaPods
        run: |
          gem install cocoapods --no-document || true
          pod --version

      - name: Install CocoaPods dependencies
        run: |
          set -euo pipefail
          PODFILE=$(find . -maxdepth 5 -name "Podfile" | head -n 1 || true)
          if [ -z "$PODFILE" ]; then
            echo "No Podfile found — skipping pod install"
            exit 0
          fi
          POD_DIR=$(dirname "$PODFILE")
          echo "Found Podfile at $PODFILE"
          cd "$POD_DIR"
          pod install --repo-update || pod install

      - name: Build Unsigned App with xcodebuild
        run: |
          set -euo pipefail
          XCODE_SPACE=$(find . -maxdepth 5 -name "*.xcworkspace" ! -path "*/Pods/*" | head -n 1 || true)
          XCODE_PROJ=$(find . -maxdepth 5 -name "*.xcodeproj" ! -path "*/Pods/*" | head -n 1 || true)

          echo "Found Xcode Project: $XCODE_PROJ"
          echo "Found Xcode Workspace: $XCODE_SPACE"

          mkdir -p build/DerivedData build/Products

          pick_scheme() {
            local LIST="$1"
            local S
            S=$(echo "$LIST" | sed -n '/Schemes:/,/^$/p' | sed '1d' | sed 's/^[[:space:]]*//' | grep -E '^SyndykCardGame$' | head -n 1 || true)
            if [ -z "$S" ]; then
              S=$(echo "$LIST" | sed -n '/Schemes:/,/^$/p' | sed '1d' | sed 's/^[[:space:]]*//' | grep -v -E 'Test|Pods|Tests' | head -n 1 || true)
            fi
            echo "$S"
          }

          COMMON_ARGS=(
            -sdk iphoneos
            -configuration Release
            -derivedDataPath "$PWD/build/DerivedData"
            CODE_SIGNING_ALLOWED=NO
            CODE_SIGNING_REQUIRED=NO
            CODE_SIGN_IDENTITY=
            ONLY_ACTIVE_ARCH=NO
            CONFIGURATION_BUILD_DIR="$PWD/build/Products"
          )

          if [ -n "$XCODE_SPACE" ]; then
            LIST=$(xcodebuild -workspace "$XCODE_SPACE" -list)
            SCHEME_NAME=$(pick_scheme "$LIST")
            echo "Building scheme '$SCHEME_NAME' from workspace $XCODE_SPACE..."
            xcodebuild build -workspace "$XCODE_SPACE" -scheme "$SCHEME_NAME" "${COMMON_ARGS[@]}"
          elif [ -n "$XCODE_PROJ" ]; then
            LIST=$(xcodebuild -project "$XCODE_PROJ" -list)
            SCHEME_NAME=$(pick_scheme "$LIST")
            echo "Building scheme '$SCHEME_NAME' from project $XCODE_PROJ..."
            xcodebuild build -project "$XCODE_PROJ" -scheme "$SCHEME_NAME" "${COMMON_ARGS[@]}"
          else
            echo "Error: Xcode project file (.xcodeproj / .xcworkspace) not found!"
            exit 1
          fi

          echo "=== Products tree (DerivedData) ==="
          find build/DerivedData/Build/Products -maxdepth 3 -print || true
          echo "=== Products tree (CONFIGURATION_BUILD_DIR) ==="
          find build/Products -maxdepth 3 -print || true

      - name: Package Unsigned .ipa
        run: |
          set -euo pipefail
          rm -rf Payload
          mkdir -p Payload

          echo "Searching for .app bundles..."
          find build -type d -name "*.app" -print || true

          APP_PATH=$(find build/Products build/DerivedData/Build/Products -type d -name "SyndykCardGame.app" 2>/dev/null | head -n 1 || true)
          if [ -z "$APP_PATH" ]; then
            APP_PATH=$(find build -type d -name "*.app" | grep -i 'iphoneos' | grep -v '/PlugIns/' | head -n 1 || true)
          fi
          if [ -z "$APP_PATH" ]; then
            APP_PATH=$(find build -type d -name "*.app" | grep -v '/PlugIns/' | head -n 1 || true)
          fi

          if [ -z "$APP_PATH" ] || [ ! -d "$APP_PATH" ]; then
            echo "Error: .app bundle not found!"
            find build -maxdepth 8 -type d -print | head -n 300 || true
            exit 1
          fi

          echo "Using APP_PATH=$APP_PATH"
          cp -R "$APP_PATH" Payload/
          ditto -c -k --sequesterRsrc --keepParent Payload UnsignedApp.ipa
          ls -lh UnsignedApp.ipa
          echo "IPA successfully created!"

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
    print("🎉 SUCCESS! Project uploaded & building on GitHub Actions!")
    print("=" * 65)
    print("👨‍💻 Script Developer: yearningss (https://github.com/yearningss)")
    print(f"🔗 Build Status Link: {actions_url}")
    print("\n-----------------------------------------------------------------")
    print("📥 HOW TO DOWNLOAD YOUR FINISHED .IPA FILE:")
    print("1. Go to the link above (opened automatically in your browser).")
    print("2. Click on the latest workflow run at the top of the list.")
    print("3. Scroll down to the 'Artifacts' section at the bottom of the page.")
    print("4. Click 'Unsigned-iOS-IPA' to download the zip archive.")
    print("5. Extract the downloaded zip file — inside you will find 'UnsignedApp.ipa'.")
    print("-----------------------------------------------------------------")
    print("📲 HOW TO INSTALL ON IPHONE / IPAD VIA SIDELOADLY:")
    print("1. Download Sideloadly from the official website: https://sideloadly.io")
    print("2. Connect your iPhone / iPad to your computer via USB cable.")
    print("3. Open Sideloadly and drag & drop 'UnsignedApp.ipa' into the window.")
    print("4. In the 'Apple ID' field, enter your Apple account email.")
    print("5. Click 'Start' to install the app onto your device.")
    print("6. On your iOS device: Settings -> General -> VPN & Device Management.")
    print("7. Tap your Apple ID and select 'Trust'. Enjoy! 🎮")
    print("=" * 65 + "\n")

def run_command(cmd, cwd=None):
    print(f"\n[EXEC] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    return res.returncode == 0

def find_gamemaker_paths():
    """ Deep multi-directory search for Igor CLI, Runtimes, Prefabs, and User License """
    igor_path = None
    runtime_path = None
    prefabs_path = None
    user_dir = None
    licence_file = None

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        programdata = os.environ.get("PROGRAMDATA", "C:\\ProgramData")

        # 1. Search for Runtimes & Igor.exe
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

        # Fallback deep search if standard paths didn't match
        if not igor_path or not os.path.exists(igor_path):
            deep_search = (
                glob.glob(os.path.join(programdata, "**", "Igor.exe"), recursive=True) +
                glob.glob(os.path.join(localappdata, "**", "Igor.exe"), recursive=True) +
                glob.glob(os.path.join(appdata, "**", "Igor.exe"), recursive=True)
            )
            if deep_search:
                igor_path = deep_search[0]
                runtime_path = os.path.abspath(os.path.join(os.path.dirname(igor_path), "..", "..", ".."))

        # 2. Search for Prefabs
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

        # 3. Search for User Profile
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

    # 1. Prompt for .yyp project path
    yyp_input = input("\n[1] Enter path to your GameMaker project (.yyp file or folder): ").strip(' "\'')

    if not yyp_input:
        print("[!] Path not specified. Exiting.")
        return

    if os.path.isdir(yyp_input):
        yyp_files = glob.glob(os.path.join(yyp_input, "*.yyp"))
        if not yyp_files:
            print("[!] Error: No .yyp project file found in specified directory!")
            return
        yyp_path = yyp_files[0]
    else:
        yyp_path = yyp_input

    if not os.path.exists(yyp_path) or not yyp_path.endswith(".yyp"):
        print(f"[!] Error: File '{yyp_path}' does not exist or is not a .yyp project!")
        return

    project_dir = os.path.dirname(os.path.abspath(yyp_path))
    print(f"[+] Project found: {yyp_path}")

    # 2. Compiler Output mode selection (VM vs YYC)
    print("\n[2] Select Output Compiler Mode:")
    print("  1. GMS2 VM  (Interpreted / Virtual Machine)")
    print("  2. GMS2 YYC (YoYo C++ Compiler)")
    mode_input = input("Select mode (1 or 2) [default 1]: ").strip()

    is_yyc = (mode_input == "2")
    mode_str = "GMS2 YYC (C++)" if is_yyc else "GMS2 VM (Interpreted)"
    print(f"[+] Selected mode: {mode_str}")

    # 3. Environment Deep Search
    print("\n[3] Deep searching for installed Igor CLI and GameMaker environment...")
    igor_path, runtime_path, prefabs_path, user_dir, licence_file = find_gamemaker_paths()

    if not igor_path or not os.path.exists(igor_path):
        igor_path = input("[?] Igor CLI not found automatically. Enter path to Igor.exe / Igor: ").strip(' "\'')

    if not runtime_path or not os.path.exists(runtime_path):
        runtime_path = input("[?] GameMaker Runtime path not found. Enter path (runtime-X.X.X folder): ").strip(' "\'')

    print(f"  * Igor CLI: {igor_path}")
    print(f"  * Runtime: {runtime_path}")
    if prefabs_path:
        print(f"  * Prefabs: {prefabs_path}")
    if licence_file:
        print(f"  * Licence: {licence_file}")

    # 4. Compile to Build_iOS unified directory via Igor
    output_xcode_dir = os.path.join(project_dir, "Build_iOS")
    os.makedirs(output_xcode_dir, exist_ok=True)

    print(f"\n[4] Compiling project to Build_iOS folder ({mode_str})...")

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
        print("[!] Error during Igor CLI compilation!")
        return

    print("\n[+] Xcode project compilation completed successfully!")

    # Locate generated .xcodeproj
    xcode_proj_dirs = glob.glob(os.path.join(output_xcode_dir, "**", "*.xcodeproj"), recursive=True)
    if xcode_proj_dirs:
        target_export_folder = os.path.dirname(xcode_proj_dirs[0])
        print(f"[+] Xcode project ready in: {target_export_folder}")
        try:
            if sys.platform == "win32":
                os.startfile(target_export_folder)
            else:
                subprocess.run(["open", target_export_folder])
        except Exception:
            pass
    else:
        target_export_folder = output_xcode_dir
        print(f"[+] Build folder: {output_xcode_dir}")

    # 5. Prompt for GitHub Actions .ipa packaging
    answer = input("\n[5] Do you want to build an unsigned .ipa file via GitHub Actions? (y/n): ").strip().lower()

    if answer not in ['y', 'yes', 'д', 'да']:
        print("[+] Finished Xcode project saved locally in Build_iOS folder!")
        return

    # 6. Check Git & Git LFS
    print("\n[6] Checking Git and Git LFS installation...")

    git_check = subprocess.run("git --version", shell=True, capture_output=True, text=True)
    if git_check.returncode != 0:
        print("[!] Error: Git is not installed on your computer!")
        print(" -> Please install Git from the official website: https://git-scm.com/")
        webbrowser.open("https://git-scm.com/downloads")
        return
    print(f"  * {git_check.stdout.strip()}")

    lfs_check = subprocess.run("git lfs --version", shell=True, capture_output=True, text=True)
    if lfs_check.returncode != 0:
        print("[!] Warning: Git LFS not detected. Installing Git LFS...")
        run_command("git lfs install")
    else:
        print(f"  * {lfs_check.stdout.strip()}")

    git_user = subprocess.run("git config user.name", shell=True, capture_output=True, text=True).stdout.strip()
    git_email = subprocess.run("git config user.email", shell=True, capture_output=True, text=True).stdout.strip()

    if not git_user or not git_email:
        print("\n[!] Warning: Git user name/email is not configured.")
        new_name = input("Enter your Git name: ").strip()
        new_email = input("Enter your Git email: ").strip()
        run_command(f'git config --global user.name "{new_name}"')
        run_command(f'git config --global user.email "{new_email}"')

    # 7. GitHub Repository setup prompt
    print("\n[7] GitHub Repository Configuration...")
    print("=" * 65)
    print("⚠️  RECOMMENDED: CREATE A NEW CLEAN REPOSITORY ON GITHUB!")
    print("    This protects your main source code repository from build artifacts.")
    print("    Create a new repository at: https://github.com/new")
    print("    Example URL: https://github.com/username/gms2-ios-build.git")
    print("=" * 65)

    repo_url = input("\nEnter your new GitHub Repository URL: ").strip()

    if not repo_url.startswith("http") and not repo_url.startswith("git@"):
        print("[!] Error: Invalid repository URL entered!")
        return

    # 8. Prepare repository files
    print("\n[8] Preparing repository and build files...")

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
    
    # Configure remote
    run_command("git remote remove origin", cwd=target_export_folder)
    run_command(f'git remote add origin "{repo_url}"', cwd=target_export_folder)
    run_command("git branch -M main", cwd=target_export_folder)

    print("\n[9] Indexing files locally (git add .)...")
    run_command("git add .", cwd=target_export_folder)
    run_command(f'git commit -m "Auto-generated Xcode project ({mode_str}) with GitHub Actions iOS build workflow by yearningss"', cwd=target_export_folder)
    
    print("\n[10] Uploading Git LFS resources to GitHub server (may take 1-3 minutes)...")
    print("⏳ Please wait for LFS object upload to complete 100%...")
    lfs_push_success = run_command("git lfs push origin main --all", cwd=target_export_folder)

    print("\n[11] Pushing branch to GitHub (git push origin main)...")
    push_success = run_command("git push -u origin main --force", cwd=target_export_folder)

    # 12. Verify receipt on remote
    print("\n[12] Verifying server receipt on GitHub...")
    fetch_success = run_command("git fetch origin main", cwd=target_export_folder)

    # 13. Clean temporary build caches
    print("\n[13] Cleaning up temporary build caches...")
    temp_cache = os.path.join(project_dir, "cache")
    if os.path.exists(temp_cache):
        try:
            shutil.rmtree(temp_cache)
            print("  * Cleaned temporary cache directory (cache/)")
        except Exception:
            pass
    
    actions_url = repo_url.rstrip(".git") + "/actions"
    
    # Print post-build instructions & open browser
    print_sideloadly_instructions(actions_url)
    webbrowser.open(actions_url)

if __name__ == "__main__":
    main()
