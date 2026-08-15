# Security Policy 🔐

BasiliskShell is a project whose **core purpose** is to safely translate natural-language
requests into Bash commands. Security is therefore a first-class concern, not an afterthought.

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest commit on `main` | ✅ |
| Older commits | ❌ |

Please upgrade to the latest version before reporting.

---

## Reporting a Vulnerability

**Please do not file a public issue for security problems.**

Instead, report privately via one of these channels:

1. **GitHub Security Advisories** (preferred):
   Visit `https://github.com/sakawatkabir13/basilisk-shell/security/advisories/new`
2. **Email**: `sakawatkabir13@gmail.com` (replace with your real contact address)

Include as much of the following as you can:

- Description of the vulnerability and its impact
- Steps to reproduce / proof-of-concept
- Affected file(s) and, if known, suggested fix
- Your name / handle for acknowledgement (optional)

You should receive a response within **72 hours**. We will coordinate disclosure timing
with you before publishing any patch or CVE.

---

## What We Promise

- We will acknowledge new reports within 3 days.
- We will keep you informed of the progress toward a fix.
- We will credit you (if you wish) in the release notes once the issue is resolved.

---

## Areas of Special Concern

If you find a way to bypass any of these, please report it immediately:

- The `BLOCKLIST` patterns in `basilisk_ai_setup.py`
- The static `security_audit()` function
- The `subprocess.run(..., shell=False)` execution path
- The `eval "$cmd"` paths in `basilisk.sh` (for non-AI commands)
- Login / password hashing logic

Even something like “the AI can be tricked into producing `rm -rf /`” counts.
