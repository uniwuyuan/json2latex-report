# Markdown 输入支持范围

支持：`# 标题`、`- / 1.` 列表、`| 表格 |`、```` ``` ```` 代码块、`$$ 公式 $$`、`> 引用`、空行分段。

`---` 包裹的 YAML 头里 `title/author/date` 会填进导言区：

```markdown
---
title: 快速上手 texgen
author: 示例作者（虚构）
---
```

用法：

```bash
python3 texgen.py note.md -o out/note.tex --from md --compile
```
