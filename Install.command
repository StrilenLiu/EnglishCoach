#!/usr/bin/env bash
# =============================================================================
#  English Coach — macOS 安装脚本 / macOS installer
#
#  在「访达」中双击本文件即可运行。
#  Double-click this file in Finder to run it.
#
#  它做三件事 / It does three things:
#    1. 把 English Coach.app 复制到「应用程序」文件夹
#       Copies English Coach.app into your Applications folder
#    2. 移除隔离标记 —— 本程序未做代码签名，不移除的话首次打开会被系统拦截
#       Removes the quarantine flag: the app is unsigned, so without this
#       macOS refuses to open it the first time
#    3. 在启动台中注册，使其立即可见
#       Registers it with Launch Services so it shows up right away
#
#  卸载请运行同目录的 Uninstall.command / To remove, run Uninstall.command.
# =============================================================================
set -euo pipefail

APP_NAME="English Coach"
APP_BUNDLE="${APP_NAME}.app"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> English Coach 安装 / installer"
echo

# ---- 定位 .app ----
SRC=""
for cand in "${HERE}/${APP_BUNDLE}" "${HERE}/dist/${APP_BUNDLE}"; do
    [ -d "$cand" ] && SRC="$cand" && break
done
if [ -z "${SRC}" ]; then
    echo "✗ 在脚本所在目录找不到 \"${APP_BUNDLE}\""
    echo "  请把本脚本与 .app 放在同一目录（解压后的目录内）后重试。"
    echo
    echo "  Could not find \"${APP_BUNDLE}\" next to this script."
    read -n 1 -s -r -p "按任意键关闭 / Press any key to close"
    exit 1
fi

# ---- 选择安装位置 ----
if [ -w "/Applications" ]; then
    DEST_DIR="/Applications"
    SCOPE="所有用户 / all users"
else
    DEST_DIR="${HOME}/Applications"
    mkdir -p "${DEST_DIR}"
    SCOPE="当前用户 / current user"
    echo "    /Applications 不可写，改装到 ${DEST_DIR}"
fi
DEST="${DEST_DIR}/${APP_BUNDLE}"

echo "    来源 / source: ${SRC}"
echo "    目标 / target: ${DEST}"
echo "    范围 / scope : ${SCOPE}"
echo

# ---- 复制 ----
echo "==> [1/3] 复制应用"
if [ -d "${DEST}" ]; then
    echo "    检测到已安装版本，先移除旧版"
    rm -rf "${DEST}"
fi
# -R 保留符号链接与包结构；路径含空格已全部加引号
cp -R "${SRC}" "${DEST}"

# ---- 移除隔离标记 ----
echo "==> [2/3] 移除隔离标记（未签名应用必需）"
if xattr -rd com.apple.quarantine "${DEST}" 2>/dev/null; then
    echo "    已移除"
else
    echo "    ! 移除失败或本就没有隔离标记"
    echo "      若首次打开被拦截，请到「系统设置 → 隐私与安全性」点『仍要打开』"
fi
chmod -R u+rwX "${DEST}" 2>/dev/null || true

# ---- 注册到启动台 ----
echo "==> [3/3] 注册到启动台"
LSREG="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
[ -x "${LSREG}" ] && "${LSREG}" -f "${DEST}" 2>/dev/null || true
echo "    完成"

echo
echo "✓ 安装完成 / Installation complete"
echo
echo "  启动方式 / How to launch:"
echo "    · 打开「启动台」或「应用程序」文件夹，点击 English Coach"
echo "      Open Launchpad or the Applications folder and click English Coach"
echo
echo "  卸载 / To uninstall: 运行同目录的 Uninstall.command"
echo
read -n 1 -s -r -p "按任意键关闭 / Press any key to close"
echo
