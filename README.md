# json2latex-report

把 **JSON 块列表**或**简易 Markdown** 一键转成可编译的 `.tex`，可选直接出 PDF——纯 Python 标准库，无需第三方依赖。

> **示例数据为虚构**
> `demo.json`、`note.md` 中的产线名、工位名、作者、指标数值全部为虚构示例，不对应任何真实企业、产线或客户。

## 安装

```bash
# 1) Python 依赖：无。要求 Python >= 3.7
git clone https://github.com/uniwuyuan/json2latex-report.git
cd json2latex-report

# 2) 准备 LaTeX 引擎（二选一）
#    A. tectonic：单文件二进制，推荐
#       macOS/Linux 见 https://github.com/tectonic-typesetting/tectonic
#       下载后放到 ./bin/tectonic 或加入 PATH
#    B. TeX Live / MacTeX：确保 xelatex（或 lualatex）在 PATH 中，中文需 ctex 宏包
```

## 运行

```bash
# JSON → tex → PDF
python3 texgen.py demo.json -o out/demo.tex --compile

# Markdown → tex（YAML 头写 title/author/date）
python3 texgen.py note.md -o out/note.tex --from md --compile

# 只生成 tex，不编译
python3 texgen.py demo.json -o out/demo.tex

# 指定引擎与输出目录（相对当前工作目录）
python3 texgen.py demo.json -o build/report.tex --engine tectonic
```

## LaTeX 引擎说明

脚本按以下顺序自动探测，也可用 `--engine` 显式指定：

1. `./bin/tectonic` —— 随仓库放置的单文件引擎（`bin/` 已在 `.gitignore` 中，需自行下载）
2. `tectonic` —— PATH 中的 tectonic
3. `xelatex` / `lualatex` / `pdflatex` —— TeX Live 系

- **tectonic**：首次编译会联网拉取 bundle（约 60 MB），之后缓存在 `~/.cache/Tectonic`，可离线使用；不需要系统安装 TeX 宏包
- **TeX Live**：中文走 `ctexart` + Fandol 字体，需预装 `ctex` 与中文字体包
- 英文模板：`--en` 切换为 `article` + `lmodern`，不使用 ctex

## JSON 结构

```json
{ "meta": {"title": "标题", "author": "作者", "date": "2026 年 11 月"},
  "blocks": [ {"type": "heading", "level": 1, "text": "第一章"} ] }
```

| type | 关键字段 | 说明 |
| --- | --- | --- |
| `title` | text, subtitle, author, date, page | 题头；`page:true` 单独成封面页 |
| `toc` | — | 目录 + 分页 |
| `heading` | text, level(1-3), numbered | 章节标题 |
| `para` | text | 段落，支持 `**粗**` `*斜*` `` `代码` `` `$公式$` |
| `list` | items, ordered | 项目 / 编号列表 |
| `table` | header, rows, caption, align, width | booktabs 三线表；`align:"lccc"` |
| `code` | text, caption | Verbatim 代码块，长行自动折行 |
| `math` | text, display | 独立或行内公式 |
| `quote` | text | 引用块 |
| `figure` | path, caption, width | 插图，`width:"0.8"` 为线宽比例（路径相对输入文件） |
| `hrule` / `pagebreak` | — | 分隔线 / 分页 |

正文自动转义 `% & # _ $ { } ~ \ ^`；`$...$` 内的 LaTeX 原样保留，公式可直接写。

## Markdown 支持范围

`# 标题`、`- / 1.` 列表、`| 表格 |`、```` ``` ```` 代码块、`$$ 公式 $$`、`> 引用`、空行分段。
`---` 包裹的 YAML 头里 `title/author/date` 会填进导言区。

## 批量出稿

```bash
for f in reports/*.json; do
  python3 texgen.py "$f" -o "out/$(basename "${f%.json}").tex" --compile
done
```

## 目录结构

```
texgen.py          生成器（约 400 行，含 Markdown 解析与编译调用）
demo.json          示例数据（虚构）
note.md            示例 Markdown（虚构）
requirements.txt   依赖说明（无第三方依赖，Python >= 3.7）
out/               产物目录（已忽略）
```

## 说明

- 首次使用 tectonic 需网络拉取 bundle，之后离线可用
- 页眉默认显示章节名与页码，去掉可在导言区加 `\pagestyle{plain}`
- **本项目在 AI 辅助下构建，核心逻辑经人工审查与故障注入验证**

## License

[MIT](LICENSE)
