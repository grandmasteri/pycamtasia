# REV-test_quality-004: test_techsmith_roundtrip.py scans /tmp for test data

## Finding
`_collect_samples()` scans `/tmp/techsmith_extra` and `/tmp/techsmith_samples`
at module import time, making the parametrized test count environment-dependent.

## Reproduction

```bash
cd /Users/isaadoug/Documents/pycamtasia

# Check what samples are found on this machine
python -c "
from tests.test_techsmith_roundtrip import ALL_SAMPLES
print(f'Found {len(ALL_SAMPLES)} samples:')
for p in ALL_SAMPLES:
    print(f'  {p}')
"

# On a clean machine, only fixtures/ samples are found
# On a machine with /tmp/techsmith_*, additional samples appear

# Show the test count varies
python -m pytest tests/test_techsmith_roundtrip.py --collect-only 2>&1 | grep 'test session starts' -A 5
```

## Impact
Test results are non-reproducible: a developer's machine may test 20 samples
while CI tests only 4 (the bundled fixtures). A regression caught by an
extra sample on one machine won't be caught in CI.
