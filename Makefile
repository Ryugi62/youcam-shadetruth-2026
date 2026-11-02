.PHONY: run test drift
run:
	python3 server.py
test:
	python3 -m pytest -q
drift:
	python3 scripts/run_drift_table.py && mkdir -p web/data && cp data/drift.json web/data/drift.json
