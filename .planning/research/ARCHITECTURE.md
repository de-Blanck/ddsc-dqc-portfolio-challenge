# CI/CD Architecture for GitHub Auto-Scoring Challenge

**Domain:** GitHub-based coding challenge with automated scoring
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

GitHub Actions provides a secure, scalable architecture for auto-scoring PRs from public forks. The critical security boundary is between untrusted fork code and privileged repository operations (commenting, README updates, secrets access). The recommended pattern uses two-workflow isolation: one workflow runs untrusted code with restricted permissions, while a second privileged workflow handles repository writes.

## Recommended Architecture

### Two-Workflow Pattern (workflow_run trigger)

```
┌─────────────────────────────────────────────────────────────┐
│ Participant Flow                                             │
│                                                              │
│ 1. Fork repo                                                 │
│ 2. Add submission JSON to submissions/                       │
│ 3. Open PR to main repo                                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ WORKFLOW 1: Score Submission (pull_request trigger)         │
│ Security Context: UNTRUSTED (fork code, no secrets, no write)│
│                                                              │
│ Steps:                                                       │
│ 1. Checkout PR code (HEAD)                                  │
│ 2. Setup Python                                             │
│ 3. Install dependencies (numpy, pandas)                     │
│ 4. Run evaluate.py --score submissions/<file>.json          │
│ 5. Parse JSON output (energy, feasible, cardinality)        │
│ 6. Upload score as artifact                                 │
│                                                              │
│ Permissions: NONE (read-only repo access)                   │
│ Secrets: NONE                                                │
│ Runs on: ubuntu-latest (GitHub-hosted runner)               │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ (workflow completes)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ WORKFLOW 2: Post Results (workflow_run trigger)             │
│ Security Context: TRUSTED (base branch, has secrets, write OK)│
│                                                              │
│ Triggered: on completion of Workflow 1                      │
│                                                              │
│ Steps:                                                       │
│ 1. Download artifact from triggering workflow               │
│ 2. Extract score data                                       │
│ 3. POST sticky comment to PR with score                     │
│ 4. Update README leaderboard (if new top score)             │
│ 5. Commit + push README if changed                          │
│                                                              │
│ Permissions: write (pull-requests, contents)                │
│ Secrets: GITHUB_TOKEN (auto-provided)                       │
│ Runs on: ubuntu-latest (GitHub-hosted runner)               │
└─────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

**Security isolation:** Untrusted participant code runs in Workflow 1 with zero write permissions and no secrets. Even if a malicious PR attempts code injection, it cannot access GITHUB_TOKEN, cannot post comments, cannot modify README, and cannot exfiltrate secrets.

**Artifact passing:** The only data flow from untrusted to trusted context is the score JSON artifact. Artifacts are immutable and stored by GitHub — attackers cannot inject malicious code via artifact contents (though sanitization is still recommended).

**Explicit trust boundary:** Workflow 2 runs from the base branch's workflow definition, not the PR's. Attackers cannot redefine Workflow 2 logic from a fork PR.

## Component Boundaries

| Component | Responsibility | Communicates With | Trust Level |
|-----------|---------------|-------------------|-------------|
| **Workflow 1: score.yml** | Execute scoring script on PR submission | evaluate.py, GitHub Artifacts API | UNTRUSTED |
| **Workflow 2: post-results.yml** | Comment on PR, update leaderboard | GitHub REST API (issues, contents), Workflow 1 artifacts | TRUSTED |
| **evaluate.py** | Load submission JSON, compute QUBO energy, return score | instance.json (data/), submission JSON (submissions/) | UNTRUSTED CODE EXECUTES THIS |
| **Sticky Comment Action** | Create or update single PR comment | GitHub Issues API via GITHUB_TOKEN | TRUSTED |
| **README Updater** | Parse scores, rebuild leaderboard section, commit | README.md, git, GitHub Contents API | TRUSTED |
| **GitHub Artifacts** | Store score JSON between workflows | Workflow 1 (upload), Workflow 2 (download) | TRUSTED STORAGE |

### Security Boundaries

```
┌──────────────────────────────────────────────────────────────┐
│ UNTRUSTED ZONE (fork PR code)                                │
│                                                              │
│ - Participant submission JSON                                │
│ - Any code changes participant makes to evaluate.py         │
│ - Dependencies listed in requirements.txt                   │
│                                                              │
│ Mitigation:                                                  │
│ - Workflow 1 uses pull_request trigger (no write, no secrets)│
│ - checkout uses PR HEAD (not base)                          │
│ - No self-hosted runners (only GitHub-hosted ephemeral VMs)  │
│ - evaluate.py should validate submission schema before exec  │
└──────────────────────────────────────────────────────────────┘
                           │
                   Artifact Upload (score.json)
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ TRUSTED ZONE (base repo, workflow_run context)               │
│                                                              │
│ - GITHUB_TOKEN secret                                        │
│ - Write permission to pull-requests                          │
│ - Write permission to contents (for README commit)           │
│                                                              │
│ Mitigation:                                                  │
│ - Workflow 2 uses workflow_run trigger                       │
│ - Workflow 2 definition comes from base branch               │
│ - Sanitize artifact data before using in API calls           │
│ - Least-privilege token scopes                               │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. PR Opened (Scoring Phase)

```
Participant opens PR
    ↓
pull_request event fires
    ↓
score.yml triggered (runs on fork HEAD)
    ↓
Actions checkout PR code
    ↓
evaluate.py --score submissions/<username>.json
    ↓
Output: {"energy": -0.00123, "feasible": true, "cardinality": 5, "K": 5}
    ↓
Upload artifact: score.json
    ↓
Workflow 1 completes
```

### 2. Artifact Published (Privileged Phase)

```
Workflow 1 completion
    ↓
workflow_run event fires
    ↓
post-results.yml triggered (runs on base branch context)
    ↓
Download artifact from completed workflow
    ↓
Parse score.json
    ↓
┌─────────────────────────────────────────┐
│ Parallel Operations:                    │
│ A. POST sticky comment                  │
│ B. Update README leaderboard (if needed)│
└─────────────────────────────────────────┘
    ↓
Comment posted: "Your score: -0.00123 (feasible)"
    ↓
If top 10 score:
  - Update README <!-- LEADERBOARD --> section
  - git commit -m "Update leaderboard: +<username>"
  - git push
```

### 3. README Leaderboard Update Mechanism

```markdown
<!-- README.md structure -->

## Leaderboard

<!-- LEADERBOARD:START -->
| Rank | User | Score | Feasible | Submitted |
|------|------|-------|----------|-----------|
| 1 | @alice | -0.00456 | ✓ | 2026-02-10 |
| 2 | @bob | -0.00234 | ✓ | 2026-02-09 |
| ... | ... | ... | ... | ... |
<!-- LEADERBOARD:END -->
```

**Update script logic:**

1. Read current README.md
2. Download existing leaderboard data (from artifact or JSON file in repo)
3. Add new score to dataset
4. Sort by energy (ascending), then by timestamp (earliest first)
5. Take top 10
6. Regenerate markdown table
7. Replace text between `<!-- LEADERBOARD:START -->` and `<!-- LEADERBOARD:END -->`
8. If changed, commit + push

**Leaderboard persistence options:**

| Option | Pros | Cons |
|--------|------|------|
| Store in README only | Simple, single source of truth | Parsing markdown is brittle |
| Store JSON in repo (data/leaderboard.json) | Easy parsing, append-only audit log | Extra file to maintain |
| Store as artifact | No repo clutter | Artifacts expire after 90 days |

**Recommendation:** Store `data/leaderboard.json` with full submission log, update README from it. This allows historical analysis and is append-only (safe for concurrent PRs).

## Patterns to Follow

### Pattern 1: Two-Workflow Isolation

**What:** Separate untrusted code execution from privileged operations using workflow_run trigger.

**When:** Any public repo that accepts PRs from forks and needs to write back to the repo (comments, labels, file updates).

**Why:** The pull_request_target trigger is dangerous — combining it with checkout of PR code has led to widespread secret exfiltration vulnerabilities. workflow_run provides safer isolation.

**Example:**

```yaml
# .github/workflows/score.yml (Workflow 1 - UNTRUSTED)
name: Score Submission
on:
  pull_request:
    paths:
      - 'submissions/**'

permissions:
  contents: read  # Explicit read-only

jobs:
  score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # PR code

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install -r requirements.txt

      - name: Score submission
        id: score
        run: |
          # Find new submission file
          SUBMISSION=$(git diff --name-only origin/${{ github.base_ref }}...HEAD | grep '^submissions/.*\.json$' | head -n1)
          if [ -z "$SUBMISSION" ]; then
            echo "No submission found"
            exit 1
          fi

          python scripts/evaluate.py --score "$SUBMISSION" > score.json
          cat score.json

      - uses: actions/upload-artifact@v4
        with:
          name: score
          path: score.json
```

```yaml
# .github/workflows/post-results.yml (Workflow 2 - TRUSTED)
name: Post Results
on:
  workflow_run:
    workflows: ["Score Submission"]
    types: [completed]

permissions:
  pull-requests: write
  contents: write

jobs:
  post:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    steps:
      - uses: actions/checkout@v4

      - uses: dawidd6/action-download-artifact@v3
        with:
          workflow: score.yml
          run_id: ${{ github.event.workflow_run.id }}
          name: score

      - name: Post comment
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          number: ${{ github.event.workflow_run.pull_requests[0].number }}
          header: score
          path: score.json
```

### Pattern 2: Sticky Comment for Results

**What:** Update a single comment on each PR run instead of posting duplicates.

**When:** Workflows that run multiple times per PR (on each push).

**Why:** Keeps PR conversation clean. Participants see updated score, not spam.

**Example:**

```yaml
- name: Format score comment
  run: |
    SCORE=$(jq -r '.energy' score.json)
    FEASIBLE=$(jq -r '.feasible' score.json)
    CARDINALITY=$(jq -r '.cardinality' score.json)

    cat > comment.md <<EOF
    ## Submission Score

    | Metric | Value |
    |--------|-------|
    | Energy | $SCORE |
    | Feasible | $FEASIBLE |
    | Cardinality | $CARDINALITY / 5 |

    $(if [ "$FEASIBLE" = "true" ]; then echo "✅ Valid submission"; else echo "❌ Invalid (must select exactly 5 assets)"; fi)
    EOF

- uses: marocchino/sticky-pull-request-comment@v2
  with:
    header: score
    path: comment.md
```

### Pattern 3: Conditional README Update

**What:** Only update leaderboard if new submission is in top 10.

**When:** High-volume repos where most submissions don't change rankings.

**Why:** Reduces commit noise, avoids unnecessary git operations.

**Example:**

```python
import json

# Load current leaderboard
with open('data/leaderboard.json') as f:
    leaderboard = json.load(f)

# Load new score
with open('score.json') as f:
    new_score = json.load(f)

# Add metadata
new_entry = {
    'user': os.environ['GITHUB_ACTOR'],
    'pr': os.environ['PR_NUMBER'],
    'energy': new_score['energy'],
    'feasible': new_score['feasible'],
    'timestamp': os.environ['GITHUB_EVENT_TIME']
}

# Append and sort
leaderboard.append(new_entry)
leaderboard.sort(key=lambda x: (x['energy'], x['timestamp']))

# Take top 10
top10 = leaderboard[:10]

# Check if new entry is in top 10
if new_entry in top10:
    # Update README
    update_readme(top10)
    # Write leaderboard.json
    with open('data/leaderboard.json', 'w') as f:
        json.dump(leaderboard, f, indent=2)
    # Commit
    subprocess.run(['git', 'add', 'README.md', 'data/leaderboard.json'])
    subprocess.run(['git', 'commit', '-m', f'Update leaderboard: +{new_entry["user"]}'])
    subprocess.run(['git', 'push'])
else:
    print('Not in top 10, skipping README update')
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: pull_request_target + checkout PR

**What:** Using pull_request_target trigger and checking out PR code in the same workflow.

**Why bad:** This is the "pwn request" vulnerability. pull_request_target runs with write permissions and secrets. If you then checkout untrusted PR code and execute it (even indirectly via pip install or actions), attackers can exfiltrate secrets or inject malicious code into your repo.

**Instead:** Use workflow_run pattern to separate untrusted execution from privileged operations.

**Real-world impact:** GitHub Security Lab documented numerous cases of secret exfiltration and repository compromise from this pattern.

### Anti-Pattern 2: Using Self-Hosted Runners for Public Repos

**What:** Running workflows on self-hosted infrastructure.

**Why bad:** Anyone can open a PR to a public repo. Self-hosted runners persist between jobs — attackers can install malware, steal credentials from the host, or pivot to internal networks.

**Instead:** Use GitHub-hosted runners exclusively for public repos. They are ephemeral VMs that are destroyed after each job.

**Real-world impact:** Multiple incidents of crypto miners, reverse shells, and credential theft via malicious PRs targeting self-hosted runners.

### Anti-Pattern 3: Trusting Artifact Contents Without Sanitization

**What:** Downloading artifact from untrusted workflow and using its contents directly in shell commands or API calls.

**Why bad:** While artifacts themselves are stored securely, the data inside was produced by untrusted code. Script injection can occur if you interpolate artifact data into bash or API calls without escaping.

**Instead:** Validate and sanitize artifact data. Use parameterized APIs, not string interpolation.

**Example of vulnerability:**

```yaml
# VULNERABLE
- run: |
    SCORE=$(cat score.json)
    gh pr comment $PR --body "$SCORE"  # If SCORE contains $(malicious), it executes
```

**Safe version:**

```yaml
# SAFE
- uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const score = JSON.parse(fs.readFileSync('score.json', 'utf8'));
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: `Energy: ${score.energy}`  // Parameterized, no injection
      });
```

### Anti-Pattern 4: Committing Every Submission to Leaderboard

**What:** Updating README on every PR, even if score doesn't change top 10.

**Why bad:** Creates excessive git history noise. 100 submissions = 100 commits, most irrelevant.

**Instead:** Only commit README when top 10 changes. Store full submission log in data/leaderboard.json (which you can update atomically or not at all).

### Anti-Pattern 5: Using GITHUB_TOKEN for Cross-Repo Operations

**What:** Attempting to use the auto-provided GITHUB_TOKEN to push to other repos or create PRs in other repos.

**Why bad:** GITHUB_TOKEN is scoped to the current repository only. It cannot authenticate to other repos, even within the same organization.

**Instead:** For cross-repo operations, create a Personal Access Token (PAT) or GitHub App and store it as a secret. For this challenge (single-repo), GITHUB_TOKEN is sufficient.

## Scalability Considerations

| Concern | At 10 submissions | At 100 submissions | At 1000 submissions |
|---------|-------------------|-------------------|-------------------|
| **Workflow concurrency** | No issue | May queue if many PRs open simultaneously | Use concurrency limits + queue |
| **README merge conflicts** | Unlikely | Possible if 2 PRs score identically | Use leaderboard.json, rebuild README from single source |
| **Artifact storage** | ~10KB total | ~100KB total | ~1MB total (artifacts expire after 90 days) |
| **Git history size** | Negligible | 100 commits if all update README | Only commit top 10 changes |
| **API rate limits** | No concern | No concern (GITHUB_TOKEN has 1000 req/hr for authenticated) | Batch operations, cache reads |

### Recommended Limits

```yaml
# score.yml
concurrency:
  group: score-${{ github.event.pull_request.number }}
  cancel-in-progress: true  # Cancel old runs if new commits pushed

# post-results.yml
concurrency:
  group: post-results
  cancel-in-progress: false  # Don't cancel — ensure all scores posted
```

### Handling Concurrent PRs

If two PRs score simultaneously and both are top 10, they could create a git conflict on README.md. Mitigations:

1. **Atomic leaderboard.json updates:** Each workflow appends to leaderboard.json, then rebuilds README from scratch. No merge conflicts because README is generated, not edited.

2. **Pull before push:** Always `git pull --rebase` before pushing README changes to catch concurrent updates.

3. **Retry on conflict:** If push fails, re-run leaderboard update and retry push.

```yaml
- name: Commit and push leaderboard
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add README.md data/leaderboard.json
    git commit -m "Update leaderboard: +${{ github.actor }}" || exit 0

    # Retry push up to 3 times on conflict
    for i in {1..3}; do
      git pull --rebase && git push && break
      sleep 2
    done
```

## Build Order Dependencies

### Phase 1: Scoring Workflow (Workflow 1)
**Depends on:** None
**Builds:** Untrusted code execution, artifact upload
**Must exist before:** Workflow 2

### Phase 2: Comment Posting (Workflow 2, Part A)
**Depends on:** Workflow 1 artifacts
**Builds:** PR feedback loop
**Must exist before:** Leaderboard updates (so participants see scores immediately)

### Phase 3: README Leaderboard (Workflow 2, Part B)
**Depends on:** Workflow 1 artifacts, Workflow 2 comment logic
**Builds:** Public scoreboard
**Must exist before:** Nothing (this is the final feature)

### Optional Phase 4: Leaderboard Data Storage
**Depends on:** README updates working
**Builds:** Historical tracking, analytics
**Must exist before:** Nothing (this is an enhancement)

## Technology Decisions

| Component | Technology | Why |
|-----------|-----------|-----|
| **Workflow trigger (untrusted)** | pull_request | Standard, safe, no write permissions |
| **Workflow trigger (trusted)** | workflow_run | Secure isolation from fork PRs |
| **Artifact storage** | actions/upload-artifact@v4 | Built-in, reliable, 90-day retention |
| **Artifact download** | dawidd6/action-download-artifact@v3 | Supports workflow_run cross-workflow downloads |
| **Comment action** | marocchino/sticky-pull-request-comment@v2 | Most popular, header-based identification, update-in-place |
| **Git operations** | Native git CLI | Simple, no extra dependencies |
| **README update** | Custom Python script | Full control, easy to test locally |

## Sources

**HIGH CONFIDENCE (Official Documentation & Security Labs):**
- [Secure use reference - GitHub Docs](https://docs.github.com/en/actions/reference/security/secure-use)
- [Keeping your GitHub Actions and workflows secure Part 1: Preventing pwn requests | GitHub Security Lab](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)
- [Use autograding - GitHub Docs](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/use-autograding)
- [Store and share data with workflow artifacts - GitHub Docs](https://docs.github.com/en/actions/tutorials/store-and-share-data)

**MEDIUM CONFIDENCE (Verified Community Patterns):**
- [GitHub Actions Security Best Practices Cheat Sheet](https://blog.gitguardian.com/github-actions-security-cheat-sheet/)
- [Pull Request vs Pull Request Target trigger - RunsOn](https://runs-on.com/github-actions/pull-request-vs-pull-request-target/)
- [Accessing secrets from forks safely with GitHub Actions | michaelheap.com](https://michaelheap.com/access-secrets-from-forks/)
- [Cross-Workflow Artifact Passing in GitHub Actions | Medium](https://medium.com/@michamarszaek/cross-workflow-artifact-passing-in-github-actions-7f20acbb1b70)
- [Sticky Pull Request Comment · Actions · GitHub Marketplace](https://github.com/marketplace/actions/sticky-pull-request-comment)
- [Automate Pull Request Comments with GitHub Actions | BEN ABT](https://benjamin-abt.com/blog/2026/01/04/github-action-add-or-update-custom-comment/)
