# Publishing pycamtasia to PyPI

This playbook walks through publishing pycamtasia to PyPI for the first time, then automating future releases.

## Prerequisites (one-time setup)

### 1. PyPI accounts
- Create account at https://pypi.org/account/register/
- Create account at https://test.pypi.org/account/register/ (staging / dry-run)
- Enable 2FA on BOTH (required for publishing)

### 2. Check name availability
```bash
pip index versions pycamtasia 2>&1 | head -5  # if 'No matching distribution', name is available
# or visit https://pypi.org/project/pycamtasia/ (404 = available)
```

### 3. Install build tools
```bash
python -m pip install --upgrade pip build twine
```

### 4. Configure trusted publisher (recommended, no API tokens)
1. Log in to pypi.org and test.pypi.org
2. Go to 'Publishing' -> 'Trusted publishers' in account settings
3. Add GitHub publisher:
   - Owner: grandmasteri
   - Repository: pycamtasia
   - Workflow filename: release.yml
   - Environment name: pypi (for real PyPI) or testpypi (for TestPyPI)
4. No token copy/paste needed; GitHub OIDC handles auth

## Pre-release checklist

Before every release, verify ALL of:

- [ ] Version bumped in pyproject.toml AND src/camtasia/version.py AND CHANGELOG.md
- [ ] CHANGELOG.md has a dated section for the new version (move from [Unreleased])
- [ ] All tests pass: `pytest`
- [ ] 100% coverage: `pytest --cov=camtasia --cov-fail-under=100`
- [ ] ruff clean: `ruff check src/ tests/`
- [ ] mypy clean: `mypy src/camtasia`
- [ ] Sphinx docs build: `cd docs && sphinx-build -b html . _build/html -W`
- [ ] git status clean
- [ ] git log shows expected commits since last tag
- [ ] CI green on main: `gh run list --limit 1 --branch main`

## First-time publish (manual dry-run to TestPyPI)

```bash
# 1. Clean old build artifacts
rm -rf dist/ build/ *.egg-info/

# 2. Build sdist and wheel
python -m build
# Output: dist/pycamtasia-0.1.0-py3-none-any.whl and dist/pycamtasia-0.1.0.tar.gz

# 3. Verify the build
python -m twine check dist/*
# Should say: PASSED for both files

# 4. Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*
# Enter username: __token__
# Enter password: <TestPyPI API token with upload:pycamtasia scope>

# 5. Verify install from TestPyPI in a clean venv
python -m venv /tmp/test-pycamtasia
source /tmp/test-pycamtasia/bin/activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pycamtasia
python -c 'import camtasia; print(camtasia.__version__)'
# Should print: 0.1.0

# 6. Smoke test
python -c 'from pathlib import Path; import camtasia; p = camtasia.new_project(Path("/tmp/smoke.cmproj")); p.save(); print("OK")'

# 7. Deactivate and cleanup
deactivate
rm -rf /tmp/test-pycamtasia /tmp/smoke.cmproj
```

## Publishing to PyPI (real)

```bash
# Use twine upload (not pip); this is the live PyPI
python -m twine upload dist/*
# Same token flow as TestPyPI but for pypi.org

# Verify immediately
pip install --upgrade pycamtasia
python -c 'import camtasia; print(camtasia.__version__)'
```

## Post-publish

1. Tag the release in git:
```bash
git tag v0.1.0
git push origin v0.1.0
```

2. Create GitHub Release:
```bash
gh release create v0.1.0 --title 'pycamtasia v0.1.0' --notes-from-tag
# Or use the web UI: https://github.com/grandmasteri/pycamtasia/releases/new
```

3. Announce (optional): Twitter, blog, Discord, etc.

## Automated releases going forward

Once trusted publisher is configured, future releases are fully automated:

```bash
# 1. Bump version everywhere, update CHANGELOG
# 2. Commit and tag:
git commit -am 'release: 0.2.0'
git tag v0.2.0
git push origin main --tags

# 3. The release.yml workflow automatically:
#    - Builds sdist + wheel
#    - Uploads to PyPI via OIDC
#    - Creates GitHub Release with auto-generated notes
```

See .github/workflows/release.yml for the workflow definition.

## Troubleshooting

- **'HTTPError: 400 Bad Request'**: Usually a version conflict — PyPI doesn't allow re-uploading the same version. Bump the version.
- **'File already exists'**: Same as above. Use a new version number; you can't delete+re-upload the same version on PyPI.
- **'InvalidDistribution: metadata is missing Content-Type'**: add `content-type = "text/markdown"` to readme in pyproject.toml.
- **Wheel builds but imports fail at install**: check `py.typed` and package-data are declared correctly.
- **Trusted publisher auth fails**: verify the workflow filename and environment match exactly what you configured on PyPI.

## References
- [Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [PEP 639 License Expressions](https://peps.python.org/pep-0639/)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Keep a Changelog](https://keepachangelog.com/)
