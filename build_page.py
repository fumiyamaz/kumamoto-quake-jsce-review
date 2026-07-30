"""生成レポートを、GitHub Pages で配信できる完全なHTML文書にして index.html に書き出す。

生成側（JSCE論文データレイクの `src/kumamoto_quake/build_report.py`）が出力する
HTML は、`<!DOCTYPE>` や `<head>` を持たない**断片**である。断片のまま配信すると
ブラウザが互換モード（quirks mode）で描画し、viewport 指定も無いためモバイルで崩れる。
このスクリプトが外枠を付けて、単体で成立する文書にする。

  uv run python build_page.py                        # 既定のパスから取り込む
  uv run python build_page.py <生成HTMLのパス>        # パスを指定する

やっていること:
  1. 断片から <title> を取り出して <head> へ移す（断片では body 直下にあり不正）
  2. DOCTYPE・lang・charset・viewport・description・color-scheme を付ける
  3. 絵文字のファビコンを data URI で埋める（favicon.ico の404を防ぐ）
  4. テンプレート由来の開発用コメントを取り除く（内部のファイル名が出ないように）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = (HERE.parent / "jsce" / "reports" / "熊本地震" / "熊本地震_統合レポート.html")
DEST = HERE / "index.html"

DESCRIPTION = ("平成28年（2016年）熊本地震を扱った土木学会全国大会論文の振り返り。"
               "論文一覧、年次・部門・テーマ別の比較、応急対応から復旧復興までの実務示唆。")
# 城の絵文字。外部リクエストを増やさないよう SVG を data URI で埋める
FAVICON = ("data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
           "%3Ctext y='.9em' font-size='90'%3E%F0%9F%8F%AF%3C/text%3E%3C/svg%3E")


def strip_dev_comments(html: str) -> str:
    """HTMLコメントを除去する。<script> 内に `<!--` が無いことを確かめてから行う。"""
    for block in re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.S | re.I):
        if "<!--" in block:
            raise SystemExit("script 内に <!-- がある。コメント除去は安全に行えない。")
    return re.sub(r"<!--.*?-->", "", html, flags=re.S)


def wrap(fragment: str) -> str:
    m = re.search(r"<title>(.*?)</title>", fragment, re.S | re.I)
    if not m:
        raise SystemExit("断片に <title> が無い")
    title = " ".join(m.group(1).split())
    body = fragment[:m.start()] + fragment[m.end():]     # title は head へ移すので取り除く
    body = strip_dev_comments(body).strip()

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{DESCRIPTION}">
<link rel="icon" href="{FAVICON}">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    if not src.exists():
        raise SystemExit(f"生成HTMLが見つからない: {src}\n"
                         "生成側で build_report を実行してから、パスを指定して再試行する。")

    out = wrap(src.read_text(encoding="utf-8"))
    DEST.write_text(out, encoding="utf-8")

    print(f"[in ] {src}  ({src.stat().st_size / 1024:.0f} KB)")
    print(f"[out] {DEST}  ({DEST.stat().st_size / 1024:.0f} KB)")
    for need in ("<!DOCTYPE html>", 'lang="ja"', 'name="viewport"', "<title>"):
        assert need in out, need
    print("      DOCTYPE / lang / viewport / title を確認")


if __name__ == "__main__":
    main()
