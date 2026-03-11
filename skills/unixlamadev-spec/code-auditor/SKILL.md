---
name: code-auditor
description: Review any GitHub repo for security issues and code quality
acceptLicenseTerms: true
metadata:
  clawdbot:
    emoji: "🔍"
    homepage: https://aiprox.dev
    requires:
      env:
        - AIPROX_SPEND_TOKEN
---

# Code Auditor

Audit any GitHub repository for security vulnerabilities, code quality issues, and best practices. Returns a score, detailed findings, and actionable summary.

## When to Use

- Security review before deploying code
- Evaluating third-party dependencies or libraries
- Code quality assessment for repositories
- Finding vulnerabilities in open source projects

## Usage Flow

1. Provide a GitHub repository URL
2. Optionally specify an audit focus (security, performance, etc.)
3. AIProx routes to the code-auditor agent
4. Returns score (0-100), findings array, and summary

## Security Manifest

| Permission | Scope | Reason |
|------------|-------|--------|
| Network | aiprox.dev | API calls to orchestration endpoint |
| Env Read | AIPROX_SPEND_TOKEN | Authentication for paid API |

## Make Request

```bash
curl -X POST https://aiprox.dev/api/orchestrate \
  -H "Content-Type: application/json" \
  -H "X-Spend-Token: $AIPROX_SPEND_TOKEN" \
  -d '{
    "task": "security audit",
    "repo_url": "https://github.com/user/repo"
  }'
```

### Response

```json
{
  "score": 72,
  "findings": [
    "No input validation on user-supplied data in handler.js:45",
    "Hardcoded API key found in config.js:12",
    "Missing rate limiting on public endpoints"
  ],
  "summary": "Repository has moderate security concerns. Critical: 1 hardcoded secret. High: missing input validation. Recommend immediate remediation."
}
```

## Trust Statement

Code Auditor analyzes public repository contents only. No code is executed. Analysis is performed by Claude via LightningProx. Your spend token is used for payment; no other credentials are stored or transmitted.
