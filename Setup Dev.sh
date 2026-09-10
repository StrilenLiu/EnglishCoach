#!/usr/bin/env bash
# =============================================================================
#  English Coach — 源码开发环境一键配齐 / one-shot dev setup (Linux)
#
#  README 承诺过不编译也能 python english_coach.py 直接跑，但光靠
#  pip install -r requirements.txt 是不够的：模型权重不是 pip 包，spaCy 的
#  英文模型又不在 PyPI 上。这个脚本把两件事一起做完。
#
#  用法 / Usage:
#      ./Setup Dev.sh              # 缺什么装什么
#      ./Setup Dev.sh --force      # 已有的也重新下
#      ./Setup Dev.sh whisper      # 只装指定的几样
#
#  装什么、从哪装，全部取自 english_coach.py 里的 _ASSETS 登记表，
#  本脚本不重复维护地址。
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
echo "==> Python: $("$PY" -V 2>&1)  ($(command -v "$PY"))"

echo "==> [1/2] 安装 pip 依赖"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

echo "==> [2/2] 下载组件与模型"
"$PY" setup_assets.py "$@"
