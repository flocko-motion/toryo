// Typst-Vorlage fuer das PDF. Wird von build.py mit Werten gefuellt.
// Erzeugen:  python3 build.py toryo.txt template.typ toryo.typ && typst compile toryo.typ

#set document(title: "{{DOC_TITLE}}", author: "{{DOC_AUTHOR}}")

#let ink  = rgb("#1c1a17")
#let mute = rgb("#8a8377")
#let shu  = rgb("#8f3410")
#let hair = rgb("#d9d2c2")

// Papierformat ueber die Kommandozeile:  typst compile --input paper=a4 ...
// Satzbreite bleibt in beiden Formaten bei rund 65 Zeichen pro Zeile.
#let paper = sys.inputs.at("paper", default: "a5")
#let a4 = paper == "a4"

#set page(
  paper: paper,
  margin: if a4 { (x: 42mm, top: 28mm, bottom: 30mm) }
          else   { (x: 18mm, top: 20mm, bottom: 22mm) },
  numbering: "1",
  number-align: center,
)
#set text(
  font: ("Iowan Old Style", "Palatino", "Georgia", "Times New Roman"),
  size: if a4 { 11.5pt } else { 10pt },
  lang: "{{LANG}}",
  fill: ink,
  hyphenate: true,
)
#set par(justify: true, leading: 0.72em, spacing: 1.15em)
#show link: set text(fill: shu)

// ---------- Titelei ----------
#page(numbering: none)[
  #v(1fr)
  #align(center)[
    #text(
      font: ("Hiragino Mincho ProN", "Songti SC"),
      size: if a4 { 68pt } else { 54pt },
      fill: shu,
      tracking: 6pt,
    )[{{TITLE_SEAL}}]

    #v(1.6em)
    #text(size: if a4 { 20pt } else { 17pt }, tracking: 7pt)[{{TITLE_MAIN}}]

    #v(2em)
    #text(size: 10pt, fill: mute)[
      {{TAGLINE}}
    ]

    #v(1.6em)
    #text(size: 7pt, tracking: 1.2pt, fill: mute)[{{LICENSE}}]

    #v(0.7em)
    #text(size: 6.5pt, tracking: 0.6pt, fill: mute)[{{VERSION}}]
  ]
  #v(1fr)

  #align(center)[
    #block(width: 72%)[
      #line(length: 100%, stroke: 0.4pt + hair)
      #v(0.9em)
      #text(size: 8pt, style: "italic", fill: mute)[{{EPIGRAPH}}]
    ]
  ]
  #v(1fr)
]

// ---------- Fliesstext ----------
{{BODY}}

// ---------- Anmerkungen ----------
{{FOOTNOTES}}
