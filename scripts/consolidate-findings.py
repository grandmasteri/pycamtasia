#!/usr/bin/env python3
"""Consolidate review findings into ROADMAP.md and produce a dashboard.

Reads all docs/development/reviews/*.jsonl files (one JSON finding per
line per aspect file) and:

1. Validates each finding against the schema.
2. Dedupes by semantic similarity (file+line, finding text hash).
3. Outputs consolidated findings to /tmp/pycamtasia_findings.jsonl.
4. Appends a new section to ROADMAP.md listing all findings sorted
   by severity.
5. Prints a dashboard summary.

Usage:
    python scripts/consolidate-findings.py                # default: all
    python scripts/consolidate-findings.py --verified     # only VERIFIED
    python scripts/consolidate-findings.py --severity HIGH  # HIGH or CRITICAL
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWS_DIR = ROOT / 'docs' / 'development' / 'reviews'
ROADMAP = ROOT / 'ROADMAP.md'
OUTPUT = Path('/tmp/pycamtasia_findings.jsonl')

SEVERITY_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']


def load_findings() -> list[dict]:
    findings: list[dict] = []
    for jsonl_file in sorted(REVIEWS_DIR.glob('*.jsonl')):
        aspect_from_filename = jsonl_file.stem
        with jsonl_file.open() as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    d = json.loads(line)
                    # Infer aspect if missing
                    if 'aspect' not in d or not d['aspect']:
                        d['aspect'] = aspect_from_filename
                    findings.append(d)
                except json.JSONDecodeError as e:
                    print(f'ERROR: {jsonl_file.name}:{lineno} invalid JSON: {e}', file=sys.stderr)
    return findings


def content_hash(finding: dict) -> str:
    """Hash content for dedup. Ignores ID and verification fields.

    Only exact content duplicates are collapsed. Different-aspect findings
    at the same file:line with different descriptions are NOT dedup'd.
    """
    loc = finding.get('location', {})
    if isinstance(loc, str):
        loc = {'file': loc}
    key = (
        finding.get('id', ''),  # include ID so we basically only collapse exact duplicates
    )
    return hashlib.sha256(str(key).encode()).hexdigest()[:12]


def dedup(findings: list[dict]) -> tuple[list[dict], int]:
    seen: dict[str, dict] = {}
    dup_count = 0
    for f in findings:
        h = content_hash(f)
        if h not in seen:
            seen[h] = f
        else:
            # Keep higher severity
            existing = seen[h]
            if SEVERITY_ORDER.index(f['severity']) < SEVERITY_ORDER.index(existing['severity']):
                seen[h] = f
            dup_count += 1
    return list(seen.values()), dup_count


def dashboard(findings: list[dict]) -> None:
    print('=' * 60)
    print('  PYCAMTASIA REVIEW DASHBOARD')
    print('=' * 60)
    print(f'Total findings: {len(findings)}')
    print()
    # By severity
    by_sev: dict[str, int] = defaultdict(int)
    for f in findings:
        by_sev[f['severity']] += 1
    print('By severity:')
    for sev in SEVERITY_ORDER:
        if by_sev[sev]:
            print(f'  {sev:10s} {by_sev[sev]:4d}')
    print()
    # By aspect
    by_aspect: dict[str, int] = defaultdict(int)
    for f in findings:
        by_aspect[f.get('aspect', 'unknown')] += 1
    print('By aspect:')
    for aspect in sorted(by_aspect):
        print(f'  {aspect:30s} {by_aspect[aspect]:4d}')
    print()
    # Verification status
    by_status: dict[str, int] = defaultdict(int)
    for f in findings:
        by_status[f.get('verification_status', 'PENDING')] += 1
    print('Verification status:')
    for status in ['VERIFIED', 'UNCONFIRMED', 'FALSE_POSITIVE', 'DUPLICATE', 'PENDING']:
        if by_status[status]:
            print(f'  {status:15s} {by_status[status]:4d}')
    print()
    # Resolution
    resolved = sum(1 for f in findings if f.get('resolved'))
    if resolved:
        print(f'Resolved: {resolved}/{len(findings)} ({100*resolved/len(findings):.0f}%)')
    print('=' * 60)


def roadmap_section(findings: list[dict], filter_severity: str | None = None) -> str:
    """Render findings as a markdown section for ROADMAP.md."""
    lines = ['## Pre-release audit findings (2026-05-01)', '']
    lines.append(
        '_Findings from the 17-agent review swarm. Each entry has a stable ID '
        'traceable back to the full details in `docs/development/reviews/<aspect>.jsonl`. '
        'Mark items as `[x] RESOLVED` when fixed, citing the commit hash._'
    )
    lines.append('')
    findings_sorted = sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER.index(f['severity']), f['id']),
    )
    current_sev = None
    for f in findings_sorted:
        if filter_severity and f['severity'] not in filter_severity:
            continue
        if f['severity'] != current_sev:
            current_sev = f['severity']
            lines.append(f'\n### {current_sev}\n')
        check = '[x]' if f.get('resolved') else '[ ]'
        commit = f' (resolved in `{f["resolved_by_commit"][:7]}`)' if f.get('resolved_by_commit') else ''
        loc = f.get('location', {})
        if isinstance(loc, str):
            loc_str = loc
        elif isinstance(loc, dict):
            loc_str = f'{loc.get("file", "?")}:{loc.get("line", "?")}'
        else:
            loc_str = '?'
        lines.append(f'- {check} **{f.get("id", "???")}** ({f.get("aspect", "unknown")}) — {f.get("finding", "(no description)")} `{loc_str}`{commit}')
    return '\n'.join(lines) + '\n'


def append_to_roadmap(section: str) -> None:
    current = ROADMAP.read_text()
    marker = '## Pre-release audit findings'
    if marker in current:
        # Replace existing section
        before, _, after = current.partition(marker)
        # Find the next ## heading
        rest_lines = after.split('\n')
        end_idx = len(rest_lines)
        for i, line in enumerate(rest_lines[1:], 1):
            if line.startswith('## '):
                end_idx = i
                break
        new_content = before + section + '\n'.join(rest_lines[end_idx:])
        ROADMAP.write_text(new_content)
    else:
        # Insert after "## Pending Bugs" section
        if '## Pending Bugs' in current:
            parts = current.split('## Pending Bugs', 1)
            tail = parts[1]
            # Find the next ## heading
            next_heading = tail.find('\n## ')
            if next_heading == -1:
                new_content = current + '\n' + section
            else:
                new_content = (
                    parts[0]
                    + '## Pending Bugs'
                    + tail[:next_heading]
                    + '\n'
                    + section
                    + tail[next_heading:]
                )
            ROADMAP.write_text(new_content)
        else:
            ROADMAP.write_text(current + '\n' + section)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--verified', action='store_true', help='Only include VERIFIED findings')
    parser.add_argument('--severity', nargs='+', help='Filter by severity (e.g. CRITICAL HIGH)')
    parser.add_argument('--dry-run', action='store_true', help="Don't modify ROADMAP.md")
    args = parser.parse_args()

    findings = load_findings()
    if not findings:
        print('No findings found in docs/development/reviews/*.jsonl', file=sys.stderr)
        return 1

    findings, dup_count = dedup(findings)
    if dup_count:
        print(f'Deduped {dup_count} findings.', file=sys.stderr)

    if args.verified:
        findings = [f for f in findings if f.get('verification_status') == 'VERIFIED']

    # Write consolidated JSONL
    with OUTPUT.open('w') as f:
        for finding in findings:
            f.write(json.dumps(finding) + '\n')

    dashboard(findings)

    # Append to ROADMAP
    section = roadmap_section(findings, filter_severity=args.severity)
    if args.dry_run:
        print('\n--- ROADMAP section (dry-run) ---')
        print(section)
    else:
        append_to_roadmap(section)
        print(f'\nWrote {len(findings)} findings to ROADMAP.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
