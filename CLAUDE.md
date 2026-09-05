# English Coach — 项目须知

给在本仓库工作的 Claude。**动手之前先读完。**

---

## 一、最重要的三条

1. **v2.15.12 是里程碑版本，当前运行良好。非必要不改动良好的部分。**
   改动前先说清楚会碰哪里、不碰哪里；改完验证已有功能没受影响。

2. **mac 相关代码一律不动。** mac 的深浅主题、下拉、滚动条经过长期打磨已经完美，
   踩过很多坑才到今天。所有主题相关函数的 `if sys.platform == "darwin":` 分支
   都在前面 `return`，只改非 mac 分支。改完要伪装 darwin 验证 mac 路径原样执行。

3. **回答简洁。** 不写万字长文、不写学术论文式的说明。
   **不要动不动就重新打包整套代码。** 先把问题聊清楚，确实需要更新时再更新。

---

## 二、项目概况

中英翻译 + 语音朗读 + 卡拉OK字幕的桌面应用。PyQt6 单文件，约 8700 行。

- 14 个翻译引擎（含 10 个 LLM）
- 双 TTS 后端：edge-tts（在线）/ Kokoro（离线本地）
- 逐词卡拉OK字幕、原文译文选区联动、翻译历史、文件导入导出
- 界面中英双语、深浅主题

作者 Strilen Liu，GPLv3，仓库 `StrilenLiu/EnglishCoach`。

**目录里只有源码。** `dist/`、`build/`、`_kokoro_stage/`、`.build-venv*/` 全在
`.gitignore` 里；编译产物走 GitHub Releases 手动上传，不进版本库。

---

## 三、关键文件

| 文件 | 说明 |
|---|---|
| `english_coach.py` | 主程序，单文件。版本号在 `APP_VERSION` |
| `Build Linux.sh` | Linux CPU 版构建（`BUILD_VARIANT=GPU` 切 GPU 变体） |
| `Build Linux GPU.sh` | GPU 版薄封装，复用上面那个 |
| `Build MacOS.sh` | 按 `uname -m` 自动分 Intel / Apple Silicon |
| `Build Windows.bat` / `Build Windows GPU.bat` | Windows CPU / GPU |
| `Install.sh` / `.command` / `.bat` + 对应 `Uninstall.*` | 三平台安装卸载脚本 |
| `gen_changelog.py` | 从主程序的 `CHANGELOG` 列表生成 `CHANGELOG.md` |
| `requirements.txt` / `-build.txt` / `-gpu.txt` | 运行 / 打包 / CUDA 依赖 |

---

## 四、代码里几处必须知道的设计

**`_ec_bootstrap_hf()`（文件顶部，约 47 行）**
必须在任何 `import huggingface_hub / transformers / kokoro` **之前**执行。
huggingface_hub 在模块导入时就把 endpoint 读成常量固定了，之后改环境变量无效。
它负责：找本地 Kokoro 模型（找到就完全离线）、大陆环境自动切 hf-mirror。
**不要把这段挪到函数内部或延后执行。**

**主题系统（非 mac）**
`_win_hybrid_qss()` + `_apply_win_palette()` + `setColorScheme()` 三者配合：
原生控件（复选框、滚动条、窗口底色）由 `setColorScheme` 和调色板驱动，
QSS 只绘制按钮、下拉闭合框、下拉弹出、滑杆、状态栏。
**绝不要给 QCheckBox 加任何样式表** —— 一旦加了，windows11 样式引擎会整体接管
渲染，指示器边线就没了。这个坑踩过很多次。

**启动与热切换必须做完全一样的事**
`_apply_style()`（启动）和 `apply_theme()`（热切换）要保持对称。历史上出过
"打开好、改主题坏、重启又好"，就是热切换漏了设调色板。

**`_log_error()` 是唯一的日志函数**，没有 `_log()`。曾因写错名字导致日志一直
为空却还提示"已记录到日志"。

**PyQt6 槽函数里未捕获的异常会直接 abort()**（表现为闪退）。
`_install_global_excepthook()` 是兜底，别删。

**`KaraokeHighlighter`（约 5336 行）** 的图层顺序：灰联动 → 蓝选区 → 卡拉OK 最上。
三种带背景的格式都显式带白字前景。

---

## 五、构建脚本的拦截机制

四个构建脚本都有**产物完整性拦截**：任何会让产物功能残缺的问题都**阻断编译**，
绝不"警告一下就假装成功"。

- `record_problem` 记录问题，`gate_check` 结算并以非 0 退出
- 检查点：torch 变体、Kokoro 模型与音色、Argos 模型、spaCy 模型、
  可执行文件、`_internal`、CUDA 组件、ctranslate2 依赖完整性、总体积下限
- `STRICT=0` 可强行忽略，**仅用于明知故犯的场景**

**新增功能如果引入了新的必需组件，要同步加拦截检查。**

---

## 六、平台差异备忘（都是踩坑换来的）

| 问题 | 结论 |
|---|---|
| Linux 上 `pip install torch` | **默认是 CUDA 版**，会拖进 12 个 nvidia 包。CPU 版必须走 `--index-url .../whl/cpu` |
| `ctranslate2` 的 Linux x86_64 轮子 | 硬链接自带的 cuDNN（DT_NEEDED），**删了 Argos 就完全加载不了** |
| PyQt6 6.10+ 的 Linux 轮子 | 要求 glibc 2.34，Debian 11 / Ubuntu 20.04 装不了。**Linux 钉 6.9.1** |
| Wayland | Qt 工具提示会触发协议错误崩溃，启动脚本和桌面项都回退到 `QT_QPA_PLATFORM=xcb` |
| `libxcb-cursor0` | Qt 6.5+ 必需但多数发行版不装，产物已捆绑那 4 个 xcb 小库（约 94KB） |
| `.desktop` 的 `Exec=` | 含空格的路径必须用**双引号**，反斜杠转义不合规、GNOME 会静默失败 |
| conda 环境 | CPU 与 GPU 变体要用**不同的 env**，否则 pip 见版本已满足就跳过安装，变体串味 |
| conda 里的 C 扩展 | 链接的是 conda 目录下的库，PyInstaller 要显式捆绑（如 `libexpat`），否则报 undefined symbol |
| PyInstaller + multiprocessing | 入口最前必须 `freeze_support()`，否则子进程会重新启动整个 app |

---

## 七、发版流程

1. 改 `APP_VERSION`，在主程序的 `CHANGELOG` 列表里加一条（**中英双语**，
   字段：`version` / `date` / `title` / `notes` / `title_en` / `notes_en`）
2. `python gen_changelog.py` 重新生成 `CHANGELOG.md`
3. 各平台分别编译（**PyInstaller 不支持交叉编译**）
4. 提交 + 打 tag + 推送
5. GitHub Releases 上传各平台产物，更新 README 里的下载直链

**Linux 建议在 Docker 里编**（`python:3.10-bullseye`，glibc 2.31），
这样产物能覆盖 Ubuntu 20.04 及以上。本机若是新系统，编出的包老系统跑不了。

---

## 八、验证习惯

改完至少确认这些：

```bash
python -m py_compile english_coach.py                    # 语法
QT_QPA_PLATFORM=offscreen python english_coach.py        # 能启动
bash -n "Build Linux.sh"                                  # 脚本语法
python gen_changelog.py --check                           # 文档同步
```

涉及主题的改动，额外验证：反复切换深浅色多次、主界面与设置窗下拉都打开一遍、
伪装 darwin 确认 mac 路径未被触及。
