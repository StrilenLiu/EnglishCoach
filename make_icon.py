# English Coach icon generator
# Copyright (C) 2026 Strilen Liu — SPDX-License-Identifier: GPL-3.0-or-later
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EnglishCoach 应用图标生成。
设计：圆角渐变底 + 居中"翻开的书" + 书上方两枚圆角标牌(A / 文)。
线条采用圆头粗笔、平滑连接，质感接近 Apple 原生图标。
输出：
  icon_1024.png        (CPU 版 · macOS 留边)
  icon_win_1024.png    (CPU 版 · Windows 铺满)
  icon_gpu_1024.png    (GPU 版 · macOS 留边，青绿底 + 闪电)
  icon_gpu_win_1024.png(GPU 版 · Windows 铺满)
"""
from PIL import Image, ImageDraw

SIZE = 1024
S = 8                      # 超采样倍数（更高 -> 边缘更圆润）
W = SIZE * S
cx = W // 2

# 配色
BG_BLUE_TOP = (32, 132, 200)
BG_BLUE_BOT = (12, 92, 158)
BG_GREEN_TOP = (32, 196, 150)
BG_GREEN_BOT = (16, 138, 116)
WHITE = (255, 255, 255, 255)
ORANGE = (255, 170, 64, 255)
TEAL = (40, 210, 184, 255)
BOLT = (255, 216, 72, 255)


def lerp(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def round_cap_line(d, p1, p2, width, fill):
    """圆头粗线：线段 + 两端实心圆，连接处自然圆润。"""
    d.line([p1, p2], fill=fill, width=width)
    r = width // 2
    for p in (p1, p2):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def make_bg(top, bot):
    """生成圆角渐变底。"""
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    grad = Image.new("RGBA", (W, W))
    gd = ImageDraw.Draw(grad)
    for y in range(W):
        gd.line([(0, y), (W, y)], fill=lerp(top, bot, y / W) + (255,))
    radius = int(W * 0.225)
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, W - 1], radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)
    return img


def draw_foreground(draw, with_bolt=False):
    """在给定 draw 上绘制：两枚标牌(A/文) + 翻开的书。两个版本共用，保证一致。"""
    # ---------------- 上方两枚圆角标牌 ----------------
    badge_w = badge_h = int(W * 0.215)
    badge_y = int(W * 0.205)
    gap = int(W * 0.045)
    bx_a = cx - gap - badge_w
    bx_t = cx + gap
    brad = int(badge_w * 0.32)

    draw.rounded_rectangle([bx_a, badge_y, bx_a + badge_w, badge_y + badge_h],
                           radius=brad, fill=ORANGE)
    draw.rounded_rectangle([bx_t, badge_y, bx_t + badge_w, badge_y + badge_h],
                           radius=brad, fill=TEAL)

    glw = int(W * 0.030)   # 字形线宽（更粗更圆润）

    # 字母 A
    acx = bx_a + badge_w // 2
    acy = badge_y + badge_h // 2
    ah = int(badge_h * 0.54)
    aw = int(badge_w * 0.44)
    top = (acx, acy - ah // 2)
    bl = (acx - aw // 2, acy + ah // 2)
    br = (acx + aw // 2, acy + ah // 2)
    round_cap_line(draw, bl, top, glw, WHITE)
    round_cap_line(draw, top, br, glw, WHITE)
    round_cap_line(draw, (acx - int(aw * 0.27), acy + int(ah * 0.10)),
                         (acx + int(aw * 0.27), acy + int(ah * 0.10)), glw, WHITE)

    # 汉字 文
    fcx = bx_t + badge_w // 2
    fcy = badge_y + badge_h // 2
    fh = int(badge_h * 0.58)
    fw = int(badge_w * 0.52)
    # 点
    round_cap_line(draw, (fcx, fcy - fh // 2),
                         (fcx, fcy - fh // 2 + int(fh * 0.12)), glw, WHITE)
    # 横
    hy = fcy - int(fh * 0.22)
    round_cap_line(draw, (fcx - fw // 2, hy), (fcx + fw // 2, hy), glw, WHITE)
    # 撇
    round_cap_line(draw, (fcx + int(fw * 0.22), hy + int(fh * 0.06)),
                         (fcx - int(fw * 0.42), fcy + fh // 2), glw, WHITE)
    # 捺
    round_cap_line(draw, (fcx - int(fw * 0.10), fcy - int(fh * 0.02)),
                         (fcx + int(fw * 0.42), fcy + fh // 2), glw, WHITE)

    # ---------------- 居中"翻开的书" ----------------
    bcx = cx
    bcy = int(W * 0.635)
    bw = int(W * 0.52)
    bh = int(W * 0.26)
    blw = int(W * 0.028)   # 书线宽（更粗更圆润）

    spine_top = (bcx, bcy - bh // 2 + int(bh * 0.18))
    spine_bot = (bcx, bcy + bh // 2)

    def page(sign):
        return [
            (bcx + sign * int(bw * 0.03), bcy - bh // 2 + int(bh * 0.18)),
            (bcx + sign * (bw // 2), bcy - bh // 2),
            (bcx + sign * (bw // 2), bcy + bh // 2 - int(bh * 0.16)),
            (bcx + sign * int(bw * 0.03), bcy + bh // 2),
        ]

    for sign in (-1, 1):
        pts = page(sign)
        for i in range(len(pts)):
            round_cap_line(draw, pts[i], pts[(i + 1) % len(pts)], blw, WHITE)
    round_cap_line(draw, spine_top, spine_bot, blw, WHITE)

    # 书页横线
    for frac in (0.42, 0.58, 0.74):
        yy = bcy - bh // 2 + int(bh * frac)
        round_cap_line(draw, (bcx - int(bw * 0.38), yy), (bcx - int(bw * 0.13), yy),
                       int(blw * 0.72), WHITE)
        round_cap_line(draw, (bcx + int(bw * 0.13), yy), (bcx + int(bw * 0.38), yy),
                       int(blw * 0.72), WHITE)

    # ---------------- GPU 版闪电 ----------------
    if with_bolt:
        lx, ly = int(W * 0.715), int(W * 0.605)
        ls = int(W * 0.155)
        bolt = [
            (lx + int(ls * 0.45), ly),
            (lx, ly + int(ls * 0.60)),
            (lx + int(ls * 0.33), ly + int(ls * 0.60)),
            (lx + int(ls * 0.14), ly + ls),
            (lx + int(ls * 0.66), ly + int(ls * 0.38)),
            (lx + int(ls * 0.31), ly + int(ls * 0.38)),
        ]
        draw.polygon(bolt, fill=BOLT)


def build(top, bot, with_bolt, out_mac, out_win):
    img = make_bg(top, bot)
    draw_foreground(ImageDraw.Draw(img), with_bolt=with_bolt)
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    # Windows：铺满
    img.save(out_win)
    print("已生成", out_win, img.size)
    # macOS：留边 82%
    CONTENT = 0.82
    inner = int(SIZE * CONTENT)
    content = img.resize((inner, inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    off = (SIZE - inner) // 2
    canvas.paste(content, (off, off), content)
    canvas.save(out_mac)
    print("已生成", out_mac, canvas.size)


# CPU 版（蓝底）
build(BG_BLUE_TOP, BG_BLUE_BOT, False, "icon_1024.png", "icon_win_1024.png")
# GPU 版（青绿底 + 闪电）
build(BG_GREEN_TOP, BG_GREEN_BOT, True, "icon_gpu_1024.png", "icon_gpu_win_1024.png")
