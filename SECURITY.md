# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 7.x     | ✅ Yes             |
| < 7.0   | ❌ No              |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it through
[GitHub's private vulnerability reporting](https://github.com/grandmasteri/pycamtasia/security/advisories/new).

**Do not open a public issue for security vulnerabilities.**

Reports will be acknowledged within 72 hours.

pycamtasia processes Camtasia project files (`.cmproj` / `.tscproj`) which
are JSON-based. The library does **not**:

- Execute arbitrary code from project files
- Make network requests
- Access system resources beyond the project directory

The primary security consideration is that project files may contain
file paths that reference media outside the project bundle. The library
reads and writes these paths but does not validate them.
