PY ?= python3

.PHONY: check
check:
	$(PY) -m unittest discover -s tests
	$(PY) scripts/validate_public_export.py
