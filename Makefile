.PHONY: medeval-v1-smoke medeval-v1-check-reports medeval-v1-validate

medeval-v1-smoke:
	./scripts/run_medeval_v1_smoke.sh

medeval-v1-check-reports:
	cd backend && ./.venv/bin/python ../scripts/check_medeval_v1_reports.py

medeval-v1-validate:
	cd backend && ./.venv/bin/medeval validate-dataset --path ../datasets/medeval-v1
	cd backend && ./.venv/bin/medeval dataset-stats --path ../datasets/medeval-v1
