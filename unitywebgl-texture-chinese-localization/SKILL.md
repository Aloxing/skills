---
name: unitywebgl-texture-chinese-localization
description: Unity WebGL 游戏运行时视觉汉化与递归交互探索：用真实浏览器打开游戏、持续截图，结合 AI 视觉与 OCR 识别全屏文字、图片内嵌文字和贴图资源，给可操作控件编号并生成标注截图，逐次点击、截图确认、深度优先递归探索所有界面/弹窗/分页，确认真正的开始游戏入口，把未汉化视觉内容交给 AI 翻译与图像编辑，定位原始贴图回填后重新运行浏览器复测，产出视觉汉化数据库与报告，并按开源许可管理汉化字体版权。Use when the user asks to 汉化 Unity WebGL 游戏里的图片文字、按钮贴图、Logo、CG、UI 贴图，通过浏览器自动化逐个界面探索并列出未汉化内容，自动点击寻找开始游戏入口，生成标注截图与视觉汉化清单，或核查汉化字体的版权合规。
---

# Unity WebGL 运行时视觉汉化与递归交互探索

## 适用场景

- 游戏已部署、能在浏览器中运行（线上 URL 或本地 WebGL 地址），没有可供常规文本解包的完整信息。
- 需要靠真实运行画面发现常规文本提取容易遗漏的内容：按钮背景贴图、图片文字、Logo、封面、主菜单背景、角色介绍图、任务插画、剧情 CG、横幅、技能/道具/装备图标、地图标注、预渲染界面。
- 需要自动识别并标注可操作控件，逐个点击确认，递归探索所有可访问界面，并确认真正的开始游戏入口。
- 需要把视觉资源做成中文化并在真实浏览器中验证，同时保证字体版权合规。

不适用于：文本资源解包、批量文本翻译、UABEA 回填等构建资源汉化流程（交给 `unitywebgl-code-chinese-localization`）。

## 流程依据

完整定位、原则、阶段流程与数据结构以 [references/runtime-visual-localization.md](references/runtime-visual-localization.md) 为唯一依据；字体选型、授权、技术适配与交付标记以 [references/font-license-compliance.md](references/font-license-compliance.md) 为准。开始任何操作前先完整阅读这两份文档，不得凭记忆或猜测执行其中未描述的操作，不得擅自增删或改写文档中的操作要求。

## 核心原则（必须始终遵守）

1. 运行时观察优先：所有分析以真实浏览器运行画面为依据，不得只靠 HTML、JavaScript 或资源文件推测界面；每次重要交互都必须有对应截图证据。
2. 递归探索：不得只看首页；从初始界面开始，每发现一个新界面就继续识别控件并探索，采用深度优先搜索，每个新界面都走「截图 → 识别控件 → 分配 ID → 点击 → 等待 → 再截图 → 判断变化 → 入队」。
3. 视觉汉化优先：重点关注贴图、图片内嵌文字、图标文字、装饰性文字等常规文本流程遗漏的内容。
4. 反重复探索：用截图感知哈希、OCR 文字集合、界面布局、控件分布建立界面指纹；动态数字/时间/动画变化不算新界面，但同一界面出现新弹窗、状态、分页仍需重新检查。
5. 诚实执行：不伪造点击结果，不把截图编辑结果冒充游戏实际修改结果，不把未访问的界面标记为已检查；遇到自动化能力限制必须明确记录。
6. 安全红线：删除存档、重置游戏、购买、消耗付费货币、真实支付、发布内容、账号退出、不可逆剧情选择、可能覆盖进度的操作，只截图识别记录，不自动确认执行。
7. 字体合规：新增/替换/生成的中文字体必须来源可追溯、许可证可核实、使用方式被授权、版权声明完整；许可不明确时标记 `FONT_LICENSE_UNVERIFIED` 转入人工审核，不得宣称已通过版权审核。

## 工具映射（先检测本机已有能力，禁止重复安装）

| 能力 | 使用方式 |
|---|---|
| 浏览器自动化 | 优先复用已有 Playwright 或 browser-use 类工具：打开 URL、等待 Unity 初始化、截图、按坐标点击、读取控制台、注入脚本；本机无此类工具时如实记录限制 |
| 截图与标注 | `scripts/annotate_screenshots.py`（Pillow）：按控件登记表绘制带编号矩形框、批量裁剪小字区域供 OCR；标签文字自动使用自带字体库，可用 `ANNOTATE_FONT` 覆盖 |
| OCR / 区域分析 | 复用已有 OCR、OpenCV；分辨率大时裁剪局部 OCR，但必须保留原始完整截图 |
| 视觉识别 | 直接把截图作为视觉输入，识别文字、语言、控件形态、悬停与按钮状态 |
| 图像汉化 | 用 ImageGen 编辑截图或原始贴图，配合 `imagegen` skill 写提示词：只改文字区域，保留构图、背景、角色、图标形状、色彩、光影、透明通道与分辨率 |
| 回填与复测 | 定位原始 PNG/JPG/TGA/Sprite/Texture2D 并替换，清缓存后重新运行，浏览器逐项截图验证 |

坐标规则：一律以实际截图尺寸为基准；浏览器窗口尺寸、设备缩放或画布尺寸变化后必须重算坐标；CSS 像素与设备像素不一致时给脚本传 `--scale`。截图默认使用原生分辨率，不裁切重要 UI、不压缩到影响 OCR。

## 执行 SOP（严格按顺序，细节见参考文档十六节）

1. 环境检测：确认浏览器自动化、截图、OCR、图像编辑能力齐全；缺失项记录，不重复安装。
2. 启动游戏：打开 URL，等待 Unity WebGL 初始化与加载进度结束；加载完成不等于可交互，必须截图确认，必要时先点击页面获取焦点；不得绕过安全提示、登录或授权页面。
3. 初始截图：保存 `000_initial.png`、`001_loading.png`、`002_main_menu.png` 等真实出现的状态，不为不存在的状态造假记录。
4. 全屏视觉扫描：按顶部/左侧/右侧/底部/中央/弹窗/背景/图片贴图分区识别文字，记录原文、截图、区域、坐标、所属 UI、是否贴图、是否已汉化。
5. 控件识别：不只看 DOM，Unity 常只暴露一个 Canvas；用视觉识别 + OCR + 元素检测 + 坐标探索找按钮、标签页、滚动区、可点击图片与图标，并结合形状、边框、悬停与点击反馈。
6. 编号标注：为每个控件登记 `screen_id`、`control_id`、`label`、`translated_label`、`type`、`bounds`、`center`、`clickable`、`visited`、`screenshot`，生成唯一编号的标注截图，不覆盖原图。
7. 逐个安全点击：每点一个重要按钮就截图确认，判断是否打开新界面、弹窗、切场景、出新文字、加载中、状态变化、无变化或报错；无变化时等待、复截图、检查双击/延迟/未关弹窗，不得无限重复点击。
8. 递归探索：对每个新界面重复 4–7 步；无法返回时用游戏自身返回/关闭/菜单，必要时按已记录导航状态重新进入；不得在未记录状态时随意刷新。
9. 确认开始游戏入口：区分 Start / Play / New Game / Continue / Begin / Enter 的真实语义，按「截图 → 标记 → 分析周围文字 → 点击 → 等待 → 再截图 → 判断是否进入角色选择/难度/剧情/正式场景」确认；进入可操作场景后标记 `START_GAME_CONFIRMED = true` 并保留完整进入过程截图。
10. 进入游戏后继续观察：HUD、任务提示、对话框、NPC 交互、暂停菜单、角色状态、地图、技能按钮、背包入口、系统提示、新手教程；需要移动或交互时先识别操作方式，按低风险原则执行。
11. 动态与隐藏内容：弹窗、悬停/按下/禁用/选中/锁定状态、滚动列表、分页逐页截图，剧情对白与提示用关键帧采样，不能只查第一页、不能每帧都交给 AI。
12. 汇总未汉化内容：建立统一记录，状态使用 `pending`、`translating`、`editing`、`imported`、`verified`、`failed`、`manual_review`，状态必须真实更新。
13. 翻译与图像编辑：按界面/场景/UI 类/图标组/背景组/文字风格分组，统一术语与字体风格；翻译用简体中文、符合游戏语境、保持简洁并适配原图空间；图像编辑只改文字区域，不得重绘无关内容、不得改变按钮位置尺寸。
14. 区分模式 A / 模式 B：截图上做汉化只作视觉参考、对比图和效果检查，不能替代游戏内原始贴图；要让游戏真正显示中文，必须定位原始视觉资源、确认与截图文字对应、编辑后核对尺寸格式透明通道并回填。
15. 复测：重新运行游戏，逐项确认替换成功、中文正常、尺寸正确、透明通道保留、无黑块白边溢出、图标与 UI 不错位、游戏正常加载；每个修改界面保留「修改前截图 / AI 修改结果 / 回填后实际截图」三方对比。
16. 验证失败时按文档 12.2 排查：资源定位、是否真正加载、重复贴图、Addressables 缓存、浏览器缓存、尺寸格式、引用关系，然后重测；不得仅凭图片编辑成功就标记完成。
17. 生成报告：输出探索报告与视觉汉化报告，统计真实数据并按文档十四节交付文件。

## 记录与目录

沿用文档结构：探索阶段维护 `Exploration/`（`screen_registry.json`、`control_registry.json`、`visited_screens.json`、`pending_controls.json`、`interaction_log.json`）；汉化阶段维护 `VisualLocalization/`（`OriginalScreenshots/`、`AnnotatedScreenshots/`、`CroppedRegions/`、`ImageAssets/`、`AI_Edited/`、`Verified/`、`Failed/`、`Reports/`、`Database/`）。标注截图仅用于分析，绝不作为游戏最终资源；原始截图必须保留。

## 探索终止条件

满足以下才能宣布探索完成：初始界面已扫描；开始游戏入口已确认或记录了无法进入的原因；已发现界面的控件均已检查；可安全访问的子界面已递归探索；图片文字已全部登记；动态内容已完成合理抽样；未汉化视觉内容已进入任务数据库；无法自动探索的内容已明确记录。不得把一次会话的有限探索描述成已穷尽游戏全部内容，随机事件、隐藏剧情、时间条件或特定进度解锁的内容须单独标记为未覆盖。

## 字体合规要点

先查原游戏自带中文字体，其次 OFL 开源字体（思源黑体/宋体、Noto Sans/Serif SC、霞鹜文楷），再是明确允许非商业使用、嵌入、修改的字体；禁止来源不明、未授权商业字体、从其他游戏提取或仅个人预览许可的字体。使用前核对 LICENSE，登记 `FontManifest.json`（来源、版本、许可、是否允许修改/嵌入/随游戏分发），并检查 TTF/OTF/WebGL 加载、TMP 图集、Fallback 与字符覆盖。免费下载不等于可自由使用。详见字体参考文档。

本 skill 自带 `assets/FontLibrary/`：5 个 OFL 字体（思源黑体/思源宋体 Regular OTF、Noto Sans/Serif SC 可变 TTF、霞鹜文楷 Regular）、`License/OFL/` 许可证原文、`License/LICENSE_RECORDS/FONT_SOURCES.md` 与含 sha256 的 `FontManifest.json`。选字优先从该库取，项目内按文档 18.4 建库时整库复制并保留许可证与清单。注意可变字体在 Pillow/FreeType 默认实例为 Thin(100)/ExtraLight(200)，需要常规字重时先固定实例：`python -m fontTools.varLib.instancer "NotoSansSC[wght].ttf" wght=400 --output=NotoSansSC-Regular.ttf`（OFL 允许修改，该字族无保留字体名）。

## 交付

必须提供：浏览器探索报告（启动结果、初始截图、开始游戏入口确认、界面/按钮/点击/未访问/人工确认数量）、视觉汉化报告（文字总量、已有中文、未汉化、贴图文字、图像编辑、回填、验证、失败、待人工数量）、数据库 JSON、报告 Markdown、截图与 AI 编辑结果；若用户要求真正完成游戏视觉汉化，还需修改后的原始图片资源、资源定位信息、回填记录、修改后完整 WebGL 文件与复测截图。字体按 `font-license-compliance.md` 第 18.8 节输出名称、版本、来源、许可证、LICENSE、修改记录与分发情况。

## 资源

- [references/runtime-visual-localization.md](references/runtime-visual-localization.md)：角色定位、核心原则、环境检测、全屏扫描、控件识别与标注、自动点击与递归探索、开始游戏入口确认、图片汉化与图像编辑、动态内容、任务数据库、批量处理、复测、终止条件、交付与 SOP 全文。
- [references/font-license-compliance.md](references/font-license-compliance.md)：字体版权合规、使用优先级、推荐开源字体库与目录、自动选字策略、版权检查、技术适配、交付与强制规则全文。
- [scripts/annotate_screenshots.py](scripts/annotate_screenshots.py)：`python scripts/annotate_screenshots.py annotate --registry control_registry.json --out-dir AnnotatedScreenshots [--scale 2]` 生成编号标注图；`... crop --registry control_registry.json --out-dir CroppedRegions --enlarge 2 [--scale 2]` 批量裁剪控件区域供 OCR；控件清单未写截图路径时用 `--screenshot` 指定。标签字体优先用自带字体库，可用环境变量 `ANNOTATE_FONT` 覆盖。
- [assets/FontLibrary/](assets/FontLibrary)：自带 OFL 中文字体库、许可证原文与 `FontManifest.json`（来源、版本、授权范围、sha256）；做图像汉化、贴图回填与字体交付时优先使用，交付时按清单和 `License/` 记录名称、版本、来源、许可证与分发情况。
