# LaTeX 引擎探测与说明

`texgen.py` 在 `--compile` 时按以下顺序自动探测引擎，也可用 `--engine` 显式指定。

1. `./bin/tectonic` —— 随仓库放置的单文件引擎（`bin/` 已在 `.gitignore` 中，需自行下载，不随仓库分发）
2. `tectonic` —— PATH 中的 tectonic
3. `xelatex` / `lualatex` / `pdflatex` —— TeX Live 系

## tectonic（推荐）

- 单文件二进制，无需安装整套 TeX 发行版
- 首次编译会联网拉取 bundle（约 60 MB），之后缓存在 `~/.cache/Tectonic`，可离线使用
- 下载地址：<https://github.com/tectonic-typesetting/tectonic>
- 放到 `./bin/tectonic` 或加入 `PATH` 即可被自动探测

## TeX Live / MacTeX

- 中文走 `ctexart` + Fandol 字体，需预装 `ctex` 宏包与中文字体包
- 确保 `xelatex`（或 `lualatex`）在 `PATH` 中

## 英文模板

`--en` 切换为 `article` + `lmodern`，不使用 ctex，适合纯英文文档。

## 页眉

页眉默认显示章节名与页码；去掉可在导言区加 `\pagestyle{plain}`。
