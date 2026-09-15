// Cover fuer EPUB und Vorschau. Wird von build.py gefuellt, dann:
//   typst compile --format png --ppi 72 site/cover.typ site/cover.png
// Seitenmass in pt = Pixel bei 72 ppi -> 1600 x 2560.

#let ink   = rgb("#16150f")
#let shu   = rgb("#c0562a")
#let chalk = rgb("#e9e3d3")
#let mute  = rgb("#8c8674")
#let serif = ("Iowan Old Style", "Palatino", "Georgia")

#set page(width: 1600pt, height: 2560pt, margin: (x: 150pt, y: 190pt), fill: ink)
#set text(lang: "de", fill: chalk)
#set par(leading: 0.6em)

#align(center)[
  #v(0.9fr)

  // Siegel: top-/bottom-edge schneiden den Leerraum der Zeilenbox weg,
  // sonst reisst die Kegelhoehe ein Loch in die Mitte.
  // move(dx) gleicht aus, dass tracking auch hinter dem letzten Zeichen wirkt
  // und den zentrierten Block sonst nach links kippt.
  #move(dx: 17pt)[#text(
    font: ("Hiragino Mincho ProN", "Songti SC"),
    size: 470pt,
    fill: shu,
    tracking: 34pt,
    top-edge: "cap-height",
    bottom-edge: "baseline",
  )[{{TITLE_SEAL}}]]

  #v(0.85fr)
  #line(length: 170pt, stroke: 1.2pt + mute)
  #v(0.62fr)

  #move(dx: 22pt)[#text(font: serif, size: 124pt, tracking: 44pt,
    top-edge: "cap-height")[{{TITLE_MAIN}}]]

  #v(38pt)
  #text(font: serif, size: 42pt, fill: mute, style: "italic")[{{COVER_SUBTITLE}}]

  #v(1.5fr)

  #move(dx: 4.5pt)[#text(font: serif, size: 50pt, tracking: 9pt)[{{COVER_AUTHOR}}]]

  #v(0.15fr)
]
