"""common.py — 3 種の Office ビルダーが共有する小道具（文字幅・文書名置換・Mermaid 画像化・ID 収集）。"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import mdparse as md

REQ_DIR = "docs/03-requirements"
SOURCE_DIRS = ("docs/01-rfp", "docs/03-requirements")  # Office 化の対象（直下の *.md。reviews/ と extracted/ は除く）
SOURCE_PATHS: dict[str, Path] = {}


def text_width(s: str) -> int:
    """全角=2・半角=1 で数えた表示幅。"""
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 1
    return w


def col_weights(header: list[str], rows: list[list[str]], min_w: int = 4, max_w: int = 60) -> list[int]:
    n = len(header)
    ws = []
    for i in range(n):
        cells = [header[i]] + [r[i] if i < len(r) else "" for r in rows]
        longest = max((max((text_width(line) for line in c.split("\n")), default=0) for c in cells), default=0)
        avg = sum(text_width(c) for c in cells) / max(len(cells), 1)
        w = int(0.6 * longest + 0.4 * avg)
        # 見出し語（最長の 1 語）と ID は折り返させない
        head_floor = min(max((text_width(t) for t in re.split(r"[／/（）()\s]", header[i]) if t), default=0), 12)
        ids = [c.strip() for c in cells[1:] if md.ID_RE.fullmatch(c.strip())]
        id_floor = max((text_width(c) for c in ids), default=0)
        ws.append(max(min_w, head_floor, id_floor, min(max_w, w)))
    return ws


def col_floors(header: list[str], rows: list[list[str]], ids_only: bool = False) -> list[int]:
    """折り返させたくない最小幅（半角単位）：ID 値と、見出しの最長語（12 まで）。ids_only なら ID 値だけ。"""
    out = []
    for i, h in enumerate(header):
        head = 0 if ids_only else min(max((text_width(t) for t in re.split(r"[／/（）()\s]", h) if t), default=0), 12)
        ids = [r[i].strip() for r in rows if i < len(r) and md.ID_RE.fullmatch(r[i].strip())]
        out.append(max([head] + [text_width(c) for c in ids]))
    return out


class DocNamer:
    """本文中のファイル名（requirements.md 等）を、納品文書での呼び名に置き換える。"""

    def __init__(self, mapping: dict[str, str]):
        # 長いファイル名から置換（non-functional-requirements.md が requirements.md に誤一致しないよう境界付き）
        self.pairs = []
        for src in sorted(mapping, key=len, reverse=True):
            pat = re.compile(r"(?<![\w./-])(?:docs/03-requirements/)?" + re.escape(src) + r"(?![\w-])")
            self.pairs.append((pat, mapping[src]))

    def __call__(self, s: str) -> str:
        for pat, name in self.pairs:
            s = pat.sub(name, s)
        return s


def mermaid_to_png(code: str, mode: str, cache_dir: Path) -> Path | None:
    """mode=auto: mmdc が PATH にあれば使う / npx: npx 経由で取得 / source・off: 画像化しない。"""
    if mode not in ("auto", "npx"):
        return None
    cmd = None
    if shutil.which("mmdc"):
        cmd = ["mmdc"]
    elif mode == "npx" and shutil.which("npx"):
        cmd = ["npx", "-y", "@mermaid-js/mermaid-cli"]
    if not cmd:
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(code.encode("utf-8")).hexdigest()[:16]
    src, out = cache_dir / f"{key}.mmd", cache_dir / f"{key}.png"
    if out.exists():
        return out
    src.write_text(code, encoding="utf-8")
    try:
        subprocess.run(cmd + ["-i", str(src), "-o", str(out), "-b", "white", "-s", "2"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    except Exception:
        return None
    return out if out.exists() else None


def load_sources(root: Path) -> dict[str, list]:
    """docs/01-rfp/*.md と docs/03-requirements/*.md をパースして {ファイル名: blocks} を返す。"""
    out = {}
    for rel in SOURCE_DIRS:
        d = root / rel
        if d.is_dir():
            for p in sorted(d.glob("*.md")):
                if p.name in ("README.md", "INDEX.md"):
                    continue
                out[p.name] = md.parse_file(p)
                SOURCE_PATHS[p.name] = p
    return out


def body_blocks(blocks: list, drop_preamble: bool = True) -> list:
    """先頭の H1（文書タイトル）と、最初の H2 までの前書き（この文書について・作成日など）を除く。"""
    if not drop_preamble:
        return blocks
    for i, b in enumerate(blocks):
        if isinstance(b, md.Heading) and b.level == 2:
            return blocks[i:]
    # H2 が無い文書は H1 だけ落とす
    return [b for b in blocks if not (isinstance(b, md.Heading) and b.level == 1)]


def preamble_quote(blocks: list) -> list:
    """「この文書について」の引用ブロック（最初の H2 より前）を返す。"""
    out = []
    for b in blocks:
        if isinstance(b, md.Heading) and b.level == 2:
            break
        if isinstance(b, md.Quote):
            out.append(b)
    return out


PLACEHOLDER_RE = re.compile(r"YYYY-MM-DD|YYYY-MM|〈[^〉]{0,20}〉|（記入）|（未記入）|TODO|TBD|\.\.\.|…（|（…）|¥…|N 件")
