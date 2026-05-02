# REV-test_quality-001: tempfile.mkdtemp() leak reproduction

## Finding
15 test files use `tempfile.mkdtemp()` instead of pytest's `tmp_path` fixture,
leaking temporary directories on every test run.

## Reproduction

```bash
# Count leaked dirs before running tests
ls /tmp/ | wc -l

# Run the affected tests
cd /Users/isaadoug/Documents/pycamtasia
python -m pytest tests/test_caption_accessibility.py tests/test_themes.py -v --tb=no -q

# Count leaked dirs after
ls /tmp/ | wc -l
# Expect: more directories than before (each mkdtemp() call creates one)

# Verify the dirs are not cleaned up
ls -d /tmp/tmp* 2>/dev/null | tail -5
# Should show recently-created directories
```

## Affected files and line numbers

| File | Lines with mkdtemp() |
|------|---------------------|
| test_caption_accessibility.py | 20, 33, 50, 62, 73 |
| test_themes.py | 14, 71, 87, 103, 119 |
| test_invariants_property.py | 26, 129, 448, 565 |
| test_themes_extended.py | 168, 216, 234 |
| test_timeline_operations.py | 1245, 1264 |
| test_captions_export.py | 16, 80 |
| test_slide_import.py | 28 |
| test_device_frame.py | 23 |
| test_invariants.py | 28 |
| test_captions_import_export.py | 23 |
| test_export_campackage.py | 17 |
| test_slide_import_extended.py | 34 |

## Fix pattern

Before:
```python
tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
proj = Project.new(str(tmp))
```

After:
```python
def test_example(self, tmp_path):
    tmp = tmp_path / 'test.cmproj'
    proj = Project.new(str(tmp))
```
