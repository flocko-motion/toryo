#!/usr/bin/env python3
"""Erzeugt toryo.html aus toryo.txt und template.html.

Single Source of Truth ist toryo.txt; das HTML ist ein Build-Artefakt.
Reine Standardbibliothek, keine Dependencies.

    python3 build.py [quelle.txt] [template.html] [ausgabe.html]

Konventionen im .txt (kein zusaetzliches Markup noetig):
  - Kopf = "schluessel: wert"-Zeilen bis zur ersten Leerzeile. Erkannte
    Schluessel (alle optional, Reihenfolge egal):
      title      Titel; ein Klammerteil "(投了)" wird als Schriftzeichen gesetzt
      subtitle   Untertitel
      author     Credits ("von ...")
      epigraph   Motto unter dem Titel
      license    Lizenzangabe (z.B. "CC BY-SA 4.0")
      link       Autoren-Website (z.B. "fmnoel.de"); wird verlinkt
    Unbekannte Schluessel brechen den Build ab (Tippfehler sollen auffallen).
  - Leerzeile trennt Absaetze (im Fliesstext).
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

# Kopfzeile "schluessel: wert". Der Wert darf weitere Doppelpunkte enthalten.
HEAD_RE = re.compile(r"^([a-z_]+):[ \t]+(.*)$")
HEAD_KEYS = ("title", "subtitle", "author", "epigraph", "license", "link", "lang")

# Ein Absatz, der nur aus einem dieser Woerter besteht, wird als Schlussmarke
# gesetzt (zentriert, gesperrt) statt als Fliesstext.
END_WORDS = ("Ende", "End", "Tōryō")

# Sprachabhaengige Beschriftungen. Die Sprache kommt aus dem Kopf ("lang: en"),
# Vorgabe ist Deutsch.
LABELS = {
    "de": {"notes": "Anmerkungen", "end": "Ende", "back": "zurueck"},
    "en": {"notes": "Notes",       "end": "End",  "back": "back"},
}


def labels(head: dict) -> dict:
    return LABELS.get(head.get("lang", "de"), LABELS["de"])


def head_en() -> dict:
    """Kopfdaten der Uebersetzung, fuer die zweisprachige Startseite."""
    src = Path("toryo-en.txt")
    if not src.exists():
        return {}
    try:
        return parse_head(src.read_text(encoding="utf-8").split("\n"))[0]
    except SystemExit:
        return {}


def edition_en(current_lang: str) -> str:
    """Zeile der englischen Fassung auf der Startseite.

    Solange toryo-en.txt fehlt, steht dort ein Hinweis statt toter Links.
    """
    pending = ('<div class="edition"><div class="edition-name pending">'
               "English &mdash; in Vorbereitung</div></div>")
    if not Path("toryo-en.txt").exists():
        return pending
    return (
        '<div class="edition">\n'
        '        <div class="edition-name"><a href="toryo-en.html">English &mdash; read</a></div>\n'
        '        <div class="formats">\n'
        '          <a href="toryo-en-a5.pdf">PDF&nbsp;A5</a>\n'
        '          <a href="toryo-en-a4.pdf">PDF&nbsp;A4</a>\n'
        '          <a href="toryo-en.epub">EPUB</a>\n'
        '          <a href="toryo-en.txt">TXT</a>\n'
        "        </div>\n"
        "      </div>"
    )


def esc(s: str) -> str:
    return html.escape(s, quote=False)


# --- Typst ---------------------------------------------------------------
# In Typst leiten diese Zeichen Markup ein und muessen maskiert werden.
TYP_SPECIAL = "\\#$*_`<>@[]"


def esc_typ(s: str) -> str:
    return "".join("\\" + c if c in TYP_SPECIAL else c for c in s)


def render_para_typ(s: str, fns: list) -> str:
    """Absatztext fuer Typst; [url] wird zur hochgestellten Endnoten-Ziffer."""
    out = []
    last = 0
    for m in FN_RE.finditer(s):
        out.append(esc_typ(s[last:m.start()]))
        n = len(fns) + 1
        fns.append(m.group(1))
        out.append(f"#super[{n}]")
        last = m.end()
    out.append(esc_typ(s[last:]))
    return "".join(out)


def parse_head(lines: list):
    """Kopf lesen: 'schluessel: wert'-Zeilen bis zur ersten Leerzeile.

    Gibt (kopf-dict, index der ersten Fliesstextzeile) zurueck.
    """
    head = {}
    idx = 0
    for idx, ln in enumerate(lines):
        if not ln.strip():
            idx += 1
            break
        m = HEAD_RE.match(ln.strip())
        if not m:
            raise SystemExit(
                f"build: Zeile {idx + 1} ist keine Kopfzeile 'schluessel: wert':\n  {ln}"
            )
        key, val = m.group(1), m.group(2).strip()
        if key not in HEAD_KEYS:
            raise SystemExit(
                f"build: unbekannter Kopf-Schluessel '{key}' in Zeile {idx + 1}. "
                f"Erlaubt: {', '.join(HEAD_KEYS)}"
            )
        head[key] = val
    else:
        idx = len(lines)
    return head, idx


def link_label(link: str) -> str:
    """Anzeigetext fuer einen Link: ohne Schema, ohne 'www.', ohne Schraegstrich."""
    return re.sub(r"^https?://(www\.)?", "", link).rstrip("/")


def render_license(license_text: str, link: str) -> str:
    """Lizenzzeile unter den Credits; der Link wird klickbar."""
    parts = []
    if license_text:
        parts.append(esc(license_text))
    if link:
        href = link if link.startswith(("http://", "https://")) else f"https://{link}"
        parts.append(
            f'<a class="site-link" href="{esc(href)}" '
            f'rel="noopener noreferrer">{esc(link_label(link))}</a>'
        )
    if not parts:
        return ""
    return '<div class="license">' + ' <span class="sep">&middot;</span> '.join(parts) + "</div>"


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


TXT_WIDTH = 72


def build_text(tpl, out, head, title, title_main, title_seal,
               subtitle, credits, epigraph_text, body_blocks) -> int:
    """Lesbare Plaintext-Fassung; Quellen werden zu [1] plus Liste am Schluss."""
    import textwrap
    import unicodedata

    def cols(s: str) -> int:
        """Darstellungsbreite: CJK-Zeichen belegen zwei Spalten."""
        return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)

    def centre(s: str) -> str:
        out_ = []
        for ln in s.split("\n"):
            pad = max(0, (TXT_WIDTH - cols(ln)) // 2)
            out_.append((" " * pad + ln).rstrip())
        return "\n".join(out_)

    def wrap(s: str, indent: str = "") -> str:
        return textwrap.fill(
            s, width=TXT_WIDTH, initial_indent=indent, subsequent_indent=indent,
            break_long_words=False, break_on_hyphens=False,
        )

    lab = labels(head)
    fns: list = []
    parts = []
    for b in body_blocks:
        joined = " ".join(b).strip()
        if joined in END_WORDS:
            parts.append(centre(joined))
            break
        # [url] durch [n] ersetzen und die Quelle merken
        def _sub(m):
            fns.append(m.group(1))
            return f"[{len(fns)}]"
        parts.append(wrap(FN_RE.sub(_sub, joined)))
    body_txt = "\n\n".join(parts)

    notes_txt = ""
    if fns:
        lines_ = [centre(lab["notes"]), ""]
        # URLs nicht umbrechen: sie sollen kopierbar auf einer Zeile stehen.
        for i, url in enumerate(fns, 1):
            lines_.append(f"  [{i}] {url}")
        notes_txt = "\n".join(lines_)

    tagline = "\n".join(centre(x) for x in (subtitle, credits) if x)
    lic = " · ".join(x for x in (
        head.get("license", ""),
        link_label(head["link"]) if head.get("link") else "",
    ) if x)

    page = tpl.read_text(encoding="utf-8")
    for k, v in {
        "{{TITLE_SEAL}}": centre(title_seal),
        "{{TITLE_MAIN}}": centre(title_main.upper()),
        "{{TAGLINE}}": tagline,
        "{{LICENSE}}": centre(lic),
        "{{EPIGRAPH}}": wrap(epigraph_text, indent="  "),
        "{{BODY}}": body_txt,
        "{{FOOTNOTES}}": notes_txt,
    }.items():
        page = page.replace(k, v)

    out.write_text(page, encoding="utf-8")
    print(f"build: {out} geschrieben ({len(fns)} Anmerkungen, {len(body_blocks)} Bloecke)")
    return 0


def build_typst(tpl, out, head, title, title_main, title_seal,
                subtitle, credits, epigraph_text, body_blocks) -> int:
    """Typst-Quelle schreiben; typst compile macht daraus das PDF."""
    lab = labels(head)
    fns: list = []
    body_parts = []
    for b in body_blocks:
        joined = " ".join(b).strip()
        if joined in END_WORDS:
            body_parts.append('#v(2em)\n#align(center)[#text(size: 7pt, '
                              'tracking: 3pt, fill: luma(110))'
                              f'[{esc_typ(joined.upper())}]]')
            break
        body_parts.append(render_para_typ(joined, fns))
    body_typ = "\n\n".join(body_parts)

    if fns:
        items = "\n".join(
            f'  [{i}], [#link("{u}")[{esc_typ(u)}]],' for i, u in enumerate(fns, 1)
        )
        notes_typ = (
            "#pagebreak()\n"
            f'#text(size: 7pt, tracking: 2.5pt, fill: luma(110))[{lab["notes"].upper()}]\n'

            "#v(0.8em)\n"
            "#set text(size: 7.5pt)\n"
            "#table(columns: (1.2em, 1fr), stroke: none, inset: 3pt,\n"
            f"{items}\n)"
        )
    else:
        notes_typ = ""

    tagline = []
    if subtitle:
        tagline.append(f"#emph[{esc_typ(subtitle)}]")
    if credits:
        tagline.append(f"#v(0.3em)\n#text(size: 9pt)[{esc_typ(credits)}]")

    lic_parts = []
    if head.get("license"):
        lic_parts.append(esc_typ(head["license"]))
    if head.get("link"):
        ln = head["link"]
        href = ln if ln.startswith(("http://", "https://")) else f"https://{ln}"
        lic_parts.append(f'#link("{href}")[{esc_typ(link_label(ln))}]')
    license_typ = " · ".join(lic_parts)

    page = tpl.read_text(encoding="utf-8")
    for k, v in {
        "{{LANG}}": head.get("lang", "de"),
        "{{DOC_TITLE}}": title.replace('"', "'"),
        "{{DOC_AUTHOR}}": credits.replace("von ", "").split(",")[0].replace('"', "'"),
        "{{TITLE_SEAL}}": esc_typ(title_seal),
        "{{TITLE_MAIN}}": esc_typ(title_main),
        "{{TAGLINE}}": "\n".join(tagline),
        "{{LICENSE}}": license_typ,
        "{{EPIGRAPH}}": esc_typ(epigraph_text),
        "{{COVER_SUBTITLE}}": esc_typ(subtitle),
        "{{COVER_AUTHOR}}": esc_typ(re.sub(r",.*$", "", credits).strip()),
        "{{BODY}}": body_typ,
        "{{FOOTNOTES}}": notes_typ,
    }.items():
        page = page.replace(k, v)

    out.write_text(page, encoding="utf-8")
    print(f"build: {out} geschrieben ({len(fns)} Anmerkungen, {len(body_blocks)} Bloecke)")
    return 0


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "toryo.txt")
    tpl = Path(sys.argv[2] if len(sys.argv) > 2 else "template.html")
    out = Path(sys.argv[3] if len(sys.argv) > 3 else "toryo.html")

    raw = src.read_text(encoding="utf-8")
    raw = TAG_LINE_RE.sub("", raw)   # Navigations-Tags entfernen

    lines = raw.split("\n")
    head, body_start = parse_head(lines)
    if not head:
        print("build: leerer Kopf", file=sys.stderr)
        return 1

    title = head.get("title", "")
    subtitle = head.get("subtitle", "")
    credits = head.get("author", "")
    epigraph_text = head.get("epigraph", "")

    title_main, title_seal = render_title(title)
    body_blocks = split_blocks("\n".join(lines[body_start:]))
    is_typ = out.suffix == ".typ"

    if out.suffix == ".txt":
        return build_text(
            tpl, out, head, title, title_main, title_seal,
            subtitle, credits, epigraph_text, body_blocks,
        )

    if is_typ:
        return build_typst(
            tpl, out, head, title, title_main, title_seal,
            subtitle, credits, epigraph_text, body_blocks,
        )

    # Untertitel / Credits.
    tagline_html = "\n      ".join(
        f'<div class="{"author" if ln.lower().startswith("von ") else "subtitle"}">'
        f"{esc(ln)}</div>"
        for ln in (subtitle, credits) if ln
    )

    license_html = render_license(head.get("license", ""), head.get("link", ""))

    # Epigraph.
    epigraph_html = (
        f'<aside class="epigraph">{esc(epigraph_text)}</aside>' if epigraph_text else ""
    )

    # Fliesstext.
    lab = labels(head)
    fns: list = []
    body_html = []
    for b in body_blocks:
        joined = " ".join(b).strip()
        if joined in END_WORDS:
            body_html.append(
                f'<div class="end" aria-label="{lab["end"]}">'
                f'<span>{esc(joined)}</span></div>')
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
                f'<a class="fn-back" href="#fnref{i}" aria-label="{lab["back"]}">&#8617;</a></li>'
            )
        notes_html = (
            '<footer class="notes">\n'
            f'      <h2 class="notes-label">{lab["notes"]}</h2>\n'
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
        "{{LICENSE}}": license_html,
        "{{LANG}}": head.get("lang", "de"),
        "{{EDITION_EN}}": edition_en(head.get("lang", "de")),
        "{{SUBTITLE}}": esc(subtitle),
        "{{AUTHOR}}": esc(credits),
        "{{EPIGRAPH_PLAIN}}": esc(epigraph_text),
        "{{SUBTITLE_EN}}": esc(head_en().get("subtitle", "")),
        "{{EPIGRAPH_EN}}": esc(head_en().get("epigraph", "")),
        "{{EPIGRAPH}}": epigraph_html,
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
