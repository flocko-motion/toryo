# toryo.txt ist die Quelle; toryo.html wird erzeugt.
SRC      := toryo.txt
TEMPLATE := template.html
BUILD    := build.py
OUT      := toryo.html

PYTHON   ?= python3

.PHONY: all clean open watch

all: $(OUT)

$(OUT): $(SRC) $(TEMPLATE) $(BUILD)
	$(PYTHON) $(BUILD) $(SRC) $(TEMPLATE) $(OUT)

open: $(OUT)
	open $(OUT)

clean:
	rm -f $(OUT)

# Neu bauen, sobald sich eine Quelldatei aendert (benoetigt fswatch).
watch:
	@command -v fswatch >/dev/null 2>&1 || { echo "fswatch fehlt: brew install fswatch"; exit 1; }
	@echo "Beobachte $(SRC) $(TEMPLATE) $(BUILD) ... (Ctrl-C beendet)"
	@fswatch -o $(SRC) $(TEMPLATE) $(BUILD) | while read _; do $(MAKE) --no-print-directory all; done
