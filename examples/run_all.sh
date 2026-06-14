#!/usr/bin/env bash
# run_all.sh — one-shot verification of the entire engine.
# Runs tests, all demos, generates HTML for every sample client.
set -e
cd "$(dirname "$0")/.."

echo "============================================================"
echo " 1. Running unit tests (calculators)"
echo "============================================================"
PYTHONPATH=. python3 tests/test_calculators.py

echo ""
echo "============================================================"
echo " 2. Running integration tests (all archetypes)"
echo "============================================================"
PYTHONPATH=. python3 tests/test_integration.py

echo ""
echo "============================================================"
echo " 3. Listing curated archetypes"
echo "============================================================"
python3 -m fitness_engine.cli archetypes

echo ""
echo "============================================================"
echo " 4. Archetype cohort showcase"
echo "============================================================"
python3 -m fitness_engine.cli showcase

echo ""
echo "============================================================"
echo " 5. Generating HTML plans for every sample client"
echo "============================================================"
for f in examples/sample_*.json; do
    name=$(basename "$f" .json | sed 's/^sample_//')
    echo "  -> $name"
    python3 examples/render_html.py "$f" "output/${name}_plan.html" > /dev/null
done
ls -la output/

echo ""
echo "============================================================"
echo " 6. Sample profile commands (run yourself)"
echo "============================================================"
echo "  python -m fitness_engine.cli profile examples/sample_client.json"
echo "  python -m fitness_engine.cli profile examples/sample_client.json --format html --out plan.html"
echo "  python -m fitness_engine.cli profile examples/sample_client.json --format json --out plan.json"
echo "  python -m fitness_engine.cli meals"
echo "  python -m fitness_engine.cli new /tmp/new_client.json"

echo ""
echo "============================================================"
echo " All checks complete!"
echo "============================================================"
