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
TAG="Linux-x64"
# 多镜像：清华优先，失败回退官方源
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_FALLBACK="https://pypi.org/simple"

pip_install () {
    python -m pip install "$@" -i "$PIP_MIRROR" || \
    python -m pip install "$@" -i "$PIP_FALLBACK"
}

echo "==> [1/7] 激活 conda 环境: ${CONDA_ENV}"
if [ -z "$(command -v conda)" ]; then
    echo "✗ 未找到 conda，请先安装并加入 PATH"; exit 1
fi
CONDA_BASE="$(conda info --base 2>/dev/null)"
for cand in "$CONDA_BASE" "$HOME/anaconda3" "$HOME/miniconda3" \
            "/opt/anaconda3" "/opt/miniconda3"; do
    if [ -n "$cand" ] && [ -f "$cand/etc/profile.d/conda.sh" ]; then
        source "$cand/etc/profile.d/conda.sh"; break
    fi
done
if ! conda env list | grep -qE "(^|/)${CONDA_ENV}(\s|$)"; then
    echo "✗ 未找到环境 ${CONDA_ENV}，请先：conda create -n ${CONDA_ENV} python=3.12 -y"; exit 1
fi
conda activate "${CONDA_ENV}"
echo "    ----------------------------------------"
echo "    当前 conda 环境: ${CONDA_DEFAULT_ENV}"
echo "    Python 路径    : $(which python)"
python --version
echo "    ----------------------------------------"
if [ "${CONDA_DEFAULT_ENV}" != "${CONDA_ENV}" ]; then
    echo "✗ 环境未正确激活，中止以免装错环境"; exit 1
fi

echo "==> [2/7] 升级 pip 与打包工具"
pip_install -U pip
pip_install pyinstaller

echo "==> [3/7] 安装运行依赖"
# Linux 用最新 PyQt6(6.11.x)——Linux 无 Big Sur 兼容包袱
pip_install PyQt6 PyQt6-Qt6
# —— Argos 离线翻译：与其它平台一致的兼容版本组合 ——
pip_install "setuptools<81"
pip_install "numpy<2"
pip_install "sentencepiece==0.2.0"
pip_install "ctranslate2==4.3.1"
python -m pip install "argostranslate==1.9.6" --no-deps -i "$PIP_MIRROR" || \
python -m pip install "argostranslate==1.9.6" --no-deps -i "$PIP_FALLBACK"
pip_install sacremoses
pip_install -U edge-tts

# Kokoro 本地离线 TTS（Linux x86_64 与 mac 用同一套钉死版本，确保行为一致）
echo "    安装 Kokoro 离线 TTS 依赖..."
pip_install "torch==2.2.2"
pip_install "transformers==4.40.2"
pip_install kokoro soundfile
pip_install lameenc
pip_install python-docx pypdf pdfplumber reportlab num2words
pip_install ordered_set addict regex pydantic loguru
pip_install pypinyin jieba cn2an "misaki[zh]" || pip_install pypinyin jieba cn2an
# misaki 英文 G2P 需要 spaCy 英文模型。它不在 PyPI（走 GitHub Releases），
# 镜像会返回 0 字节占位导致 "Wheel is invalid" 报错。先检查是否已安装：
# 已装则跳过，未装才安装——优先官方 GitHub wheel，失败再退回 pip。
if python -c "import en_core_web_sm" >/dev/null 2>&1; then
  echo "  ✓ en_core_web_sm 已安装，跳过"
else
  python -m pip install \
    "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" \
    || pip_install en_core_web_sm \
    || echo "  ⚠ en_core_web_sm 预装失败，首次离线英文朗读会自动下载（需联网）"
fi
python -c "import torch,transformers,kokoro;print('  ✓ Kokoro 依赖链 OK, torch',torch.__version__,'transformers',transformers.__version__)" \
  || echo "  ⚠ Kokoro 依赖校验未通过，离线朗读可能不可用"
# espeak-ng 是 Kokoro 英文 G2P 的后备依赖（Linux 用系统包管理器）
if ! command -v espeak-ng >/dev/null 2>&1; then
    echo "    提示：可选安装 espeak-ng（Debian/Ubuntu: sudo apt install espeak-ng；"
    echo "          Fedora/RedHat: sudo dnf install espeak-ng），Kokoro 英文音素化更稳。"
fi

echo "==> [4/7] 预下载 Kokoro 模型（约 330MB，首次较慢，可离线跳过）"
python - <<'PYEOF' || echo "  ⚠ Kokoro 模型预下载失败，离线英文嗓音在无网时将不可用"
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
if ! python -c "import ctranslate2, sentencepiece" 2>/dev/null; then
    echo "✗ ctranslate2 / sentencepiece 导入失败。"
    echo "  请确认用了预编译包： pip install 'sentencepiece==0.2.0' 'ctranslate2==4.3.1' --only-binary :all:"
    exit 1
fi
echo "    离线翻译依赖 OK"

echo "==> [6/7] PyInstaller 编译"
# 图标：Linux 窗口图标由程序内部 SVG 设置，PyInstaller 不强制需要 .ico/.icns
ICON_ARG=""
[ -f icon_1024.png ] && ICON_ARG="--icon icon_1024.png"
# 内置 Argos 模型目录一并打包
MODEL_ARG=""
if [ -d argos_models ] && [ -n "$(ls -A argos_models 2>/dev/null)" ]; then
    MODEL_ARG="--add-data argos_models:argos_models"
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

python -m PyInstaller \
    --name "$APP_NAME" --windowed --noconfirm --clean \
    $ICON_ARG $MODEL_ARG $KOKORO_DATA \
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
LAUNCH="${DESTDIR}/${APP_NAME}/启动 English Coach.sh"
cat > "$LAUNCH" <<'LAUNCHEOF'
#!/bin/bash
cd "$(dirname "$0")"
exec "./English Coach"
LAUNCHEOF
chmod +x "$LAUNCH" "${DESTDIR}/${APP_NAME}/English Coach" 2>/dev/null || true
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
