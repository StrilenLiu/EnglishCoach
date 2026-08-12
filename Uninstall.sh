#!/usr/bin/env bash
# =============================================================================
#  English Coach — Linux 卸载脚本 / Linux uninstaller
#
#  用法 / Usage:
#      ./Uninstall.sh                 # 卸载当前用户的安装 / per-user install
#      sudo ./Uninstall.sh --system   # 卸载全系统安装 / system-wide install
#      ./Uninstall.sh --purge         # 同时删除个人数据（历史/日志/密钥）
#                                     # also remove personal data
# =============================================================================
set -euo pipefail

# 支持 CPU 与 GPU 两个变体：默认卸载 CPU 版，--gpu 卸载 GPU 版。
# 脚本若就在某个安装目录内，则按该目录自动判断。
SLUG="englishcoach"
DISPLAY_NAME="English Coach"
_self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${_self_dir}/English Coach GPU" ]; then
    SLUG="englishcoach-gpu"
    DISPLAY_NAME="English Coach GPU"
fi

SYSTEM=0
PURGE=0
for arg in "$@"; do
    case "$arg" in
        --system) SYSTEM=1 ;;
        --purge)  PURGE=1 ;;
        --gpu)    SLUG="englishcoach-gpu"; DISPLAY_NAME="English Coach GPU" ;;
        --cpu)    SLUG="englishcoach";     DISPLAY_NAME="English Coach" ;;
        -h|--help)
            sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "未知参数: $arg"; exit 1 ;;
    esac
done

if [ "$SYSTEM" = "1" ]; then
    if [ "$(id -u)" != "0" ]; then
        echo "✗ --system 需要 root 权限，请用： sudo ./Uninstall.sh --system"
        exit 1
    fi
    TARGET_DIR="/opt/${SLUG}"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
else
    TARGET_DIR="${HOME}/.local/opt/${SLUG}"
    DESKTOP_DIR="${HOME}/.local/share/applications"
    ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
fi

echo "==> ${DISPLAY_NAME} 卸载 / uninstaller"
echo "    程序目录 / program: ${TARGET_DIR}"
echo

FOUND=0
[ -d "${TARGET_DIR}" ] && FOUND=1
[ -f "${DESKTOP_DIR}/${SLUG}.desktop" ] && FOUND=1
if [ "$FOUND" = "0" ]; then
    echo "  未找到已安装的 ${DISPLAY_NAME}。"
    echo "  Nothing to remove at the location above."
    if [ "$SYSTEM" = "0" ]; then
        echo "  若当初是全系统安装，请用： sudo ./Uninstall.sh --system"
    fi
    exit 0
fi

printf "确认卸载？(y/N) "
read -r ans
case "$ans" in
    y|Y) ;;
    *) echo "已取消。"; exit 0 ;;
esac

echo "==> 移除程序文件"
rm -rf "${TARGET_DIR}"

echo "==> 移除菜单入口与图标"
rm -f "${DESKTOP_DIR}/${SLUG}.desktop"
rm -f "${ICON_DIR}/${SLUG}.png"

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f -t "$(dirname "$(dirname "$(dirname "${ICON_DIR}")")")" 2>/dev/null || true

# ---- 个人数据 ----
DATA_DIR="${HOME}/.local/share/EnglishCoach"
CONF_DIR="${HOME}/.config/Strilen"
if [ "$PURGE" = "1" ]; then
    echo "==> 移除个人数据（翻译历史、运行日志、API Key）"
    rm -rf "${DATA_DIR}" "${CONF_DIR}"
    echo "    已删除"
else
    if [ -d "${DATA_DIR}" ] || [ -d "${CONF_DIR}" ]; then
        echo
        echo "  个人数据已保留 / Personal data kept:"
        [ -d "${DATA_DIR}" ] && echo "    ${DATA_DIR}   （翻译历史、运行日志）"
        [ -d "${CONF_DIR}" ] && echo "    ${CONF_DIR}   （设置与 API Key）"
        echo "  如需一并删除，请重新运行并加 --purge"
        echo "  To remove these as well, re-run with --purge"
    fi
fi

echo
echo "✓ 卸载完成 / Uninstalled"
