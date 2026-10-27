PY ?= python3

.PHONY: check
check:
	$(PY) -m unittest discover -s tests
	$(PY) scripts/build_source_components.py --check
	$(PY) scripts/validate_public_export.py
