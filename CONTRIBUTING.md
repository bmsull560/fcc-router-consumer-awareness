# Contributing

Thanks for your interest in helping improve the FCC Router Consumer Awareness project.

## Local setup

The project requires Python 3.10 or newer. The fastest way to set up a local environment is:

```bash
make install
```

If you prefer to set up the virtual environment manually, run the equivalent of:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -e ".[dev]"
```

This installs the package plus development tools (ruff, mypy, pytest, pytest-cov, pre-commit, pip-audit).

## Development commands

Run all common tasks through `make`:

| Task | Command |
|---|---|
| Lint | `make lint` |
| Format | `make format` |
| Type check | `make type-check` |
| Run tests | `make test` |
| Run E2E tests | `make e2e` |
| Audit dependencies | `make audit` |
| Validate database | `make validate` |
| Build static site | `make build` |
| Run pre-commit hooks | `make pre-commit` |

## Pull request workflow

- Keep commits focused and easy to review.
- Add or update tests for any behavior change in `app/` or `scripts/`.
- CI must pass before merging.
- Update `CHANGELOG.md` under `## [Unreleased]`.

## Code style

- Python 3.10+.
- Type annotations are required for function signatures; mypy is enforced in CI.
- Linting and formatting are handled by ruff.
- Tests are written with pytest.

## Security and dependency hygiene

- Run `make audit` before opening a pull request.
- Do not commit secrets, API keys, or database files.
- Keep dependencies pinned with lower and upper bounds in `pyproject.toml`.
- If `pip-audit` reports a vulnerability, fix it in the same PR or document why it is a false positive.

## Security reporting

Please see [`SECURITY.md`](SECURITY.md) for how to report vulnerabilities privately.

## License

By contributing, you agree that your contributions will be released under the CC0-1.0 license.
