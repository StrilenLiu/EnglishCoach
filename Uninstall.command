#!/usr/bin/env bash
# =============================================================================
#  English Coach — macOS 卸载脚本 / macOS uninstaller
#
#  在「访达」中双击本文件即可运行。
#  Double-click this file in Finder to run it.
#
#  默认只删除应用本身，保留个人数据（翻译历史、设置与 API Key）。
#  运行时会询问是否一并删除。
#  By default only the app is removed; your translation history, settings and
#  API keys are kept. You will be asked whether to delete those as well.
# =============================================================================
set -euo pipefail

APP_NAME="English Coach"
APP_BUNDLE="${APP_NAME}.app"

echo "==> English Coach 卸载 / uninstaller"
echo

# ---- 查找已安装位置 ----
FOUND=()
for d in "/Applications" "${HOME}/Applications"; do
    [ -d "${d}/${APP_BUNDLE}" ] && FOUND+=("${d}/${APP_BUNDLE}")
done

if [ ${#FOUND[@]} -eq 0 ]; then
    echo "  未找到已安装的 ${APP_BUNDLE}。"
    echo "  ${APP_BUNDLE} was not found in /Applications or ~/Applications."
    echo
    read -n 1 -s -r -p "按任意键关闭 / Press any key to close"
    exit 0
fi

echo "  找到以下安装 / Found:"
for f in "${FOUND[@]}"; do echo "    ${f}"; done
echo

printf "确认删除应用？(y/N) "
read -r ans
case "$ans" in
    y|Y) ;;
    *) echo "已取消。"; read -n 1 -s -r -p "按任意键关闭"; exit 0 ;;
esac

echo "==> 移除应用"
for f in "${FOUND[@]}"; do
    if rm -rf "$f" 2>/dev/null; then
        echo "    已删除 ${f}"
    else
        echo "    需要管理员权限，尝试 sudo …"
        sudo rm -rf "$f" && echo "    已删除 ${f}"
    fi
done

# ---- 个人数据 ----
DATA_DIR="${HOME}/Library/Application Support/EnglishCoach"
PREF_FILE="${HOME}/Library/Preferences/com.strilen.EnglishCoach.plist"
PREF_ALT="${HOME}/Library/Preferences/com.Strilen.EnglishCoach.plist"
SAVED_STATE="${HOME}/Library/Saved Application State/com.strilen.EnglishCoach.savedState"

HAS_DATA=0
for p in "${DATA_DIR}" "${PREF_FILE}" "${PREF_ALT}" "${SAVED_STATE}"; do
    [ -e "$p" ] && HAS_DATA=1
done

if [ "${HAS_DATA}" = "1" ]; then
    echo
    echo "  以下为个人数据 / Personal data:"
    [ -e "${DATA_DIR}" ]    && echo "    ${DATA_DIR}   （翻译历史、运行日志）"
    [ -e "${PREF_FILE}" ]   && echo "    ${PREF_FILE}"
    [ -e "${PREF_ALT}" ]    && echo "    ${PREF_ALT}"
    [ -e "${SAVED_STATE}" ] && echo "    ${SAVED_STATE}"
    echo
    printf "是否一并删除？删除后无法恢复 (y/N) "
    read -r ans2
    case "$ans2" in
        y|Y)
            rm -rf "${DATA_DIR}" "${PREF_FILE}" "${PREF_ALT}" "${SAVED_STATE}"
            echo "    个人数据已删除"
            ;;
        *)
            echo "    个人数据已保留"
            ;;
    esac
fi

echo
echo "✓ 卸载完成 / Uninstalled"
echo
read -n 1 -s -r -p "按任意键关闭 / Press any key to close"
echo
