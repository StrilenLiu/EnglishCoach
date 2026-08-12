#!/usr/bin/env bash
# ============================================================================
#  English Coach — Linux GPU 版构建脚本 / Linux GPU build
#
#  与 CPU 版共用同一份构建逻辑，只是把 torch 换成 CUDA 版。
#  Shares all build logic with the CPU script; only the torch build differs.
#
#  用法 / Usage:
#      bash "Build Linux GPU.sh"
#
#  产物 / Output:
#      dist/Linux-x64-GPU/  与同名 tar.gz
#
#  适用对象 / Who needs this:
#      仅装有 NVIDIA 显卡且已安装显卡驱动的 Linux 用户。CUDA 运行时已随
#      torch 打包，用户【不需要】单独安装 CUDA Toolkit，但【必须】有驱动。
#      没有独立显卡的用户请用 CPU 版 —— 功能完全相同，只是离线朗读慢一些。
#
#      Only for Linux users with an NVIDIA card and its driver installed. The
#      CUDA runtime ships inside the torch wheels, so no separate CUDA Toolkit
#      is needed, but the driver is required. Everyone else should use the CPU
#      build: identical features, merely slower offline speech synthesis.
#
#  体积提醒 / Size warning:
#      CUDA 组件很大，产物通常 8-10GB，压缩后仍会超过 GitHub Release 的
#      单文件 2GiB 上限，需要用 7-Zip 分卷上传：
#          7z a -v1800m "EnglishCoach-<版本>-Linux-x64-GPU.7z" "dist/Linux-x64-GPU/English Coach/"*
#
#      The CUDA components are large: expect 8-10GB, which still exceeds the
#      2GiB per-file limit on GitHub Releases after compression. Split it with
#      7-Zip as shown above before uploading.
# ============================================================================
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if [ ! -f "Build Linux.sh" ]; then
    echo "✗ 找不到 \"Build Linux.sh\" —— 两个脚本必须放在同一目录。"
    echo "  Cannot find \"Build Linux.sh\"; both scripts must sit in the same folder."
    exit 1
fi

echo "============================================================"
echo "  English Coach — Linux GPU (CUDA) 构建"
echo "  使用独立的虚拟环境 .build-venv-gpu，与 CPU 版互不干扰"
echo "  Uses its own .build-venv-gpu, isolated from the CPU build"
echo "============================================================"
echo

# 通过环境变量切换变体，其余逻辑完全复用 CPU 脚本
BUILD_VARIANT=GPU bash "Build Linux.sh" "$@"
