# Security Policy

## Supported Versions

| Version | Status | Notes |
| ------- | ------ | ----- |
| 0.1.x | ✅ Fully supported | Current release — receives all bug fixes and security patches |

This is an initial release. All prior internal versions were pre-publication
and are not considered released software.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities through one of these private channels:

1. **GitHub Private Vulnerability Reporting** (preferred):
   <https://github.com/grandmasteri/pycamtasia/security/advisories/new>

2. **Email**: Send an encrypted report to `austin@sixty-north.com`.

### What to Include

- A clear description of the vulnerability and its potential impact.
- Steps to reproduce, including a minimal `.cmproj`/`.tscproj` file if applicable.
- The pycamtasia version and Python version you tested against.
- Any suggested fix or mitigation, if you have one.

### What NOT to Do

- Do not disclose the vulnerability publicly (issues, social media, forums) before a fix is released.
- Do not exploit the vulnerability against other users' systems.

## Disclosure Policy

| Milestone | Target |
| --------- | ------ |
| Acknowledgment | Within **72 hours** of report |
| Triage & severity assessment | Within **1 week** |
| Fix for critical severity | Within **30 days** |
| Fix for high severity | Within **60 days** |
| Fix for medium/low severity | Next scheduled release |
| Public disclosure | Coordinated with reporter after fix is released |

We follow coordinated disclosure: the reporter is credited (unless they prefer anonymity), and the fix is published before the vulnerability details are made public. If we cannot meet a timeline target, we will communicate the revised estimate to the reporter.

## Scope

### In Scope

- All code in `src/camtasia/` and the `pytsc` CLI entry point.
- CI/CD configuration (`.github/workflows/`).
- Documentation that could mislead users into insecure usage.
- Dependencies declared in `pyproject.toml` (to the extent pycamtasia controls their usage).

### Out of Scope

- **TechSmith Camtasia desktop application** — report those to [TechSmith](https://www.techsmith.com/about-security.html) directly.
- **User-authored `.cmproj`/`.tscproj` data** — pycamtasia does not validate the semantic correctness of user content.
- **macOS/Windows file permissions** — the library relies on the operating system's permission model and does not implement its own access controls.
- **Vulnerabilities in upstream dependencies** that are not triggered by pycamtasia's usage of them.

## Known Security Considerations

pycamtasia processes Camtasia project files (`.cmproj`/`.tscproj`) which are JSON-based. The library does **not** execute arbitrary code from project files, make network requests, or access system resources beyond the project directory. However, users should be aware of the following:

### Path Handling

The library reads and writes file paths stored in `.tscproj` files (media references, output paths). These paths are passed through as-is — pycamtasia does **not** validate, sandbox, or sanitize them. If you ingest `.tscproj` files from untrusted sources, validate all embedded paths before performing filesystem operations based on them. Specifically, watch for:

- Path traversal (`../`) that could reference files outside the project bundle.
- Absolute paths pointing to sensitive locations.
- Symbolic link targets.

### Media Import & Filesystem Metadata

`import_media()` and related functions read filesystem metadata (file size, modification time, media dimensions via optional `pymediainfo`). Do not run these on adversarial media files from untrusted sources — a crafted file could exploit vulnerabilities in the underlying OS metadata APIs or in `pymediainfo`'s native library.

### pymediainfo (Optional Dependency)

The optional `pymediainfo` dependency wraps [MediaInfo](https://mediaarea.net/en/MediaInfo), a native C++ library. pycamtasia does not bundle or pin the native library version. Users who install `pymediainfo` should:

- Keep the system MediaInfo library up to date with security patches.
- Be aware that `pymediainfo` parses binary media formats — a class of software historically prone to memory-safety vulnerabilities.

### JSON Parsing

Project files are parsed with Python's built-in `json` module, which is not vulnerable to billion-laughs or entity-expansion attacks. However, extremely large or deeply nested project files could consume significant memory. The library does not impose size limits on input files.

## CVE / GHSA Policy

We request CVE identifiers through the [GitHub Security Advisory (GHSA)](https://docs.github.com/en/code-security/security-advisories) workflow. When a vulnerability is confirmed:

1. A draft GitHub Security Advisory is created.
2. A fix is developed in a private fork (via GHSA's temporary private fork feature).
3. A CVE is requested through the advisory.
4. The fix is merged, the advisory is published, and the CVE details are made public.

## Acknowledgments

We thank the security researchers who help keep pycamtasia safe. Contributors will be credited here (with permission) after their reported vulnerability is resolved.

*No acknowledgments yet — be the first!*
