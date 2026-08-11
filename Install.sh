#!/usr/bin/env bash
# =============================================================================
#  English Coach — Linux 安装脚本 / Linux installer
#
#  把程序安装到标准位置，并在应用菜单中创建入口。
#  Installs the program to a standard location and adds an application-menu entry.
#
#  用法 / Usage:
#      ./Install.sh              # 安装到当前用户（无需 sudo）/ per-user, no sudo
#      sudo ./Install.sh --system   # 安装给所有用户 / for all users
#
#  卸载请运行同目录的 Uninstall.sh / To remove, run Uninstall.sh in this folder.
# =============================================================================
set -euo pipefail

APP_NAME="English Coach"
SLUG="englishcoach"

# 脚本所在目录（即解压出来的产物目录），路径含空格也安全
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SYSTEM=0
for arg in "$@"; do
    case "$arg" in
        --system) SYSTEM=1 ;;
        -h|--help)
            sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "未知参数: $arg"; exit 1 ;;
    esac
done

if [ "$SYSTEM" = "1" ]; then
    if [ "$(id -u)" != "0" ]; then
        echo "✗ --system 需要 root 权限，请用： sudo ./Install.sh --system"
        exit 1
    fi
    TARGET_DIR="/opt/${SLUG}"
    DESKTOP_DIR="/usr/share/applications"
    ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
    SCOPE="所有用户 / all users"
else
    TARGET_DIR="${HOME}/.local/opt/${SLUG}"
    DESKTOP_DIR="${HOME}/.local/share/applications"
    ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
    SCOPE="当前用户 / current user"
fi

echo "==> English Coach 安装 / installer"
echo "    范围 / scope : ${SCOPE}"
echo "    目标 / target: ${TARGET_DIR}"
echo

# ---- 检查产物完整性 ----
if [ ! -f "${HERE}/${APP_NAME}" ]; then
    echo "✗ 在脚本所在目录找不到可执行文件 \"${APP_NAME}\""
    echo "  请确认本脚本与程序放在同一目录（解压后的目录内）。"
    exit 1
fi
if [ ! -d "${HERE}/_internal" ]; then
    echo "✗ 找不到 _internal 目录 —— 它包含全部依赖库，必须与可执行文件同在。"
    echo "  请重新完整解压压缩包，不要只复制单个文件。"
    exit 1
fi

# ---- 检查运行所需的系统库 ----
# 只提示不阻断：装到系统里没问题，但启动时会失败，提前说清楚
_missing=""
ldconfig -p 2>/dev/null | grep -q 'libxcb-cursor\.so'    || _missing="${_missing} libxcb-cursor0"
ldconfig -p 2>/dev/null | grep -q 'libxkbcommon-x11\.so' || _missing="${_missing} libxkbcommon-x11-0"
ldconfig -p 2>/dev/null | grep -q 'libGL\.so'            || _missing="${_missing} libgl1"
if [ -n "${_missing}" ]; then
    echo "  [!] 检测到缺少运行所需的系统库 / Missing system libraries:"
    for m in ${_missing}; do echo "        - $m"; done
    echo "      安装完才能正常启动 / The app cannot start until these are installed:"
    if command -v apt >/dev/null 2>&1; then
        echo "        sudo apt install -y${_missing}"
    elif command -v dnf >/dev/null 2>&1; then
        echo "        sudo dnf install -y xcb-util-cursor libxkbcommon-x11 mesa-libGL"
    elif command -v pacman >/dev/null 2>&1; then
        echo "        sudo pacman -S xcb-util-cursor libxkbcommon-x11"
    fi
    echo "      安装过程会继续。/ Installation will continue anyway."
    echo
fi

# ---- 复制程序 ----
echo "==> [1/4] 复制程序文件"
if [ -e "${TARGET_DIR}" ]; then
    echo "    检测到已安装版本，先移除旧版"
    rm -rf "${TARGET_DIR}"
fi
mkdir -p "$(dirname "${TARGET_DIR}")"
# 用 cp -a 保留权限；排除安装脚本自身，避免装进去造成困惑
mkdir -p "${TARGET_DIR}"
# 排除安装脚本自身，但【保留】卸载脚本 —— 用户日后要靠它卸载
( cd "${HERE}" && tar -cf - --exclude='./Install.sh' . ) \
  | ( cd "${TARGET_DIR}" && tar -xf - )
# 万一产物里没带卸载脚本，从脚本所在目录补一份
if [ ! -f "${TARGET_DIR}/Uninstall.sh" ] && [ -f "${HERE}/Uninstall.sh" ]; then
    cp "${HERE}/Uninstall.sh" "${TARGET_DIR}/Uninstall.sh"
fi
[ -f "${TARGET_DIR}/Uninstall.sh" ] && chmod +x "${TARGET_DIR}/Uninstall.sh"
chmod +x "${TARGET_DIR}/${APP_NAME}"
[ -f "${TARGET_DIR}/启动 English Coach.sh" ] && chmod +x "${TARGET_DIR}/启动 English Coach.sh"
find "${TARGET_DIR}" -maxdepth 1 -name '*.sh' -exec chmod +x {} \; 2>/dev/null || true

# ---- 图标 ----
echo "==> [2/4] 安装图标"
mkdir -p "${ICON_DIR}"
ICON_SRC=""
for cand in "${TARGET_DIR}/icon_1024.png" "${TARGET_DIR}/_internal/icon_1024.png"; do
    [ -f "$cand" ] && ICON_SRC="$cand" && break
done
if [ -n "${ICON_SRC}" ]; then
    cp "${ICON_SRC}" "${ICON_DIR}/${SLUG}.png"
    echo "    已安装图标"
else
    echo "    ! 未找到 icon_1024.png，菜单项将使用默认图标"
fi

# ---- 桌面项 ----
echo "==> [3/4] 创建应用菜单入口"
mkdir -p "${DESKTOP_DIR}"
# Exec 用绝对路径并转义空格（desktop 规范要求用反斜杠转义，不能用引号）
EXEC_PATH="${TARGET_DIR}/${APP_NAME}"
EXEC_ESCAPED="${EXEC_PATH// /\\ }"
cat > "${DESKTOP_DIR}/${SLUG}.desktop" << EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=English Coach
Name[zh_CN]=英语导师
GenericName=Translation and Speech Tool
GenericName[zh_CN]=翻译与朗读工具
Comment=Chinese-English translation, text-to-speech and karaoke subtitles
Comment[zh_CN]=中英翻译、语音朗读与卡拉OK字幕
Exec=${EXEC_ESCAPED}
Icon=${SLUG}
Terminal=false
Categories=Education;Utility;Office;
Keywords=translate;translation;english;speech;tts;翻译;英语;朗读;
StartupNotify=true
StartupWMClass=English Coach
EOF
chmod 644 "${DESKTOP_DIR}/${SLUG}.desktop"

# ---- 刷新缓存 ----
echo "==> [4/4] 刷新菜单与图标缓存"
command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f -t "$(dirname "$(dirname "$(dirname "${ICON_DIR}")")")" 2>/dev/null || true

echo
echo "✓ 安装完成 / Installation complete"
echo
echo "  启动方式 / How to launch:"
echo "    · 在应用菜单中搜索 “English Coach” 或 “英语导师”"
echo "      Search for \"English Coach\" in your application menu"
echo "    · 或在终端运行 / or from a terminal:"
echo "        \"${EXEC_PATH}\""
echo
echo "  卸载 / To uninstall:"
if [ "$SYSTEM" = "1" ]; then
    echo "    sudo \"${TARGET_DIR}/Uninstall.sh\" --system"
else
    echo "    \"${TARGET_DIR}/Uninstall.sh\""
fi
echo
echo "  若菜单里暂时看不到图标，注销后重新登录即可。"
echo "  If the entry does not appear yet, log out and back in."
