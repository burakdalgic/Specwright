# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Specwright, please report it responsibly.

**Do not open a public issue.**

Instead, email **burak@dalgic.dev** (or open a [private security advisory](https://github.com/specwright/specwright/security/advisories/new) on GitHub) with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You can expect an initial response within 48 hours. We will work with you to understand the issue and coordinate a fix before any public disclosure.

## Scope

Specwright performs runtime code execution (import scanning in `specwright validate` and `specwright docs`). If you discover a way to exploit this for unintended code execution, that is in scope.

The following are **not** in scope:

- Vulnerabilities in dependencies (report those upstream)
- Issues requiring physical access to the machine
- Social engineering
