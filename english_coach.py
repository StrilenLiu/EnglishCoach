# English Coach (英语导师) — 翻译 + 朗读 学习助手
# Copyright (C) 2026 Strilen Liu <vfx@strilen.com>  https://www.strilen.com
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# <https://www.gnu.org/licenses/>
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EnglishCoach - 英语助手工具
第一版 (v1.0.0)

功能:
    - 翻译 (默认 Google 免费引擎; DeepL / DeepSeek 可在设置中作为备选)
    - 朗读 (edge-tts 在线 TTS, 多嗓音 / 语速)
    - 版本更新说明与管理
    - 关于
    - Readme / 帮助文档与使用说明
    - 开发者介绍
    - 图标系统 (内置 SVG)

作者: Strilen  (vfx@strilen.com  |  www.strilen.com)
"""

import sys
import os
import json
import re
import asyncio
import tempfile
import traceback


# =============================================================================
#  Argos 离线翻译兼容层（必须在任何 argostranslate 导入之前执行）
#  目的：让 Argos 在无 PyTorch、Big Sur 等受限环境下也能离线翻译。
#    1) 注入假 stanza 模块，骗过顶层 import 与运行时的 Pipeline 调用，甩掉 torch
#    2) 设 stanza_available=True，绕过缺 sbd 包导致语言被过滤为空的问题
#    3) 把模型目录锁定到程序内置 / 用户数据目录（解决"装了读不到"）
# =============================================================================

def _setup_argos_compat():
    import types
    # —— 1) 假 stanza（带断句 Pipeline）——
    if "stanza" not in sys.modules:
        fake = types.ModuleType("stanza")

        class _FakeStanzaPipeline:
            def __init__(self, *a, **k):
                pass

            def __call__(self, text):
                # 简单按整段返回单句，断句交给上层；够 Argos 用
                class _Sentence:
                    def __init__(self, t):
                        self.text = t

                class _Doc:
                    sentences = [_Sentence(text)]
                return _Doc()

        fake.Pipeline = _FakeStanzaPipeline
        fake.download = lambda *a, **k: None
        sys.modules["stanza"] = fake


def _configure_argos_dirs():
    """把 Argos 的模型读取/写入目录都锁定到同一处。返回 (target, bundled)。"""
    from pathlib import Path
    import argostranslate.settings as s
    # 程序内置模型目录（打包后在 _MEIPASS/argos_models）
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    bundled = os.path.join(base, "argos_models")
    # 用户数据目录（运行期实际安装位置，避免只读问题）
    user_dir = os.path.join(
        os.path.expanduser("~"), ".englishcoach", "argos_packages")
    os.makedirs(user_dir, exist_ok=True)
    target = Path(user_dir)
    s.package_dirs = [target]
    s.package_data_dir = target
    s.stanza_available = True   # 关键：别因缺 sbd 包过滤掉语言
    return target, bundled


def _ensure_argos_models(required=("en", "zh")):
    """确保所需语言模型已安装；缺失则从内置目录安装。幂等、可重复调用。
    返回 True 表示所需语言齐备。"""
    try:
        target, bundled = _configure_argos_dirs()
        import argostranslate.package as ap
        import argostranslate.translate as at
        have = {l.code for l in at.get_installed_languages()}
        if all(c in have for c in required):
            return True
        # 缺失 -> 从内置 .argosmodel 安装
        if os.path.isdir(bundled):
            for fn in sorted(os.listdir(bundled)):
                if fn.endswith(".argosmodel"):
                    try:
                        ap.install_from_path(os.path.join(bundled, fn))
                    except Exception:
                        pass
        have = {l.code for l in at.get_installed_languages()}
        return all(c in have for c in required)
    except Exception:
        return False


_setup_argos_compat()

import requests
import edge_tts

from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QSize, QUrl, QSettings,
                          QTimer, QBuffer, QByteArray, QIODevice, QElapsedTimer)
from PyQt6.QtGui import (QIcon, QPixmap, QFont, QAction,
                         QSyntaxHighlighter, QTextCharFormat, QColor)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel, QSlider, QToolBar,
    QStatusBar, QDialog, QDialogButtonBox, QLineEdit, QFormLayout,
    QTextBrowser, QMessageBox, QSplitter, QFrame, QSizePolicy,
    QCheckBox, QScrollArea
)

# =============================================================================
#  应用元信息 / 版本管理
# =============================================================================

APP_NAME = "EnglishCoach"
APP_VERSION = "2.5.1"
APP_AUTHOR = "Strilen"
APP_EMAIL = "vfx@strilen.com"
APP_WEBSITE = "www.strilen.com"

# 统一按钮标准宽度（以"显示/隐藏"按钮为准）
BTN_W = 96

# 数字/符号 -> 名称（用于"单个符号或数字串"特殊翻译模式）
_DIGIT_EN = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
             "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}
_DIGIT_ZH = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四",
             "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}
_SYM_EN = {",": "comma", "，": "comma", ".": "period", "。": "period",
           "!": "exclamation mark", "！": "exclamation mark",
           "?": "question mark", "？": "question mark", ";": "semicolon",
           "；": "semicolon", ":": "colon", "：": "colon", "+": "plus",
           "-": "minus", "*": "asterisk", "/": "slash", "=": "equals",
           "%": "percent", "$": "dollar", "#": "hash", "@": "at", "&": "ampersand",
           "(": "left parenthesis", ")": "right parenthesis",
           "（": "left parenthesis", "）": "right parenthesis"}
_SYM_ZH = {",": "逗号", "，": "逗号", ".": "句号", "。": "句号",
           "!": "感叹号", "！": "感叹号", "?": "问号", "？": "问号",
           ";": "分号", "；": "分号", ":": "冒号", "：": "冒号", "+": "加号",
           "-": "减号", "*": "星号", "/": "斜杠", "=": "等号", "%": "百分号",
           "$": "美元符", "#": "井号", "@": "艾特", "&": "和号",
           "(": "左括号", ")": "右括号", "（": "左括号", "）": "右括号"}


def _app_data_dir():
    """系统约定的用户级应用数据目录。
    Windows: %APPDATA%\\EnglishCoach ；macOS: ~/Library/Application Support/EnglishCoach；
    其它: ~/.local/share/EnglishCoach。返回路径并确保存在。"""
    import os, sys
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    d = os.path.join(base, APP_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        d = os.path.expanduser("~")
    return d

HISTORY_FILE = None    # 延迟初始化
LOG_FILE = None

def _history_path():
    global HISTORY_FILE
    if HISTORY_FILE is None:
        import os
        HISTORY_FILE = os.path.join(_app_data_dir(), "翻译历史.txt")
    return HISTORY_FILE

def _log_path():
    global LOG_FILE
    if LOG_FILE is None:
        import os
        LOG_FILE = os.path.join(_app_data_dir(), "运行日志.txt")
    return LOG_FILE

def _log_error(msg):
    """把出错记录追加到日志文件（带时间戳）。"""
    import datetime
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

# 历史记录用 Markdown 文本格式存储：人可读，任意文本/浏览器打开都清晰；
# 每条以 "## " 开头便于解析回结构。
_HIST_SEP = "\n\n---\n\n"

def _load_history():
    import os, re
    p = _history_path()
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return []
    items = []
    for block in raw.split(_HIST_SEP):
        block = block.strip()
        if not block.startswith("## "):
            continue
        try:
            header = block.splitlines()[0][3:].strip()
            parts = header.split(" · ")
            ts = parts[0].strip()
            engine = parts[1].strip() if len(parts) > 1 else ""
            body = block.split("\n", 1)[1] if "\n" in block else ""
            src = ""; tgt = ""
            if "【原文】" in body:
                after = body.split("【原文】", 1)[1]
                if "【译文】" in after:
                    src, tgt = after.split("【译文】", 1)
                else:
                    src = after
            items.append({"ts": ts, "engine": engine,
                          "src": src.strip(), "tgt": tgt.strip()})
        except Exception:
            continue
    return items

def _save_history(items):
    blocks = []
    for it in items[-500:]:
        blocks.append(
            f"## {it.get('ts','')} · {it.get('engine','')}\n\n"
            f"【原文】{it.get('src','')}\n\n"
            f"【译文】{it.get('tgt','')}")
    try:
        with open(_history_path(), "w", encoding="utf-8") as f:
            f.write("# EnglishCoach 翻译历史" + _HIST_SEP)
            f.write(_HIST_SEP.join(blocks))
            f.write("\n")
    except Exception as e:
        _log_error(f"保存历史失败: {e}")

def _add_history(src_text, tgt_text, engine):
    """新增一条翻译历史。返回更新后的列表。"""
    import datetime
    if not src_text.strip():
        return _load_history()
    items = _load_history()
    if items and items[-1].get("src") == src_text.strip():
        return items
    items.append({
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "src": src_text.strip(), "tgt": tgt_text.strip(), "engine": engine,
    })
    _save_history(items)
    return items

# 版本更新说明 —— 以后每版在最前面追加一条记录即可
CHANGELOG = [
    {
        "version": "2.5.1",
        "date": "2026-07-04",
        "title": "跨侧续播回位 · 换嗓保字幕保选区(根治) · 光标处粘贴 · 单实例守护",
        "notes": [
            "跨侧暂停后回来点继续，从暂停位置续播不再从头：暂停位置存入该侧缓存，重播时自动定位；同侧继续/按停止会正确清零",
            "换嗓/引擎重读根治两处：①重读时沿用原选区（此前重新推导误判为读全文并清掉蓝色选区）②为重读而停被误当自然播完、250ms后清绿——preserve期间跳过收尾",
            "粘贴细化：主动区有明确光标位置时粘贴到光标处；从属区且无选区才默认贴到末尾",
            "新增单实例守护（QLockFile）：程序已在运行时再次启动会提示并退出，修复偶发双开",
        ],
    },
    {
        "version": "2.5.0",
        "date": "2026-07-03",
        "title": "缓存直播/真清空 · 换嗓保位保字幕 · 数字翻译修复+小数 · 选区复制粘贴 · 混合文本翻译",
        "notes": [
            "有音频缓存时点朗读直接重播（分侧缓存命中），不再重新生成；清空钮改为真清（同步清掉旧全局缓存，重播不再复活）",
            "换嗓音/引擎重读：卡拉OK绿色与蓝/灰选区随进度条一并保持；播放或暂停中切换嗓音必定触发重新生成（修复偶发不触发）",
            "修复强制中/英数字翻译失效根因：目标判断只比对『英语』而下拉项是『English』永不命中；88 现按目标正确输出中/英两式",
            "原文/译文语言下拉变化即强制重新翻译（等同点翻译按钮）；翻译大按钮无条件重翻",
            "数字支持小数：888.89 → 逐位拼读(含点/point) + 数学读法（八百八十八点八九 / point eight nine）",
            "复制/粘贴选区感知：有蓝/灰选区只复制或只覆盖选中部分；无选区复制全部、粘贴默认到末尾",
            "修复混合中英文本翻译：自动检测含中日韩字符时显式声明源为中文，Google 不再 en→en 原样返回（『中文』二字现在会被翻译）",
            "底部忙碌进度条改自绘胶囊：滑块滑到两端也保持圆角（Qt原生样式两端变方的限制已绕开）",
        ],
    },
    {
        "version": "2.4.0",
        "date": "2026-07-03",
        "title": "多风格翻译修复+单词多译法 · 进度条冻结 · 载入下一条 · 按钮语义与间距",
        "notes": [
            "修复多风格翻译失效根因：导入过一次文件后残留路径会永久禁用多风格，改为仅在原文与导入内容一致时禁用",
            "多风格新增单词模式：输入单字/词（中文≤4字或英文单词）输出多种准确译法，每行一个，无解释无音标；词组/句子仍按书面/口语/正式等风格分类",
            "朗读钮颜色语义严格化：缓存有音频=青色，无=灰色；播放到头/拖到最右不再误变灰",
            "更改嗓音/引擎重读时，进度条冻结在当前位置，生成完成后就地续播，不再跳回开头",
            "新增『载入下一条原文』按钮（上一条右侧，镜像图标），双向循环历史",
            "设置弹窗保存钮改蓝色，取消保持灰色",
            "按钮组间距统一为10px（对标顶排语言框与交换钮间距）",
        ],
    },
    {
        "version": "2.3.1",
        "date": "2026-07-03",
        "title": "修复样式表整表失效(按钮丢样式元凶) · 控件统一加高 · 音频/文字清空分离",
        "notes": [
            "根因修复：样式表为三段拼接，占位符替换只作用于最后一段，残留占位符导致整表解析失败被丢弃——翻译钮丢蓝色、按钮变矮变形的元凶",
            "翻译大按钮恢复蓝色并加圆角；朗读钮青色态加圆角；导入钮变青后不再缩小",
            "所有下拉框/按钮统一加高到34px，图标钮改正方形，交换钮不再偏矮",
            "气球提示外框缩小约20%并改圆角",
            "翻译历史弹窗：检查历史去掉蓝色，关闭钮改蓝色，与关于/说明弹窗统一",
            "朗读语速滑杆两侧统一灰色（不再左蓝右灰），与播放进度条区分",
            "主动/从属切换补修：切换后新从属区正确显示灰色选区（去掉误清联动的旧逻辑）",
            "原生滚动条模式下文本框右内边距 20px 恢复为 8px，滚动条贴右不再有空隙",
            "朗读区新增音频清空钮（原文/译文各一，下载钮右侧）：仅释放该侧音频缓存，朗读钮变灰、下载失效",
            "原文/译文区文字清空钮改为只清文字与导入文件，不再清音频（文字与音频清空分离）",
        ],
    },
    {
        "version": "2.3.0",
        "date": "2026-07-02",
        "title": "主动区点击切换重构 · 原生胶囊滚动条(Mac/Win11) · 高亮清除根治 · 清空按钮重做",
        "notes": [
            "主动/从属区重构：鼠标按下即切换（点文字或空白都生效），只有一个蓝框；从属区灰色选区点击后变蓝，原主动区蓝选区自动转灰",
            "点击当前主动区：保持主动，仅清掉两侧联动选区",
            "改字清高亮根治：真实变更时掐断卡拉OK定时器、清词边界、停联动防抖、作废对齐表；边界过期自动熔断，绿色不再被画回",
            "改字时若该侧正在朗读，自动停止朗读（读的已是旧内容）",
            "滚动条：Mac 与 Win11(Qt>=6.7) 用系统原生胶囊；Win10及以下/Linux用自定义样式；全局样式解毒（QWidget规则改为调色板，不再污染滚动条）",
            "清空按钮移位：原文清空钮在翻译历史右侧（隔开），译文清空钮在最右侧（隔开）",
            "清空增强：原文清空=清文字+清导入(钮变灰)+译文随清+双侧音频释放(朗读/下载钮变灰)+导出钮隐藏；译文清空=清文字+译文音频释放",
        ],
    },
    {
        "version": "2.2.2",
        "date": "2026-07-01",
        "title": "根治选区朗读失效（高亮反馈环彻底消灭）",
        "notes": [
            "根因：停止/清除卡拉OK时 rehighlight 触发 textChanged，被误判为用户改字，导致选区信息被抹掉、自动翻译误触发、离线嗓音卡拉OK从全文扫（看似在读全文）",
            "根治：textChanged 处理器入口做文本比对——内容没变（仅格式重绘）直接跳过，一劳永逸消灭此类误伤",
            "选区朗读现在全程保留选区：蓝色底色、卡拉OK范围、边界估算都只在选区内",
        ],
    },
    {
        "version": "2.2.1",
        "date": "2026-07-01",
        "title": "修复选区朗读被三态切换吃掉的问题",
        "notes": [
            "修复：选中一段文字再点朗读钮，会被『暂停/继续』三态切换拦截而继续播旧音频（v2.1.2 引入）",
            "现在：只要该区有新的选区（与当前朗读内容不同），点朗读钮即停掉旧音频、只朗读选区",
        ],
    },
    {
        "version": "2.2.0",
        "date": "2026-07-01",
        "title": "主动/从属区单蓝框 · 两侧独立音频缓存 · 高亮清除与导出钮修复 · Mac原生滚动条",
        "notes": [
            "主动区只保留一个蓝框（去掉 :focus 导致的第二个蓝框），从属区灰框",
            "两侧朗读音频各自独立缓存：朗读钮青色=音频在内存可下载，灰色=无音频不可下载",
            "改动某侧文字，该侧音频缓存作废、朗读钮变灰、下载禁用；停止后若音频仍在内存则钮保持青色、进度归零",
            "跨侧朗读：一侧朗读时点另一侧，先暂停该侧（进度保留、青色继续态）再读另一侧",
            "彻底修复文字变更时蓝色选区/绿色卡拉OK未清除（根因：译文区未监听 textChanged + guard 误伤，改用精确 _highlighting 标记）",
            "修复导出翻译后文件按钮显隐（根因：setPlainText 时序竞争，导入状态改为先记录后填文本）",
            "Mac 使用系统原生胶囊滚动条（无灰槽、自动隐藏）；Windows 保留自定义细样式",
            "最小窗口宽度调整为 720（较原缩小约 400px）",
        ],
    },
    {
        "version": "2.1.3",
        "date": "2026-06-30",
        "title": "修复卡拉OK失效与停止键 · 跨侧朗读暂停 · 最小窗口缩小 · 多项细节",
        "notes": [
            "修复原文区卡拉OK字幕失效（高亮 rehighlight 触发 textChanged 误清高亮的反馈环）",
            "修复文字变更时蓝色选区/绿色字幕未清除（补上清蓝色选区）",
            "修复停止朗读键失效（暂停态下也能停止）",
            "跨侧朗读：一侧朗读时点另一侧，先把该侧暂停（进度保留、按钮青色继续态），再读另一侧",
            "设置面板 HY-MT Key 改为『混元 HY-MT Key』",
            "关于窗『英语导师』与『English Coach』同字号同颜色",
            "最小窗口宽度大幅缩小（960→620）",
            "语速气球拖动时持续显示、跟随滑块",
            "进度条/滚动条进一步圆角处理",
        ],
    },
    {
        "version": "2.1.2",
        "date": "2026-06-30",
        "title": "界面标签改气球提示 · 翻译按钮可靠性 · 朗读按钮三态 · 导出钮智能显隐",
        "notes": [
            "关于窗 English Coach 下方加副标题『英语导师』",
            "原文/译文文字变更时，自动清除蓝色选区高亮与卡拉OK绿色高亮",
            "翻译按钮修复点击无效问题；点翻译会先中断所有进行中的翻译再重新开始",
            "界面文字标签全部去除改为悬停气球提示（引擎/语言/嗓音/文字区/进度条/语速等）",
            "语速气球实时显示『朗读语速 正常 / +20% / -50%』",
            "引擎名缩短：GLM-4-Flash→GLM、HY-MT→混元；约束最小窗口宽度让交换钮居中",
            "导出翻译后文件按钮：平时隐藏，导入成功才出现（灰），翻译完成变青可点；原文与导入不一致则消失",
            "所有滚动条只留胶囊滑块，去掉深灰背景轨道；等待进度条去底槽、圆角胶囊形",
            "朗读按钮悬停三态：朗读原文/译文 → 暂停朗读 → 继续朗读，循环（并修复暂停图标不显示的 bug）",
        ],
    },
    {
        "version": "2.1.1",
        "date": "2026-06-30",
        "title": "修复 PDF 导出报错 · 文件名空格化 · 进度条与滚动条精修 · 交换钮居中",
        "notes": [
            "修复导出 PDF 报错（reportlab.pdfbase.pdfmetrics 导入路径）",
            "所有导出文件名分隔符由下划线改空格，如 EC ZH XiaoXiao 2026-06-30 013733.mp3",
            "状态栏进度条改极简药丸形（无外框、更细、半透明槽、青色块）",
            "拖文件到文本框任意位置=导入内容（不再粘贴文件名）",
            "原文/译文朗读进度条彻底分离，拖动互不影响",
            "翻译历史按钮改名：检查历史 / 下载文档",
            "文本框滚动条改 mac 风格细药丸、不再挡字",
            "交换钮用网格强制窗口居中；下拉框留白压到最小；原文语言/译文语言改名",
        ],
    },
    {
        "version": "2.1.0",
        "date": "2026-06-29",
        "title": "选区主动/从属双向联动 · 界面重排 · 文件导入导出完善",
        "notes": [
            "选区双向联动：原文↔译文互选都能定位（依据保存的句对应关系），译文区选择终于能联动原文区",
            "主动/从属区逻辑：选中区为主动区（蓝框蓝底），另一区为从属区（选区灰底）；点击从属区即切换",
            "状态栏『正在生成音频』改用消息区显示，与『翻译完成』等交替不重叠（修正上次实现方式）",
            "进度条改药丸形：细灰黑轮廓、透明外围、青色滚动块",
            "第一排重排：翻译引擎｜源语言｜交换(居中)｜目标语言｜设置区(右)",
            "操作排重排：原文｜复制粘贴清空｜导出原文+导入文件｜上一条+历史｜翻译｜…｜导出译文+导出文件｜译文",
            "导出文件名规则 OT/TT_语言_日期时间，历史 TH_日期时间；保存路径记忆",
            "PDF 导出改 A4 竖版自动换行（修右侧出画），中文字体 PingFang/思源黑体/雅黑回退",
            "清空原文→重置导入状态；清空译文→重置导出状态（青色恢复灰色）",
            "停止键分侧独立：原文停止只停原文，译文停止只停译文",
            "上一条原文改为循环遍历全部历史原文",
            "拖拽文件到窗口=导入文件内容；原文区右内边距加大，滚动条不再挡字",
            "按钮宽度统一（显示隐藏为准），所有 Close 改『关闭』；标题改 English Coach",
        ],
    },
    {
        "version": "2.0.0",
        "date": "2026-06-29",
        "title": "2.0 大改版：文件导入导出 · 朗读分原文/译文两组 · 多项修复",
        "notes": [
            "修复 Argos 离线翻译『出出出』重复退化（改为逐句翻译 + 重复压缩兜底）",
            "朗读控制分原文/译文两组，上移到复制粘贴排与嗓音排之间，按钮改纯图标方形",
            "新增导入文件（txt/docx/pdf，支持拖拽）：内容填入原文区并自动翻译，按钮变青色",
            "新增导出当前原文/译文文字（txt/md/docx/json/pdf）",
            "新增导出翻译后文件：docx 保留段落结构，文件名加 T 后缀；pdf 暂只读入不导出",
            "翻译历史新增多格式下载（txt/md/json/docx/pdf）",
            "数字/单符号特殊翻译：78→Seven Eight / seventy-eight（中英各两式）；逗号→comma/逗号",
            "文件导入翻译模式下，多风格翻译与符号翻译自动失效",
            "进度条改青色无外框，状态栏提示移到右侧不再重叠，Mac/Win 右侧留 5% 空隙",
            "设置窗取消/保存按钮统一右对齐",
            "模型目录更名为 EnglishCoach Models/Argos、EnglishCoach Models/Kokoro",
        ],
    },
    {
        "version": "1.9.6",
        "date": "2026-06-29",
        "title": "选区联动重做（句级对齐）· 朗读交互修复 · 状态栏与下拉修复",
        "notes": [
            "选区联动重新设计：翻译时按句建立原文↔译文对应，选区覆盖所有相关句（选全文即全亮）",
            "合成期间界面不变：已选区的蓝/灰背景在生成音频时保持显示",
            "改朗读引擎/嗓音时进度条不再跳回头、按钮保持青色『继续朗读』不闪",
            "朗读中点交换：立即终止朗读并清空音频缓存，自动重新翻译",
            "状态栏『正在生成音频』改为蓝底白字，与其它提示一致",
            "Mac 合成进度条左移，右侧留约 10% 空隙，构图匀称",
            "Windows 嗓音下拉滚轮不再滚出末尾空行",
        ],
    },
    {
        "version": "1.9.5",
        "date": "2026-06-28",
        "title": "更新应用图标",
        "notes": [
            "重绘应用图标：线条更圆润饱满，接近原生质感",
            "GPU 版图标补回 A/文 标牌（青绿底 + 闪电，与 CPU 版区分）",
        ],
    },
    {
        "version": "1.9.4",
        "date": "2026-06-28",
        "title": "朗读可中断 · 选区联动不再翻译 · GPU 图标 · 打包命名 · 多项修复",
        "notes": [
            "新增朗读中断：合成中按停止可中断（段边界软中断），并提示『正在停止…』",
            "选区联动改为按位置比例映射，完全不再调用翻译引擎（选译文不再触发自动翻译）",
            "新增 GPU 版专属图标（青绿底+闪电）",
            "Mac 打包为 English Coach.app；Win 打包为含 English Coach 文件夹与 English Coach.exe（GPU 版同理）",
            "选区强制蓝色背景（修复某些系统显示绿色）",
            "中文嗓音下拉加宽（Windows 不再截断），并去除末尾空行与多余滚动",
            "合成中『正在生成音频』文字持续到结束，进度条约占窗口 40% 居中偏右、右侧留白",
            "朗读中点交换内容会停止当前朗读，避免青绿字幕错位到对面",
        ],
    },
    {
        "version": "1.9.3",
        "date": "2026-06-28",
        "title": "修复中文离线朗读截断 · 译文区选区稳定 · 多项界面优化",
        "notes": [
            "修复中文离线朗读长文本被截断（按标点切句分段合成，避免 Kokoro token 上限静默截断）",
            "选区联动改为仅『原文→译文』单向，译文区选择不再被刷新重置",
            "翻译历史文件改为 txt 纯文本",
            "翻译历史按钮图标改为列表横线样式（与更新说明区分）",
            "翻译按钮用网格真正居中，不再因左侧按钮增多而偏右",
            "合成进度：文字并入左侧状态栏，进度条加长放右侧",
        ],
    },
    {
        "version": "1.9.2",
        "date": "2026-06-28",
        "title": "修复新环境 ctranslate2 因 setuptools 过新缺 pkg_resources",
        "notes": [
            "构建脚本在装 ctranslate2 前固定 setuptools<81，解决新版移除 pkg_resources 导致 Argos 离线翻译导入失败",
        ],
    },
    {
        "version": "1.9.1",
        "date": "2026-06-28",
        "title": "修复 Windows GPU 打包脚本无法运行（换行符与编码）",
        "notes": [
            "修复 Build Windows GPU.bat 因换行符为 LF、含中文注释导致命令被截断、无法运行",
            "所有 .bat 脚本统一为纯 ASCII + CRLF 换行（GBK 控制台安全）",
        ],
    },
    {
        "version": "1.9.0",
        "date": "2026-06-27",
        "title": "翻译按钮防闪 · 历史改 MD · 进度条优化 · GPU 打包脚本",
        "notes": [
            "翻译按钮文字不再变化（不闪动），状态提示移到底部状态栏",
            "翻译历史改用可读的 Markdown 文本格式（任意文本/浏览器打开都清晰，不再乱码）",
            "合成音频进度提示加文字『正在生成音频…』，进度条加长、左文右条、留白匀称",
            "上一条/历史按钮缩小到与复制粘贴一致，间距统一；撤回图标改为逆时针箭头",
            "按钮气泡提示字号缩小；历史弹窗内悬停气泡字号放大到正文大小",
            "暂停时拖动进度条，青色已读实时跟随（未松手也刷新）",
            "朗读按钮激活时喇叭图标同步反色",
            "选区联动响应更快，降低首次朗读读整段的概率",
            "新增 Windows GPU 加速打包脚本（EnglishCoach-GPU 环境 + CUDA），Kokoro 自动用 GPU",
            "构建脚本更名 Build MacOS.sh / Build Windows.bat / Build Windows GPU.bat",
        ],
    },
    {
        "version": "1.8.1",
        "date": "2026-06-27",
        "title": "中文离线朗读修复 · 选区联动位置加权 · 合成进度提示 · 多项打磨",
        "notes": [
            "修复中文离线朗读缺 pypinyin 等依赖（已补入打包）",
            "移除会 404 的 Bella+Sarah 混合音（HF 无该现成文件）",
            "选区联动加入位置加权与段落感知：相同词句按位置就近匹配，结果不再离谱",
            "合成语音较慢时状态栏提示，超过约 1 秒显示忙碌进度条",
            "历史弹窗：按钮改为『查看历史文档/重新载入/关闭』三等宽，预览限宽无横向滚动条",
            "上一条原文按钮换更大图标",
            "设置：显示隐藏与查看日志按钮等宽；取消/保存改中文并统一取消在左保存在右",
        ],
    },
    {
        "version": "1.8.0",
        "date": "2026-06-27",
        "title": "翻译历史 · 日志 · 修复 Kokoro 缺 ordered_set · Windows 图标",
        "notes": [
            "修复 Kokoro 缺少 ordered_set 依赖导致离线朗读不可用（已补入打包）",
            "新增翻译历史：原文区删除键右侧加『上一条原文』与『历史』两个按钮",
            "历史弹窗按天分组，每条显示开头提示，悬停蓝色高亮并气泡显示全文，点选可载入并翻译",
            "新增日志：出错记录写入用户数据目录，设置面板加『查看日志』按钮",
            "历史与日志统一存放在系统用户数据目录（win:%APPDATA% / mac:Application Support）",
            "Windows 应用图标改回铺满尺寸（不再显小）；macOS 图标不变",
            "选区联动匹配更智能：英文吸附到整词，不停在半个单词中间",
        ],
    },
    {
        "version": "1.7.1",
        "date": "2026-06-27",
        "title": "修复外置硬盘导致 Kokoro 不可用 · 朗读高亮与选区联动优化",
        "notes": [
            "修复 Kokoro 因 conda 在外置 SSD 上读时区文件被 macOS 拒绝（Operation not permitted）导致离线朗读不可用；自动改用系统时区库，并给出权限设置指引",
            "朗读高亮不再改变字色（黑字变白字），只改背景颜色，更清爽",
            "灰色联动区朗读时保持灰色，读到处变青色，读完恢复灰色（不再变蓝、不消失）",
            "下载音频记住上次选择的格式（wav/mp3）作为默认",
            "交换原文译文时，选区随之继承到新原文区并自动联动新译文区",
        ],
    },
    {
        "version": "1.7.0",
        "date": "2026-06-26",
        "title": "Kokoro 打包落地 · 音质提升 · 音频格式可选 · 设置面板优化",
        "notes": [
            "Kokoro 离线朗读依赖钉死兼容 Big Sur 的版本（torch 2.2.2 + transformers 4.40.2 + spaCy 英文模型）",
            "英文离线嗓音默认改为 Heart（盲测最像真人），新增 Nova 与 Bella+Sarah 混合音",
            "下载音频可选 wav（无损）或 mp3（压缩），按需转换",
            "Argos 离线模型缓存改放 EnglishCoach-models/argos 子目录（win/mac）",
            "帮助文档新增系统要求（macOS/Windows 版本、空间、未签名解除拦截等），便于分享",
            "设置：Key 输入框限宽右侧留白、显示/隐藏按钮居中、滚动条不再挡字、下拉悬停蓝色统一",
            "Key 标签简化（GPT/Gemini/GLM/豆包/HY-MT）",
            "构建脚本加固：醒目确认并强制校验 conda 环境，杜绝误装到 base",
        ],
    },
    {
        "version": "1.6.0",
        "date": "2026-06-26",
        "title": "修复闪退与 Kokoro 打包 · 重播缓存 · 多项界面优化",
        "notes": [
            "修复选择文字时的闪退（选区联动跨线程刷新高亮的崩溃，已加锁保护）",
            "修复 Kokoro 打包缺失 language_tags 等数据导致离线朗读不可用",
            "无变化时再次点朗读，直接重播已生成音频，不再重新合成",
            "修复原文区有选区时朗读，青色不覆盖蓝色选区的问题（与译文区一致）",
            "卡拉OK字幕提前量回调到中间值，更贴合声音",
            "选区联动匹配更稳，异常不再影响主流程",
            "引擎名简化：GPT / Gemini / GLM-4-Flash / 豆包 / HY-MT 等",
            "界面标签去掉冒号；『进度』改为『朗读进度』",
            "设置：显示隐藏按钮缩短、窗口变窄并自动换行、多风格翻译默认开启",
        ],
    },
    {
        "version": "1.5.0",
        "date": "2026-06-26",
        "title": "选区联动 · 新增 Google 官方引擎 · 朗读与界面多项打磨",
        "notes": [
            "新增选区联动：选一侧文字，临时翻译后在另一侧灰色高亮最匹配区间，可直接朗读",
            "新增『Google -API-Key联网』官方云翻译 Basic v2 引擎（免费版保留不变）",
            "帮助文档补充各引擎的模型、收费、稳定性说明，便于甄别",
            "卡拉OK字幕加大提前量，修复再次出现的滞后",
            "原文区选区朗读高亮与译文区一致；读完保留普通蓝色选区（可正常取消/重选）",
            "朗读时按钮变青绿背景，暂停仍保持，停止/读完恢复",
            "只有当前朗读语种的嗓音改动才打断朗读（改另一语种嗓音不打断）",
            "中文嗓音移到左、英文嗓音移到右；窗口最窄时不再与设置按钮重叠",
            "更改翻译引擎后自动触发翻译",
            "Kokoro 离线朗读报错时显示真实原因，便于排查",
        ],
    },
    {
        "version": "1.4.0",
        "date": "2026-06-26",
        "title": "新增 8 个 LLM 翻译引擎 · 多风格翻译",
        "notes": [
            "新增 OpenAI GPT、Google Gemini、Claude、智谱GLM-4-Flash、文心一言、字节豆包、通义千问、Kimi 八个大模型引擎（均需 API Key）",
            "所有 LLM 引擎统一走 OpenAI 兼容接口，设置中分别填 Key",
            "新增『多风格翻译』开关：选用 LLM 引擎时，主译文不变，下方附书面/口语/俚语/美式英式等多种辅助译法",
            "设置页 Key 较多，改为可滚动",
        ],
    },
    {
        "version": "1.3.0",
        "date": "2026-06-26",
        "title": "新增 Kokoro 本地离线朗读 · 引擎/嗓音标注联网离线 · 多项修复",
        "notes": [
            "新增 Kokoro 本地离线朗读引擎：无需联网、CPU 即可、原生对齐时间戳，卡拉OK更精准",
            "嗓音标注来源：edge-tts 标『-线上联网』，Kokoro 标『-离线本地』",
            "引擎名标注联网方式：Google/DeepL/DeepSeek/HunYuan 联网，Argos 本地离线",
            "修复原文区选区朗读无青蓝覆盖；修复朗读结束后蓝色选区无法取消",
            "朗读失败不再反复弹窗打扰，并提示可改用离线嗓音",
            "字幕加入提前量补偿，跟声音更齐；选区朗读字幕只在选区内推进",
            "保存音频记住上次目录；离线为 wav、在线为 mp3，文件名 EC_语种_嗓音_日期_时间",
            "关于页：联系方式一行、版权用标准英文写法",
        ],
    },
    {
        "version": "1.2.2",
        "date": "2026-06-25",
        "title": "字幕提前补偿 · 选区字幕只走选区 · 关于页排版",
        "notes": [
            "卡拉OK字幕加入提前量补偿，跟声音对得更齐（中英文都不再慢半拍）",
            "修复选区朗读时字幕仍从全文头走到尾的问题，现在只在选区内推进",
            "关于页：网址与邮箱一行、两个电话另起一行，版权恢复 © 符号",
            "关于页主标题下方空行高度与其它文档一致",
        ],
    },
    {
        "version": "1.2.1",
        "date": "2026-06-25",
        "title": "卡拉OK更精准 · 选区朗读恢复 · 音频命名优化",
        "notes": [
            "卡拉OK高亮改用播放器真实位置同步，更精准（暂停时位置准确）",
            "恢复『选中部分朗读』：选区显示蓝底，读到处覆盖青蓝绿，读完恢复蓝色",
            "朗读高亮色改为偏青蓝、降饱和，更柔和",
            "保存音频记住上次保存目录；文件名改为 EC_语种_嗓音_日期_时间（中文嗓音用拼音）",
            "标题字号略增大（仍克制）；原文/译文区字号再放大",
            "关于页联系方式与版权信息更新",
        ],
    },
    {
        "version": "1.2.0",
        "date": "2026-06-25",
        "title": "卡拉OK高亮独立时钟驱动 · 符号翻译 · 多项界面优化",
        "notes": [
            "卡拉OK高亮改为纯独立时钟驱动，彻底脱离播放器状态，两平台稳定逐词高亮",
            "无词边界时按字符比例估算，保证仍有高亮兜底",
            "新增标点/符号翻译：如 . → dot、（ → 左括号，引擎无能为力时由内置词典兜底",
            "单个英文单词、过短文本也会尽力翻译出含义",
            "Windows 下拉弹窗去掉多余滚动条",
            "原文/译文区字号放大一号，更醒目",
            "文档主标题下方增加空行，排版更匀称",
        ],
    },
    {
        "version": "1.1.9",
        "date": "2026-06-25",
        "title": "卡拉OK高亮改用底层着色（修复 macOS 不显示）· 下拉排版匀称",
        "notes": [
            "卡拉OK高亮改用 QSyntaxHighlighter 底层着色，修复 macOS/Big Sur 完全不显示高亮的问题",
            "朗读时逐词背景变青绿，随进度递增，读完恢复",
            "下拉列表去掉底部多余空白，外边框单层均匀，行距匀称",
        ],
    },
    {
        "version": "1.1.8",
        "date": "2026-06-25",
        "title": "下拉项加大行距 · 文档标题确实缩小 · 按钮等宽",
        "notes": [
            "下拉列表选项行距加大，文字不再重叠；弹窗去掉底部缝隙",
            "文档标题改用更可靠的方式渲染，确实缩小到接近正文",
            "设置中 Save 与 Cancel 按钮等宽",
        ],
    },
    {
        "version": "1.1.7",
        "date": "2026-06-25",
        "title": "卡拉OK高亮改用墙上时钟 · 文档标题再缩小 · 弹窗去白边",
        "notes": [
            "卡拉OK逐词高亮改用独立时钟驱动，不再依赖播放器位置，macOS 也能逐词推进",
            "文档（关于/更新/帮助）标题字号改用更可靠的方式设置，确实缩小到接近正文",
            "下拉弹出列表去掉上下白边、深色背景",
            "暂停/继续时高亮位置正确衔接",
        ],
    },
    {
        "version": "1.1.6",
        "date": "2026-06-25",
        "title": "修复下载报错 · 下拉弹窗加宽 · 缩窄不重叠",
        "notes": [
            "修复下载音频第二次报『只读文件系统』错误：默认保存到「下载」文件夹",
            "下载文件名自动命名：EnglishCoach_日期_编号.mp3（编号自增）",
            "下载按钮换成更直观的下载图标",
            "下拉弹出列表加宽，完整显示选项、两侧留空隙、去掉上下白边",
            "修复窗口缩到最小时顶部控件与设置图标重叠",
        ],
    },
    {
        "version": "1.1.5",
        "date": "2026-06-25",
        "title": "修复崩溃 · 内存播放提速 · 卡拉OK与下载音频",
        "notes": [
            "修复反复朗读/拖动/退出时的崩溃（朗读线程安全退役与回收）",
            "改为内存直接播放，不再生成临时 mp3，启动播放更快",
            "修复卡拉OK逐词高亮（时间轴换算修正 + 高频刷新）",
            "朗读中改参数时进度条停在当前位置，不再归零",
            "新增「下载音频」按钮：点击才生成 mp3 文件保存",
            "按钮文案精简：朗读原文 / 朗读译文 / 停止朗读，播放时显示 暂停/继续朗读",
            "下拉框去掉选中对号、加蓝色高亮（含 macOS），并尽量收窄",
        ],
    },
    {
        "version": "1.1.4",
        "date": "2026-06-24",
        "title": "修复卡拉OK高亮 · 窗口可缩窄 · 进度条不归零",
        "notes": [
            "修复卡拉OK逐词高亮无效：改用高频定时器驱动，高亮随声音顺滑推进",
            "朗读中更改设置时，进度条停在当前位置，不再跳回开头",
            "修复窗口过宽且无法缩窄：朗读控件分两行排布，窗口可自由调窄",
            "下拉框完整显示且不过度拉伸；悬停项目显示蓝色高亮",
            "文档标题字号确认缩小到接近正文",
        ],
    },
    {
        "version": "1.1.3",
        "date": "2026-06-24",
        "title": "卡拉OK式朗读高亮 · 进度条 · 选区朗读",
        "notes": [
            "朗读时按真实词级时间戳逐词高亮已读内容（青绿色），类似 MV 字幕",
            "选中部分文字后点朗读，只朗读选中的部分",
            "新增播放进度条，可拖动实时调整播放位置",
            "朗读按钮改为「开始/暂停/继续朗读」三态切换",
            "朗读中更改嗓音或语速，自动以新设置重读并跳回大致进度",
            "所有下拉框再加宽，鼠标悬停项目显示蓝色高亮",
            "更新/使用/关于文档标题字号再缩小一号",
            "macOS 程序图标四周留白，显示更精致协调",
        ],
    },
    {
        "version": "1.1.2",
        "date": "2026-06-24",
        "title": "修复 Argos 偶发翻译失败 · 下拉箭头改尖角号",
        "notes": [
            "修复 Argos 离线翻译时好时坏的问题：翻译前确保模型已就绪并自动重试",
            "下拉框右侧箭头改为扁平尖角号（V 形），无边框",
        ],
    },
    {
        "version": "1.1.1",
        "date": "2026-06-24",
        "title": "中英嗓音分离 · 界面与样式优化",
        "notes": [
            "朗读嗓音拆分为「英文嗓音」「中文嗓音」两个下拉，按文本语种自动取用",
            "英文嗓音不再被迫去读中文，避免乱兜底；两个嗓音选择均会记住",
            "第一排标签改为「目标语言」「翻译引擎」",
            "「使用说明」去掉 Readme 字样",
            "更新说明 / 使用说明 / 关于 的标题字号再缩小一号",
            "下拉框与滑竿的尖角图标改为扁平无边框风格",
            "修复 Windows 状态栏右下角灰色拖拽块",
        ],
    },
    {
        "version": "1.1.0",
        "date": "2026-06-23",
        "title": "下拉框加宽 · 按钮顺序调整 · 模型仓库复用",
        "notes": [
            "源/目标语言、引擎、嗓音下拉框按最长内容精确加宽，文字完整显示",
            "原文 / 译文操作按钮顺序调整为：复制、粘贴、删除",
            "编译脚本支持公共模型仓库（~/EnglishCoach-models）：模型下载一次，所有版本复用",
            "模型下载改用 HTTP/1.1，规避 argos-net 的 HTTP/2 中断问题",
        ],
    },
    {
        "version": "1.0.9",
        "date": "2026-06-23",
        "title": "Argos 离线翻译彻底打通 · 内置中英模型",
        "notes": [
            "Argos 离线翻译现已完全可用：中英互译，无需联网、无需 Key",
            "内置中英离线模型，安装即用，不再需要运行时下载",
            "彻底移除 PyTorch 依赖（通过兼容层让 Argos 在无 torch 环境运行）",
            "兼容 macOS Big Sur 等较老系统的依赖版本组合",
            "断网时也能用 Argos 完成中英翻译",
        ],
    },
    {
        "version": "1.0.8",
        "date": "2026-06-23",
        "title": "界面重排 · 朗读自动重试 · Argos 报错优化",
        "notes": [
            "顶部重排：第一排左侧为 源/目标语言与引擎，右侧为 设置/更新/帮助/关于",
            "原文 / 译文标题与 粘贴/复制/删除 按钮下移至「翻译」大按钮同一排",
            "朗读合成失败时静默重试，最多 3 次，仍失败才提示",
            "Argos 加载失败时显示真实原因，便于定位（区分源码运行 / 打包缺失）",
            "编译脚本新增 argostranslate 导入校验，装不上会提前明确报错",
            "下拉框加宽，自动检测等文字显示完整",
            "关于页邮箱与网址并列显示",
        ],
    },
    {
        "version": "1.0.7",
        "date": "2026-06-23",
        "title": "修复中文朗读与离线翻译 · 多项界面优化",
        "notes": [
            "修复中文朗读全部失败：读中文时自动切换到中文嗓音；新增 3 个中文嗓音",
            "修复 Argos 英译中报错：改用正确的翻译路径并处理英语中转",
            "Argos 中英模型随程序预置打包，安装后即可离线翻译（无需再下载）",
            "移除有道朗读引擎与「失败换嗓音」提示（已不再需要）",
            "朗读时更改嗓音或语速即时生效（自动以新设置重读当前栏）",
            "原文 / 译文区新增「粘贴」按钮",
            "源语言 / 目标语言 / 引擎下拉框自适应宽度，文字显示完整",
            "帮助与更新说明的标题字号缩小，更协调",
            "关于页开发者信息追加邮箱 vfx@Strilen.com",
        ],
    },
    {
        "version": "1.0.6",
        "date": "2026-06-23",
        "title": "翻译新增 Argos 离线 与 混元 引擎 · 双平台打包",
        "notes": [
            "翻译新增「Argos (离线)」引擎：纯本地、无需 Key、无需联网（首次用会提示下载语言模型）",
            "翻译新增「混元 HY-MT」引擎：腾讯混元在线翻译（需腾讯云 Key）",
            "翻译引擎增至 5 个：Google（默认）、DeepL、DeepSeek、Argos、混元",
            "同时提供 macOS 与 Windows 两套编译脚本",
        ],
    },
    {
        "version": "1.0.5",
        "date": "2026-06-23",
        "title": "朗读新增有道引擎 · 嗓音失败可改选",
        "notes": [
            "朗读新增「有道」嗓音（国内免费、无需 Key），作为微软 edge-tts 的备选",
            "微软 edge-tts 仍为默认，音质更佳、嗓音更多",
            "某嗓音合成失败时，弹出列表让你改选其它嗓音并立即重试",
            "朗读改用流式/二进制写入，更稳定",
        ],
    },
    {
        "version": "1.0.4",
        "date": "2026-06-23",
        "title": "兼容旧版 macOS · 界面与交互优化",
        "notes": [
            "兼容 macOS Big Sur：使用 PyQt6 6.4.x，解决 IOKit 符号缺失导致无法启动",
            "新增输入即译：停止输入约 0.8 秒后自动翻译（手动「翻译」按钮仍保留）",
            "左右两栏拉开间距，不再重叠；复制与删除按钮间距收紧",
            "引擎下拉中「Google」不再显示「(免费)」后缀",
            "朗读改用流式合成，更稳定；嗓音失效时给出明确提示",
            "移除「开发者介绍」页，作者信息并入「关于」（开发者：Strilen Liu）",
        ],
    },
    {
        "version": "1.0.3",
        "date": "2026-06-22",
        "title": "修复界面不弹出 · 兼容 macOS Big Sur · 全新图标",
        "notes": [
            "修复打包后无报错但窗口不显示的问题（强制窗口前置并抢占焦点）",
            "音频后端初始化失败不再阻止主界面启动（朗读不可用时自动降级）",
            "兼容 macOS 11 Big Sur：打包设置最低系统版本为 11.0",
            "启动异常时弹窗显示具体错误，便于排查",
            "全新应用图标：构图居中、字形圆润、双色配色",
        ],
    },
    {
        "version": "1.0.2",
        "date": "2026-06-22",
        "title": "改用 PyInstaller 打包并加入应用图标",
        "notes": [
            "macOS 打包改用 PyInstaller，更可靠地处理 PyQt6 的 Qt 插件，解决持续的启动崩溃",
            "新增应用图标（A/文 + 翻开的书），编译后 .app / Dock 显示专属图标",
            "窗口与任务栏同步使用新图标",
        ],
    },
    {
        "version": "1.0.1",
        "date": "2026-06-22",
        "title": "修复 macOS 打包启动崩溃",
        "notes": [
            "修复 py2app 打包后出现「Launch error」无法启动的问题",
            "打包时完整收录 PyQt6 插件（cocoa 平台、SVG、多媒体），解决 Qt 无法初始化",
            "编译脚本加入 conda 环境自动激活",
        ],
    },
    {
        "version": "1.0.0",
        "date": "2026-06-22",
        "title": "首个正式版本",
        "notes": [
            "新增「翻译」功能：默认 Google 免费引擎（无需 Key），DeepL / DeepSeek 可作备选",
            "翻译支持中英双向与自动检测，可一键互换",
            "新增「朗读」功能：基于 edge-tts 在线语音合成，多嗓音、可调语速",
            "新增「版本更新说明与管理」面板",
            "新增「关于」「Readme / 帮助」「开发者介绍」页面",
            "内置 SVG 图标系统",
        ],
    },
]

# =============================================================================
#  图标系统  (内置 SVG, 不依赖外部图片资源)
# =============================================================================

class Icons:
    """集中管理的内置 SVG 图标。颜色用 currentColor 占位，渲染时替换。"""

    _DEFS = {
        "app": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  <path d="M9 7h6M9 11h6"/></svg>""",
        "translate": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/>
                  <path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/></svg>""",
        "speak": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>""",
        "swap": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="m16 3 4 4-4 4"/><path d="M20 7H4"/>
                  <path d="m8 21-4-4 4-4"/><path d="M4 17h16"/></svg>""",
        "settings": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>""",
        "info": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>""",
        "history": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/>
                  <path d="M12 7v5l4 2"/></svg>""",
        "help": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>""",
        "dev": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>""",
        "stop": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <rect x="6" y="6" width="12" height="12" rx="2"/></svg>""",
        "copy": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>""",
        "paste": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
                  <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>""",
        "clear": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
                  <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>""",
        "pause": """<svg viewBox="0 0 24 24" fill="{c}" stroke="none">
                  <rect x="6" y="5" width="4" height="14" rx="1"/>
                  <rect x="14" y="5" width="4" height="14" rx="1"/></svg>""",
        "export": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>""",
        "file": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/></svg>""",
        "file_down": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/><line x1="12" y1="12" x2="12" y2="18"/>
                  <polyline points="9 15 12 18 15 15"/></svg>""",
        "list": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
                  <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
                  <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>""",
        "undo": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/></svg>""",
        "download": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>""",
    }

    @classmethod
    def icon(cls, name: str, color: str = "#e8e8e8") -> QIcon:
        svg = cls._DEFS.get(name, "").format(c=color).encode("utf-8")
        pm = QPixmap()
        pm.loadFromData(svg, "SVG")
        return QIcon(pm)

    @classmethod
    def pixmap(cls, name: str, color: str = "#e8e8e8", size: int = 48) -> QPixmap:
        svg = cls._DEFS.get(name, "").format(c=color).encode("utf-8")
        pm = QPixmap()
        pm.loadFromData(svg, "SVG")
        return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)


# =============================================================================
#  翻译引擎  (DeepSeek API, 后台线程)
# =============================================================================

LANG_OPTIONS = ["自动检测", "中文", "English"]

# 翻译引擎标识
ENGINE_GOOGLE = "Google -线上联网"
ENGINE_GOOGLE_API = "Google -API-Key联网"
ENGINE_DEEPL = "DeepL -API-Key联网"
ENGINE_DEEPSEEK = "DeepSeek -API-Key联网"
ENGINE_ARGOS = "Argos -离线本地"
ENGINE_HUNYUAN = "混元 -API-Key联网"
# LLM 多风格翻译引擎（均为 OpenAI 兼容 chat 接口）
ENGINE_OPENAI = "GPT -API-Key联网"
ENGINE_GEMINI = "Gemini -API-Key联网"
ENGINE_CLAUDE = "Claude -API-Key联网"
ENGINE_GLM = "GLM -API-Key联网"
ENGINE_ERNIE = "文心一言 -API-Key联网"
ENGINE_DOUBAO = "豆包 -API-Key联网"
ENGINE_QWEN = "通义千问 -API-Key联网"
ENGINE_KIMI = "Kimi -API-Key联网"

# 各引擎端点
GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
GOOGLE_API_ENDPOINT = "https://translation.googleapis.com/language/translate/v2"  # 官方 Basic v2
DEEPL_ENDPOINT_FREE = "https://api-free.deepl.com/v2/translate"   # 免费版 Key
DEEPL_ENDPOINT_PRO = "https://api.deepl.com/v2/translate"          # 付费版 Key
DEEPSEEK_ENDPOINT = "https://api.deepseek.com/chat/completions"
# 腾讯混元 OpenAI 兼容端点（需腾讯云 Key）
HUNYUAN_ENDPOINT = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"

# LLM 引擎统一配置：均为 OpenAI 兼容 /chat/completions 接口
# key: 引擎常量；值: {endpoint, model, key_name(设置中保存的键), auth(bearer/x-api-key)}
LLM_ENGINES = {
    ENGINE_DEEPSEEK: {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat", "key_name": "deepseek", "auth": "bearer",
        "label": "DeepSeek",
    },
    ENGINE_OPENAI: {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini", "key_name": "openai", "auth": "bearer",
        "label": "OpenAI GPT",
    },
    ENGINE_GEMINI: {
        # Gemini 的 OpenAI 兼容端点
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": "gemini-2.5-flash", "key_name": "gemini", "auth": "bearer",
        "label": "Google Gemini",
    },
    ENGINE_CLAUDE: {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "model": "claude-sonnet-4-6", "key_name": "claude", "auth": "anthropic",
        "label": "Claude",
    },
    ENGINE_GLM: {
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-4-flash", "key_name": "glm", "auth": "bearer",
        "label": "智谱GLM-4-Flash",
    },
    ENGINE_ERNIE: {
        # 文心一言 OpenAI 兼容端点（千帆）
        "endpoint": "https://qianfan.baidubce.com/v2/chat/completions",
        "model": "ernie-4.5-turbo-128k", "key_name": "ernie", "auth": "bearer",
        "label": "文心一言",
    },
    ENGINE_DOUBAO: {
        "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "model": "doubao-pro-32k", "key_name": "doubao", "auth": "bearer",
        "label": "字节豆包",
    },
    ENGINE_QWEN: {
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus", "key_name": "qwen", "auth": "bearer",
        "label": "通义千问",
    },
    ENGINE_KIMI: {
        "endpoint": "https://api.moonshot.cn/v1/chat/completions",
        "model": "moonshot-v1-8k", "key_name": "kimi", "auth": "bearer",
        "label": "Kimi",
    },
    ENGINE_HUNYUAN: {
        "endpoint": HUNYUAN_ENDPOINT,
        "model": "hunyuan-turbo", "key_name": "hunyuan", "auth": "bearer",
        "label": "HunYuan",
    },
}

# 所有引擎的显示顺序
ALL_ENGINES = [
    ENGINE_GOOGLE, ENGINE_GOOGLE_API, ENGINE_DEEPL, ENGINE_ARGOS,
    ENGINE_DEEPSEEK, ENGINE_OPENAI, ENGINE_GEMINI, ENGINE_CLAUDE,
    ENGINE_GLM, ENGINE_ERNIE, ENGINE_DOUBAO, ENGINE_QWEN, ENGINE_KIMI,
    ENGINE_HUNYUAN,
]
# 哪些是 LLM（支持多风格翻译）
LLM_ENGINE_SET = {
    ENGINE_DEEPSEEK, ENGINE_OPENAI, ENGINE_GEMINI, ENGINE_CLAUDE,
    ENGINE_GLM, ENGINE_ERNIE, ENGINE_DOUBAO, ENGINE_QWEN, ENGINE_KIMI,
    ENGINE_HUNYUAN,
}

# 语言名 -> 各引擎语言代码
_LANG_GOOGLE = {"中文": "zh-CN", "English": "en", "自动检测": "auto"}
_LANG_DEEPL = {"中文": "ZH", "English": "EN", "自动检测": None}
_LANG_ARGOS = {"中文": "zh", "English": "en"}   # Argos 用 ISO 639-1


class TranslateWorker(QThread):
    """多引擎翻译。默认 Google（免费、无需 Key）；DeepL / DeepSeek 需 Key。"""
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    # 常见标点/符号的中英文名称（翻译引擎对单个符号常无能为力，这里内置兜底）
    _SYMBOL_NAMES = {
        ".": ("dot", "点 / 句号"), ",": ("comma", "逗号"),
        "。": ("period (Chinese full stop)", "句号"), "，": ("comma", "逗号"),
        "?": ("question mark", "问号"), "？": ("question mark", "问号"),
        "!": ("exclamation mark", "感叹号"), "！": ("exclamation mark", "感叹号"),
        ";": ("semicolon", "分号"), "；": ("semicolon", "分号"),
        ":": ("colon", "冒号"), "：": ("colon", "冒号"),
        "(": ("left parenthesis", "左括号"), ")": ("right parenthesis", "右括号"),
        "（": ("left parenthesis", "左括号"), "）": ("right parenthesis", "右括号"),
        "[": ("left bracket", "左方括号"), "]": ("right bracket", "右方括号"),
        "{": ("left brace", "左花括号"), "}": ("right brace", "右花括号"),
        "<": ("less-than sign", "小于号"), ">": ("greater-than sign", "大于号"),
        "@": ("at sign", "艾特 / @符号"), "#": ("hash / pound sign", "井号"),
        "$": ("dollar sign", "美元符号"), "%": ("percent sign", "百分号"),
        "&": ("ampersand", "和号"), "*": ("asterisk", "星号"),
        "+": ("plus sign", "加号"), "-": ("hyphen / minus", "连字符 / 减号"),
        "=": ("equals sign", "等号"), "/": ("slash", "斜杠"),
        "\\": ("backslash", "反斜杠"), "|": ("vertical bar", "竖线"),
        "_": ("underscore", "下划线"), "~": ("tilde", "波浪号"),
        "^": ("caret", "脱字符"), "`": ("backtick", "反引号"),
        "'": ("apostrophe", "撇号"), '"': ("quotation mark", "引号"),
        "“": ("left quotation mark", "左引号"), "”": ("right quotation mark", "右引号"),
        "…": ("ellipsis", "省略号"), "—": ("em dash", "破折号"),
        "、": ("Chinese enumeration comma", "顿号"),
    }

    def __init__(self, text, src, tgt, engine, keys: dict, multi_style=False, parent=None):
        super().__init__(parent)
        self.text, self.src, self.tgt = text, src, tgt
        self.engine = engine
        self.keys = keys  # {"deepl": "...", "deepseek": "...", ...}
        self.multi_style = multi_style   # LLM 引擎下是否输出多风格翻译
        self._cancelled = False

    # ---- 目标语言解析：「自动检测」目标 = 中→英 / 其它→中 ----
    def _resolve_target(self):
        if self.tgt != "自动检测":
            return self.tgt
        # 含中文字符则译为英文，否则译为中文
        for ch in self.text:
            if "\u4e00" <= ch <= "\u9fff":
                return "English"
        return "中文"

    def _has_letters_or_cjk(self):
        """文本是否包含字母或中文（即可判断语言的内容）。"""
        for ch in self.text:
            if ch.isalpha() or "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    def _try_symbol_fallback(self):
        """纯符号/标点输入时，返回内置的中/英文名称；无法判断语言时按设置或默认英文。
        返回译文字符串；若不适用则返回 None。"""
        stripped = self.text.strip()
        if not stripped or self._has_letters_or_cjk():
            return None   # 含字母/中文，交给翻译引擎
        # 目标语言：显式设置优先；自动检测时，纯符号默认英文
        if self.tgt == "English":
            want_en = True
        elif self.tgt == "中文":
            want_en = False
        else:  # 自动检测：纯符号无法判断 -> 默认英文
            want_en = True
        # 单个已知符号：直接给名称
        if len(stripped) == 1 and stripped in self._SYMBOL_NAMES:
            en, zh = self._SYMBOL_NAMES[stripped]
            return en if want_en else zh
        # 多个符号：逐个翻译拼接
        names = []
        for ch in stripped:
            if ch in self._SYMBOL_NAMES:
                en, zh = self._SYMBOL_NAMES[ch]
                names.append(en if want_en else zh)
            elif ch.strip():
                names.append(ch)   # 未知符号原样保留
        if names:
            return (", ".join(names) if want_en else "、".join(names))
        return None

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            # 纯符号/标点：先用内置词典兜底（引擎对单符号常无能为力）
            sym = self._try_symbol_fallback()
            if sym is not None:
                if not getattr(self, "_cancelled", False):
                    self.finished_ok.emit(sym)
                return
            if self.engine == ENGINE_GOOGLE:
                out = self._run_google()
            elif self.engine == ENGINE_GOOGLE_API:
                out = self._run_google_api()
            elif self.engine == ENGINE_DEEPL:
                out = self._run_deepl()
            elif self.engine == ENGINE_ARGOS:
                out = self._run_argos()
            elif self.engine in LLM_ENGINES:
                # 所有 LLM 引擎走统一 OpenAI 兼容处理（含多风格翻译）
                out = self._run_llm(LLM_ENGINES[self.engine])
            else:
                self.failed.emit(f"未知翻译引擎: {self.engine}")
                return
            # 已被取消（用户重新点了翻译）则丢弃本次结果，不回填
            if getattr(self, "_cancelled", False):
                return
            self.finished_ok.emit(out.strip())
        except requests.exceptions.RequestException as e:
            self.failed.emit(f"网络错误: {e}\n（大陆环境请确认代理 / Clash Verge 是否开启）")
        except RuntimeError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"翻译失败: {e}\n{traceback.format_exc()}")

    # ---- Google 免费端点（非官方，无需 Key）----
    def _run_google(self):
        sl = _LANG_GOOGLE.get(self.src, "auto")
        # 自动检测且含中日韩字符时显式声明源为中文：否则 Google 按多数字符判成
        # 英文，en->en 原样返回，夹杂的中文不被翻译
        if sl == "auto" and _text_is_chinese(self.text):
            sl = "zh-CN"
        tl = _LANG_GOOGLE.get(self._resolve_target(), "en")
        params = {
            "client": "gtx", "sl": sl, "tl": tl,
            "dt": "t", "q": self.text,
        }
        resp = requests.get(GOOGLE_ENDPOINT, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Google 返回 {resp.status_code}。该免费端点可能不稳定，"
                               f"可改用设置中的 DeepL / DeepSeek 备选引擎。")
        data = resp.json()
        # 结构: [[["译文","原文",...], ...], ...]
        return "".join(seg[0] for seg in data[0] if seg[0])

    # ---- Google 官方 Cloud Translation Basic v2（需 API Key）----
    def _run_google_api(self):
        key = self.keys.get("google_api", "").strip()
        if not key:
            raise RuntimeError(
                "尚未配置 Google 云翻译 API Key。请到「设置」中填写。\n"
                "（Google Cloud Translation Basic v2，需在 Google Cloud 启用计费）")
        tl = _LANG_GOOGLE.get(self._resolve_target(), "en")
        params = {"key": key, "q": self.text, "target": tl, "format": "text"}
        if self.src != "自动检测":
            params["source"] = _LANG_GOOGLE.get(self.src, "")
        resp = requests.post(GOOGLE_API_ENDPOINT, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Google 云翻译返回 {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return data["data"]["translations"][0]["translatedText"]

    # ---- DeepL（需 Key，自动识别免费/付费）----
    def _run_deepl(self):
        key = self.keys.get("deepl", "").strip()
        if not key:
            raise RuntimeError("尚未配置 DeepL API Key。请到「设置」中填写。")
        endpoint = DEEPL_ENDPOINT_FREE if key.endswith(":fx") else DEEPL_ENDPOINT_PRO
        payload = {"text": [self.text], "target_lang": _LANG_DEEPL[self._resolve_target()]}
        if self.src != "自动检测":
            payload["source_lang"] = _LANG_DEEPL[self.src]
        resp = requests.post(
            endpoint,
            headers={"Authorization": f"DeepL-Auth-Key {key}",
                     "Content-Type": "application/json"},
            json=payload, timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"DeepL 返回 {resp.status_code}: {resp.text[:200]}")
        return resp.json()["translations"][0]["text"]

    # ---- 统一 LLM 翻译（OpenAI 兼容；支持多风格）----
    def _run_llm(self, cfg):
        key = self.keys.get(cfg["key_name"], "").strip()
        if not key:
            raise RuntimeError(
                f"尚未配置 {cfg['label']} API Key。请到「设置」中填写。")
        tgt = self._resolve_target()
        tgt_name = "英文" if tgt == "English" else "简体中文"

        if self.multi_style:
            _t = self.text.strip()
            _no_sep = not re.search(r"[\s，。！？、；：,.!?;:\n]", _t)
            _has_cjk = any("\u4e00" <= c <= "\u9fff" for c in _t)
            # 中文词≤4字，纯英文单词≤24字母（如 screenshot）
            _is_word = _no_sep and ((_has_cjk and len(_t) <= 4)
                                    or (not _has_cjk and len(_t) <= 24))
            if _is_word:
                # 单字/单词：给多种准确译法，每行一个，无解释无音标
                system = (
                    "你是一名精通中英互译的词典专家。用户给出一个字或词，"
                    "请给出它在" + tgt_name + "中的多种准确译法。\n"
                    "输出规则：每行一个译法，只写译文本身；不要编号、解释、"
                    "音标、风格标注或任何多余文字；按常用程度从高到低排序，"
                    "给出 3-8 个。")
                user = _t
                return (self._call_anthropic(cfg, key, system, user, 1.0)
                        if cfg["auth"] == "anthropic"
                        else self._call_openai_compat(cfg, key, system, user, 1.0))
            system = (
                "你是一名精通中英互译的语言老师。请把用户给的文本翻译成" + tgt_name +
                "，并提供多种风格的译法，帮助语言学习者理解不同语境下的表达。\n"
                "输出严格遵循以下格式（不要任何额外说明）：\n"
                "第一行：最推荐、最自然通用的译文（不加任何前缀标注）\n"
                "随后每行一个其它风格译法，格式为『【风格】译文』，风格如："
                "正式书面、口语随意、美式、英式、俚语、网络用语、生僻文雅等，"
                "只给适用于该文本的 2-5 种，不要硬凑。")
            user = f"请翻译为{tgt_name}：\n{self.text}"
            temperature = 1.0
        else:
            system = ("你是一名专业的中英翻译。只输出译文本身，不要添加任何解释、"
                      "标注、引号或前后缀。保持原文的语气与格式。")
            user = (f"把以下文本翻译成{'地道、自然的英文' if tgt=='English' else '自然流畅的简体中文'}。"
                    f"\n\n文本:\n{self.text}")
            temperature = 1.0

        # Claude 用 messages 接口，其余用 OpenAI chat 接口
        if cfg["auth"] == "anthropic":
            return self._call_anthropic(cfg, key, system, user, temperature)
        return self._call_openai_compat(cfg, key, system, user, temperature)

    def _call_openai_compat(self, cfg, key, system, user, temperature):
        resp = requests.post(
            cfg["endpoint"],
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": cfg["model"],
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}],
                  "temperature": temperature, "stream": False},
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"{cfg['label']} 返回 {resp.status_code}: {resp.text[:200]}")
        return resp.json()["choices"][0]["message"]["content"]

    def _call_anthropic(self, cfg, key, system, user, temperature):
        resp = requests.post(
            cfg["endpoint"],
            headers={"x-api-key": key,
                     "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": cfg["model"], "max_tokens": 1024,
                  "system": system,
                  "messages": [{"role": "user", "content": user}],
                  "temperature": temperature},
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"{cfg['label']} 返回 {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        # Anthropic 返回 content 是块列表
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        return "".join(parts)

    # ---- Argos Translate（纯离线，无需 Key / 联网）----
    def _run_argos(self):
        try:
            _ensure_argos_models(("en", "zh"))   # 锁定目录 + 确保模型已装
            import argostranslate.translate as at
            import argostranslate.package as ap
        except ImportError as e:
            raise RuntimeError(
                "Argos 离线翻译库加载失败。\n\n"
                f"真实原因：{e}\n\n"
                "若为源码运行：请在 EnglishCoach 环境执行 pip install argostranslate；\n"
                "若为打包版：说明编译时未成功安装该库或其依赖（ctranslate2 / sentencepiece），"
                "请重新编译并确认依赖安装无误。")
        tgt = self._resolve_target()
        if self.src == "自动检测":
            has_zh = any("\u4e00" <= c <= "\u9fff" for c in self.text)
            src_code = "zh" if has_zh else "en"
        else:
            src_code = _LANG_ARGOS[self.src]
        tgt_code = _LANG_ARGOS[tgt]
        if src_code == tgt_code:
            return self.text

        installed = at.get_installed_languages()
        by_code = {l.code: l for l in installed}
        if src_code not in by_code or tgt_code not in by_code:
            raise RuntimeError(
                "Argos 离线模型未就绪。\n\n"
                "请确认程序已内置中英模型，或在设置中重新安装离线模型。")

        # get_translation 偶发返回 None（语言对象匹配不稳定）。
        # 重试若干次，每次重新拉取已安装语言，提升稳定性。
        translation = None
        last_err = None
        for _ in range(3):
            try:
                langs = at.get_installed_languages()
                bc = {l.code: l for l in langs}
                if src_code in bc and tgt_code in bc:
                    translation = bc[src_code].get_translation(bc[tgt_code])
                    if translation is not None:
                        break
            except Exception as e:
                last_err = e
            import time
            time.sleep(0.2)

        if translation is None:
            raise RuntimeError(
                f"Argos 暂时无法建立 {src_code}→{tgt_code} 的翻译。\n"
                "请重试一次；若持续失败，请在设置中重新安装离线模型。")
        # Argos 对长文本（尤其多句）易出现"重复退化"（同一个字反复输出，
        # 如满屏"出出出"）。改为按句逐句翻译再拼接，显著缓解该问题，
        # 也让句子更短、更稳定。
        text = self.text
        # 按中英文句末标点切句（保留标点与换行）
        parts = re.split(r'(?<=[。！？；…\.\!\?;\n])', text)
        out = []
        for seg in parts:
            if not seg.strip():
                out.append(seg)        # 保留空白/换行
                continue
            try:
                tr = translation.translate(seg)
            except Exception:
                tr = seg
            # 兜底：若结果出现明显单字重复退化，回退原文该句
            tr = _strip_degenerate_repeat(tr)
            out.append(tr)
        return "".join(out)


def _strip_degenerate_repeat(s, threshold=8):
    """检测并修正 Argos 的重复退化：同一字符连续重复超过 threshold 次，
    压缩为单个，避免满屏重复字。"""
    import re
    if not s:
        return s
    # 把任意单字符连续重复 threshold 次以上压成 1 个
    return re.sub(r'(.)\1{' + str(threshold) + r',}', r'\1', s)


# =============================================================================
#  朗读引擎  (edge-tts -> mp3, 后台线程)
# =============================================================================

# 英文嗓音
# 嗓音定义：每个嗓音标注引擎（edge=线上联网, kokoro=本地离线）与 id。
# 显示名后缀：edge -> " -线上联网"；kokoro -> " -离线本地"
EN_VOICES = {
    "Aria (美音·女) -线上联网":        {"id": "en-US-AriaNeural",        "engine": "edge"},
    "Jenny (美音·女) -线上联网":       {"id": "en-US-JennyNeural",       "engine": "edge"},
    "Guy (美音·男) -线上联网":         {"id": "en-US-GuyNeural",         "engine": "edge"},
    "Christopher (美音·男) -线上联网": {"id": "en-US-ChristopherNeural", "engine": "edge"},
    "Sonia (英音·女) -线上联网":       {"id": "en-GB-SoniaNeural",       "engine": "edge"},
    "Ryan (英音·男) -线上联网":        {"id": "en-GB-RyanNeural",        "engine": "edge"},
    "Natasha (澳音·女) -线上联网":     {"id": "en-AU-NatashaNeural",     "engine": "edge"},
    # Kokoro 本地离线英文嗓音（a=美式, b=英式）。Heart 盲测最像真人，置顶为默认
    "Heart (美音·女) -离线本地":       {"id": "af_heart",   "engine": "kokoro", "lang": "a"},
    "Bella (美音·女) -离线本地":       {"id": "af_bella",   "engine": "kokoro", "lang": "a"},
    "Nova (美音·女) -离线本地":        {"id": "af_nova",    "engine": "kokoro", "lang": "a"},
    "Sarah (美音·女) -离线本地":       {"id": "af_sarah",   "engine": "kokoro", "lang": "a"},
    "Adam (美音·男) -离线本地":        {"id": "am_adam",    "engine": "kokoro", "lang": "a"},
    "Michael (美音·男) -离线本地":     {"id": "am_michael", "engine": "kokoro", "lang": "a"},
    "Emma (英音·女) -离线本地":        {"id": "bf_emma",    "engine": "kokoro", "lang": "b"},
    "George (英音·男) -离线本地":      {"id": "bm_george",  "engine": "kokoro", "lang": "b"},
}

# 中文嗓音
ZH_VOICES = {
    "晓晓 (普通话·女) -线上联网":      {"id": "zh-CN-XiaoxiaoNeural", "engine": "edge"},
    "云希 (普通话·男) -线上联网":      {"id": "zh-CN-YunxiNeural",    "engine": "edge"},
    "晓伊 (普通话·女) -线上联网":      {"id": "zh-CN-XiaoyiNeural",   "engine": "edge"},
    # Kokoro 本地离线中文嗓音（z=普通话）
    "晓贝 (普通话·女) -离线本地":      {"id": "zf_xiaobei",  "engine": "kokoro", "lang": "z"},
    "云健 (普通话·男) -离线本地":      {"id": "zm_yunjian",  "engine": "kokoro", "lang": "z"},
}

# 嗓音 -> 文件名用的简短名（中文用拼音首字母大写）
VOICE_SHORTNAME = {
    "Aria (美音·女) -线上联网": "Aria", "Jenny (美音·女) -线上联网": "Jenny",
    "Guy (美音·男) -线上联网": "Guy", "Christopher (美音·男) -线上联网": "Christopher",
    "Sonia (英音·女) -线上联网": "Sonia", "Ryan (英音·男) -线上联网": "Ryan",
    "Natasha (澳音·女) -线上联网": "Natasha",
    "Heart (美音·女) -离线本地": "Heart", "Bella (美音·女) -离线本地": "Bella",
    "Nova (美音·女) -离线本地": "Nova",
    "Sarah (美音·女) -离线本地": "Sarah", "Adam (美音·男) -离线本地": "Adam",
    "Michael (美音·男) -离线本地": "Michael", "Emma (英音·女) -离线本地": "Emma",
    "George (英音·男) -离线本地": "George",
    "晓晓 (普通话·女) -线上联网": "XiaoXiao", "云希 (普通话·男) -线上联网": "YunXi",
    "晓伊 (普通话·女) -线上联网": "XiaoYi",
    "晓贝 (普通话·女) -离线本地": "XiaoBei", "云健 (普通话·男) -离线本地": "YunJian",
}


def _text_is_chinese(text):
    """文本是否主要为中文。"""
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def fit_combo_width(combo):
    """按最长项设为固定显示宽度。弹出列表比按钮略宽、完整显示、
    行距适中、无多余空白、边框均匀。"""
    from PyQt6.QtGui import QFontMetrics
    from PyQt6.QtWidgets import QFrame, QListView
    fm = QFontMetrics(combo.font())
    widest = 0
    for i in range(combo.count()):
        widest = max(widest, fm.horizontalAdvance(combo.itemText(i)))
    # 留足右侧下拉箭头 + 最小内边距（尽量紧凑，给交换钮居中腾空间）
    combo.setFixedWidth(widest + 42)
    combo.setFixedHeight(34)   # 统一控件高度，与按钮等高
    lv = QListView()
    lv.setFrameShape(QFrame.Shape.NoFrame)
    lv.setUniformItemSizes(True)
    lv.setSpacing(0)
    lv.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    lv.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    lv.setResizeMode(QListView.ResizeMode.Fixed)
    lv.setAutoScroll(False)
    lv.setVerticalScrollMode(QListView.ScrollMode.ScrollPerItem)
    combo.setView(lv)
    combo.view().setMinimumWidth(widest + 56)
    # 关键：可见项数 = 实际项数，杜绝末尾空行 + 可滚动
    combo.setMaxVisibleItems(max(1, combo.count()))
    # 拦截弹出列表的滚轮事件，避免滚出多余空行
    lv.wheelEvent = lambda e: e.ignore()
    # 弹出容器：深色背景 + 单层均匀边框，避免双层错位与多余空白
    popup = combo.view().parent()
    if popup is not None:
        popup.setContentsMargins(0, 0, 0, 0)
        popup.setStyleSheet(
            "background:#2d2d30; border:1px solid #3a3a3a;")


def _split_for_tts(text, max_len=120):
    """把长文本按标点切成句子片段，每段不超过 max_len 字符，
    避免 Kokoro 单次推理超 token 上限被静默截断。中英文标点都作为切点。"""
    import re
    if not text:
        return []
    # 在中英文句末/分隔标点后切分（保留标点）
    pieces = re.split(r'(?<=[。！？；…\.\!\?;])\s*', text)
    segments = []
    buf = ""
    for p in pieces:
        if not p:
            continue
        # 单段仍超长，再按逗号/顿号等次级标点切
        if len(p) > max_len:
            subs = re.split(r'(?<=[，,、])\s*', p)
            for s in subs:
                if not s:
                    continue
                if len(buf) + len(s) > max_len and buf:
                    segments.append(buf); buf = ""
                # 仍然超长则硬切
                while len(s) > max_len:
                    segments.append(s[:max_len]); s = s[max_len:]
                buf += s
        else:
            if len(buf) + len(p) > max_len and buf:
                segments.append(buf); buf = ""
            buf += p
    if buf.strip():
        segments.append(buf)
    return segments or [text]


class TTSWorker(QThread):
    # 输出: 音频字节, 词边界列表[(char_start,char_end,offset_ms,dur_ms)]
    finished_ok = pyqtSignal(bytes, list)
    failed = pyqtSignal(str)

    def __init__(self, text, voice_spec, rate, char_offset=0, parent=None):
        super().__init__(parent)
        self.text = text
        # voice_spec: {"id":..., "engine":"edge"|"kokoro", "lang":...}
        self.voice_spec = voice_spec
        self.rate = rate
        self.char_offset = char_offset
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            engine = self.voice_spec.get("engine", "edge")
            if engine == "kokoro":
                self._run_kokoro()
            else:
                self._run_edge()
        except Exception as e:
            if not self._cancelled:
                self.failed.emit(f"朗读失败：{e}")

    # ---- edge-tts（线上联网，音质最好）----
    def _run_edge(self):
        import time
        last_err = None
        rate_str = f"{'+' if self.rate >= 0 else ''}{self.rate}%"
        voice_id = self.voice_spec["id"]
        for attempt in range(3):
            if self._cancelled:
                return
            audio_buf = bytearray()
            boundaries = []
            search_pos = 0
            try:
                async def _synth():
                    nonlocal search_pos
                    comm = edge_tts.Communicate(self.text, voice_id, rate=rate_str)
                    got = False
                    async for chunk in comm.stream():
                        if self._cancelled:
                            return got
                        t = chunk.get("type")
                        if t == "audio" and chunk.get("data"):
                            audio_buf.extend(chunk["data"])
                            got = True
                        elif t == "WordBoundary":
                            word = chunk.get("text", "")
                            off_ms = chunk.get("offset", 0) / 10000.0
                            dur_ms = chunk.get("duration", 0) / 10000.0
                            idx = self.text.find(word, search_pos)
                            if idx < 0:
                                idx = self.text.find(word)
                            if idx >= 0:
                                cs = self.char_offset + idx
                                ce = cs + len(word)
                                search_pos = idx + len(word)
                                boundaries.append((cs, ce, off_ms, dur_ms))
                    return got

                got = asyncio.run(_synth())
                if self._cancelled:
                    return
                if got and len(audio_buf) > 0:
                    self.finished_ok.emit(bytes(audio_buf), boundaries)
                    return
                last_err = "未能合成语音（返回空音频）"
            except Exception as e:
                last_err = str(e)
            if self._cancelled:
                return
            time.sleep(0.5)
        if not self._cancelled:
            self.failed.emit(
                f"线上朗读失败（已重试 3 次）：{last_err}\n"
                "（edge-tts 需联网，大陆请确认网络/代理；或改用『-离线本地』嗓音）")

    # ---- Kokoro（本地离线，无需联网，原生对齐时间戳）----
    def _run_kokoro(self):
        try:
            import io, wave
            import numpy as np
            pipeline = _get_kokoro_pipeline(self.voice_spec.get("lang", "a"))
            if pipeline is None:
                reason = _KOKORO_LAST_ERROR or "未知原因"
                hint = ""
                if "Operation not permitted" in reason or "zoneinfo" in reason:
                    hint = ("\n\n这是 macOS 对『外置硬盘』的访问限制：你的 conda 装在外置 SSD（CineeSD）上，"
                            "系统不允许程序读取其中的时区文件。解决办法：\n"
                            "① 打开『系统设置 → 隐私与安全性 → 完全磁盘访问权限』，"
                            "把本程序（或终端 Terminal）加进去并打勾；\n"
                            "② 或把 EnglishCoach 的 conda 环境装到内置硬盘；\n"
                            "③ 已尝试自动改用系统时区库，若仍失败请用上面①。")
                self.failed.emit(
                    "本地离线朗读不可用：Kokoro 引擎未就绪。\n\n"
                    f"真实原因：{reason}{hint}\n\n"
                    "也可改用『-线上联网』嗓音（edge-tts）。")
                return
            voice_id = self.voice_spec["id"]
            speed = 1.0 + (self.rate / 100.0)   # rate -50..50 -> speed 0.5..1.5
            speed = max(0.5, min(2.0, speed))

            audio_chunks = []
            boundaries = []
            sample_rate = 24000
            search_pos = 0
            cum_samples = 0
            # Kokoro 单次推理有 token 上限（约 510），中文长文本若不切分会被静默截断，
            # 导致"声音没读完但进度跑满"。这里先按标点把长文本切成句子片段，逐段合成。
            segments = _split_for_tts(self.text)
            for seg_text in segments:
                if self._cancelled:
                    return
                if not seg_text.strip():
                    continue
                for result in pipeline(seg_text, voice=voice_id, speed=speed):
                    if self._cancelled:
                        return
                    audio = result.output.audio if hasattr(result, "output") and result.output else None
                    if audio is None:
                        continue
                    audio_np = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
                    chunk_start_ms = cum_samples / sample_rate * 1000.0
                    tokens = getattr(result, "tokens", None) or []
                    for tk in tokens:
                        word = getattr(tk, "text", "") or ""
                        st = getattr(tk, "start_ts", None)
                        et = getattr(tk, "end_ts", None)
                        if not word.strip() or st is None:
                            continue
                        idx = self.text.find(word, search_pos)
                        if idx < 0:
                            idx = self.text.find(word)
                        if idx >= 0:
                            cs = self.char_offset + idx
                            ce = cs + len(word)
                            search_pos = idx + len(word)
                            off_ms = chunk_start_ms + st * 1000.0
                            dur_ms = ((et - st) * 1000.0) if et else 200.0
                            boundaries.append((cs, ce, off_ms, dur_ms))
                    audio_chunks.append(audio_np)
                    cum_samples += len(audio_np)

            if self._cancelled:
                return
            if not audio_chunks:
                self.failed.emit("本地朗读未生成音频。")
                return
            # 拼接并编码为 WAV bytes
            full = np.concatenate(audio_chunks)
            full = np.clip(full, -1.0, 1.0)
            pcm16 = (full * 32767).astype("<i2")
            buf = io.BytesIO()
            with wave.open(buf, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sample_rate)
                w.writeframes(pcm16.tobytes())
            self.finished_ok.emit(buf.getvalue(), boundaries)
        except Exception as e:
            if not self._cancelled:
                import traceback
                self.failed.emit(f"本地朗读失败：{e}\n{traceback.format_exc()[:300]}")


# Kokoro pipeline 缓存（按语言）。首次使用时惰性创建。
_KOKORO_PIPELINES = {}
_KOKORO_AVAILABLE = None

_KOKORO_LAST_ERROR = ""

def _kokoro_available():
    global _KOKORO_AVAILABLE, _KOKORO_LAST_ERROR
    if _KOKORO_AVAILABLE is None:
        # 规避外置 SSD 上 conda 的 zoneinfo 权限问题（Operation not permitted）：
        # 让 Python 优先用系统时区库，并固定 TZ，避免 import 链路去读外置卷的时区文件。
        import os as _os
        _os.environ.setdefault("TZ", "Asia/Shanghai")
        # 系统时区目录优先（macOS/Linux 通常在 /usr/share/zoneinfo）
        sys_tz = "/usr/share/zoneinfo"
        if _os.path.isdir(sys_tz):
            _os.environ.setdefault("PYTHONTZPATH", sys_tz)
            try:
                import zoneinfo
                zoneinfo.reset_tzpath([sys_tz])
            except Exception:
                pass
        try:
            import time as _time
            _time.tzset()
        except Exception:
            pass
        try:
            import kokoro  # noqa
            _KOKORO_AVAILABLE = True
        except Exception as e:
            _KOKORO_AVAILABLE = False
            _KOKORO_LAST_ERROR = f"{type(e).__name__}: {e}"
    return _KOKORO_AVAILABLE

def _get_kokoro_pipeline(lang_code="a"):
    """惰性创建并缓存 Kokoro pipeline。失败返回 None，原因记入 _KOKORO_LAST_ERROR。"""
    global _KOKORO_LAST_ERROR
    if not _kokoro_available():
        return None
    if lang_code in _KOKORO_PIPELINES:
        return _KOKORO_PIPELINES[lang_code]
    try:
        # 打包后优先用内置模型目录（离线可用），避免联网下载
        import os as _os
        base = getattr(sys, "_MEIPASS", None)
        if base:
            bundled = _os.path.join(base, "kokoro_model")
            if _os.path.isdir(bundled):
                _os.environ.setdefault("HF_HUB_OFFLINE", "1")
                _os.environ.setdefault("HF_HOME", bundled)
        from kokoro import KPipeline
        # 有 CUDA GPU 则用 GPU 加速，否则 CPU（CUDA 版 torch 无卡时自动回退）
        device = None
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
        except Exception:
            pass
        try:
            p = KPipeline(lang_code=lang_code, device=device)
        except TypeError:
            p = KPipeline(lang_code=lang_code)   # 老版本不支持 device 参数
        _KOKORO_PIPELINES[lang_code] = p
        return p
    except Exception as e:
        import traceback
        _KOKORO_LAST_ERROR = f"{type(e).__name__}: {e}"
        traceback.print_exc()
        return None


# =============================================================================
#  对话框: 设置 / 关于 / 更新说明 / 帮助 / 开发者
# =============================================================================

DOC_CSS = """
<style>
  body { font-family: 'Segoe UI','Microsoft YaHei',sans-serif; color:#dcdcdc;
         line-height:1.7; }
  h1 { color:#4ea1ff; font-size:13px; }
  h2 { color:#7bbcff; font-size:12px; margin-top:12px;
       border-bottom:1px solid #333; padding-bottom:2px; }
  h3 { color:#9ad; font-size:12px; }
  code { background:#2a2a2a; padding:1px 5px; border-radius:3px; color:#ffcb6b; }
  a { color:#4ea1ff; }
  .ver { color:#4ea1ff; font-weight:bold; }
  .date { color:#888; font-size:12px; }
  ul { margin-top:4px; }
</style>
"""

# QTextDocument 的默认样式表（setDefaultStyleSheet 用，标题字号明确压到接近正文）
DOC_STYLESHEET = """
body { color:#dcdcdc; line-height:170%; }
.t1 { color:#4ea1ff; font-size:15px; font-weight:bold; margin-bottom:10px; }
.t2 { color:#7bbcff; font-size:13px; font-weight:bold; }
.t3 { color:#9ad; font-size:13px; font-weight:bold; }
code { background:#2a2a2a; color:#ffcb6b; }
a { color:#4ea1ff; }
.ver { color:#4ea1ff; font-weight:bold; }
.date { color:#888; font-size:11px; }
"""


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumWidth(440)
        self.resize(460, 640)
        # 让设置窗内的下拉与主界面一致：悬停/选中蓝色高亮
        self.setStyleSheet("""
            QComboBox QAbstractItemView { background:#2d2d30; outline:none; border:none;
                selection-background-color:#0e639c; selection-color:white; }
            QComboBox QAbstractItemView::item { padding:7px 14px; border:none; }
            QComboBox QAbstractItemView::item:selected { background:#0e639c; color:white; }
            QComboBox QAbstractItemView::item:hover { background:#0e639c; color:white; }
        """)

        outer = QVBoxLayout(self)
        # 内容较多，放进滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        # 右侧多留白，避免滚动条压住文字
        layout.setContentsMargins(4, 4, 18, 4)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # —— 默认翻译引擎 ——
        eng_label = QLabel("默认翻译引擎")
        eng_label.setStyleSheet("font-weight:bold; color:#7bbcff; margin-top:4px;")
        layout.addWidget(eng_label)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(ALL_ENGINES)
        self.engine_combo.setCurrentText(
            settings.value("engine", ENGINE_GOOGLE))
        layout.addWidget(self.engine_combo)

        eng_tip = QLabel("Google 免费、无需 Key、即开即用（推荐）。"
                         "Argos 纯离线。其余 LLM 引擎需填对应 Key，并可开启多风格翻译。")
        eng_tip.setWordWrap(True)
        eng_tip.setStyleSheet("color:#888; font-size:12px; margin-bottom:8px;")
        layout.addWidget(eng_tip)

        # —— 备选引擎 Key ——
        key_label = QLabel("备选引擎 API Key（可选）")
        key_label.setStyleSheet("font-weight:bold; color:#7bbcff; margin-top:6px;")
        layout.addWidget(key_label)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.deepl_edit = QLineEdit(settings.value("deepl_key", ""))
        self.deepl_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.deepl_edit.setPlaceholderText("免费版 Key 以 :fx 结尾")
        self.deepl_edit.setMaximumWidth(240)
        form.addRow("DeepL Key:", self.deepl_edit)

        self.google_api_edit = QLineEdit(settings.value("google_api_key", ""))
        self.google_api_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_api_edit.setPlaceholderText("Google 云翻译 Key (AIza...)")
        self.google_api_edit.setMaximumWidth(240)
        form.addRow("Google 云翻译 Key:", self.google_api_edit)

        # 各 LLM 引擎的 Key 输入框（动态生成）
        self._key_edits = {}   # key_name -> QLineEdit
        _llm_key_rows = [
            ("deepseek", "DeepSeek Key:", "sk-..."),
            ("openai", "GPT Key:", "sk-..."),
            ("gemini", "Gemini Key:", "AIza..."),
            ("claude", "Claude Key:", "sk-ant-..."),
            ("glm", "GLM Key:", "xxxxxxxx.xxxxxxxx"),
            ("ernie", "文心一言 Key:", "百度千帆 Key"),
            ("doubao", "豆包 Key:", "火山引擎 Key"),
            ("qwen", "通义千问 Key:", "阿里百炼 sk-..."),
            ("kimi", "Kimi Key:", "sk-..."),
            ("hunyuan", "混元 HY-MT Key:", "腾讯云混元 sk-..."),
        ]
        for kn, label, ph in _llm_key_rows:
            e = QLineEdit(settings.value(f"{kn}_key", ""))
            e.setEchoMode(QLineEdit.EchoMode.Password)
            e.setPlaceholderText(ph)
            e.setMaximumWidth(240)        # 限宽，右侧留白，匀称
            form.addRow(label, e)
            self._key_edits[kn] = e
        # 兼容旧引用
        self.deepseek_edit = self._key_edits["deepseek"]
        self.hunyuan_edit = self._key_edits["hunyuan"]

        # 多风格翻译开关（默认勾选）
        self.multi_style_chk = QCheckBox("LLM 引擎多风格翻译")
        self.multi_style_chk.setChecked(settings.value("multi_style", "true") == "true")
        form.addRow("", self.multi_style_chk)
        ms_tip = QLabel("（主译文 + 书面/口语/俚语/美英式等辅助译法）")
        ms_tip.setWordWrap(True)
        ms_tip.setStyleSheet("color:#888; font-size:11px;")
        form.addRow("", ms_tip)

        layout.addLayout(form)

        show_chk = QPushButton("显示/隐藏")
        show_chk.setCheckable(True)
        show_chk.setFixedWidth(BTN_W)
        show_chk.toggled.connect(self._toggle_echo)
        _show_row = QHBoxLayout()
        _show_row.setSpacing(8)   # 收紧间距（对标主界面下拉与交换钮的距离）
        _show_row.addStretch()
        _show_row.addWidget(show_chk)
        # 查看日志按钮
        log_btn = QPushButton("查看日志")
        log_btn.setFixedWidth(BTN_W)
        log_btn.clicked.connect(self._open_log)
        _show_row.addWidget(log_btn)
        _show_row.addStretch()
        layout.addLayout(_show_row)

        tip = QLabel("提示：Google 免费无需 Key；Argos 纯离线无需 Key 与联网；"
                     "其余 LLM 引擎需各自 API Key。勾选『多风格翻译』后，"
                     "选用 LLM 引擎时会在主译文下给出多种风格译法。"
                     "朗读 edge-tts 无需 Key。Key 仅保存在本机，不上传。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#888; font-size:12px; margin-top:8px;")
        layout.addWidget(tip)

        # 取消在左、保存在右，统一宽度，靠右对齐，间距收紧
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        cancel_btn = QPushButton("取消")
        save_btn = QPushButton("保存")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.save)
        save_btn.setDefault(True)
        save_btn.setStyleSheet("QPushButton{background:#0e639c;border:none;border-radius:5px;color:white;}"\
            "QPushButton:hover{background:#1177bb;}")
        for b in (cancel_btn, save_btn):
            b.setFixedWidth(BTN_W)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

    def _toggle_echo(self, show):
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.deepl_edit.setEchoMode(mode)
        self.google_api_edit.setEchoMode(mode)
        for e in self._key_edits.values():
            e.setEchoMode(mode)

    def _open_log(self):
        """用系统默认程序打开日志文件。"""
        import os
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        p = _log_path()
        if not os.path.exists(p):
            try:
                open(p, "a", encoding="utf-8").close()
            except Exception:
                pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def save(self):
        self.settings.setValue("engine", self.engine_combo.currentText())
        self.settings.setValue("deepl_key", self.deepl_edit.text().strip())
        self.settings.setValue("google_api_key", self.google_api_edit.text().strip())
        for kn, e in self._key_edits.items():
            self.settings.setValue(f"{kn}_key", e.text().strip())
        self.settings.setValue(
            "multi_style", "true" if self.multi_style_chk.isChecked() else "false")
        self.accept()


class DocDialog(QDialog):
    """通用文档展示对话框 (关于 / 更新 / 帮助 / 开发者)。"""
    def __init__(self, title, html, parent=None, width=560, height=480):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        from PyQt6.QtGui import QFont
        browser.setFont(QFont("Microsoft YaHei", 10))
        # 用 setDefaultStyleSheet 让 QTextBrowser 可靠地应用字号（比内联 <style> 稳）
        browser.document().setDefaultStyleSheet(DOC_STYLESHEET)
        browser.setHtml(html)
        layout.addWidget(browser)
        btn_row = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(BTN_W)
        close_btn.setStyleSheet("QPushButton{background:#0e639c;border:none;border-radius:5px;color:white;}"\
            "QPushButton:hover{background:#1177bb;}")
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)


def changelog_html():
    parts = ['<div class="t1">版本更新说明</div><br>']
    for entry in CHANGELOG:
        parts.append(f'<div class="t2"><span class="ver">v{entry["version"]}</span>'
                     f' &nbsp;<span class="date">{entry["date"]}</span></div>')
        parts.append(f'<div class="t3">{entry["title"]}</div><ul>')
        for n in entry["notes"]:
            parts.append(f"<li>{n}</li>")
        parts.append("</ul>")
    return "".join(parts)


def about_html():
    return f"""
    <div class="t1">English Coach</div>
    <div class="t1" style="margin-top:0;">英语导师</div><br>
    <p>一款简洁的英语助手工具，集成<b>翻译</b>与<b>朗读</b>两大核心功能。</p>
    <p><b>当前版本：</b><span class="ver">v{APP_VERSION}</span></p>
    <p><b>开发者：</b>Strilen Liu</p>
    <p><a href="https://www.Strilen.com">www.Strilen.com</a>
       <a href="mailto:vfx@Strilen.com">vfx@Strilen.com</a>
       +8613811001963 +1(626)565-9633</p>
    <div class="t2">核心功能</div>
    <ul>
      <li><b>翻译</b> — 多引擎：Google（免费）、DeepL、Argos（离线）等传统引擎，外加 DeepSeek / OpenAI GPT / Gemini / Claude / 智谱GLM / 文心一言 / 豆包 / 通义千问 / Kimi / HunYuan 等大模型引擎；大模型引擎可开启多风格翻译（主译文 + 书面/口语/俚语/美英式等辅助译法）。</li>
      <li><b>朗读</b> — edge-tts（线上联网，音质佳）与 Kokoro（本地离线，无需联网）双引擎，多种中英嗓音、语速可调、卡拉OK逐词高亮。</li>
    </ul>
    <div class="t2">技术栈</div>
    <ul>
      <li>界面：PyQt6</li>
      <li>翻译：传统引擎 + 多家 LLM（OpenAI 兼容接口统一接入）</li>
      <li>语音：edge-tts（在线）+ Kokoro（离线）+ Qt Multimedia</li>
    </ul>
    <p class="date">© 2026 Strilen Liu. All rights reserved.</p>
    """


def readme_html():
    return f"""
    <div class="t1">使用说明</div><br>
    <div class="t2">系统要求（分享给他人前请阅读）</div>
    <ul>
      <li><b>macOS</b>：Intel 芯片可直接运行；Apple Silicon（M 系列）需通过 Rosetta 运行。
          系统需 <b>macOS 11.0 Big Sur 或更新</b>。建议预留 <b>2-3GB</b> 空间（含离线朗读模型）。</li>
      <li><b>Windows</b>：64 位 <b>Windows 10 / 11</b>。建议预留 2-3GB 空间。</li>
      <li><b>首次使用离线朗读（Kokoro）</b>：需联网下载语音模型（约 330MB），下载一次后即可完全离线。</li>
      <li><b>未签名应用提示</b>：本程序未签名，首次打开可能被系统拦截。
          macOS 可在「系统设置 → 隐私与安全性」点『仍要打开』，或终端执行
          <code>sudo xattr -rd com.apple.quarantine /Applications/EnglishCoach.app</code>；
          Windows 在 SmartScreen 提示点『更多信息 → 仍要运行』。</li>
      <li><b>联网</b>：翻译与在线朗读需联网（大陆请开代理）；离线引擎 Argos / Kokoro 无需联网。</li>
    </ul>
    <div class="t2">快速开始</div>
    <ul>
      <li>① 默认使用 <b>Google 免费引擎</b>，无需任何配置，打开即用。</li>
      <li>② 在左侧输入框粘贴或键入文本。</li>
      <li>③ 选择目标语言，点击 <b>翻译</b>，译文显示在右侧。</li>
      <li>④ 点击任一侧的 <b>朗读</b> 收听该框内文本。</li>
    </ul>
    <div class="t2">翻译引擎对比（请按需甄别）</div>
    <div class="t3">免费 / 离线引擎</div>
    <ul>
      <li><b>Google -线上联网</b>：网页版非官方接口。<b>免费、无需 Key</b>，即开即用。
          模型为 Google 网页翻译。<b>稳定性：不保证</b>——Google 未公开承诺此接口，
          可能随时变动或失效，大陆还需代理。适合日常随手翻。</li>
      <li><b>Google -API-Key联网</b>：官方 <b>Cloud Translation Basic (v2)</b>，NMT 神经翻译模型。
          需 Google Cloud 的 API Key 并<b>启用计费</b>。<b>收费：每月前 50 万字符免费</b>，
          超出按字符计费。<b>稳定性：官方保证，稳定可靠</b>。适合追求稳定的场景。</li>
      <li><b>Argos -离线本地</b>：纯本地离线，<b>无需 Key、无需联网</b>，免费。
          模型为 OpenNMT 离线中英模型（首次随程序内置或下载）。
          质量中等，胜在完全离线、隐私好。</li>
      <li><b>DeepL -API-Key联网</b>：以翻译质量著称。需 DeepL API Key
          （免费版 Key 以 :fx 结尾，每月 50 万字符免费；付费版更高额度）。稳定可靠。</li>
    </ul>
    <div class="t3">大模型（LLM）引擎 —— 支持「多风格翻译」</div>
    <p>以下引擎均为大语言模型，走各自官方 OpenAI 兼容接口，<b>需对应 API Key 且联网</b>。
       在「设置」勾选『多风格翻译』后，主译文下会附书面 / 口语 / 俚语 / 美式英式等多种译法，
       适合英语学习对比。各家收费、免费额度、稳定性以官网为准（政策常变）：</p>
    <ul>
      <li><b>DeepSeek</b>：中英俱佳、价格极低，国内可直接接入，推荐首选。</li>
      <li><b>智谱GLM-4-Flash</b>：中文地道，<b>该型号长期免费</b>，国内接入简单，推荐兜底。</li>
      <li><b>通义千问</b>：阿里，非英语表现强，有新用户免费额度，国内接入简单。</li>
      <li><b>Kimi</b>：月之暗面，不限 Token 仅限频率，适合慢翻长文。</li>
      <li><b>文心一言</b>：百度，中文理解精准，基础模型有免费额度。</li>
      <li><b>字节豆包</b>：火山引擎，有永久免费额度，接口稳定。</li>
      <li><b>HunYuan</b>：腾讯混元，需腾讯云 Key。</li>
      <li><b>OpenAI GPT</b>：能力顶尖，但大陆需海外信用卡 + 纯净海外 IP，封号风险高，门槛大。</li>
      <li><b>Google Gemini</b>：能力强，免费额度高，但大陆需代理，稳定性看网络。</li>
      <li><b>Claude</b>：能力强，大陆同样需海外信用卡 + 代理，门槛高。</li>
    </ul>
    <p style="color:#888;">提示：模型默认版本与端点可能随各家政策调整；若某引擎报错，多为 Key 未填、
       额度用尽、模型名变动或网络问题。Key 仅保存在本机，不上传。</p>
    <div class="t2">朗读引擎</div>
    <ul>
      <li><b>-线上联网（edge-tts）</b>：微软在线语音，音质最好，<b>需联网</b>（大陆需代理）。</li>
      <li><b>-离线本地（Kokoro）</b>：本地离线神经语音，<b>无需联网、CPU 即可</b>，
          英文质量好、原生时间戳让卡拉OK更准；中文为其支持语言但非强项。
          需随程序安装 Kokoro 及模型。</li>
    </ul>
    <div class="t2">选区联动</div>
    <p>在原文或译文一侧选中一段文字，程序会临时翻译该段并在另一侧用<b>灰色</b>自动高亮
       最匹配的区间（近似匹配，可能略有偏差）。灰色联动区间也可直接朗读。</p>
    <div class="t2">常见问题</div>
    <ul>
      <li><b>翻译/朗读报错？</b> 多为网络或 Key 问题；大陆请确认代理 / Clash Verge 已开启，
          或改用离线引擎（Argos 翻译 / Kokoro 朗读）。</li>
      <li><b>卡拉OK字幕？</b> 朗读时逐词高亮青蓝绿，跟随进度。</li>
      <li><b>Key 存在哪？</b> 保存在本机 (QSettings)，不上传。</li>
    </ul>
    """


def developer_html():
    return f"""
    <div class="t1">开发者介绍</div>
    <p><b>{APP_AUTHOR}</b> —— VFX 从业者，专注影视特效、合成（Nuke）与创意工具开发。</p>
    <div class="t2">联系方式</div>
    <ul>
      <li>邮箱：<a href="mailto:{APP_EMAIL}">{APP_EMAIL}</a></li>
      <li>个人站点：<a href="https://{APP_WEBSITE}">{APP_WEBSITE}</a></li>
    </ul>
    <div class="t2">关于本工具</div>
    <p>{APP_NAME} 源于日常英语阅读与学习需求，强调「轻量、本地、即用」，
       延续作者一贯的本地工具开发风格。</p>
    """


# =============================================================================
#  主窗口
# =============================================================================

def _sentence_spans(text):
    """按中英文句末标点把文本切成句子，返回 [(start,end), ...]（含位置）。"""
    import re
    if not text:
        return []
    spans = []
    start = 0
    for m in re.finditer(r'[。！？；…\.\!\?;\n]+', text):
        end = m.end()
        if text[start:end].strip():
            spans.append((start, end))
        start = end
    if start < len(text) and text[start:].strip():
        spans.append((start, len(text)))
    return spans or [(0, len(text))]


def _proportional_span(src_full, s0, s1, tgt_full):
    """把原文 [s0,s1) 选区按"段落对齐 + 段内比例"映射到译文区间。
    不调用翻译引擎。中英文标点都作为段落切点，先定位选区落在哪个句段，
    再在译文对应句段内按字符比例取区间，英文吸附整词。"""
    import re
    if not src_full or not tgt_full:
        return None
    s0 = max(0, min(s0, len(src_full)))
    s1 = max(s0, min(s1, len(src_full)))
    # 句段切分（保留位置）
    def segments(text):
        segs = []
        start = 0
        for m in re.finditer(r'[。！？；…\.\!\?;\n]+', text):
            end = m.end()
            segs.append((start, end))
            start = end
        if start < len(text):
            segs.append((start, len(text)))
        return segs or [(0, len(text))]
    src_segs = segments(src_full)
    tgt_segs = segments(tgt_full)
    # 选区中心落在哪个源句段
    mid = (s0 + s1) / 2.0
    si = 0
    for i, (a, b) in enumerate(src_segs):
        if a <= mid < b:
            si = i; break
    else:
        si = len(src_segs) - 1
    # 对应译文句段（按段索引比例映射，段数可能不同）
    ti = int(round(si / max(1, len(src_segs) - 1) * (len(tgt_segs) - 1))) if len(src_segs) > 1 else 0
    ta, tb = tgt_segs[min(ti, len(tgt_segs) - 1)]
    sa, sb = src_segs[si]
    seg_len = max(1, sb - sa)
    # 段内比例
    r0 = (s0 - sa) / seg_len
    r1 = (s1 - sa) / seg_len
    r0 = max(0.0, min(1.0, r0)); r1 = max(0.0, min(1.0, r1))
    tlen = tb - ta
    ts = ta + int(r0 * tlen)
    te = ta + int(r1 * tlen)
    if te <= ts:
        te = min(tb, ts + 1)
    # 英文整词吸附
    while ts > ta and tgt_full[ts-1].isalnum() and tgt_full[ts].isalnum():
        ts -= 1
    while te < tb and tgt_full[te-1].isalnum() and tgt_full[te].isalnum():
        te += 1
    while ts < te and tgt_full[ts].isspace():
        ts += 1
    while te > ts and tgt_full[te-1].isspace():
        te -= 1
    return (ts, te) if te > ts else None


def _best_match_span(haystack, needle, pos_ratio=None):
    """在 haystack 中找与 needle 最相似的连续字符区间，返回 (start, end) 或 None。
    用于选区联动：把临时译文 needle 在对方文本里定位到最近似的合理区间。
    pos_ratio 是源选区在源文本的相对位置（0~1），用于位置加权，避免选到
    文中其它相似但位置不对的段落。"""
    import difflib
    if not haystack or not needle:
        return None
    needle = needle.strip()
    n = len(needle)
    H = len(haystack)
    if n == 0 or H == 0:
        return None
    sm = difflib.SequenceMatcher()
    sm.set_seq2(needle)
    best = (-1.0, None)
    min_w = max(1, int(n * 0.6))
    max_w = min(H, int(n * 1.6) + 2)
    step = max(1, n // 8)
    target_center = (pos_ratio * H) if pos_ratio is not None else None
    for start in range(0, H, step):
        for w in (min_w, n, max_w):
            end = min(H, start + w)
            if end <= start:
                continue
            window = haystack[start:end]
            sm.set_seq1(window)
            ratio = sm.quick_ratio()
            score = ratio
            # 位置加权：窗口中心离目标位置越近，加分越多（最多 +0.15）
            if target_center is not None:
                center = (start + end) / 2.0
                dist = abs(center - target_center) / H   # 0~1
                score += 0.15 * (1.0 - dist)
            if score > best[0]:
                best = (score, (start, end), ratio)
        if start + min_w >= H:
            break
    # 相似度太低则放弃（用原始相似度判断，不含位置加权）
    if best[1] is None or best[2] < 0.35:
        return None
    s, e = best[1]
    # 化零为整：英文不要停在半个单词中间，把边界吸附到最近的词边界/空白
    # 向左把 s 移到单词开头
    while s > 0 and haystack[s-1].isalnum() and haystack[s].isalnum():
        s -= 1
    # 向右把 e 移到单词结尾
    while e < len(haystack) and haystack[e-1].isalnum() and (e < len(haystack) and haystack[e].isalnum()):
        e += 1
    # 去掉首尾空白
    while s < e and haystack[s].isspace():
        s += 1
    while e > s and haystack[e-1].isspace():
        e -= 1
    return (s, e)


class KaraokeHighlighter(QSyntaxHighlighter):
    """逐词高亮：朗读已读部分上青蓝绿背景。可选地在选区上铺蓝色底，
    朗读经过处用绿色覆盖，读完恢复蓝色。比 ExtraSelection 跨平台更可靠。"""
    def __init__(self, document):
        super().__init__(document)
        self._hl_start = 0
        self._hl_end = 0
        self._sel_start = 0      # 蓝色选区
        self._sel_end = 0
        self._link_start = 0     # 灰色联动选区（非活跃，自动匹配）
        self._link_end = 0
        # 朗读已读：偏青蓝、饱和度降低（更柔和）。只改背景，不改字色。
        self._fmt = QTextCharFormat()
        self._fmt.setBackground(QColor("#5aa8b0"))
        # 蓝色选区底色（只改背景）
        self._sel_fmt = QTextCharFormat()
        self._sel_fmt.setBackground(QColor("#3a6ea5"))
        # 灰色联动选区底色（非活跃，只改背景）
        self._link_fmt = QTextCharFormat()
        self._link_fmt.setBackground(QColor("#5a5a5a"))

    def set_range(self, start, end):
        self._hl_start = max(0, start)
        self._hl_end = max(0, end)
        self.rehighlight()

    def set_selection(self, start, end):
        self._sel_start = max(0, start)
        self._sel_end = max(0, end)
        self.rehighlight()

    def set_link(self, start, end):
        self._link_start = max(0, start)
        self._link_end = max(0, end)
        self.rehighlight()

    def clear_link(self):
        self._link_start = 0
        self._link_end = 0
        self.rehighlight()

    def clear_selection(self):
        self._sel_start = 0
        self._sel_end = 0
        self.rehighlight()

    def clear_range(self):
        self._hl_start = 0
        self._hl_end = 0
        self.rehighlight()

    def clear_all(self):
        self._hl_start = self._hl_end = 0
        self._sel_start = self._sel_end = 0
        self._link_start = self._link_end = 0
        self.rehighlight()

    def highlightBlock(self, text):
        block_start = self.currentBlock().position()
        block_end = block_start + len(text)
        # 灰色联动选区（最底层）
        ls = max(self._link_start, block_start)
        le = min(self._link_end, block_end)
        if le > ls:
            self.setFormat(ls - block_start, le - ls, self._link_fmt)
        # 蓝色选区
        ss = max(self._sel_start, block_start)
        se = min(self._sel_end, block_end)
        if se > ss:
            self.setFormat(ss - block_start, se - ss, self._sel_fmt)
        # 绿色已读（最上层）
        s = max(self._hl_start, block_start)
        e = min(self._hl_end, block_end)
        if e > s:
            self.setFormat(s - block_start, e - s, self._fmt)


class HistoryDialog(QDialog):
    """翻译历史弹窗：按天分组，每条显示开头一段提示，悬停蓝色高亮 + 气泡显示全文。
    双击或选中后点『载入翻译』返回该条。"""
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("翻译历史")
        self.setMinimumSize(520, 560)
        self.chosen = None
        self._items = items

        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        layout = QVBoxLayout(self)
        info = QLabel("点选一条记录后『载入并翻译』；悬停可见全文。")
        info.setStyleSheet("color:#888; font-size:12px;")
        layout.addWidget(info)

        self.listw = QListWidget()
        self.listw.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listw.setWordWrap(False)
        self.listw.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.listw.setStyleSheet("""
            QToolTip { background:#2d2d30; color:#e8e8e8; border:1px solid #4a4a4a;
                padding:2px 5px; border-radius:6px; }
            QListWidget { background:#252526; border:1px solid #3a3a3a; border-radius:6px; }
            QListWidget::item { padding:8px 10px; border-bottom:1px solid #2f2f2f; }
            QListWidget::item:hover { background:#0e639c; color:white; }
            QListWidget::item:selected { background:#0e639c; color:white; }
        """)
        layout.addWidget(self.listw, 1)

        # 按天分组（倒序，新的在上）
        import datetime
        cur_day = None
        for it in reversed(items):
            ts = it.get("ts", "")
            day = ts[:10]
            if day != cur_day:
                cur_day = day
                header = QListWidgetItem(f"——— {day} ———")
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                header.setForeground(QColor("#4ea1ff"))
                self.listw.addItem(header)
            src = it.get("src", "").replace("\n", " ")
            preview = src[:28] + ("…" if len(src) > 28 else "")
            li = QListWidgetItem(f"  {preview}")
            full = f"【原文】{it.get('src','')}\n\n【译文】{it.get('tgt','')}\n\n[{it.get('engine','')}]"
            li.setToolTip(full)                    # 悬停气泡显示全文
            li.setData(Qt.ItemDataRole.UserRole, it)
            self.listw.addItem(li)

        self.listw.itemDoubleClicked.connect(self._choose)

        btns = QHBoxLayout()
        view_file_btn = QPushButton("检查历史")
        view_file_btn.clicked.connect(self._open_history_file)
        dl_btn = QPushButton("下载文档")
        dl_btn.clicked.connect(self._download_history)
        load_btn = QPushButton("重新载入")
        load_btn.clicked.connect(self._load_selected)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.reject)
        for b in (view_file_btn, dl_btn, load_btn):
            b.setAutoDefault(False); b.setDefault(False)   # 去掉『检查历史』等的默认蓝
        close_btn.setStyleSheet("QPushButton{background:#0e639c;border:none;border-radius:5px;color:white;}"\
            "QPushButton:hover{background:#1177bb;}")
        for b in (view_file_btn, dl_btn, load_btn, close_btn):
            b.setFixedWidth(BTN_W)
        btns.setSpacing(6)
        btns.addStretch()
        btns.addWidget(view_file_btn)
        btns.addWidget(dl_btn)
        btns.addWidget(load_btn)
        btns.addWidget(close_btn)
        layout.addLayout(btns)

    def _download_history(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os, datetime
        filters = "文本 (*.txt);;Markdown (*.md);;JSON (*.json);;Word (*.docx);;PDF (*.pdf)"
        # 默认文件名 TH 日期 时间.txt；默认目录记忆（首次下载目录）
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")
        last_dir = ""
        try:
            last_dir = self.parent().settings.value("last_dir_export", "")
        except Exception:
            pass
        if not last_dir or not os.path.isdir(last_dir):
            last_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        default = os.path.join(last_dir, f"TH {ts}.txt")
        path, sel = QFileDialog.getSaveFileName(self, "下载历史文档", default, filters)
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        try:
            items = self._items
            if ext == ".json":
                import json as _j
                with open(path, "w", encoding="utf-8") as f:
                    _j.dump(items, f, ensure_ascii=False, indent=2)
            elif ext == ".docx":
                from docx import Document
                doc = Document()
                doc.add_heading("翻译历史", 0)
                for it in items:
                    doc.add_heading(f"{it.get('ts','')} · {it.get('engine','')}", level=2)
                    doc.add_paragraph("【原文】" + it.get("src", ""))
                    doc.add_paragraph("【译文】" + it.get("tgt", ""))
                doc.save(path)
            elif ext == ".pdf":
                self._history_pdf(path, items)
            elif ext == ".md":
                with open(path, "w", encoding="utf-8") as f:
                    f.write("# 翻译历史\n\n")
                    for it in items:
                        f.write(f"## {it.get('ts','')} · {it.get('engine','')}\n\n")
                        f.write(f"**原文**：{it.get('src','')}\n\n")
                        f.write(f"**译文**：{it.get('tgt','')}\n\n---\n\n")
            else:  # txt
                with open(path, "w", encoding="utf-8") as f:
                    for it in items:
                        f.write(f"[{it.get('ts','')} · {it.get('engine','')}]\n")
                        f.write("原文：" + it.get("src", "") + "\n")
                        f.write("译文：" + it.get("tgt", "") + "\n\n")
            QMessageBox.information(self, "已下载", f"已保存到：\n{path}")
            try:
                self.parent().settings.setValue("last_dir_export", os.path.dirname(path))
            except Exception:
                pass
        except Exception as e:
            QMessageBox.warning(self, "下载失败", str(e))

    def _history_pdf(self, path, items):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        font = "Helvetica"
        for fp in ("/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/PingFang.ttc",
                   "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc"):
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CJK", fp)); font = "CJK"; break
                except Exception:
                    pass
        c = canvas.Canvas(path, pagesize=A4)
        w, h = A4; x, y = 2*cm, h-2*cm
        c.setFont(font, 11)
        for it in items:
            for line in (f"[{it.get('ts','')} · {it.get('engine','')}]",
                         "原文：" + it.get("src",""), "译文：" + it.get("tgt",""), ""):
                s = line
                while True:
                    chunk = s[:42]; s = s[42:]
                    c.drawString(x, y, chunk); y -= 0.6*cm
                    if y < 2*cm:
                        c.showPage(); c.setFont(font, 11); y = h-2*cm
                    if not s:
                        break
        c.save()

    def _open_history_file(self):
        import os
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        p = _history_path()
        if os.path.exists(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _choose(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.chosen = data
            self.accept()

    def _load_selected(self):
        it = self.listw.currentItem()
        if it:
            data = it.data(Qt.ItemDataRole.UserRole)
            if data:
                self.chosen = data
                self.accept()


class PillBusyBar(QWidget):
    """自绘胶囊形忙碌指示条：Qt 原生不确定进度条的滑块到两端会变方角
    （样式引擎限制），改用 QPainter 自绘，滑块任何位置都是完整胶囊。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._pos = 0.0
        self._dir = 1
        self._t = QTimer(self)
        self._t.setInterval(16)
        self._t.timeout.connect(self._tick)

    def showEvent(self, e):
        self._t.start(); super().showEvent(e)

    def hideEvent(self, e):
        self._t.stop(); super().hideEvent(e)

    def _tick(self):
        self._pos += 0.018 * self._dir
        if self._pos >= 1.0:
            self._pos, self._dir = 1.0, -1
        elif self._pos <= 0.0:
            self._pos, self._dir = 0.0, 1
        self.update()

    def paintEvent(self, e):
        from PyQt6.QtGui import QPainter, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 26))      # 极淡胶囊槽
        p.drawRoundedRect(0, 0, w, h, r, r)
        cw = max(int(w * 0.28), h * 2)              # 滑块宽
        x = int((w - cw) * self._pos)
        p.setBrush(QColor("#5aa8b0"))               # 青色胶囊滑块
        p.drawRoundedRect(x, 0, cw, h, r, r)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Strilen", "EnglishCoach")
        self.translate_worker = None
        self.tts_worker = None

        # 老系统 / 缺音频后端时，多媒体初始化失败不应阻止主界面弹出
        self.player = None
        self.audio_out = None
        try:
            self.player = QMediaPlayer()
            self.audio_out = QAudioOutput()
            self.player.setAudioOutput(self.audio_out)
            self.player.positionChanged.connect(self._on_play_position)
            self.player.durationChanged.connect(self._on_play_duration)
            self.player.playbackStateChanged.connect(self._on_play_state)
        except Exception as e:
            print(f"[warn] 音频初始化失败，朗读功能将不可用: {e}")

        # 朗读状态
        self._speak_editor = None      # 当前朗读的文本框
        self._speak_boundaries = []    # 词边界列表
        # 两侧各自独立的音频缓存（互不干扰）：
        #   bytes=已生成音频, boundaries=卡拉OK边界, duration=时长, position=暂停位置, sig=签名
        self._side_cache = {
            "src": {"bytes": None, "boundaries": [], "duration": 0, "position": 0, "sig": None},
            "tgt": {"bytes": None, "boundaries": [], "duration": 0, "position": 0, "sig": None},
        }
        self._speak_rate = 0           # 当前语速（用于 offset 换算）
        self._seeking = False          # 进度条拖动中
        self._karaoke_timer = QTimer(self)   # 高频驱动逐词高亮
        self._karaoke_timer.setInterval(50)
        self._karaoke_timer.timeout.connect(self._karaoke_tick)

        self.setWindowTitle(f"English Coach  v{APP_VERSION}")
        self.setAcceptDrops(True)   # 支持拖拽文件导入
        self.setWindowIcon(self._load_app_icon())
        self.setMinimumSize(720, 480)   # 交换钮居中，宽度较原来缩小约400px
        self.resize(920, 620)

        self._build_central()
        self._build_statusbar()
        self._apply_style()
        self._install_bundled_argos_models()

    def _load_app_icon(self):
        """优先加载随包的 icon_1024.png；找不到则回退内置 SVG 图标。"""
        # PyInstaller 打包后资源在 sys._MEIPASS；开发时在脚本目录
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        for name in ("icon_1024.png", "icon.png"):
            p = os.path.join(base, name)
            if os.path.exists(p):
                ic = QIcon(p)
                if not ic.isNull():
                    return ic
        return Icons.icon("app", "#4ea1ff")

    def _install_bundled_argos_models(self):
        """启动时确保内置中英模型已安装（幂等）。"""
        try:
            _ensure_argos_models(("en", "zh"))
        except Exception:
            pass

    # ---------- 顶部功能按钮（设置/更新/帮助/关于）----------
    def _make_tool_buttons(self):
        """返回一个含 设置/更新/帮助/关于 的横向布局，用于放在顶排右侧。"""
        box = QHBoxLayout()
        box.setSpacing(4)

        def mk(icon, tip, slot):
            b = QPushButton(Icons.icon(icon), "")
            b.setFixedSize(34, 34)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            return b

        box.addWidget(mk("settings", "设置", self.open_settings))
        box.addWidget(mk("history", "更新说明",
                         lambda: DocDialog("版本更新说明", changelog_html(), self).exec()))
        box.addWidget(mk("help", "使用说明",
                         lambda: DocDialog("使用说明", readme_html(), self).exec()))
        box.addWidget(mk("info", "关于",
                         lambda: DocDialog("关于 EnglishCoach", about_html(), self).exec()))
        return box

    # ---------- 中央区域 ----------
    def _build_central(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 12, 14, 10)
        root.setSpacing(10)

        # —— 第一排：翻译引擎(左) | 原文语言(贴交换) | 交换(中央) | 译文语言(贴交换) | 设置区(右) ——
        self.src_combo = QComboBox()
        self.src_combo.addItems(LANG_OPTIONS)
        fit_combo_width(self.src_combo)
        self.src_combo.setToolTip("原文语言")
        self.tgt_combo = QComboBox()
        self.tgt_combo.addItems(LANG_OPTIONS)
        fit_combo_width(self.tgt_combo)
        self.tgt_combo.setCurrentText("自动检测")
        self.tgt_combo.setToolTip("译文语言")

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(ALL_ENGINES)
        fit_combo_width(self.engine_combo)
        self.engine_combo.setCurrentText(
            self.settings.value("engine", ENGINE_GOOGLE))
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        self.engine_combo.setToolTip("翻译引擎")
        # 原文/译文语言变化 -> 无条件强制重新翻译（等同点翻译按钮）
        self.src_combo.currentTextChanged.connect(lambda _t: self._on_lang_changed())
        self.tgt_combo.currentTextChanged.connect(lambda _t: self._on_lang_changed())

        swap_btn = QPushButton(Icons.icon("swap"), "")
        swap_btn.setToolTip("交换源文译文内容")
        swap_btn.setFixedSize(44, 34)
        swap_btn.clicked.connect(self.swap_sides)

        from PyQt6.QtWidgets import QGridLayout, QWidget as _QWt
        left_w = _QWt(); ll = QHBoxLayout(left_w); ll.setContentsMargins(0,0,0,0)
        ll.addWidget(self.engine_combo)     # 引擎下拉左对齐贴左
        ll.addStretch()
        ll.addWidget(self.src_combo)        # 原文语言右对齐贴近交换钮

        right_w = _QWt(); rl = QHBoxLayout(right_w); rl.setContentsMargins(0,0,0,0)
        rl.addWidget(self.tgt_combo)        # 译文语言左对齐贴近交换钮
        rl.addStretch()
        rl.addLayout(self._make_tool_buttons())

        top_grid = QGridLayout()
        top_grid.setContentsMargins(0, 0, 0, 0)
        top_grid.setHorizontalSpacing(10)
        top_grid.addWidget(left_w, 0, 0)
        top_grid.addWidget(swap_btn, 0, 1)
        top_grid.addWidget(right_w, 0, 2)
        top_grid.setColumnStretch(0, 1)
        top_grid.setColumnStretch(2, 1)
        root.addLayout(top_grid)

        # —— 双栏文本（仅文本框，标题与操作按钮移到下方按钮排）——
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(10)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("在此输入或粘贴文本…")
        self.input_edit.setToolTip("原文文字")
        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText("译文显示在这里…")
        self.output_edit.setToolTip("译文文字")
        # 原文/译文区字号放大，更醒目
        _edit_font = QFont("Microsoft YaHei", 13)
        self.input_edit.setFont(_edit_font)
        self.output_edit.setFont(_edit_font)
        # 强制选区为蓝色（跨平台一致，避免某些系统出现绿色等异色）
        from PyQt6.QtGui import QPalette
        for _ed in (self.input_edit, self.output_edit):
            _pal = _ed.palette()
            _pal.setColor(QPalette.ColorRole.Highlight, QColor("#3a6ea5"))
            _pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            _ed.setPalette(_pal)
        # 卡拉OK高亮器（QSyntaxHighlighter，跨平台可靠渲染）
        self._hl_input = KaraokeHighlighter(self.input_edit.document())
        self._hl_output = KaraokeHighlighter(self.output_edit.document())
        # 选区联动：选一边的文字，自动在另一边灰色高亮对应区间
        self._link_guard = False
        self._link_timer = QTimer(self)
        self._link_timer.setSingleShot(True)
        self._link_timer.setInterval(250)
        self._link_timer.timeout.connect(self._do_selection_link)
        self._link_pending_src = None
        self.input_edit.selectionChanged.connect(lambda: self._on_selection_changed(self.input_edit))
        self.output_edit.selectionChanged.connect(lambda: self._on_selection_changed(self.output_edit))
        # 点击/聚焦某区即把它设为主动区（蓝框跳过去，颜色互换）
        # 区域激活改由 eventFilter 的鼠标按下事件处理（点空白也能切换）
        # 让拖到文本框里的文件也走"导入内容"，而非粘贴文件名/URL
        self.input_edit.installEventFilter(self)
        self.output_edit.installEventFilter(self)
        self.input_edit.viewport().installEventFilter(self)
        self.output_edit.viewport().installEventFilter(self)

        splitter.addWidget(self.input_edit)
        splitter.addWidget(self.output_edit)
        splitter.setSizes([460, 460])
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        # 输入即译：停止输入约 0.8 秒后自动翻译（手动按钮仍保留）
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.setInterval(800)
        self._auto_timer.timeout.connect(self._auto_translate)
        self.input_edit.textChanged.connect(self._on_input_changed)
        self.output_edit.textChanged.connect(self._on_output_changed)

        # —— 操作排：原文 | 复制粘贴清空 | 导出原文+导入文件 | 上一条+历史 | 翻译 |
        #             译文复制粘贴清空 | 导出译文+导出文件 | 译文 ——
        def _mini_btn(icon, tip, slot):
            b = QPushButton(Icons.icon(icon), "")
            b.setFixedSize(34, 34)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            return b

        # 原文侧：导出当前原文 + 导入文件
        self.export_src_btn = _mini_btn("export", "导出当前原文", lambda: self._export_text("src"))
        self.import_btn = _mini_btn("file", "导入文件", self._import_file)
        src_io = QHBoxLayout(); src_io.setSpacing(3); src_io.setContentsMargins(10, 0, 0, 0)
        src_io.addWidget(self.export_src_btn); src_io.addWidget(self.import_btn)

        # 上一条 + 历史
        hist_box = QHBoxLayout()
        hist_box.setSpacing(3)
        hist_box.setContentsMargins(10, 0, 0, 0)
        self.prev_src_btn = _mini_btn("undo", "载入上一条原文", self._load_prev_source)
        self.history_btn = _mini_btn("list", "翻译历史", self._open_history_dialog)
        self.next_src_btn = _mini_btn("undo", "载入下一条原文", self._load_next_source)
        from PyQt6.QtGui import QTransform as _QT, QIcon as _QIc
        _pm = Icons.icon("undo").pixmap(20, 20).transformed(_QT().scale(-1, 1))
        self.next_src_btn.setIcon(_QIc(_pm))   # 镜像撤销图标=前进
        hist_box.addWidget(self.prev_src_btn)
        hist_box.addWidget(self.next_src_btn)
        hist_box.addWidget(self.history_btn)

        # 译文侧：导出当前译文 + 导出翻译后文件
        self.export_tgt_btn = _mini_btn("export", "导出当前译文", lambda: self._export_text("tgt"))
        self.export_file_btn = _mini_btn("file_down", "导出翻译后文件", self._export_file)
        self.export_file_btn.setEnabled(False)
        self.export_file_btn.setVisible(False)   # 平时隐藏，导入成功后才出现
        tgt_io = QHBoxLayout(); tgt_io.setSpacing(3); tgt_io.setContentsMargins(10, 0, 0, 0)
        tgt_io.addWidget(self.export_tgt_btn); tgt_io.addWidget(self.export_file_btn)

        self.translate_btn = QPushButton(Icons.icon("translate"), "  翻译")
        self.translate_btn.setObjectName("primary")
        self.translate_btn.setMinimumHeight(40)
        self.translate_btn.setToolTip("翻译")
        self.translate_btn.clicked.connect(self.do_translate)

        from PyQt6.QtWidgets import QGridLayout, QWidget as _QW
        left_w = _QW(); left_l = QHBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(0)   # 组间距只由各组margin(10)决定，全局统一
        left_l.addLayout(self._panel_buttons(self.input_edit))
        left_l.addLayout(src_io)
        left_l.addLayout(hist_box)
        left_l.addSpacing(10)
        clear_src_btn = QPushButton(Icons.icon("clear"), "")
        clear_src_btn.setFixedSize(34, 34)
        clear_src_btn.setToolTip("清空")
        clear_src_btn.clicked.connect(lambda: self._clear_editor(self.input_edit))
        left_l.addWidget(clear_src_btn)
        left_l.addStretch()          # 整组左对齐

        right_w = _QW(); right_l = QHBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(0)
        right_l.addStretch()         # 整组右对齐
        right_l.addLayout(self._panel_buttons(self.output_edit))
        right_l.addLayout(tgt_io)
        right_l.addSpacing(10)
        clear_tgt_btn = QPushButton(Icons.icon("clear"), "")
        clear_tgt_btn.setFixedSize(34, 34)
        clear_tgt_btn.setToolTip("清空")
        clear_tgt_btn.clicked.connect(lambda: self._clear_editor(self.output_edit))
        right_l.addWidget(clear_tgt_btn)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(left_w, 0, 0)
        grid.addWidget(self.translate_btn, 0, 1)
        grid.addWidget(right_w, 0, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(2, 1)
        root.addLayout(grid)

        # ===== 朗读音频条：原文 / 译文 各一组 =====
        play_groups = QHBoxLayout()
        play_groups.setSpacing(16)
        play_groups.addLayout(self._make_play_group("src"), 1)
        play_groups.addLayout(self._make_play_group("tgt"), 1)
        root.addLayout(play_groups)

        # 朗读控制条（嗓音 + 语速）：标签去掉，改成悬停气球提示
        tts_bar = QHBoxLayout()
        self.zh_voice_combo = QComboBox()
        self.zh_voice_combo.addItems(ZH_VOICES.keys())
        fit_combo_width(self.zh_voice_combo)
        self.zh_voice_combo.setCurrentText(
            self.settings.value("zh_voice", next(iter(ZH_VOICES))))
        self.zh_voice_combo.currentTextChanged.connect(self._on_zh_voice_changed)
        self.zh_voice_combo.setToolTip("中文嗓音")
        tts_bar.addWidget(self.zh_voice_combo)

        self.en_voice_combo = QComboBox()
        self.en_voice_combo.addItems(EN_VOICES.keys())
        fit_combo_width(self.en_voice_combo)
        self.en_voice_combo.setCurrentText(
            self.settings.value("en_voice", next(iter(EN_VOICES))))
        self.en_voice_combo.currentTextChanged.connect(self._on_en_voice_changed)
        self.en_voice_combo.setToolTip("英文嗓音")
        tts_bar.addWidget(self.en_voice_combo)
        tts_bar.addSpacing(12)

        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setObjectName("rateSlider")
        self.rate_slider.setRange(-50, 50)
        self.rate_slider.setValue(0)
        self.rate_slider.setMinimumWidth(100)
        self.rate_label = QLabel("0%")
        self._update_rate_tooltip(0)   # 初始化语速气球
        self.rate_slider.valueChanged.connect(
            lambda v: self.rate_label.setText(f"{'+' if v>=0 else ''}{v}%"))
        self.rate_slider.valueChanged.connect(self._update_rate_tooltip)
        # 语速变更防抖：拖动停止 0.4s 后才重新朗读，避免拖动过程频繁触发
        self._rate_timer = QTimer(self)
        self._rate_timer.setSingleShot(True)
        self._rate_timer.setInterval(400)
        self._rate_timer.timeout.connect(self._on_voice_or_rate_changed)
        self.rate_slider.valueChanged.connect(
            lambda _: self._rate_timer.start())
        tts_bar.addWidget(self.rate_slider, 1)
        self.rate_label.setVisible(False)   # 数值改用气球提示，界面不再显示
        tts_bar.addWidget(self.rate_label)
        root.addLayout(tts_bar)

        self.setCentralWidget(central)
        # 兼容别名：默认指向原文侧；朗读某侧时在 do_speak 里切换到该侧
        self.play_slider = self.play_slider_src
        self.download_audio_btn = self.dl_src_btn
        self._active_side = "src"
        self._active_editor = self.input_edit
        self.input_edit.setProperty("activeRegion", "1")
        self.output_edit.setProperty("activeRegion", "0")

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        et = event.type()
        if et == QEvent.Type.MouseButtonPress:
            # 鼠标按下任何位置（文字或空白）都切换主动区——比 cursorPositionChanged
            # 可靠（点空白处光标可能不动、信号不发）
            editor = None
            if obj in (self.input_edit, self.input_edit.viewport()):
                editor = self.input_edit
            elif obj in (self.output_edit, self.output_edit.viewport()):
                editor = self.output_edit
            if editor is not None:
                if editor is getattr(self, "_active_editor", None):
                    # 点主动区：保持主动，清掉联动选区对（原生选区由点击本身清）
                    self._clear_selection_pair()
                else:
                    self._activate_region(editor)
            return False   # 不吞事件，光标照常定位
        if et in (QEvent.Type.DragEnter, QEvent.Type.DragMove):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                return True
        elif et == QEvent.Type.Drop:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                if urls:
                    path = urls[0].toLocalFile()
                    if path:
                        event.acceptProposedAction()
                        self._do_import(path)   # 导入内容，而非粘贴文件名
                        return True
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._do_import(path)

    def _make_play_group(self, side):
        """构建一组朗读控制（side='src' 原文 / 'tgt' 译文）：
        音频条 [朗读▶] [停止■] [下载↓]。导入/导出按钮在上方操作排。"""
        editor = self.input_edit if side == "src" else self.output_edit
        name = "原文" if side == "src" else "译文"
        box = QHBoxLayout()
        box.setSpacing(4)

        # 音频进度条
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 1000)
        slider.setValue(0)
        slider.setMinimumWidth(90)
        slider.setToolTip(f"{name}朗读进度")
        slider.sliderPressed.connect(lambda s=side: self._on_seek_start(s))
        slider.sliderReleased.connect(lambda s=side: self._on_seek_end_side(s))
        slider.sliderMoved.connect(lambda v, s=side: self._on_seek_moved(v, s))
        box.addWidget(slider, 1)

        speak_btn = QPushButton(Icons.icon("speak"), "")
        speak_btn.setFixedSize(34, 34)
        speak_btn.setToolTip(f"朗读{name}")
        speak_btn.clicked.connect(lambda _=False, e=editor: self._toggle_speak(e))
        box.addWidget(speak_btn)

        stop_btn = QPushButton(Icons.icon("stop"), "")
        stop_btn.setFixedSize(34, 34)
        stop_btn.setToolTip(f"停止朗读{name}")
        stop_btn.clicked.connect(lambda _=False, e=editor: self._stop_side(e))
        box.addWidget(stop_btn)

        dl_btn = QPushButton(Icons.icon("download"), "")
        dl_btn.setFixedSize(34, 34)
        dl_btn.setToolTip(f"下载{name}朗读音频")
        dl_btn.setEnabled(False)
        dl_btn.clicked.connect(lambda _=False, s=side: self._download_audio(s))
        box.addWidget(dl_btn)

        clr_btn = QPushButton(Icons.icon("clear"), "")
        clr_btn.setFixedSize(34, 34)
        clr_btn.setToolTip("清空")
        clr_btn.clicked.connect(lambda _=False, s=side: self._clear_side_audio(s))
        box.addWidget(clr_btn)

        if side == "src":
            self.play_slider_src = slider
            self.speak_src_btn = speak_btn
            self.stop_src_btn = stop_btn
            self.dl_src_btn = dl_btn
        else:
            self.play_slider_tgt = slider
            self.speak_tgt_btn = speak_btn
            self.stop_tgt_btn = stop_btn
            self.dl_tgt_btn = dl_btn
        return box

    def _clear_editor(self, editor):
        """清空文本框及全部关联状态：
        - 原文清空：文字清、导入文件状态清（导入钮变灰）、译文随之清空、
          两侧朗读音频释放（朗读钮/下载钮变灰）、导出文件钮隐藏。
        - 译文清空：文字清、译文侧音频释放（钮变灰）、导出文件钮隐藏。
        若被清一侧正在朗读，先停止朗读。"""
        # v2.3.1：文字清空与音频清空分离——本钮只清文字+导入文件，音频缓存保留
        self._preserve_audio_on_clear = True
        try:
            editor.clear()
            if editor is self.input_edit:
                self._imported_path = None
                self._imported_ext = None
                self._imported_text = None
                self._can_export_file = False
                self.output_edit.clear()   # 译文文字随之清空（音频仍保留）
        finally:
            self._preserve_audio_on_clear = False
        self._update_file_buttons()

    def _sel_or_link_range(self, editor):
        """该区当前选区范围：原生蓝选 > 高亮蓝选 > 灰色联动，都无则 None。"""
        cur = editor.textCursor()
        if cur.hasSelection():
            return (cur.selectionStart(), cur.selectionEnd())
        hl = self._hl_input if editor is self.input_edit else self._hl_output
        if hl._sel_end > hl._sel_start:
            return (hl._sel_start, hl._sel_end)
        if hl._link_end > hl._link_start:
            return (hl._link_start, hl._link_end)
        return None

    def _smart_copy(self, editor):
        """有选区(蓝/灰)只复制选中部分；无选区复制全部。"""
        from PyQt6.QtWidgets import QApplication as _QA
        r = self._sel_or_link_range(editor)
        text = editor.toPlainText()
        _QA.clipboard().setText(text[r[0]:r[1]] if r else text)
        self.status.showMessage("已复制选中部分" if r else "已复制全部文字", 2000)

    def _smart_paste(self, editor):
        """有选区(蓝/灰)只覆盖选中部分；无选区默认粘贴到末尾。"""
        from PyQt6.QtWidgets import QApplication as _QA
        from PyQt6.QtGui import QTextCursor
        clip = _QA.clipboard().text()
        if not clip:
            self.status.showMessage("剪贴板为空", 2000)
            return
        r = self._sel_or_link_range(editor)
        c = editor.textCursor()
        if r:
            c.setPosition(r[0])
            c.setPosition(r[1], QTextCursor.MoveMode.KeepAnchor)
            c.insertText(clip)
        elif editor is getattr(self, "_active_editor", None):
            # 主动区有明确光标位置：粘贴到光标处
            c.insertText(clip)
        else:
            # 从属区且无选区：默认粘贴到末尾
            c.movePosition(QTextCursor.MoveOperation.End)
            editor.setTextCursor(c)
            c.insertText(clip)

    def _panel_buttons(self, editor):
        """返回某个文本框的 粘贴/复制/删除 按钮横排。"""
        box = QHBoxLayout()
        box.setSpacing(3)
        box.setContentsMargins(0, 0, 0, 0)
        paste_btn = QPushButton(Icons.icon("paste"), "")
        paste_btn.setFixedSize(34, 34)
        paste_btn.setToolTip("粘贴")
        paste_btn.clicked.connect(lambda: self._smart_paste(editor))
        copy_btn = QPushButton(Icons.icon("copy"), "")
        copy_btn.setFixedSize(34, 34)
        copy_btn.setToolTip("复制")
        copy_btn.clicked.connect(lambda: self._smart_copy(editor))
        box.addWidget(copy_btn)
        box.addWidget(paste_btn)
        return box

    def _paste(self, editor):
        text = QApplication.clipboard().text()
        if text:
            editor.insertPlainText(text)
        self.status.showMessage("已粘贴", 2000)

    def _copy(self, editor):
        QApplication.clipboard().setText(editor.toPlainText())
        self.status.showMessage("已复制到剪贴板", 2000)

    # ---------- 状态栏 ----------
    def _build_statusbar(self):
        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)   # 去掉 Windows 右下角的灰色拖拽块
        self.setStatusBar(self.status)
        self.status.showMessage("就绪")

    # ---------- 样式 ----------
    def _chevron_path(self, color="#9aa0a6"):
        """生成一个扁平 V 形尖角号 SVG，写入临时文件，供下拉箭头使用。"""
        import tempfile, os as _os
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="8" '
               f'viewBox="0 0 12 8"><path d="M1 1.5 L6 6.5 L11 1.5" '
               f'fill="none" stroke="{color}" stroke-width="1.8" '
               f'stroke-linecap="round" stroke-linejoin="round"/></svg>')
        p = _os.path.join(tempfile.gettempdir(),
                          f"ec_chevron_{color.strip('#')}.svg")
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(svg)
        except Exception:
            return ""
        return p.replace("\\", "/")

    def _apply_style(self):
        chevron = self._chevron_path("#9aa0a6")
        chevron_hi = self._chevron_path("#4ea1ff")
        arrow_css = ""
        if chevron:
            arrow_css = (
                f"QComboBox::down-arrow {{ image:url('{chevron}'); "
                f"width:12px; height:8px; margin-right:8px; }}\n"
                f"QComboBox::down-arrow:hover {{ image:url('{chevron_hi}'); }}\n")
        _ss = ("""
            QMainWindow, QDialog, QMessageBox { background:#1e1e1e; }
            QLabel, QCheckBox { background:transparent; color:#dcdcdc; }
            QToolTip { background:#2d2d30; color:#e0e0e0; border:1px solid #4a4a4a;
                padding:2px 5px; font-size:11px; border-radius:6px; }
            QToolBar { background:#252526; border:none; padding:4px; spacing:4px; }
            QToolBar QToolButton { color:#dcdcdc; padding:6px 10px; border-radius:5px; }
            QToolBar QToolButton:hover { background:#37373d; }
            QTextEdit { background:#252526; border:1px solid #3a3a3a;
                border-radius:6px; padding:%EDITPAD%; font-size:14px; }
            QTextEdit[activeRegion="1"] { border:1px solid #4ea1ff; }
            QTextEdit[activeRegion="0"] { border:1px solid #3a3a3a; }
%SCROLLBAR%
            QComboBox, QLineEdit { background:#2d2d30; border:1px solid #3a3a3a;
                border-radius:5px; padding:5px 8px; }
            QComboBox:hover { border:1px solid #4ea1ff; }
            QComboBox QAbstractItemView { background:#2d2d30; outline:none;
                border:none;
                selection-background-color:#0e639c; selection-color:white; }
            QComboBox QAbstractItemView::item {
                padding:7px 14px; border:none; }
            QComboBox QAbstractItemView::item:selected { background:#0e639c; color:white; }
            QComboBox QAbstractItemView::item:hover { background:#0e639c; color:white; }
            QComboBox QAbstractItemView::indicator { width:0px; height:0px; }
            QComboBox::drop-down { border:none; background:transparent;
                width:24px; subcontrol-origin:padding; subcontrol-position:center right; }
            """ + arrow_css + """
            QPushButton { background:#2d2d30; border:1px solid #3a3a3a;
                border-radius:5px; padding:6px 12px; }
            QPushButton:hover { background:#37373d; border:1px solid #4ea1ff; }
            QPushButton:pressed { background:#094771; }
            QPushButton#primary { background:#0e639c; border:none; font-size:15px;
                border-radius:8px; color:white; font-weight:bold; padding:8px 40px; }
            QPushButton#primary:disabled { background:#12557f; color:#bbccdd; }
            QPushButton#primary:hover { background:#1177bb; }
            QLabel { color:#cccccc; }
            QSlider { border:none; }
            QSlider#rateSlider::sub-page:horizontal { background:#3a3a3a; border-radius:2px; }
            QSlider#rateSlider::add-page:horizontal { background:#3a3a3a; border-radius:2px; }
            QSlider::groove:horizontal { height:4px; background:#3a3a3a; border-radius:2px;
                border:none; }
            QSlider::handle:horizontal { background:#4ea1ff; width:14px; height:14px;
                margin:-5px 0; border-radius:7px; border:none; }
            QStatusBar { background:#007acc; color:white; }
            QStatusBar QLabel { background:transparent; color:white; }
            QStatusBar::item { border:none; }
            QSizeGrip { background:transparent; width:0; height:0; }
            QSplitter::handle { background:#1e1e1e; width:8px; }
        """)
        # 关键：替换必须作用于整张拼接后的样式表（此前只作用于最后一段，
        # 占位符残留导致整表解析失败被丢弃——按钮丢样式/翻译钮丢蓝色的元凶）
        _sb = self._scrollbar_css()
        _ss = _ss.replace("%SCROLLBAR%", _sb)
        _ss = _ss.replace("%EDITPAD%", "8px" if _sb == "" else "8px 20px 8px 8px")
        self.setStyleSheet(_ss)

    def _scrollbar_css(self):
        """Mac / Win11(Qt>=6.7) 用系统原生胶囊滚动条（不设任何样式）；
        Win10 及以下 / Linux / Qt过旧 用自定义细样式。"""
        import sys
        if sys.platform == "darwin":
            return ""   # mac 原生胶囊
        if sys.platform == "win32":
            try:
                if sys.getwindowsversion().build >= 22000:
                    from PyQt6.QtWidgets import QStyleFactory
                    if "windows11" in [k.lower() for k in QStyleFactory.keys()]:
                        return ""   # Win11 原生 Fluent 胶囊
            except Exception:
                pass
        return (
            "            QScrollBar:vertical { background:transparent; width:8px;"
            " margin:4px 2px 4px 0; border:none; }\n"
            "            QScrollBar::handle:vertical { background:rgba(150,150,150,140);"
            " border-radius:4px; min-height:30px; }\n"
            "            QScrollBar::handle:vertical:hover { background:rgba(190,190,190,200); }\n"
            "            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
            " height:0; background:none; border:none; }\n"
            "            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {"
            " background:transparent; }\n"
            "            QScrollBar:horizontal { height:0px; background:transparent; }")

    # ====================================================================
    #  动作
    # ====================================================================

    def open_settings(self):
        SettingsDialog(self.settings, self).exec()
        # 设置里改了默认引擎，同步到主界面下拉
        self.engine_combo.setCurrentText(
            self.settings.value("engine", ENGINE_GOOGLE))

    def swap_sides(self):
        # 朗读中交换：把卡拉OK朗读目标也对换到对面窗，避免青绿色显示在错误文字上
        was_speaking = getattr(self, "_is_speaking", False)
        speak_ed = getattr(self, "_speak_editor", None)
        # 记住交换前原文区的选区（若有），交换后继承到新原文区
        in_cur = self.input_edit.textCursor()
        out_cur = self.output_edit.textCursor()
        out_sel = (out_cur.selectionStart(), out_cur.selectionEnd()) if out_cur.hasSelection() else None

        a, b = self.input_edit.toPlainText(), self.output_edit.toPlainText()
        self.input_edit.setPlainText(b)
        self.output_edit.setPlainText(a)
        s, t = self.src_combo.currentText(), self.tgt_combo.currentText()
        if s in LANG_OPTIONS and t in LANG_OPTIONS:
            self.src_combo.setCurrentText(t)
            self.tgt_combo.setCurrentText(s)
        # 清掉旧的高亮（含可能停在错误文字上的青绿/灰条）
        self._link_guard = True
        try:
            self._hl_input.clear_all(); self._hl_output.clear_all()
        finally:
            self._link_guard = False
        # 朗读中交换：立即终止朗读 + 清空音频缓存，避免青绿字幕错位到对面
        if was_speaking:
            self.stop_speak()
        self._last_audio = None
        self._last_audio_sig = None
        self._speak_boundaries = []
        # 交换后内容已对调，触发翻译刷新译文与对齐
        if self.input_edit.toPlainText().strip():
            self._start_translate(auto=True)

    def _kill_repaint_sources(self, side):
        """文字真实变更时，掐断该侧所有高亮重画源（只擦画面会被定时器立刻画回来）：
        1) 清词边界 2) 停卡拉OK定时器 3) 停联动防抖 4) 作废过期对齐表。
        若该侧正在朗读，顺带停止朗读（文字已变，读的是旧内容）。"""
        ed = self.input_edit if side == "src" else self.output_edit
        if getattr(self, "_speak_editor", None) is ed:
            self._speak_boundaries = []
            self._karaoke_running = False
            try:
                self._karaoke_timer.stop()
            except Exception:
                pass
            try:
                self.stop_speak(clear_only=True)
            except Exception:
                pass
        self._link_timer.stop()
        self._link_pending_src = None
        self._align = None   # 文字变了，旧句对齐全部失效

    # ---------- 翻译 ----------
    def _on_input_changed(self):
        # 根治方案：rehighlight 触发的 textChanged 中文本内容并未变化，
        # 用文本比对判断是否"真实编辑"——从根上消灭所有高亮反馈环误伤。
        cur_text = self.input_edit.toPlainText()
        if cur_text == getattr(self, "_last_input_text", ""):
            return                      # 仅格式重绘，非真实变更
        self._last_input_text = cur_text
        if getattr(self, "_highlighting", False) or getattr(self, "_link_guard", False):
            return
        self._kill_repaint_sources("src")   # 掐断卡拉OK/联动重画源
        self._clear_all_highlights()
        self._update_file_buttons()
        if not getattr(self, "_preserve_audio_on_clear", False):
            self._invalidate_side_audio("src")   # 原文变了 -> 原文音频缓存失效
        if not cur_text.strip():
            self.output_edit.clear()
            self._auto_timer.stop()
            return
        self._auto_timer.start()

    def _on_output_changed(self):
        cur_text = self.output_edit.toPlainText()
        if cur_text == getattr(self, "_last_output_text", ""):
            return                      # 仅格式重绘，非真实变更
        self._last_output_text = cur_text
        if getattr(self, "_highlighting", False) or getattr(self, "_link_guard", False):
            return
        if getattr(self, "_filling_output", False):
            return   # 翻译结果回填不算用户编辑
        self._kill_repaint_sources("tgt")   # 掐断卡拉OK/联动重画源
        self._clear_all_highlights()
        self._update_file_buttons()
        if not getattr(self, "_preserve_audio_on_clear", False):
            self._invalidate_side_audio("tgt")   # 译文变了 -> 译文音频缓存失效

    def _invalidate_side_audio(self, side):
        """某侧文字变化 -> 该侧音频缓存作废，朗读钮变灰、下载钮禁用。"""
        c = self._side_cache.get(side)
        if not c:
            return
        c["bytes"] = None; c["boundaries"] = []; c["sig"] = None
        self._last_audio = None          # 同步清全局缓存，防止旧重播路径"复活"
        self._last_audio_sig = None
        c["duration"] = 0; c["position"] = 0
        # 若该侧不是正在朗读，才把按钮变灰（正在朗读的青色由播放状态管理）
        if getattr(self, "_active_side", None) != side or not getattr(self, "_is_speaking", False):
            btn = self.speak_src_btn if side == "src" else self.speak_tgt_btn
            dl = self.dl_src_btn if side == "src" else self.dl_tgt_btn
            self._set_speak_btn_active(btn, False)
            dl.setEnabled(False)

    def _clear_all_highlights(self):
        """清掉两区的蓝色选区、灰色联动、绿色卡拉OK全部高亮。"""
        if getattr(self, "_highlighting", False):
            return
        self._highlighting = True
        try:
            for hl in (self._hl_input, self._hl_output):
                hl._sel_start = hl._sel_end = 0
                hl._link_start = hl._link_end = 0
                hl._hl_start = hl._hl_end = 0
                hl.rehighlight()
        finally:
            self._highlighting = False
        self._sel_range = None
        self._sel_editor = None
        self._sel_is_link = False

    def _auto_translate(self):
        # 自动翻译：与手动相同，但失败时不弹窗（仅状态栏提示）
        self._start_translate(auto=True)

    def _on_lang_changed(self):
        """语言下拉变化 -> 强制重新翻译当前内容。"""
        if self.input_edit.toPlainText().strip():
            self.do_translate()

    def do_translate(self):
        # 手动按钮：先中断所有正在进行的翻译（网络/本地推理都先停），再开始新翻译
        self._auto_timer.stop()
        self._abort_translation()
        self._start_translate(auto=False, force=True)

    def _abort_translation(self):
        """中断当前正在进行的翻译 worker（不等待结果）。"""
        w = getattr(self, "translate_worker", None)
        if w is not None and w.isRunning():
            try:
                if hasattr(w, "cancel"):
                    w.cancel()           # 软取消（worker 内部检查点会停）
                w.requestInterruption()
            except Exception:
                pass
            # 退役到后台，避免阻塞 UI；不 join 等待
            if not hasattr(self, "_retired_tworkers"):
                self._retired_tworkers = []
            try:
                w.finished_ok.disconnect()
                w.failed.disconnect()
            except Exception:
                pass
            self._retired_tworkers.append(w)
            w.finished.connect(lambda w=w: self._retired_tworkers.remove(w)
                               if w in self._retired_tworkers else None)
        self.translate_worker = None

    def _in_file_mode(self):
        """是否处于有效的文件导入翻译模式（原文与导入内容strip后一致）。"""
        it = getattr(self, "_imported_text", None)
        return (bool(getattr(self, "_imported_path", None)) and it is not None
                and self.input_edit.toPlainText().strip() == it)

    def _start_translate(self, auto=False, force=False):
        text = self.input_edit.toPlainText().strip()
        if not text:
            if not auto:
                self.status.showMessage("请输入要翻译的文本", 3000)
            self.translate_btn.setEnabled(True)
            return
        # 特殊模式：原文仅为单个/一串符号或数字 -> 本地处理（不走引擎）
        if not self._in_file_mode():
            special = self._maybe_symbol_number(text)
            if special is not None:
                self.output_edit.setPlainText(special)
                self.status.showMessage("已按符号/数字规则转换", 3000)
                self.translate_btn.setEnabled(True)
                return
        # 上一个翻译还在跑：自动模式下稍后再试；手动(force)已在 do_translate 里中断
        if not force and self.translate_worker is not None and self.translate_worker.isRunning():
            if auto:
                self._auto_timer.start()
                return
            self._abort_translation()
        engine = self.engine_combo.currentText()
        keys = {
            "deepl": self.settings.value("deepl_key", ""),
            "google_api": self.settings.value("google_api_key", ""),
            "deepseek": self.settings.value("deepseek_key", ""),
            "hunyuan": self.settings.value("hunyuan_key", ""),
            "openai": self.settings.value("openai_key", ""),
            "gemini": self.settings.value("gemini_key", ""),
            "claude": self.settings.value("claude_key", ""),
            "glm": self.settings.value("glm_key", ""),
            "ernie": self.settings.value("ernie_key", ""),
            "doubao": self.settings.value("doubao_key", ""),
            "qwen": self.settings.value("qwen_key", ""),
            "kimi": self.settings.value("kimi_key", ""),
        }
        # LLM 引擎且开启了多风格开关时，输出多种译法；
        # 仅在"有效的文件导入模式"(原文与导入内容一致)下才禁用多风格——
        # 之前只看 _imported_path 是否为 None，导入过一次后残留路径会永久禁掉多风格(bug)。
        multi = (engine in LLM_ENGINE_SET and
                 self.settings.value("multi_style", "true") == "true" and
                 not self._in_file_mode())
        self._current_auto = auto
        self.translate_btn.setEnabled(False)
        # 按钮文字始终不变（避免闪动），状态提示放到底部状态栏
        self.status.showMessage(f"正在翻译（{engine}）…")

        self.translate_worker = TranslateWorker(
            text, self.src_combo.currentText(), self.tgt_combo.currentText(),
            engine, keys, multi_style=multi)
        self.translate_worker.finished_ok.connect(self.on_translate_ok)
        self.translate_worker.failed.connect(self.on_translate_fail)
        self.translate_worker.start()

    def _maybe_symbol_number(self, text):
        """若原文仅为单个符号/数字，或符号数字混合串，返回本地转换结果；否则 None。
        纯数字给『逐位拼读』+『整数读法』两种；目标语种按 tgt 决定中/英。"""
        import re as _re
        # 仅含数字、常见符号、空白才进入此模式（不含字母/汉字）
        if not text or _re.search(r'[A-Za-z\u4e00-\u9fff]', text):
            return None
        if not _re.fullmatch(r'[\d\s\.\,\-\+\*/=%\$#@!\?\(\)\[\]{}:;~`\^&|<>，。！？；：（）]+', text):
            return None
        tgt = self._resolve_tgt_lang()
        # 修复：下拉项是 "English"，旧代码只比对 "英语" 永不命中，导致强制英文失效
        to_en = tgt in ("英语", "English", "英文")
        # 纯数字（可带空格）
        num = _re.sub(r'\s+', '', text)
        if _re.fullmatch(r'\d+(\.\d+)?', num):
            results = []
            # 逐位拼读（小数点读 point/点）
            per = [("point" if to_en else "点") if d == '.'
                   else (_DIGIT_EN[d] if to_en else _DIGIT_ZH[d]) for d in num]
            results.append(("Per-digit" if to_en else "逐位拼读", " ".join(per)))
            # 数学读法（整数与小数都支持）
            try:
                if '.' in num:
                    if to_en:
                        from num2words import num2words
                        whole = num2words(float(num))
                    else:
                        import cn2an
                        whole = cn2an.an2cn(num)
                else:
                    whole = self._num_to_words(int(num), to_en)
                results.append(("As a number" if to_en else "数学读法", whole))
            except Exception:
                pass
            sep = ": " if to_en else "："
            return "\n".join(f"{label}{sep}{val}" for label, val in results)
        # 符号/混合串：逐字符映射为名称
        mapped = []
        for ch in text:
            if ch.isspace():
                mapped.append(ch); continue
            if ch.isdigit():
                mapped.append((_DIGIT_EN if to_en else _DIGIT_ZH)[ch])
            else:
                mapped.append((_SYM_EN if to_en else _SYM_ZH).get(ch, ch))
        return " ".join(m for m in mapped if m.strip())

    def _resolve_tgt_lang(self):
        t = self.tgt_combo.currentText()
        if t == "自动检测":
            # 原文是数字/符号，默认中文输入 -> 英文；否则中文
            return "英语"
        return t

    def _num_to_words(self, n, to_en):
        if to_en:
            try:
                from num2words import num2words
                return num2words(n)
            except Exception:
                return str(n)
        else:
            try:
                import cn2an
                return cn2an.an2cn(str(n))
            except Exception:
                return str(n)

    def on_translate_ok(self, out):
        self._filling_output = True
        try:
            self.output_edit.setPlainText(out)
        finally:
            self._filling_output = False
        self._reset_translate_btn()
        self.status.showMessage("翻译完成", 3000)
        self._update_file_buttons()
        # 建立"原文句 <-> 译文句"对应关系，供选区联动精确定位
        try:
            src = self.input_edit.toPlainText()
            self._build_alignment(src, out)
            _add_history(src, out, self.engine_combo.currentText())
        except Exception as e:
            _log_error(f"记录历史/对齐失败: {e}")

    def _build_alignment(self, src, tgt):
        """把原文、译文各自按句切分，建立句级对应（按顺序一一对应）。
        存成 [(src_a,src_b,tgt_a,tgt_b), ...]，选区联动时据此定位。"""
        src_segs = _sentence_spans(src)
        tgt_segs = _sentence_spans(tgt)
        self._align = []
        n = max(len(src_segs), 1)
        m = len(tgt_segs)
        for i, (sa, sb) in enumerate(src_segs):
            # 按比例把第 i 个原文句映射到对应的译文句索引
            if m == 0:
                break
            j = int(round(i / max(1, len(src_segs) - 1) * (m - 1))) if len(src_segs) > 1 else 0
            ta, tb = tgt_segs[min(j, m - 1)]
            self._align.append((sa, sb, ta, tb))

    def on_translate_fail(self, msg):
        self._reset_translate_btn()
        self.status.showMessage("翻译失败", 3000)
        _log_error(f"翻译失败 [{self.engine_combo.currentText()}]: {msg}")
        # 自动翻译失败不打扰；手动翻译才弹窗
        if not getattr(self, "_current_auto", False):
            QMessageBox.warning(self, "翻译失败", msg)

    def _reset_translate_btn(self):
        self.translate_btn.setEnabled(True)
        # 文字始终保持"翻译"不变（不再改文案，避免闪动）

    def _load_prev_source(self):
        """循环载入历史中的所有原文（每点一次往前一条，到头回到最新）。"""
        items = _load_history()
        if not items:
            self.status.showMessage("暂无历史记录", 2500)
            return
        # 维护一个游标，在所有历史原文间循环
        srcs = [it.get("src", "") for it in items if it.get("src", "").strip()]
        if not srcs:
            self.status.showMessage("暂无历史原文", 2500)
            return
        idx = getattr(self, "_prev_src_idx", None)
        cur = self.input_edit.toPlainText().strip()
        if idx is None:
            # 首次：从最新一条开始；若当前正是最新，则跳到上一条
            idx = len(srcs) - 1
            if srcs[idx].strip() == cur and len(srcs) > 1:
                idx -= 1
        else:
            idx -= 1
            if idx < 0:
                idx = len(srcs) - 1   # 循环回最新
        self._prev_src_idx = idx
        self.input_edit.setPlainText(srcs[idx])
        self.status.showMessage(f"已载入历史原文 {idx+1}/{len(srcs)}", 2500)

    def _load_next_source(self):
        """与『上一条』相反方向循环载入历史原文。"""
        items = _load_history()
        srcs = [it.get("src", "") for it in items if it.get("src", "").strip()]
        if not srcs:
            self.status.showMessage("暂无历史原文", 2500)
            return
        idx = getattr(self, "_prev_src_idx", None)
        if idx is None:
            idx = 0
        else:
            idx += 1
            if idx >= len(srcs):
                idx = 0   # 循环回最早
        self._prev_src_idx = idx
        self.input_edit.setPlainText(srcs[idx])
        self.status.showMessage(f"已载入历史原文 {idx+1}/{len(srcs)}", 2500)

    def _open_history_dialog(self):
        items = _load_history()
        if not items:
            self.status.showMessage("暂无历史记录", 2500)
            return
        dlg = HistoryDialog(items, self)
        if dlg.exec() and dlg.chosen is not None:
            src = dlg.chosen.get("src", "")
            self.input_edit.setPlainText(src)
            # 载入后开始翻译，并记为新记录
            self._start_translate(auto=False)

    # ---------- 朗读 ----------
    def _toggle_speak(self, editor):
        """开始 / 暂停 / 继续 三态切换。跨侧朗读时，先暂停另一侧（不停止）。
        关键：若该区有"新的选区"（与当前朗读内容不同），视为新的朗读请求，
        优先按选区重新朗读——否则三态切换会把选区朗读吃掉（v2.1.2 引入的 bug）。"""
        if self.player is None:
            self.status.showMessage("音频后端不可用，无法播放", 3000)
            return
        state = self.player.playbackState()
        # 新选区优先：用户选了一段文字再点朗读 -> 停掉旧音频，朗读选区
        cur = editor.textCursor()
        if cur.hasSelection():
            new_range = (cur.selectionStart(), cur.selectionEnd())
            if (self._speak_editor is not editor or
                    getattr(self, "_sel_range", None) != new_range):
                if state != QMediaPlayer.PlaybackState.StoppedState:
                    self.stop_speak(clear_only=True)
                self.do_speak(editor)
                return
        # 正在播放当前栏 -> 暂停（把位置记入该侧缓存，供跨侧回来续播）
        if (self._speak_editor is editor and
                state == QMediaPlayer.PlaybackState.PlayingState):
            self._side_cache[self._active_side]["position"] = self.player.position()
            self.player.pause()
            return
        # 已暂停当前栏 -> 继续（同侧续播不需要缓存位置，清掉防止以后误回跳）
        if (self._speak_editor is editor and
                state == QMediaPlayer.PlaybackState.PausedState):
            self._side_cache[self._active_side]["position"] = 0
            self.player.play()
            return
        # 点了另一侧：若当前有一侧在朗读，先把它暂停在当前位置（按钮保持青色→继续朗读）
        if (self._speak_editor is not None and self._speak_editor is not editor and
                state == QMediaPlayer.PlaybackState.PlayingState):
            self._pause_other_side()
        # 开始朗读这一栏
        self.do_speak(editor)

    def _pause_other_side(self):
        """把当前正在朗读的一侧暂停（保留进度与青色按钮，显示继续朗读态）。"""
        other = self._speak_editor
        if other is None or self.player is None:
            return
        # 记住该侧的暂停位置与音频缓存，便于以后继续
        pos = self.player.position()
        _oside = "src" if other is self.input_edit else "tgt"
        self._side_cache[_oside]["position"] = pos   # 存进该侧缓存，重播时从此处续
        self._paused_side_editor = other
        self._paused_side_pos = pos
        # 暂停播放器（会触发 on_play_state 把该侧按钮设为『继续朗读』青色）
        self.player.pause()
        # 该侧按钮强制设成青色继续态（喇叭图标 + 青底）
        btn = self.speak_src_btn if other is self.input_edit else self.speak_tgt_btn
        self._set_speak_btn_active(btn, True, icon="speak")
        btn.setToolTip("继续朗读")

    def do_speak(self, editor, from_pos_ratio=None):
        if from_pos_ratio is None:
            self._freeze_slider = False   # 全新朗读不冻结
        # 切换"当前活动侧"别名（进度条/下载按钮指向该侧）
        if editor is self.input_edit:
            self._active_side = "src"
            self.play_slider = self.play_slider_src
            self.download_audio_btn = self.dl_src_btn
        else:
            self._active_side = "tgt"
            self.play_slider = self.play_slider_tgt
            self.download_audio_btn = self.dl_tgt_btn
        # 若有选中文字，只读选中部分；否则看是否有灰色联动区间；再否则读全部
        cursor = editor.textCursor()
        hl = self._hl_input if editor is self.input_edit else self._hl_output
        link_has = hl._link_end > hl._link_start
        if (from_pos_ratio is not None and
                getattr(self, "_sel_editor", None) is editor and
                getattr(self, "_sel_range", None)):
            # 变更嗓音/引擎重读：沿用原选区。此时原生选区早已转为高亮，
            # 重新推导会误判成"读全文"并把蓝色选区清掉（#2 根因之一）
            _a, _b = self._sel_range
            full = editor.toPlainText()
            text = full[_a:_b].replace("\u2029", "\n").strip()
            char_offset = _a
        elif cursor.hasSelection():
            text = cursor.selectedText().replace("\u2029", "\n").strip()
            char_offset = cursor.selectionStart()
            self._sel_range = (cursor.selectionStart(), cursor.selectionEnd())
            self._sel_editor = editor
            self._sel_is_link = False    # 用户主动选区 -> 蓝色
            _c = editor.textCursor()
            _c.clearSelection()
            editor.setTextCursor(_c)
        elif link_has:
            # 灰色联动选区也可朗读（与主动选区同等效果），但保持灰色不变蓝
            full = editor.toPlainText()
            char_offset = hl._link_start
            text = full[hl._link_start:hl._link_end].strip()
            self._sel_range = (hl._link_start, hl._link_end)
            self._sel_editor = editor
            self._sel_is_link = True     # 灰色联动区 -> 保持灰色
        else:
            text = editor.toPlainText().strip()
            char_offset = 0
            self._sel_range = None
            self._sel_editor = None
            self._sel_is_link = False
        if not text:
            self.status.showMessage("没有可朗读的文本", 3000)
            return
        # 立即铺好选区底色（蓝/灰），让合成期间界面不变、选区保持可见
        self._setup_selection_highlight()
        # 计算本次朗读的"签名"：文本+嗓音+语速+选区。若与上次已合成的一致，
        # 且有缓存音频，则直接重播，不重新生成（像播放音频文件一样）。
        if _text_is_chinese(text):
            _vname_sig = self.zh_voice_combo.currentText()
        else:
            _vname_sig = self.en_voice_combo.currentText()
        sig = (id(editor), text, _vname_sig, self.rate_slider.value(), self._sel_range)
        self._last_lang = "ZH" if _text_is_chinese(text) else "EN"   # 重播路径也要设，供嗓音切换判断
        _sc = self._side_cache[self._active_side]
        if (from_pos_ratio is None and _sc.get("bytes")
                and _sc.get("sig") == sig):
            # 该侧缓存命中 -> 直接重播，不重新生成（缓存被清空后此路必不命中）
            self._speak_boundaries = _sc.get("boundaries") or []
            self._speak_editor = editor
            self._last_speak_editor = editor
            self._is_speaking = True
            self._pending_seek_ratio = None
            self.stop_speak(clear_only=True)
            self._setup_selection_highlight()
            QTimer.singleShot(600, lambda: setattr(self, "_freeze_slider", False))
            self.status.showMessage("播放中…", 2000)
            _resume = _sc.get("position") or 0
            _sc["position"] = 0            # 用掉即清
            self._play_bytes(_sc["bytes"])
            if _resume > 0:
                # 缓存里存过暂停位置 -> 续播而不是从头（媒体加载后再定位）
                QTimer.singleShot(150, lambda pms=_resume: self.player.setPosition(pms))
            return
        self._pending_sig = sig
        # 变更重读时保留进度条位置，不跳回头
        keep_progress = from_pos_ratio is not None
        self.stop_speak(clear_only=True, keep_slider=keep_progress)
        self._retire_worker()   # 安全退役上一个 worker，避免线程未结束就析构（崩溃根因）
        self._speak_editor = editor
        self._last_speak_editor = editor
        self._is_speaking = True
        self._pending_seek_ratio = from_pos_ratio
        # 按文本语种选嗓音
        if _text_is_chinese(text):
            voice_name = self.zh_voice_combo.currentText()
            voice_spec = ZH_VOICES.get(voice_name, next(iter(ZH_VOICES.values())))
            self._last_lang = "ZH"
        else:
            voice_name = self.en_voice_combo.currentText()
            voice_spec = EN_VOICES.get(voice_name, next(iter(EN_VOICES.values())))
            self._last_lang = "EN"
        self._last_voice_name = voice_name
        rate = self.rate_slider.value()
        self._speak_rate = rate
        is_kokoro = voice_spec.get("engine") == "kokoro"
        self._synth_in_progress = True
        # 文字提示立即显示并持续到合成结束（不被其它状态信息冲掉）
        self._show_synth_busy(bar=False)
        # 进度条延迟 1.2s 再出（短合成不闪进度条）
        QTimer.singleShot(1200, self._show_synth_busy)

        self.tts_worker = TTSWorker(text, voice_spec, rate, char_offset)
        self.tts_worker.finished_ok.connect(self.on_tts_ok)
        self.tts_worker.failed.connect(self.on_tts_fail)
        self.tts_worker.start()

    def _show_synth_busy(self, bar=True):
        """合成时：文字『正在生成音频…』走左侧消息区(showMessage)，与『翻译完成』等
        交替占用同一位置、不重叠；进度条单独放右侧永久区（药丸形、细轮廓、透明外围）。"""
        if not getattr(self, "_synth_in_progress", False):
            return
        # 文字：用 showMessage 进入左侧消息区（同一位置，自动与其它消息互相覆盖）
        self.status.showMessage("正在生成音频…")
        from PyQt6.QtWidgets import QProgressBar, QWidget as _QW, QHBoxLayout as _QH
        if getattr(self, "_synth_holder", None) is None:
            holder = _QW()
            hl = _QH(holder)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(0)
            pb = PillBusyBar()
            hl.addWidget(pb)
            spacer = _QW()
            hl.addWidget(spacer)
            self._synth_holder = holder
            self._synth_bar = pb
            self._synth_spacer = spacer
            self.status.addPermanentWidget(holder)
        self._synth_holder.show()
        if not bar:
            self._synth_bar.hide()
            self._synth_spacer.setFixedWidth(max(20, int(self.width() * 0.05)))
            return
        self._synth_bar.setFixedWidth(max(300, int(self.width() * 0.42)))
        self._synth_spacer.setFixedWidth(max(20, int(self.width() * 0.05)))
        self._synth_bar.show()

    def _hide_synth_busy(self):
        self._synth_in_progress = False
        holder = getattr(self, "_synth_holder", None)
        if holder is not None:
            holder.hide()
        # 清掉左侧"正在生成音频"消息（让其它状态正常显示）
        if self.status.currentMessage().startswith("正在生成音频"):
            self.status.clearMessage()

    def _next_audio_filename(self):
        """生成 EC_<语种>_<嗓音>_<日期>_<时间>.<ext>，例如 EC_ZH_XiaoXiao_2026-06-26_210825.mp3。
        Kokoro 离线为 wav，edge 在线为 mp3。保存目录优先用上次用户选过的目录。"""
        import datetime
        save_dir = self.settings.value("last_audio_dir", "")
        if not save_dir or not os.path.isdir(save_dir):
            save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.isdir(save_dir):
                save_dir = os.path.expanduser("~")
        lang = getattr(self, "_last_lang", "EN")
        vname = getattr(self, "_last_voice_name", "")
        short = VOICE_SHORTNAME.get(vname, "Voice")
        data = getattr(self, "_last_audio", b"")
        # 默认扩展名优先用上次选择的格式，否则按源音频类型
        last_fmt = self.settings.value("last_audio_fmt", "")
        if last_fmt in ("wav", "mp3"):
            ext = last_fmt
        else:
            ext = "wav" if data[:4] == b"RIFF" else "mp3"
        now = datetime.datetime.now()
        stamp = now.strftime("%Y-%m-%d %H%M%S")
        name = f"EC {lang} {short} {stamp}.{ext}"
        return os.path.join(save_dir, name)

    def _clear_side_audio(self, side):
        """仅清空该侧朗读音频缓存：缓存释放，朗读钮青->灰，下载钮失效。不动文字。"""
        ed = self.input_edit if side == "src" else self.output_edit
        if getattr(self, "_speak_editor", None) is ed:
            try:
                self.stop_speak(clear_only=True)
            except Exception:
                pass
        self._invalidate_side_audio(side)
        self.status.showMessage(("原文" if side == "src" else "译文") + "朗读音频已清空", 2500)

    def _download_audio(self, side=None):
        if side is None:
            side = getattr(self, "_active_side", "src")
        # 从该侧独立缓存取音频；无则提示（钮为灰时不应能点，双保险）
        data = self._side_cache.get(side, {}).get("bytes") or getattr(self, "_last_audio", None)
        if not data:
            self.status.showMessage("该侧没有可下载的音频（朗读钮为灰色时不可下载）", 3000)
            return
        from PyQt6.QtWidgets import QFileDialog
        default_path = self._next_audio_filename()
        # 让用户在保存对话框里选 wav 或 mp3；记住上次选择作为默认
        wav_filt = "WAV 无损 (*.wav)"
        mp3_filt = "MP3 压缩 (*.mp3)"
        last_fmt = self.settings.value("last_audio_fmt", "")
        if last_fmt == "mp3":
            filters = f"{mp3_filt};;{wav_filt}"
        elif last_fmt == "wav":
            filters = f"{wav_filt};;{mp3_filt}"
        else:
            is_wav_src = data[:4] == b"RIFF"
            filters = f"{wav_filt};;{mp3_filt}" if is_wav_src else f"{mp3_filt};;{wav_filt}"
        is_wav_src = data[:4] == b"RIFF"
        path, sel_filt = QFileDialog.getSaveFileName(
            self, "保存朗读音频", default_path, filters)
        if not path:
            return
        want_mp3 = "mp3" in sel_filt.lower()
        ext = ".mp3" if want_mp3 else ".wav"
        self.settings.setValue("last_audio_fmt", "mp3" if want_mp3 else "wav")  # 记住选择
        # 去掉已有扩展名再补正确的
        base, _e = os.path.splitext(path)
        path = base + ext
        try:
            out = data
            if want_mp3 and is_wav_src:
                out = self._wav_bytes_to_mp3(data)        # Kokoro wav -> mp3
            elif (not want_mp3) and (not is_wav_src):
                # edge 是 mp3，用户却要 wav：解码为 wav
                out = self._mp3_bytes_to_wav(data)
            with open(path, "wb") as f:
                f.write(out)
            self.settings.setValue("last_audio_dir", os.path.dirname(path))
            self.status.showMessage(f"已保存：{path}", 4000)
        except Exception as e:
            QMessageBox.warning(self, "保存失败",
                                f"{e}\n（格式转换可能缺少依赖，可改存另一种格式）")

    def _wav_bytes_to_mp3(self, wav_bytes):
        """WAV 字节 -> MP3 字节。优先用 lameenc，失败则提示。"""
        import io, wave
        with wave.open(io.BytesIO(wav_bytes), "rb") as w:
            ch = w.getnchannels(); sr = w.getframerate()
            pcm = w.readframes(w.getnframes())
        try:
            import lameenc
        except Exception:
            raise RuntimeError("缺少 mp3 编码库 lameenc，无法转 mp3")
        enc = lameenc.Encoder()
        enc.set_bit_rate(192)
        enc.set_in_sample_rate(sr)
        enc.set_channels(ch)
        enc.set_quality(2)
        mp3 = enc.encode(pcm) + enc.flush()
        return bytes(mp3)

    def _mp3_bytes_to_wav(self, mp3_bytes):
        """MP3 字节 -> WAV 字节。用 soundfile/miniaudio 之一解码。"""
        import io
        try:
            import soundfile as sf
            import numpy as np
            data, sr = sf.read(io.BytesIO(mp3_bytes))
            buf = io.BytesIO()
            sf.write(buf, data, sr, format="WAV", subtype="PCM_16")
            return buf.getvalue()
        except Exception:
            raise RuntimeError("无法将 mp3 解码为 wav（缺少解码库）")

    def _retire_worker(self):
        """安全停止并回收正在运行的 TTSWorker，防止线程未结束就被销毁导致崩溃。"""
        w = getattr(self, "tts_worker", None)
        if w is not None and w.isRunning():
            try:
                w.cancel()
                w.finished_ok.disconnect()
                w.failed.disconnect()
            except Exception:
                pass
            # 保留引用直到线程真正结束，由 finished 信号触发 deleteLater
            if not hasattr(self, "_retired_workers"):
                self._retired_workers = []
            self._retired_workers.append(w)
            w.finished.connect(lambda w=w: self._cleanup_worker(w))
            w.quit()
        self.tts_worker = None

    def _cleanup_worker(self, w):
        try:
            w.wait(2000)
        except Exception:
            pass
        if hasattr(self, "_retired_workers") and w in self._retired_workers:
            self._retired_workers.remove(w)
        w.deleteLater()

    def on_tts_ok(self, audio_bytes, boundaries):
        self._hide_synth_busy()
        self._speak_boundaries = boundaries
        self._last_audio = audio_bytes
        self._last_audio_sig = getattr(self, "_pending_sig", None)
        # 存入当前侧的独立缓存（该侧从此"音频在内存"，朗读钮青色，可下载）
        side = getattr(self, "_active_side", "src")
        c = self._side_cache[side]
        c["bytes"] = audio_bytes
        c["boundaries"] = boundaries
        c["sig"] = self._last_audio_sig
        self.download_audio_btn.setEnabled(bool(audio_bytes))
        # 该侧朗读钮标记为"有音频"（青色）——即使还没开始播放也代表可下载
        self._mark_side_has_audio(side, bool(audio_bytes))
        if self.player is None:
            self.status.showMessage("音频后端不可用，无法播放", 3000)
            return
        self._setup_selection_highlight()
        self._play_bytes(audio_bytes)
        if not boundaries:
            QTimer.singleShot(300, self._build_fallback_boundaries)
        if getattr(self, "_pending_seek_ratio", None):
            r = self._pending_seek_ratio
            self._pending_seek_ratio = None
            QTimer.singleShot(150, lambda: self._seek_ratio(r))
        QTimer.singleShot(600, lambda: setattr(self, "_freeze_slider", False))
        self.status.showMessage("播放中…", 2000)

    def _mark_side_has_audio(self, side, has):
        """标记某侧是否有音频在内存：有->朗读钮青色(可下载)，无->灰色。"""
        btn = self.speak_src_btn if side == "src" else self.speak_tgt_btn
        dl = self.dl_src_btn if side == "src" else self.dl_tgt_btn
        if has:
            self._set_speak_btn_active(btn, True, icon="speak")
        # 下载钮可用性跟随
        dl.setEnabled(has)

    def _build_fallback_boundaries(self):
        """没有 WordBoundary 时，按字符/词在总时长上均匀估算高亮时间表。
        若朗读的是选区，只在选区范围内估算（不能从全文开头算）。"""
        if self._speak_boundaries:   # 已经有真实边界
            return
        editor = self._speak_editor
        if editor is None:
            return
        dur = getattr(self, "_play_duration", 0) or (self.player.duration() if self.player else 0)
        if dur <= 0:
            return
        # 朗读选区时，只取选区文本与其在文档中的偏移
        sel = getattr(self, "_sel_range", None)
        if sel and getattr(self, "_sel_editor", None) is editor:
            base_off = sel[0]
            full = editor.toPlainText()
            text = full[sel[0]:sel[1]]
        else:
            base_off = 0
            text = editor.toPlainText()
        if not text.strip():
            return
        import re
        if _text_is_chinese(text):
            tokens = [(m.start(), m.end()) for m in re.finditer(r'\S', text)]
        else:
            tokens = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
        if not tokens:
            return
        n = len(tokens)
        bounds = []
        for i, (s, e) in enumerate(tokens):
            off = dur * i / n
            bounds.append((base_off + s, base_off + e, off, dur / n))
        self._speak_boundaries = bounds

    def _play_bytes(self, audio_bytes):
        # 用 QBuffer 把内存中的音频喂给 QMediaPlayer；按头部判断格式提示
        self._audio_qba = QByteArray(audio_bytes)
        self._audio_buffer = QBuffer(self)
        self._audio_buffer.setData(self._audio_qba)
        self._audio_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        hint = "audio.wav" if audio_bytes[:4] == b"RIFF" else "audio.mp3"
        self.player.setSourceDevice(self._audio_buffer, QUrl(hint))
        self.player.play()
        # 纯墙上时钟驱动高亮：一旦开始播放，时钟自走，完全不依赖 player 状态/位置
        self._karaoke_clock = QElapsedTimer()
        self._karaoke_clock.start()
        self._karaoke_paused_at = 0
        self._karaoke_running = True
        self._karaoke_timer.start()

    def on_tts_fail(self, msg):
        self._hide_synth_busy()
        self._is_speaking = False
        self.tts_worker = None
        self._reset_speak_buttons()
        self.status.showMessage("朗读失败（可改用『-线上联网』嗓音）", 6000)
        _log_error(f"朗读失败: {msg}")

    # ---- 播放器信号 ----
    def _on_play_duration(self, dur):
        self._play_duration = dur

    def _on_play_position(self, pos):
        # 更新进度条（仅用于进度条显示）
        dur = getattr(self, "_play_duration", 0) or self.player.duration()
        if dur > 0 and not self._seeking and not getattr(self, "_freeze_slider", False):
            self.play_slider.setValue(int(pos / dur * 1000))

    def _karaoke_elapsed_ms(self):
        """当前已播放毫秒。优先用 player.position()（与音频精确同步），
        若它不推进（某些 macOS 情况）则回退到墙上时钟。"""
        # 1) 优先播放器真实位置
        if self.player is not None:
            try:
                pos = self.player.position()
            except Exception:
                pos = 0
            if pos > 0:
                self._pos_seen = True
                return pos
        # 2) 回退：墙上时钟
        base = getattr(self, "_karaoke_paused_at", 0)
        clk = getattr(self, "_karaoke_clock", None)
        if clk is not None and getattr(self, "_karaoke_running", False):
            return base + clk.elapsed()
        return base

    def _karaoke_tick(self):
        """定时驱动逐词高亮——纯靠墙上时钟，不检查 playbackState。"""
        if self._speak_editor is None or not self._speak_boundaries:
            return
        if not getattr(self, "_karaoke_running", False):
            return
        self._update_karaoke(self._karaoke_elapsed_ms())

    def _on_play_state(self, state):
        # 仅负责按钮文案与时钟暂停/恢复；高亮由墙上时钟独立驱动
        editor = self._speak_editor
        if state == QMediaPlayer.PlaybackState.PausedState:
            # 暂停：累计已播放时间，停表
            self._karaoke_paused_at = self._karaoke_elapsed_ms()
            self._karaoke_running = False
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            # 播放/继续：重启表（基准是累计值）
            if getattr(self, "_karaoke_clock", None) is None:
                self._karaoke_clock = QElapsedTimer()
            self._karaoke_clock.start()
            self._karaoke_running = True
            if not self._karaoke_timer.isActive():
                self._karaoke_timer.start()
        else:  # Stopped
            self._karaoke_running = False
            self._karaoke_timer.stop()
        # 按钮状态（纯图标）：播放/暂停切换图标 + 青绿背景 + 悬停提示三态
        self._reset_speak_buttons()
        if editor is not None:
            btn = self.speak_src_btn if editor is self.input_edit else self.speak_tgt_btn
            name = "原文" if editor is self.input_edit else "译文"
            if state == QMediaPlayer.PlaybackState.PlayingState:
                self._set_speak_btn_active(btn, True, icon="pause")
                btn.setToolTip("暂停朗读")
            elif state == QMediaPlayer.PlaybackState.PausedState:
                self._set_speak_btn_active(btn, True, icon="speak")
                btn.setToolTip("继续朗读")
            else:
                # 停止态颜色由 _reset_speak_buttons 按缓存决定，这里只更新提示
                btn.setToolTip(f"朗读{name}")
        if state == QMediaPlayer.PlaybackState.StoppedState:
            # 为重读而主动 stop（preserve 期间）不是自然播完：跳过收尾闪亮与清绿，
            # 否则 250ms 后 _finish_karaoke 会把要保持的卡拉OK/选区清掉（#2 根因之二）
            if getattr(self, "_preserve_play_ui", False):
                return
            # 播放结束：读完所有词都点亮一瞬，然后清除绿色已读；
            # 若之前是朗读选区，恢复成普通的原生蓝色选区（可正常点击取消/重选）
            if self._speak_editor is not None and self._speak_boundaries:
                last_end = self._speak_boundaries[-1][1]
                first_start = self._speak_boundaries[0][0]
                self._apply_karaoke_selection(first_start, last_end)
                QTimer.singleShot(250, self._finish_karaoke)
            else:
                self._finish_karaoke()

    def _set_speak_btn_active(self, btn, active, icon="speak"):
        """active=True 青绿背景；icon 决定显示喇叭(speak)还是暂停(pause)图标。
        图标在最后设置，不再被背景样式覆盖（修复之前暂停图标看不到的 bug）。"""
        if active:
            btn.setStyleSheet(
                "QPushButton{background:#5aa8b0; color:#0e2024; border:1px solid #5aa8b0; border-radius:6px;}"
                "QPushButton:hover{background:#66b8c0;}")
            btn.setIcon(Icons.icon(icon, "#0e2024"))   # 深色图标（按状态：喇叭或暂停）
        else:
            btn.setStyleSheet("")
            btn.setIcon(Icons.icon("speak"))           # 恢复浅色喇叭图标

    def _finish_karaoke(self):
        """朗读彻底结束：清绿色已读高亮。
        - 若读的是用户主动选区：恢复为普通原生蓝色选区（点击即可取消/重选）。
        - 若读的是灰色联动区：恢复灰色联动高亮（不消失，也不变蓝）。"""
        self._hl_input.clear_range()
        self._hl_output.clear_range()
        sel = getattr(self, "_sel_range", None)
        ed = getattr(self, "_sel_editor", None)
        is_link = getattr(self, "_sel_is_link", False)
        if sel and ed is not None:
            hl = self._hl_input if ed is self.input_edit else self._hl_output
            if is_link:
                # 恢复灰色联动高亮
                self._link_guard = True
                try:
                    hl.clear_selection()
                    hl.set_link(sel[0], sel[1])
                finally:
                    self._link_guard = False
            else:
                # 用原生选区还原蓝色（普通选区，可正常取消/重选）
                hl.clear_selection()
                from PyQt6.QtGui import QTextCursor
                c = ed.textCursor()
                c.setPosition(sel[0])
                c.setPosition(sel[1], QTextCursor.MoveMode.KeepAnchor)
                ed.setTextCursor(c)
        self._sel_range = None
        self._sel_editor = None
        self._sel_is_link = False

    def _reset_speak_buttons(self):
        # 颜色语义原则：该侧缓存有音频=青色(可下载)，无=灰。播放结束不改此语义。
        for _side, _btn in (("src", self.speak_src_btn), ("tgt", self.speak_tgt_btn)):
            _has = bool(self._side_cache.get(_side, {}).get("bytes"))
            self._set_speak_btn_active(_btn, _has, icon="speak")

    def _clear_selection_pair(self):
        """点主动区：保持主动权，清掉两侧联动选区对（蓝/灰高亮），不碰卡拉OK绿色。"""
        self._link_guard = True
        try:
            for hl in (self._hl_input, self._hl_output):
                hl._sel_start = hl._sel_end = 0
                hl._link_start = hl._link_end = 0
                hl.rehighlight()
        finally:
            self._link_guard = False
        self._link_timer.stop()
        self._link_pending_src = None

    def _activate_region(self, editor):
        """统一的主动/从属切换：点击从属区任何位置 -> 它变主动区（蓝框），
        其灰色联动选区变蓝色；原主动区变从属（灰框），其蓝色选区变灰色联动。
        选区内容两侧都保留，只是蓝/灰跟着主动权走。"""
        from PyQt6.QtGui import QTextCursor
        self._link_timer.stop()           # 防止挂起的联动稍后覆盖本次切换结果
        self._link_pending_src = None
        old = getattr(self, "_active_editor", None)
        self._set_active_editor(editor)   # 蓝框跳到新主动区，旧区灰框
        new_hl = self._hl_input if editor is self.input_edit else self._hl_output
        old_hl = self._hl_output if editor is self.input_edit else self._hl_input
        self._link_guard = True
        try:
            # 1) 原主动区：蓝色选区（原生或高亮）-> 灰色联动
            if old is not None and old is not editor:
                old_cur = old.textCursor()
                if old_cur.hasSelection():
                    s0, s1 = old_cur.selectionStart(), old_cur.selectionEnd()
                    c = old.textCursor(); c.clearSelection(); old.setTextCursor(c)
                    old_hl.set_link(s0, s1)
                elif old_hl._sel_end > old_hl._sel_start:
                    old_hl.set_link(old_hl._sel_start, old_hl._sel_end)
                    old_hl._sel_start = old_hl._sel_end = 0
                    old_hl.rehighlight()
            # 2) 新主动区：灰色联动 -> 蓝色高亮选区
            if new_hl._link_end > new_hl._link_start:
                a, b = new_hl._link_start, new_hl._link_end
                new_hl._link_start = new_hl._link_end = 0
                new_hl.set_selection(a, b)
        finally:
            self._link_guard = False

    def _on_selection_changed(self, editor):
        """任一区选择文字 -> 该区成为『主动区』(蓝框+蓝底)，另一区为『从属区』，
        用句对应关系把选区映射到从属区并铺灰色底。双向均可。"""
        if self._link_guard:
            return
        cur = editor.textCursor()
        if cur.hasSelection():
            # 该区成为主动区
            self._set_active_editor(editor)
            self._link_pending_src = editor
            self._link_timer.start()
        else:
            # 选区被清掉：不再顺手清两侧联动（会误伤切换刚画好的灰条）；
            # 联动选区对的清除统一由点击主动区(_clear_selection_pair)负责
            pass

    def _set_active_editor(self, editor):
        """切换主动区：蓝色边框给主动区，从属区去框。"""
        if getattr(self, "_active_editor", None) is editor:
            return
        self._active_editor = editor
        # 蓝框：主动区 focus 边框色已是蓝，这里通过属性强调
        for ed in (self.input_edit, self.output_edit):
            is_active = ed is editor
            ed.setProperty("activeRegion", "1" if is_active else "0")
            ed.style().unpolish(ed); ed.style().polish(ed)

    def _do_selection_link(self):
        """把主动区选区映射到从属区，铺灰色底。支持原文↔译文双向。"""
        try:
            editor = self._link_pending_src
            if editor is None:
                return
            cur = editor.textCursor()
            if not cur.hasSelection():
                return
            s0, s1 = cur.selectionStart(), cur.selectionEnd()
            from_src = editor is self.input_edit
            other = self.output_edit if from_src else self.input_edit
            other_full = other.toPlainText()
            if not other_full.strip():
                return
            align = getattr(self, "_align", None)
            ts = te = None
            if align:
                lo = hi = None
                for (sa, sb, ta, tb) in align:
                    # 主动侧区间 / 从属侧区间
                    a0, a1 = (sa, sb) if from_src else (ta, tb)
                    o0, o1 = (ta, tb) if from_src else (sa, sb)
                    if a1 > s0 and a0 < s1:          # 选区与该句有重叠
                        lo = o0 if lo is None else min(lo, o0)
                        hi = o1 if hi is None else max(hi, o1)
                if lo is not None:
                    ts, te = lo, hi
            if ts is None:
                span = _proportional_span(editor.toPlainText(), s0, s1, other_full)
                if span:
                    ts, te = span
            if ts is None:
                return
            while ts < te and other_full[ts].isspace():
                ts += 1
            while te > ts and other_full[te-1].isspace():
                te -= 1
            other_hl = self._hl_output if from_src else self._hl_input
            self._link_guard = True
            try:
                other_hl.set_link(ts, te)
            finally:
                self._link_guard = False
        except Exception:
            self._link_guard = False

    def _apply_link_match(self, other_editor, translated, src_ratio=None):
        """在 other_editor 文本中找与 translated 最相似的连续区间，灰色高亮。
        src_ratio 是源选区相对位置，用于优先在目标文本对应段落/位置附近匹配。"""
        try:
            translated = (translated or "").strip()
            if not translated:
                return
            text = other_editor.toPlainText()
            if not text.strip():
                return
            span = _best_match_span(text, translated, src_ratio)
            if span is None:
                return
            s, e = span
            hl = self._hl_input if other_editor is self.input_edit else self._hl_output
            self._link_guard = True
            try:
                hl.set_link(s, e)
            finally:
                self._link_guard = False
        except Exception:
            self._link_guard = False

    def _collect_keys(self):
        return {
            "deepl": self.settings.value("deepl_key", ""),
            "google_api": self.settings.value("google_api_key", ""),
            "deepseek": self.settings.value("deepseek_key", ""),
            "hunyuan": self.settings.value("hunyuan_key", ""),
            "openai": self.settings.value("openai_key", ""),
            "gemini": self.settings.value("gemini_key", ""),
            "claude": self.settings.value("claude_key", ""),
            "glm": self.settings.value("glm_key", ""),
            "ernie": self.settings.value("ernie_key", ""),
            "doubao": self.settings.value("doubao_key", ""),
            "qwen": self.settings.value("qwen_key", ""),
            "kimi": self.settings.value("kimi_key", ""),
        }

    def _on_selection_changed_END(self):
        pass

    def _update_karaoke(self, pos_ms):
        """根据当前播放位置高亮已读部分（青绿色）。"""
        if self._speak_editor is None:
            return
        bounds = self._speak_boundaries
        if not bounds:
            return
        # 保险丝：边界超出当前文字长度说明已过期（文字被改过），自动清空防错位重画
        try:
            if bounds[-1][1] > len(self._speak_editor.toPlainText()):
                self._speak_boundaries = []
                return
        except Exception:
            pass
        # 提前量：取中间值。之前 350ms 偏多导致字幕抢拍，180ms 偏少又滞后。
        LEAD_FIXED = 120   # 固定提前 120ms
        cur_end = None
        cur_start = bounds[0][0]
        for (cs, ce, off, dur) in bounds:
            lead = LEAD_FIXED + (dur * 0.25 if dur else 0)
            if off - lead <= pos_ms:
                cur_end = ce
            else:
                break
        if cur_end is None:
            # 还没到第一个词的时间点，清空已读绿色（但保留蓝色选区）
            self._apply_karaoke_selection(cur_start, cur_start)
            return
        self._apply_karaoke_selection(cur_start, cur_end)

    def _apply_karaoke_selection(self, start, end):
        editor = self._speak_editor
        hl = self._hl_input if editor is self.input_edit else self._hl_output
        # rehighlight 会触发 textChanged -> 用 guard 防止 _on_input_changed 清掉本高亮
        self._link_guard = True
        try:
            hl.set_range(start, end)
        finally:
            self._link_guard = False

    def _clear_karaoke(self):
        # 清掉绿色已读；若之前是朗读选区，恢复蓝色选区底色
        self._hl_input.clear_range()
        self._hl_output.clear_range()

    def _setup_selection_highlight(self):
        """朗读选区时铺底色：用户选区=蓝色；灰色联动区=灰色（保持不变蓝）。"""
        sel = getattr(self, "_sel_range", None)
        ed = getattr(self, "_sel_editor", None)
        is_link = getattr(self, "_sel_is_link", False)
        self._link_guard = True
        try:
            self._hl_input.clear_selection()
            self._hl_output.clear_selection()
            if sel and ed is not None:
                hl = self._hl_input if ed is self.input_edit else self._hl_output
                if is_link:
                    hl.set_link(sel[0], sel[1])      # 保持灰色
                else:
                    hl.clear_link()
                    hl.set_selection(sel[0], sel[1]) # 蓝色
        finally:
            self._link_guard = False

    def _restore_selection_highlight(self):
        """朗读结束：清绿色，恢复蓝色选区（若有）。"""
        self._hl_input.clear_range()
        self._hl_output.clear_range()
        # set_selection 已在 _setup 时设好，clear_range 后蓝色仍在；无选区则什么都不显示

    # ---- 进度条拖动 ----
    def _update_rate_tooltip(self, value=None):
        """语速气球：0 显示『朗读语速 正常』，否则带正负百分比。
        拖动时用 QToolTip 在滑块上方持续显示，不消失。"""
        if value is None:
            value = self.rate_slider.value()
        if value == 0:
            txt = "朗读语速 正常"
        else:
            txt = f"朗读语速 {'+' if value > 0 else ''}{value}%"
        self.rate_slider.setToolTip(txt)
        # 拖动时在滑块手柄上方持续显示气球
        from PyQt6.QtWidgets import QToolTip
        from PyQt6.QtCore import QPoint
        sl = self.rate_slider
        rng = sl.maximum() - sl.minimum()
        if rng > 0:
            frac = (value - sl.minimum()) / rng
            x = int(frac * sl.width())
            gp = sl.mapToGlobal(QPoint(x, -6))
            QToolTip.showText(gp, txt, sl)

    def _on_seek_start(self, side=None):
        # 只有拖动"当前朗读侧"的进度条才生效；拖另一侧无效（互不影响）
        if side is not None and side != getattr(self, "_active_side", "src"):
            self._seeking = False
            return
        self._seeking = True

    def _on_seek_moved(self, value, side=None):
        """拖动进度条时实时刷新青色已读位置。只对当前朗读侧生效。"""
        if not getattr(self, "_seeking", False):
            return
        if side is not None and side != getattr(self, "_active_side", "src"):
            return
        dur = getattr(self, "_play_duration", 0) or (self.player.duration() if self.player else 0)
        if dur > 0 and self._speak_boundaries:
            pos_ms = dur * (value / 1000.0)
            self._update_karaoke(pos_ms)

    def _on_seek_end(self):
        self._seeking = False
        self._seek_ratio(self.play_slider.value() / 1000.0)

    def _seek_ratio(self, ratio):
        if self.player is None:
            return
        dur = getattr(self, "_play_duration", 0) or self.player.duration()
        if dur > 0:
            self.player.setPosition(int(dur * ratio))
            # 立即刷新高亮到目标位置（暂停时也更新）
            if self._speak_boundaries:
                self._update_karaoke(dur * ratio)

    def _on_en_voice_changed(self, name):
        self.settings.setValue("en_voice", name)
        self._on_voice_or_rate_changed(changed_lang="EN")

    def _on_engine_changed(self, engine):
        self.settings.setValue("engine", engine)
        # 改引擎后自动触发翻译（若有输入文本）
        if self.input_edit.toPlainText().strip():
            self._start_translate(auto=True)

    def _on_zh_voice_changed(self, name):
        self.settings.setValue("zh_voice", name)
        self._on_voice_or_rate_changed(changed_lang="ZH")

    def _on_voice_or_rate_changed(self, changed_lang=None):
        # 朗读进行中更改嗓音/语速/引擎 -> 在当前进度处用新设置重读，
        # 但保持进度条位置不跳回、按钮保持"继续朗读"青色不闪。
        _playing = False
        if self.player is not None:
            _st = self.player.playbackState()
            _playing = _st in (QMediaPlayer.PlaybackState.PlayingState,
                               QMediaPlayer.PlaybackState.PausedState)
        if not ((getattr(self, "_is_speaking", False) or _playing)
                and self._speak_editor is not None):
            return
        _ll = getattr(self, "_last_lang", None)
        if changed_lang is not None and _ll and changed_lang != _ll:
            return   # 改的是另一种语言的嗓音，与当前朗读无关，不打断
        ratio = 0.0
        dur = getattr(self, "_play_duration", 0)
        if dur > 0 and self.player is not None:
            ratio = self.player.position() / dur
        self._preserve_play_ui = True          # 重读期间保持进度条与按钮状态
        self._preserve_slider_value = self.play_slider.value()
        self._freeze_slider = True             # 生成期间冻结进度条在当前位置
        self.do_speak(self._speak_editor, from_pos_ratio=ratio)
        self._preserve_play_ui = False

    def _stop_side(self, editor):
        """停止指定侧的朗读/暂停/音频生成。当前朗读的是另一侧则不动作。"""
        # 该侧是否是当前朗读/暂停/生成的对象
        is_current = getattr(self, "_speak_editor", None) is editor
        worker_running = getattr(self, "tts_worker", None) and self.tts_worker.isRunning()
        player_active = False
        if self.player is not None:
            st = self.player.playbackState()
            player_active = st in (QMediaPlayer.PlaybackState.PlayingState,
                                   QMediaPlayer.PlaybackState.PausedState)
        if is_current and (worker_running or player_active or getattr(self, "_is_speaking", False)):
            self.stop_speak()
        # 否则本侧无正在进行的朗读，停止键无效

    def _on_seek_end_side(self, side):
        if side != getattr(self, "_active_side", "src"):
            self._seeking = False
            return
        self._on_seek_end()

    # ---------- 导出当前文字 ----------
    def _last_dir(self, key="export"):
        """记住的上次保存目录；首次默认下载目录。"""
        import os
        d = self.settings.value(f"last_dir_{key}", "")
        if d and os.path.isdir(d):
            return d
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def _remember_dir(self, path, key="export"):
        import os
        self.settings.setValue(f"last_dir_{key}", os.path.dirname(path))

    def _gen_filename(self, side, ext=".txt"):
        """文件名规则（空格分隔）：OT/TT 语言 日期 时间。
        例如 OT ZH 2026-06-30 013733.txt。原文=OT，译文=TT。"""
        import datetime
        text = (self.input_edit if side == "src" else self.output_edit).toPlainText()
        prefix = "OT" if side == "src" else "TT"
        lang = "ZH" if _text_is_chinese(text) else "EN"
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")
        return f"{prefix} {lang} {ts}{ext}"

    def _export_text(self, side):
        """导出当前原文/译文区的文字（只文字，无时间等信息）。"""
        import os
        text = (self.input_edit if side == "src" else self.output_edit).toPlainText()
        if not text.strip():
            self.status.showMessage("没有可导出的文字", 2500)
            return
        name = "原文" if side == "src" else "译文"
        from PyQt6.QtWidgets import QFileDialog
        filters = "文本 (*.txt);;Markdown (*.md);;Word (*.docx);;JSON (*.json);;PDF (*.pdf)"
        default = os.path.join(self._last_dir("export"), self._gen_filename(side, ".txt"))
        path, sel = QFileDialog.getSaveFileName(self, f"导出{name}文字", default, filters)
        if not path:
            return
        try:
            self._write_text_file(path, text, sel)
            self._remember_dir(path, "export")
            self.status.showMessage(f"已导出：{path}", 4000)
        except Exception as e:
            _log_error(f"导出文字失败: {e}")
            QMessageBox.warning(self, "导出失败", str(e))

    def _write_text_file(self, path, text, sel_filter=""):
        """按扩展名写出文字到 txt/md/json/docx/pdf。"""
        import os
        ext = os.path.splitext(path)[1].lower()
        if ext == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"text": text}, f, ensure_ascii=False, indent=2)
        elif ext == ".docx":
            from docx import Document
            doc = Document()
            for line in text.split("\n"):
                doc.add_paragraph(line)
            doc.save(path)
        elif ext == ".pdf":
            self._write_pdf(path, text)
        else:  # txt / md / 其它都按纯文本
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def _cjk_font(self):
        """注册并返回 PDF 用中文字体名；找不到指定字体则回退系统默认中文字体。"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os, sys
        if getattr(self, "_pdf_font_name", None):
            return self._pdf_font_name
        # 优先：Mac=PingFangHK-Light / Win=思源黑体HK Light；回退系统默认中文字体
        candidates = []
        if sys.platform == "darwin":
            candidates = ["/System/Library/Fonts/PingFang.ttc",
                          "/Library/Fonts/PingFang.ttc",
                          "/System/Library/Fonts/STHeiti Light.ttc"]
        elif sys.platform.startswith("win"):
            candidates = [r"C:\Windows\Fonts\SourceHanSansHWHK-Light.otf",
                          r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyh.ttf",
                          r"C:\Windows\Fonts\simsun.ttc"]
        else:
            candidates = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        for fp in candidates:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CJK", fp))
                    self._pdf_font_name = "CJK"
                    return "CJK"
                except Exception:
                    continue
        self._pdf_font_name = "Helvetica"
        return "Helvetica"

    def _write_pdf(self, path, text):
        """A4 竖版纯文本 PDF，按可用宽度自动换行（修右侧出画）。"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.pdfbase.pdfmetrics import stringWidth
        font = self._cjk_font()
        size = 12
        c = canvas.Canvas(path, pagesize=A4)
        W, H = A4                       # 595 x 842 pt
        ml = mr = 2 * cm
        mt = mb = 2 * cm
        usable = W - ml - mr
        x = ml
        y = H - mt
        line_h = size * 1.5
        for para in text.split("\n"):
            if para == "":
                y -= line_h
                if y < mb:
                    c.showPage(); c.setFont(font, size); y = H - mt
                continue
            # 按字符累积，超出可用宽度就换行（中英混排通用）
            line = ""
            for ch in para:
                if stringWidth(line + ch, font, size) > usable:
                    c.setFont(font, size); c.drawString(x, y, line); y -= line_h
                    if y < mb:
                        c.showPage(); y = H - mt
                    line = ch
                else:
                    line += ch
            if line:
                c.setFont(font, size); c.drawString(x, y, line); y -= line_h
                if y < mb:
                    c.showPage(); y = H - mt
        c.save()

    # ---------- 导入文件 ----------
    def _import_file(self):
        from PyQt6.QtWidgets import QFileDialog
        filters = "支持的文件 (*.txt *.md *.docx *.pdf);;文本 (*.txt *.md);;Word (*.docx);;PDF (*.pdf)"
        path, _ = QFileDialog.getOpenFileName(self, "导入文件", self._last_dir("import"), filters)
        if not path:
            return
        self._remember_dir(path, "import")
        self._do_import(path)

    def _do_import(self, path):
        import os
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in (".txt", ".md"):
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            elif ext == ".docx":
                from docx import Document
                doc = Document(path)
                text = "\n".join(p.text for p in doc.paragraphs)
            elif ext == ".pdf":
                text = self._read_pdf_text(path)
            else:
                QMessageBox.warning(self, "不支持的格式", f"暂不支持导入：{ext}")
                return
        except Exception as e:
            _log_error(f"导入文件失败: {e}")
            QMessageBox.warning(self, "导入失败", str(e))
            return
        # 关键：先记录导入状态，再 setPlainText。
        # 因为 setPlainText 会同步触发 textChanged -> _on_input_changed -> _update_file_buttons，
        # 若此时导入状态还没记录，会先被判为"不一致"产生错误中间态（这是之前反复失败的根因）。
        self._imported_path = path
        self._imported_ext = ext
        self._imported_text = text.strip()
        self._can_export_file = ext in (".txt", ".md", ".docx")
        self.input_edit.setPlainText(text)
        self._update_file_buttons()
        self.status.showMessage(f"已导入：{os.path.basename(path)}", 4000)
        # 触发翻译
        if text.strip():
            self._start_translate(auto=True)

    def _update_file_buttons(self):
        """根据导入/翻译/一致性状态，更新导入钮颜色与导出钮显隐/颜色。
        逻辑：
        - 原文与导入内容一致 -> 导入钮青色；不一致或无导入 -> 导入钮灰、导出钮隐藏。
        - 导入有效时导出钮出现：译文区有译文且格式可导出 -> 青色可点，否则灰色不可点。
        """
        imported = getattr(self, "_imported_path", None)
        imported_text = getattr(self, "_imported_text", None)
        cur_src = self.input_edit.toPlainText().strip()
        consistent = bool(imported) and imported_text is not None and cur_src == imported_text

        # 导入按钮颜色
        if hasattr(self, "import_btn"):
            if consistent:
                self.import_btn.setStyleSheet(
                    "QPushButton{background:#5aa8b0; border:1px solid #5aa8b0; border-radius:5px;}")
            else:
                self.import_btn.setStyleSheet("")

        if not hasattr(self, "export_file_btn"):
            return
        if not consistent:
            # 脱离文件模式：导出钮消失
            self.export_file_btn.setVisible(False)
            self.export_file_btn.setEnabled(False)
            self.export_file_btn.setStyleSheet("")
            return
        # 一致：导出钮出现
        self.export_file_btn.setVisible(True)
        has_tgt = bool(self.output_edit.toPlainText().strip())
        if self._can_export_file and has_tgt:
            self.export_file_btn.setEnabled(True)
            self.export_file_btn.setStyleSheet(
                "QPushButton{background:#5aa8b0; border:1px solid #5aa8b0; border-radius:5px;}")
        else:
            self.export_file_btn.setEnabled(False)
            self.export_file_btn.setStyleSheet("")

    def _read_pdf_text(self, path):
        """优先用 pdfplumber 抽取文字；失败再尝试 pypdf。"""
        try:
            import pdfplumber
            out = []
            with pdfplumber.open(path) as pdf:
                for pg in pdf.pages:
                    out.append(pg.extract_text() or "")
            text = "\n".join(out).strip()
            if text:
                return text
        except Exception as e:
            _log_error(f"pdfplumber 抽取失败: {e}")
        try:
            from pypdf import PdfReader
            r = PdfReader(path)
            return "\n".join((pg.extract_text() or "") for pg in r.pages).strip()
        except Exception as e:
            _log_error(f"pypdf 抽取失败: {e}")
            raise RuntimeError("无法从该 PDF 提取文字（可能是扫描件，需要 OCR）。")

    # ---------- 导出翻译后的文件 ----------
    def _export_file(self):
        if not getattr(self, "_can_export_file", False):
            QMessageBox.information(self, "暂不支持", "当前导入的文件类型暂不支持导出（如 PDF）。")
            return
        import os
        src_path = getattr(self, "_imported_path", "")
        if not src_path:
            return
        d = os.path.dirname(src_path)
        base, ext = os.path.splitext(os.path.basename(src_path))
        default = os.path.join(d, f"{base} T{ext}")   # 加 T 后缀
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出翻译后的文件", default,
                                              f"原格式 (*{ext})")
        if not path:
            return
        try:
            text = self.output_edit.toPlainText()
            if ext == ".docx":
                self._export_docx_keep(src_path, path, text)
            else:
                self._write_text_file(path, text)
            self.status.showMessage(f"已导出：{path}", 4000)
        except Exception as e:
            _log_error(f"导出文件失败: {e}")
            QMessageBox.warning(self, "导出失败", str(e))

    def _export_docx_keep(self, src_path, out_path, translated):
        """导出 docx：尽量沿用原文档段落结构，逐段替换为译文。
        （基础排版继承：段落数对应时按段替换；不完全对应时整体写入。）"""
        from docx import Document
        src = Document(src_path)
        src_paras = [p for p in src.paragraphs]
        tgt_lines = [l for l in translated.split("\n")]
        if len([p for p in src_paras if p.text.strip()]) == len([l for l in tgt_lines if l.strip()]):
            ti = 0
            tgt_nonempty = [l for l in tgt_lines if l.strip()]
            for p in src_paras:
                if p.text.strip():
                    # 保留段落样式，只换文字
                    for run in p.runs:
                        run.text = ""
                    if p.runs:
                        p.runs[0].text = tgt_nonempty[ti]
                    else:
                        p.add_run(tgt_nonempty[ti])
                    ti += 1
            src.save(out_path)
        else:
            # 段落数不匹配，退回纯文本 docx
            doc = Document()
            for line in tgt_lines:
                doc.add_paragraph(line)
            doc.save(out_path)

    def stop_speak(self, clear_only=False, keep_slider=False):
        self._is_speaking = False
        preserve = getattr(self, "_preserve_play_ui", False)
        # 中断正在进行的合成：worker 在下一个段边界检查点停止（软中断）
        w = getattr(self, "tts_worker", None)
        if w is not None and w.isRunning():
            w.cancel()
            if not clear_only:
                self.status.showMessage("正在停止…", 1500)
        self._hide_synth_busy()
        if hasattr(self, "_karaoke_timer"):
            self._karaoke_timer.stop()
        if self.player is not None and \
           self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
        if not preserve:
            self._clear_karaoke()   # 变更嗓音/引擎重读期间保留卡拉OK绿色与选区
        if not keep_slider and not preserve:
            self.play_slider.setValue(0)   # 进度跳回开始
        if not preserve:
            # 停止后：若该侧音频仍在内存，朗读钮保持青色（喇叭图标+可下载），
            # 否则才灰化。图标恢复喇叭、提示恢复"朗读原文/译文"。
            side = getattr(self, "_active_side", "src")
            self._side_cache.get(side, {})["position"] = 0   # 停止=进度归零，续播位置作废
            has_audio = bool(self._side_cache.get(side, {}).get("bytes"))
            btn = self.speak_src_btn if side == "src" else self.speak_tgt_btn
            name = "原文" if side == "src" else "译文"
            if has_audio:
                self._set_speak_btn_active(btn, True, icon="speak")
            else:
                self._set_speak_btn_active(btn, False)
            btn.setToolTip(f"朗读{name}")
            # 另一侧按钮状态按其缓存独立设置
            other = "tgt" if side == "src" else "src"
            obtn = self.speak_src_btn if other == "src" else self.speak_tgt_btn
            oname = "原文" if other == "src" else "译文"
            if bool(self._side_cache.get(other, {}).get("bytes")):
                self._set_speak_btn_active(obtn, True, icon="speak")
            else:
                self._set_speak_btn_active(obtn, False)
            obtn.setToolTip(f"朗读{oname}")
        if not clear_only:
            self.status.showMessage("已停止", 2000)

    def closeEvent(self, event):
        # 退出前安全结束朗读线程，避免 "QThread destroyed while running" 崩溃
        try:
            if self.player is not None:
                self.player.stop()
            w = getattr(self, "tts_worker", None)
            if w is not None and w.isRunning():
                w.cancel()
                w.quit()
                w.wait(2000)
            for rw in getattr(self, "_retired_workers", []):
                if rw.isRunning():
                    rw.cancel()
                    rw.quit()
                    rw.wait(1000)
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)
    # 单实例守护：已有实例运行则提示并退出（修复偶发双开两个程序）
    from PyQt6.QtCore import QLockFile, QDir
    _lock = QLockFile(QDir.temp().absoluteFilePath("EnglishCoach.single.lock"))
    if not _lock.tryLock(100):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, "English Coach",
                                "English Coach 已在运行，请勿重复启动。")
        sys.exit(0)
    app._single_instance_lock = _lock   # 保持引用直到退出
    # 深色调色板：接替原全局 QWidget 样式规则的着色（该规则会"污染"滚动条，
    # 使 Qt 放弃原生绘制画出原始样式，故删规则改用调色板——调色板不影响原生滚动条）
    from PyQt6.QtGui import QPalette, QColor
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#dcdcdc"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#252526"))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#2d2d30"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#dcdcdc"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#2d2d30"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#dcdcdc"))
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#3a6ea5"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2d2d30"))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor("#e0e0e0"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#777777"))
    app.setPalette(pal)
    f = app.font(); f.setPixelSize(13); app.setFont(f)
    # Win11（构建号>=22000）且 Qt>=6.7 提供 windows11 样式 -> 用原生 Fluent 胶囊滚动条
    if sys.platform == "win32":
        try:
            if sys.getwindowsversion().build >= 22000:
                from PyQt6.QtWidgets import QStyleFactory
                if "windows11" in [k.lower() for k in QStyleFactory.keys()]:
                    app.setStyle("windows11")
        except Exception:
            pass
    try:
        win = MainWindow()
    except Exception as e:
        # 启动期异常：弹窗显示，避免"无报错也无界面"
        import traceback as _tb
        msg = f"{e}\n\n{_tb.format_exc()}"
        try:
            QMessageBox.critical(None, "EnglishCoach 启动失败", msg)
        except Exception:
            print(msg)
        sys.exit(1)
    win.show()
    win.raise_()              # 提到最前
    win.activateWindow()      # 抢占焦点（老 macOS 上常需要）
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
