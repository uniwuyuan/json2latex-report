# JSON 结构

顶层为 `meta` + `blocks`：

```json
{ "meta": {"title": "标题", "author": "作者", "date": "2026 年 11 月"},
  "blocks": [ {"type": "heading", "level": 1, "text": "第一章"} ] }
```

## 块类型

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

## 转义规则

正文自动转义 `% & # _ $ { } ~ \ ^`；`$...$` 内的 LaTeX 原样保留，公式可直接写。
