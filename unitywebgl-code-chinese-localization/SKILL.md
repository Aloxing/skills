---
name: unitywebgl-code-chinese-localization
description: 在仅有已发布的 Unity WebGL 构建、没有 Unity 工程和 C# 源码的条件下完成简体中文汉化与本地化修复：扫描 Build 目录、识别 Unity 版本与压缩格式、优先启用或复用游戏自带中文、批量提取/去重/翻译文本并用兼容方式回填 TextAsset、MonoBehaviour、AssetBundle、Addressables、修复 TMP 中文字体缺字与布局，通过本地 HTTP 服务和浏览器自动化验证，并按开源许可管理中文字体版权。Use when the user asks to 汉化/本地化 Unity WebGL 游戏、处理 *.data.unityweb、*.bundle 里的文本、修复中文显示方框或 TMP 字体、复用或补齐语言包，或核查汉化字体的版权合规。
---

# Unity WebGL 游戏汉化与本地化修复

## 适用场景

- 只有打包好的 WebGL 文件夹（index.html、Build、TemplateData），没有 Unity Editor 工程或 C# 源码。
- 目标是把游戏本地化为简体中文：启用隐藏中文、复用现有中文、补齐缺失文本、修复字体与排版。
- 需要在不破坏原始构建的前提下回填资源，并在浏览器中验证。

不适用于：要求热补丁注入桌面运行时（BepInEx、Harmony、XUnity）的场景。

## 流程依据

完整流程与操作细节以 [references/localization-workflow.md](references/localization-workflow.md) 为唯一依据；字体选型、授权与交付标记以 [references/font-license-compliance.md](references/font-license-compliance.md) 为准。开始任何操作前先完整阅读这两份文档，不得凭记忆或猜测执行其中未描述的操作。

## 核心原则（必须始终遵守）

1. 先检查，再汉化：禁止假设游戏没有中文；先扫描语言配置、语言包、隐藏语言选项和中文字体，存在完整中文时只改配置启用。
2. 优先级：先找中文，再补中文；先改配置，再改资源；先处理文本资源，再考虑二进制；先保证游戏能运行，再追求汉化完整度。
3. 最小改动：只修改需要汉化的文本，保留 Key、Path ID、GUID、引用关系、序列化结构和未修改字段；禁止用导出 JSON 整体覆盖原始资源。
4. 工具：先检测本地已安装工具，禁止重复下载；不臆造工具功能、命令参数和执行结果，gameloc 等工具使用前必须核实当前版本用法。
5. 翻译：去重后翻译，保护占位符、富文本、TMP 标签和转义字符；统一术语表；不翻译代码标识符、资源路径和内部 Key。
6. 字体：仅替换 TTF/OTF 不代表 TMP 图集已含中文；新增或替换字体必须满足「来源可追溯、许可证可核实、使用方式被授权、版权声明完整」，许可不明确时标记 `FONT_LICENSE_UNVERIFIED` 并转人工审核。
7. 安全与诚实：关键修改前备份；不破坏原始 WebGL Loader；未在浏览器验证前不得宣称汉化成功；无法自动处理的步骤明确说明原因和所需信息。

## 执行 SOP

1. 扫描 Build 文件夹，建立完整文件清单。
2. 识别 Unity 版本与资源压缩格式（依据文件头，不只看扩展名：Brotli、Gzip、Deflate、LZ4、LZMA、UnityFS）。
3. 检测本地工具是否就绪（Python、AssetStudio、UABEA、AssetRipper、解压工具、gameloc）。
4. 解压 WebGL DATA 文件，判断内部是 SerializedFile、AssetBundle 还是其他结构。
5. 扫描 AssetBundle 和 Addressables（catalog、Bundle 地址、依赖、Hash）。
6. 提取全部可识别文本，保留文件名、类型、Path ID、GUID、Bundle 名称与字段结构。
7. 检测是否存在已有中文语言包或隐藏中文选项。
8. 复用已有中文（简体保留、繁体按需转简体），筛选需要翻译的文本。
9. 文本去重、格式保护、术语统一。
10. 并发批量翻译（有缓存、重试、限流、断点续传、逐批落盘）。
11. 校验翻译结果：占位符数量、标签结构、变量名、Key 不变。
12. 使用兼容工具回填资源（TextAsset、MonoBehaviour、AssetBundle/Addressables）。
13. 检查中文字体与 TMP 图集，修复缺字、方框、标点和 Fallback。
14. 重建必要资源及压缩文件，保留原始目录结构和未修改文件。
15. 用本地 HTTP 服务启动游戏，禁止用 file:// 判断最终效果。
16. 浏览器自动化测试：启动、中文显示、布局、控制台错误，并截图留证。
17. 输出完整汉化项目、备份和报告。

## 文本提取优先级

1. TextAsset、JSON、CSV、XML、TXT。
2. MonoBehaviour、ScriptableObject、Localization Table、String Table、对话与配置数据。
3. Prefab、Scene、UI Text、TextMeshProUGUI、TMP Font Asset。
4. AssetBundle、Addressables、自定义序列化数据。

禁止逐个手动查看资源，优先批量导出；不得把 GUID、Hash、路径、Shader 名、变量名当作游戏文本翻译。

## 文本不在 DATA 中时

依次排查独立 AssetBundle、StreamingAssets、Addressables、外部 JSON、远程配置、动态语言包；只有资源层方案无法解决时才评估 WASM 字符串修补（高风险路径），不得直接认定文本一定在 WASM 中。

## 最终交付

必须提供：项目分析报告（Unity 版本、构建结构、压缩格式、原生中文与字体情况、所用工具）、汉化统计（总量/已有中文/新翻译/跳过/失败/待人工）、修改记录（文件、资源、语言配置、字体、Addressables、压缩）、测试报告（启动、中文显示、缺字、布局、控制台错误）、最终文件（完整汉化 WebGL 文件夹、原始备份、文本表、翻译缓存、修改记录、测试截图、汉化报告）。字体部分按字体文档第 16.8 节输出名称、版本、来源、许可证、LICENSE、修改记录与分发情况。

## 内置字体资源库

[assets/FontLibrary](assets/FontLibrary) 已预置字体文档 16.3 节列出的五款 OFL 1.1 中文字体（Regular/可变字重），目录结构遵循 16.4 节：

```
assets/FontLibrary/
├── Sans/       SourceHanSansSC/  NotoSansSC/
├── Serif/      SourceHanSerifSC/ NotoSerifSC/
├── Artistic/   LXGWWenKai/
├── License/    OFL/  LICENSE_RECORDS/
└── FontManifest.json
```

选用字体时：

1. 先按 16.5 节风格表从本库选择；优先保留原游戏字体风格。
2. 使用前核对 `FontManifest.json` 与 `License/OFL/` 中对应许可证原文，随游戏附带许可证和版权声明。
3. 思源黑体/宋体的保留字体名 "Source" 受限，生成子集或修改后不得沿用保留名。
4. 本库只提供基础字形文件；替换后仍须按流程处理 TMP Font Asset、图集、材质与引用，不能只替换 TTF/OTF 就宣称中文可显示。

## 资源

- [references/localization-workflow.md](references/localization-workflow.md)：角色定位、中文检查、项目结构识别、工具选择、提取/复用/翻译/回填、字体修复、浏览器验证、特殊情况、自动化策略与交付要求全文。
- [references/font-license-compliance.md](references/font-license-compliance.md)：字体版权合规、使用优先级、推荐开源字体库与目录、自动选字策略、版权检查、技术适配和交付规则全文。
- [assets/FontLibrary/FontManifest.json](assets/FontLibrary/FontManifest.json)：内置字体清单、版本、许可证、来源与使用场景。
