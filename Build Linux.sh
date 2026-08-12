#!/bin/bash
# ============================================================================
#  EnglishCoach · Linux 一键编译脚本
#  PyInstaller 打包（onedir），内置 Argos 中英离线模型 + 可选 Kokoro 模型。
#  产物: dist/Linux-x64/English Coach/  与  dist/Linux-x64/EnglishCoach-<版本>-Linux-x64.tar.gz
#        (版本自动取自 APP_VERSION)
#
#  重要（glibc 向下兼容）：请在“尽量老”的发行版上编译（推荐 Ubuntu 20.04），
#  在老系统上编出的产物能在新系统上运行，反之不行。x86_64 二进制在
#  Ubuntu/Debian/Fedora/RedHat 等各发行版通用，无需逐个发行版编译。
# ============================================================================

set -e

APP_NAME="English Coach"
# 版本号自动从 english_coach.py 提取(单一事实来源)
VERSION=$(sed -n 's/^APP_VERSION = "\(.*\)"/\1/p' english_coach.py | head -1)
[ -z "$VERSION" ] && VERSION="0.0.0"
MAIN="english_coach.py"
CONDA_ENV="EnglishCoach"
# CPU / GPU 变体（由 Build Linux GPU.sh 覆盖为 GPU）
BUILD_VARIANT="${BUILD_VARIANT:-CPU}"
if [ "$BUILD_VARIANT" = "GPU" ]; then
    TAG="Linux-x64-GPU"
    # CUDA 12.1 版 torch，与 Windows GPU 版思路一致
    TORCH_SPEC="torch==2.2.2"
    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
    VENV_DIR="${VENV_DIR:-.build-venv-gpu}"
    # GPU 版可执行文件与安装后的菜单项都叫 "English Coach GPU"，
    # 可与 CPU 版并存互不覆盖
    APP_NAME="English Coach GPU"
else
    TAG="Linux-x64-CPU"
    TORCH_SPEC="torch==2.2.2"
    TORCH_INDEX="https://download.pytorch.org/whl/cpu"
    VENV_DIR="${VENV_DIR:-.build-venv}"
fi
# 多镜像：清华优先，失败回退官方源
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_FALLBACK="https://pypi.org/simple"

pip_install () {
    "$PY" -m pip install "$@" -i "$PIP_MIRROR" || \
    "$PY" -m pip install "$@" -i "$PIP_FALLBACK"
}

echo "==> [1/7] 准备 Python 环境"
# 有 conda 就用指定的 conda 环境；没有(如 Docker / CI 容器)则直接用当前 Python。
# 这样在 python:3.10-bullseye 这类镜像里可以零配置直接编译，
# 而 glibc 2.31 的底座正好保证产物能兼容 Ubuntu 20.04 及以上。
USE_CONDA=0
if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base 2>/dev/null)"
    for cand in "$CONDA_BASE" "$HOME/anaconda3" "$HOME/miniconda3" \
                "/opt/anaconda3" "/opt/miniconda3"; do
        if [ -n "$cand" ] && [ -f "$cand/etc/profile.d/conda.sh" ]; then
            source "$cand/etc/profile.d/conda.sh"; break
        fi
    done
    if conda env list | grep -qE "(^|/)${CONDA_ENV}(\s|$)"; then
        conda activate "${CONDA_ENV}"
        if [ "${CONDA_DEFAULT_ENV}" != "${CONDA_ENV}" ]; then
            echo "✗ conda 环境 ${CONDA_ENV} 激活失败，中止以免装错环境"; exit 1
        fi
        USE_CONDA=1
        echo "    使用 conda 环境: ${CONDA_DEFAULT_ENV}"
    else
        echo "    ! 未找到 conda 环境 ${CONDA_ENV}，改用当前 Python"
        echo "      如需使用 conda: conda create -n ${CONDA_ENV} python=3.12 -y"
    fi
else
    echo "    未检测到 conda，使用当前 Python(适用于 Docker / CI)"
fi

# 统一确定解释器：conda 环境下是 python，否则用虚拟环境里的 python。
# 建虚拟环境有两个原因：一是 Debian/Ubuntu 的系统 Python 受 PEP 668 保护，
# 直接 pip 安装会被拒绝(externally-managed-environment)；二是避免把一堆
# 依赖装进系统目录污染环境。
if [ "$USE_CONDA" = "1" ]; then
    PY=python
else
    BASE_PY="$(command -v python3 || command -v python)"
    if [ -z "$BASE_PY" ]; then
        echo "✗ 未找到 Python 解释器"; exit 1
    fi
    # 兜底：VENV_DIR 不该为空，为空时用默认值而不是让后续路径拼成 "/bin/python"
    [ -z "${VENV_DIR:-}" ] && VENV_DIR=".build-venv"
    # 已存在的虚拟环境若是低版本 Python 建的(比如换了容器/基础镜像)，
    # 直接复用会一直卡在版本检查上，这里自动识别并重建。
    if [ -x "${VENV_DIR}/bin/python" ]; then
        if "${VENV_DIR}/bin/python" -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
            echo "    复用已有虚拟环境: ${VENV_DIR}"
        else
            _old_ver="$("${VENV_DIR}/bin/python" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null)"
            echo "    已有虚拟环境是 Python ${_old_ver}(低于 3.10)，删除重建"
            rm -rf "${VENV_DIR}"
        fi
    fi
    if [ ! -x "${VENV_DIR}/bin/python" ]; then
        # 基础解释器本身也要够新，否则建出来的还是旧版本
        if ! "$BASE_PY" -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
            echo "✗ 当前 Python 为 $("$BASE_PY" -c 'import sys;print(sys.version.split()[0])')，需要 3.10 或更新"
            echo "  提示：ubuntu:20.04 镜像自带 Python 3.8，请改用 python:3.10-bullseye"
            echo "        docker run --rm -it -v \"%cd%\":/src -w /src python:3.10-bullseye bash"
            exit 1
        fi
        echo "    创建虚拟环境: ${VENV_DIR}"
        "$BASE_PY" -m venv "${VENV_DIR}" || {
            echo "✗ 创建虚拟环境失败。Debian/Ubuntu 上可能需要： apt install -y python3-venv"
            exit 1
        }
    fi
    PY="$(cd "${VENV_DIR}/bin" && pwd)/python"
fi
if [ -z "$PY" ] || [ ! -x "$PY" ]; then
    echo "✗ 未找到可用的 Python 解释器"; exit 1
fi
echo "    ----------------------------------------"
echo "    Python 路径: $PY"
"$PY" --version
echo "    ----------------------------------------"
# 版本下限检查：程序需要 3.10+
"$PY" - <<'PYCHK' || exit 1
import sys
if sys.version_info < (3, 10):
    print(f"\u2717 需要 Python 3.10 或更新，当前为 {sys.version.split()[0]}")
    sys.exit(1)
PYCHK

echo "==> [2/7] 升级 pip 与打包工具"
pip_install -U pip
pip_install pyinstaller

# —— 系统级工具检查 ——
# PyInstaller 在 Linux 上需要 objdump(来自 binutils) 分析二进制依赖，缺了会在
# 打包阶段才报错。binutils 不是 Python 包，pip / requirements.txt 装不了它，
# 但 conda 可以。这里提前检查，能自动装就自动装。
if ! command -v objdump >/dev/null 2>&1; then
    echo "    缺少 objdump（PyInstaller 必需，来自 binutils），尝试自动安装…"
    _ok=0
    if [ "$USE_CONDA" = "1" ] && command -v conda >/dev/null 2>&1; then
        conda install -y -q binutils >/dev/null 2>&1 && _ok=1
        [ "$_ok" = "1" ] && echo "    已通过 conda 安装 binutils"
    fi
    if [ "$_ok" = "0" ] && command -v apt-get >/dev/null 2>&1; then
        if [ "$(id -u)" = "0" ]; then
            apt-get install -y -qq binutils >/dev/null 2>&1 && _ok=1
        else
            sudo -n apt-get install -y -qq binutils >/dev/null 2>&1 && _ok=1
        fi
        [ "$_ok" = "1" ] && echo "    已通过 apt 安装 binutils"
    fi
    if [ "$_ok" = "0" ] || ! command -v objdump >/dev/null 2>&1; then
        echo ""
        echo "✗ 缺少 objdump，PyInstaller 无法打包。请手动安装后重试："
        echo ""
        echo "    conda 环境 : conda install -y binutils"
        echo "    Debian/Ubuntu: sudo apt install -y binutils"
        echo "    Fedora/RHEL  : sudo dnf install -y binutils"
        echo "    Arch         : sudo pacman -S binutils"
        echo ""
        exit 1
    fi
fi

echo "==> [3/7] 安装运行依赖"
# PyQt6 版本必须钉死：6.10 起的 Linux 轮子是 manylinux_2_34，要求 glibc >= 2.34，
# 在 Debian 11 / Ubuntu 20.04(glibc 2.31) 上装不了 —— pip 会退去下源码包现场编译，
# 而编译 PyQt6 需要 qmake 工具链，最终报 PyProjectOptionException('qmake')。
# 6.9.x 的轮子是 manylinux_2_28(glibc >= 2.28)，是能在 2.31 底座上安装的最新版本。
# 用它编出的产物可覆盖 Ubuntu 20.04 及以上；若改用 6.10+，最低要求会抬到 glibc 2.34，
# 把 Ubuntu 20.04 与 22.04 的用户都挡在外面。
PYQT_VER="${PYQT_VER:-6.9.1}"
echo "    PyQt6 ${PYQT_VER}(manylinux_2_28，兼容 glibc 2.28+)"
# --only-binary 强制使用预编译轮子：装不上就立刻报错，
# 而不是悄悄退去源码编译、跑很久再失败。
"$PY" -m pip install --only-binary :all: \
    "PyQt6==${PYQT_VER}" "PyQt6-Qt6==${PYQT_VER}" "PyQt6-sip" -i "$PIP_MIRROR" || \
"$PY" -m pip install --only-binary :all: \
    "PyQt6==${PYQT_VER}" "PyQt6-Qt6==${PYQT_VER}" "PyQt6-sip" -i "$PIP_FALLBACK" || {
    echo "✗ PyQt6 ${PYQT_VER} 预编译轮子安装失败"
    echo "  本机 glibc: $(ldd --version 2>/dev/null | head -1)"
    echo "  需要 glibc >= 2.28。若底座过旧，可试更低版本： PYQT_VER=6.8.1 bash \"Build Linux.sh\""
    exit 1
}
# —— Argos 离线翻译：与其它平台一致的兼容版本组合 ——
pip_install "setuptools<81"
pip_install "numpy<2"
pip_install "sentencepiece==0.2.0"
pip_install "ctranslate2==4.3.1"
"$PY" -m pip install "argostranslate==1.9.6" --no-deps -i "$PIP_MIRROR" || \
"$PY" -m pip install "argostranslate==1.9.6" --no-deps -i "$PIP_FALLBACK"
pip_install sacremoses
pip_install -U edge-tts

# Kokoro 本地离线 TTS（Linux x86_64 与 mac 用同一套钉死版本，确保行为一致）
echo "    安装 Kokoro 离线 TTS 依赖..."
# 关键：Linux 上 PyPI 的 torch 默认就是【CUDA 版】，还会自动拖进 12 个 nvidia-* 包
# (cudnn / cublas / cusparse / nccl 等)，能让 CPU 版产物凭空多出好几 GB。
# Windows 与 macOS 的默认轮子本就是 CPU 版，只有 Linux 有这个行为，
# 因此两个变体都必须【显式】指定索引，不能依赖默认。
echo "    变体 ${BUILD_VARIANT}：使用索引 ${TORCH_INDEX}"
"$PY" -m pip install "${TORCH_SPEC}" --index-url "${TORCH_INDEX}" || {
    echo "    ! 指定索引安装失败，回退到默认源"
    [ "$BUILD_VARIANT" = "CPU" ] && echo "      注意：默认源在 Linux 上是 CUDA 版，产物会明显变大"
    pip_install "${TORCH_SPEC}"
}
# 校验：CPU 版不该带 +cu，GPU 版必须带。提前发现，不必等打包完才看出体积异常。
BUILD_VARIANT="$BUILD_VARIANT" "$PY" - <<'TORCHCHK'
import os, sys
want = os.environ.get("BUILD_VARIANT", "CPU")
try:
    import torch
    v = torch.__version__
    is_cuda = ("+cu" in v) or ("cu1" in v)
    print(f"    torch {v}")
    if want == "CPU" and is_cuda:
        print("    [!] 警告：CPU 版却装成了 CUDA 版 torch，产物会大出数 GB")
        print("        多为 pip 全局镜像源劫持了 --index-url，可试 --no-cache-dir")
    elif want == "GPU" and not is_cuda:
        print("    [!] 警告：GPU 版却装成了 CPU 版 torch，将【无法使用显卡加速】")
        print("        请检查 CUDA 索引是否可达")
    else:
        print(f"    已确认为 {want} 版")
except Exception as e:
    print(f"    [!] 无法导入 torch: {e}")
    sys.exit(1)
TORCHCHK
pip_install "transformers==4.40.2"
pip_install kokoro soundfile
pip_install lameenc
pip_install python-docx pypdf pdfplumber reportlab num2words
pip_install ordered_set addict regex pydantic loguru
pip_install pypinyin jieba cn2an "misaki[zh]" || pip_install pypinyin jieba cn2an
# misaki 英文 G2P 需要 spaCy 英文模型。它不在 PyPI（走 GitHub Releases），
# 镜像会返回 0 字节占位导致 "Wheel is invalid" 报错。先检查是否已安装：
# 已装则跳过，未装才安装——优先官方 GitHub wheel，失败再退回 pip。
if "$PY" -c "import en_core_web_sm" >/dev/null 2>&1; then
  echo "  ✓ en_core_web_sm 已安装，跳过"
else
  "$PY" -m pip install \
    "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" \
    || pip_install en_core_web_sm \
    || echo "  ⚠ en_core_web_sm 预装失败，首次离线英文朗读会自动下载（需联网）"
fi
"$PY" -c "import torch,transformers,kokoro;print('  ✓ Kokoro 依赖链 OK, torch',torch.__version__,'transformers',transformers.__version__)" \
  || echo "  ⚠ Kokoro 依赖校验未通过，离线朗读可能不可用"
# espeak-ng 是 Kokoro 英文 G2P 的后备依赖（Linux 用系统包管理器）
if ! command -v espeak-ng >/dev/null 2>&1; then
    echo "    提示：可选安装 espeak-ng（Debian/Ubuntu: sudo apt install espeak-ng；"
    echo "          Fedora/RedHat: sudo dnf install espeak-ng），Kokoro 英文音素化更稳。"
fi

echo "==> [4/7] 预下载 Kokoro 模型（约 330MB，首次较慢，可离线跳过）"
"$PY" - <<'PYEOF' || echo "  ⚠ Kokoro 模型预下载失败，离线英文嗓音在无网时将不可用"
import os
try:
    from huggingface_hub import snapshot_download
    target = os.path.expanduser("~/EnglishCoach Models/Kokoro")
    os.makedirs(target, exist_ok=True)
    snapshot_download(repo_id="hexgrad/Kokoro-82M", local_dir=target)
    print("  ✓ Kokoro 模型已就绪:", target)
except Exception as e:
    print("  Kokoro 预下载异常:", e)
    raise
PYEOF

echo "==> [5/7] 校验离线翻译依赖"
if ! "$PY" -c "import ctranslate2, sentencepiece" 2>/dev/null; then
    echo "✗ ctranslate2 / sentencepiece 导入失败。"
    echo "  请确认用了预编译包： pip install 'sentencepiece==0.2.0' 'ctranslate2==4.3.1' --only-binary :all:"
    exit 1
fi
echo "    离线翻译依赖 OK"

echo "==> [6/7] PyInstaller 编译"
# 图标：Linux 窗口图标由程序内部 SVG 设置，PyInstaller 不强制需要 .ico/.icns
ICON_ARG=""
if [ "$BUILD_VARIANT" = "GPU" ] && [ -f icon_gpu_1024.png ]; then
    ICON_ARG="--icon icon_gpu_1024.png"
elif [ -f icon_1024.png ]; then
    ICON_ARG="--icon icon_1024.png"
fi
# 内置 Argos 模型目录一并打包
MODEL_ARG=""
if [ -d argos_models ] && [ -n "$(ls -A argos_models 2>/dev/null)" ]; then
    MODEL_ARG="--add-data argos_models:argos_models"
fi
# —— 捆绑常缺的 xcb 小库 ——
# Qt 6.5+ 的 xcb 平台插件需要 libxcb-cursor，而多数发行版默认不装，
# 用户一启动就是一堆 qt.qpa.plugin 报错。这几个都是叶子库(共约 94KB)，
# 不直接与 X 服务器做协议交互，打包进来很安全。
# 注意：libxcb.so.1 / libX11 / libc 绝【不能】打包 —— 它们必须与用户的
# X 服务器和显卡驱动版本匹配，捆绑反而会引发难查的崩溃。
XCB_ARGS=""
XCB_FOUND=0
XCB_MISS=""
for _lib in libxcb-cursor.so.0 libxcb-image.so.0 libxcb-util.so.1 \
            libxcb-render-util.so.0; do
    _p=""
    for _d in /usr/lib/x86_64-linux-gnu /usr/lib64 /usr/lib; do
        [ -e "${_d}/${_lib}" ] && _p="${_d}/${_lib}" && break
    done
    if [ -n "${_p}" ]; then
        XCB_ARGS="${XCB_ARGS} --add-binary ${_p}:."
        XCB_FOUND=$((XCB_FOUND+1))
    else
        XCB_MISS="${XCB_MISS} ${_lib}"
    fi
done
if [ "${XCB_FOUND}" -gt 0 ]; then
    echo "    将捆绑 ${XCB_FOUND} 个 xcb 支持库(约 94KB)，减少用户端缺库导致的启动失败"
fi
# —— CPU 变体：排除 CUDA 相关模块 ——
# Linux 上有【两个】CUDA 来源，都要处理：
#   1. torch —— PyPI 默认是 CUDA 版，已在装依赖时用 /whl/cpu 索引解决
#   2. ctranslate2 —— Linux x86_64 轮子固定内含 cuDNN(183MB，arm64 才 15MB)，
#      没有 CPU 版可选，只能在打包时排除
# 排除后 Argos 离线翻译仍在 CPU 上正常工作。
CUDA_EXCLUDE=""
if [ "$BUILD_VARIANT" = "CPU" ]; then
    for _m in nvidia nvidia.cudnn nvidia.cublas nvidia.cuda_runtime \
              nvidia.cuda_nvrtc nvidia.cuda_cupti nvidia.cufft nvidia.curand \
              nvidia.cusolver nvidia.cusparse nvidia.nccl nvidia.nvtx triton; do
        CUDA_EXCLUDE="${CUDA_EXCLUDE} --exclude-module ${_m}"
    done
    echo "    CPU 变体：打包时排除 CUDA 模块"
fi

if [ -n "${XCB_MISS}" ]; then
    echo "    ! 编译环境缺少：${XCB_MISS}"
    echo "      建议先安装后再编译，让产物自带这些库："
    echo "        apt install -y libxcb-cursor0 libxcb-image0 libxcb-util1 libxcb-render-util0"
fi

# Kokoro 模型：含空格路径先复制到无空格临时目录再打包
KOKORO_DATA=""
if [ -d "$HOME/EnglishCoach Models/Kokoro" ]; then
    rm -rf _kokoro_stage
    mkdir -p _kokoro_stage
    cp -R "$HOME/EnglishCoach Models/Kokoro/." _kokoro_stage/
    KOKORO_DATA="--add-data _kokoro_stage:kokoro_model"
    echo "    将打包 Kokoro 模型"
fi

# 只清理本平台自己的产物目录，不动 dist 下其它平台的成果
DESTDIR="dist/${TAG}"
rm -rf build "${APP_NAME}.spec" "$DESTDIR"
mkdir -p "$DESTDIR"

"$PY" -m PyInstaller \
    --name "$APP_NAME" --windowed --noconfirm --clean \
    $ICON_ARG $MODEL_ARG $KOKORO_DATA $XCB_ARGS $CUDA_EXCLUDE \
    --collect-all argostranslate \
    --collect-all ctranslate2 \
    --collect-all sentencepiece \
    --collect-all kokoro \
    --collect-all misaki \
    --collect-all language_tags \
    --collect-all espeakng_loader \
    --collect-all num2words \
    --collect-all en_core_web_sm \
    --collect-all transformers \
    --collect-submodules lameenc \
    --hidden-import ordered_set \
    --hidden-import addict \
    --hidden-import pypinyin \
    --collect-all jieba \
    --hidden-import cn2an \
    --collect-all docx \
    --collect-all pdfplumber \
    --collect-all reportlab \
    --hidden-import num2words \
    --hidden-import pypdf \
    --copy-metadata kokoro \
    --copy-metadata misaki \
    "$MAIN"

rm -rf _kokoro_stage

# PyInstaller 默认输出到 dist/<APP_NAME>/，移进本平台子目录保持 dist 根干净
if [ -d "dist/${APP_NAME}" ]; then
    rm -rf "${DESTDIR}/${APP_NAME}"
    mv "dist/${APP_NAME}" "${DESTDIR}/"
fi

echo "==> [7/7] 打包 tar.gz"
TARBALL="EnglishCoach-${VERSION}-${TAG}.tar.gz"
# 生成一个简易启动脚本，方便双击/命令行运行
LAUNCH="${DESTDIR}/${APP_NAME}/English Coach.sh"
cat > "$LAUNCH" <<'LAUNCHEOF'
#!/bin/bash
# English Coach 启动脚本 / launcher
# 启动前先检查 Qt 运行所需的系统库，缺失时给出可直接复制的安装命令，
# 而不是让用户面对一堆 qt.qpa.plugin 报错。
cd "$(dirname "$0")"

missing=""
# Qt 6.5+ 的 xcb 平台插件必须依赖 libxcb-cursor，多数桌面默认不装
if ! ldconfig -p 2>/dev/null | grep -q 'libxcb-cursor\.so'; then
    missing="${missing} libxcb-cursor0"
fi
if ! ldconfig -p 2>/dev/null | grep -q 'libxkbcommon-x11\.so'; then
    missing="${missing} libxkbcommon-x11-0"
fi
if ! ldconfig -p 2>/dev/null | grep -q 'libGL\.so'; then
    missing="${missing} libgl1"
fi

if [ -n "$missing" ]; then
    echo "=============================================================="
    echo " 缺少运行所需的系统库 / Missing required system libraries:"
    for m in $missing; do echo "   - $m"; done
    echo ""
    echo " 请按你的发行版执行 / Install them with:"
    echo ""
    if command -v apt >/dev/null 2>&1; then
        echo "   sudo apt install -y$missing"
    elif command -v dnf >/dev/null 2>&1; then
        echo "   sudo dnf install -y xcb-util-cursor libxkbcommon-x11 mesa-libGL"
    elif command -v pacman >/dev/null 2>&1; then
        echo "   sudo pacman -S xcb-util-cursor libxkbcommon-x11"
    else
        echo "   请用你的包管理器安装上面列出的库"
    fi
    echo ""
    echo " 装好后重新运行本脚本即可。"
    echo " Run this script again once they are installed."
    echo "=============================================================="
    exit 1
fi

exec "./English Coach"
LAUNCHEOF
chmod +x "$LAUNCH" "${DESTDIR}/${APP_NAME}/English Coach" 2>/dev/null || true
# CPU 变体：清理 PyInstaller 仍复制进来的 CUDA 动态库。
# --exclude-module 只能拦 Python 模块，管不到 ctranslate2.libs/ 里的 .so 文件，
# 必须在这里按文件名删掉。删除后 Argos 走 CPU 推理，功能不受影响。
if [ "$BUILD_VARIANT" = "CPU" ]; then
    _appdir="${DESTDIR}/${APP_NAME}"
    _freed=0
    for _pat in 'libcudnn*' 'libcublas*' 'libcudart*' 'libcufft*' 'libcurand*' \
                'libcusolver*' 'libcusparse*' 'libnccl*' 'libnvrtc*' 'libcupti*' \
                'libnvToolsExt*' 'libnvJitLink*'; do
        while IFS= read -r -d '' _f; do
            _sz=$(stat -c%s "$_f" 2>/dev/null || echo 0)
            _freed=$((_freed + _sz))
            rm -f "$_f"
        done < <(find "$_appdir" -name "$_pat" -type f -print0 2>/dev/null)
    done
    # nvidia 包目录整体移除
    if [ -d "${_appdir}/_internal/nvidia" ]; then
        _sz=$(du -sb "${_appdir}/_internal/nvidia" 2>/dev/null | cut -f1)
        _freed=$((_freed + ${_sz:-0}))
        rm -rf "${_appdir}/_internal/nvidia"
    fi
    if [ "$_freed" -gt 0 ]; then
        echo "    已清除 CUDA 库，节省 $((_freed / 1024 / 1024)) MB"
    fi
    # 清理后自检：确认程序仍能导入关键模块
    echo "    验证清理后依赖完整性..."
fi

# 随产物附带安装/卸载脚本，让用户能像正常程序那样装进应用菜单
for _s in Install.sh Uninstall.sh; do
    if [ -f "$_s" ]; then
        cp "$_s" "${DESTDIR}/${APP_NAME}/$_s"
        chmod +x "${DESTDIR}/${APP_NAME}/$_s"
        echo "    已附带 $_s"
    else
        echo "    ! 未找到 $_s，产物中将没有安装脚本"
    fi
done
# 从 DESTDIR 内打包，让 tar 里是 "English Coach/..." 结构
( cd "$DESTDIR" && tar -czf "$TARBALL" "$APP_NAME" )
echo ""
echo "  完成 ✅"
echo "  可执行目录 : ${DESTDIR}/${APP_NAME}/"
echo "  可执行文件 : ${DESTDIR}/${APP_NAME}/English Coach"
echo "  分发压缩包 : ${DESTDIR}/${TARBALL}"
echo ""
echo "  运行方式："
echo "    cd \"${DESTDIR}/${APP_NAME}\" && ./\"English Coach\""
echo "  或解压 tar.gz 后运行其中的 English Coach 可执行文件。"
echo ""
echo "  提示：如目标机缺少 Qt 运行库，Debian/Ubuntu 可安装："
echo "    sudo apt install libxcb-cursor0 libxcb-xinerama0"
