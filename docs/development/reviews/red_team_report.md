# Red Team Adversarial Audit Report

**Date:** 2026-05-03
**Auditor:** red_team agent
**Scope:** Post-fix library state after 17-reviewer + 4-critic + 8-fixer waves

## Executive Summary

The library is in **good shape for 0.1.0** with one HIGH finding that should be addressed before release. The massive review process caught the important bugs. My adversarial testing found 1 HIGH, 1 MEDIUM, and 2 LOW issues — all in the **intersection between fixes** (cross-cutting blind spots), which is exactly the gap siloed reviewers would miss.

## What I Tested

### 1. Fix Regression Analysis
Reviewed all 30+ commits from the last 6 hours. Inspected diffs for:
- Security fixes: symlink check, file size limit, path traversal in libzip
- Fuzz fixes: structural validation in `Project.__init__`, `validate()` robustness
- Edge case fixes: `speed_to_scalar`, `FrameStamp.frame_rate`, `add_clip` validation
- Error handling fixes: narrowed exception catches in probe functions

### 2. Adversarial Input After Fixes
Crafted inputs specifically designed to defeat the new guards:
- **Deeply nested groups** (bypasses file-size limit AND structural validation) → **FOUND BUG**
- **Huge string fractions** (bypasses `limit_denominator` cap) → **FOUND BUG**
- **Extreme speed values** (tests boundary of new validation) → **FOUND minor issue**
- **Path traversal with backslashes** (tests `_is_safe_relative_path`) → Safe on POSIX
- **Symlink + rmtree** in `from_template`/`new` → **FOUND defense gap** (not exploitable on Py 3.12)

### 3. Cross-Cutting Analysis
Looked for bugs spanning multiple reviewer aspects:
- Security × fuzz: The fuzz fixes validated structure but not depth → **REV-red_team-001**
- Typing × security: `parse_scalar` string path bypasses float safeguards → **REV-red_team-002**
- Security × API: `from_template` has weaker symlink protection than `load` → **REV-red_team-003**

### 4. Coverage Theater Check
- Verified that `except Exception` catches in `project.py` (lines 86, 110, 123, 148) are properly narrowed with specific catches first — they are.
- Verified that `history.py` `except Exception` blocks are `# pragma: no cover` — appropriate since they're defensive re-raise paths.
- No bare `except:` clauses found anywhere in src/.

### 5. API Consistency Spot Check
- `Project.save_as` does not exist (confirmed — `save()` with path arg is the pattern)
- `import_media` docstring matches signature
- `add_clip` docstring matches the new validation behavior

## Findings

| ID | Severity | Summary |
|----|----------|---------|
| REV-red_team-001 | **HIGH** | Deeply nested groups cause unhandled `RecursionError` on load |
| REV-red_team-002 | MEDIUM | `parse_scalar` string fractions bypass `limit_denominator` cap |
| REV-red_team-003 | LOW | `from_template`/`new` missing symlink check before `rmtree` |
| REV-red_team-004 | LOW | `speed_to_scalar` produces huge Fractions for extreme inputs |

## What the Original Review Missed and Why

### REV-red_team-001 (HIGH): Nested group recursion bomb
**Why missed:** The fuzz reviewer tested corrupted top-level structure (missing keys, wrong types) but not **valid-structure-but-pathological-depth** inputs. The security reviewer focused on file I/O (symlinks, file size, path traversal) not JSON parsing. Neither reviewer considered that `json.loads` itself has a recursion limit. This is a classic cross-cutting blind spot: it's simultaneously a fuzz issue, a security issue, and a validation issue.

### REV-red_team-002 (MEDIUM): Unbounded string fractions
**Why missed:** The edge_cases reviewer tested `speed_to_scalar` with zero/negative/tiny values but not the `parse_scalar` string path. The typing reviewer checked type annotations but not value bounds. The design-decisions doc (D-005) explicitly mentions string fractions as a "higher precision" path, which may have discouraged scrutiny.

### REV-red_team-003 (LOW): Missing symlink check
**Why missed:** The security reviewer added the symlink check to `Project.load()` but didn't audit all other `shutil.rmtree` call sites. The fix was scoped to the specific finding (REV-security-003) rather than applied as a pattern across the codebase.

## Overall Assessment

**Confidence: The library is ready for 0.1.0**, contingent on fixing REV-red_team-001.

Rationale:
- The HIGH finding (recursion bomb) is a real DoS vector but requires a crafted malicious file. If the library is used only with trusted project files, the risk is low. If it processes untrusted files (e.g., a web service), the fix is essential.
- The MEDIUM finding is a quality issue, not a correctness bug — it produces valid but wasteful output.
- The LOW findings are defense-in-depth improvements.
- The existing test suite (5000+ unit tests, 217 integration tests, 100% coverage, mypy, ruff) is genuinely thorough. The review process caught and fixed 47 HIGH/CRITICAL issues. The 4 issues I found are in the gaps between reviewer scopes, which is expected.

## Methodology Notes

- Total time: ~60 minutes of active testing
- Approach: Read design decisions first, then recent fix diffs, then targeted adversarial testing
- Tools: Python REPL for crafting adversarial inputs, grep for anti-pattern scanning
- Did NOT modify src/ or tests/ — all findings are in review artifacts only
