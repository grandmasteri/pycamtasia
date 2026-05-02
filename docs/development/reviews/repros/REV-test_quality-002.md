# REV-test_quality-002: NamedTemporaryFile(delete=False) leak in test_import_trec_mocked

## Finding
Two tests create temp files with `delete=False` and rely on `finally: os.unlink(tmp)`
for cleanup. Combined with `importlib.reload()` for mock injection, this is fragile.

## Reproduction

```bash
cd /Users/isaadoug/Documents/pycamtasia

# Show the pattern
grep -n 'NamedTemporaryFile.*delete=False' tests/test_import_trec_mocked.py
# Lines 97 and 139

# Show the manual cleanup
grep -n 'os.unlink' tests/test_import_trec_mocked.py
# Lines 108 and 153

# Show the importlib.reload pattern
grep -n 'importlib.reload' tests/test_import_trec_mocked.py
# Multiple lines — reload in try AND finally blocks
```

## Risk scenario

If the mock setup raises an unexpected exception between `NamedTemporaryFile`
creation and the `finally` block, the temp file leaks. More critically, if
`importlib.reload(tp)` in the finally block fails, the trec_probe module
remains in a corrupted state with mocked pymediainfo for all subsequent tests.

## Fix pattern

```python
def test_dual_rate_audio_does_not_crash(self, tmp_path):
    trec = tmp_path / 'test.trec'
    trec.write_bytes(b'\x00')

    with patch('camtasia.media_bin.trec_probe.pymediainfo') as mock_pymediainfo:
        mock_pymediainfo.MediaInfo.parse.return_value = mock_mi
        result = tp.probe_trec(str(trec))
        assert len(result['sourceTracks']) == 1
```
