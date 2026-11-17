# json2latex-report

把 **JSON 块列表**或**简易 Markdown** 一键转成可编译的 `.tex`，可选直接出 PDF——纯 Python 标准库，无第三方依赖。

> **示例数据为虚构**：`demo.json`、`note.md` 里的产线名、工位名、作者、指标均为虚构示例，不对应任何真实企业、产线或客户。

## 最快上手
```json
{ "meta": { "title": "Hello", "author": "示例作者" },
  "blocks": [
    { "type": "heading", "level": 1, "text": "第一节" },
    { "type": "para", "text": "最小示例，支持 `代码` 与 $E=mc^2$。" } ] }
```
```bash
python3 texgen.py hello.json -o out/hello.tex --compile
```

预期产物：`out/hello.tex`（约 400 字节）+ `out/hello.pdf`（1 页，含标题、段落、行内代码与公式）。只要 `.tex` 就去掉 `--compile`。

首次用 tectonic 编译需联网拉取约 60 MB bundle，之后离线可用；换 TeX Live 或指定引擎见 [docs/engine.md](docs/engine.md)。

## 安装

```bash
# Python 依赖：无。要求 Python >= 3.7
git clone https://github.com/uniwuyuan/json2latex-report.git
cd json2latex-report

# LaTeX 引擎（二选一）
#   A. tectonic：单文件二进制，推荐；放到 ./bin/tectonic 或加入 PATH
#   B. TeX Live / MacTeX：确保 xelatex（或 lualatex）在 PATH 中，中文需 ctex 宏包
```

引擎探测顺序、tectonic 缓存位置、英文模板等细节见 [docs/engine.md](docs/engine.md)。

## 更多运行方式

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

## JSON 结构

顶层 `meta` + `blocks`，块类型共 12 种（heading / para / table / code / math / figure …）。

<details>
<summary>展开完整块类型表</summary>

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

</details>

完整字段说明见 [docs/json-schema.md](docs/json-schema.md)。

## 高级用法

### Markdown 输入

`# 标题`、`- / 1.` 列表、`| 表格 |`、```` ``` ```` 代码块、`$$ 公式 $$`、`> 引用`、空行分段；
`---` 包裹的 YAML 头里 `title/author/date` 会填进导言区。

```bash
python3 texgen.py note.md -o out/note.tex --from md --compile
```

细节见 [docs/markdown.md](docs/markdown.md)。

### 批量出稿

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
docs/              引擎说明、JSON 结构、Markdown 支持
out/               产物目录（已忽略）
```

## 说明

- 首次使用 tectonic 需网络拉取 bundle，之后离线可用
- 页眉默认显示章节名与页码，去掉可在导言区加 `\pagestyle{plain}`
- **本项目在 AI 辅助下构建，核心逻辑经人工审查与故障注入验证**

## License

[MIT](LICENSE)
