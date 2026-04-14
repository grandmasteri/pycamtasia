# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 7.x     | ✅ Yes             |
| < 7.0   | ❌ No              |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by opening a
[GitHub issue](https://github.com/grandmasteri/pycamtasia/issues) with the
label `security`.

pycamtasia processes Camtasia project files (`.cmproj` / `.tscproj`) which
are JSON-based. The library does **not**:

- Execute arbitrary code from project files
- Make network requests
- Access system resources beyond the project directory

The primary security consideration is that project files may contain
file paths that reference media outside the project bundle. The library
reads and writes these paths but does not validate them.
