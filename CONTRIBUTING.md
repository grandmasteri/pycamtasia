# Contributing to pycamtasia

Thanks for your interest in contributing! We welcome bug reports, documentation improvements, tests, and code contributions of all sizes.

Before contributing, please read the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Development setup

```bash
# Clone the repository
git clone https://github.com/grandmasteri/pycamtasia.git
cd pycamtasia

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install the library in editable mode with all dev extras
pip install -e '.[test,dev,docs]'
```

## Running tests and checks

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/camtasia

# Unit tests (parallel, ~30s)
pytest

# With coverage (100% required)
pytest --cov=camtasia --cov-fail-under=100

# Integration tests (macOS only; requires Camtasia app)
pytest -m integration

# Docs build
cd docs && sphinx-build -b html . _build/html -W
```

## Pull request checklist

Before opening a PR:

- [ ] Tests have been added or updated
- [ ] Documentation has been updated (README, docs/, docstrings) if user-facing
- [ ] `CHANGELOG.md` has an entry under `[Unreleased]` if user-facing
- [ ] `ruff check src/ tests/` passes
- [ ] `mypy src/camtasia` passes
- [ ] `pytest` passes with 100% coverage maintained
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat: add X`, `fix: Y`, `docs: Z`)
- [ ] You've read the [Code of Conduct](CODE_OF_CONDUCT.md)

## Key rules

1. **Clip mutations must cascade-delete transitions.** Never delete clips by mutating `_data['medias']` directly — use `track.remove_clip()`, which removes transitions referencing the clip.

2. **Parameter keys use hyphens.** Camtasia's JSON uses `mask-shape`, not `mask_shape`. Python properties handle the mapping, but raw dicts must use hyphens.

3. **Effects use plain scalar format.** Parameters are flat: `{"defaultValue": 16.0, "type": "double", "interp": "linr"}`. No extra nesting.

4. **Camtasia integration test is mandatory** for any change affecting `.tscproj` output. The JSON format is reverse-engineered — always validate in the real app.

5. **100% line coverage required.** The build fails below 100%.

6. **Use [Conventional Commits](https://www.conventionalcommits.org/).** Examples: `feat: add mask effect`, `fix: cascade-delete on group clips`, `test: cover edge case in split`, `docs: update quickstart`, `chore: bump ruff`.

## Reporting issues

- **Bugs**: [File a bug report](https://github.com/grandmasteri/pycamtasia/issues/new?template=bug_report.yml)
- **Features**: [File a feature request](https://github.com/grandmasteri/pycamtasia/issues/new?template=feature_request.yml)
- **Security**: See [SECURITY.md](SECURITY.md) — do NOT file a public issue

## Asking questions

- [GitHub Discussions](https://github.com/grandmasteri/pycamtasia/discussions) for Q&A
- [Documentation](docs/) for guides and API reference

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
