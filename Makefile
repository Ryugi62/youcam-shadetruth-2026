.PHONY: run test drift
run:
	python3 server.py
test:
	python3 -m pytest -q
drift:
	python3 scripts/run_drift_table.py && mkdir -p docs/data && cp data/drift.json docs/data/drift.json
