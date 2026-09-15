# toryo.txt (und spaeter toryo-en.txt) sind die Quellen; site/ enthaelt die
# fertige, verteilbare Website und wird versioniert.
#
# Die englische Fassung wird automatisch mitgebaut, sobald toryo-en.txt
# existiert - vorher bleiben ihre Targets leer und die Startseite zeigt
# statt toter Links den Hinweis "in Vorbereitung".

SRC       := toryo.txt
SRC_EN    := $(wildcard toryo-en.txt)

TEMPLATE  := template.html
TPL_INDEX := template_index.html
TPL_TYP   := template.typ
TPL_TXT   := template.txt
TPL_COVER := template_cover.typ
BUILD     := build.py
SITE      := site

INDEX     := $(SITE)/index.html
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

.PHONY: all clean open watch index de en

all: $(INDEX) de en

de: $(DE_OUT)
en: $(EN_OUT)
index: $(INDEX)

$(SITE):
	@mkdir -p $(SITE)

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

open: $(INDEX)
	open $(INDEX)

clean:
	rm -f $(SITE)/*.html $(SITE)/*.typ $(SITE)/*.pdf $(SITE)/*.epub \
	      $(SITE)/*.png $(SITE)/*.txt

watch:
	@command -v fswatch >/dev/null 2>&1 || { echo "fswatch fehlt: brew install fswatch"; exit 1; }
	@echo "Beobachte Quellen und Vorlagen ... (Ctrl-C beendet)"
	@fswatch -o $(SRC) $(SRC_EN) $(TEMPLATE) $(TPL_INDEX) $(TPL_TYP) \
	         $(TPL_TXT) $(TPL_COVER) $(BUILD) \
	  | while read _; do $(MAKE) --no-print-directory all; done
