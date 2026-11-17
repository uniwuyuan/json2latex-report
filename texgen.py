#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
texgen.py — 数据驱动的 LaTeX 生成器（纯标准库，无第三方依赖）

输入：JSON block 列表，或简易 Markdown
输出：完整可编译的 .tex（可选直接调用引擎出 PDF）

块类型：
  title    {text, subtitle?, author?, date?}
  heading  {text, level:1|2|3, numbered?}
  para     {text}                       行内支持 **粗** *斜* `代码` $公式$
  list     {items:[...], ordered?:bool}
  table    {header:[...], rows:[[...]], caption?, align?:"lcr", width?}
  code     {text, caption?, lang?}
  math     {text, display?:bool}
  quote    {text}
  figure   {path, caption?, width?:"0.8"}
  toc      {}
  pagebreak{}
  hrule    {}

用法：
  python3 texgen.py demo.json -o out/demo.tex
  python3 texgen.py demo.json -o out/demo.tex --compile
  python3 texgen.py note.md  -o out/note.tex --from md
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def esc(s: str) -> str:
    return "".join(SPECIAL.get(c, c) for c in str(s))


def inline(s: str) -> str:
    """转义 + 行内标记。保护 $公式$ 与 `代码`，其余字符转义。"""
    maths, codes = [], []

    def keep_math(m):
        maths.append(m.group(0))
        return f"\x00M{len(maths) - 1}\x00"

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00C{len(codes) - 1}\x00"

    s = re.sub(r"\$[^$]+\$", keep_math, str(s))
    s = re.sub(r"`([^`]+)`", keep_code, s)
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\\emph{\1}", s)
    s = re.sub(r"\x00C(\d+)\x00", lambda m: r"\texttt{" + esc(codes[int(m.group(1))]) + "}", s)
    s = re.sub(r"\x00M(\d+)\x00", lambda m: maths[int(m.group(1))], s)
    return s


# ---------- 块渲染 ----------

def b_title(b, ctx):
    out = []
    out.append(r"\begin{titlepage}" if b.get("page") else "")
    out.append(r"\begin{center}")
    out.append(r"{\Huge\bfseries %s\par}" % esc(b["text"]))
    if b.get("subtitle"):
        out.append(r"\vspace{0.6em}{\Large %s\par}" % esc(b["subtitle"]))
    if b.get("author"):
        out.append(r"\vspace{2em}%s\par" % esc(b["author"]))
    if b.get("date"):
        out.append(r"%s\par" % esc(b["date"]))
    out.append(r"\end{center}")
    if b.get("page"):
        out.append(r"\end{titlepage}")
    return out


def b_heading(b, ctx):
    lvl = int(b.get("level", 1))
    star = "" if b.get("numbered", True) else "*"
    cmd = {1: "section", 2: "subsection", 3: "subsubsection"}.get(lvl, "paragraph")
    return [r"\%s%s{%s}" % (cmd, star, inline(b["text"]))]


def b_para(b, ctx):
    return [inline(b["text"]), ""]


def b_list(b, ctx):
    env = "enumerate" if b.get("ordered") else "itemize"
    out = [r"\begin{%s}" % env]
    for it in b["items"]:
        out.append(r"  \item %s" % inline(it))
    out.append(r"\end{%s}" % env)
    return out


def b_table(b, ctx):
    align = b.get("align") or "l" * max(1, len(b.get("header") or b["rows"][0]))
    width = b.get("width")
    if width:
        spec = "".join("p{%.3f\\linewidth}" % (float(width) / len(align)) for _ in align)
    else:
        spec = align
    out = [r"\begin{table}[htbp]", r"\centering"]
    if b.get("caption"):
        out.append(r"\caption{%s}" % inline(b["caption"]))
    out.append(r"\begin{tabular}{%s}" % spec)
    out.append(r"\toprule")
    if b.get("header"):
        out.append(" & ".join(r"\textbf{%s}" % inline(c) for c in b["header"]) + r" \\")
        out.append(r"\midrule")
    for row in b["rows"]:
        out.append(" & ".join(inline(c) for c in row) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    out.append(r"\end{table}")
    return out


def b_code(b, ctx):
    body = b["text"].rstrip("\n")
    out = []
    if b.get("caption"):
        out.append(r"\begin{center}\small %s\end{center}" % inline(b["caption"]))
    out.append(r"\begin{Verbatim}[breaklines=true,breakanywhere=true,fontsize=\small]")
    out.append(body)
    out.append(r"\end{Verbatim}")
    return out


def b_math(b, ctx):
    t = b["text"].strip()
    if b.get("display", True):
        return [r"\[", t, r"\]"]
    return ["$%s$" % t]


def b_quote(b, ctx):
    return [r"\begin{quote}", inline(b["text"]), r"\end{quote}"]


def b_figure(b, ctx):
    path = b["path"]
    if not os.path.isabs(path) and ctx.get("base"):
        path = os.path.join(ctx["base"], path)
    out = [r"\begin{figure}[htbp]", r"\centering",
           r"\includegraphics[width=%s\linewidth]{%s}" % (b.get("width", "0.8"), path)]
    if b.get("caption"):
        out.append(r"\caption{%s}" % inline(b["caption"]))
    out.append(r"\end{figure}")
    return out


def b_toc(b, ctx):
    return [r"\tableofcontents", r"\clearpage"]


def b_pagebreak(b, ctx):
    return [r"\clearpage"]


def b_hrule(b, ctx):
    return [r"\noindent\rule{\linewidth}{0.4pt}"]


RENDER = {
    "title": b_title, "heading": b_heading, "para": b_para, "list": b_list,
    "table": b_table, "code": b_code, "math": b_math, "quote": b_quote,
    "figure": b_figure, "toc": b_toc, "pagebreak": b_pagebreak, "hrule": b_hrule,
}


# ---------- 文档组装 ----------

PREAMBLE_ZH = r"""\documentclass[11pt,a4paper]{ctexart}
\usepackage[margin=2.4cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{fancyvrb}
\usepackage{fvextra}
\usepackage{xcolor}
\usepackage[hidelinks]{hyperref}
\linespread{1.35}
"""

PREAMBLE_EN = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.4cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{fancyvrb}
\usepackage{fvextra}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[hidelinks]{hyperref}
\linespread{1.2}
"""


def build_tex(blocks, meta=None, chinese=True, base_dir=None):
    meta = meta or {}
    ctx = {"base": base_dir}
    head = [PREAMBLE_EN if not chinese else PREAMBLE_ZH]
    if meta.get("title"):
        head.append(r"\title{%s}" % inline(meta["title"]))
    if meta.get("author"):
        head.append(r"\author{%s}" % inline(meta["author"]))
    if meta.get("date"):
        head.append(r"\date{%s}" % inline(meta["date"]))
    body = []
    if meta.get("title"):
        body += [r"\maketitle"]
    for b in blocks:
        fn = RENDER.get(b.get("type"))
        if not fn:
            raise SystemExit(f"未知块类型: {b.get('type')!r}")
        body += fn(b, ctx)
        body.append("")
    if meta.get("title") and meta.get("maketitle", True):
        head.append(r"\begin{document}")
    else:
        head.append(r"\begin{document}")
    return "\n".join(head) + "\n" + "\n".join(body) + "\n\\end{document}\n"


# ---------- 简易 Markdown 解析 ----------

def md_to_blocks(md: str):
    """支持 # 标题 / - 与 1. 列表 / | 表格 | / ``` 代码 / $$ 公式 / > 引用 / 空行分段。"""
    lines = md.splitlines()
    blocks, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append({"type": "code", "text": "\n".join(buf)})
            continue
        if s.startswith("$$"):
            buf = [s[2:]]
            i += 1
            while i < n and "$$" not in lines[i]:
                buf.append(lines[i])
                i += 1
            if i < n:
                buf.append(lines[i].split("$$")[0])
            i += 1
            blocks.append({"type": "math", "text": "\n".join(buf).strip()})
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)), "text": m.group(2)})
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[-: ]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            header, body = rows[0], rows[1:]
            blocks.append({"type": "table", "header": header, "rows": body})
            continue
        if re.match(r"^[-*+]\s+", s):
            items = []
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            blocks.append({"type": "list", "items": items})
            continue
        if re.match(r"^\d+[.)]\s+", s):
            items = []
            while i < n and re.match(r"^\d+[.)]\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+[.)]\s+", "", lines[i].strip()))
                i += 1
            blocks.append({"type": "list", "ordered": True, "items": items})
            continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append({"type": "quote", "text": " ".join(buf)})
            continue
        buf = []
        while i < n and lines[i].strip() and not re.match(
            r"^(#{1,3}\s|\||[-*+]\s|\d+[.)]\s|```|>|\$\$)", lines[i].strip()
        ):
            buf.append(lines[i].strip())
            i += 1
        blocks.append({"type": "para", "text": " ".join(buf)})
    return blocks


# ---------- 编译 ----------

def find_engine(prefer=None):
    order = [prefer] if prefer else []
    order += ["tectonic", "xelatex", "lualatex", "pdflatex"]
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "bin", "tectonic"), os.path.join(here, "bin", "tectonic")):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    for e in order:
        if e and shutil.which(e):
            return shutil.which(e)
    return None


def compile_pdf(tex_path, engine=None, keep_aux=True):
    eng = find_engine(engine)
    if not eng:
        return None, "未找到 LaTeX 引擎（tectonic/xelatex/lualatex/pdflatex）"
    d = os.path.dirname(os.path.abspath(tex_path))
    name = os.path.basename(tex_path)
    if "tectonic" in os.path.basename(eng):
        cmd = [eng, "-X", "compile", name]
    else:
        cmd = [eng, "-interaction=nonstopmode", "-halt-on-error", name]
    try:
        p = subprocess.run(cmd, cwd=d, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return None, "编译超时"
    pdf = os.path.join(d, os.path.splitext(name)[0] + ".pdf")
    if p.returncode != 0 or not os.path.exists(pdf):
        tail = (p.stdout or "")[-1500:] + (p.stderr or "")[-1500:]
        return None, tail
    if not keep_aux:
        for ext in (".aux", ".log", ".out", ".toc"):
            f = os.path.join(d, os.path.splitext(name)[0] + ext)
            if os.path.exists(f):
                os.remove(f)
    return pdf, None


def main():
    ap = argparse.ArgumentParser(description="JSON/Markdown → LaTeX 生成器")
    ap.add_argument("src", help="输入文件：.json（块列表或 {meta,blocks}）或 .md")
    ap.add_argument("-o", "--out", required=True, help="输出 .tex 路径")
    ap.add_argument("--from", dest="fmt", choices=["auto", "json", "md"], default="auto")
    ap.add_argument("--en", action="store_true", help="英文文档（article 类，不用 ctex）")
    ap.add_argument("--compile", action="store_true", help="生成后直接编译 PDF")
    ap.add_argument("--engine", help="tectonic|xelatex|lualatex|pdflatex")
    args = ap.parse_args()

    raw = open(args.src, encoding="utf-8").read()
    fmt = args.fmt
    if fmt == "auto":
        fmt = "md" if args.src.lower().endswith((".md", ".markdown")) else "json"

    if fmt == "md":
        meta = {}
        m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            raw = raw[m.end():]
        blocks = md_to_blocks(raw)
    else:
        data = json.loads(raw)
        if isinstance(data, list):
            meta, blocks = {}, data
        else:
            meta, blocks = data.get("meta", {}), data["blocks"]

    chinese = not args.en
    tex = build_tex(blocks, meta, chinese=chinese, base_dir=os.path.dirname(os.path.abspath(args.src)))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"[ok] 写出 {args.out}  ({len(tex)} 字节, {len(blocks)} 个块)")

    if args.compile:
        pdf, err = compile_pdf(args.out, args.engine)
        if pdf:
            print(f"[ok] 编译成功 {pdf} ({os.path.getsize(pdf)} 字节)")
        else:
            print("[warn] 编译失败:\n" + err)
            sys.exit(2)


if __name__ == "__main__":
    main()
