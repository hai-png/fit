# Contributing to Fitness Engine

Thanks for your interest in contributing! This document covers the basics.

## Development setup

```bash
git clone https://github.com/hai-png/fit.git
cd fit
python -m pip install -e .
python -m pip install ruff pytest pytest-cov
```

## Before submitting a pull request

1. **Run the tests.** All 92 tests must pass.
   ```bash
   python -m pytest -q
   ```

2. **Run the linter.** Ruff must report zero violations.
   ```bash
   ruff check .
   ```

3. **Run the integration script.** It exercises every CLI command and every
   sample profile.
   ```bash
   bash examples/run_all.sh
   ```

4. **Add tests for new behavior.** If you fix a bug, add a regression test
   that would have caught it. If you add a feature, add tests that verify
   the feature works.

5. **Update the changelog.** Add an entry under `[Unreleased]` in
   `CHANGELOG.md` describing your change.

## Code style

- Line length: 120 characters (configured in `pyproject.toml`).
- Use type hints on every public function.
- Pure functions in `calculators.py`, `decision_trees.py`, and `meal_plans.py`.
  Side effects (file I/O, randomness) belong in `recommender.py`,
  `persistence.py`, `cli.py`, or `examples/`.
- Dataclasses for all result types. No bare dicts in public APIs.
- Docstrings cite sources where applicable (RippedBody, M&S, specific
  papers). Reference guides belong in `docs/reference/`.

## Pull request flow

1. Fork the repository and create a feature branch.
2. Make your changes. Keep commits focused; one logical change per commit.
3. Push to your fork and open a pull request against `main`.
4. CI runs automatically. Fix any failures before requesting review.

## Reporting bugs

Open a GitHub issue with:
- A minimal reproduction (a Python snippet or a sample JSON profile).
- The expected behavior.
- The actual behavior, including the full traceback if applicable.
- The engine version (`python -c "from fitness_engine import __version__; print(__version__)"`).
