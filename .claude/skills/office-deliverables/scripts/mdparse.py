"""mdparse.py — 要件定義 Markdown を Office 出力用の中間 AST に変換する。

ブロック: Heading / Para / ListBlock / Table / Code / Quote / HR
インライン: Run(text, bold, italic, code, strike, link) の配列

markdown-it-py（CommonMark + table + strikethrough）でトークン化し、Office 生成に
必要な構造だけを残す。HTML コメントは捨てる。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from markdown_it import MarkdownIt

# --------------------------------------------------------------------------- AST


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    strike: bool = False
    link: str | None = None


@dataclass
class Heading:
    level: int
    runs: list[Run]

    @property
    def text(self) -> str:
        return plain(self.runs)


@dataclass
class Para:
    runs: list[Run]


@dataclass
class ListBlock:
    ordered: bool
    items: list[list]  # 各 item はブロックの配列
    start: int = 1


@dataclass
class Table:
    header: list[list[Run]]
    rows: list[list[list[Run]]]
    aligns: list[str | None] = field(default_factory=list)

    def header_text(self) -> list[str]:
        return [plain(c) for c in self.header]

    def rows_text(self) -> list[list[str]]:
        return [[plain(c) for c in r] for r in self.rows]


@dataclass
class Code:
    lang: str
    text: str


@dataclass
class Quote:
    blocks: list


@dataclass
class HR:
    pass


def plain(runs: list[Run]) -> str:
    return "".join(r.text for r in runs)


# --------------------------------------------------------------------------- parse

_md = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_BR = re.compile(r"<br\s*/?>", re.I)
_TAG = re.compile(r"</?[a-zA-Z][^>]*>")


def _inline(token) -> list[Run]:
    runs: list[Run] = []
    st = {"bold": 0, "italic": 0, "strike": 0}
    link: list[str] = []
    for ch in token.children or []:
        t = ch.type
        if t == "text":
            runs.append(Run(ch.content, st["bold"] > 0, st["italic"] > 0, False, st["strike"] > 0, link[-1] if link else None))
        elif t == "code_inline":
            runs.append(Run(ch.content, st["bold"] > 0, st["italic"] > 0, True, False, link[-1] if link else None))
        elif t in ("softbreak",):
            runs.append(Run(" "))
        elif t == "hardbreak":
            runs.append(Run("\n"))
        elif t == "strong_open":
            st["bold"] += 1
        elif t == "strong_close":
            st["bold"] -= 1
        elif t == "em_open":
            st["italic"] += 1
        elif t == "em_close":
            st["italic"] -= 1
        elif t == "s_open":
            st["strike"] += 1
        elif t == "s_close":
            st["strike"] -= 1
        elif t == "link_open":
            link.append(ch.attrs.get("href", ""))
        elif t == "link_close":
            if link:
                link.pop()
        elif t == "html_inline":
            if _BR.fullmatch(ch.content.strip()):
                runs.append(Run("\n"))
            # その他のタグ・コメントは捨てる
        elif t == "image":
            runs.append(Run(f"［図：{ch.content or ch.attrs.get('src', '')}］", italic=True))
    return _merge(_cjk_emphasis(runs))


_CJK_STRONG = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")


def _cjk_emphasis(runs: list[Run]) -> list[Run]:
    """日本語の句読点に隣接した **太字** は CommonMark の規則で強調にならず記号が残る。テキスト中の残りを太字にする。"""
    out: list[Run] = []
    for r in runs:
        if r.code or "**" not in r.text:
            out.append(r)
            continue
        pos = 0
        for m in _CJK_STRONG.finditer(r.text):
            if m.start() > pos:
                out.append(Run(r.text[pos:m.start()], r.bold, r.italic, False, r.strike, r.link))
            out.append(Run(m.group(1), True, r.italic, False, r.strike, r.link))
            pos = m.end()
        if pos < len(r.text):
            out.append(Run(r.text[pos:], r.bold, r.italic, False, r.strike, r.link))
    return out


def _merge(runs: list[Run]) -> list[Run]:
    out: list[Run] = []
    for r in runs:
        if not r.text:
            continue
        if out and (out[-1].bold, out[-1].italic, out[-1].code, out[-1].strike, out[-1].link) == (
            r.bold, r.italic, r.code, r.strike, r.link
        ):
            out[-1].text += r.text
        else:
            out.append(r)
    return out


def parse(text: str) -> list:
    text = _COMMENT.sub("", text)
    tokens = _md.parse(text)
    pos = 0

    def parse_blocks(end_type: str | None) -> list:
        nonlocal pos
        blocks: list = []
        while pos < len(tokens):
            tok = tokens[pos]
            if end_type and tok.type == end_type:
                pos += 1
                return blocks
            t = tok.type
            if t == "heading_open":
                level = int(tok.tag[1])
                runs = _inline(tokens[pos + 1])
                blocks.append(Heading(level, runs))
                pos += 3
            elif t == "paragraph_open":
                runs = _inline(tokens[pos + 1])
                if runs:
                    blocks.append(Para(runs))
                pos += 3
            elif t in ("bullet_list_open", "ordered_list_open"):
                ordered = t == "ordered_list_open"
                start = int(tok.attrs.get("start", 1)) if ordered else 1
                close = t.replace("_open", "_close")
                pos += 1
                items = []
                while tokens[pos].type != close:
                    if tokens[pos].type == "list_item_open":
                        pos += 1
                        items.append(parse_blocks("list_item_close"))
                    else:
                        pos += 1
                pos += 1
                blocks.append(ListBlock(ordered, items, start))
            elif t == "table_open":
                pos += 1
                header: list = []
                rows: list = []
                aligns: list = []
                cur: list | None = None
                in_head = False
                while tokens[pos].type != "table_close":
                    tt = tokens[pos]
                    if tt.type == "thead_open":
                        in_head = True
                    elif tt.type == "thead_close":
                        in_head = False
                    elif tt.type == "tr_open":
                        cur = []
                    elif tt.type == "tr_close":
                        if in_head:
                            header = cur or []
                        else:
                            rows.append(cur or [])
                    elif tt.type in ("th_open", "td_open"):
                        style = tt.attrs.get("style", "") if tt.attrs else ""
                        if in_head:
                            m = re.search(r"text-align:(\w+)", style or "")
                            aligns.append(m.group(1) if m else None)
                        cur.append(_inline(tokens[pos + 1]))
                        pos += 2
                    pos += 1
                pos += 1
                blocks.append(Table(header, rows, aligns))
            elif t in ("fence", "code_block"):
                blocks.append(Code((tok.info or "").strip().split(" ")[0], tok.content.rstrip("\n")))
                pos += 1
            elif t == "blockquote_open":
                pos += 1
                blocks.append(Quote(parse_blocks("blockquote_close")))
            elif t == "hr":
                blocks.append(HR())
                pos += 1
            elif t == "html_block":
                body = _TAG.sub("", _COMMENT.sub("", tok.content)).strip()
                if body:
                    blocks.append(Para([Run(body)]))
                pos += 1
            else:
                pos += 1
        return blocks

    return parse_blocks(None)


def parse_file(path: str | Path) -> list:
    return parse(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- helpers

def iter_tables_with_context(blocks: list, ctx: list[str] | None = None):
    """(heading_path, table) を文書順に返す。heading_path は直近の見出し文字列の配列。"""
    ctx = list(ctx or [])
    stack: list[tuple[int, str]] = []
    for b in blocks:
        if isinstance(b, Heading):
            while stack and stack[-1][0] >= b.level:
                stack.pop()
            stack.append((b.level, b.text))
        elif isinstance(b, Table):
            yield [h for _, h in stack], b
        elif isinstance(b, Quote):
            yield from iter_tables_with_context(b.blocks, [h for _, h in stack])
        elif isinstance(b, ListBlock):
            for item in b.items:
                yield from iter_tables_with_context(item, [h for _, h in stack])


def section(blocks: list, title_contains: str) -> list:
    """見出しテキストに title_contains を含む節（次の同レベル以上の見出しまで）を返す。"""
    out: list = []
    level = None
    for b in blocks:
        if isinstance(b, Heading):
            if level is not None and b.level <= level:
                break
            if level is None and title_contains in b.text:
                level = b.level
                continue
        if level is not None:
            out.append(b)
    return out


def drop_sections(blocks: list, patterns: list[str]) -> list:
    """見出しが patterns のいずれかを含む節を取り除く（Self-Check / Handoff など社内向けの節）。"""
    out: list = []
    skip_level = None
    for b in blocks:
        if isinstance(b, Heading):
            if skip_level is not None and b.level <= skip_level:
                skip_level = None
            if skip_level is None and any(p in b.text for p in patterns):
                skip_level = b.level
                continue
        if skip_level is None:
            out.append(b)
    return out


ID_RE = re.compile(r"\b(?:[A-Z]{1,6}(?:-[A-Z0-9]{1,10})*-\d{1,4})\b")


def find_ids(text: str) -> list[str]:
    return ID_RE.findall(text)


_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U00002B00-\U00002BFF️‍]"
)


def strip_emoji(s: str) -> str:
    return _EMOJI.sub("", s).strip()
