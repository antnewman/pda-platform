# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

We support only the latest minor version with security updates.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Where to Report

Email security issues to: **security@pdataskforce.com**

### What to Include

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)
- Your contact information

### Response Timeline

- **Acknowledgement**: Within 48 hours
- **Initial assessment**: Within 5 working days
- **Fix timeline**: Depends on severity
  - Critical: 7 days
  - High: 14 days
  - Medium: 30 days
  - Low: Next planned release

## Security Considerations

### Data Processing

pda-platform is designed with security in mind:

- **No network calls**: All processing is local
- **No persistent storage**: No data is stored between sessions
- **No telemetry**: No usage data is transmitted
- **File-based input only**: Processes only files you explicitly provide

### Deployment Recommendations

1. **Principle of least privilege**: Run with minimal necessary permissions
2. **Input validation**: Validate project files before processing
3. **Sandboxed environment**: Consider running in isolated environments for untrusted files
4. **Keep dependencies updated**: Regularly update pm-data-tools and dependencies

## Known Security Limitations

1. **File parsing**: Malformed project files could potentially cause crashes
2. **XML/Excel processing**: Relies on underlying parser security
3. **Resource exhaustion**: Very large files could consume significant memory

## Security Best Practices

### For Users

- Only process project files from trusted sources
- Keep the platform updated to the latest version
- Review output before using in production decisions
- Report any suspicious behavior

### For Developers

- Follow secure coding practices
- Validate all inputs
- Keep dependencies updated
- Run security scanners in CI/CD
- Review dependencies for known vulnerabilities

## Vulnerability Disclosure

We follow coordinated disclosure:
- We will work with you to understand and resolve the issue
- We will not take legal action against good-faith security researchers
- We request 90 days before public disclosure to allow time for fixes

## Security Updates

Security updates are announced via:
- GitHub Security Advisories
- Release notes
- PyPI release metadata

## Contact

- Security issues: security@pdataskforce.com
- General enquiries: hello@pdataskforce.com
