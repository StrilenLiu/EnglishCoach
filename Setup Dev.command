#!/usr/bin/env bash
# =============================================================================
#  English Coach — 源码开发环境一键配齐 / one-shot dev setup (macOS)
#
#  在「访达」中双击本文件即可运行 / Double-click this file in Finder.
#
#  README 承诺过不编译也能 python english_coach.py 直接跑，但光靠
#  pip install -r requirements.txt 是不够的：模型权重不是 pip 包，spaCy 的
#  英文模型又不在 PyPI 上。这个脚本把两件事一起做完。
#
#  装什么、从哪装，全部取自 english_coach.py 里的 _ASSETS 登记表。
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

# 双击运行时终端窗口会立刻关掉，留一下让人看见结果
echo
read -n 1 -s -r -p "完成，按任意键关闭…"
echo
