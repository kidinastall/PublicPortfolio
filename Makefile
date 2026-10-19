.PHONY: evals-fast cost
evals-fast:
	python3 -m pytest -q evals
cost:
	python3 runtime/scripts/cost_model.py
