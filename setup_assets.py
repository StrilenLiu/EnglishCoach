#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把源码运行所需的组件与模型一次配齐（Setup Dev 脚本的干活部分）。

为什么单独有这个文件：`pip install -r requirements.txt` 只能装 pip 包，
装不了几百 MB 的模型权重，也装不了不在 PyPI 上的 spaCy 英文模型。以前这
些只有构建脚本会下载，于是打包用户没事、源码用户卡住 —— 而 README 是承诺
过源码可以直接跑的。

登记表不在这里重抄一份：下载地址、镜像、检测方式全部取自 english_coach.py
的 _ASSETS，那是唯一的事实来源。改地址只改那一处，这里自动跟上。

    python setup_assets.py            # 缺什么装什么
    python setup_assets.py --force    # 已有的也重新下
    python setup_assets.py whisper    # 只处理指定的几样
"""

import sys


def _report(pct, extra):
    """把下载进度打在同一行上，不刷屏。"""
    if pct is not None and pct >= 0:
        msg = f"    {pct:3d}%" + (f"  {extra}" if extra else "")
    else:
        msg = f"    {extra or '...'}"
    sys.stdout.write("\r" + msg.ljust(70))
    sys.stdout.flush()


def main(argv):
    force = "--force" in argv
    wanted = [a for a in argv if not a.startswith("-")]

    try:
        import english_coach as ec
    except Exception as e:
        print(f"[×] 无法载入 english_coach.py：{e}")
        print("    先跑 pip install -r requirements.txt，再运行本脚本。")
        return 2

    ids = wanted or list(ec._ASSETS.keys())
    bad = [i for i in ids if i not in ec._ASSETS]
    if bad:
        print(f"[×] 不认识的组件：{', '.join(bad)}")
        print(f"    可选：{', '.join(ec._ASSETS)}")
        return 2

    print(f"English Coach v{ec.APP_VERSION} — 配齐源码运行所需的组件与模型")
    print(f"模型目录：{ec.os.path.expanduser('~/EnglishCoach Models')}\n")

    failed = []
    for aid in ids:
        a = ec._ASSETS[aid]
        label = f"{aid} ({a['size']})"
        if not force and ec._asset_ready(aid):
            print(f"[✓] {label} 已就位，跳过")
            continue
        print(f"[·] {label} 开始安装…")
        # 官方源优先，不成换国内镜像 —— 所有源一律都会走到。只有在同一个
        # 源上原地重试确实没意义时(404、磁盘满)才提前跳过剩下的次数。
        sources = [("官方源", a["official"])]
        if a.get("mirror"):
            sources.append(("国内镜像", a["mirror"]))
        ok = False
        last = ""
        for sname, endpoint in sources:
            for attempt in range(ec.ASSET_RETRIES):
                try:
                    a["fetch"](endpoint, _report)
                    sys.stdout.write("\r" + " " * 70 + "\r")
                    print(f"[✓] {label} 完成（{sname}）")
                    ok = True
                    break
                except Exception as e:
                    sys.stdout.write("\r" + " " * 70 + "\r")
                    last = f"{type(e).__name__}: {e}"
                    print(f"    {sname} 第 {attempt + 1} 次失败：{last}")
                    if not ec._worth_retrying(e):
                        break
                    if attempt < ec.ASSET_RETRIES - 1:
                        import time
                        time.sleep(ec.ASSET_BACKOFF[
                            min(attempt, len(ec.ASSET_BACKOFF) - 1)])
            if ok:
                break
        if not ok:
            failed.append((aid, last, a.get("manual", "")))
            print(f"[×] {label} 所有来源均失败")

    print()
    if not failed:
        print("全部就位，现在可以 python english_coach.py 了。")
        return 0
    print(f"有 {len(failed)} 项没装上，手动办法如下：\n")
    for aid, last, manual in failed:
        print(f"  {aid}：{last}")
        print(f"    {manual}\n")
    print("装不上不影响其余功能：缺哪一样，就只有对应的那个功能不可用；")
    print("程序运行时也会在用到它的时候再问你要不要下载。")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
