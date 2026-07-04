#!/bin/bash
# ============================================================================
#  EnglishCoach · macOS 一键编译脚本  (v1.9.1)
#  PyInstaller 打包，兼容 macOS 11 Big Sur，内置 Argos 中英离线模型。
#  产物: dist/EnglishCoach.app  和  EnglishCoach-2.5.1-<arch>.dmg
# ============================================================================

set -e

APP_NAME="English Coach"
VERSION="2.5.1"
MAIN="english_coach.py"
CONDA_ENV="EnglishCoach"
# 多镜像：清华优先，失败回退官方源（解决 argostranslate 下载被重置）
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_FALLBACK="https://pypi.org/simple"

pip_install () {
    # 先试清华源，失败再用官方源
    python -m pip install "$@" -i "$PIP_MIRROR" || \
    python -m pip install "$@" -i "$PIP_FALLBACK"
}

echo "==> [1/8] 激活 conda 环境: ${CONDA_ENV}"
if [ -z "$(command -v conda)" ]; then
    echo "✗ 未找到 conda，请先安装并加入 PATH"; exit 1
fi
# 加载 conda 钩子：优先用 conda info --base，找不到再试常见路径（含外置 SSD）
CONDA_BASE="$(conda info --base 2>/dev/null)"
for cand in "$CONDA_BASE" \
            "/Volumes/CineeSD/StrilenLiu/Scenarios/AnaConda" \
            "$HOME/anaconda3" "$HOME/miniconda3" "/opt/anaconda3" "/opt/miniconda3"; do
    if [ -n "$cand" ] && [ -f "$cand/etc/profile.d/conda.sh" ]; then
        source "$cand/etc/profile.d/conda.sh"; break
    fi
done
if ! conda env list | grep -qE "(^|/)${CONDA_ENV}(\s|$)"; then
    echo "✗ 未找到环境 ${CONDA_ENV}，请先：conda create -n ${CONDA_ENV} python=3.12 -y"; exit 1
fi
conda activate "${CONDA_ENV}"
# 醒目确认当前环境，避免误装到 base
echo "    ----------------------------------------"
echo "    当前 conda 环境: ${CONDA_DEFAULT_ENV}"
echo "    Python 路径    : $(which python)"
python --version
echo "    ----------------------------------------"
if [ "${CONDA_DEFAULT_ENV}" != "${CONDA_ENV}" ]; then
    echo "✗ 当前不在 ${CONDA_ENV} 环境（实际: ${CONDA_DEFAULT_ENV}）。已中止以防装错环境。"
    exit 1
fi

echo "==> [2/8] 安装依赖（清华源，失败自动回退官方源）"
python -m pip install --upgrade pip -i "$PIP_MIRROR" || true
# PyQt6 钉 6.4.x（兼容 Big Sur）
pip_install "PyQt6==6.4.2" "PyQt6-Qt6==6.4.3" "PyQt6-sip"
pip_install requests pyinstaller pillow
# —— Argos 离线翻译：钉死兼容 Big Sur 且无 PyTorch 的版本组合 ——
# numpy<2 避免 NumPy 2.x 冲突；sentencepiece 0.2.0 有 cp312 Intel 预编译包；
# ctranslate2 4.3.1 兼容 Big Sur；argostranslate 1.9.6 用 --no-deps 挡掉 stanza/torch
pip_install "setuptools<81"
pip_install "numpy<2"
pip_install "sentencepiece==0.2.0"
pip_install "ctranslate2==4.3.1"
python -m pip install "argostranslate==1.9.6" --no-deps -i "$PIP_MIRROR" || \
python -m pip install "argostranslate==1.9.6" --no-deps -i "$PIP_FALLBACK"
pip_install sacremoses
pip_install -U edge-tts

# Kokoro 本地离线 TTS。版本组合经 Big Sur + Intel Mac 实测验证（关键！）：
#   torch==2.2.2          —— Intel Mac 能装的最高版（2.3+ 无 x86 wheel）
#   transformers==4.40.2  —— 新版要求 torch>=2.4，会禁用 torch2.2 导致 Kokoro 失败
#   en_core_web_sm 3.8.0  —— misaki 英文 G2P 的隐藏依赖（spaCy 英文模型）
echo "    安装 Kokoro 离线 TTS 依赖（钉死兼容 Big Sur 的版本组合）..."
pip_install "torch==2.2.2"
pip_install "transformers==4.40.2"
pip_install kokoro soundfile
pip_install lameenc                       # mp3 导出用（纯 Python，体积小）
# 文件导入/导出 + 历史多格式下载所需
pip_install python-docx pypdf pdfplumber reportlab num2words
# Kokoro/misaki 链路中容易缺失的传递依赖，显式补齐（曾遇 ordered_set 缺失）
pip_install ordered_set addict regex pydantic loguru
# 中文 G2P 依赖（Kokoro 读中文需要：pypinyin/jieba/cn2an）
pip_install pypinyin jieba cn2an "misaki[zh]" || pip_install pypinyin jieba cn2an
# misaki 英文 G2P 需要 spaCy 英文模型，预装好避免运行时联网下载
python -m pip install \
  "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" \
  || pip_install en_core_web_sm || echo "  ⚠ en_core_web_sm 预装失败，首次离线英文朗读会自动下载（需联网）"
# 校验 Kokoro 关键链路：torch 没被 transformers 禁用
python -c "import torch,transformers,kokoro;print('  ✓ Kokoro 依赖链 OK, torch',torch.__version__,'transformers',transformers.__version__)" \
  || echo "  ⚠ Kokoro 依赖校验未通过，离线朗读可能不可用"
# espeak-ng 是 Kokoro 英文 G2P 的后备依赖（mac 用 brew）
if ! command -v espeak-ng >/dev/null 2>&1; then
    echo "    提示：可选 brew install espeak-ng（Kokoro 英文音素化更稳，多数情况非必需）"
fi
# 预下载 Kokoro 模型到 HF 缓存，并复制到打包目录，确保离线可用
echo "    预下载 Kokoro 模型（约 330MB，首次较慢）..."
KOKORO_REPO="$HOME/EnglishCoach Models/Kokoro"
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


# 校验 ctranslate2 + sentencepiece 能否导入（这是 Big Sur 上最易失败处）
echo "    校验离线翻译依赖 ..."
if ! python -c "import ctranslate2, sentencepiece" 2>/dev/null; then
    echo "✗ ctranslate2 / sentencepiece 导入失败。"
    echo "  请确认用了预编译包： pip install 'sentencepiece==0.2.0' 'ctranslate2==4.3.1' --only-binary :all:"
    exit 1
fi
echo "    离线翻译依赖 OK"

echo "==> [3/8] 准备 Argos 中英离线模型（打包进 App）"
mkdir -p argos_models
EN_ZH_URL="https://argos-net.com/v1/translate-en_zh-1_9.argosmodel"
ZH_EN_URL="https://argos-net.com/v1/translate-zh_en-1_9.argosmodel"

# 公共模型仓库查找顺序（找到完整的就复用，避免每个版本重复下载）：
#   1) 环境变量 ENGLISHCOACH_MODELS 指定的目录
#   2) ~/EnglishCoach Models/
#   3) 上级目录的 _models/
ARGOS_CACHE="$HOME/EnglishCoach Models/Argos"
MODEL_REPOS=(
    "${ENGLISHCOACH_MODELS:-}"
    "$ARGOS_CACHE"
    "$HOME/EnglishCoach Models"
    "../_models"
)

is_complete () {  # 文件存在且 > 40MB
    [ -f "$1" ] && [ "$(stat -f%z "$1" 2>/dev/null || echo 0)" -gt 40000000 ]
}

fetch_model () {
    local fname="$1" url="$2" dst="argos_models/$1"
    if is_complete "$dst"; then echo "  已就绪 $dst（本目录）"; return 0; fi
    # 先从公共仓库找
    for repo in "${MODEL_REPOS[@]}"; do
        [ -z "$repo" ] && continue
        if is_complete "$repo/$fname"; then
            cp "$repo/$fname" "$dst"
            echo "  ✓ 从仓库复用 $repo/$fname"
            return 0
        fi
    done
    # 仓库没有 -> 下载（用 http1.1 避开 HTTP/2 stream reset）
    echo "  仓库未找到，开始下载 $fname ..."
    curl --http1.1 -L --retry 10 --retry-delay 5 -C - -o "$dst" "$url" || true
    # 下成功后顺手存一份到 ~/EnglishCoach Models/Argos/ 供以后复用
    if is_complete "$dst"; then
        mkdir -p "$ARGOS_CACHE"
        cp "$dst" "$ARGOS_CACHE/$fname" 2>/dev/null || true
        echo "  ✓ 已缓存到 ~/EnglishCoach Models/Argos/$fname（以后复用）"
    fi
}

fetch_model "en_zh.argosmodel" "$EN_ZH_URL"
fetch_model "zh_en.argosmodel" "$ZH_EN_URL"

# 完整性校验
for f in argos_models/en_zh.argosmodel argos_models/zh_en.argosmodel; do
    if ! is_complete "$f"; then
        echo "  [警告] $f 不完整或缺失，离线翻译将不可用。"
        echo "         请手动下载完整模型放到 ~/EnglishCoach Models/ 后重试。"
    fi
done

echo "==> [4/8] 生成图标"
[ -f make_icon.py ] && python make_icon.py
ICNS="AppIcon.icns"; ICON_ARG=""; DATA_ARG="--add-data icon_1024.png:."
if [ -f icon_1024.png ]; then
    ISET="AppIcon.iconset"; rm -rf "$ISET"; mkdir "$ISET"
    for s in 16 32 64 128 256 512; do
        sips -z $s $s icon_1024.png --out "$ISET/icon_${s}x${s}.png" >/dev/null
        d=$((s*2)); sips -z $d $d icon_1024.png --out "$ISET/icon_${s}x${s}@2x.png" >/dev/null
    done
    sips -z 1024 1024 icon_1024.png --out "$ISET/icon_512x512@2x.png" >/dev/null
    iconutil -c icns "$ISET" -o "$ICNS"; rm -rf "$ISET"
    ICON_ARG="--icon $ICNS"
fi
# 内置模型目录一并打包
MODEL_ARG=""
if [ -d argos_models ] && [ -n "$(ls -A argos_models 2>/dev/null)" ]; then
    MODEL_ARG="--add-data argos_models:argos_models"
fi

echo "==> [5/8] 清理旧产物"
rm -rf build dist "${APP_NAME}.spec" "${APP_NAME}-${VERSION}"*.dmg

echo "==> [6/8] PyInstaller 编译（兼容 Big Sur）"
export MACOSX_DEPLOYMENT_TARGET=11.0
ARCH="$(uname -m)"
echo "    本机架构: ${ARCH}（产物仅适配此架构）"
# Kokoro 模型作为数据打包进 app（若已预下载）
KOKORO_DATA=""
if [ -d "$HOME/EnglishCoach Models/Kokoro" ]; then
    # PyInstaller 的 --add-data 在变量展开时会被空格拆分，故先把含空格路径的
    # 模型复制到无空格的临时目录 _kokoro_stage，再从那里打包。
    rm -rf _kokoro_stage
    mkdir -p _kokoro_stage
    cp -R "$HOME/EnglishCoach Models/Kokoro/." _kokoro_stage/
    KOKORO_DATA="--add-data _kokoro_stage:kokoro_model"
    echo "    将打包 Kokoro 模型: $HOME/EnglishCoach Models/Kokoro"
fi

python -m PyInstaller \
    --name "$APP_NAME" --windowed --noconfirm --clean \
    $ICON_ARG $DATA_ARG $MODEL_ARG $KOKORO_DATA \
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
    --osx-bundle-identifier "com.strilen.englishcoach" \
    --target-architecture "$ARCH" \
    "$MAIN"

PLIST="dist/${APP_NAME}.app/Contents/Info.plist"
if [ -f "$PLIST" ]; then
    /usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 11.0" "$PLIST" 2>/dev/null \
      || /usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 11.0" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${VERSION}" "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${VERSION}" "$PLIST" 2>/dev/null || true
fi

echo "==> [7/8] 解除自身隔离"
xattr -cr "dist/${APP_NAME}.app" 2>/dev/null || true

echo "==> [8/8] 打包 DMG"
DMG="${APP_NAME}-${VERSION}-${ARCH}.dmg"
# 先卸载可能残留的同名挂载卷，避免 "hdiutil: create failed - 资源忙"
for v in /Volumes/${APP_NAME}*; do
    [ -d "$v" ] && hdiutil detach "$v" -force >/dev/null 2>&1 || true
done
rm -f "$DMG"
sleep 1
STAGE=$(mktemp -d)
cp -R "dist/${APP_NAME}.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
# 重试机制：资源忙时等待再试
n=0
until hdiutil create -volname "${APP_NAME}" -srcfolder "$STAGE" -ov -format UDZO "$DMG"; do
    n=$((n+1)); [ $n -ge 3 ] && { echo "DMG 打包多次失败"; break; }
    echo "  资源忙，5 秒后重试 ($n/3)…"; sleep 5
done
rm -rf "$STAGE"

echo ""
echo "================================================================"
echo "  完成 ✅   App: dist/${APP_NAME}.app   DMG: ${DMG}"
echo "================================================================"
echo ""
echo "若无法启动，终端运行查看真实报错："
echo "    ./dist/${APP_NAME}.app/Contents/MacOS/${APP_NAME}"
echo "分发他人首次打开若提示\"已损坏\"（未签名）："
echo "    sudo xattr -rd com.apple.quarantine /路径/${APP_NAME}.app"
