# REV-test_quality-003: test_trec_import.py depends on external /tmp project

## Finding
Three tests in TestProbeTrec silently skip when `/tmp/Anomaly Detection Demo (v3).cmproj`
doesn't exist, providing zero coverage in CI.

## Reproduction

```bash
cd /Users/isaadoug/Documents/pycamtasia

# Verify the directory doesn't exist (typical CI/clean machine)
ls '/tmp/Anomaly Detection Demo (v3).cmproj' 2>&1
# Expected: No such file or directory

# Run the tests and observe they all skip
python -m pytest tests/test_trec_import.py -v 2>&1 | grep -E 'SKIP|PASS|FAIL'
# Expected: all 3 TestProbeTrec tests show SKIPPED
# test_probe_nonexistent_raises should PASS (it doesn't need the external file)

# Count actual test executions
python -m pytest tests/test_trec_import.py -v 2>&1 | grep -c 'PASSED'
# Expected: 1 (only test_probe_nonexistent_raises)
```

## Impact
These tests appear green in CI but provide zero coverage of probe_trec()
with real .trec files. The mocked version in test_import_trec_mocked.py
covers some paths but not the actual pymediainfo parsing.
