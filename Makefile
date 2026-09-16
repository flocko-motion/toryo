# toryo.txt (und spaeter toryo-en.txt) sind die Quellen; site/ enthaelt die
# fertige, verteilbare Website und wird versioniert.
#
# Die englische Fassung wird automatisch mitgebaut, sobald toryo-en.txt
# existiert - vorher bleiben ihre Targets leer und die Startseite zeigt
# statt toter Links den Hinweis "in Vorbereitung".

SRC       := toryo.txt
SRC_EN    := $(wildcard toryo-en.txt)

# Alles, was zum Bauen gebraucht wird, liegt in build/; site/ ist das Ergebnis.
TPL       := build
TEMPLATE  := $(TPL)/template.html
TPL_INDEX := $(TPL)/template_index.html
TPL_TYP   := $(TPL)/template.typ
TPL_TXT   := $(TPL)/template.txt
TPL_COVER := $(TPL)/template_cover.typ
BUILD     := $(TPL)/build.py
SITE      := site

INDEX     := $(SITE)/index.html
FAVICON   := $(SITE)/favicon.svg
PYTHON    ?= python3

# Artefakte einer Sprache: $(call artefacts,<praefix>)
#   toryo    -> site/toryo.html, site/toryo-a5.pdf, ...
#   toryo-en -> site/toryo-en.html, site/toryo-en-a5.pdf, ...
define artefacts
$(SITE)/$(1).html $(SITE)/$(1)-a5.pdf $(SITE)/$(1)-a4.pdf \
$(SITE)/$(1).epub $(SITE)/$(1).txt $(SITE)/$(1)-cover.png
endef

DE_OUT := $(call artefacts,toryo)
EN_OUT := $(if $(SRC_EN),$(call artefacts,toryo-en),)

.PHONY: all clean open watch index de en help

all: $(INDEX) $(FAVICON) de en   ## alles bauen (Vorgabe)

de: $(DE_OUT)                    ## nur die deutsche Fassung
en: $(EN_OUT)                    ## nur die englische Fassung
index: $(INDEX)                  ## nur die Startseite

$(SITE):
	@mkdir -p $(SITE)

$(FAVICON): $(TPL)/favicon.svg | $(SITE)
	cp $< $@

# Die Startseite haengt auch an SRC_EN: taucht die Uebersetzung auf,
# wird die Fassungsliste neu gerendert.
$(INDEX): $(SRC) $(SRC_EN) $(TPL_INDEX) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $(SRC) $(TPL_INDEX) $(INDEX)

# ---------------------------------------------------------------- Regeln
# Eine Musterregel pro Format, gilt fuer beide Sprachen.

$(SITE)/%.html: %.txt $(TEMPLATE) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $< $(TEMPLATE) $@

$(SITE)/%.txt: %.txt $(TPL_TXT) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $< $(TPL_TXT) $@

$(SITE)/%.typ: %.txt $(TPL_TYP) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $< $(TPL_TYP) $@

$(SITE)/%-cover.typ: %.txt $(TPL_COVER) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $< $(TPL_COVER) $@

$(SITE)/%-a5.pdf: $(SITE)/%.typ
	@command -v typst >/dev/null 2>&1 || { echo "typst fehlt: brew install typst"; exit 1; }
	typst compile --input paper=a5 $< $@
	@echo "build: $@ geschrieben"

$(SITE)/%-a4.pdf: $(SITE)/%.typ
	@command -v typst >/dev/null 2>&1 || { echo "typst fehlt: brew install typst"; exit 1; }
	typst compile --input paper=a4 $< $@
	@echo "build: $@ geschrieben"

$(SITE)/%-cover.png: $(SITE)/%-cover.typ
	@command -v typst >/dev/null 2>&1 || { echo "typst fehlt: brew install typst"; exit 1; }
	typst compile --format png --ppi 72 $< $@
	@echo "build: $@ geschrieben"

# EPUB braucht Sprache und Cover, darum je eine eigene Regel.
$(SITE)/toryo.epub: $(SITE)/toryo.html $(SITE)/toryo-cover.png
	@command -v pandoc >/dev/null 2>&1 || { echo "pandoc fehlt: brew install pandoc"; exit 1; }
	pandoc $< -f html -t epub3 -o $@ \
	  --metadata title="Tōryō" --metadata author="Florian Metzger-Noel" \
	  --metadata lang=de --metadata rights="CC BY-SA 4.0" \
	  --epub-cover-image=$(SITE)/toryo-cover.png
	@echo "build: $@ geschrieben"

$(SITE)/toryo-en.epub: $(SITE)/toryo-en.html $(SITE)/toryo-en-cover.png
	@command -v pandoc >/dev/null 2>&1 || { echo "pandoc fehlt: brew install pandoc"; exit 1; }
	pandoc $< -f html -t epub3 -o $@ \
	  --metadata title="Tōryō" --metadata author="Florian Metzger-Noel" \
	  --metadata lang=en --metadata rights="CC BY-SA 4.0" \
	  --epub-cover-image=$(SITE)/toryo-en-cover.png
	@echo "build: $@ geschrieben"

# Zwischenstufen nicht loeschen (make raeumt implizite Ziele sonst weg).
.PRECIOUS: $(SITE)/%.typ $(SITE)/%-cover.typ

open: $(INDEX)                   ## Startseite im Browser oeffnen
	open $(INDEX)

clean:                           ## alle Artefakte in site/ loeschen
	rm -f $(SITE)/*.html $(SITE)/*.typ $(SITE)/*.pdf $(SITE)/*.epub \
	      $(SITE)/*.png $(SITE)/*.txt $(SITE)/*.svg

watch:                           ## bei jeder Aenderung neu bauen
	@command -v fswatch >/dev/null 2>&1 || { echo "fswatch fehlt: brew install fswatch"; exit 1; }
	@echo "Beobachte Quellen und Vorlagen ... (Ctrl-C beendet)"
	@fswatch -o $(SRC) $(SRC_EN) $(TEMPLATE) $(TPL_INDEX) $(TPL_TYP) \
	         $(TPL_TXT) $(TPL_COVER) $(BUILD) \
	  | while read _; do $(MAKE) --no-print-directory all; done

# ------------------------------------------------------------------ Hilfe
# Die Uebersicht liest sich selbst aus den "##"-Kommentaren oben zusammen,
# bleibt also automatisch aktuell.

help:                            ## diese Uebersicht
	@echo "Toryo - Ziele:"
	@echo
	@grep -hE '^[a-z][a-z-]*:.*## ' $(MAKEFILE_LIST) \
	  | sed -E 's/^([a-z-]+):.*## /\1\t/' \
	  | awk -F'\t' '{ printf "  %-8s %s\n", $$1, $$2 }'
	@echo
	@echo "Quellen: $(SRC)$(if $(SRC_EN), und $(SRC_EN), - englische Fassung fehlt noch)"
	@echo "Ergebnis: $(SITE)/ - Vorlagen und Skript: $(TPL)/"
	@echo
	@echo "Gebraucht werden: python3, typst (PDF, Cover), pandoc (EPUB),"
	@echo "fswatch (nur fuer watch). Anderer Interpreter: make PYTHON=..."
