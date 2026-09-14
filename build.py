#!/usr/bin/env python3
"""Erzeugt toryo.html aus toryo.txt und template.html.

Single Source of Truth ist toryo.txt; das HTML ist ein Build-Artefakt.
Reine Standardbibliothek, keine Dependencies.

    python3 build.py [quelle.txt] [template.html] [ausgabe.html]

Konventionen im .txt (kein zusaetzliches Markup noetig):
  - Leerzeile trennt Absaetze.
  - Erste Zeile        = Titel; ein Klammerteil "(投了)" wird als Schriftzeichen gesetzt.
  - Zeilen vor "Personen" = Untertitel/Autor ("von ..." -> Autor).
  - Block "Personen"   = Figurenliste, je Zeile "Name, Rolle".
  - [https://...]      = wird zur nummerierten Endnote.
  - Zeile "Ende" allein = Schlussmarke.
  - [name] allein auf einer Zeile = Navigations-Tag, wird beim Build entfernt
    (z.B. [kessler] ueber dem Absatz, in dem Kessler spricht/handelt).
"""
import html
import re
import sys
from pathlib import Path

# Optional ein einzelnes Leerzeichen vor der Klammer schlucken, damit die
# hochgestellte Ziffer eng am Wort sitzt.
FN_RE = re.compile(r"[ \t]?\[(https?://[^\]\s]+)\]")

# Navigations-Tags: eine Zeile, die nur aus [wort] besteht (z.B. [kessler]).
# Greift NICHT bei Fussnoten [https://...] (nicht die ganze Zeile, enthaelt :/.)
# und nicht bei Ultraglot-Saetzen (ganzer Satz, nicht bloss ein Klammerwort).
TAG_LINE_RE = re.compile(r"(?m)^[ \t]*\[[A-Za-zÀ-ÿ_-]+\][ \t]*\n?")


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def split_blocks(text: str):
    """Text in Bloecke zerlegen (durch Leerzeilen getrennt)."""
    blocks = []
    for raw in re.split(r"\n[ \t]*\n", text.strip("\n")):
        lines = [ln.rstrip() for ln in raw.split("\n") if ln.strip()]
        if lines:
            blocks.append(lines)
    return blocks


def render_para(s: str, fns: list) -> str:
    """Absatztext escapen und [url] durch Fussnoten-Anker ersetzen."""
    out = []
    last = 0
    for m in FN_RE.finditer(s):
        out.append(esc(s[last:m.start()]))
        n = len(fns) + 1
        fns.append(m.group(1))
        out.append(
            f'<sup class="fn-ref"><a id="fnref{n}" href="#fn{n}">{n}</a></sup>'
        )
        last = m.end()
    out.append(esc(s[last:]))
    return "".join(out)


def render_title(title: str):
    """Titel in Romaji-Teil und Schriftzeichen-Teil (in Klammern) trennen."""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", title)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return title.strip(), ""


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "toryo.txt")
    tpl = Path(sys.argv[2] if len(sys.argv) > 2 else "template.html")
    out = Path(sys.argv[3] if len(sys.argv) > 3 else "toryo.html")

    raw = src.read_text(encoding="utf-8")
    raw = TAG_LINE_RE.sub("", raw)   # Navigations-Tags entfernen
    blocks = split_blocks(raw)
    if not blocks:
        print("build: leere Quelle", file=sys.stderr)
        return 1

    title = blocks[0][0]
    title_main, title_seal = render_title(title)

    # Frontmatter: Bloecke zwischen Titel und "Personen".
    p_idx = next(
        (i for i, b in enumerate(blocks) if b[0].strip().lower() == "personen"),
        None,
    )
    if p_idx is None:
        tagline_lines, cast_lines, body_blocks = [], [], blocks[1:]
    else:
        tagline_lines = [ln for b in blocks[1:p_idx] for ln in b]
        # "Personen" kann die Namen im selben Block tragen oder (bei Leerzeile
        # darunter) im naechsten Block.
        cast_lines = blocks[p_idx][1:]
        if cast_lines:
            body_blocks = blocks[p_idx + 1:]
        elif p_idx + 1 < len(blocks):
            cast_lines = blocks[p_idx + 1]
            body_blocks = blocks[p_idx + 2:]
        else:
            body_blocks = []

    # Untertitel / Autor.
    tagline_html = []
    for ln in tagline_lines:
        cls = "author" if ln.lower().startswith("von ") else "subtitle"
        tagline_html.append(f'<div class="{cls}">{esc(ln)}</div>')
    tagline_html = "\n      ".join(tagline_html)

    # Figurenliste.
    cast_html = []
    for ln in cast_lines:
        if "," in ln:
            name, role = ln.split(",", 1)
            cast_html.append(
                f'<li><span class="cast-name">{esc(name.strip())}</span>'
                f'<span class="cast-role">{esc(role.strip())}</span></li>'
            )
        else:
            cast_html.append(f'<li><span class="cast-name">{esc(ln.strip())}</span></li>')
    cast_html = "\n        ".join(cast_html)

    # Fliesstext.
    fns: list = []
    body_html = []
    for b in body_blocks:
        joined = " ".join(b).strip()
        if joined == "Ende":
            body_html.append('<div class="end" aria-label="Ende"><span>Ende</span></div>')
            break
        body_html.append(f"<p>{render_para(joined, fns)}</p>")
    body_html = "\n      ".join(body_html)

    # Endnoten.
    if fns:
        items = []
        for i, url in enumerate(fns, 1):
            items.append(
                f'<li id="fn{i}"><a class="fn-link" href="{esc(url)}" '
                f'target="_blank" rel="noopener noreferrer">{esc(url)}</a> '
                f'<a class="fn-back" href="#fnref{i}" aria-label="zurueck">&#8617;</a></li>'
            )
        notes_html = (
            '<footer class="notes">\n'
            '      <h2 class="notes-label">Anmerkungen</h2>\n'
            '      <ol class="notes-list">\n        '
            + "\n        ".join(items)
            + "\n      </ol>\n    </footer>"
        )
    else:
        notes_html = ""

    page = tpl.read_text(encoding="utf-8")
    repl = {
        "{{HEAD_TITLE}}": esc(title),
        "{{TITLE_SEAL}}": esc(title_seal),
        "{{TITLE_MAIN}}": esc(title_main),
        "{{TAGLINE}}": tagline_html,
        "{{CAST}}": cast_html,
        "{{BODY}}": body_html,
        "{{FOOTNOTES}}": notes_html,
    }
    for k, v in repl.items():
        page = page.replace(k, v)

    out.write_text(page, encoding="utf-8")
    print(f"build: {out} geschrieben ({len(fns)} Anmerkungen, {len(body_blocks)} Bloecke)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
