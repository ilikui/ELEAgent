# PDF 阅读集成：book-to-skill

ELEAgent 增加了一个面向 VS Code / GitHub Copilot 的 PDF-to-Skill 工作流，参考上游项目：

- 上游仓库：[virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill)
- 上游 README：[使用方式与支持格式](https://github.com/virgiliojr94/book-to-skill/blob/master/README.md)
- 上游 Skill：[SKILL.md](https://github.com/virgiliojr94/book-to-skill/blob/master/SKILL.md)
- ELEAgent 集成 Skill：`.github/skills/pdf-book-to-skill/SKILL.md`

## 设计说明

上游方案把确定性文档提取与 Agent 结构化知识生成分开：先提取文本和元数据，再由 Agent 整理框架、决策规则、反模式与按需章节文件。本仓库新增的 `pdf-book-to-skill` 将这个流程适配到 ELEAgent，特别强调工程文档页码证据、芯片手册/原理图复核和保密边界。

**本次提交不是完整复制上游仓库。** ELEAgent 保留自己的 PDF 页面提取脚本，同时提供适配本仓库的 Skill 指令；需要上游的多格式抽取器时，可以按下面的方式安装官方上游 Skill。这样避免复制一个会快速演进的整套依赖，同时保留上游维护与许可证信息。

## 在 VS Code / GitHub Copilot 使用

### 方案 A：使用 ELEAgent 内置 Skill 工作流

在 ELEAgent 仓库根目录打开 VS Code，确认 Copilot 能读取 `.github/skills/`，然后让 Copilot：

> 使用 pdf-book-to-skill Skill 分析 `path/to/book.pdf`。先输出文档元信息、章节目录、提取覆盖率和待人工复核页，再生成章节化知识 Skill。不要改动原始 PDF，不要把生成的书籍内容提交到公开仓库。

快速提取 PDF 文本和页面图像：

```bash
python .github/skills/autosar-hw-code-traceability/scripts/extract_pdf.py path/to/book.pdf --out engineering/extracted/pdf_text --render
```

默认本地输出位于 `engineering/extracted/`，该目录已加入 `.gitignore`。

### 方案 B：安装上游 book-to-skill

上游支持 PDF、EPUB、DOCX、TXT、Markdown、HTML、RTF 等格式，具体能力与依赖以其当前文档为准。

可以将上游 Skill 安装到当前用户支持的 Agent Skills 目录。上游文档提供的方式包括：

```bash
npx skills add virgiliojr94/book-to-skill
```

也可以按上游仓库的安装说明手动安装。安装后先运行上游文档指定的依赖检查：

```bash
python scripts/extract.py --check
```

上面第二条命令需要在上游仓库或安装后的 Skill 对应目录执行，不能直接假设 ELEAgent 根目录存在该脚本。具体安装位置、命令和可用格式请以 [上游安装文档](https://github.com/virgiliojr94/book-to-skill/blob/master/docs/install.md) 为准。

## 推荐的知识文件结构

```text
engineering/library/<skill-slug>/
├── SKILL.md
├── chapters/
│   ├── ch01-foundations.md
│   └── ch02-methods.md
├── glossary.md
├── patterns.md
├── cheatsheet.md
└── sources.json
```

这只是建议结构，不会自动创建或覆盖用户文件。首次生成前先确认目标路径；更新已有知识 Skill 时，先对比旧文件并提出合并计划。

## AUTOSAR / ECU 工程使用要求

对芯片手册、AUTOSAR 标准、MCAL/BSW 文档或原理图：
1. 每个关键结论保留 PDF 页码、印刷页码（若不同）、章节和版本。
2. 原理图连线、引脚、极性、寄存器和公式必须复核原页，不能只相信提取文本。
3. 把文档知识与真实项目的 ARXML、ECUC、C 源码和测试证据分开记录。
4. 生成的知识 Skill 是参考资料，不等于当前 ECU 项目的验证证据。
5. 不将受限芯片手册、客户资料或由受版权保护书籍生成的知识 Skill 提交到公开仓库。

## 当前范围与后续扩展

当前集成提供 Skill 工作流和现有 PDF 提取器的连接说明；没有把上游所有解析器、测试和依赖完整 vendoring 到 ELEAgent，也没有在本次提交中自动转换某本实际 PDF。后续可以按需增加批量导入、章节边界检测、OCR 复核队列、Skill 链接校验和独立测试。
