# English Coach 英语导师

> 中英翻译 + 语音朗读 + 卡拉OK字幕的桌面应用
> A desktop app for Chinese-English translation, text-to-speech and karaoke-style subtitles.

**当前版本 / Current version: v2.15.12**

![English Coach](screenshot.png)

---

## 简介 / Overview

English Coach 是一款桌面翻译与朗读工具：14 个翻译引擎（含 10 个大模型引擎）、双语音合成后端（在线 edge-tts / 离线 Kokoro）、逐词卡拉OK字幕、原文译文选区联动、翻译历史与文件导入导出。界面支持中英双语与深浅主题。

English Coach is a desktop translation and speech tool. It bundles 14 translation engines — 10 of them powered by large language models — two text-to-speech backends (online edge-tts and offline Kokoro), word-by-word karaoke subtitles driven by real timestamps, two-way selection linking between the source and target panes, a searchable translation history, and file import/export. The interface is fully bilingual (Chinese/English) and follows light or dark themes.

---

## 用户须知 / For Users

### 下载即用，无需配置环境 / Download and run — no setup

**无需安装 Python、依赖库或 conda** —— 解释器与全部依赖已打包进程序，下载解压后双击即可运行。

**No Python, no dependencies, no conda required.** The interpreter and every library are bundled into the app. Download the archive for your platform, unpack it, and double-click to run. Nothing is installed system-wide, and removing the folder removes the program.

### 系统要求 / System Requirements

| 平台 / Platform | 要求 / Requirement |
|---|---|
| **macOS (Intel)** | macOS 11.0 Big Sur 或更新<br>macOS 11.0 Big Sur or newer |
| **macOS (Apple Silicon)** | macOS 12.0 或更新，原生 arm64<br>macOS 12.0 or newer, native arm64 |
| **Windows** | 64 位 Windows 10 / 11<br>64-bit Windows 10 or 11 |
| **Linux** | glibc 2.31 或更新（Ubuntu 20.04 及以上同级发行版）<br>glibc 2.31 or newer (Ubuntu 20.04-era distributions and later) |
| **磁盘空间 / Disk** | 建议预留 2–3GB（含离线朗读模型）<br>Allow 2–3GB including the offline speech model |

**GPU 版 / GPU edition**：打包了 CUDA 组件，体积明显更大（分卷压缩上传），仅在有 NVIDIA 显卡的 Windows 机器上才有意义。没有独立显卡请下载 CPU 版。

**GPU edition**: bundles CUDA components and is considerably larger, so it is uploaded as a multi-part archive. It is only worth downloading on a Windows machine with an NVIDIA graphics card — otherwise use the CPU edition, which has identical features and merely runs offline speech synthesis more slowly.

### 各平台安装与启动 / Installing and launching

**Windows**

解压后双击 `EnglishCoach.exe` 即可。GPU 版为分卷压缩包，请把所有分卷（`.7z.001`、`.7z.002` …）下载到**同一目录**，然后右键第一个分卷用 7-Zip 解压。

Unpack the archive and double-click `EnglishCoach.exe`. The GPU edition ships as a multi-part 7-Zip archive: download **every** part (`.7z.001`, `.7z.002`, …) into the **same folder**, then right-click the first part and extract with 7-Zip. Extracting only the first part will fail.

**macOS**

把 `EnglishCoach.app` 拖入「应用程序」文件夹后启动。请按芯片类型选择对应下载：Intel 机型选 `MacOS-Intel`，M 系列芯片选 `MacOS-AppleSilicon`。

Drag `EnglishCoach.app` into your Applications folder and launch it. Choose the download that matches your chip: `MacOS-Intel` for Intel Macs, `MacOS-AppleSilicon` for M-series Macs. The Apple Silicon build runs natively and does not need Rosetta.

**Linux**

下载 `EnglishCoach-<版本>-Linux-x64.tar.gz`，解压后运行启动脚本：

Download `EnglishCoach-<version>-Linux-x64.tar.gz`, extract it, and run the launcher script:

```bash
tar -xzf EnglishCoach-2.15.12-Linux-x64.tar.gz
cd EnglishCoach-2.15.12-Linux-x64
chmod +x EnglishCoach        # 首次运行前加执行权限 / make it executable once
./EnglishCoach
```

若提示缺少系统库，请按发行版安装 Qt 运行所需的组件：

If the program reports a missing system library, install the components Qt needs for your distribution:

```bash
# Debian / Ubuntu
sudo apt install libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 libgl1

# Fedora / RHEL
sudo dnf install xcb-util-cursor libxkbcommon-x11 mesa-libGL

# Arch
sudo pacman -S xcb-util-cursor libxkbcommon-x11
```

其中 `libxcb-cursor0` 是最常见的缺失项 —— Qt 6 必须依赖它，而许多桌面环境默认不装。

`libxcb-cursor0` is by far the most common missing piece: Qt 6 requires it, yet many desktop environments do not install it by default.

想在应用菜单里显示图标，可自建一个桌面项：

To make the app appear in your application menu, create a desktop entry:

```bash
cat > ~/.local/share/applications/englishcoach.desktop << EOF
[Desktop Entry]
Type=Application
Name=English Coach
Exec=/绝对路径/EnglishCoach
Icon=/绝对路径/icon_1024.png
Categories=Education;Utility;
EOF
```

### 未签名应用提示 / Unsigned App Warning

本程序未做代码签名（Apple 开发者证书为年费制），首次打开可能被系统拦截：

This app is not code-signed — Apple's Developer ID requires a paid yearly membership — so the system may block it on first launch:

- **macOS**：「系统设置 → 隐私与安全性」点『仍要打开』，或在终端执行下面这条命令移除隔离标记。
  Go to System Settings → Privacy & Security and click **Open Anyway**, or remove the quarantine flag from Terminal:
  ```bash
  sudo xattr -rd com.apple.quarantine /Applications/EnglishCoach.app
  ```
- **Windows**：SmartScreen 提示时点『更多信息 → 仍要运行』。
  At the SmartScreen prompt, click **More info → Run anyway**.
- **Linux**：无签名机制，只需确认文件有执行权限。
  Linux has no equivalent gatekeeper; just make sure the file is executable.

### 哪些需要联网 / What Needs a Network Connection

| 类别 / Category | 说明 / Details |
|---|---|
| **已打包，立即可用**<br>Bundled, works immediately | 程序本体与全部依赖库<br>The program itself and every bundled library |
| **首次使用下载一次**<br>Downloaded once on first use | Kokoro 离线朗读模型（约 330MB）、Argos 离线语言包；下载后完全离线<br>The Kokoro offline speech model (~330MB) and Argos language packs; fully offline afterwards |
| **始终需要联网**<br>Always needs a network | 在线翻译引擎、在线朗读<br>Online translation engines and online text-to-speech |
| **需自备 API Key**<br>Requires your own API key | LLM 引擎在云端运行，本地不打包任何大模型<br>LLM engines run in the cloud; no language model is bundled locally |

### 中国大陆用户须知 / Notes for Users in Mainland China

- **无需 VPN 即可使用**：国内 LLM 引擎（DeepSeek、文心一言、豆包、通义千问、混元、智谱 GLM）与 Argos 离线语言包。
  **Works without a VPN**: the Chinese LLM engines (DeepSeek, ERNIE, Doubao, Qwen, Hunyuan and GLM) and the Argos offline language packs are all reachable directly.
- **Kokoro 朗读模型**：托管在 Hugging Face，大陆无法直连。程序会按系统区域自动改用 `hf-mirror.com` 公益镜像，通常无需 VPN 即可完成首次下载；如需指定其它镜像，设置环境变量 `HF_ENDPOINT` 即可覆盖。
  **The Kokoro speech model** is hosted on Hugging Face, which is not directly reachable from mainland China. The app detects the system region and automatically falls back to the `hf-mirror.com` community mirror, so the one-time download normally succeeds without a VPN. Set the `HF_ENDPOINT` environment variable to point at a different mirror.
- **需要 VPN**：Google 翻译、DeepL 翻译，以及在线朗读（微软 Edge 嗓音）。
  **Needs a VPN**: Google Translate, DeepL, and online text-to-speech (Microsoft Edge voices).

---

## 主要功能 / Features

- **14 个翻译引擎 / 14 translation engines**
  Google（免费）、Google Cloud、DeepL、Argos（离线），以及 DeepSeek、GPT、Gemini、Claude、GLM、文心一言、豆包、通义千问、Kimi、混元。
  Google (free), Google Cloud, DeepL and Argos (fully offline), plus ten LLM engines: DeepSeek, GPT, Gemini, Claude, GLM, ERNIE, Doubao, Qwen, Kimi and Hunyuan. Each engine keeps its own API key, and you can switch between them at any time.
- **多风格翻译 / Multi-style translation**
  LLM 引擎下同时给出书面、口语、俚语、美式英式等多种译法。
  With an LLM engine selected, one request returns several renderings at once — formal, conversational, idiomatic, and American versus British — so you can compare register rather than settle for a single output.
- **双语音后端 / Dual TTS backends**
  edge-tts（在线，多语言嗓音）与 Kokoro（离线，本地推理）。
  edge-tts provides a wide range of online voices across languages, while Kokoro runs entirely on your machine after its first download — useful offline, and free of any per-character quota.
- **卡拉OK字幕 / Karaoke subtitles**
  按真实词级时间戳逐词高亮，支持选区朗读与进度条拖动定位。
  Words highlight one by one against real word-level timestamps rather than an estimated pace. You can read aloud just a selection, and dragging the progress slider re-renders the highlight at the matching word.
- **选区联动 / Selection linking**
  选中一侧文字，另一侧自动高亮对应内容。
  Selecting text in one pane highlights the corresponding span in the other, which makes it easy to check how a particular phrase was rendered.
- **文件导入导出 / File import & export**
  txt / docx / pdf 导入，txt / md / docx / json / pdf 导出。
  Import from txt, docx and pdf; export to txt, md, docx, json and pdf, with the source and translation kept side by side.
- **翻译历史 / Translation history**
  按天分组、可重新载入与导出。
  Entries are grouped by day, can be reloaded into the editor, and can be exported as a whole.
- **界面 / Interface**
  中英双语、深浅主题跟随系统、极简模式、窗口置顶。
  Bilingual interface, light and dark themes that can follow the system, a compact minimal mode, and an always-on-top option.

---

## 从源码运行 / Running from Source

```bash
# 1. 创建环境（推荐 Python 3.10+）
#    Create an environment (Python 3.10 or newer recommended)
conda create -n EnglishCoach python=3.10
conda activate EnglishCoach

# 2. 安装运行依赖 / Install runtime dependencies
pip install -r requirements.txt

# 3. 安装 spaCy 英文模型（Kokoro 分词需要，pip 索引中没有）
#    Install the spaCy English model (needed by Kokoro, not on PyPI)
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# 4. 运行 / Run
python english_coach.py
```

**Windows GPU 用户**：先装 CUDA 版 torch，再装其余依赖，避免被 CPU 版覆盖。

**Windows GPU users**: install CUDA torch first so the CPU wheel cannot overwrite it, then the rest:

```bash
pip install -r requirements-gpu.txt
pip install -r requirements.txt
```

### 依赖文件说明 / About the requirements files

| 文件 / File | 用途 / Purpose |
|---|---|
| `requirements.txt` | 运行本程序所需的全部库，已用平台标记区分 Windows / macOS / Linux<br>Everything needed to run the app, with environment markers separating Windows, macOS and Linux |
| `requirements-build.txt` | 额外的打包工具（PyInstaller、Pillow），仅自行编译时需要<br>Extra packaging tools (PyInstaller, Pillow) — only needed when building installers |
| `requirements-gpu.txt` | Windows + NVIDIA 显卡专用的 CUDA 版 torch<br>CUDA torch for Windows machines with an NVIDIA GPU |

平台差异已写进 `requirements.txt` 的标记，无需手动挑选：Intel Mac 会拿到钉死的 PyQt6 6.4.2（兼容 Big Sur），Apple Silicon、Windows 与 Linux 拿最新版；`pyobjc-framework-Cocoa` 只在 macOS 上安装。

Platform differences are encoded as markers, so you do not need to pick anything by hand: Intel Macs receive the pinned PyQt6 6.4.2 that keeps Big Sur support, while Apple Silicon, Windows and Linux take the current release, and `pyobjc-framework-Cocoa` installs on macOS only.

**关于版本钉死 / On the pinned versions**：`torch`、`transformers`、`ctranslate2` 的版本组合经过实机验证，随意升级很可能破坏 Kokoro 离线朗读或 Argos 离线翻译。

The `torch`, `transformers` and `ctranslate2` versions are pinned to a combination validated on real machines. Upgrading them casually is likely to break Kokoro offline speech or Argos offline translation.

---

## 自行编译 / Building

仓库内含四个构建脚本，版本号自动从 `english_coach.py` 的 `APP_VERSION` 提取：

Four build scripts are included. Each extracts the version automatically from `APP_VERSION` in `english_coach.py`, so you never edit a version string in two places:

| 脚本 / Script | 产物 / Output |
|---|---|
| `Build MacOS.sh` | `dist/MacOS-Intel/` 或 `dist/MacOS-AppleSilicon/`（按 `uname -m` 自动判断）<br>`dist/MacOS-Intel/` or `dist/MacOS-AppleSilicon/`, selected automatically via `uname -m` |
| `Build Windows.bat` | `dist/Windows-x64-CPU/` |
| `Build Windows GPU.bat` | `dist/Windows-x64-GPU/`（CUDA）<br>`dist/Windows-x64-GPU/` (CUDA) |
| `Build Linux.sh` | `dist/Linux-x64/` 与 tar.gz 压缩包<br>`dist/Linux-x64/` plus a tar.gz archive |

**PyInstaller 不支持交叉编译** —— 每个平台的产物必须在该平台上编译。

**PyInstaller cannot cross-compile.** Each platform's binary must be produced on that platform: build the Windows editions on Windows, the macOS editions on the matching Mac, and the Linux build on Linux.

**Windows 编译提示 / Windows build note**：若 `ctranslate2` 导入失败，请先安装
[Visual C++ Redistributable (x64)](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist)。

If `ctranslate2` fails to import during the build, install the Visual C++ Redistributable (x64) first.

**Linux 编译提示 / Linux build note**：建议在较老的发行版（如 Ubuntu 20.04）上编译。glibc 向下不兼容，用新系统编出的产物无法在老系统上运行，反之则可以。

Build on an older distribution such as Ubuntu 20.04. glibc is forward-compatible but not backward-compatible, so a binary built on a new system will refuse to start on older ones, while a binary built on an old system runs everywhere newer.

---

## 隐私 / Privacy

API Key 仅保存在本机（QSettings），不会上传。翻译历史与运行日志保存在系统用户数据目录（Windows `%APPDATA%`、macOS `~/Library/Application Support`、Linux `~/.local/share`）。程序不做任何遥测或使用统计。

API keys are stored locally through QSettings and are never transmitted anywhere except to the translation service you explicitly choose. Translation history and runtime logs live in the standard user-data directory for your system: `%APPDATA%` on Windows, `~/Library/Application Support` on macOS, and `~/.local/share` on Linux. The app performs no telemetry and collects no usage statistics.

---

## 支持作者 / Support the Author

如果这个程序对你有帮助，欢迎请作者喝杯咖啡：

If you find this program useful, you are welcome to buy the author a coffee:

<img src="alipay.png" alt="支付宝 / Alipay" width="220">

**支付宝 / Alipay**

（更多打赏渠道正在准备中 / More options are being set up.）

---

## 许可与作者 / License & Author

- **许可 / License**：GPLv3
- **作者 / Author**：Strilen Liu
- **网站 / Website**：[www.strilen.com](https://www.strilen.com)
- **邮箱 / Email**：vfx@strilen.com

---

## 更新记录 / Changelog

完整的版本历史见 [CHANGELOG.md](CHANGELOG.md)，中英双语，涵盖全部 107 个版本。

The full bilingual version history is in [CHANGELOG.md](CHANGELOG.md), covering all 107 releases.

该文件由 `gen_changelog.py` 从 `english_coach.py` 里的 `CHANGELOG` 自动生成 —— 程序内的「关于 → 更新记录」与该文件读的是同一份数据，不会脱节。发布新版前运行：

The file is generated by `gen_changelog.py` from the `CHANGELOG` list inside `english_coach.py`, which is the same data the in-app "What's New" dialog reads, so the two can never drift apart. Before publishing a release, run:

```bash
python gen_changelog.py            # 重新生成 / regenerate
python gen_changelog.py --check    # 只检查是否最新 / check only
```

---

## 维护提示 / Maintenance Note

> **每次版本更新时，请同步更新本文件顶部的版本号、运行 `python gen_changelog.py` 重新生成 CHANGELOG.md，并检查上述说明是否仍然准确**（尤其是系统要求、模型下载方式、大陆访问情况与构建脚本产物名）。
>
> **On every release, update the version number at the top of this file** and verify that the notes above are still accurate — especially the system requirements, model download behaviour, mainland China access notes, and build script outputs.
