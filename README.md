# English Coach 英语导师

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

一款跨平台（macOS / Windows）的英语学习桌面工具：**多引擎翻译 + 双引擎朗读 + 卡拉OK跟读字幕**。
A cross-platform desktop English-learning tool: multi-engine translation, online/offline TTS with karaoke-style word highlighting.

![screenshot](assets/screenshot.png)

## ✨ 功能特性
- **14 个翻译引擎**：Google / Google API / DeepL / Argos 纯离线，以及 DeepSeek、GPT、Gemini、Claude、GLM、文心一言、豆包、通义千问、Kimi、混元 等 LLM 引擎（自备 API Key）
- **多风格翻译**：LLM 引擎下单词给出多种译法，句子按书面 / 口语 / 正式等风格分类
- **双引擎朗读**：edge-tts 线上嗓音 + Kokoro 本地离线模型，原文/译文独立音频缓存
- **卡拉OK字幕**：逐词青绿高亮跟随朗读进度，支持只朗读选中区域
- **原文↔译文选区联动**：选中一侧，另一侧自动灰色高亮对应句
- **文件导入导出**：txt / md / docx / pdf 导入翻译，docx 保留段落结构导出
- **数字/符号特殊翻译**：88 → 逐位拼读 + 数学读法（中英双式，支持小数）
- 翻译历史、多格式下载、深色界面、Mac/Win11 原生胶囊滚动条

## 🚀 快速开始
**源码运行**
```bash
git clone https://github.com/StrilenLiu/EnglishCoach.git
cd EnglishCoach
pip install -r requirements.txt
python english_coach.py
```
**打包安装包**：直接运行仓库根目录的构建脚本（会自动创建 conda 环境、安装依赖、下载模型并打包）：
- macOS：`bash "Build MacOS.sh"`
- Windows：双击 `Build Windows.bat`（NVIDIA GPU 加速版用 `Build Windows GPU.bat`）

## 📦 离线模型
离线翻译与离线朗读的模型**不包含在仓库中**（体积大），构建脚本会自动下载，也可手动放置：
- Argos 翻译模型 → `~/EnglishCoach Models/Argos/`
- Kokoro 朗读模型 → `~/EnglishCoach Models/Kokoro/`

## 🔑 API Key
LLM 翻译引擎需在「设置」中填入你自己的 API Key，Key 仅保存在本机、不上传。Google 线上与 Argos 离线无需 Key。

## ☕ 支持作者 / Support
纯自愿打赏，不解锁任何功能，软件永远自由：
- 爱发电：<https://afdian.com/a/Strilen> <!-- TODO: 建好爱发电主页后确认此链接 -->
- Buy Me a Coffee：<https://buymeacoffee.com/strilenliu> <!-- TODO: 创建后替换为实际链接 -->
- 支付宝：<img src="assets/alipay.png" width="180" alt="支付宝收款码"/> <!-- TODO: 放入收款码图片 assets/alipay.png -->

## 📄 许可证 License
本项目以 **GNU GPL v3 或更高版本** 发布（见 [LICENSE](LICENSE)）。
依赖 [PyQt6](https://riverbankcomputing.com/software/pyqt/)（GPLv3）与 [edge-tts](https://github.com/rany2/edge-tts)（GPLv3）；线上朗读与免费 Google 翻译调用的是面向个人的公开接口，请以个人学习用途使用。

## 👤 作者 Author
**Strilen Liu** · <https://www.strilen.com> · vfx@strilen.com

## English
English Coach is a GPLv3 desktop app (PyQt6) for English learners: 14 translation engines (incl. offline Argos & major LLMs with your own keys), online (edge-tts) + offline (Kokoro) text-to-speech with karaoke word highlighting, bidirectional sentence linkage, docx/pdf import & export, and number/symbol reading modes. Build scripts for macOS and Windows are included; offline models are downloaded automatically at build time.
