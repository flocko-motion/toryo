# toryo.txt ist die Quelle; site/ enthaelt die fertige, verteilbare Website.
# site/ wird versioniert, damit die Dateien direkt aus dem Repo heraus
# ausgeliefert werden koennen.
SRC      := toryo.txt
TEMPLATE := template.html
TPL_INDEX:= template_index.html
TPL_TYP  := template.typ
BUILD    := build.py
SITE     := site

INDEX    := $(SITE)/index.html
HTML     := $(SITE)/toryo.html
TYP      := $(SITE)/toryo.typ
PDF_A5   := $(SITE)/toryo-a5.pdf
PDF_A4   := $(SITE)/toryo-a4.pdf
EPUB     := $(SITE)/toryo.epub
COVER_TYP:= $(SITE)/cover.typ
COVER    := $(SITE)/cover.png
TXT      := $(SITE)/toryo.txt
TPL_TXT  := template.txt

# Englische Fassung wird gebaut, sobald toryo_en.txt existiert.
EN_SRC   := $(wildcard toryo_en.txt)
EN_HTML  := $(if $(EN_SRC),$(SITE)/toryo_en.html,)

PYTHON   ?= python3

.PHONY: all clean open watch html pdf epub index cover txt

all: $(INDEX) $(HTML) $(EN_HTML) $(PDF_A5) $(PDF_A4) $(EPUB) $(COVER) $(TXT)

index: $(INDEX)
html:  $(HTML)
pdf:   $(PDF_A5) $(PDF_A4)
epub:  $(EPUB)
cover: $(COVER)
txt:   $(TXT)

$(SITE):
	@mkdir -p $(SITE)

$(INDEX): $(SRC) $(TPL_INDEX) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $(SRC) $(TPL_INDEX) $(INDEX)

$(HTML): $(SRC) $(TEMPLATE) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $(SRC) $(TEMPLATE) $(HTML)

$(SITE)/toryo_en.html: toryo_en.txt $(TEMPLATE) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) toryo_en.txt $(TEMPLATE) $@

$(TYP): $(SRC) $(TPL_TYP) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $(SRC) $(TPL_TYP) $(TYP)

# --- PDF: txt -> typst -> pdf, zwei Papierformate aus derselben Quelle ---
$(PDF_A5): $(TYP)
	@command -v typst >/dev/null 2>&1 || { echo "typst fehlt: brew install typst"; exit 1; }
	typst compile --input paper=a5 $(TYP) $(PDF_A5)
	@echo "build: $(PDF_A5) geschrieben"

$(PDF_A4): $(TYP)
	@command -v typst >/dev/null 2>&1 || { echo "typst fehlt: brew install typst"; exit 1; }
	typst compile --input paper=a4 $(TYP) $(PDF_A4)
	@echo "build: $(PDF_A4) geschrieben"

$(TXT): $(SRC) $(TPL_TXT) $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $(SRC) $(TPL_TXT) $(TXT)

# --- Cover: txt -> typst -> png (1600x2560, EPUB-tauglich) ---
$(COVER_TYP): $(SRC) template_cover.typ $(BUILD) | $(SITE)
	$(PYTHON) $(BUILD) $(SRC) template_cover.typ $(COVER_TYP)

$(COVER): $(COVER_TYP)
	@command -v typst >/dev/null 2>&1 || { echo "typst fehlt: brew install typst"; exit 1; }
	typst compile --format png --ppi 72 $(COVER_TYP) $(COVER)
	@echo "build: $(COVER) geschrieben"

# --- EPUB: ueber das fertige HTML, mit Cover ---
$(EPUB): $(HTML) $(COVER)
	@command -v pandoc >/dev/null 2>&1 || { echo "pandoc fehlt: brew install pandoc"; exit 1; }
	pandoc $(HTML) -f html -t epub3 -o $(EPUB) \
	  --metadata title="Tōryō" \
	  --metadata author="Florian Metzger-Noel" \
	  --metadata lang=de \
	  --metadata rights="CC BY-SA 4.0" \
	  --epub-cover-image=$(COVER)
	@echo "build: $(EPUB) geschrieben"

open: $(INDEX)
	open $(INDEX)

clean:
	rm -f $(SITE)/*.html $(SITE)/*.typ $(SITE)/*.pdf $(SITE)/*.epub $(SITE)/*.png $(SITE)/*.txt

# Neu bauen, sobald sich eine Quelldatei aendert (benoetigt fswatch).
watch:
	@command -v fswatch >/dev/null 2>&1 || { echo "fswatch fehlt: brew install fswatch"; exit 1; }
	@echo "Beobachte Quellen ... (Ctrl-C beendet)"
	@fswatch -o $(SRC) $(TEMPLATE) $(TPL_INDEX) $(TPL_TYP) $(BUILD) \
	  | while read _; do $(MAKE) --no-print-directory all; done
