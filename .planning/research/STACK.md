# Technology Stack: GitHub Actions Auto-Scoring Infrastructure

**Project:** DDSC x DQC Quantum Portfolio Challenge - Auto-Scoring CI/CD
**Researched:** 2026-02-12
**Overall Confidence:** HIGH

## Executive Summary

GitHub Actions-based auto-scoring for coding challenges in public repositories requires a security-first architecture due to the risks of executing untrusted code from forked PRs. The recommended 2026 stack uses a **two-workflow pattern** with `workflow_run` triggers to safely score submissions, post PR comments, and maintain a README leaderboard without exposing repository secrets or write access to untrusted code.

**Critical Security Finding:** Never use `pull_request_target` with explicit checkout of PR code. This creates "pwn request" vulnerabilities that can compromise the repository. The March 2025 tj-actions/changed-files compromise affected 23,000+ repositories by exploiting mutable Git tags.

## Recommended Stack

### Core CI/CD Platform

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **GitHub Actions** | Native | CI/CD orchestration | Built-in to GitHub, zero external infrastructure, free for public repos, mature security model as of 2026 |
| **GitHub-hosted runners** | `ubuntu-latest` | Execution environment | Ephemeral, clean, isolated VMs prevent persistent compromise. No self-hosted runner security risks. |

**Confidence:** HIGH (Official GitHub documentation, widely adopted)

### Workflow Execution Pattern

| Component | Technology | Version | Purpose | Why |
|-----------|------------|---------|---------|-----|
| **Trigger 1** | `pull_request` | N/A | Score submission (read-only) | Runs in PR context with read-only token, no secrets access. Safe for untrusted code. |
| **Trigger 2** | `workflow_run` | N/A | Post results + update leaderboard | Runs in base repo context with write access. Triggered AFTER scoring completes. Cannot execute PR code. |

**Confidence:** HIGH (GitHub Security Lab official recommendation)

**Architecture Rationale:**
- **Workflow 1 (`pull_request`)**: Validates JSON schema, runs evaluate.py on user submission, uploads results as artifact. Zero write permissions, zero secrets.
- **Workflow 2 (`workflow_run`)**: Downloads scoring artifact, posts PR comment, updates README leaderboard. Has write access but NEVER checks out PR code.

This pattern is the [official secure solution](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) for "building untrusted code and writing to a PR."

### Python Environment Setup

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **actions/setup-python** | `v6` (pinned SHA) | Install Python runtime | Official GitHub action, upgraded to node24 in 2026, supports Python 3.13 |
| **Python** | `3.11` | Script execution environment | Matches project requirements.txt, stable, widely supported |
| **pip cache** | Built-in | Dependency caching | Speeds up workflow runs, built into setup-python@v6 |

**Confidence:** HIGH (Official GitHub Actions repository)

**Installation in workflow:**
```yaml
- uses: actions/setup-python@f677139bbe7f9c59b41e40162b753c062f5d49a3  # v6.0.0
  with:
    python-version: '3.11'
    cache: 'pip'
```

### PR Comment Automation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **thollander/actions-comment-pull-request** | `v3.0.1` (pinned SHA) | Post scoring results as PR comment | Most popular PR comment action (2026), supports comment updates via `comment-tag`, prevents spam |

**Confidence:** HIGH (GitHub Marketplace, 3.0.1 released Nov 2024)

**Usage Pattern:**
```yaml
- uses: thollander/actions-comment-pull-request@24bffb9b452ba05a5f16e8aa61c4c4f6e8f82d16  # v3.0.1
  with:
    message: |
      ## Submission Scored

      Energy: **${{ env.ENERGY }}**
      Feasible: **${{ env.FEASIBLE }}**
      Cardinality: **${{ env.CARDINALITY }}**
    comment-tag: quantum-challenge-score
    create-if-not-exists: true
```

The `comment-tag` ensures edits to existing comments (prevents spam when participants push updates).

### README Leaderboard Update

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **stefanzweifel/git-auto-commit-action** | `v7.1.0` (pinned SHA) | Commit leaderboard changes to README | Most popular auto-commit action (2026), handles git configuration automatically, works with GITHUB_TOKEN |
| **Python script** | Custom | Parse scores, update README table | Domain-specific logic for sorting/formatting leaderboard |

**Confidence:** HIGH (GitHub Marketplace, v7.x uses node24 runtime)

**Usage Pattern:**
```yaml
- run: python scripts/update_leaderboard.py --submission-file results.json
- uses: stefanzweifel/git-auto-commit-action@8621497c8c39c72f3e2a999a26b4ca1b5058a842  # v7.1.0
  with:
    commit_message: "Update leaderboard: ${{ github.event.workflow_run.head_repository.owner.login }}"
    file_pattern: README.md
```

### JSON Validation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Existing evaluate.py** | Current | Schema validation + scoring | Already implements JSON parsing, validation, scoring. No need for separate action. |
| **Alternative: liminalitythree/validate-json** | `v1.0.1` | (Optional) Pre-validation step | Lightweight, can fail-fast before running Python if JSON is malformed |

**Confidence:** MEDIUM (evaluate.py is HIGH, separate validator is optional optimization)

**Recommendation:** Use evaluate.py for all validation. Adding a separate JSON validator is premature optimization since evaluate.py already handles malformed JSON gracefully.

## Security Architecture

### Action Version Pinning (CRITICAL)

| Practice | Recommendation | Why |
|----------|---------------|-----|
| **Pin to commit SHA** | REQUIRED for ALL third-party actions | Tags are mutable. March 2025 tj-actions/changed-files attack: attacker updated 350+ tags to malicious commit, compromised 23,000+ repos. |
| **Use Dependabot/Renovate** | REQUIRED | Automate SHA updates when new versions release. Safety + maintainability. |
| **Comment with version tag** | Best practice | `actions/setup-python@abc123  # v6.0.0` makes it human-readable |

**Confidence:** HIGH (Multiple security advisories, GitHub official docs)

**Example:**
```yaml
# BAD: Mutable tag
- uses: thollander/actions-comment-pull-request@v3

# GOOD: Immutable SHA with comment
- uses: thollander/actions-comment-pull-request@24bffb9b452ba05a5f16e8aa61c4c4f6e8f82d16  # v3.0.1
```

### GITHUB_TOKEN Permissions (Principle of Least Privilege)

| Workflow | Required Permissions | Rationale |
|----------|---------------------|-----------|
| **Workflow 1 (score)** | `contents: read` (default) | Read-only. Checks out base repo data (instance.json, evaluate.py). No PR code checkout. |
| **Workflow 2 (comment+leaderboard)** | `contents: write`, `pull-requests: write` | Writes README, posts PR comments. Runs in base context, never executes PR code. |

**Confidence:** HIGH (GitHub official documentation)

**Configuration:**
```yaml
# Workflow 1: score.yml
permissions:
  contents: read

# Workflow 2: report.yml
permissions:
  contents: write
  pull-requests: write
```

### Fork PR Approval Settings

| Setting | Recommendation | Why |
|---------|---------------|-----|
| **Require approval for fork PRs** | YES | Prevents abuse from throwaway accounts. Maintainer must approve first run. |
| **Require approval for first-time contributors** | YES | Additional safety layer. |

**Confidence:** HIGH (GitHub official settings)

**Configuration:** Repository Settings → Actions → General → Fork pull request workflows from outside collaborators

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| **PR trigger pattern** | `pull_request` + `workflow_run` (two workflows) | `pull_request_target` (single workflow) | `pull_request_target` with checkout is a [known security vulnerability](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/). Risk of pwn requests, cache poisoning, secret leakage. |
| **Comment action** | thollander/actions-comment-pull-request | actions/github-script | github-script requires manual API calls, more verbose, no built-in comment-tag upsert feature. |
| **Auto-commit action** | stefanzweifel/git-auto-commit-action | EndBug/add-and-commit | Both are good. Stefanzweifel has more stars (2026), more active maintenance, better docs. |
| **Runners** | GitHub-hosted (ubuntu-latest) | Self-hosted | Self-hosted runners in public repos are [dangerous](https://docs.github.com/en/actions/reference/security/secure-use): persistent state, shared with fork PRs, credential theft risk. |
| **JSON validator** | evaluate.py (built-in) | Separate GitHub Action | Redundant. evaluate.py already validates JSON. Separate action adds complexity without benefit. |

## Workflow Architecture

### Workflow 1: `score-submission.yml`

**Trigger:** `pull_request` (paths: `submissions/*.json`)
**Permissions:** `contents: read` (read-only)
**Runs on:** GitHub-hosted `ubuntu-latest`

**Steps:**
1. Checkout base repository (NOT PR code) at base ref
2. Setup Python 3.11 with pip cache
3. Install requirements.txt
4. Copy PR submission file to temp location (via GitHub API or actions/checkout with sparse-checkout)
5. Run `python scripts/evaluate.py --score submissions/<file>.json`
6. Capture JSON output (energy, feasible, cardinality)
7. Upload results as workflow artifact (`results.json`)

**Security:** No secrets, no write access, ephemeral runner. If malicious JSON crashes evaluate.py, workflow fails safely.

### Workflow 2: `report-results.yml`

**Trigger:** `workflow_run` (workflows: `["score-submission.yml"]`, types: `[completed]`)
**Permissions:** `contents: write`, `pull-requests: write`
**Runs on:** GitHub-hosted `ubuntu-latest`

**Steps:**
1. Download artifact from Workflow 1
2. Parse results.json
3. Post PR comment with score (using thollander/actions-comment-pull-request)
4. If feasible submission, update README leaderboard:
   - Checkout base repository
   - Run Python script to insert/update leaderboard entry
   - Commit with git-auto-commit-action
5. If score workflow failed, post error comment

**Security:** Runs in base context. Never executes PR code. Has write access but only to trusted base repo code.

### Data Flow

```
User submits PR (submissions/user.json)
  ↓
[Workflow 1: pull_request trigger]
  - Read-only context
  - Run evaluate.py on submission
  - Upload results artifact
  ↓
[Workflow 2: workflow_run trigger]
  - Write context (base repo only)
  - Download results artifact
  - Post PR comment
  - Update README leaderboard
```

**Key security property:** User-controlled data (submission JSON) is only processed in Workflow 1 (read-only). Workflow 2 (write access) only processes artifacts from Workflow 1, never PR code directly.

## Implementation Checklist

**Phase 1: Basic Scoring**
- [ ] Create `.github/workflows/score-submission.yml` (pull_request trigger)
- [ ] Pin actions/setup-python to SHA with v6 comment
- [ ] Run evaluate.py on PR submission files
- [ ] Upload results as artifact
- [ ] Test with sample submission PR

**Phase 2: PR Comments**
- [ ] Create `.github/workflows/report-results.yml` (workflow_run trigger)
- [ ] Download scoring artifact
- [ ] Pin thollander/actions-comment-pull-request to SHA with v3.0.1 comment
- [ ] Post formatted comment with score
- [ ] Test comment updates (push new commit to same PR)

**Phase 3: Leaderboard**
- [ ] Write `scripts/update_leaderboard.py` to parse scores and update README
- [ ] Pin stefanzweifel/git-auto-commit-action to SHA with v7.1.0 comment
- [ ] Commit README changes from Workflow 2
- [ ] Test leaderboard sorting (best score on top)

**Phase 4: Security Hardening**
- [ ] Configure repository: require approval for fork PRs
- [ ] Set up Dependabot for Actions version updates
- [ ] Review GITHUB_TOKEN permissions (least privilege)
- [ ] Add workflow status badge to README

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Workflow_run delay** | Results posted 30-60s after scoring completes | Acceptable for async challenge format. Users see "scoring in progress" state. |
| **Artifact retention** | 90 days default | Irrelevant for this use case. Scoring is real-time. |
| **Concurrent submissions** | Multiple PRs from same user cause leaderboard conflicts | Use git-auto-commit-action with retry logic. Python script should be idempotent. |
| **README edit conflicts** | Multiple PRs scored simultaneously | git-auto-commit-action handles this with automatic rebase/retry. |

## Sources

### Official Documentation (HIGH Confidence)
- [GitHub Actions Security - Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)
- [GitHub Actions - Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub Actions - Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)
- [GitHub Actions - Controlling GITHUB_TOKEN permissions](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token)
- [GitHub Actions - Approving workflow runs from forks](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)

### Security Research & Best Practices (HIGH Confidence)
- [StepSecurity - Pinning GitHub Actions](https://www.stepsecurity.io/blog/pinning-github-actions-for-enhanced-security-a-complete-guide)
- [StepSecurity - Defend CI/CD in Public Repos](https://www.stepsecurity.io/blog/defend-your-github-actions-ci-cd-environment-in-public-repositories)
- [GitGuardian - GitHub Actions Security Cheat Sheet](https://blog.gitguardian.com/github-actions-security-cheat-sheet/)
- [Pull Request vs Pull Request Target (RunsOn)](https://runs-on.com/github-actions/pull-request-vs-pull-request-target/)
- [Why pin actions by commit hash (Rafael Gonzaga)](https://blog.rafaelgss.dev/why-you-should-pin-actions-by-commit-hash)

### Action Documentation (HIGH Confidence)
- [actions/setup-python - GitHub](https://github.com/actions/setup-python)
- [thollander/actions-comment-pull-request - GitHub](https://github.com/thollander/actions-comment-pull-request)
- [stefanzweifel/git-auto-commit-action - GitHub](https://github.com/stefanzweifel/git-auto-commit-action)

### Community Guides (MEDIUM Confidence)
- [Using workflow_run in GitHub Actions (NimblePros)](https://blog.nimblepros.com/blogs/using-workflow-run-in-github-actions/)
- [How to post a comment on a PR (Graphite)](https://graphite.com/guides/how-to-post-comment-on-pr-github-actions)
- [Using GitHub Actions to Build a Self Updating README (Danielle Heberling)](https://danielleheberling.xyz/blog/github-actions/)

### Security Incidents
- March 2025 tj-actions/changed-files compromise: 23,000+ repositories affected by mutable tag attack (mentioned in [StepSecurity pinning guide](https://www.stepsecurity.io/blog/pinning-github-actions-for-enhanced-security-a-complete-guide))

## Version History

| Date | Action | Latest Version | SHA (first 7 chars) | Notes |
|------|--------|---------------|---------------------|-------|
| 2026-02-12 | actions/setup-python | v6.0.0 | f677139 | Upgraded to node24 |
| 2024-11-02 | thollander/actions-comment-pull-request | v3.0.1 | 24bffb9 | Current stable |
| 2026-01-15 | stefanzweifel/git-auto-commit-action | v7.1.0 | 8621497 | Uses node24 runtime |

**Maintenance Note:** Use Dependabot to track updates. Check [actions/setup-python releases](https://github.com/actions/setup-python/releases) monthly for security patches.

## Anti-Patterns to Avoid

### CRITICAL: Never Do This

```yaml
# DANGEROUS - pwn request vulnerability
on:
  pull_request_target:  # Has write access + secrets

jobs:
  score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # Checks out untrusted PR code
      - run: python scripts/evaluate.py  # Executes attacker-controlled code with write access
```

**Why this is catastrophic:** Attacker can modify evaluate.py in their PR to:
- Steal `GITHUB_TOKEN` and push malicious commits to main
- Exfiltrate repository secrets via HTTP requests
- Poison workflow cache to compromise future runs
- Delete branches, create malicious releases

**March 2025 reality check:** This exact pattern enabled the tj-actions compromise that affected 23,000 repos.

### Moderate Anti-Patterns

| Anti-Pattern | Why Bad | Do This Instead |
|-------------|---------|-----------------|
| Pinning to `@v3` or `@latest` | Tags are mutable, can be hijacked | Pin to full SHA: `@24bffb9b452ba05a5f16e8aa61c4c4f6e8f82d16` |
| Self-hosted runners in public repo | Persistent state, shared with forks, credential theft | Use GitHub-hosted runners only |
| `if: always()` on comment step | Posts comments even for malicious PRs that fail validation | `if: success()` or check workflow_run conclusion |
| Manual git commands instead of actions | Error-prone, verbose, manual auth setup | Use git-auto-commit-action |
| Separate JSON validator action | Redundant, adds latency | evaluate.py already validates JSON |

## Future Considerations (Out of Scope for MVP)

| Feature | Value | Complexity | Notes |
|---------|-------|------------|-------|
| **Email notifications** | Low | Medium | GitHub already sends PR comment emails |
| **Submission time tracking** | Medium | Low | Could track first submission timestamp for tiebreaker beyond "submitted first" |
| **Historic leaderboard** | Low | Medium | Archive leaderboard snapshots over time. Useful for multi-day events. |
| **Visualization** | Medium | High | Generate matplotlib chart of score distribution. Would require base64 embedding in comment or uploading to GitHub Pages. |
| **Rate limiting** | Medium | Medium | Prevent spam submissions (e.g., max 1 submission per user per hour). Would need external state (GitHub Issues API or separate DB). |
| **Multi-language support** | N/A | N/A | Python is baked into the challenge. Not applicable. |

**Recommendation:** Defer all enhancements until MVP is deployed and tested with real participants. The workshop is async, so complexity adds risk.
