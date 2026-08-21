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
# conda 环境名：GPU 变体优先用 EnglishCoach-GPU（若存在），
# 否则与 CPU 共用 EnglishCoach。共用时两个变体会互相覆盖 torch ——
# pip 见"版本已满足"就跳过安装，于是 GPU 版装成了 CPU 版。
# 可用 CONDA_ENV 环境变量强制指定。
CONDA_ENV="${CONDA_ENV:-EnglishCoach}"
# 允许用户直接指定解释器，绕过一切自动探测：
#   PY=/path/to/envs/EnglishCoach/bin/python bash "Build Linux.sh"
PY_OVERRIDE="${PY:-}"
# CPU / GPU 变体（由 Build Linux GPU.sh 覆盖为 GPU）
BUILD_VARIANT="${BUILD_VARIANT:-CPU}"
if [ "$BUILD_VARIANT" = "GPU" ]; then
    TAG="Linux-x64-GPU"
    # CUDA 12.1 版 torch，与 Windows GPU 版思路一致
    TORCH_SPEC="torch==2.2.2"
    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
    VENV_DIR="${VENV_DIR:-.build-venv-gpu}"
    # 若存在专用的 GPU conda 环境就优先用它，避免与 CPU 版共用同一 env
    if [ -z "${CONDA_ENV_EXPLICIT:-}" ] && command -v conda >/dev/null 2>&1; then
        if conda info --envs 2>/dev/null | grep -qE "^EnglishCoach-GPU[[:space:]]"; then
            CONDA_ENV="EnglishCoach-GPU"
        fi
    fi
    # GPU 版可执行文件与安装后的菜单项都叫 "English Coach GPU"，
    # 可与 CPU 版并存互不覆盖
    APP_NAME="English Coach GPU"
else
    TAG="Linux-x64-CPU"
    TORCH_SPEC="torch==2.2.2"
    TORCH_INDEX="https://download.pytorch.org/whl/cpu"
    VENV_DIR="${VENV_DIR:-.build-venv}"
fi
# ============================================================================
#  产物完整性拦截 / Build integrity gate
#
#  原则：任何会让产物功能残缺的问题，都必须【阻断编译】并说清原因，
#  绝不允许"打印一行警告然后假装编译成功" —— 那会把问题一路带到用户手上。
#
#  STRICT=1（默认）：发现问题即失败，退出码非 0
#  STRICT=0        ：仅警告并继续，供明知故犯的场景使用
#      STRICT=0 bash "Build Linux.sh"
# ============================================================================
STRICT="${STRICT:-1}"
BUILD_PROBLEMS=""

record_problem () {   # $1=简述  $2=后果  $3=修复建议
    BUILD_PROBLEMS="${BUILD_PROBLEMS}
  ✗ $1
      影响：$2
      处理：$3"
}

gate_check () {       # 在关键节点结算已记录的问题
    [ -z "$BUILD_PROBLEMS" ] && return 0
    echo ""
    echo "============================================================"
    echo "  编译被拦截：产物将存在功能缺失"
    echo "  Build blocked: the output would be functionally incomplete"
    echo "============================================================"
    echo "$BUILD_PROBLEMS"
    echo ""
    if [ "$STRICT" = "1" ]; then
        echo "  已中止，未产出安装包。修复后重新编译即可。"
        echo "  Aborted; no package was produced. Fix the above and rebuild."
        echo ""
        echo "  如确实需要在明知功能缺失的情况下强行编译："
        echo "  To build anyway despite the missing features:"
        echo "      STRICT=0 bash \"$(basename "${BASH_SOURCE[0]}")\""
        echo ""
        exit 1
    fi
    echo "  STRICT=0：已知问题被忽略，继续编译（产物功能不完整）。"
    echo ""
    BUILD_PROBLEMS=""
}

# 多镜像：清华优先，失败回退官方源
PIP_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_FALLBACK="https://pypi.org/simple"

pip_install () {
    "$PY" -m pip install "$@" -i "$PIP_MIRROR" || \
    "$PY" -m pip install "$@" -i "$PIP_FALLBACK"
}

echo "==> [1/8] 准备 Python 环境"
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
    # 不能直接用 "python" —— conda 装在非默认路径时，PATH 里的 python 未必是
    # 该环境的解释器（尤其非交互 shell 下 conda 的 PATH 注入可能不完整）。
    # 依次尝试：conda 报告的环境前缀 -> CONDA_PREFIX -> PATH 兜底。
    PY=""
    _env_prefix="$(conda info --envs 2>/dev/null \
        | awk -v e="$CONDA_ENV" '$1==e {print $NF}' | head -1)"
    for _cand in "${_env_prefix}/bin/python" \
                 "${CONDA_PREFIX:-}/bin/python" \
                 "$(command -v python 2>/dev/null)"; do
        if [ -n "$_cand" ] && [ -x "$_cand" ]; then PY="$_cand"; break; fi
    done
    if [ -z "$PY" ]; then
        echo "✗ 无法定位 conda 环境 ${CONDA_ENV} 的 Python 解释器"
        echo "  可手动指定后重试： PY=/你的路径/envs/${CONDA_ENV}/bin/python bash \"Build Linux.sh\""
        exit 1
    fi
    echo "    conda 环境解释器: $PY"
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
# 用户显式指定的优先级最高
if [ -n "$PY_OVERRIDE" ] && [ -x "$PY_OVERRIDE" ]; then
    PY="$PY_OVERRIDE"
    echo "    使用指定的解释器: $PY"
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

echo "==> [2/8] 升级 pip 与打包工具"
pip_install -U pip
pip_install pyinstaller

# ============================================================================
#  系统级工具检查（统一处理，避免每次缺一个工具就在半途失败）
#
#  这些是【系统命令】不是 Python 包，pip / requirements.txt 装不了；
#  conda 与系统包管理器可以。缺失时按 conda -> apt/dnf/pacman/apk 顺序尝试
#  自动安装，都不行才退出并给出各发行版的手动命令。
#
#  命令 -> 各平台包名对照：
#    objdump : binutils      —— PyInstaller 分析二进制依赖必需
#    curl    : curl          —— 下载 Argos 离线翻译模型
#    tar     : tar           —— 打包产物
# ============================================================================
_pkg_for () {   # $1=命令名 $2=包管理器 -> 输出包名
    case "$1" in
        objdump) echo "binutils" ;;
        curl)    echo "curl" ;;
        tar)     echo "tar" ;;
        *)       echo "$1" ;;
    esac
}

_try_install () {   # $1=包名 ; 成功返回 0
    local pkg="$1" ok=1
    # 1) conda（用户自己的环境，无需 root）
    if [ "$USE_CONDA" = "1" ] && command -v conda >/dev/null 2>&1; then
        conda install -y -q "$pkg" >/dev/null 2>&1 && return 0
    fi
    # 2) 系统包管理器；非 root 时用免密 sudo，不弹密码提示卡住脚本
    local SUDO=""
    if [ "$(id -u)" != "0" ]; then
        command -v sudo >/dev/null 2>&1 && SUDO="sudo -n"
    fi
    if command -v apt-get >/dev/null 2>&1; then
        $SUDO apt-get update -qq >/dev/null 2>&1 || true
        $SUDO apt-get install -y -qq "$pkg" >/dev/null 2>&1 && return 0
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO dnf install -y -q "$pkg" >/dev/null 2>&1 && return 0
    elif command -v yum >/dev/null 2>&1; then
        $SUDO yum install -y -q "$pkg" >/dev/null 2>&1 && return 0
    elif command -v pacman >/dev/null 2>&1; then
        $SUDO pacman -S --noconfirm --quiet "$pkg" >/dev/null 2>&1 && return 0
    elif command -v apk >/dev/null 2>&1; then
        $SUDO apk add --quiet "$pkg" >/dev/null 2>&1 && return 0
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO zypper --non-interactive --quiet install "$pkg" >/dev/null 2>&1 && return 0
    fi
    return 1
}

_missing_tools=""
for _cmd in objdump curl tar; do
    command -v "$_cmd" >/dev/null 2>&1 && continue
    _pkg="$(_pkg_for "$_cmd")"
    echo "    缺少 ${_cmd}（来自 ${_pkg}），尝试自动安装…"
    if _try_install "$_pkg" && command -v "$_cmd" >/dev/null 2>&1; then
        echo "    ✓ 已安装 ${_pkg}"
    else
        _missing_tools="${_missing_tools} ${_pkg}"
    fi
done

if [ -n "$_missing_tools" ]; then
    echo ""
    echo "✗ 以下系统工具缺失且无法自动安装：${_missing_tools}"
    echo "  它们不是 Python 包，请用下列方式之一手动安装后重试："
    echo ""
    echo "    conda 环境    : conda install -y${_missing_tools}"
    echo "    Debian/Ubuntu : sudo apt install -y${_missing_tools}"
    echo "    Fedora/RHEL   : sudo dnf install -y${_missing_tools}"
    echo "    Arch          : sudo pacman -S${_missing_tools}"
    echo "    Alpine        : sudo apk add${_missing_tools}"
    echo ""
    echo "  说明：objdump 来自 binutils，PyInstaller 用它分析二进制依赖；"
    echo "        curl 用于下载 Argos 离线翻译模型；tar 用于打包产物。"
    echo ""
    exit 1
fi

echo "==> [3/8] 安装运行依赖"
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
# 关键：pip 见"版本已满足"就跳过安装，--index-url 便形同虚设 —— 复用旧虚拟环境时
# CPU/GPU 变体会互相串味(GPU 版装成 CPU 版，或反之)。先卸载已装的 torch，
# 强制从指定索引重新安装。
_cur_tv="$("$PY" -c 'import torch;print(torch.__version__)' 2>/dev/null || true)"
if [ -n "$_cur_tv" ]; then
    case "$_cur_tv" in
        *+cu*|*cu1*) _cur_variant=GPU ;;
        *)           _cur_variant=CPU ;;
    esac
    if [ "$_cur_variant" != "$BUILD_VARIANT" ]; then
        echo "    环境中已有 ${_cur_variant} 版 torch ${_cur_tv}，与本次(${BUILD_VARIANT})不符，先卸载"
        "$PY" -m pip uninstall -y torch >/dev/null 2>&1 || true
        # CUDA 版会连带 12 个 nvidia-* 包，切到 CPU 时必须一并清掉，
        # 否则它们仍会被打进产物白白撑大体积
        if [ "$BUILD_VARIANT" = "CPU" ]; then
            _nv=$("$PY" -m pip list 2>/dev/null | awk '/^nvidia-/{print $1}' | tr '\n' ' ')
            [ -n "$_nv" ] && "$PY" -m pip uninstall -y $_nv triton >/dev/null 2>&1 || true
        fi
    fi
fi
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
        print("    [X] CPU 版却装成了 CUDA 版 torch")
        sys.exit(2)
    elif want == "GPU" and not is_cuda:
        print("    [X] GPU 版却装成了 CPU 版 torch")
        sys.exit(3)
    else:
        print(f"    已确认为 {want} 版")
except Exception as e:
    print(f"    [!] 无法导入 torch: {e}")
    sys.exit(1)
TORCHCHK
_tchk=$?
if [ "$_tchk" = "2" ]; then
    record_problem \
        "CPU 变体装成了 CUDA 版 torch" \
        "产物会凭空大出数 GB，且包含 CPU 版根本用不到的 CUDA 组件" \
        "多为 pip 全局镜像源劫持了 --index-url。可先 pip uninstall -y torch 及全部 nvidia-* 包，再加 --no-cache-dir 重装"
elif [ "$_tchk" = "3" ]; then
    record_problem \
        "GPU 变体装成了 CPU 版 torch" \
        "产物体积与 CPU 版无异，且【完全无法使用显卡加速】—— 名为 GPU 版实则不是" \
        "确认能访问 ${TORCH_INDEX}；若复用了旧虚拟环境，删除 ${VENV_DIR} 后重新编译"
elif [ "$_tchk" != "0" ]; then
    record_problem \
        "torch 无法导入" \
        "离线朗读功能将完全不可用" \
        "检查上方 pip 安装输出"
fi
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
    || record_problem \
        "spaCy 英文模型 en_core_web_sm 未安装" \
        "离线英文朗读的分词依赖它，缺失时首次使用需联网下载" \
        "手动安装：pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"
fi
"$PY" -c "import torch,transformers,kokoro;print('  ✓ Kokoro 依赖链 OK, torch',torch.__version__,'transformers',transformers.__version__)" \
  || record_problem \
        "Kokoro 依赖链校验未通过" \
        "离线朗读功能将无法使用" \
        "检查上方 pip 安装输出，确认 torch / transformers / kokoro 均已正确安装"
# espeak-ng 是 Kokoro 英文 G2P 的后备依赖（Linux 用系统包管理器）
if ! command -v espeak-ng >/dev/null 2>&1; then
    echo "    提示：可选安装 espeak-ng（Debian/Ubuntu: sudo apt install espeak-ng；"
    echo "          Fedora/RedHat: sudo dnf install espeak-ng），Kokoro 英文音素化更稳。"
fi

echo "==> [4/8] 预下载 Kokoro 模型（约 330MB，首次较慢，可离线跳过）"
if ! "$PY" - <<'PYEOF'
import os, sys
target = os.path.expanduser("~/EnglishCoach Models/Kokoro")
os.makedirs(target, exist_ok=True)

# 已有完整模型就直接复用，不重复下载
def _has_weights(d):
    return any(f.endswith((".pth", ".onnx", ".safetensors", ".bin"))
               for _r, _d, fs in os.walk(d) for f in fs)
# 已是缓存结构且含权重才算就绪；扁平旧目录会重新按缓存结构下载一次
if os.path.isdir(os.path.join(target, "hub")) and _has_weights(target):
    print("  ✓ 已有 Kokoro 模型，跳过下载:", target)
    sys.exit(0)

# 端点顺序：用户指定 > 大陆镜像 > 官方。构建机常在大陆，直连 huggingface.co
# 会失败，此前没有镜像回退，导致产物缺模型、用户端仍需联网。
endpoints = []
if os.environ.get("HF_ENDPOINT"):
    endpoints.append(os.environ["HF_ENDPOINT"])
endpoints += ["https://hf-mirror.com", "https://huggingface.co"]

# 关键：下载成 HF 的【缓存结构】(target/hub/models--hexgrad--Kokoro-82M/...)，
# 而不是 local_dir 的扁平目录。运行时只需把 HF_HOME 指向 target，
# 模型与音色(voices/*.pt)就全部离线可用 —— 扁平目录只能解决模型、
# 音色仍会联网下载。
os.environ["HF_HOME"] = target
last = None
for ep in endpoints:
    os.environ["HF_ENDPOINT"] = ep
    try:
        print(f"  尝试端点 {ep} ...")
        # 必须在设好环境变量【之后】再导入，否则端点被固定成旧值
        for _m in [m for m in list(sys.modules) if m.startswith("huggingface_hub")]:
            del sys.modules[_m]
        from huggingface_hub import snapshot_download
        snapshot_download(repo_id="hexgrad/Kokoro-82M")
        print("  ✓ Kokoro 模型已就绪(HF 缓存结构):", target)
        sys.exit(0)
    except Exception as e:
        last = e
        print(f"    失败: {str(e)[:120]}")
print("  Kokoro 预下载异常:", last)
sys.exit(1)
PYEOF
then
    record_problem \
        "Kokoro 离线朗读模型未能下载" \
        "产物内不含模型，用户首次朗读必须联网；无网环境下离线朗读完全不可用" \
        "确认网络后重试；大陆可先设 export HF_ENDPOINT=https://hf-mirror.com；或手动下载 hexgrad/Kokoro-82M 到 ~/EnglishCoach Models/Kokoro/ 再编译"
fi

echo "==> [5/8] 准备 Argos 中英离线模型（打包进产物）"
# 此前 Linux 脚本漏了这一步：后面的 MODEL_ARG 会引用 argos_models 目录，
# 目录不存在时 MODEL_ARG 为空，模型打不进产物，离线翻译在用户端直接失效。
# 逻辑与 mac / Windows 版一致，仅把 stat 换成 Linux 语法(-c%s)。
mkdir -p argos_models
EN_ZH_URL="https://argos-net.com/v1/translate-en_zh-1_9.argosmodel"
ZH_EN_URL="https://argos-net.com/v1/translate-zh_en-1_9.argosmodel"

# 公共模型仓库查找顺序（找到完整的就复用，避免每个版本重复下载）
ARGOS_CACHE="$HOME/EnglishCoach Models/Argos"
MODEL_REPOS=(
    "${ENGLISHCOACH_MODELS:-}"
    "$ARGOS_CACHE"
    "$HOME/EnglishCoach Models"
    "../_models"
)

is_complete () {   # 文件存在且 > 40MB
    [ -f "$1" ] && [ "$(stat -c%s "$1" 2>/dev/null || echo 0)" -gt 40000000 ]
}

fetch_model () {
    local fname="$1" url="$2" dst="argos_models/$1"
    if is_complete "$dst"; then echo "  已就绪 $dst（本目录）"; return 0; fi
    for repo in "${MODEL_REPOS[@]}"; do
        [ -z "$repo" ] && continue
        if is_complete "$repo/$fname"; then
            cp "$repo/$fname" "$dst"
            echo "  ✓ 从仓库复用 $repo/$fname"
            return 0
        fi
    done
    echo "  仓库未找到，开始下载 $fname ..."
    # curl 已在系统工具检查中保证存在；仍留 wget 作为备选，
    # 以防某些环境里 curl 存在但被策略限制。
    # --http1.1 避开 HTTP/2 stream reset；-C - 支持断点续传
    if command -v curl >/dev/null 2>&1; then
        curl --http1.1 -L --retry 10 --retry-delay 5 -C - -o "$dst" "$url" || true
    elif command -v wget >/dev/null 2>&1; then
        wget -c -t 10 -O "$dst" "$url" || true
    fi
    if is_complete "$dst"; then
        mkdir -p "$ARGOS_CACHE"
        cp "$dst" "$ARGOS_CACHE/$fname" 2>/dev/null || true
        echo "  ✓ 已缓存到 ~/EnglishCoach Models/Argos/$fname（以后复用）"
    fi
}

fetch_model "en_zh.argosmodel" "$EN_ZH_URL"
fetch_model "zh_en.argosmodel" "$ZH_EN_URL"

# 完整性校验：缺失时明确告警，避免编出一个离线翻译不可用的包却毫无察觉
_argos_ok=1
for f in argos_models/en_zh.argosmodel argos_models/zh_en.argosmodel; do
    if ! is_complete "$f"; then
        echo "  [缺失] $f 不完整或缺失"
        _argos_ok=0
    fi
done
if [ "$_argos_ok" = "0" ]; then
    record_problem \
        "Argos 中英离线翻译模型缺失或不完整" \
        "产物内不含离线翻译模型，Argos 引擎在用户端完全不可用" \
        "确认网络后重试，或手动下载到 ~/EnglishCoach Models/Argos/ ：$EN_ZH_URL 与 $ZH_EN_URL"
fi

# 编译前结算：功能性缺失在此拦截，不浪费后续十几分钟的打包时间
gate_check

echo "==> [6/8] 校验离线翻译依赖"
if ! "$PY" -c "import ctranslate2, sentencepiece" 2>/dev/null; then
    echo "✗ ctranslate2 / sentencepiece 导入失败。"
    echo "  请确认用了预编译包： pip install 'sentencepiece==0.2.0' 'ctranslate2==4.3.1' --only-binary :all:"
    exit 1
fi
echo "    离线翻译依赖 OK"

echo "==> [7/8] PyInstaller 编译"
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
# —— conda 环境专用：捆绑 conda 自己的 C 库 ——
# conda 里的 Python C 扩展(pyexpat / _ssl / _lzma 等)链接的是 conda 目录下的
# 库，而不是系统库。PyInstaller 不一定会把它们收全，产物在别的机器上运行时
# 就会回退去找系统库，若系统版本较旧便报：
#     ImportError: pyexpat...so: undefined symbol: XML_SetAllocTrackerActivationThreshold
# (该符号是较新 expat 才有的)。这里显式把这些库打进产物。
CONDA_LIB_ARGS=""
if [ "$USE_CONDA" = "1" ]; then
    _cp="$("$PY" -c 'import sys,os; print(os.path.dirname(os.path.dirname(sys.executable)))' 2>/dev/null)"
    if [ -d "${_cp}/lib" ]; then
        _n=0
        for _lib in libexpat.so.1 libffi.so libffi.so.8 liblzma.so.5 \
                    libbz2.so.1.0 libsqlite3.so.0 libz.so.1 libuuid.so.1 \
                    libcrypto.so.3 libssl.so.3 libreadline.so libtinfo.so.6; do
            if [ -e "${_cp}/lib/${_lib}" ]; then
                CONDA_LIB_ARGS="${CONDA_LIB_ARGS} --add-binary ${_cp}/lib/${_lib}:."
                _n=$((_n+1))
            fi
        done
        [ "$_n" -gt 0 ] && echo "    将捆绑 ${_n} 个 conda 运行库（避免产物在其它机器上找不到符号）"
    fi
fi

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
    $ICON_ARG $MODEL_ARG $KOKORO_DATA $XCB_ARGS $CONDA_LIB_ARGS $CUDA_EXCLUDE \
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

echo "==> [8/8] 打包 tar.gz"
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

# Wayland 下 Qt 的工具提示若未设置 transientParent，会触发协议错误直接断开
# 连接("The Wayland connection experienced a fatal error")。走 XWayland(xcb)
# 可完全避开，且产物已捆绑 xcb 支持库。用户可用 QT_QPA_PLATFORM 覆盖。
if [ -z "${QT_QPA_PLATFORM:-}" ] && [ -n "${WAYLAND_DISPLAY:-}" ]; then
    export QT_QPA_PLATFORM=xcb
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
# CPU 变体：清理 torch 带来的 CUDA 运行时。
#
# 【重要教训】不能按文件名全目录搜删 libcudnn* 之类：ctranslate2 的 Linux 轮子
# 在编译时就把自带的那份 cuDNN 写进了 ELF 的 DT_NEEDED，属于硬依赖 ——
# 即便只做 CPU 推理，该文件缺失也会让整个 ctranslate2 加载失败，报
#   "libcudnn-<hash>.so.8.9.7: 无法打开共享目标文件"
# 导致 Argos 离线翻译彻底不可用。
#
# 因此这里【只】删除 torch 的 CUDA 运行时(_internal/nvidia 与 torch/lib 下的
# CUDA 库) —— 那些是 torch 按需动态加载的，CPU 版用不到、删了也不影响启动；
# 而 ctranslate2.libs/ 下的任何文件一律保留。
if [ "$BUILD_VARIANT" = "CPU" ]; then
    _appdir="${DESTDIR}/${APP_NAME}"
    _freed=0
    # 仅在 torch/lib 目录内按名字删（不波及 ctranslate2.libs 等其它目录）
    for _torchlib in "${_appdir}/_internal/torch/lib" "${_appdir}/torch/lib"; do
        [ -d "$_torchlib" ] || continue
        for _pat in 'libcudnn*' 'libcublas*' 'libcudart*' 'libcufft*' \
                    'libcurand*' 'libcusolver*' 'libcusparse*' 'libnccl*' \
                    'libnvrtc*' 'libcupti*' 'libnvToolsExt*' 'libnvJitLink*'; do
            while IFS= read -r -d '' _f; do
                _sz=$(stat -c%s "$_f" 2>/dev/null || echo 0)
                _freed=$((_freed + _sz))
                rm -f "$_f"
            done < <(find "$_torchlib" -maxdepth 1 -name "$_pat" -type f -print0 2>/dev/null)
        done
    done
    # nvidia 包目录整体移除（这是 CUDA 版 torch 的依赖包，CPU 版不需要）
    if [ -d "${_appdir}/_internal/nvidia" ]; then
        _sz=$(du -sb "${_appdir}/_internal/nvidia" 2>/dev/null | cut -f1)
        _freed=$((_freed + ${_sz:-0}))
        rm -rf "${_appdir}/_internal/nvidia"
    fi
    # 清理后校验：确认没有 .so 因删库而出现未满足的依赖。
    # 这是上一次事故的直接教训 —— 当时删掉了 ctranslate2 硬依赖的 cuDNN，
    # 编译过程毫无报错，直到用户点开 Argos 才发现整个库加载不了。
    if command -v ldd >/dev/null 2>&1; then
        _broken=""
        for _so in $(find "${_appdir}" -name "libctranslate2*.so*" \
                          -o -name "_ctranslate2*.so" 2>/dev/null | head -5); do
            if ldd "$_so" 2>/dev/null | grep -q "not found"; then
                _broken="${_broken} $(basename "$_so")"
            fi
        done
        if [ -n "$_broken" ]; then
            record_problem \
                "CUDA 清理后 ctranslate2 出现缺失依赖：${_broken}" \
                "Argos 离线翻译将完全无法加载" \
                "说明清理规则误删了硬依赖库，请检查 Build Linux.sh 的清理范围"
        else
            echo "      ✓ ctranslate2 依赖完整"
        fi
    fi
    if [ "$_freed" -gt 0 ]; then
        echo "    已清除 CUDA 库，节省 $((_freed / 1024 / 1024)) MB"
    fi
    # 清理后自检：确认程序仍能导入关键模块
    echo "    验证清理后依赖完整性..."
fi

# 图标 png 复制到产物根目录：Install.sh 要用它注册应用菜单图标，
# PyInstaller 的 --icon 只影响可执行文件自身，不会把源图放进产物。
if [ "$BUILD_VARIANT" = "GPU" ] && [ -f icon_gpu_1024.png ]; then
    cp icon_gpu_1024.png "${DESTDIR}/${APP_NAME}/" 2>/dev/null && \
        echo "    已附带 icon_gpu_1024.png（菜单图标）"
elif [ -f icon_1024.png ]; then
    cp icon_1024.png "${DESTDIR}/${APP_NAME}/" 2>/dev/null && \
        echo "    已附带 icon_1024.png（菜单图标）"
fi

# ---- 产物实物校验 ----
# 前面的检查看的是"编译过程有没有报错"，这里看的是"产物里到底有没有东西"。
# 两者缺一不可：曾出现过过程无报错、产物却缺模型的情况。
_appdir="${DESTDIR}/${APP_NAME}"
echo "    校验产物完整性..."

# 可执行文件
[ -x "${_appdir}/${APP_NAME}" ] || record_problem \
    "产物中缺少可执行文件 ${APP_NAME}" \
    "程序根本无法启动" \
    "检查上方 PyInstaller 输出是否有错误"

# 依赖目录
[ -d "${_appdir}/_internal" ] || record_problem \
    "产物中缺少 _internal 目录" \
    "所有依赖库缺失，程序无法启动" \
    "检查 PyInstaller 是否正常完成"

# Argos 离线翻译模型
_n_argos=$(find "${_appdir}" -name "*.argosmodel" -size +30M 2>/dev/null | wc -l)
if [ "${_n_argos}" -lt 2 ]; then
    record_problem \
        "产物内的 Argos 模型不足（找到 ${_n_argos} 个，应为 2 个）" \
        "离线翻译在用户端不可用" \
        "确认 argos_models/ 下两个 .argosmodel 均完整后重新编译"
else
    echo "      ✓ Argos 离线翻译模型 ${_n_argos} 个"
fi

# GPU 变体：反过来必须【确认 CUDA 组件在位】。
# GPU 版若体积与 CPU 版相当，基本就是 CUDA 没进去 —— 那样它名为 GPU 版
# 却完全无法加速，用户下载数 GB 后才发现，必须在此拦截。
if [ "$BUILD_VARIANT" = "GPU" ]; then
    _cuda_n=$(find "${_appdir}" \( -name "libcudnn*" -o -name "libcublas*" \
                  -o -name "libcudart*" \) -size +10M 2>/dev/null | wc -l)
    _torch_sz=$(du -sm "${_appdir}/_internal/torch" 2>/dev/null | cut -f1)
    _torch_sz="${_torch_sz:-0}"
    if [ "$_cuda_n" -lt 1 ] || [ "$_torch_sz" -lt 1200 ]; then
        record_problem \
            "GPU 产物内缺少 CUDA 组件（CUDA 库 ${_cuda_n} 个，torch 目录 ${_torch_sz} MB）" \
            "该产物无法使用显卡加速，与 CPU 版无异 —— 不应作为 GPU 版发布" \
            "确认已安装 CUDA 版 torch(版本号应含 +cu)；如复用了旧环境，删除 ${VENV_DIR} 后重编"
    else
        echo "      ✓ CUDA 组件 ${_cuda_n} 个，torch 目录 ${_torch_sz} MB"
    fi
fi

# Kokoro 朗读模型权重。
# 只数文件个数不够 —— 别的库里也可能有同后缀的文件混进来，导致明明模型
# 没下载成功却报"✓ 1 个"。这里要求：权重文件必须大于 80MB（Kokoro-82M 的
# 真实体积约 330MB，其它库的同后缀文件远小于此），且必须位于打包进来的
# kokoro_model 目录内。
_kok_real=$(find "${_appdir}" -path "*kokoro_model*" \
            \( -name "*.pth" -o -name "*.safetensors" -o -name "*.onnx" \) \
            -size +80M 2>/dev/null | wc -l)
if [ "${_kok_real}" -lt 1 ]; then
    # 放宽一次：不限目录，但仍要求 >80MB，兼容目录结构变化
    _kok_real=$(find "${_appdir}" \
                \( -name "kokoro*.pth" -o -name "kokoro*.safetensors" \) \
                -size +80M 2>/dev/null | wc -l)
fi
if [ "${_kok_real}" -lt 1 ]; then
    _kok_any=$(find "${_appdir}" \( -name "*.pth" -o -name "*.safetensors" \) \
               -size +10M 2>/dev/null | wc -l)
    record_problem \
        "产物内没有 Kokoro 模型权重（找到 ${_kok_any} 个疑似文件，但均不足 80MB）" \
        "离线朗读在用户端必须联网首次下载；无网环境完全不可用" \
        "先确保模型下到 ~/EnglishCoach Models/Kokoro/（应含 kokoro-v1_0.pth，约 330MB）再重新编译"
else
    echo "      ✓ Kokoro 模型权重 ${_kok_real} 个（>80MB）"
fi

# 音色文件：中文/英文嗓音各需对应的 voices/*.pt，缺了照样要联网
_voice_n=$(find "${_appdir}" -path "*voices*" -name "*.pt" 2>/dev/null | wc -l)
if [ "${_voice_n}" -lt 1 ]; then
    record_problem \
        "产物内没有 Kokoro 音色文件（voices/*.pt）" \
        "即便模型在位，切换嗓音时仍会联网下载音色，离线不可用" \
        "预下载须使用 HF 缓存结构（本脚本已改为此方式），请重新执行预下载步骤"
else
    echo "      ✓ Kokoro 音色文件 ${_voice_n} 个"
fi

# 打包后结算：产物已生成但内容不合格，同样阻断，避免误当成品发布
gate_check

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
# ---- 最终守卫：总体积合理性 ----
# 体积是最直观的完整性信号。CPU 版低于 1.2GB 基本意味着模型或依赖没进去；
# GPU 版低于 3GB 说明 CUDA 没打进来（这正是"GPU 版只有 1.1GB"的情形）。
_total_mb=$(du -sm "${DESTDIR}/${APP_NAME}" 2>/dev/null | cut -f1)
_total_mb="${_total_mb:-0}"
echo "    产物总体积: ${_total_mb} MB"
if [ "$BUILD_VARIANT" = "GPU" ]; then
    _min_mb=3000
    _hint="GPU 版应含 CUDA 组件（通常 6-10GB）。体积接近 CPU 版即说明装成了 CPU 版 torch"
else
    _min_mb=1200
    _hint="CPU 版通常 1.5-2.5GB。明显偏小说明模型或依赖未打包进来"
fi
if [ "${_total_mb}" -lt "${_min_mb}" ]; then
    record_problem \
        "产物总体积仅 ${_total_mb} MB，低于 ${BUILD_VARIANT} 版的合理下限 ${_min_mb} MB" \
        "几乎可以肯定有组件未打包进去，该产物不应发布" \
        "${_hint}；请检查上方各步骤输出"
fi

# 打包前最后结算
gate_check

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
