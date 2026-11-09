PY ?= python3

.PHONY: check
check:
	$(PY) -m unittest discover -s tests
	$(PY) scripts/correct_pseudo_diophantus_attribution.py --check
	$(PY) scripts/compare_oga_glaux_dates.py --published-projection --check
	$(PY) scripts/build_source_components.py --check
	$(PY) scripts/validate_public_export.py
