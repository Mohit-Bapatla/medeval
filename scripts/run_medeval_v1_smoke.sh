#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"

BACKEND_PYTHON="${BACKEND_PYTHON:-${BACKEND_DIR}/.venv/bin/python}"
BACKEND_MEDEVAL="${BACKEND_MEDEVAL:-${BACKEND_DIR}/.venv/bin/medeval}"

DATASET_PATH="../datasets/medeval-v1"
DATASET_NAME="MedEval v1 Public Healthcare Seed"

require_executable() {
  local path="$1"
  local label="$2"
  if [[ ! -x "${path}" ]]; then
    echo "ERROR: ${label} is not executable at ${path}" >&2
    echo "Install the backend environment first, for example:" >&2
    echo "  cd backend && python -m pip install -e \".[dev]\"" >&2
    exit 1
  fi
}

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "ERROR: required command not found: ${command_name}" >&2
    exit 1
  fi
}

run_experiment() {
  local label="$1"
  local config_path="$2"
  echo >&2
  echo "==> Running ${label}: ${config_path}" >&2
  local output
  output="$("${BACKEND_MEDEVAL}" run-experiment --config "${config_path}")"
  printf '%s\n' "${output}" >&2
  local experiment_id
  experiment_id="$(printf '%s\n' "${output}" | awk '/^Experiment ID: / {print $3; exit}')"
  if [[ -z "${experiment_id}" ]]; then
    echo "ERROR: could not parse experiment ID for ${label}" >&2
    exit 1
  fi
  printf '%s' "${experiment_id}"
}

require_command docker
require_executable "${BACKEND_PYTHON}" "BACKEND_PYTHON"
require_executable "${BACKEND_MEDEVAL}" "BACKEND_MEDEVAL"

echo "==> Starting local Postgres service"
cd "${REPO_ROOT}"
docker compose up -d db

echo
echo "==> Applying database migrations"
cd "${BACKEND_DIR}"
"${BACKEND_PYTHON}" -m alembic upgrade head

echo
echo "==> Validating MedEval v1 filesystem dataset"
"${BACKEND_MEDEVAL}" validate-dataset --path "${DATASET_PATH}"

echo
echo "==> Printing MedEval v1 dataset stats"
"${BACKEND_MEDEVAL}" dataset-stats --path "${DATASET_PATH}"

echo
echo "==> Seeding MedEval v1 into local database"
"${BACKEND_MEDEVAL}" seed-dataset --path "${DATASET_PATH}" --dataset-name "${DATASET_NAME}"

baseline_id="$(run_experiment "baseline" "../configs/experiments/medeval_v1_deterministic.yaml")"
clean_context_id="$(
  run_experiment "clean-context" "../configs/experiments/medeval_v1_deterministic_clean_context.yaml"
)"
refusal_aware_id="$(
  run_experiment "metadata-assisted refusal control" "../configs/experiments/medeval_v1_deterministic_refusal_aware.yaml"
)"
clean_refusal_id="$(
  run_experiment "clean-context refusal control" "../configs/experiments/medeval_v1_deterministic_top5_clean_refusal.yaml"
)"

echo
echo "==> Exporting baseline reports"
"${BACKEND_MEDEVAL}" export-report \
  --experiment-id "${baseline_id}" \
  --format markdown \
  --out ../reports/medeval_v1_seed_report.md
"${BACKEND_MEDEVAL}" export-report \
  --experiment-id "${baseline_id}" \
  --format json \
  --out ../reports/medeval_v1_seed_report.json
"${BACKEND_MEDEVAL}" export-results \
  --experiment-id "${baseline_id}" \
  --format csv \
  --out ../reports/medeval_v1_seed_results.csv

echo
echo "==> Exporting comparison reports"
"${BACKEND_MEDEVAL}" compare-runs \
  --experiment-id "${baseline_id}" \
  --experiment-id "${clean_context_id}" \
  --experiment-id "${refusal_aware_id}" \
  --experiment-id "${clean_refusal_id}" \
  --format markdown \
  --out ../reports/medeval_v1_comparison_report.md
"${BACKEND_MEDEVAL}" compare-runs \
  --experiment-id "${baseline_id}" \
  --experiment-id "${clean_context_id}" \
  --experiment-id "${refusal_aware_id}" \
  --experiment-id "${clean_refusal_id}" \
  --format json \
  --out ../reports/medeval_v1_comparison_report.json
"${BACKEND_MEDEVAL}" compare-runs \
  --experiment-id "${baseline_id}" \
  --experiment-id "${clean_context_id}" \
  --experiment-id "${refusal_aware_id}" \
  --experiment-id "${clean_refusal_id}" \
  --format csv \
  --out ../reports/medeval_v1_comparison_results.csv

echo
echo "==> Checking report artifact structure"
cd "${REPO_ROOT}"
"${BACKEND_PYTHON}" scripts/check_medeval_v1_reports.py

echo
echo "MedEval v1 smoke workflow completed successfully."
echo "Experiment IDs:"
echo "  baseline: ${baseline_id}"
echo "  clean_context: ${clean_context_id}"
echo "  refusal_aware_control: ${refusal_aware_id}"
echo "  clean_refusal_control: ${clean_refusal_id}"
echo "Report artifacts:"
echo "  reports/medeval_v1_seed_report.md"
echo "  reports/medeval_v1_seed_report.json"
echo "  reports/medeval_v1_seed_results.csv"
echo "  reports/medeval_v1_comparison_report.md"
echo "  reports/medeval_v1_comparison_report.json"
echo "  reports/medeval_v1_comparison_results.csv"
