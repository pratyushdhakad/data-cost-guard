.PHONY: run test serve

run:
	PYTHONPATH=src python3 -m data_cost_guard.pipeline

test:
	python3 -m unittest discover -s tests -v

serve:
	python3 -m http.server 8000 --directory dashboard
