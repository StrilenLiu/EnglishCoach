#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 english_coach.py 生成 CHANGELOG.md
Generate CHANGELOG.md from english_coach.py

程序内的 CHANGELOG 列表是唯一数据源 —— 「关于 / 更新记录」弹窗和本文件
读的是同一份数据，所以文档不会和程序里的说明脱节。

The CHANGELOG list inside the program is the single source of truth: the
in-app "What's New" dialog and this file read the same data, so the document
can never drift from what the program itself reports.

用法 / Usage:
    python gen_changelog.py            # 写入 CHANGELOG.md
    python gen_changelog.py --check    # 只检查是否需要更新（CI 友好）
"""
import argparse
import os
import re
import sys

HEADER = """# 更新记录 / Changelog

> 本文件由 `gen_changelog.py` 从 `english_coach.py` 自动生成，请勿手工编辑。
> 修改版本说明请改 `english_coach.py` 里的 `CHANGELOG`，然后重新运行生成脚本。
>
> This file is generated from `english_coach.py` by `gen_changelog.py` — do not
> edit it by hand. To change a release note, edit the `CHANGELOG` list in
> `english_coach.py` and re-run the generator.

"""


def load():
    """从源码里取 APP_VERSION 与 CHANGELOG，不执行 GUI 代码。"""
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "english_coach.py"), encoding="utf-8").read()

    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', src, re.M)
    version = m.group(1) if m else "unknown"

    start = src.index("CHANGELOG = [")
    # 逐字符配对方括号，准确定位列表结尾
    i = src.index("[", start)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "[":
            depth += 1
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    else:
        raise RuntimeError("找不到 CHANGELOG 列表结尾")

    ns = {}
    exec(src[start:end], {}, ns)          # 只执行这一段字面量赋值
    return version, ns["CHANGELOG"]


def render(version, entries):
    out = [HEADER, f"**当前版本 / Current version: v{version}**\n\n---\n"]
    for e in entries:
        ver = e.get("version", "?")
        date = e.get("date", "")
        out.append(f"\n## v{ver}" + (f" — {date}" if date else "") + "\n")

        t_zh = e.get("title", "")
        t_en = e.get("title_en", "")
        if t_zh:
            out.append(f"\n**{t_zh}**\n")
        if t_en:
            out.append(f"\n*{t_en}*\n")

        notes = e.get("notes") or []
        notes_en = e.get("notes_en") or []
        if notes:
            out.append("\n")
            for n in notes:
                out.append(f"- {n}\n")
        if notes_en:
            out.append("\n")
            for n in notes_en:
                out.append(f"- *{n}*\n")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="只检查 CHANGELOG.md 是否为最新，不写入")
    args = ap.parse_args()

    version, entries = load()
    text = render(version, entries)
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "CHANGELOG.md")

    if args.check:
        cur = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if cur == text:
            print(f"CHANGELOG.md 已是最新（v{version}，{len(entries)} 条记录）")
            return 0
        print("CHANGELOG.md 需要更新，请运行：python gen_changelog.py")
        return 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"已生成 CHANGELOG.md：v{version}，共 {len(entries)} 条版本记录")
    return 0


if __name__ == "__main__":
    sys.exit(main())
