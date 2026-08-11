# 更新记录 / Changelog

> 本文件由 `gen_changelog.py` 从 `english_coach.py` 自动生成，请勿手工编辑。
> 修改版本说明请改 `english_coach.py` 里的 `CHANGELOG`，然后重新运行生成脚本。
>
> This file is generated from `english_coach.py` by `gen_changelog.py` — do not
> edit it by hand. To change a release note, edit the `CHANGELOG` list in
> `english_coach.py` and re-run the generator.

**当前版本 / Current version: v2.15.12**

---

## v2.15.12 — 2026-07-28

**恢复 API Key 输入框样式 · 复选框勾选色恢复为蓝色（不再跟随系统强调色）**

*Restored the API key field styling · checkbox tick colour is blue again instead of following the system accent*

- 修复 API Key 输入框在 Win10 深色下变白、Win11 出现原生底部亮条：输入框原本与下拉闭合框共用同一条样式规则，改用混合方案时只搬了下拉、把输入框漏了，导致它退回原生渲染。现已恢复，深色 #2d2d30 / 浅色 #ffffff，与下拉闭合框一致，悬停与聚焦为蓝边
- 修复 Win11 复选框勾选后是黄色：复选框现在走系统原生渲染，勾选色默认取自【系统强调色】，系统若设成黄色勾选就是黄色。现在显式把调色板的强调色固定为程序蓝 #1e88e5，原生渲染与边线保持不变，Win10 同样受益
- 关于朗读与卡拉OK字幕的原则：经实测验证，卡拉OK（青蓝 #5aa8b0 + 白字）确实覆盖在蓝色主动选区与灰色被动选区之上，三层重叠时最终显示卡拉OK；拖动进度条的『字幕铁律』（该侧音频缓存在且文字在则必有字幕，边界丢失会先从缓存恢复、再按朗读范围重建）也已在代码中实现
- 本次仅改动非 mac 路径的两处样式；mac 分支未动（经伪装 darwin 验证不调用非 mac 的调色板函数、不重建样式）；6.11 与 6.4.2 两套 Qt 验证：主界面下拉、设置窗下拉、反复切换主题均正常，设置窗与主窗样式一致，无崩溃
- 新增三平台的安装与卸载脚本：Windows 的 Install.bat / Uninstall.bat（装到用户目录并创建开始菜单与可选桌面快捷方式，无需管理员权限）、macOS 的 Install.command / Uninstall.command（复制到应用程序并自动移除隔离标记，未签名应用首次打开不再被拦截）、Linux 的 Install.sh / Uninstall.sh（装到 ~/.local/opt 或 /opt，安装图标并创建应用菜单入口）。卸载脚本默认保留翻译历史、设置与 API Key，会单独询问是否一并删除
- 四个构建脚本现在会把对应平台的安装脚本一并打进产物
- Linux 构建脚本改进：conda 由必需改为可选，没有 conda 时自动创建虚拟环境（绕开 Debian/Ubuntu 系统 Python 的 PEP 668 限制），可直接在 Docker 容器里编译；旧虚拟环境若是低版本 Python 建的会自动重建；新增 Python 3.10 版本下限检查
- Linux 构建脚本钉死 PyQt6 6.9.1：6.10 起的 Linux 轮子要求 glibc 2.34 以上，在 Debian 11 / Ubuntu 20.04 上装不了，pip 会退去编译源码并因缺少 qmake 而失败。6.9.x 是能装在 glibc 2.31 上的最新版本，用它编出的产物可覆盖 Ubuntu 20.04 及以上
- Linux 产物现在捆绑四个常缺的 xcb 支持库（约 94KB）：Qt 6.5+ 需要 libxcb-cursor 才能加载 xcb 平台插件，而多数发行版默认不装，用户一启动就是一堆 qt.qpa.plugin 报错。libxcb.so.1、libX11、libc 等仍用系统的，因为它们必须与用户的 X 服务器和显卡驱动匹配
- Linux 启动脚本会在启动前检查系统库，缺失时直接给出按发行版适配的安装命令，而不是抛出难以理解的 Qt 插件报错
- 仓库文档整理：新增 CHANGELOG.md（由 gen_changelog.py 从程序内的更新记录生成，与「关于 → 更新记录」同源）、.gitignore，依赖拆分为 requirements.txt（运行，带平台标记）、requirements-build.txt（打包工具）与 requirements-gpu.txt（CUDA 版 torch）；README 增加下载链接、各平台安装说明与常见问题；移除测试用的 scrollbar_probe.py

- *Fixed the API key field turning white in dark mode on Win10 and showing a native bottom accent line on Win11: the field originally shared one style rule with the dropdown closed-box, and when the hybrid approach was introduced only the dropdown was carried over, leaving the field to fall back to native rendering. It is restored now — #2d2d30 in dark, #ffffff in light, matching the dropdown closed-box, with a blue border on hover and focus*
- *Fixed the Win11 checkbox tick appearing yellow: checkboxes are rendered natively, and the tick colour defaults to the system accent, so a yellow system accent produced a yellow tick. The palette's accent role is now pinned to the app blue #1e88e5, leaving native rendering and the indicator border untouched; Win10 benefits from the same change*
- *On the playback and karaoke subtitle principle: verified by test that karaoke (teal #5aa8b0 with white text) does paint above both the blue active selection and the grey passive selection, and wins where all three overlap; the slider's subtitle rule (whenever that side has cached audio and text, dragging must show subtitles, restoring boundaries from cache and otherwise rebuilding them from the spoken range) is already implemented*
- *This release changes only two styling spots on the non-mac path; the mac branch is untouched (a simulated-darwin run confirms it neither calls the non-mac palette helper nor rebuilds the style); verified on Qt 6.11 and 6.4.2: main window dropdowns, settings dropdowns and repeated theme switching all work, the settings dialog matches the main window, and there are no crashes*
- *Added install and uninstall scripts for all three platforms: Install.bat / Uninstall.bat on Windows (installs into the user profile and creates a Start Menu entry plus an optional Desktop shortcut, no administrator rights needed), Install.command / Uninstall.command on macOS (copies into Applications and strips the quarantine flag automatically so the unsigned app is not blocked on first launch), and Install.sh / Uninstall.sh on Linux (installs into ~/.local/opt or /opt, adds the icon and an application-menu entry). The uninstallers keep translation history, settings and API keys by default and ask separately before removing them*
- *All four build scripts now bundle the matching platform's install scripts into the output*
- *Linux build script improvements: conda is now optional rather than required, and without it a virtual environment is created automatically, side-stepping the PEP 668 restriction on Debian and Ubuntu system Python so the build runs inside a Docker container as-is; an existing virtual environment built with an older Python is detected and rebuilt; a Python 3.10 minimum-version check was added*
- *The Linux build pins PyQt6 6.9.1: from 6.10 onwards the Linux wheels require glibc 2.34 or newer, which Debian 11 and Ubuntu 20.04 lack, so pip falls back to building from source and fails for want of qmake. The 6.9.x wheels are the newest installable on glibc 2.31, and building against them keeps the result compatible with Ubuntu 20.04 and later*
- *Linux builds now bundle four commonly-missing xcb support libraries (about 94KB): Qt 6.5+ needs libxcb-cursor to load its xcb platform plugin, yet most distributions do not install it, leaving users with a wall of qt.qpa.plugin errors at startup. libxcb.so.1, libX11 and libc are deliberately left to the system because they must match the user's X server and graphics drivers*
- *The Linux launcher now checks for the required system libraries before starting and prints a ready-to-paste install command matched to the distribution, instead of surfacing an opaque Qt plugin failure*
- *Repository housekeeping: added CHANGELOG.md (generated by gen_changelog.py from the changelog inside the program, so it shares a source with the in-app What's New dialog) and .gitignore; split dependencies into requirements.txt (runtime, with platform markers), requirements-build.txt (packaging tools) and requirements-gpu.txt (CUDA torch); the README gained download links, per-platform installation instructions and troubleshooting notes; removed the diagnostic scrollbar_probe.py*

## v2.15.11 — 2026-07-27

**修复设置窗语言/主题下拉『整体向上串一行、末尾空白』：弹出列表被卡在滚下一行的位置**

*Fixed the settings language/theme dropdowns appearing shifted up by one row with a blank at the end: the popup list was stuck scrolled down by one row*

- 根因(由现象精确定位)：这不是丢项，而是弹出列表被卡在『向下滚了一行』的位置。这两个下拉的弹出高度正好等于项数，本不需要滚动；但选中最后一项时 Qt 会 scrollTo 让当前项可见，把视图滚下一行，而弹出的滚动条是关闭的、滚轮也被忽略，滚下去就卡住回不来 —— 于是显示成 items[1..N-1] 加一行空白，正是『中文/English US』变成『English US/空白』、『深色/浅色/跟随系统』变成『浅色/跟随系统/空白』的现象
- 修复：只给设置窗的语言与主题这两个下拉，在弹出后把列表滚动位置归零。范围极窄 —— 不改任何弹出机制，不影响主界面下拉，也不影响设置窗里的其它下拉
- Linux/Fusion 下项目较矮、内容正好装得下，滚动上限为 0 根本滚不动，这正是此前在测试环境反复复现不出来的原因；windows11 原生样式下项目更高，才会滚出这一行
- Mac 分支直接跳过本处理，弹出仍走系统原生；6.11 与 6.4.2 两套 Qt 验证：主界面下拉(14 项)正常，反复选择并弹出 12 次后语言恒 2 项、主题恒 3 项、滚动位置恒为 0，无崩溃

- *Root cause (pinned down from the exact symptom): nothing was ever lost — the popup list was stuck one row down. These dropdowns size their popup to exactly the number of items so no scrolling should be needed, but selecting the last item makes Qt scroll the view to reveal it, and because the popup's scrollbar is disabled and the wheel is ignored, it stays scrolled and cannot come back. The result is items[1..N-1] plus a blank row, exactly matching 'Chinese / English US' becoming 'English US / blank' and 'Dark / Light / Follow System' becoming 'Light / Follow System / blank'*
- *Fix: for the settings dialog's language and theme dropdowns only, the list scroll position is reset to the top after the popup opens. The change is deliberately narrow — no popup machinery is modified, the main window dropdowns are untouched, and other dropdowns in the settings dialog are unaffected*
- *Under Linux/Fusion the items are shorter and the content fits exactly, so the scroll maximum is zero and nothing can scroll — which is why this never reproduced in the test environment; the native windows11 style renders taller items, which is what produces the extra row*
- *The mac branch skips this handling entirely and popups still use the native system look; verified on both Qt 6.11 and 6.4.2: the main window dropdowns (14 items) work, and after 12 rounds of selecting and reopening the language dropdown stays at 2 items, the theme dropdown at 3, and the scroll position stays at 0, with no crashes*

## v2.15.10 — 2026-07-27

**回退 2.15.9 对下拉弹出机制的改动（它弄坏了主界面下拉），只保留设置窗语言/主题下拉的丢项自愈**

*Reverted the 2.15.9 dropdown popup changes (they broke the main window dropdowns), keeping only the settings-dialog language/theme item self-heal*

- 回退：2.15.9 改了所有下拉共用的弹出机制（每次弹出重算可见项数、开滚动条兜底、滚轮条件放行），本意是修设置窗的丢项，结果把 2.15.8 里已经好用的主界面下拉一起弄坏了。现已完整恢复成 2.15.8 的弹出机制：滚动条关闭、可见项数按创建时项数、滚轮一律忽略、无弹出包装
- 保留：2.15.8 的下拉弹出背景随主题刷新（深色 #2d2d30 / 浅色 #ffffff）不受影响，仍然生效
- 保留并收紧：设置窗语言/主题下拉的丢项自愈改为只按身份值判断、且只在项【真的少了】时才重建 —— 项目齐全时完全不碰下拉，零副作用（此前按显示文字比对，会在每次界面重译时误触发重建）
- Mac 分支一字未动；6.11 与 6.4.2 两套 Qt 验证：主界面下拉(14 项引擎)与设置窗下拉(语言 2/主题 3)弹出均正常，弹出背景随主题正确，无崩溃

- *Reverted: 2.15.9 modified the popup machinery shared by every dropdown (recomputing the visible-item count on each popup, a scrollbar fallback, conditional wheel scrolling). It was meant to fix the settings dialog but broke the main window dropdowns that worked fine in 2.15.8. The 2.15.8 popup machinery is fully restored: scrollbar off, visible-item count fixed at creation, wheel always ignored, no popup wrapper*
- *Kept: the 2.15.8 fix that refreshes the dropdown popup background with the theme (#2d2d30 dark / #ffffff light) is unaffected and still active*
- *Kept and tightened: the settings dialog's language/theme item self-heal now checks identity values only and rebuilds only when an item is genuinely missing — when the items are complete it does not touch the dropdown at all, so there are no side effects (it previously compared display text, which triggered a needless rebuild on every UI retranslation)*
- *The mac branch is untouched; verified on both Qt 6.11 and 6.4.2: the main window dropdowns (14-item engine list) and the settings dropdowns (2 language / 3 theme) open correctly, the popup background follows the theme, and there are no crashes*

## v2.15.9 — 2026-07-27

**修复 Windows 语言/主题下拉反复切换后『丢一项』：弹出高度不够且滚不动，那一项永远够不着**

*Fixed the language/theme dropdowns losing an item after repeated switching on Windows: the popup was too short to fit every item and could not scroll*

- 根因：弹出列表同时做了三件相互冲突的事 —— 关闭垂直滚动条、禁用滚轮、且可见项数只在下拉『创建时』按当时项数算一次。在 windows11 原生样式下项目实际更高(原生内边距叠加样式表 padding)，弹出高度就只装得下 N-1 项；而滚动条和滚轮又都被关掉，那一项便永远够不着，看起来就是『丢了一项』(Linux/Fusion 装得下，所以此前一直复现不出)
- 修复一：每次弹出前按当前真实项数重算可见项数；弹出后若仍装不下，自动打开滚动条兜底，保证任何一项都能被看到和选到
- 修复二：滚轮不再一律拦截 —— 确实可滚动时放行(mac 保持原来一律忽略的行为不变)
- 修复三：语言与主题两个下拉都加上项目完整性自愈 —— 每次界面重译后校验，一旦项数或身份值不符，自动重建为完整项并保留当前选择(此前只有语言下拉有这道保险)
- Mac 分支一字未动：尺寸重算与滚动兜底都在 mac 上直接跳过，弹出仍走系统原生(经伪装 darwin 验证)；6.11 与 6.4.2 两套 Qt 反复切换 16 次后语言恒 2 项、主题恒 3 项，无崩溃

- *Root cause: the popup list did three conflicting things at once — the vertical scrollbar was disabled, the mouse wheel was blocked, and the visible-item count was computed only once when the dropdown was created. Under the native windows11 style the items are taller (native padding on top of the stylesheet padding), so the popup only fits N-1 items; with both the scrollbar and the wheel disabled, that last item became permanently unreachable and looked like it had disappeared (everything fits under Linux/Fusion, which is why this never reproduced in testing)*
- *Fix 1: the visible-item count is recomputed from the real item count before every popup, and if items still do not fit the scrollbar is enabled afterwards as a fallback so every item can be seen and selected*
- *Fix 2: the mouse wheel is no longer blocked unconditionally — it now scrolls when the list actually can scroll (mac keeps its previous always-ignore behaviour)*
- *Fix 3: both the language and theme dropdowns now self-heal their item lists — after every UI retranslation the items are validated and rebuilt with the current selection preserved if anything is missing (previously only the language dropdown had this safeguard)*
- *The mac branch is untouched: the resizing and scroll fallback are skipped entirely on mac and popups still use the native system look (verified with a simulated-darwin run); after 16 consecutive switches on both Qt 6.11 and 6.4.2 the language dropdown stays at 2 items and the theme dropdown at 3, with no crashes*

## v2.15.8 — 2026-07-27

**修复 Windows 切浅色后下拉弹出仍是黑底、以及由此造成的『下拉少一项』（两者是同一个 Bug）**

*Fixed the dropdown popup staying black after switching to the light theme on Windows, and the resulting phantom missing item (both were the same bug)*

- 根因：下拉弹出容器的背景色只在下拉『创建时』设过一次，切换主题时从不更新。所以从深色切到浅色后，弹出容器仍是黑底，而项目文字已随浅色主题变成深色 —— 深字配黑底就完全看不见了
- 这同时解释了『反复改几次就丢一项』：项目其实一个都没丢（实测反复切换 12 次后语言仍是 2 项、主题仍是 3 项），只是没被选中的那些项深字黑底看不见；被选中那项因为有蓝色高亮加白字所以还看得见，于是看起来就像少了一项
- 修复：把弹出容器配色抽成与主样式表共用的函数，并在主题热切换时刷新主窗与所有已打开弹窗内的全部下拉 —— 深色 #2d2d30、浅色 #ffffff，与下拉闭合框配色一致
- Mac 分支一字未动：mac 的下拉弹出走系统原生、不设任何样式，热切换时也不会调用这个刷新（经伪装 darwin 验证）；6.11 与 6.4.2 两套 Qt 反复切换均无崩溃

- *Root cause: the dropdown popup container's background colour was set only once, when the dropdown was created, and never updated on a theme change. After switching from dark to light the popup container was still black while the item text had followed the light theme and turned dark — dark text on a black background is simply invisible*
- *This also explains the reported item loss after repeated changes: no item was ever removed (after 12 consecutive switches the language dropdown still had 2 items and the theme dropdown 3). The unselected items were merely invisible, while the selected one stayed visible thanks to its blue highlight and white text, making it look like an item had gone missing*
- *Fix: the popup container colours were extracted into a function shared with the main stylesheet, and the theme hot-switch now refreshes every dropdown in the main window and in any open dialog — #2d2d30 in dark, #ffffff in light, matching the dropdown closed-box*
- *The mac branch is untouched: mac dropdown popups use the native system look with no stylesheet, and the hot-switch never calls this refresh on mac (verified with a simulated-darwin run); repeated switching on both Qt 6.11 and 6.4.2 produces no crashes*

## v2.15.7 — 2026-07-27

**修复 Windows 深色切浅色后按钮图标/文字看不见：切主题时重新生成图标**

*Fixed invisible button icons and text on Windows after switching dark to light: icons are now regenerated on theme change*

- 找到根因：按钮图标是按当前深浅现场渲染的 SVG（浅色主题用深色 #1f1f22，深色主题用浅色 #e8e8e8）。mac 分支在切主题时一直会重新生成图标，非 mac 分支却漏了这一步——从深色切到浅色后，图标仍是浅灰色，落在浅底按钮上就看不见了
- 修复：非 mac 的主题热切换现在同样调用图标重生成，并且连已打开的设置窗/弹窗里的按钮图标也一并按新深浅重新着色
- 已用实际像素颜色验证：深色主题下图标为 #e8e8e8、浅色主题下为 #1f1f22，按钮文字色也随主题正确切换（深色 #dcdcdc / 浅色 #1f1f22）
- Mac 分支一字未动：mac 仍走 _mac_hybrid_qss，既不重建样式对象也不调用非 mac 的调色板函数（经伪装 darwin 验证）；6.11 与 6.4.2 两套 Qt 连切 5 次均无崩溃，设置窗与主窗始终一致

- *Root cause: button icons are SVGs rendered on the fly for the current theme (dark #1f1f22 for the light theme, light #e8e8e8 for the dark theme). The mac branch has always regenerated icons on a theme change, but the non-mac branch skipped this step — after switching from dark to light the icons stayed light grey and became invisible on light buttons*
- *Fix: the non-mac theme hot-switch now regenerates icons too, including button icons inside any already-open Settings dialog or popup*
- *Verified by sampling actual pixel colors: icons are #e8e8e8 in the dark theme and #1f1f22 in the light theme, and button text follows the theme correctly (#dcdcdc dark / #1f1f22 light)*
- *The mac branch is untouched: mac still uses _mac_hybrid_qss and neither rebuilds the style object nor calls the non-mac palette helper (verified with a simulated-darwin run); five consecutive switches on both Qt 6.11 and 6.4.2 produce no crashes and the Settings dialog stays identical to the main window*

## v2.15.6 — 2026-07-27

**修复 Windows 切换深浅色后仍错乱：热切换时重建样式对象并全量重绘（Mac 不受影响）**

*Fixed Windows still breaking after a light/dark switch: the style object is now rebuilt and everything repolished on switch (Mac unaffected)*

- 找到『重启才好』的最后一块拼图：启动时的顺序是 设调色板 -> app.setStyle() 新建样式对象 -> 再设 colorScheme -> 建窗口。原生样式(windows11)在【创建那一刻】确定深浅状态，之后再改 colorScheme，这个已存在的样式对象不会彻底重绘——所以只有重启(重新创建样式对象)才正常
- 修复：主题热切换时完整复刻启动顺序——重设调色板、重建样式对象、在其后再设一次调色板与 colorScheme(setStyle 会把调色板重置为样式标准值，必须在其后补回)，最后重套混合样式表
- 新增全量重新 polish：仅调 update() 不足以让已经 polish 过的控件按新样式与调色板重绘，现在对所有控件执行 unpolish/polish，强制彻底刷新
- Mac 分支一字未动：mac 仍走 _mac_hybrid_qss，既不重建样式对象也不调用 _apply_win_palette(经伪装 darwin 验证)；6.11 与 6.4.2 两套 Qt 反复切换 5 次均无崩溃，样式引擎保持不变、调色板随主题正确变化、设置窗与主窗始终一致

- *Found the last piece of the "only a restart fixes it" puzzle: startup does palette -> app.setStyle() creating a fresh style object -> colorScheme -> build window. The native windows11 style fixes its light/dark state at the moment it is created, so changing colorScheme afterwards never fully repaints the existing style object — which is exactly why only a restart looked right*
- *Fix: the theme hot-switch now mirrors the startup sequence exactly — set the palette, rebuild the style object, then set the palette and colorScheme again afterwards (setStyle resets the palette to the style's standard one, so it must be restored), and finally re-apply the hybrid stylesheet*
- *Added a full repolish: calling update() alone does not make already-polished widgets repaint under the new style and palette, so unpolish/polish is now run across all widgets to force a complete refresh*
- *The mac branch is untouched: mac still uses _mac_hybrid_qss and neither rebuilds the style object nor calls _apply_win_palette (verified with a simulated-darwin run); on both Qt 6.11 and 6.4.2, five consecutive switches produce no crashes, the style engine stays the same, the palette tracks the theme, and the Settings dialog stays identical to the main window*

## v2.15.5 — 2026-07-26

**真正修复 Windows 改深浅色后错乱 + 复选框没边线（Mac 不受影响）**

*Actually fixed Windows corruption after changing light/dark + checkboxes with no border (Mac unaffected)*

- 找到真正根因：启动时非 mac 会给 app 设一套深/浅调色板，但主题热切换(apply_theme)在改用混合方案后漏掉了这一步——原生控件(复选框边线、背景)保留启动时的旧调色板，于是出现『打开好、改主题坏、重启又好』；现在启动与热切换共用同一个 _apply_win_palette，切主题时调色板同步更新
- 修复复选框小方块没有边线：复选框改为完全走原生(由 setColorScheme+调色板驱动)——移除了窗口级样式表里的 QCheckBox 规则，以及每个复选框的内联样式；只要给复选框设任何样式表，windows11 引擎就会对它整体接管渲染而丢失原生边线(测试程序的混合模式正是不设 QCheckBox 规则才正确)
- 两条修复合力：调色板同步 + 复选框纯原生，改主题后复选框、按钮、下拉、背景都跟着正确变深浅
- Mac 分支一字未动：mac 继续走 _mac_hybrid_qss，且 _apply_win_palette 仅在非 mac 调用(经伪装 darwin 验证 mac 路径不碰它)；6.11 与 6.4.2 两套 Qt 环境反复切换均无崩溃、设置窗与主窗始终一致

- *Found the true root cause: at startup the non-mac path sets a full dark/light palette on the app, but the theme hot-switch (apply_theme) dropped this step when it moved to the hybrid approach — native controls (checkbox borders, backgrounds) kept the startup palette, producing "fine on open, broken on change, fine after restart"; startup and hot-switch now share the same _apply_win_palette so the palette updates on every theme change*
- *Fixed checkboxes having no border: checkboxes are now fully native (driven by setColorScheme plus the palette) — the QCheckBox rule was removed from the window stylesheet along with each checkbox's inline style; setting any stylesheet on a checkbox makes the windows11 engine take over its rendering and lose the native border (the test program's hybrid mode was correct precisely because it set no QCheckBox rule)*
- *The two fixes together: palette sync plus fully-native checkboxes mean that after a theme change the checkboxes, buttons, dropdowns and backgrounds all switch light/dark correctly*
- *The mac branch is untouched: mac still uses _mac_hybrid_qss, and _apply_win_palette is called only on non-mac (verified via a simulated-darwin run that the mac path never touches it); repeated switching on both Qt 6.11 and 6.4.2 shows no crashes and the Settings dialog stays identical to the main window*

## v2.15.4 — 2026-07-26

**修复 Windows 在设置里改深浅色后界面错乱（设置窗改为与主窗完全一致，Mac 不受影响）**

*Fixed Windows UI corruption after changing light/dark in Settings (Settings dialog now identical to the main window; Mac unaffected)*

- 根因找到(靠『刚开好、改主题坏、重启又好』这条线索锁定)：设置窗的下拉/按钮样式函数只有 mac 分支、没有 Windows 分支，改主题时它给设置窗套上一张残缺样式表(只有下拉弹出、没有下拉闭合框和按钮)，覆盖了主窗正确的混合样式，于是整个界面错乱；重启因设置窗未打开而恢复正常
- 修复：非 mac 时设置窗直接套用主窗的混合样式(_win_hybrid_qss)，与主界面一模一样，且只有一个深浅真相来源，改主题不再错乱
- mac 分支一字未动：mac 继续走原有的 _mac_hybrid_qss，效果完全不变(经伪装 darwin 验证 mac 代码路径原样执行)
- 6.11 与 6.4.2 两套 Qt 环境均验证：反复切换深浅色后，设置窗样式始终与主窗完全一致，下拉正常、无崩溃

- *Root cause (pinned down by the clue "fine on open, breaks on theme change, fine again after restart"): the Settings dialog's dropdown/button style function had only a mac branch and no Windows branch, so changing the theme applied an incomplete stylesheet (dropdown popup only, no closed-box or buttons) that overrode the main window's correct hybrid style and corrupted the whole UI; a restart looked fine because the Settings dialog was not open*
- *Fix: on non-mac the Settings dialog now applies the main window's hybrid stylesheet (_win_hybrid_qss) directly, making it identical to the main UI with a single source of truth for light/dark, so changing the theme no longer corrupts it*
- *The mac branch is untouched: mac still uses the existing _mac_hybrid_qss and is completely unchanged (verified via a simulated-darwin run that the mac code path executes as before)*
- *Verified on both Qt 6.11 and 6.4.2: after repeated light/dark switches the Settings dialog stylesheet stays identical to the main window, dropdowns work, no crashes*

## v2.15.3 — 2026-07-26

**Windows/Linux 改用混合主题方案（照搬 mac 成功模式）：深浅切换正常、复选框原生、按钮下拉自绘保持**

*Windows/Linux switched to the hybrid theme approach (mirroring the working mac model): correct dark/light, native checkboxes, self-drawn buttons and dropdowns preserved*

- 彻底重做 Windows/Linux 的深浅主题：改用与 mac 同构的混合方案——用 Qt 的 setColorScheme 驱动系统原生控件(复选框、滚动条、窗口底色随之正确变深浅)，样式表只绘制按钮、下拉闭合框、下拉弹出(蓝色高亮)、滑杆、状态栏，不再碰复选框指示器与滚动条
- 解决 Win11 深浅切换后按钮字太浅、复选框没边线/勾选变实心：这些都源于旧方案用样式表强行涂色与 windows11 原生引擎打架；混合方案让原生引擎自己画复选框，样式表只管按钮/下拉，两不相扰
- 下拉弹出的蓝色高亮(#0e639c)+白字效果完整保留，深浅两主题都在
- 此改动仅影响非 mac 路径；mac(Intel/Silicon)继续用原有的 _mac_hybrid_qss，效果完全不变

- *Reworked Windows/Linux dark/light theming to mirror mac's hybrid approach: Qt's setColorScheme drives the native controls (checkboxes, scrollbars and window background change light/dark correctly), while the stylesheet only draws buttons, the dropdown closed-box, the dropdown popup (blue highlight), sliders and the status bar — it no longer touches the checkbox indicator or scrollbar*
- *Fixes pale button text and missing checkbox borders / solid-fill checkmarks on Win11 after a theme switch: these came from the old approach fighting the native windows11 engine with stylesheet colors; the hybrid approach lets the native engine draw checkboxes while the stylesheet handles only buttons and dropdowns*
- *The dropdown popup's blue highlight (#0e639c) with white text is fully preserved in both light and dark themes*
- *This change affects only the non-mac path; mac (Intel/Silicon) continues to use the existing _mac_hybrid_qss and is completely unchanged*

## v2.15.2 — 2026-07-26

**Win11 深浅切换按钮字太浅/复选框实心 · 语言下拉丢项 两个老问题再修（不影响 Mac）**

*Win11 dark/light: pale button text / solid checkbox · language dropdown losing an item — both re-fixed (Mac untouched)*

- 撤销上一版给复选框指示器加的自绘样式：它在 Win11 上让勾选态变成实心方块(SVG 对勾在 windows11 原生样式下不渲染)。现改为让 Windows 原生样式自己画正确的对勾
- 修复 Win11 浅色主题下按钮文字太浅看不清：跟随系统且 Qt 返回未知色彩方案时，之前默认按深色处理，导致浅底配浅字；现在未知时保守当作浅色，只有明确深色才用深色配色
- 语言下拉丢项(中文项消失)彻底根治：改用 userData 存身份值让显示文字与身份解耦(读 currentData 而非文字)，并在每次界面重译后加自愈保险——若因任何原因少了项，自动重建为『中文/English US』两项并保留当前选择
- 以上仅改动非 Mac 路径与共享样式表，Mac(Intel/Silicon)的原生混合方案完全未动，效果不受影响

- *Reverted the custom checkbox-indicator styling added last version: on Win11 it turned the checked state into a solid square (the SVG check does not render under the native windows11 style). The native Windows style now draws the correct checkmark*
- *Fixed pale, unreadable button text in light theme on Win11: when following the system and Qt reported an unknown color scheme, it previously defaulted to dark, producing light text on a light background; unknown is now treated as light, and only an explicit dark scheme uses dark colors*
- *Definitively fixed the language dropdown losing its Chinese item: it now stores identity values in userData (decoupled from display text, read via currentData rather than text), plus a self-healing guard after every UI retranslation that rebuilds the two items (Chinese / English US) and keeps the current selection if any item goes missing*
- *These changes touch only the non-Mac path and the shared stylesheet; the Mac (Intel/Silicon) native hybrid approach is entirely untouched and unaffected*

## v2.15.1 — 2026-07-26

**多风格换行误判修复 · 选区/卡拉OK统一白字 · 日志写入修复 · Win11深浅复选框 · 被动选区朗读报错**

*Multi-style newline misdetection fix · unified white text for selection/karaoke · log-write fix · Win11 dark/light checkbox · passive-selection speak error*

- 修复普通翻译时原文含换行被误判为多风格分区：此前用译文第一个空行作直译区/多风格区分界，导致原文如『下载(换行)计算机』译成『Download(空行)computer』时 computer 被误划入多风格区变灰。现在只有多风格模式真正开启时才做空行分界，普通模式绝不分区
- 文字颜色统一：原文区/译文区只要有选区或卡拉OK效果，被覆盖的字一律显示白色——不论深浅主题、不论直译区黑字还是多风格灰字、不论主动蓝色还是被动灰色背景；未被覆盖的多风格区仍是灰字
- 修复朗读时到达处的青蓝卡拉OK效果+白字有时不覆盖：三种背景格式(青蓝已读/蓝选区/灰联动)现都显式带白字前景，覆盖一致
- 修复朗读被动灰色联动区报错『cannot access local variable text』：该分支里 len(text) 用在了 text 赋值之前，现已调整顺序
- 修复日志文件一直为空(谎报写入)：异常钩子调用的是不存在的 _log 函数，写入在 try 中被静默吞掉，却仍提示已记录；改为正确的 _log_error，日志真正写入(全平台，非仅 Silicon)
- 修复 Win11 深浅切换后复选框没有边框：给复选框指示器加了显式样式(边框+背景+白色对勾 SVG)，不再依赖 windows11 原生样式在调色板切换时重绘
- 进度滑杆拖到最左的卡拉OK边界问题与朗读到达覆盖逻辑一并改良

- *Fixed normal translations with a newline in the source being misread as a multi-style split: the first blank line in the output was used as the direct/multi-style boundary, so a source like 'download(newline)computer' translated to 'Download(blank line)computer' had computer wrongly grayed into the multi-style area. The blank-line split now only happens when multi-style mode is actually on; normal mode never splits*
- *Unified text color: in both the source and target areas, any text under a selection or karaoke effect now shows white — regardless of light/dark theme, direct-area black text or multi-style gray text, and active blue or passive gray background; uncovered multi-style text stays gray*
- *Fixed the teal karaoke highlight + white text sometimes not covering during playback: all three background formats (teal read / blue selection / gray link) now explicitly carry a white foreground for consistent coverage*
- *Fixed 'cannot access local variable text' when speaking the passive gray link region: that branch used len(text) before text was assigned; the order is now corrected*
- *Fixed the log file always being empty (falsely reporting a write): the exception hook called a non-existent _log function, so the write was silently swallowed in a try while still claiming it logged; switched to the correct _log_error so the log actually writes (all platforms, not just Silicon)*
- *Fixed checkboxes losing their border after a light/dark switch on Win11: the checkbox indicator now has explicit styling (border, background and a white check SVG) instead of relying on the windows11 native style to repaint on a palette change*
- *Improved the karaoke boundary when the progress slider is dragged fully left, alongside the playback coverage logic*

## v2.15.0 — 2026-07-25

**修复 macOS Apple Silicon：不再弹新窗、深浅色正常 · 按架构分 Qt 版本**

*Fixed macOS Apple Silicon: no more popup windows, correct light/dark · Qt version per architecture*

- 修复 Apple Silicon 打包版生成朗读音频时不断弹出新 App 窗口：torch/Kokoro 用 multiprocessing 起子进程，冻结的 app 里未调用 freeze_support() 会让每个子进程重新启动整个程序；现在入口最前调用 multiprocessing.freeze_support()
- 修复 Apple Silicon 界面颜色混乱、深色模式按钮全白、切换深浅无反应：mac 深浅之前只靠 pyobjc(AppKit)驱动，Silicon+新系统上失效；现改为优先用 Qt 原生 setColorScheme/colorScheme(6.5+，Apple Silicon 的 6.11 可靠且不依赖 pyobjc)，老 Intel(6.4.2)自动回退 AppKit
- 按架构分 Qt 版本：Apple Silicon 用 PyQt6 6.11.x(最低 macOS 12.0)，Intel 保持 6.4.2(最低 Big Sur 11.0)；Windows 与 Linux 用 6.11.x。构建脚本按 uname -m 自动选择版本与最低系统
- 构建脚本两架构都装 pyobjc-framework-Cocoa，作为标题栏等系统装饰深浅同步的辅助

- *Fixed the Apple Silicon packaged build spawning new app windows while generating audio: torch/Kokoro use multiprocessing to start workers, and in a frozen app without freeze_support() each worker relaunches the whole program; multiprocessing.freeze_support() is now called first thing at the entry point*
- *Fixed Apple Silicon UI color chaos, all-white buttons in dark mode, and light/dark switching doing nothing: mac dark/light previously relied solely on pyobjc (AppKit), which fails on Silicon with newer systems; it now prefers Qt's native setColorScheme/colorScheme (6.5+, reliable on Apple Silicon's 6.11 without pyobjc) and falls back to AppKit on older Intel (6.4.2)*
- *Qt version per architecture: Apple Silicon uses PyQt6 6.11.x (min macOS 12.0), Intel stays on 6.4.2 (min Big Sur 11.0); Windows and Linux use 6.11.x. The build script picks the version and minimum system automatically from uname -m*
- *The build script installs pyobjc-framework-Cocoa on both architectures, as an aid for syncing system decorations like the title bar to light/dark*

## v2.14.9 — 2026-07-25

**滚动条回归系统原生 · 语言下拉丢项/主题错乱/卡拉OK字色/暂停失效/滚轮误改 五项修复 · 新增 Linux 构建脚本**

*Scrollbars back to OS-native · five fixes (language dropdown, theme colors, karaoke text, pause, wheel) · new Linux build script*

- 滚动条不再强加任何自定义样式，各平台一律用系统原生：Win11 原生 Fluent 圆角、Win10 原生 Vista 直角、macOS 原生——与主窗风格统一
- 修复 Windows 版语言下拉在中英切换后丢失中文项：语言项是身份值(用于判断当前语言)，不应被界面重译改写，现标记为不参与重译
- 修复深浅主题互换时设置窗下拉/按钮颜色错乱：设置窗缺少主题热切换回调，切主题时保留了旧配色；现补上回调，按新深浅重建自绘样式
- 卡拉OK字幕字色统一为白色：多风格区原本灰字，被卡拉OK/选区背景覆盖的部分现一律显示白字，与直译区一致；未被覆盖的灰区保持灰字
- 修复全选文字并有卡拉OK时暂停键失效：全选朗读时选区仍在，暂停点击被误判为新朗读请求而重启；现同段朗读时优先按暂停/继续处理，只有真正不同的新选区才重启
- 修复设置窗内用滚轮滚动内容时误改下拉选项：下拉框未获焦点时不再响应滚轮，把滚动交给页面
- 新增 Linux 一键构建脚本 Build Linux.sh：PyInstaller 打包，产物为 dist/Linux-x64/ 下的可执行目录与 tar.gz；建议在较老发行版(如 Ubuntu 20.04)上编译以保 glibc 向下兼容

- *Scrollbars no longer force any custom style; every platform uses its native default: Win11 native Fluent rounded, Win10 native Vista square, macOS native — consistent with the main window*
- *Fixed the Windows language dropdown losing its Chinese item after switching languages: the language items are identity values (used to determine the current language) and must not be rewritten by UI retranslation; they are now marked to skip it*
- *Fixed dropdown and button colors going wrong in the Settings dialog when switching light/dark themes: the dialog lacked a theme-refresh callback and kept its old colors; the callback is now added and rebuilds the styling for the new theme*
- *Karaoke subtitle text is now uniformly white: the multi-style area was gray, and the parts covered by the karaoke/selection background now show white text like the direct-translation area; uncovered gray regions stay gray*
- *Fixed the pause button failing when playing a full-text selection with karaoke: the selection stays active during playback, so a pause click was misread as a new play request and restarted; pausing/resuming now takes priority for the same spoken span, and only a genuinely different selection restarts*
- *Fixed the scroll wheel accidentally changing dropdown values while scrolling the Settings dialog: dropdowns no longer respond to the wheel unless focused, passing the scroll to the page*
- *Added a one-command Linux build script (Build Linux.sh): PyInstaller packaging producing an executable folder and a tar.gz under dist/Linux-x64/; build on an older distro (e.g. Ubuntu 20.04) for forward glibc compatibility*

## v2.14.8 — 2026-07-25

**自绘滚动条配色改进：Win10 深浅主题下都清晰可见**

*Custom scrollbar colors improved: clearly visible on Win10 in both light and dark themes*

- 修复 Win10 上自绘圆角滚动条看不清：此前滑块用半透明灰，对比依赖底层背景色，Win10 背景不同就与轨道糊在一起
- 改用不透明实色并主动画一层浅色圆角轨道，滑块与轨道之间保证足够亮度差；按深浅主题自动选配色，浅色主题用中深灰滑块、深色主题用中灰滑块
- 各类背景(浅色/深色/中灰)下实测滑块与轨道亮度差均 ≥80，清晰可辨

- *Fixed the custom rounded scrollbar being hard to see on Win10: the slider previously used a semi-transparent gray whose contrast depended on the underlying background, so on Win10's different background it blended into the track*
- *Now uses opaque solid colors and draws a light rounded track underneath, guaranteeing enough brightness difference between slider and track; colors are chosen automatically per light/dark theme (a mid-dark gray slider on light themes, a mid gray slider on dark themes)*
- *Measured slider-vs-track brightness difference is >=80 across light, dark and mid-gray backgrounds — clearly distinguishable*

## v2.14.7 — 2026-07-25

**修复 DeepSeek 模型停用导致翻译失败 · Win10 滚动条改自绘圆角 · 构建脚本消噪**

*Fixed DeepSeek translation failure from model retirement · Win10 scrollbars now custom-drawn round · quieter build scripts*

- 修复 DeepSeek 翻译报 400：deepseek-chat 模型名已于 2026-07-24 15:59 UTC 停用，改用官方新名 deepseek-v4-flash（原 deepseek-chat 对应的经济档）
- 翻译任务显式关闭 DeepSeek 的思考模式（v4-flash 默认开启思考，会平添延迟与费用），保持与原来一致的快速非思考行为
- Win10 滚动条改用自绘方案（QProxyStyle 直接用 QPainter 画圆角胶囊）：此前给滚动条套 Fusion 样式在实机上仍是直角，因为 Qt 新版的 windows11 引擎会忽略 QSS 圆角、且样式表回退到平台样式；自绘完全绕开样式引擎与 QSS 的层叠，任何 Qt 版本都画出一致圆角
- 构建脚本消除 en_core_web_sm 的无害报错：该 spaCy 模型不在 PyPI（走 GitHub Releases），镜像返回 0 字节占位导致 Wheel invalid 报错；现改为先检查是否已安装，已装则跳过，未装才从官方地址安装

- *Fixed DeepSeek translation returning HTTP 400: the deepseek-chat model name was retired on 2026-07-24 15:59 UTC, replaced with the official new name deepseek-v4-flash (the economical tier the old deepseek-chat mapped to)*
- *Thinking mode is now explicitly disabled for DeepSeek translation (v4-flash enables thinking by default, adding latency and cost), preserving the previous fast non-thinking behaviour*
- *Win10 scrollbars are now custom-drawn (a QProxyStyle painting rounded capsules directly with QPainter): applying the Fusion style still rendered square on real machines because Qt's newer windows11 engine ignores QSS rounding and the stylesheet fell back to the platform style; custom drawing bypasses the style engine and QSS entirely for consistent rounded corners on any Qt version*
- *Build scripts no longer print the harmless en_core_web_sm error: that spaCy model is not on PyPI (it ships via GitHub Releases) and mirrors return a 0-byte placeholder that fails wheel validation; the scripts now check whether it is already installed, skip if so, and otherwise install from the official URL*

## v2.14.6 — 2026-07-25

**修复 mac 进设置窗闪退（NameError: lv）**

*Fixed macOS crash when opening Settings (NameError: lv)*

- 真因找到：v2.14.3 重写下拉弹出函数时，旧函数的尾部代码被遗落在函数体外，成了缩进错误的游离代码块，其中引用的 lv 变量已不在作用域内
- 这段游离代码恰好是 macOS 专属分支(弹出列表走系统原生透明背景)，所以只在 mac 上触发、Linux 沙盒测不出来——这也是前两版反复没修对的原因
- 已删除游离代码，并把 macOS 原生弹出处理放回它应在的函数内（lv 有效作用域）
- 顺带全量扫描了模块结构，确认没有其它同类遗留代码块
- 上一版加的全局异常钩子发挥了作用：正是它把静默闪退变成了可读的错误提示，才得以一次定位

- *Real cause found: when the dropdown popup function was rewritten in v2.14.3, the tail of the old function was left outside the function body as a mis-indented orphaned block, referencing the variable lv which was no longer in scope*
- *That orphaned block happened to be the macOS-only branch (native translucent popup), so it fired only on Mac and could not be reproduced in the Linux sandbox — which is why the two previous attempts fixed the wrong thing*
- *The orphaned block has been removed and the macOS native popup handling restored inside the function where lv is actually in scope*
- *Also scanned the whole module structure to confirm no other leftover blocks of this kind exist*
- *The global exception hook added in the previous version did its job: it turned a silent crash into a readable error message, which is what made this diagnosis possible*

## v2.14.5 — 2026-07-25

**紧急修复：一点设置就闪退（槽函数异常导致 PyQt 直接中止）**

*Critical fix: crash when touching Settings (slot exception aborting PyQt)*

- 找到闪退真因：崩溃栈显示 pyqt6_err_print → QMessageLogger::fatal → qAbort，且发生在按钮点击(QAbstractButton::mouseReleaseEvent)之后——这是 PyQt6 的行为：槽函数里任何未被捕获的 Python 异常都会让程序直接 abort()，而不是像普通异常那样被忽略
- 新增全局异常钩子：槽函数抛异常时改为写入日志并弹窗提示，程序继续运行，不再闪退；日志中以 [UNCAUGHT] 标记，便于定位
- 『保持程序置顶』复选框的响应函数此前完全没有异常保护，正是崩溃栈指向的按钮点击路径，现已加上
- 置顶收尾函数改为局部导入 Qt 并整体保护，避免作用域问题引发异常
- 全流程回归通过：设置窗四个按钮逐一点击(含此前必崩的『导出日志』)、置顶勾选与取消、三个下拉弹出、关闭收尾，均无闪退

- *Found the real cause: the crash report shows pyqt6_err_print → QMessageLogger::fatal → qAbort right after a button click (QAbstractButton::mouseReleaseEvent). This is PyQt6 behaviour — any uncaught Python exception inside a slot makes the program abort() outright rather than being ignored as a normal exception would be*
- *Added a global exception hook: an exception raised in a slot is now logged and shown in a dialog while the program keeps running, instead of crashing; entries are tagged [UNCAUGHT] in the log for easy tracing*
- *The Keep Window on Top checkbox handler had no exception protection at all — precisely the button-click path the crash stack pointed to — and is now guarded*
- *The always-on-top flush function now imports Qt locally and is fully guarded, removing any scope-related failure*
- *Full regression passed: every Settings button clicked in turn (including Export Log, which previously killed the process), on-top toggled on and off, all three dropdowns opened, and the dialog closed — no crashes*

## v2.14.4 — 2026-07-25

**紧急修复：进入设置即闪退（滚动条样式对象悬空指针）**

*Critical fix: crash when opening Settings (dangling scrollbar style pointer)*

- 修复上一版一点设置就闪退：QWidget.setStyle() 并不接管样式对象的所有权，上版把 Fusion 样式存成应用的 Python 属性以为能保住它，但 Qt 退出时仍会销毁该对象，而滚动条还指向它——悬空指针导致段错误闪退
- 改为给样式对象设置真正的 Qt 父对象，生命周期交由 Qt 对象树管理，杜绝悬空
- 事件过滤器加固：只在窗口 Show 时处理并延后一拍执行，避免控件尚未构造完成或已销毁时被访问；对已销毁控件静默跳过
- 滚动条样式改为按需设置（已是目标样式则不重复设），减少无谓重绘

- *Fixed the previous version crashing as soon as Settings was touched: QWidget.setStyle() does not take ownership of the style object, and storing the Fusion style as a Python attribute on the application did not keep it alive — Qt still destroyed it at shutdown while scrollbars were pointing at it, producing a dangling pointer and a segmentation fault*
- *The style object is now given a real Qt parent so its lifetime is managed by the Qt object tree, eliminating the dangling pointer*
- *Hardened the event filter: it now acts only on window Show events and defers by one tick, avoiding access to widgets that are not yet fully constructed or have already been destroyed; destroyed widgets are skipped silently*
- *Scrollbar styling is now applied only when it differs from the current state, avoiding redundant repaints*

## v2.14.3 — 2026-07-24

**下拉弹出根治 · Win10 圆角滚动条(方案B) · 构建目录分平台 · 更新说明全部双语**

*Dropdown popup root fix · rounded scrollbars on Win10 (option B) · per-platform build folders · change log fully bilingual*

- 根治 Windows 下拉点击无效与文字截断：此前用猴子补丁改写 showPopup 并 setFixedWidth 永久锁死宽度——重复应用会层层包裹导致弹出失败，锁死的宽度又让后续任何重新布局都无法调整，越改越窄；现改为 minimumWidth 由 Qt 自行排版，可反复调用
- 弹出宽度计算补齐内边距/边框/勾号(此前只算纯文字宽，余量不足才出现 …)
- Win10 圆角滚动条改用方案B：只给滚动条套 Fusion 样式(其它控件外观不变)，绕开 Qt 6.7+ 的 windows11 引擎忽略 QSS 圆角的问题；通过全局事件过滤器覆盖主窗与所有对话框
- 中文朗读引擎下拉在中英切换后不再变窄、弹出项不再显示成 -On…：译后按新文字重算闭合框与弹出宽度，宽度只增不减
- 构建产物按平台分目录：dist/MacOS-Intel、MacOS-AppleSilicon(自动按 uname -m 判定)、Windows-x64-CPU、Windows-x64-GPU；文件名自描述如 EnglishCoach-2.14.3-Windows-x64-CPU.zip；各脚本只清理自己的目录，不再互相覆盖
- 程序置顶：首次运行显式写入未勾选状态，确保默认不置顶
- 历史更新说明翻译全部完成——87 条全部中英双语

- *Root fix for Windows dropdowns not opening and text being truncated: the previous code monkey-patched showPopup and used setFixedWidth, so re-applying the styling wrapped the patch in itself until the popup failed to open, while the locked width blocked every later relayout and made the popup progressively narrower; width is now set via minimumWidth and laid out by Qt, safe to re-apply*
- *Popup width calculation now accounts for padding, borders and the checkmark (it previously measured raw text only, leaving too little room and causing ellipses)*
- *Rounded scrollbars on Win10 now use option B: the Fusion style is applied to scrollbars only, leaving every other control's appearance untouched, which sidesteps the Qt 6.7+ windows11 engine ignoring QSS border-radius; a global event filter covers the main window and all dialogs*
- *The Chinese voice dropdown no longer narrows after switching between Chinese and English, and popup entries no longer show as -On…: widths are recalculated from the translated text and only ever grow*
- *Build artifacts are now organized per platform: dist/MacOS-Intel, MacOS-AppleSilicon (chosen automatically from uname -m), Windows-x64-CPU and Windows-x64-GPU, with self-describing names such as EnglishCoach-2.14.3-Windows-x64-CPU.zip; each script cleans only its own folder so platforms no longer overwrite each other*
- *Always-on-top: the unchecked state is written explicitly on first run so the default is genuinely off*
- *Historical change log translation is complete — all 87 entries are now bilingual*

## v2.14.2 — 2026-07-24

**使用说明补齐分发说明 · 大陆用户免 VPN 下载模型**

*Distribution details added to the guide · VPN-free model download in mainland China*

- 使用说明新增『哪些需要联网』与『中国大陆用户须知』两节，并说明无需安装 Python / 依赖 / conda、Linux 暂无预编译版、GPU 版仅适合 NVIDIA 机器
- 英文版使用说明补齐 System Requirements 整节（此前完全缺失），与中文版内容对齐
- 中国大陆免 VPN 下载 Kokoro 朗读模型：huggingface.co 大陆无法直连，现按系统区域自动改用 hf-mirror.com 公益镜像；可用 HF_ENDPOINT 环境变量自行覆盖

- *The user guide gained What Needs a Network Connection and Notes for Users in Mainland China sections, and now states that no Python, dependencies or conda are required, that Linux has no prebuilt binary yet, and that the GPU edition only suits NVIDIA machines*
- *The English guide gained a full System Requirements section (previously missing entirely), matching the Chinese version*
- *VPN-free Kokoro model download in mainland China: huggingface.co is not directly reachable there, so the app now falls back to the hf-mirror.com community mirror based on system locale; override it with the HF_ENDPOINT environment variable*

## v2.14.1 — 2026-07-24

**弹出窗宽度锚定悬停条 · 置顶失焦根治 · 对话框圆角滚动条**

*Popup width anchored to the hover bar · always-on-top focus fix · rounded scrollbars in dialogs*

- 设置窗下拉弹出列表宽度改在弹出瞬间按最长项内容重设——锚定 mac 悬停蓝条的自然宽度：引擎约占闭合框 27%、语言 18%、样式 16%，Windows 与 mac 一致
- 根治置顶导致的设置窗异常(v2.14.0 的两个 bug)：改 windowFlags 会销毁重建原生窗口——对对话框做会让它先缩小消失再出现，且 exec() 模态循环失效导致关闭后主界面按钮点了没反应；现在模态窗开着时只记录意图，等它关闭后再应用，全程不重建任何窗口
- 顺带修掉一个隐藏错误：上版弹出宽度代码引用了尚未定义的变量，整段被异常吞掉从未生效
- Win10 圆角滚动条补齐到所有对话框：设置窗/历史窗/文档窗会自设样式表覆盖应用级规则，现在各自带上圆角滚动条样式
- 继续翻译历史更新说明条目（累计 72/85 条已双语）

- *Settings dropdown popup width is now set at popup time from the longest item — anchored to the natural width of the macOS hover bar: the engine popup is about 27% of the closed box, language 18% and theme 16%, identical on Windows and macOS*
- *Root fix for the Settings dialog problems caused by always-on-top (two bugs from v2.14.0): changing windowFlags destroys and rebuilds the native window — doing it to the dialog made it shrink, vanish and reappear, and broke the exec() modal loop so main-window buttons stopped responding afterwards; the intent is now recorded while a modal dialog is open and applied once it closes, rebuilding no windows at all*
- *Also fixed a hidden error: last version's popup width code referenced a variable before it was defined, so the whole block was swallowed by the exception and never took effect*
- *Rounded scrollbars on Win10 extended to every dialog: Settings, History and document windows set their own stylesheets which override the application-level rule, so each now carries the rounded scrollbar styling itself*
- *Continued translating historical change log entries (72 of 85 now bilingual)*

## v2.14.0 — 2026-07-24

**下拉弹出窗收窄 · Win10 圆角滚动条 · Windows 置顶失焦修复**

*Narrower dropdown popups · rounded scrollbars on Win10 · Windows always-on-top focus fix*

- 设置窗下拉弹出列表大幅收窄：不再跟随被表单拉伸的闭合框，改为只按最长项内容定宽——引擎约占闭合框 25%，语言约 17%，样式约 14%
- Win10 及以下滚动条改为圆角胶囊，与 Win11 / macOS 观感一致；样式提升到应用级，设置窗、历史窗、说明窗等所有对话框一并生效（此前仅主窗有，对话框仍是直角）
- 修复 Windows 版勾选置顶时设置窗被压到主窗下面：Windows 的窗口层级变更由系统异步处理，同步归还焦点会被随后到达的置顶事件覆盖；改为立即归还后再延后两拍补两次，并让对话框跟随主窗一起置顶
- 继续翻译历史更新说明条目（累计 58/84 条已双语）

- *Settings dropdown popups made much narrower: instead of following the form-stretched closed box they size to their longest item — the engine popup is about 25% of the closed box, language about 17% and theme about 14%*
- *Scrollbars on Win10 and below are now rounded capsules matching Win11 and macOS; the styling moved to application level so Settings, History, User Guide and every other dialog gets it too (previously only the main window did, leaving dialogs square)*
- *Fixed the Settings dialog being pushed behind the main window when enabling always-on-top on Windows: Windows processes stacking changes asynchronously, so a synchronous focus restore was overridden by the arriving topmost event; focus is now restored immediately and again on two deferred ticks, and the dialog follows the main window's topmost state*
- *Continued translating historical change log entries (58 of 84 now bilingual)*

## v2.13.9 — 2026-07-23

**提示文字随语言切换 · Windows 下拉弹出窗修复 · 置顶不再抢焦点**

*Placeholders follow the UI language · Windows dropdown popup fixes · always-on-top no longer steals focus*

- 更改语言后，空的原文/译文区提示文字立即互换（通用化根治：遍历重译现在处理所有带 placeholder 的控件，不再只限单行输入框——原文/译文是多行编辑器，此前从未被覆盖）
- 修复 Windows 版设置窗下拉弹出列表过窄：补齐与主界面同款的按最长项定宽逻辑，弹出宽度与闭合框相当
- 修复 Windows 版语言/样式下拉弹出列表过高（二三项内容却有十来行）：可见项数=实际项数、按项滚动、关闭滚动条，与 macOS 表现一致
- 勾选置顶时主界面不再跳到设置窗前面：改用不抢焦点的显示方式，并把层级与焦点归还给正开着的对话框
- 引擎下拉闭合框再加宽 5 像素，弹出列表加宽 15 像素，其余位置不变
- 设置窗『保持程序置顶』与日志按钮行之间增加间距
- 继续翻译历史更新说明条目（累计 45/83 条已双语）

- *Placeholder text in the empty source and target areas now switches instantly with the UI language (generic root fix: the traversal retranslate handles every widget with a placeholder rather than single-line inputs only — the source and target areas are multi-line editors and had never been covered)*
- *Fixed the Settings dropdown popup being too narrow on Windows: it now uses the same longest-item width calculation as the main window, so the popup matches the closed box*
- *Fixed the language and theme dropdown popups being far too tall on Windows (about ten rows for two or three items): visible items now equal the actual item count, with per-item scrolling and scrollbars disabled, matching macOS*
- *Enabling always-on-top no longer makes the main window jump in front of the Settings dialog: the window is shown without stealing focus and the dialog gets its stacking order and focus back*
- *Engine dropdown closed box widened by another 5px and its popup by 15px, with everything else unchanged*
- *Added spacing between the Keep Window on Top checkbox and the log button row in Settings*
- *Continued translating historical change log entries (45 of 83 now bilingual)*

## v2.13.8 — 2026-07-23

**导出文件名统一 EC 前缀 · 导出文字钮空态灰化 · 文案与宽度微调**

*Unified EC filename prefix · export buttons dim when empty · wording and width tweaks*

- 所有导出文件名统一加 EC 前缀：日志 EC LT、翻译历史 EC TH、原文 EC OT 语言、译文 EC TT 语言、翻译后文件 EC TT 语言 … T
- 原文/译文区无文字时，导出文字按钮呈灰色不可点（与导出音频钮一致），有文字即恢复
- 引擎下拉框恢复上一版宽度（+10 像素），其余位置不变
- 英文文案改为标题式大小写：API Keys (Optional)、Multi-Style Translation、Keep Window on Top
- 继续翻译历史更新说明条目（累计 33/82 条已双语）

- *All export filenames now carry the EC prefix: log EC LT, translation history EC TH, source EC OT <lang>, target EC TT <lang>, translated file EC TT <lang> ... T*
- *Export text buttons are grayed out when their area has no text (matching the export audio buttons) and re-enable as soon as text appears*
- *Engine dropdown restored to the previous width (+10px) with everything else unchanged*
- *English wording switched to title case: API Keys (Optional), Multi-Style Translation, Keep Window on Top*
- *Continued translating historical change log entries (33 of 82 now bilingual)*

## v2.13.7 — 2026-07-22

**单词分区 · 导出日志 · 窗口置顶 · Windows 脚本修复**

*Word partition · Export log · Always on top · Windows script fix*

- 多风格模式下输入单个词：直译区只保留一个最优译法，其余备选全部归入多风格区
- 设置窗新增『导出日志』按钮（查看日志右侧、等宽同风格）：可选路径/文件名/格式，支持 .txt .log .md .json，纯标准库实现
- 设置窗新增『保持程序置顶』复选框（多风格与日志行之间），勾选后窗口始终在其它程序之上，设置持久保存、启动自动应用
- 修复 Windows 构建脚本乱码报错：脚本内中文注释在 GBK 控制台被误读，导致 setlocal/set 等语句失效、版本号提取失败（产物名丢失变成 .exe 与 -版本-windows.zip）；脚本改为纯 ASCII 并把 chcp 前置
- 原文/译文语言下拉各再加宽 10 像素（原文向左、译文向右），引擎下拉相应减 10，总宽守恒、交换钮居中不变
- Windows 版朗读速度滑杆左右滑槽统一为同色，与 macOS 一致

- *Single-word input in multi-style mode: the literal zone now keeps only one best translation, with all alternatives moved to the multi-style zone*
- *New Export Log button in Settings (right of View Log, same width and style): choose path, filename and format — .txt, .log, .md, .json — implemented with the standard library only*
- *New Keep window on top checkbox in Settings (between multi-style and the log row): keeps the window above other applications; the setting persists and is applied at startup*
- *Fixed Windows build script failures: Chinese comments inside the script were misread by GBK consoles, breaking setlocal/set statements and version extraction (producing nameless .exe and -version-windows.zip); scripts are now pure ASCII with chcp moved to the top*
- *Source/target language dropdowns widened by another 10px (source expands left, target right) with the engine dropdown narrowed by 10 — total width preserved, swap button stays centered*
- *Windows playback-speed slider grooves unified to the same color on both sides, matching macOS*

## v2.13.6 — 2026-07-21

**极简交换钮结构性居中 + 字幕/音频/文字生命周期铁律**

*Structural swap centering in minimal mode + karaoke/audio/text lifecycle rules*

- 极简界面交换钮居中根治：右组不再整体隐藏，改为隐藏其内容并在最右端放与极简钮完全镜像的隐形占位——左右结构对称，居中由布局数学保证，零校准、平台无关
- 字幕铁律：卡拉OK捆绑音频、依附文字，两者都在拖动进度条必有字幕（边界丢失自动从缓存恢复或按朗读范围重建）；任一不在必无字幕
- 文字清空钮：清文字同时该侧字幕（边界+高亮）同亡，音频缓存保留可继续播放
- 音频清空/文字变化作废音频时：该侧内存边界与卡拉OK高亮同步清除，杜绝旧字幕残留

- *Minimal-mode swap centering solved structurally: the right group's contents hide while an invisible mirror spacer sits at the far right, so centering is guaranteed by layout symmetry — zero calibration, platform-independent*
- *Karaoke iron rule: subtitles are bound to audio and attached to text — with both present, dragging the progress slider always shows karaoke (lost boundaries auto-restore from cache or rebuild from the spoken span); with either missing, karaoke never shows*
- *Text clear buttons: clearing text also kills that side's karaoke (boundaries + highlight) while the audio cache remains playable*
- *Audio clear / text-change invalidation: the side's in-memory boundaries and karaoke highlight are cleared together, eliminating stale-subtitle leftovers*

## v2.13.5 — 2026-07-20

**首次朗读无字幕修复 + 卡拉OK绑定朗读范围**

*First-play karaoke fix + karaoke bound to spoken range*

- 修复首次点朗读经常无卡拉OK：估算字幕需要音频时长，首播时时长常未加载导致估算被静默放弃且不重试；现在自动重试等待直到时长就绪
- 卡拉OK范围永远与朗读范围一一对应：朗读启动时记录实际朗读范围，估算字幕严格在该范围内铺设

- *Fixed karaoke often missing on first play: subtitle estimation needs audio duration, which is often not yet loaded on first playback — the estimator gave up silently without retrying; it now retries until duration is ready*
- *Karaoke range always maps one-to-one to the spoken range: the actual spoken span is recorded at TTS start and estimated subtitles are laid strictly within it*

## v2.13.4 — 2026-07-19

**灰色多风格区卡拉OK修复**

*Karaoke fix in the gray multi-style zone*

- 修复多风格灰色区无卡拉OK：灰字格式此前整体覆盖背景层，重写高亮分层——灰区内的蓝色选区/灰色联动/绿色卡拉OK背景照常显示
- 极简界面交换钮位置微调

- *Fixed missing karaoke in the gray multi-style zone: the gray-text format used to overwrite background layers; highlighting is now layered so blue selection, gray link and green karaoke backgrounds all render inside the gray zone*
- *Minor position tweak for the minimal-mode swap button*

## v2.13.3 — 2026-07-18

**打包版本号自动化 + 多风格朗读分区**

*Build version automation + multi-style TTS scoping*

- 修复打包产物版本号错误：三个构建脚本的版本改为自动从 APP_VERSION 提取，单一事实来源
- 多风格翻译朗读分区：无选区时点朗读译文只读直译区、卡拉OK只覆盖直译区；有选区仍按选区朗读

- *Fixed wrong packaged version numbers: all three build scripts now auto-extract the version from APP_VERSION — a single source of truth*
- *Multi-style TTS scoping: with no selection, reading the translation speaks only the literal section and karaoke covers it alone; with a selection the selection is read as before*

## v2.13.2 — 2026-07-17

**使用说明命令行文字样式统一**

*User guide command text style unified*

- 使用说明中去除隔离命令改为普通正文样式（去掉代码块底色与等宽字体），与其它文字一致

- *The quarantine-removal command in the user guide now uses plain body text style (code background and monospace font removed) to match surrounding text*

## v2.13.1 — 2026-07-16

**跟随系统昼夜切换修复 + 分割条居中吸附**

*Follow-system day/night fix + splitter center snap*

- 修复『跟随系统』在系统昼夜切换时样式不完全跟变：Qt 6.4 没有对应信号导致监听从未挂上，macOS 改用轮询兜底
- 原文/译文分割条新增居中吸附：拖到中央附近自动精准均分左右两栏

- *Fixed Follow System not fully switching on system day/night change: Qt 6.4 lacks the corresponding signal so the listener never attached; macOS now uses a polling fallback*
- *Source/target splitter now snaps to exact center when dragged near the middle*

## v2.13.0 — 2026-07-15

**界面精修里程碑：交换钮居中收官 + 三处细节**

*UI polish milestone: swap centering finale + three details*

- 原文/译文语言下拉框各加宽 10 像素，文字完整显示，交换钮居中不受影响
- 英文关于窗标题下补回一行空行
- 翻译历史窗背景跟随深浅主题：浅色模式下立即使用浅色背景

- *Source/target language dropdowns widened by 10px each for full text display; the swap button stays centered*
- *Restored a blank line under the English About title*
- *Translation history window background now follows the light/dark theme instantly*

## v2.12.29 — 2026-07-08

**交换钮精确居中(正常+极简)**

*Swap button precisely centered (normal + minimal)*

- 交换钮用右侧对称占位精确居中，正常与极简模式偏差均≈0
- 极简模式保留交换钮并居中

- *Swap button precisely centered via a symmetric right-side spacer; near-zero offset in both normal and minimal modes*
- *Minimal mode keeps the swap button centered*

## v2.12.28 — 2026-07-08

**交换钮真正居中 + 极简模式保留交换钮**

*Swap button truly centered + kept in minimal mode*

- 交换钮改用右侧对称占位实现精确居中(不再靠猜margin)，正常/极简模式偏差均≈0
- 极简模式保留交换钮并始终居中

- *Swap button now centered via a symmetric right-side spacer (no more guessed margins); near-zero offset in both normal and minimal modes*
- *Minimal mode keeps the swap button, always centered*

## v2.12.27 — 2026-07-08

**界面细节微调（引擎框/交换钮/滑杆圆球/文档英文化）**

*UI detail tweaks (engine box / swap button / slider knob / doc localization)*

- 英文环境设置窗『Google 云翻译 Key』显示为 Google Cloud Key
- 主界面最小宽度缩到880
- 交换钮组左移微调，趋向居中
- 两条朗读进度条与速度滑杆的圆球改回正圆、亮白色（去掉描边避免椭圆、灰色改白）
- 关于窗/更新说明窗标题英文化：About English Coach / Change Log
- 英文关于窗删除拼音副标题 Ying Yu Dao Shi
- 更新说明自此支持中英双语（按界面语言切换）

- *Settings 'Google Cloud Key' label now shows in English*
- *Main window minimum width reduced to 880*
- *Swap button group nudged left toward center*
- *Playback progress bars and speed slider knobs restored to true circles in bright white (removed border that caused ovals, gray changed to white)*
- *About / Change Log dialog titles localized: About English Coach / Change Log*
- *Removed the pinyin subtitle 'Ying Yu Dao Shi' from the English About page*
- *Change Log now supports bilingual display (follows UI language)*

## v2.12.10 — 2026-07-08

**删除设置窗多风格说明文字**

*Removed multi-style description text from Settings*

- 删除设置窗『（主译文 + 书面/口语/俚语/美英式等辅助译法）』说明文字

- *Removed the '(main translation + formal/casual/slang/US-UK style variants)' description text from Settings*

## v2.12.9 — 2026-07-08

**删除设置窗两段引擎说明文字**

*Removed two engine description paragraphs from Settings*

- 删除设置窗顶部『Google 免费、无需 Key…』和底部『提示：Google 免费无需 Key…』两段说明文字

- *Removed the top 'Google is free, no key required...' and bottom 'Tip: Google is free...' description paragraphs from Settings*

## v2.12.8 — 2026-07-08

**5处修复(含语言切换根治+下拉收口)**

*Five fixes (language switching root fix + dropdown width cleanup)*

- 主界面最小宽度加回到970
- 下拉宽度收口：清理设置窗输入框重复的sizePolicy叠加，主界面下拉恢复2.12.4干净公式(最长内容+52)
- 语言切换根治：改为遍历整个窗口所有控件按文字查表双向替换(中英)，覆盖按钮/气球提示/占位符/下拉项/两段说明，不再逐条点名遗漏；处理前后空格
- 设置窗『关闭』钮改蓝色主按钮样式(与关于窗一致)
- 修复极简界面往返后主窗最小宽度被改成770的bug(现与主窗970一致)

- *Main window minimum width restored to 970*
- *Dropdown width cleanup: removed duplicated sizePolicy stacking on Settings inputs; main window dropdowns restored to the clean 2.12.4 formula (longest content + 52)*
- *Language switching root fix: now traverses every widget in the window and swaps text via dictionary lookup in both directions (CN/EN), covering buttons, tooltips, placeholders, dropdown items and description paragraphs — no more one-by-one omissions; leading/trailing spaces preserved*
- *Settings Close button restyled as a blue primary button, matching the About dialog*
- *Fixed a bug where the main window minimum width became 770 after toggling minimal mode (now consistent at 970)*

## v2.12.7 — 2026-07-08

**7处界面细节微调**

*Seven UI detail tweaks*

- 主界面最小宽度减到920
- 设置窗下拉恢复正常宽度(min 200)并随窗宽自适应
- 语言切换即时生效扩展到设置窗内部(标题/关闭/多风格/两段说明即时重译)
- 设置窗改为即时保存：删除保存按钮，只留『关闭』(Close)，所有设置项自动即时保存生效
- 显示密钥按钮：文字改『显示密钥』(Show Key)、宽度与查看日志一致(BTN_W)
- 极简钮图标改为上下横杠+中间方块(SVG，随主题深浅着色)
- 英文模式设置窗两段引擎说明改为指定英文文案

- *Main window minimum width reduced to 920*
- *Settings dropdowns restored to normal width (min 200) and now adapt to window width*
- *Instant language switching extended to the Settings dialog (title, Close, multi-style and both description paragraphs retranslate immediately)*
- *Settings now saves instantly: the Save button was removed leaving only Close; every setting persists and takes effect immediately*
- *Show Key button: text changed to 'Show Key', width matched to the View Log button*
- *Minimal button icon redesigned as top/bottom bars with a center square (SVG, recolored with the light/dark theme)*
- *Specified English wording for the two engine description paragraphs in English mode*

## v2.12.6 — 2026-07-08

**9处界面细节微调**

*Nine UI detail tweaks*

- 主界面最小宽度减到970
- 设置窗下拉恢复正常宽度、并随窗宽拖动自适应
- 设置窗所有API Key输入框随窗宽自适应变宽
- 语言/样式下拉随窗宽自适应
- 显示密钥按钮：文字由『显示API-Key』改『显示密钥』(Show Key)、宽度与查看日志一致
- 语言切换更彻底：朗读嗓音下拉、更多tooltip/占位符即时重译
- 修复极简钮按下后消失：极简钮独立于左组，切换后始终可见；图标恢复▣
- 原文/译文语言下拉框加宽20%，字完整显示
- 设置窗两段引擎说明补齐英文翻译

- *Main window minimum width reduced to 970*
- *Settings dropdowns restored to normal width and adapt as the window is resized*
- *All API key inputs in Settings widen with the window*
- *Language and theme dropdowns adapt to window width*
- *Show Key button: renamed from 'Show API Key' to 'Show Key', width matched to the View Log button*
- *More thorough language switching: TTS voice dropdown and additional tooltips/placeholders retranslate immediately*
- *Fixed the minimal button disappearing after being pressed: it is now independent of the left group and always visible*
- *Source/target language dropdowns widened by 20% for full text display*

## v2.12.5 — 2026-07-08

**7处界面细节微调**

*Seven UI detail tweaks*

- 正方形按钮圆角：正常态8px，青色按下态放大到10px
- 下拉闭合框高度精确对齐正方形按钮(36)，不再偏高
- 主界面最小宽度净调整到1020
- 设置窗API Key输入框/语言/样式下拉随窗宽自适应；显示API-Key按钮改回固定宽但文字完整
- 语言切换即时生效(下拉一选界面文字立即切换，无需保存或重启)
- 样式风格切换即时生效(承前版)
- 交换钮真居中(极简钮并入左组，左右对称)，同时设置/关于那排贴到最右

- *Square button corners: 8px normally, enlarged to 10px in the cyan pressed state*
- *Dropdown closed-box height aligned exactly with square buttons (36), no longer taller*
- *Main window minimum width adjusted to 1020*
- *Settings API key inputs and language/theme dropdowns adapt to window width; the Show API Key button returns to a fixed width with full text*
- *Instant language switching (selecting in the dropdown switches UI text immediately, no save or restart needed)*
- *Instant theme switching (carried over from the previous version)*
- *Swap button truly centered (minimal button merged into the left group for symmetry) while the settings/about row sits flush right*

## v2.12.4 — 2026-07-08

**12处界面细节微调(基于v25完美版)**

*Twelve UI detail tweaks (based on the v25 reference build)*

- 正方形按钮圆角加大到10px(与青色按下态一致)；下拉闭合框圆角8px、高36与按钮等高
- 载入下一条改用独立右箭头图标(redo)，主题切换不再丢失方向
- 朗读速度滑杆左右滑槽与圆球全灰(不蓝)；朗读进度条保持左侧蓝
- 载入上一条/下一条之间分组缝隙去掉，统一小缝
- 主界面最小宽度加到970，翻译钮居中；交换钮加右侧等宽占位真居中
- 左上角极简钮图标换实心方块(线条更清晰)
- 翻译引擎/原文/译文下拉框各加宽10px
- 设置窗API Key输入框改圆角长条、随窗宽自适应；语言/样式下拉同样跟随窗宽
- 显示API-Key按钮文字完整显示(自适应宽+padding)
- 样式风格下拉即时生效(选中即切换，无需保存或重启)

- *Square button corners enlarged to 10px (matching the cyan pressed state); dropdown closed box uses 8px corners at height 36, level with the buttons*
- *Load Next now uses a dedicated right-arrow (redo) icon so direction is preserved across theme switches*
- *Playback-speed slider grooves and knob fully gray (not blue); the playback progress bar keeps its blue left side*
- *Removed the grouping gap between Load Previous and Load Next in favor of a uniform small gap*
- *Main window minimum width raised to 970 with the translate button centered; the swap button gets an equal-width right spacer for true centering*
- *Minimal button icon in the top-left changed to a solid square for sharper lines*
- *Engine, source and target dropdowns each widened by 10px*
- *Settings API key inputs restyled as rounded bars that adapt to window width; language and theme dropdowns follow the window width too*
- *Show API Key button text fully visible (adaptive width plus padding)*

## v2.12.3 — 2026-07-08

**基于v25完美版微调8处界面细节**

*Eight UI detail tweaks based on the v25 reference build*

- 正方形按钮恢复正方形(36x36)，圆角与青色按下态一致(8px)
- 浅色按钮图标/文字统一深黑、深色统一浅白：图标名登记到按钮，主题切换遍历重着色(不再漏清空/复制/粘贴等)
- 朗读速度滑杆左侧滑槽恢复灰色(不再蓝色)
- 设置/更新/帮助/关于那排贴最右侧(去掉平衡占位)
- 复制粘贴等按钮排统一小缝隙不分组，原文贴左、译文贴右
- 主界面最小宽度加宽~100(770->870)，保证翻译钮居中

- *Square buttons restored to a true square (36x36) with corners matching the cyan pressed state (8px)*
- *Light-theme button icons and text unified to deep black and dark-theme to off-white: icon names are registered on each button so theme switching recolors them by traversal (no longer missing Clear, Copy, Paste and others)*
- *Playback-speed slider left groove restored to gray (no longer blue)*
- *The Settings/Update/Help/About row sits flush right (balance spacer removed)*
- *Copy, paste and related button rows use a uniform small gap without grouping; source flush left, target flush right*
- *Main window minimum width increased by about 100 (770 to 870) to keep the translate button centered*

## v2.12.2 — 2026-07-08

**主题终极方案落地：原生+绘制精细混合，深浅完美**

*Final theming solution: native plus drawn hybrid, perfect in light and dark*

- Mac 最终混合方案(真机验证成功)正式落地主程序：
- 下拉闭合框+方按钮+普通按钮+特殊按钮=绘制(深浅两套)；下拉弹出项+气球+滚动条=系统原生
- 下拉箭头用V形SVG图片(不再是方块)；弹出项悬停走系统原生蓝条
- 按钮淡蓝按下反馈；特殊checkable按钮按下保持青色；翻译钮亮蓝
- 深浅切换由pyobjc(AppKit)驱动，切换时重画绘制部分+重生成图标，即时生效

- *The macOS hybrid solution (verified on a real machine) is now in the main program*
- *Drawn: dropdown closed box, square buttons, regular buttons and special buttons (two color sets); native: dropdown popup items, tooltips and scrollbars*
- *Dropdown arrow uses a chevron SVG image (no longer a square block); popup items use the native blue hover bar*
- *Light blue press feedback on buttons; checkable special buttons stay cyan while active; the translate button stays bright blue*
- *Light/dark switching is driven by pyobjc (AppKit); drawn parts are repainted and icons regenerated on switch, taking effect immediately*

## v2.12.1 — 2026-07-08

**Mac原生+pyobjc深浅 最终方案 + 正方形按钮圆角(QSS配合)**

*macOS native + pyobjc theming, final approach, with square button corners via QSS*

- 确立最终方案：Mac 控件走系统原生 + pyobjc(AppKit)切深浅/浅/跟随，深浅都完美且即时切换
- 正方形/工具按钮：加 objectName=toolbtn + border-radius 圆角QSS(只加圆角与hover蓝框，不设颜色，保留原生深浅跟随)
- 翻译大钮 primary、状态栏、激活区蓝框保持设计标识
- 非Mac(Windows/Linux)不受影响

- *Final approach settled: macOS controls use the native appearance with pyobjc (AppKit) driving dark/light/follow-system — perfect in both modes with instant switching*
- *Square and tool buttons: objectName=toolbtn plus border-radius QSS (corners and hover outline only, no colors, preserving native light/dark following)*
- *The primary translate button, status bar and active-area blue outline keep their design identity*
- *Non-macOS platforms (Windows/Linux) are unaffected*

## v2.12.0 — 2026-07-08

**主题系统重构：Mac 原生深浅(AppKit驱动)，彻底终结深浅打架**

*Theme system rebuilt: native macOS light/dark driven by AppKit*

- 根本方案：Mac 用 pyobjc(AppKit) 的 NSApplication.setAppearance_ 驱动系统原生深浅——这是 Qt6.4.2+BigSur 上唯一可靠方案(setColorScheme 是6.8+才有，本机装不了)
- Mac 上不再自涂 QSS 深色皮肤与调色板：所有原生控件(下拉/气球/按钮/滚动条/标题栏)由系统原生深浅驱动，自动跟随，杜绝之前十几处深浅细节bug的总根源(自涂与原生打架)
- 深色/浅色/跟随系统三选项即时生效、无需重启；跟随系统随昼夜自动变
- 主题切换后按钮图标按新深浅重新渲染
- 非 Mac(Windows/Linux)保持原有 QSS+调色板皮肤不变
- 默认主题改为跟随系统
- 注意：Mac 需安装 pyobjc-framework-Cocoa(下版加入 requirements 与打包脚本)

- *Core approach: macOS uses NSApplication.setAppearance_ via pyobjc (AppKit) — the only reliable option on Qt 6.4.2 with Big Sur (setColorScheme requires 6.8+, which cannot be installed on this machine)*
- *macOS no longer paints its own dark QSS skin or palette: all native controls (dropdowns, tooltips, buttons, scrollbars, title bar) follow the system appearance, eliminating the root cause of a dozen previous light/dark bugs (self-painting fighting the native appearance)*
- *Dark, Light and Follow System all take effect instantly without restart; Follow System changes automatically with day and night*
- *Button icons are re-rendered for the new appearance after a theme switch*
- *Non-macOS platforms keep the existing QSS and palette skin unchanged*
- *Default theme changed to Follow System*
- *Note: macOS requires pyobjc-framework-Cocoa (to be added to requirements and the build scripts next version)*

## v2.11.3 — 2026-07-07

**主界面下拉灰底块/气球方框/浅色按钮图标 三处修复**

*Three fixes: dropdown gray block, tooltip square corners, light-theme button icons*

- 主界面下拉残留灰背景块：mac 下 listview 与 popup 设透明背景(WA_TranslucentBackground)，彻底走系统原生
- 气球提示仍是方块：mac 下调色板跳过 ToolTipBase/ToolTipText，交给系统原生尖角圆角气球(apply_theme 与 main 启动两处都改)
- 浅色模式按钮图标仍白色：根因 Icons.icon 固定 #e8e8e8 浅色绘制，改为按当前主题动态取色(浅色用深色#1f1f22)

- *Residual gray background block behind main window dropdowns: on macOS the listview and popup are set to a translucent background so they fully use the native appearance*
- *Tooltips still rendering as squares: on macOS the palette now skips ToolTipBase/ToolTipText, leaving the native rounded tooltip in place (fixed in both apply_theme and startup)*
- *Button icons still white in light mode: the root cause was Icons.icon hardcoding the light color #e8e8e8; it now picks the color from the current theme (deep #1f1f22 in light mode)*

## v2.11.2 — 2026-07-07

**找到下拉方框真凶(自定义combo工厂第1734行)**

*Found the real cause of dropdown square borders (custom combo factory)*

- 根因：下拉是自定义combo(setView+自定义popup)，方框来自工厂函数里 popup.setStyleSheet(border:1px)——此前所有版本都在改无关的 QComboBox QAbstractItemView，从未碰到这行
- 修复：mac 下该 popup 与 listview 一律清空样式(setStyleSheet(''))，回归系统原生圆角无框下拉；其它平台保持深色边框
- tooltip 已确保 mac 下无自定义 QSS

- *Root cause: dropdowns are custom combos (setView plus a custom popup) and the square border came from popup.setStyleSheet(border:1px) inside the factory function — every previous version had been editing the unrelated QComboBox QAbstractItemView rule and never touched this line*
- *Fix: on macOS the popup and listview styles are cleared entirely, returning to the native borderless rounded dropdown; other platforms keep the dark border*
- *Tooltips confirmed free of custom QSS on macOS*

## v2.11.1 — 2026-07-07

**彻底修复Mac下拉/气球仍有方框(收口全部散落样式定义)**

*Fully fixed remaining square borders on macOS dropdowns and tooltips*

- 根因：combo/tooltip 样式散布在主窗/设置窗/历史窗共4处，此前只改了1-2处，其余写死样式在Mac上照样生效画出方框
- 修复①被错位替换破坏的 _tooltip_css() 函数(内嵌了无效占位符)
- 修复②主窗 QToolTip 实为写死样式(未走占位符)，改为 %TOOLTIP% 占位并注入
- 修复③历史窗写死的 QToolTip 改为平台函数注入
- 四处 combo/tooltip 定义全部收口到 _combo_popup_css()/_tooltip_css()，Mac一律返回空走系统原生(圆角无框下拉、尖角气球)

- *Root cause: combo and tooltip styles were scattered across four places (main window, Settings, History); earlier fixes only touched one or two, so the remaining hardcoded styles still drew square borders on macOS*
- *Fix 1: repaired the _tooltip_css() function that had been broken by a misplaced replacement (it contained a dead placeholder)*
- *Fix 2: the main window QToolTip was hardcoded rather than using the placeholder; it now uses %TOOLTIP% with proper injection*
- *Fix 3: the hardcoded QToolTip in the History window now uses the platform function*
- *All four combo/tooltip definitions consolidated into _combo_popup_css() and _tooltip_css(), which return empty on macOS so the native appearance is used (borderless rounded dropdowns, pointed tooltips)*

## v2.11.0 — 2026-07-06

**Mac原生下拉/气球 · 多风格标注净化 · 关于使用说明双语 · 极简状态记忆**

*Native macOS dropdowns/tooltips · multi-style label cleanup · bilingual docs · minimal state memory*

- Mac 下拉列表与气球提示改用系统原生(圆角无框下拉、尖角tooltip、深浅自适应)，复刻滚动条方案；Windows保持自定义样式
- 设置窗 Show API Key 按钮改回固定短宽、文字完整；API Key 输入框随窗口放大而变宽
- 修复浅色下点查看日志误触多风格复选框(查看日志改独立行容器)
- 翻译历史『重新载入』英文模式显示 Reload(补 L()与词条)
- 多风格直译区标注强净化：代码层强删 Part 1/第一部分/直译区/----/【..】等，不依赖模型
- 朗读范围与卡拉OK字幕范围一致(无选区读全文含多风格区，字幕同步全覆盖)
- 关于/使用说明 中英双语(按界面语言切换)；更新说明标题双语框架就位(历史条目英文下版补齐)
- 极简界面状态记忆：重启恢复；API-Key 永远默认隐藏

- *macOS dropdowns and tooltips now use the native appearance (borderless rounded lists, pointed tooltips, automatic light/dark), mirroring the scrollbar approach; Windows keeps the custom style*
- *Settings Show API Key button restored to a fixed short width with full text; API key inputs widen with the window*
- *Fixed clicking View Log accidentally toggling the multi-style checkbox in light mode (View Log moved to its own row container)*
- *Translation history Reload button now shows 'Reload' in English mode (L() and dictionary entry added)*
- *Strong cleanup of multi-style literal-zone labels: Part 1, literal-zone markers, ---- and bracketed tags are stripped in code rather than relying on the model*
- *Spoken range and karaoke range kept consistent (with no selection the full text including the multi-style zone is read and subtitles cover it all)*
- *About and User Guide are bilingual (following the UI language); the bilingual framework for the Change Log title is in place (historical entries to be translated next)*
- *Minimal mode state is remembered across restarts; API keys always default to hidden*

## v2.10.0 — 2026-07-06

**主题切换彻底化 · 两侧字幕独立 · 去边框 · 英文补全 · 多风格空行分隔**

*Thorough theme switching · independent per-side subtitles · borderless · English completion · blank-line separator*

- 深浅主题切换彻底：热切换时刷新标题栏、下拉弹出列表、已打开设置窗，不再残留深色
- 浅色模式：所有青色提亮加饱和(#00b3c6)，与蓝色一致；按钮字/图标转黑
- 修复浅色下点查看日志误触多风格复选框（复选框背景透明化）
- 下拉列表项外框与气球提示外框隐形（边框设为与背景同色）
- 朗读两侧独立：拖动某侧进度条只刷新该侧卡拉OK，不再串到另一侧
- 英文补全：占位符改正常句式(Type or paste…)、历史提示、主界面引擎名(ERNIE/Doubao/Qwen/Hunyuan)、晓贝(Xiaobei)、Key提示段落、Reload
- 设置窗 Show API Key 按钮文字完整显示；API Key 输入框随窗口放大而变宽
- 多风格：直译区与多风格区空行分隔，去掉【直译区】【多风格区】及---标注

- *Theme switching is now thorough: hot switching refreshes the title bar, dropdown popups and any open Settings dialog, leaving no dark remnants*
- *Light mode: all cyan accents brightened and saturated (#00b3c6) to match the blue; button text and icons turn black*
- *Fixed clicking View Log accidentally toggling the multi-style checkbox in light mode (checkbox background made transparent)*
- *Dropdown item outlines and tooltip outlines made invisible (border color matched to the background)*
- *The two playback sides are independent: dragging one side's progress bar only refreshes that side's karaoke*
- *English completion: placeholders reworded to natural sentences (Type or paste...), history hints, main window engine names (ERNIE/Doubao/Qwen/Hunyuan), Xiaobei, key hint paragraphs and Reload*
- *Settings Show API Key button text fully visible; API key inputs widen with the window*
- *Multi-style: literal and multi-style zones separated by a blank line, with bracketed zone labels and --- markers removed*

## v2.9.0 — 2026-07-06

**英文全覆盖(引擎/嗓音/Key/文档) · 浅色按钮字色+高饱和蓝 · 状态全记忆 · 多风格空行分隔**

*Full English coverage · light-mode button colors · state memory · blank-line separator*

- English US 全覆盖：翻译钮 Translate、文心一言 ERNIE、豆包 Doubao、通义千问 Qwen、混元 Hunyuan、晓贝 Xiaobei、Reload；设置窗 Key 标签(Baidu AI Studio / Volcengine / Alibaba Cloud Model Studio / Tencent Cloud Hunyuan)、提示段落、更新说明/使用说明/关于文档均英文
- 浅色模式：按钮文字与图标转黑；蓝色翻译钮与所有关闭钮提亮到状态栏同款高饱和蓝(#1e88e5)
- 设置窗 Show API Key 按钮宽度与查看日志等统一(BTN_W)
- 语言与主题真正即时生效不重启；跟随系统随昼夜自动切换
- 朗读两排组件统一窄间距紧挨、译文排靠右去空位
- 拖动进度滑杆时卡拉OK字幕实时跟随(无关选区)
- 多风格：直译区与多风格区改用空行分隔(去掉----标注)；朗读范围与卡拉OK范围一致
- 交换钮只交换直译区，多风格灰字区不参与
- 全状态记忆：引擎/源语言/目标语言/主题/语言/朗读语速/嗓音/多风格开关，重启后恢复

- *Full English US coverage: Translate button, ERNIE, Doubao, Qwen, Hunyuan, Xiaobei, Reload; Settings key labels (Baidu AI Studio / Volcengine / Alibaba Cloud Model Studio / Tencent Cloud Hunyuan), hint paragraphs, and the Change Log, User Guide and About documents*
- *Light mode: button text and icons turn black; the blue translate button and all close buttons brightened to the saturated blue used by the status bar (#1e88e5)*
- *Settings Show API Key button width unified with View Log and others (BTN_W)*
- *Language and theme now take effect immediately without restart; Follow System changes automatically with day and night*
- *The two playback rows use consistent tight spacing with the target row flush right*
- *Karaoke subtitles follow in real time while dragging the progress slider (regardless of selection)*
- *Multi-style: literal and multi-style zones separated by a blank line (---- markers removed); spoken range matches karaoke range*
- *The swap button only swaps the literal zone; the gray multi-style zone is excluded*

## v2.8.0 — 2026-07-06

**英文全覆盖(含下拉/弹窗)+首字母大写 · 主题立即生效 · 多风格直译区分隔**

*Full English coverage with title case · instant theme switching · multi-style zone separator*

- English US 模式全面覆盖：下拉列表选项、设置/关于/历史弹窗内所有文字均英文，且统一首字母大写(如 View History)
- 浅色模式补漏：标题栏随主题变浅、按钮悬停与下拉弹出列表统一浅色配色
- 语言与深浅主题改为立即生效：切主题热切换、切语言自动重启；跟随系统在系统昼夜切换时自动跟变
- 设置窗『查看日志』上移到多风格行下方；历史弹窗按钮英文不再截断，『载入』改为 Reload
- 极简界面图标换为更饱满的 ▣；极简最小窗口高度再压缩至 200
- 顶部交换钮真正居中(与翻译钮对齐)；朗读两排组件左右边距与上方对齐
- 已有音频缓存时再次点朗读，无论是否有选区都恢复卡拉OK字幕
- 多风格翻译分区：上半为逐行直译(黑/白字，参与原文↔译文选区联动)，---- 分隔线下为多风格区(灰字，不参与联动)

- *Comprehensive English US coverage: dropdown items and all text inside the Settings, About and History dialogs are in English with consistent title case (e.g. View History)*
- *Light mode gaps closed: the title bar lightens with the theme, and button hover states plus dropdown popups use unified light colors*
- *Language and theme now take effect immediately: theme switches hot, language triggers an automatic restart; Follow System changes with the system's day/night switch*
- *Settings View Log moved below the multi-style row; History dialog buttons no longer truncate in English and Load was renamed Reload*
- *Minimal mode icon changed to a fuller square; minimal window minimum height reduced to 200*
- *The top swap button is truly centered (aligned with the translate button); the two playback rows share the same left and right margins as the rows above*
- *With an audio cache present, pressing play again restores karaoke subtitles whether or not there is a selection*
- *Multi-style zoning: the upper part is the line-by-line literal translation (black/white text, participating in source-target selection linking); below the ---- separator is the multi-style zone (gray text, excluded from linking)*

## v2.7.0 — 2026-07-05

**界面语言中英切换 · 浅色/深色/跟随系统主题 · 设置窗改版**

*UI language switching · light/dark/follow-system themes · Settings redesign*

- 设置新增『语言』：中文 / English US，选英文后全部界面文字、气球提示、弹窗、状态栏均切换为英文（重启后生效）
- 设置新增『样式风格』：浅色 / 深色 / 跟随系统（跟随系统自动检测系统深浅模式，重启后生效）
- 设置窗改版：显示API-Key按钮移到Key输入区与多风格选项之间、与输入框左对齐，按下青色显示、弹起灰色隐藏；语言与样式风格在其下方；查看日志移至窗口底部左侧
- 极简界面按钮图标改为更简洁的 ▢
- 关于页移除电话号码，仅保留网址与邮箱（隐私保护）

- *New Language setting: Chinese or English US — choosing English switches all UI text, tooltips, dialogs and the status bar to English (applies after restart)*
- *New Theme setting: Light, Dark or Follow System (Follow System detects the OS appearance; applies after restart)*
- *Settings redesign: the Show API Key button sits between the key inputs and the multi-style option, left-aligned with the inputs, cyan when pressed and gray when hidden; language and theme sit below it; View Log moved to the bottom left*
- *Minimal mode button icon simplified to an outlined square*
- *Phone number removed from the About page, leaving only the website and email (privacy)*

## v2.6.0 — 2026-07-05

**极简界面模式 · 跨侧续播根治 · docx导出修复 · 选区字幕自愈 · 对齐分句扩充**

*Minimal UI mode · cross-side resume fix · docx export fix · selection subtitle self-healing*

- 新增极简界面：左上角⛶钮一键切换，只留原文/译文区、翻译钮与状态栏；极简下按钮青色、最小窗口可缩至420x320，再点还原
- 跨侧续播从头播根因修复：重播路径内部stop会把刚存的续播位置清零——改为先取位再stop，且只有真停止才归零
- 选区朗读偶发无卡拉OK字幕：引擎返回相对选区的词边界时自动平移为全文绝对位置
- 修复翻译历史导出docx报错(XML控制字符)：写入前统一净化NULL等非法字符，三处docx写入点全覆盖
- 主动/从属区对齐分句标点扩充：新增逗号(，,)与全角空格参与分割，对应精度更高
- 正常界面最小宽度720→770（左侧按钮增多后更合适）

- *New minimal UI: one click on the top-left button leaves only the source/target areas, translate button and status bar; buttons turn cyan and the window can shrink to 420x320; click again to restore*
- *Root fix for cross-side resume restarting from the beginning: the internal stop inside the replay path was zeroing the just-saved resume position — the position is now read before stopping and only a true stop resets it*
- *Occasional missing karaoke when reading a selection: word boundaries returned relative to the selection are now shifted to absolute document positions*
- *Fixed translation history docx export errors (XML control characters): NULL and other illegal characters are sanitized before writing, covering all three docx write points*
- *Expanded sentence-splitting punctuation for active/passive area alignment: commas and full-width spaces now participate, improving accuracy*
- *Normal-mode minimum width raised from 720 to 770 to fit the added buttons*

## v2.5.1 — 2026-07-04

**跨侧续播回位 · 换嗓保字幕保选区(根治) · 光标处粘贴 · 单实例守护**

*Cross-side resume position · voice switch preserves subtitles and selection · paste at cursor · single instance*

- 跨侧暂停后回来点继续，从暂停位置续播不再从头：暂停位置存入该侧缓存，重播时自动定位；同侧继续/按停止会正确清零
- 换嗓/引擎重读根治两处：①重读时沿用原选区（此前重新推导误判为读全文并清掉蓝色选区）②为重读而停被误当自然播完、250ms后清绿——preserve期间跳过收尾
- 粘贴细化：主动区有明确光标位置时粘贴到光标处；从属区且无选区才默认贴到末尾
- 新增单实例守护（QLockFile）：程序已在运行时再次启动会提示并退出，修复偶发双开

- *Resuming after pausing on the other side no longer restarts from the beginning: the pause position is stored in that side's cache and restored on replay; continuing on the same side or pressing stop correctly resets it*
- *Two root fixes for voice/engine re-reads: the original selection is reused (previously re-derivation misread it as full text and cleared the blue selection), and a stop issued for a re-read is no longer mistaken for natural completion that cleared the green highlight 250ms later*
- *Paste refinement: in the active area with a definite cursor position, paste goes to the cursor; in the passive area with no selection it defaults to the end*
- *Added a single-instance guard (QLockFile): launching again while running shows a notice and exits, fixing occasional double launches*

## v2.5.0 — 2026-07-03

**缓存直播/真清空 · 换嗓保位保字幕 · 数字翻译修复+小数 · 选区复制粘贴 · 混合文本翻译**

*Cache replay and true clear · voice switch keeps position · number translation fix · selection-aware copy/paste*

- 有音频缓存时点朗读直接重播（分侧缓存命中），不再重新生成；清空钮改为真清（同步清掉旧全局缓存，重播不再复活）
- 换嗓音/引擎重读：卡拉OK绿色与蓝/灰选区随进度条一并保持；播放或暂停中切换嗓音必定触发重新生成（修复偶发不触发）
- 修复强制中/英数字翻译失效根因：目标判断只比对『英语』而下拉项是『English』永不命中；88 现按目标正确输出中/英两式
- 原文/译文语言下拉变化即强制重新翻译（等同点翻译按钮）；翻译大按钮无条件重翻
- 数字支持小数：888.89 → 逐位拼读(含点/point) + 数学读法（八百八十八点八九 / point eight nine）
- 复制/粘贴选区感知：有蓝/灰选区只复制或只覆盖选中部分；无选区复制全部、粘贴默认到末尾
- 修复混合中英文本翻译：自动检测含中日韩字符时显式声明源为中文，Google 不再 en→en 原样返回（『中文』二字现在会被翻译）
- 底部忙碌进度条改自绘胶囊：滑块滑到两端也保持圆角（Qt原生样式两端变方的限制已绕开）

- *With an audio cache present, pressing play replays directly (per-side cache hit) instead of regenerating; the clear button now truly clears (the old global cache is cleared too so replay cannot revive it)*
- *Voice/engine re-reads keep the green karaoke and blue/gray selection in sync with the progress bar; switching voices while playing or paused always triggers regeneration*
- *Fixed the root cause of forced Chinese/English number translation failing: the target check compared against a Chinese label while the dropdown value was 'English', so it never matched; numbers now output correctly for the chosen target*
- *Changing the source or target language dropdown forces a re-translation (equivalent to pressing Translate); the main translate button always re-translates*
- *Decimal support for numbers: 888.89 reads digit by digit (including the point) as well as mathematically*
- *Selection-aware copy/paste: with a blue/gray selection only that part is copied or replaced; with no selection everything is copied and paste defaults to the end*
- *Fixed mixed Chinese-English translation: when CJK characters are detected the source is declared as Chinese explicitly, so Google no longer returns en-to-en unchanged*
- *The bottom busy progress bar is now custom-drawn as a capsule so the slider keeps rounded ends (working around Qt's square-end limitation)*

## v2.4.0 — 2026-07-03

**多风格翻译修复+单词多译法 · 进度条冻结 · 载入下一条 · 按钮语义与间距**

*Multi-style fixes and word mode · frozen progress bar · load next · button semantics and spacing*

- 修复多风格翻译失效根因：导入过一次文件后残留路径会永久禁用多风格，改为仅在原文与导入内容一致时禁用
- 多风格新增单词模式：输入单字/词（中文≤4字或英文单词）输出多种准确译法，每行一个，无解释无音标；词组/句子仍按书面/口语/正式等风格分类
- 朗读钮颜色语义严格化：缓存有音频=青色，无=灰色；播放到头/拖到最右不再误变灰
- 更改嗓音/引擎重读时，进度条冻结在当前位置，生成完成后就地续播，不再跳回开头
- 新增『载入下一条原文』按钮（上一条右侧，镜像图标），双向循环历史
- 设置弹窗保存钮改蓝色，取消保持灰色
- 按钮组间距统一为10px（对标顶排语言框与交换钮间距）

- *Root fix for multi-style translation being disabled: a leftover path from a single earlier file import permanently disabled it; it is now disabled only while the source text still matches the imported content*
- *New word mode for multi-style: entering a single character or word (up to 4 Chinese characters, or one English word) returns several accurate translations, one per line, with no explanations or phonetics; phrases and sentences still use the formal/casual/etc. style breakdown*
- *Stricter play button color semantics: cyan when an audio cache exists, gray when not; reaching the end or dragging to the far right no longer turns it gray by mistake*
- *When re-reading after a voice or engine change, the progress bar freezes at the current position and resumes in place once generation completes, instead of jumping back to the start*
- *New 'Load next source' button (right of Load previous, mirrored icon) for cycling through history in both directions*
- *Settings Save button turned blue while Cancel stays gray*
- *Button group spacing unified to 10px, matching the gap between the top language boxes and the swap button*

## v2.3.1 — 2026-07-03

**修复样式表整表失效(按钮丢样式元凶) · 控件统一加高 · 音频/文字清空分离**

*Root fix for stylesheet-wide failure (the cause of buttons losing styles) · uniform control height · audio and text clearing separated*

- 根因修复：样式表为三段拼接，占位符替换只作用于最后一段，残留占位符导致整表解析失败被丢弃——翻译钮丢蓝色、按钮变矮变形的元凶
- 翻译大按钮恢复蓝色并加圆角；朗读钮青色态加圆角；导入钮变青后不再缩小
- 所有下拉框/按钮统一加高到34px，图标钮改正方形，交换钮不再偏矮
- 气球提示外框缩小约20%并改圆角
- 翻译历史弹窗：检查历史去掉蓝色，关闭钮改蓝色，与关于/说明弹窗统一
- 朗读语速滑杆两侧统一灰色（不再左蓝右灰），与播放进度条区分
- 主动/从属切换补修：切换后新从属区正确显示灰色选区（去掉误清联动的旧逻辑）
- 原生滚动条模式下文本框右内边距 20px 恢复为 8px，滚动条贴右不再有空隙
- 朗读区新增音频清空钮（原文/译文各一，下载钮右侧）：仅释放该侧音频缓存，朗读钮变灰、下载失效
- 原文/译文区文字清空钮改为只清文字与导入文件，不再清音频（文字与音频清空分离）

- *Root cause fixed: the stylesheet is assembled from three parts and placeholder substitution only reached the last one; the leftover placeholders made the whole sheet fail to parse and be discarded — the true cause of the translate button losing its blue and buttons becoming short and misshapen*
- *The large translate button is blue and rounded again; the cyan play state gets rounded corners; the import button no longer shrinks when it turns cyan*
- *All dropdowns and buttons raised to a uniform 34px height, icon buttons made square, and the swap button is no longer shorter than its neighbors*
- *Tooltip frames reduced by about 20% and given rounded corners*
- *Translation history dialog: View History loses its blue and Close becomes blue, matching the About and User Guide dialogs*
- *Playback-speed slider is gray on both sides (no longer blue on the left) to distinguish it from the playback progress bar*
- *Active/passive switching follow-up fix: after switching, the new passive area correctly shows the gray selection (the old logic that wrongly cleared the link was removed)*
- *With native scrollbars the text area's right padding returns from 20px to 8px, so the scrollbar sits flush right without a gap*

## v2.3.0 — 2026-07-02

**主动区点击切换重构 · 原生胶囊滚动条(Mac/Win11) · 高亮清除根治 · 清空按钮重做**

*Active-area click switching rebuilt · native capsule scrollbars (macOS/Win11) · root fix for highlight clearing · clear buttons redone*

- 主动/从属区重构：鼠标按下即切换（点文字或空白都生效），只有一个蓝框；从属区灰色选区点击后变蓝，原主动区蓝选区自动转灰
- 点击当前主动区：保持主动，仅清掉两侧联动选区
- 改字清高亮根治：真实变更时掐断卡拉OK定时器、清词边界、停联动防抖、作废对齐表；边界过期自动熔断，绿色不再被画回
- 改字时若该侧正在朗读，自动停止朗读（读的已是旧内容）
- 滚动条：Mac 与 Win11(Qt>=6.7) 用系统原生胶囊；Win10及以下/Linux用自定义样式；全局样式解毒（QWidget规则改为调色板，不再污染滚动条）
- 清空按钮移位：原文清空钮在翻译历史右侧（隔开），译文清空钮在最右侧（隔开）
- 清空增强：原文清空=清文字+清导入(钮变灰)+译文随清+双侧音频释放(朗读/下载钮变灰)+导出钮隐藏；译文清空=清文字+译文音频释放

- *Active/passive areas rebuilt: switching happens on mouse press (on text or blank space alike) with only one blue frame; clicking a gray selection in the passive area turns it blue while the previously active blue selection turns gray*
- *Clicking the currently active area keeps it active and only clears the linked selections on both sides*
- *Root fix for highlights surviving edits: on a real change the karaoke timer is cut, word boundaries cleared, link debouncing stopped and the alignment table invalidated; expired boundaries trip a fuse so green can no longer be repainted*
- *Editing text on a side that is currently being read automatically stops playback, since what is being read is already stale*
- *Scrollbars: macOS and Win11 (Qt 6.7+) use native capsules; Win10 and below plus Linux use the custom style; global styling detoxified (the QWidget rule now uses the palette so it no longer contaminates scrollbars)*
- *Clear buttons repositioned: the source clear button sits right of Translation History (separated), the target clear button at the far right (separated)*
- *Clearing enhanced: source clear wipes text, import state (button grays out), the target text as well, releases audio on both sides (play/download gray out) and hides the export button; target clear wipes target text and releases target audio*

## v2.2.2 — 2026-07-01

**根治选区朗读失效（高亮反馈环彻底消灭）**

*Root fix for selection playback failing (highlight feedback loop eliminated)*

- 根因：停止/清除卡拉OK时 rehighlight 触发 textChanged，被误判为用户改字，导致选区信息被抹掉、自动翻译误触发、离线嗓音卡拉OK从全文扫（看似在读全文）
- 根治：textChanged 处理器入口做文本比对——内容没变（仅格式重绘）直接跳过，一劳永逸消灭此类误伤
- 选区朗读现在全程保留选区：蓝色底色、卡拉OK范围、边界估算都只在选区内

- *Root cause: stopping or clearing karaoke triggered rehighlight, which fired textChanged and was mistaken for a user edit — wiping the selection, falsely triggering auto-translation, and making offline-voice karaoke scan from the very beginning (appearing to read the whole text)*
- *Root fix: the textChanged handler now compares text at its entry point and skips immediately when the content is unchanged (a format-only repaint), eliminating this whole class of false positives once and for all*
- *Selection playback now preserves the selection throughout: the blue background, the karaoke range and boundary estimation all stay within the selection*

## v2.2.1 — 2026-07-01

**修复选区朗读被三态切换吃掉的问题**

*Fixed selection playback being swallowed by the three-state toggle*

- 修复：选中一段文字再点朗读钮，会被『暂停/继续』三态切换拦截而继续播旧音频（v2.1.2 引入）
- 现在：只要该区有新的选区（与当前朗读内容不同），点朗读钮即停掉旧音频、只朗读选区

- *Fixed: selecting text and pressing play was intercepted by the pause/resume three-state toggle and kept playing the old audio (introduced in v2.1.2)*
- *Now: whenever the area has a new selection differing from what is currently being read, pressing play stops the old audio and reads only the selection*

## v2.2.0 — 2026-07-01

**主动/从属区单蓝框 · 两侧独立音频缓存 · 高亮清除与导出钮修复 · Mac原生滚动条**

*Single blue frame for the active area · independent per-side audio cache · highlight clearing and export button fixes · native macOS scrollbars*

- 主动区只保留一个蓝框（去掉 :focus 导致的第二个蓝框），从属区灰框
- 两侧朗读音频各自独立缓存：朗读钮青色=音频在内存可下载，灰色=无音频不可下载
- 改动某侧文字，该侧音频缓存作废、朗读钮变灰、下载禁用；停止后若音频仍在内存则钮保持青色、进度归零
- 跨侧朗读：一侧朗读时点另一侧，先暂停该侧（进度保留、青色继续态）再读另一侧
- 彻底修复文字变更时蓝色选区/绿色卡拉OK未清除（根因：译文区未监听 textChanged + guard 误伤，改用精确 _highlighting 标记）
- 修复导出翻译后文件按钮显隐（根因：setPlainText 时序竞争，导入状态改为先记录后填文本）
- Mac 使用系统原生胶囊滚动条（无灰槽、自动隐藏）；Windows 保留自定义细样式
- 最小窗口宽度调整为 720（较原缩小约 400px）

- *The active area keeps only one blue frame (the second frame caused by :focus was removed) while the passive area uses a gray frame*
- *Each side caches its playback audio independently: a cyan play button means audio is in memory and downloadable, gray means no audio and no download*
- *Editing text on a side invalidates that side's audio cache, grays out its play button and disables download; after stopping, the button stays cyan with progress reset if audio is still in memory*
- *Cross-side playback: pressing play on the other side while one is reading pauses the first side (keeping its progress and cyan resume state) before reading the other*
- *Fully fixed blue selections and green karaoke not clearing on text changes (root cause: the target area never listened to textChanged, plus an overreaching guard; replaced with a precise _highlighting flag)*
- *Fixed the export-translated-file button appearing and disappearing incorrectly (root cause: a setPlainText timing race; import state is now recorded before the text is filled)*
- *macOS uses native capsule scrollbars (no gray trough, auto-hiding) while Windows keeps the custom slim style*

## v2.1.3 — 2026-06-30

**修复卡拉OK失效与停止键 · 跨侧朗读暂停 · 最小窗口缩小 · 多项细节**

*Karaoke and stop button fixes · cross-side pause · smaller minimum window · assorted details*

- 修复原文区卡拉OK字幕失效（高亮 rehighlight 触发 textChanged 误清高亮的反馈环）
- 修复文字变更时蓝色选区/绿色字幕未清除（补上清蓝色选区）
- 修复停止朗读键失效（暂停态下也能停止）
- 跨侧朗读：一侧朗读时点另一侧，先把该侧暂停（进度保留、按钮青色继续态），再读另一侧
- 设置面板 HY-MT Key 改为『混元 HY-MT Key』
- 关于窗『英语导师』与『English Coach』同字号同颜色
- 最小窗口宽度大幅缩小（960→620）
- 语速气球拖动时持续显示、跟随滑块
- 进度条/滚动条进一步圆角处理

- *Fixed karaoke subtitles failing in the source area (a feedback loop where rehighlight fired textChanged and wrongly cleared the highlight)*
- *Fixed blue selections and green subtitles not clearing on text changes (blue selection clearing added)*
- *Fixed the stop button not working (it now also stops from the paused state)*
- *Cross-side playback: pressing play on the other side while one is reading pauses the first side (progress kept, button in cyan resume state) before reading the other*
- *Settings HY-MT key relabeled as Hunyuan HY-MT Key*
- *In the About dialog the Chinese and English product names use the same size and color*
- *Minimum window width reduced substantially (960 to 620)*

## v2.1.2 — 2026-06-30

**界面标签改气球提示 · 翻译按钮可靠性 · 朗读按钮三态 · 导出钮智能显隐**

*Labels replaced by tooltips · translate button reliability · three-state play button · smart export button*

- 关于窗 English Coach 下方加副标题『英语导师』
- 原文/译文文字变更时，自动清除蓝色选区高亮与卡拉OK绿色高亮
- 翻译按钮修复点击无效问题；点翻译会先中断所有进行中的翻译再重新开始
- 界面文字标签全部去除改为悬停气球提示（引擎/语言/嗓音/文字区/进度条/语速等）
- 语速气球实时显示『朗读语速 正常 / +20% / -50%』
- 引擎名缩短：GLM-4-Flash→GLM、HY-MT→混元；约束最小窗口宽度让交换钮居中
- 导出翻译后文件按钮：平时隐藏，导入成功才出现（灰），翻译完成变青可点；原文与导入不一致则消失
- 所有滚动条只留胶囊滑块，去掉深灰背景轨道；等待进度条去底槽、圆角胶囊形
- 朗读按钮悬停三态：朗读原文/译文 → 暂停朗读 → 继续朗读，循环（并修复暂停图标不显示的 bug）

- *Added a subtitle under English Coach in the About dialog*
- *Blue selection highlights and green karaoke highlights are cleared automatically when source or target text changes*
- *Fixed the translate button not responding; pressing translate now aborts any in-flight translation before starting fresh*
- *All inline text labels removed in favor of hover tooltips (engine, language, voice, text areas, progress bar, speed and more)*
- *The speed tooltip shows the live value: Speech rate Normal / +20% / -50%*
- *Engine names shortened (GLM-4-Flash to GLM, HY-MT to Hunyuan); a minimum window width keeps the swap button centered*
- *Export-translated-file button: hidden normally, appears grayed after a successful import, turns cyan and clickable once translation finishes, and disappears if the source no longer matches the import*

## v2.1.1 — 2026-06-30

**修复 PDF 导出报错 · 文件名空格化 · 进度条与滚动条精修 · 交换钮居中**

*PDF export fix · spaces in filenames · progress bar and scrollbar refinements · centered swap button*

- 修复导出 PDF 报错（reportlab.pdfbase.pdfmetrics 导入路径）
- 所有导出文件名分隔符由下划线改空格，如 EC ZH XiaoXiao 2026-06-30 013733.mp3
- 状态栏进度条改极简药丸形（无外框、更细、半透明槽、青色块）
- 拖文件到文本框任意位置=导入内容（不再粘贴文件名）
- 原文/译文朗读进度条彻底分离，拖动互不影响
- 翻译历史按钮改名：检查历史 / 下载文档
- 文本框滚动条改 mac 风格细药丸、不再挡字
- 交换钮用网格强制窗口居中；下拉框留白压到最小；原文语言/译文语言改名

- *Fixed a PDF export error (the reportlab.pdfbase.pdfmetrics import path)*
- *All export filenames now use spaces instead of underscores, e.g. EC ZH XiaoXiao 2026-06-30 013733.mp3*
- *Status bar progress bar restyled as a minimal pill (no outer frame, thinner, translucent trough, cyan block)*
- *Dropping a file anywhere on a text box imports its content (instead of pasting the filename)*
- *Source and target playback progress bars fully separated so dragging one does not affect the other*
- *Translation history buttons renamed to View History and Download Document*
- *Text box scrollbars restyled as slim macOS-style pills that no longer cover text*

## v2.1.0 — 2026-06-29

**选区主动/从属双向联动 · 界面重排 · 文件导入导出完善**

*Two-way selection linking with active/passive areas · layout reshuffle · file import and export completed*

- 选区双向联动：原文↔译文互选都能定位（依据保存的句对应关系），译文区选择终于能联动原文区
- 主动/从属区逻辑：选中区为主动区（蓝框蓝底），另一区为从属区（选区灰底）；点击从属区即切换
- 状态栏『正在生成音频』改用消息区显示，与『翻译完成』等交替不重叠（修正上次实现方式）
- 进度条改药丸形：细灰黑轮廓、透明外围、青色滚动块
- 第一排重排：翻译引擎｜源语言｜交换(居中)｜目标语言｜设置区(右)
- 操作排重排：原文｜复制粘贴清空｜导出原文+导入文件｜上一条+历史｜翻译｜…｜导出译文+导出文件｜译文
- 导出文件名规则 OT/TT_语言_日期时间，历史 TH_日期时间；保存路径记忆
- PDF 导出改 A4 竖版自动换行（修右侧出画），中文字体 PingFang/思源黑体/雅黑回退
- 清空原文→重置导入状态；清空译文→重置导出状态（青色恢复灰色）
- 停止键分侧独立：原文停止只停原文，译文停止只停译文
- 上一条原文改为循环遍历全部历史原文
- 拖拽文件到窗口=导入文件内容；原文区右内边距加大，滚动条不再挡字
- 按钮宽度统一（显示隐藏为准），所有 Close 改『关闭』；标题改 English Coach

- *Two-way selection linking: selecting in either the source or target area locates the counterpart (based on the stored sentence mapping), so target-area selections finally link back to the source*
- *Active/passive logic: the area you select in becomes active (blue frame, blue background) and the other becomes passive (gray selection background); clicking the passive area switches roles*
- *The status bar 'Generating audio' notice moved to the message area so it alternates with 'Translation complete' instead of overlapping (correcting the previous implementation)*
- *Progress bar restyled as a pill: thin dark-gray outline, transparent surroundings, cyan scrolling block*
- *First row reshuffled: engine, source language, swap (centered), target language, settings group (right)*
- *Action row reshuffled: source, copy/paste/clear, export source plus import file, previous plus history, translate, export target plus export file, target*
- *Export filename rules OT/TT_language_datetime and history TH_datetime, with the save path remembered*

## v2.0.0 — 2026-06-29

**2.0 大改版：文件导入导出 · 朗读分原文/译文两组 · 多项修复**

*Version 2.0 overhaul: file import and export · playback split into source and target groups · assorted fixes*

- 修复 Argos 离线翻译『出出出』重复退化（改为逐句翻译 + 重复压缩兜底）
- 朗读控制分原文/译文两组，上移到复制粘贴排与嗓音排之间，按钮改纯图标方形
- 新增导入文件（txt/docx/pdf，支持拖拽）：内容填入原文区并自动翻译，按钮变青色
- 新增导出当前原文/译文文字（txt/md/docx/json/pdf）
- 新增导出翻译后文件：docx 保留段落结构，文件名加 T 后缀；pdf 暂只读入不导出
- 翻译历史新增多格式下载（txt/md/json/docx/pdf）
- 数字/单符号特殊翻译：78→Seven Eight / seventy-eight（中英各两式）；逗号→comma/逗号
- 文件导入翻译模式下，多风格翻译与符号翻译自动失效
- 进度条改青色无外框，状态栏提示移到右侧不再重叠，Mac/Win 右侧留 5% 空隙
- 设置窗取消/保存按钮统一右对齐
- 模型目录更名为 EnglishCoach Models/Argos、EnglishCoach Models/Kokoro

- *Fixed Argos offline translation degenerating into repeated characters (switched to sentence-by-sentence translation with a repetition-collapsing fallback)*
- *Playback controls split into source and target groups, moved between the copy/paste row and the voice row, with buttons changed to plain square icons*
- *New file import (txt/docx/pdf, drag and drop supported): content fills the source area and is translated automatically, turning the button cyan*
- *New export of the current source or target text (txt/md/docx/json/pdf)*

## v1.9.6 — 2026-06-29

**选区联动重做（句级对齐）· 朗读交互修复 · 状态栏与下拉修复**

*Selection linking redone (sentence-level alignment) · playback interaction fixes · status bar and dropdown fixes*

- 选区联动重新设计：翻译时按句建立原文↔译文对应，选区覆盖所有相关句（选全文即全亮）
- 合成期间界面不变：已选区的蓝/灰背景在生成音频时保持显示
- 改朗读引擎/嗓音时进度条不再跳回头、按钮保持青色『继续朗读』不闪
- 朗读中点交换：立即终止朗读并清空音频缓存，自动重新翻译
- 状态栏『正在生成音频』改为蓝底白字，与其它提示一致
- Mac 合成进度条左移，右侧留约 10% 空隙，构图匀称
- Windows 嗓音下拉滚轮不再滚出末尾空行

- *Selection linking redesigned: translation builds a sentence-by-sentence source-to-target mapping, so a selection highlights every related sentence (selecting everything lights up everything)*
- *The interface stays put during synthesis: blue and gray selection backgrounds remain visible while audio is generated*
- *Changing the playback engine or voice no longer sends the progress bar back to the start, and the button stays cyan in its resume state without flickering*
- *Pressing swap during playback immediately stops playback, clears the audio cache and re-translates automatically*
- *The status bar 'Generating audio' notice now uses white text on blue, matching the other messages*
- *On macOS the synthesis progress bar shifts left, leaving about 10% clearance on the right for a balanced layout*
- *The Windows voice dropdown no longer scrolls past the last item into blank space*

## v1.9.5 — 2026-06-28

**更新应用图标**

*Updated application icon*

- 重绘应用图标：线条更圆润饱满，接近原生质感
- GPU 版图标补回 A/文 标牌（青绿底 + 闪电，与 CPU 版区分）

- *Application icon redrawn with rounder, fuller strokes for a more native feel*
- *The GPU edition icon regains its A/文 badge (teal background with a lightning bolt, distinguishing it from the CPU edition)*

## v1.9.4 — 2026-06-28

**朗读可中断 · 选区联动不再翻译 · GPU 图标 · 打包命名 · 多项修复**

*Interruptible playback · selection linking no longer translates · GPU icon · packaging names · assorted fixes*

- 新增朗读中断：合成中按停止可中断（段边界软中断），并提示『正在停止…』
- 选区联动改为按位置比例映射，完全不再调用翻译引擎（选译文不再触发自动翻译）
- 新增 GPU 版专属图标（青绿底+闪电）
- Mac 打包为 English Coach.app；Win 打包为含 English Coach 文件夹与 English Coach.exe（GPU 版同理）
- 选区强制蓝色背景（修复某些系统显示绿色）
- 中文嗓音下拉加宽（Windows 不再截断），并去除末尾空行与多余滚动
- 合成中『正在生成音频』文字持续到结束，进度条约占窗口 40% 居中偏右、右侧留白
- 朗读中点交换内容会停止当前朗读，避免青绿字幕错位到对面

- *New interruptible playback: pressing stop during synthesis aborts it at a segment boundary and shows a 'Stopping...' notice*
- *Selection linking now maps by positional ratio and never calls the translation engine (selecting target text no longer triggers auto-translation)*
- *New dedicated icon for the GPU edition (teal background with a lightning bolt)*
- *macOS packages as English Coach.app; Windows packages as a folder named English Coach containing English Coach.exe (same for the GPU edition)*
- *Selections are forced to a blue background (fixing green selections on some systems)*
- *Chinese voice dropdown widened (no longer truncated on Windows), with trailing blank rows and excess scrolling removed*
- *During synthesis the 'Generating audio' text persists until completion, with the progress bar occupying about 40% of the window, centered slightly right with clearance on the right*

## v1.9.3 — 2026-06-28

**修复中文离线朗读截断 · 译文区选区稳定 · 多项界面优化**

*Fixed truncated Chinese offline playback · stable target-area selections · assorted UI improvements*

- 修复中文离线朗读长文本被截断（按标点切句分段合成，避免 Kokoro token 上限静默截断）
- 选区联动改为仅『原文→译文』单向，译文区选择不再被刷新重置
- 翻译历史文件改为 txt 纯文本
- 翻译历史按钮图标改为列表横线样式（与更新说明区分）
- 翻译按钮用网格真正居中，不再因左侧按钮增多而偏右
- 合成进度：文字并入左侧状态栏，进度条加长放右侧

- *Fixed long Chinese text being truncated during offline playback (text is now split at punctuation and synthesized in segments, avoiding Kokoro's silent token-limit truncation)*
- *Selection linking changed to source-to-target only, so selections in the target area are no longer reset by refreshes*
- *Translation history files changed to plain text*
- *Translation history button icon changed to a list-lines style, distinguishing it from the change log*
- *The translate button is now truly centered using a grid, instead of drifting right as buttons were added on the left*
- *Synthesis progress: the text merged into the status bar on the left with a longer progress bar on the right*

## v1.9.2 — 2026-06-28

**修复新环境 ctranslate2 因 setuptools 过新缺 pkg_resources**

*Fixed ctranslate2 failing in new environments due to a too-new setuptools missing pkg_resources*

- 构建脚本在装 ctranslate2 前固定 setuptools<81，解决新版移除 pkg_resources 导致 Argos 离线翻译导入失败

- *The build scripts now pin setuptools below 81 before installing ctranslate2, resolving Argos offline translation import failures caused by newer releases removing pkg_resources*

## v1.9.1 — 2026-06-28

**修复 Windows GPU 打包脚本无法运行（换行符与编码）**

*Fixed the Windows GPU build script failing to run (line endings and encoding)*

- 修复 Build Windows GPU.bat 因换行符为 LF、含中文注释导致命令被截断、无法运行
- 所有 .bat 脚本统一为纯 ASCII + CRLF 换行（GBK 控制台安全）

- *Fixed Build Windows GPU.bat failing to run because LF line endings combined with Chinese comments truncated commands*
- *All .bat scripts standardized to pure ASCII with CRLF line endings (safe for GBK consoles)*

## v1.9.0 — 2026-06-27

**翻译按钮防闪 · 历史改 MD · 进度条优化 · GPU 打包脚本**

*Flicker-free translate button · history in Markdown · progress bar improvements · GPU build script*

- 翻译按钮文字不再变化（不闪动），状态提示移到底部状态栏
- 翻译历史改用可读的 Markdown 文本格式（任意文本/浏览器打开都清晰，不再乱码）
- 合成音频进度提示加文字『正在生成音频…』，进度条加长、左文右条、留白匀称
- 上一条/历史按钮缩小到与复制粘贴一致，间距统一；撤回图标改为逆时针箭头
- 按钮气泡提示字号缩小；历史弹窗内悬停气泡字号放大到正文大小
- 暂停时拖动进度条，青色已读实时跟随（未松手也刷新）
- 朗读按钮激活时喇叭图标同步反色
- 选区联动响应更快，降低首次朗读读整段的概率
- 新增 Windows GPU 加速打包脚本（EnglishCoach-GPU 环境 + CUDA），Kokoro 自动用 GPU
- 构建脚本更名 Build MacOS.sh / Build Windows.bat / Build Windows GPU.bat

- *The translate button's label no longer changes (no flicker); status messages moved to the bottom status bar*
- *Translation history switched to readable Markdown text (clear in any text editor or browser, no more garbled characters)*
- *Audio synthesis progress now shows 'Generating audio...' with a longer bar, text on the left and bar on the right, evenly spaced*
- *Previous and History buttons shrunk to match copy and paste, with unified spacing; the undo icon changed to a counter-clockwise arrow*
- *Button tooltip font size reduced; hover tooltips inside the history dialog enlarged to body text size*
- *Dragging the progress slider while paused updates the cyan read position live (refreshing before you release)*
- *The speaker icon inverts in sync when the play button is active*

## v1.8.1 — 2026-06-27

**中文离线朗读修复 · 选区联动位置加权 · 合成进度提示 · 多项打磨**

*Chinese offline playback fix · position-weighted selection linking · synthesis progress · assorted polish*

- 修复中文离线朗读缺 pypinyin 等依赖（已补入打包）
- 移除会 404 的 Bella+Sarah 混合音（HF 无该现成文件）
- 选区联动加入位置加权与段落感知：相同词句按位置就近匹配，结果不再离谱
- 合成语音较慢时状态栏提示，超过约 1 秒显示忙碌进度条
- 历史弹窗：按钮改为『查看历史文档/重新载入/关闭』三等宽，预览限宽无横向滚动条
- 上一条原文按钮换更大图标
- 设置：显示隐藏与查看日志按钮等宽；取消/保存改中文并统一取消在左保存在右

- *Fixed Chinese offline playback missing pypinyin and related dependencies (now bundled)*
- *Removed the Bella+Sarah blended voice, which returned 404 (no such prebuilt file on Hugging Face)*
- *Selection linking gained position weighting and paragraph awareness: identical words are matched by proximity, so results are no longer wildly off*
- *The status bar reports slow speech synthesis, showing a busy progress bar after about one second*
- *History dialog: buttons changed to three equal-width actions (View History Document / Reload / Close) with a width-limited preview and no horizontal scrollbar*
- *Larger icon for the previous-source button*
- *Settings: Show/Hide and View Log buttons made equal width; Cancel and Save relabeled in Chinese and consistently ordered with Cancel left, Save right*

## v1.8.0 — 2026-06-27

**翻译历史 · 日志 · 修复 Kokoro 缺 ordered_set · Windows 图标**

*Translation history · logging · fixed Kokoro missing ordered_set · Windows icon*

- 修复 Kokoro 缺少 ordered_set 依赖导致离线朗读不可用（已补入打包）
- 新增翻译历史：原文区删除键右侧加『上一条原文』与『历史』两个按钮
- 历史弹窗按天分组，每条显示开头提示，悬停蓝色高亮并气泡显示全文，点选可载入并翻译
- 新增日志：出错记录写入用户数据目录，设置面板加『查看日志』按钮
- 历史与日志统一存放在系统用户数据目录（win:%APPDATA% / mac:Application Support）
- Windows 应用图标改回铺满尺寸（不再显小）；macOS 图标不变
- 选区联动匹配更智能：英文吸附到整词，不停在半个单词中间

- *Fixed Kokoro missing the ordered_set dependency, which made offline playback unavailable (now bundled)*
- *New translation history: Previous Source and History buttons added right of the source area's delete key*
- *The history dialog groups entries by day, shows an opening snippet for each, highlights on hover in blue with a full-text tooltip, and loads plus translates the entry you pick*
- *New logging: errors are written to the user data directory, with a View Log button added to Settings*
- *History and logs are stored together in the system user data directory (%APPDATA% on Windows, Application Support on macOS)*
- *The Windows application icon fills its canvas again (no longer appearing small); the macOS icon is unchanged*
- *Smarter selection linking: English snaps to whole words instead of stopping mid-word*

## v1.7.1 — 2026-06-27

**修复外置硬盘导致 Kokoro 不可用 · 朗读高亮与选区联动优化**

*Fixed Kokoro being unavailable on external drives · playback highlight and selection linking improvements*

- 修复 Kokoro 因 conda 在外置 SSD 上读时区文件被 macOS 拒绝（Operation not permitted）导致离线朗读不可用；自动改用系统时区库，并给出权限设置指引
- 朗读高亮不再改变字色（黑字变白字），只改背景颜色，更清爽
- 灰色联动区朗读时保持灰色，读到处变青色，读完恢复灰色（不再变蓝、不消失）
- 下载音频记住上次选择的格式（wav/mp3）作为默认
- 交换原文译文时，选区随之继承到新原文区并自动联动新译文区

- *Fixed Kokoro being unavailable for offline playback when conda lives on an external SSD and macOS denied reading the timezone file (Operation not permitted); the system timezone library is now used, with guidance for the permission setting*
- *Playback highlighting no longer changes the text color (black to white) and only changes the background, for a cleaner look*
- *The gray linked area stays gray while being read, turning cyan at the reading position and returning to gray afterwards (no longer turning blue or disappearing)*
- *Audio download remembers the last chosen format (wav/mp3) as the default*
- *Swapping source and target carries the selection into the new source area and links it to the new target area automatically*

## v1.7.0 — 2026-06-26

**Kokoro 打包落地 · 音质提升 · 音频格式可选 · 设置面板优化**

*Kokoro bundling completed · better audio quality · selectable audio format · Settings improvements*

- Kokoro 离线朗读依赖钉死兼容 Big Sur 的版本（torch 2.2.2 + transformers 4.40.2 + spaCy 英文模型）
- 英文离线嗓音默认改为 Heart（盲测最像真人），新增 Nova 与 Bella+Sarah 混合音
- 下载音频可选 wav（无损）或 mp3（压缩），按需转换
- Argos 离线模型缓存改放 EnglishCoach-models/argos 子目录（win/mac）
- 帮助文档新增系统要求（macOS/Windows 版本、空间、未签名解除拦截等），便于分享
- 设置：Key 输入框限宽右侧留白、显示/隐藏按钮居中、滚动条不再挡字、下拉悬停蓝色统一
- Key 标签简化（GPT/Gemini/GLM/豆包/HY-MT）
- 构建脚本加固：醒目确认并强制校验 conda 环境，杜绝误装到 base

- *Kokoro offline playback dependencies pinned to Big Sur-compatible versions (torch 2.2.2, transformers 4.40.2 and the spaCy English model)*
- *Default English offline voice changed to Heart (the most human-sounding in blind testing), with Nova and a Bella+Sarah blend added*
- *Audio downloads can be wav (lossless) or mp3 (compressed), converted on demand*
- *Argos offline model cache moved to an EnglishCoach-models/argos subdirectory (Windows and macOS)*
- *Help documentation gained system requirements (macOS/Windows versions, disk space, unblocking unsigned apps) to make sharing easier*
- *Settings: key inputs width-limited with right clearance, Show/Hide button centered, scrollbars no longer covering text, and unified blue dropdown hover*
- *Key labels simplified (GPT/Gemini/GLM/Doubao/HY-MT)*

## v1.6.0 — 2026-06-26

**修复闪退与 Kokoro 打包 · 重播缓存 · 多项界面优化**

*Fixed crashes and Kokoro bundling · replay cache · assorted UI improvements*

- 修复选择文字时的闪退（选区联动跨线程刷新高亮的崩溃，已加锁保护）
- 修复 Kokoro 打包缺失 language_tags 等数据导致离线朗读不可用
- 无变化时再次点朗读，直接重播已生成音频，不再重新合成
- 修复原文区有选区时朗读，青色不覆盖蓝色选区的问题（与译文区一致）
- 卡拉OK字幕提前量回调到中间值，更贴合声音
- 选区联动匹配更稳，异常不再影响主流程
- 引擎名简化：GPT / Gemini / GLM-4-Flash / 豆包 / HY-MT 等
- 界面标签去掉冒号；『进度』改为『朗读进度』
- 设置：显示隐藏按钮缩短、窗口变窄并自动换行、多风格翻译默认开启

- *Fixed a crash when selecting text (selection linking refreshed highlights across threads; now protected by a lock)*
- *Fixed Kokoro bundling missing language_tags and other data, which made offline playback unavailable*
- *Pressing play again with nothing changed replays the already-generated audio instead of re-synthesizing*

## v1.5.0 — 2026-06-26

**选区联动 · 新增 Google 官方引擎 · 朗读与界面多项打磨**

*Selection linking · new official Google engine · playback and UI polish*

- 新增选区联动：选一侧文字，临时翻译后在另一侧灰色高亮最匹配区间，可直接朗读
- 新增『Google -API-Key联网』官方云翻译 Basic v2 引擎（免费版保留不变）
- 帮助文档补充各引擎的模型、收费、稳定性说明，便于甄别
- 卡拉OK字幕加大提前量，修复再次出现的滞后
- 原文区选区朗读高亮与译文区一致；读完保留普通蓝色选区（可正常取消/重选）
- 朗读时按钮变青绿背景，暂停仍保持，停止/读完恢复
- 只有当前朗读语种的嗓音改动才打断朗读（改另一语种嗓音不打断）
- 中文嗓音移到左、英文嗓音移到右；窗口最窄时不再与设置按钮重叠
- 更改翻译引擎后自动触发翻译
- Kokoro 离线朗读报错时显示真实原因，便于排查

- *New selection linking: select text on one side and the closest matching range is highlighted in gray on the other side after a temporary translation, ready to be read aloud*
- *New 'Google -API-Key online' official Cloud Translation Basic v2 engine (the free version is unchanged)*
- *Help documentation now covers each engine's model, pricing and reliability to make choosing easier*
- *Increased karaoke subtitle lead time, fixing lag that had reappeared*
- *Source-area selection playback highlighting now matches the target area; after reading, a normal blue selection remains (cancelable and reselectable as usual)*
- *The play button takes a teal background while reading, keeps it while paused, and returns to normal on stop or completion*
- *Only changing the voice for the language currently being read interrupts playback (changing the other language's voice does not)*

## v1.4.0 — 2026-06-26

**新增 8 个 LLM 翻译引擎 · 多风格翻译**

*Eight new LLM translation engines · multi-style translation*

- 新增 OpenAI GPT、Google Gemini、Claude、智谱GLM-4-Flash、文心一言、字节豆包、通义千问、Kimi 八个大模型引擎（均需 API Key）
- 所有 LLM 引擎统一走 OpenAI 兼容接口，设置中分别填 Key
- 新增『多风格翻译』开关：选用 LLM 引擎时，主译文不变，下方附书面/口语/俚语/美式英式等多种辅助译法
- 设置页 Key 较多，改为可滚动

- *Added eight large-model engines: OpenAI GPT, Google Gemini, Claude, Zhipu GLM-4-Flash, ERNIE, Doubao, Qwen and Kimi (all require an API key)*
- *All LLM engines use the OpenAI-compatible interface, with separate keys entered in Settings*
- *New multi-style translation toggle: with an LLM engine the main translation is unchanged and formal, casual, slang, US and UK variants are appended below*
- *The Settings page became scrollable to accommodate the many keys*

## v1.3.0 — 2026-06-26

**新增 Kokoro 本地离线朗读 · 引擎/嗓音标注联网离线 · 多项修复**

*New Kokoro local offline playback · online/offline labels for engines and voices · assorted fixes*

- 新增 Kokoro 本地离线朗读引擎：无需联网、CPU 即可、原生对齐时间戳，卡拉OK更精准
- 嗓音标注来源：edge-tts 标『-线上联网』，Kokoro 标『-离线本地』
- 引擎名标注联网方式：Google/DeepL/DeepSeek/HunYuan 联网，Argos 本地离线
- 修复原文区选区朗读无青蓝覆盖；修复朗读结束后蓝色选区无法取消
- 朗读失败不再反复弹窗打扰，并提示可改用离线嗓音
- 字幕加入提前量补偿，跟声音更齐；选区朗读字幕只在选区内推进
- 保存音频记住上次目录；离线为 wav、在线为 mp3，文件名 EC_语种_嗓音_日期_时间
- 关于页：联系方式一行、版权用标准英文写法

- *New Kokoro local offline playback engine: no internet required, runs on CPU, with native alignment timestamps for more accurate karaoke*
- *Voices labeled by source: edge-tts marked 'online' and Kokoro marked 'offline local'*
- *Engines labeled by connectivity: Google, DeepL, DeepSeek and Hunyuan online, Argos local offline*
- *Fixed the source area lacking the teal overlay during selection playback; fixed blue selections being uncancelable after playback finished*
- *Playback failures no longer trigger repeated popups and now suggest switching to an offline voice*
- *Subtitles gained lead-time compensation for tighter sync; selection playback advances subtitles only within the selection*
- *Saving audio remembers the last directory; offline saves as wav and online as mp3, named EC_language_voice_date_time*

## v1.2.2 — 2026-06-25

**字幕提前补偿 · 选区字幕只走选区 · 关于页排版**

*Subtitle lead compensation · selection subtitles stay in the selection · About page layout*

- 卡拉OK字幕加入提前量补偿，跟声音对得更齐（中英文都不再慢半拍）
- 修复选区朗读时字幕仍从全文头走到尾的问题，现在只在选区内推进
- 关于页：网址与邮箱一行、两个电话另起一行，版权恢复 © 符号
- 关于页主标题下方空行高度与其它文档一致

- *Karaoke subtitles gained lead-time compensation for tighter audio sync (no longer half a beat behind in either language)*
- *Fixed subtitles running from the start of the whole text during selection playback; they now advance only within the selection*
- *About page: website and email on one line with phone numbers on the next, and the copyright symbol restored*
- *The blank line under the About page's main title now matches the other documents*

## v1.2.1 — 2026-06-25

**卡拉OK更精准 · 选区朗读恢复 · 音频命名优化**

*More accurate karaoke · selection playback restored · audio naming improvements*

- 卡拉OK高亮改用播放器真实位置同步，更精准（暂停时位置准确）
- 恢复『选中部分朗读』：选区显示蓝底，读到处覆盖青蓝绿，读完恢复蓝色
- 朗读高亮色改为偏青蓝、降饱和，更柔和
- 保存音频记住上次保存目录；文件名改为 EC_语种_嗓音_日期_时间（中文嗓音用拼音）
- 标题字号略增大（仍克制）；原文/译文区字号再放大
- 关于页联系方式与版权信息更新

- *Karaoke highlighting now syncs to the player's real position for better accuracy (correct position while paused)*
- *Restored reading a selection aloud: the selection shows a blue background, turns teal at the reading position and returns to blue when finished*
- *Playback highlight color shifted toward a softer, less saturated teal*
- *Saving audio remembers the last directory; filenames changed to EC_language_voice_date_time (Chinese voices use pinyin)*
- *Title font size increased slightly (still restrained); source and target area fonts enlarged further*
- *About page contact details and copyright information updated*

## v1.2.0 — 2026-06-25

**卡拉OK高亮独立时钟驱动 · 符号翻译 · 多项界面优化**

*Karaoke highlighting driven by an independent clock · symbol translation · assorted UI improvements*

- 卡拉OK高亮改为纯独立时钟驱动，彻底脱离播放器状态，两平台稳定逐词高亮
- 无词边界时按字符比例估算，保证仍有高亮兜底
- 新增标点/符号翻译：如 . → dot、（ → 左括号，引擎无能为力时由内置词典兜底
- 单个英文单词、过短文本也会尽力翻译出含义
- Windows 下拉弹窗去掉多余滚动条
- 原文/译文区字号放大一号，更醒目
- 文档主标题下方增加空行，排版更匀称

- *Karaoke highlighting now runs on a fully independent clock, decoupled from player state, for stable word-by-word highlighting on both platforms*
- *When word boundaries are unavailable, timing is estimated by character ratio so highlighting still works*
- *New punctuation and symbol translation: a period becomes 'dot' and a full-width parenthesis becomes 'left parenthesis', with a built-in dictionary covering what engines cannot*
- *Single English words and very short text are now translated as far as possible*
- *Removed the redundant scrollbar from Windows dropdown popups*

## v1.1.9 — 2026-06-25

**卡拉OK高亮改用底层着色（修复 macOS 不显示）· 下拉排版匀称**

*Karaoke highlighting moved to low-level formatting (fixing macOS) · balanced dropdown layout*

- 卡拉OK高亮改用 QSyntaxHighlighter 底层着色，修复 macOS/Big Sur 完全不显示高亮的问题
- 朗读时逐词背景变青绿，随进度递增，读完恢复
- 下拉列表去掉底部多余空白，外边框单层均匀，行距匀称

- *Karaoke highlighting now uses QSyntaxHighlighter-level formatting, fixing highlights not appearing at all on macOS Big Sur*
- *While reading, each word's background turns teal in turn, advancing with progress and restoring when finished*
- *Dropdown lists lost their trailing blank space, with a single even outer border and balanced line spacing*

## v1.1.8 — 2026-06-25

**下拉项加大行距 · 文档标题确实缩小 · 按钮等宽**

*Larger dropdown line spacing · document titles genuinely smaller · equal-width buttons*

- 下拉列表选项行距加大，文字不再重叠；弹窗去掉底部缝隙
- 文档标题改用更可靠的方式渲染，确实缩小到接近正文
- 设置中 Save 与 Cancel 按钮等宽

- *Dropdown item line spacing increased so text no longer overlaps, and the popup's bottom gap removed*
- *Document titles now render through a more reliable method and are genuinely reduced to near body-text size*
- *Save and Cancel buttons in Settings made equal width*

## v1.1.7 — 2026-06-25

**卡拉OK高亮改用墙上时钟 · 文档标题再缩小 · 弹窗去白边**

*Karaoke highlighting driven by a wall clock · smaller document titles · popup white edges removed*

- 卡拉OK逐词高亮改用独立时钟驱动，不再依赖播放器位置，macOS 也能逐词推进
- 文档（关于/更新/帮助）标题字号改用更可靠的方式设置，确实缩小到接近正文
- 下拉弹出列表去掉上下白边、深色背景
- 暂停/继续时高亮位置正确衔接

- *Word-by-word karaoke highlighting now runs on an independent clock instead of the player position, so it advances on macOS too*
- *Document titles (About, Change Log, Help) use a more reliable font-size mechanism and are genuinely close to body text*
- *Dropdown popups lost their top and bottom white edges and use a dark background*
- *Highlight position resumes correctly when pausing and continuing*

## v1.1.6 — 2026-06-25

**修复下载报错 · 下拉弹窗加宽 · 缩窄不重叠**

*Download error fix · wider dropdown popups · no overlap when narrowed*

- 修复下载音频第二次报『只读文件系统』错误：默认保存到「下载」文件夹
- 下载文件名自动命名：EnglishCoach_日期_编号.mp3（编号自增）
- 下载按钮换成更直观的下载图标
- 下拉弹出列表加宽，完整显示选项、两侧留空隙、去掉上下白边
- 修复窗口缩到最小时顶部控件与设置图标重叠

- *Fixed a read-only file system error on the second audio download: files now default to the Downloads folder*
- *Downloads are named automatically as EnglishCoach_date_number.mp3 with an incrementing number*
- *Download button replaced with a more intuitive download icon*
- *Dropdown popups widened to show options in full with clearance on both sides and no top or bottom white edges*
- *Fixed top controls overlapping the settings icon when the window is at its minimum size*

## v1.1.5 — 2026-06-25

**修复崩溃 · 内存播放提速 · 卡拉OK与下载音频**

*Crash fix · faster in-memory playback · karaoke and audio download*

- 修复反复朗读/拖动/退出时的崩溃（朗读线程安全退役与回收）
- 改为内存直接播放，不再生成临时 mp3，启动播放更快
- 修复卡拉OK逐词高亮（时间轴换算修正 + 高频刷新）
- 朗读中改参数时进度条停在当前位置，不再归零
- 新增「下载音频」按钮：点击才生成 mp3 文件保存
- 按钮文案精简：朗读原文 / 朗读译文 / 停止朗读，播放时显示 暂停/继续朗读
- 下拉框去掉选中对号、加蓝色高亮（含 macOS），并尽量收窄

- *Fixed crashes when repeatedly reading, dragging or quitting (playback threads now retire and are reclaimed safely)*
- *Playback moved to memory instead of generating a temporary mp3, so it starts faster*
- *Fixed word-by-word karaoke highlighting (timeline conversion corrected plus higher refresh rate)*
- *Changing parameters while reading leaves the progress bar at its current position instead of resetting it*
- *New Download Audio button: an mp3 file is generated and saved only when clicked*
- *Button labels simplified to Read Source / Read Target / Stop, showing Pause and Resume during playback*

## v1.1.4 — 2026-06-24

**修复卡拉OK高亮 · 窗口可缩窄 · 进度条不归零**

*Karaoke highlighting fix · window can be narrowed · progress bar no longer resets*

- 修复卡拉OK逐词高亮无效：改用高频定时器驱动，高亮随声音顺滑推进
- 朗读中更改设置时，进度条停在当前位置，不再跳回开头
- 修复窗口过宽且无法缩窄：朗读控件分两行排布，窗口可自由调窄
- 下拉框完整显示且不过度拉伸；悬停项目显示蓝色高亮
- 文档标题字号确认缩小到接近正文

- *Fixed word-by-word karaoke highlighting not working: a high-frequency timer now drives it so highlights advance smoothly with the audio*
- *Changing settings while reading leaves the progress bar at its current position instead of jumping back to the start*
- *Fixed the window being too wide and impossible to narrow: playback controls now span two rows so the window resizes freely*
- *Dropdowns display in full without over-stretching, and hovered items show a blue highlight*
- *Document title font size confirmed reduced to near body text*

## v1.1.3 — 2026-06-24

**卡拉OK式朗读高亮 · 进度条 · 选区朗读**

*Karaoke-style playback highlighting · progress bar · selection playback*

- 朗读时按真实词级时间戳逐词高亮已读内容（青绿色），类似 MV 字幕
- 选中部分文字后点朗读，只朗读选中的部分
- 新增播放进度条，可拖动实时调整播放位置
- 朗读按钮改为「开始/暂停/继续朗读」三态切换
- 朗读中更改嗓音或语速，自动以新设置重读并跳回大致进度
- 所有下拉框再加宽，鼠标悬停项目显示蓝色高亮
- 更新/使用/关于文档标题字号再缩小一号
- macOS 程序图标四周留白，显示更精致协调

- *While reading, content already spoken is highlighted word by word in teal using real word-level timestamps, like music video subtitles*
- *Selecting text and pressing play reads only the selection*
- *New playback progress bar that can be dragged to change position in real time*
- *The play button became a three-state toggle: Play, Pause and Resume*
- *Changing voice or speed while reading automatically re-reads with the new settings and returns to roughly the same position*
- *All dropdowns widened further, with a blue highlight on hovered items*

## v1.1.2 — 2026-06-24

**修复 Argos 偶发翻译失败 · 下拉箭头改尖角号**

*Fixed intermittent Argos translation failures · chevron dropdown arrow*

- 修复 Argos 离线翻译时好时坏的问题：翻译前确保模型已就绪并自动重试
- 下拉框右侧箭头改为扁平尖角号（V 形），无边框

- *Fixed Argos offline translation working only intermittently: the model is now confirmed ready before translating, with automatic retries*
- *The dropdown arrow on the right became a flat chevron (V shape) without a border*

## v1.1.1 — 2026-06-24

**中英嗓音分离 · 界面与样式优化**

*Separate Chinese and English voices · interface and styling improvements*

- 朗读嗓音拆分为「英文嗓音」「中文嗓音」两个下拉，按文本语种自动取用
- 英文嗓音不再被迫去读中文，避免乱兜底；两个嗓音选择均会记住
- 第一排标签改为「目标语言」「翻译引擎」
- 「使用说明」去掉 Readme 字样
- 更新说明 / 使用说明 / 关于 的标题字号再缩小一号
- 下拉框与滑竿的尖角图标改为扁平无边框风格
- 修复 Windows 状态栏右下角灰色拖拽块

- *Playback voices split into separate English Voice and Chinese Voice dropdowns, selected automatically by the text's language*
- *English voices are no longer forced to read Chinese, avoiding nonsensical fallbacks; both voice choices are remembered*
- *First row labels changed to Target Language and Translation Engine*
- *Removed the word Readme from the User Guide*
- *Change Log, User Guide and About titles reduced by one more size step*
- *Chevron icons on dropdowns and sliders changed to a flat, borderless style*

## v1.1.0 — 2026-06-23

**下拉框加宽 · 按钮顺序调整 · 模型仓库复用**

*Wider dropdowns · button order adjusted · shared model repository*

- 源/目标语言、引擎、嗓音下拉框按最长内容精确加宽，文字完整显示
- 原文 / 译文操作按钮顺序调整为：复制、粘贴、删除
- 编译脚本支持公共模型仓库（~/EnglishCoach-models）：模型下载一次，所有版本复用
- 模型下载改用 HTTP/1.1，规避 argos-net 的 HTTP/2 中断问题

- *Source/target language, engine and voice dropdowns widened precisely to their longest content so text displays in full*
- *Source and target action buttons reordered to Copy, Paste, Delete*
- *Build scripts support a shared model repository (~/EnglishCoach-models): models download once and are reused by every build*
- *Model downloads switched to HTTP/1.1 to work around HTTP/2 interruptions from argos-net*

## v1.0.9 — 2026-06-23

**Argos 离线翻译彻底打通 · 内置中英模型**

*Argos offline translation fully working · bundled Chinese-English models*

- Argos 离线翻译现已完全可用：中英互译，无需联网、无需 Key
- 内置中英离线模型，安装即用，不再需要运行时下载
- 彻底移除 PyTorch 依赖（通过兼容层让 Argos 在无 torch 环境运行）
- 兼容 macOS Big Sur 等较老系统的依赖版本组合
- 断网时也能用 Argos 完成中英翻译

- *Argos offline translation is now fully functional for Chinese-English in both directions, with no network and no key required*
- *Chinese-English offline models are bundled, so they work on install with no runtime download*
- *PyTorch dependency removed entirely (a compatibility layer lets Argos run without torch)*
- *Dependency versions chosen for compatibility with older systems such as macOS Big Sur*
- *Argos can complete Chinese-English translation even with no internet connection*

## v1.0.8 — 2026-06-23

**界面重排 · 朗读自动重试 · Argos 报错优化**

*Interface rearranged · automatic playback retry · clearer Argos errors*

- 顶部重排：第一排左侧为 源/目标语言与引擎，右侧为 设置/更新/帮助/关于
- 原文 / 译文标题与 粘贴/复制/删除 按钮下移至「翻译」大按钮同一排
- 朗读合成失败时静默重试，最多 3 次，仍失败才提示
- Argos 加载失败时显示真实原因，便于定位（区分源码运行 / 打包缺失）
- 编译脚本新增 argostranslate 导入校验，装不上会提前明确报错
- 下拉框加宽，自动检测等文字显示完整
- 关于页邮箱与网址并列显示

- *Top row rearranged: source/target languages and engine on the left, Settings/Change Log/Help/About on the right*
- *Source and target titles plus the Paste/Copy/Delete buttons moved down to the same row as the large Translate button*
- *Failed speech synthesis retries silently up to three times before showing a message*
- *Argos load failures now show the real cause, distinguishing running from source versus a missing bundled package*
- *Build scripts gained an argostranslate import check that fails early and clearly if installation went wrong*
- *Dropdowns widened so entries like Auto Detect display in full*

## v1.0.7 — 2026-06-23

**修复中文朗读与离线翻译 · 多项界面优化**

*Fixed Chinese playback and offline translation · assorted UI improvements*

- 修复中文朗读全部失败：读中文时自动切换到中文嗓音；新增 3 个中文嗓音
- 修复 Argos 英译中报错：改用正确的翻译路径并处理英语中转
- Argos 中英模型随程序预置打包，安装后即可离线翻译（无需再下载）
- 移除有道朗读引擎与「失败换嗓音」提示（已不再需要）
- 朗读时更改嗓音或语速即时生效（自动以新设置重读当前栏）
- 原文 / 译文区新增「粘贴」按钮
- 源语言 / 目标语言 / 引擎下拉框自适应宽度，文字显示完整
- 帮助与更新说明的标题字号缩小，更协调
- 关于页开发者信息追加邮箱 vfx@Strilen.com

- *Fixed Chinese playback failing entirely: a Chinese voice is now selected automatically for Chinese text, and three Chinese voices were added*
- *Fixed errors translating English to Chinese with Argos by using the correct translation path and handling English as a pivot*
- *Argos Chinese-English models are bundled with the program, so offline translation works right after install with no download*
- *Removed the Youdao playback engine and the switch-voice-on-failure prompt (no longer needed)*
- *Changing voice or speed during playback takes effect immediately, re-reading the current pane with the new settings*
- *New Paste button in the source and target areas*

## v1.0.6 — 2026-06-23

**翻译新增 Argos 离线 与 混元 引擎 · 双平台打包**

*New Argos offline and Hunyuan engines · builds for both platforms*

- 翻译新增「Argos (离线)」引擎：纯本地、无需 Key、无需联网（首次用会提示下载语言模型）
- 翻译新增「混元 HY-MT」引擎：腾讯混元在线翻译（需腾讯云 Key）
- 翻译引擎增至 5 个：Google（默认）、DeepL、DeepSeek、Argos、混元
- 同时提供 macOS 与 Windows 两套编译脚本

- *New Argos (offline) engine: entirely local, no key and no network required (language models are downloaded on first use)*
- *New Hunyuan HY-MT engine: Tencent Hunyuan online translation (requires a Tencent Cloud key)*
- *Translation engines increased to five: Google (default), DeepL, DeepSeek, Argos and Hunyuan*

## v1.0.5 — 2026-06-23

**朗读新增有道引擎 · 嗓音失败可改选**

*New Youdao playback engine · switch voices after a failure*

- 朗读新增「有道」嗓音（国内免费、无需 Key），作为微软 edge-tts 的备选
- 微软 edge-tts 仍为默认，音质更佳、嗓音更多
- 某嗓音合成失败时，弹出列表让你改选其它嗓音并立即重试
- 朗读改用流式/二进制写入，更稳定

- *New Youdao voices for playback (free in China, no key required) as an alternative to Microsoft edge-tts*
- *Microsoft edge-tts remains the default, with better audio quality and more voices*
- *When a voice fails to synthesize, a list appears so you can pick another and retry immediately*
- *Playback switched to streaming/binary writing for better stability*

## v1.0.4 — 2026-06-23

**兼容旧版 macOS · 界面与交互优化**

*Compatibility with older macOS · interface and interaction improvements*

- 兼容 macOS Big Sur：使用 PyQt6 6.4.x，解决 IOKit 符号缺失导致无法启动
- 新增输入即译：停止输入约 0.8 秒后自动翻译（手动「翻译」按钮仍保留）
- 左右两栏拉开间距，不再重叠；复制与删除按钮间距收紧
- 引擎下拉中「Google」不再显示「(免费)」后缀
- 朗读改用流式合成，更稳定；嗓音失效时给出明确提示
- 移除「开发者介绍」页，作者信息并入「关于」（开发者：Strilen Liu）

- *Compatible with macOS Big Sur: using PyQt6 6.4.x resolves a missing IOKit symbol that prevented startup*
- *New translate-as-you-type: translation runs automatically about 0.8 seconds after you stop typing (the manual Translate button remains)*
- *Left and right panes spaced apart so they no longer overlap; the gap between Copy and Delete tightened*
- *The Google entry in the engine dropdown no longer shows a (Free) suffix*
- *Playback switched to streaming synthesis for stability, with a clear message when a voice is unavailable*
- *Removed the Developer page; author information merged into About (developer: Strilen Liu)*

## v1.0.3 — 2026-06-22

**修复界面不弹出 · 兼容 macOS Big Sur · 全新图标**

*Fixed the window not appearing · macOS Big Sur compatibility · new icon*

- 修复打包后无报错但窗口不显示的问题（强制窗口前置并抢占焦点）
- 音频后端初始化失败不再阻止主界面启动（朗读不可用时自动降级）
- 兼容 macOS 11 Big Sur：打包设置最低系统版本为 11.0
- 启动异常时弹窗显示具体错误，便于排查
- 全新应用图标：构图居中、字形圆润、双色配色

- *Fixed the packaged app showing no error but no window either (the window is now forced to the front and takes focus)*
- *Audio backend initialization failure no longer blocks the main window from starting (playback degrades gracefully)*
- *Compatible with macOS 11 Big Sur: builds now target a minimum system version of 11.0*
- *Startup errors are shown in a dialog with the specific cause, making diagnosis easier*
- *New application icon: centered composition, rounded letterforms and a two-color scheme*

## v1.0.2 — 2026-06-22

**改用 PyInstaller 打包并加入应用图标**

*Switched to PyInstaller packaging and added an application icon*

- macOS 打包改用 PyInstaller，更可靠地处理 PyQt6 的 Qt 插件，解决持续的启动崩溃
- 新增应用图标（A/文 + 翻开的书），编译后 .app / Dock 显示专属图标
- 窗口与任务栏同步使用新图标

- *macOS packaging moved to PyInstaller, which handles PyQt6's Qt plugins more reliably and resolves the persistent startup crashes*
- *New application icon (A/文 with an open book), shown for the built .app and in the Dock*
- *The window and taskbar use the new icon as well*

## v1.0.1 — 2026-06-22

**修复 macOS 打包启动崩溃**

*Fixed the macOS packaged app crashing at startup*

- 修复 py2app 打包后出现「Launch error」无法启动的问题
- 打包时完整收录 PyQt6 插件（cocoa 平台、SVG、多媒体），解决 Qt 无法初始化
- 编译脚本加入 conda 环境自动激活

- *Fixed the Launch error that prevented the py2app build from starting*
- *Builds now include the full set of PyQt6 plugins (cocoa platform, SVG, multimedia), resolving Qt initialization failures*
- *Build script now activates the conda environment automatically*

## v1.0.0 — 2026-06-22

**首个正式版本**

*First release*

- 新增「翻译」功能：默认 Google 免费引擎（无需 Key），DeepL / DeepSeek 可作备选
- 翻译支持中英双向与自动检测，可一键互换
- 新增「朗读」功能：基于 edge-tts 在线语音合成，多嗓音、可调语速
- 新增「版本更新说明与管理」面板
- 新增「关于」「Readme / 帮助」「开发者介绍」页面
- 内置 SVG 图标系统

- *New translation feature: Google's free engine by default (no key required), with DeepL and DeepSeek as alternatives*
- *Translation supports Chinese-English in both directions plus auto-detection, with one-click swapping*
- *New playback feature: online speech synthesis via edge-tts with multiple voices and adjustable speed*
- *New change log and version management panel*
- *New About, Readme/Help and Developer pages*
- *Built-in SVG icon system*
