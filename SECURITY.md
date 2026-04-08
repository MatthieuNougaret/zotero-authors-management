# Security Policy

## Supported Versions

I provide security updates for the current major development branch.

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Data Integrity & Safety

**Important:** This tool is designed to create **copy(ies)** of your `zotero.sqlite` file(s). 
- It should never even try to modify the original zotero database file(s), if so, block it and repport it!
- All SQL call is for a local interaction without any network connection. If it try to connect out of the computer port, block it and repport it!

## Reporting a Vulnerability

If you discover a security vulnerability (such as a flaw that could cause data corruption or unintended file access):

1. **Do not open a public issue immediately.**
2. Please contact the maintainer directly via the GitHub Profile to report the flaw privately.
3. Provide a clear description of the vulnerability, including:
   - Whether it originates in a dependency (e.g., Pygame, SQLite3) or the project code.
   - Steps to reproduce the risk.
   - Any suggested fixes or mitigations.
