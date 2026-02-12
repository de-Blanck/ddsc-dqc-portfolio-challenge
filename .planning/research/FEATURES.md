# Feature Landscape

**Domain:** GitHub-based coding challenge platform (quantum optimization)
**Researched:** 2026-02-12
**Confidence:** MEDIUM (based on ecosystem survey + domain knowledge)

## Table Stakes

Features participants expect. Missing = challenge feels incomplete or unprofessional.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **PR-based submission validation** | Standard GitHub workflow — participants expect automated checks on PR creation | Medium | GitHub Actions runs on PR open/update. Requires workflow file + JSON schema validation. Sources: [GitHub PR validation](https://graphite.com/guides/how-to-automate-testing-in-pull-request) |
| **Immediate automated scoring** | Participants expect instant feedback, not manual review delays | Medium | GitHub Actions posts score as PR comment within seconds of submission. Critical for technical audience expectations. |
| **Public leaderboard** | Core to competition psychology — participants want to see ranking | Low | README-based table or JSON file. Updates after merge or via bot comment aggregation. |
| **Clear submission format documentation** | Ambiguous formats = frustration and invalid submissions | Low | Already exists in README — JSON schema with example. Schema validation in CI prevents common mistakes. |
| **Baseline solution to beat** | Gives participants a concrete target and verifies pipeline works | Low | Already exists (simulated annealing). Provides energy score benchmark. |
| **Submission history / audit trail** | Participants expect to see past attempts and improvements | Low | Git history provides this naturally — merged PRs are the record. |
| **Validation error messages** | When submission fails, participant needs to know why | Low | CI must output actionable errors: "Invalid JSON", "Wrong array length", "Missing key 'x'". |
| **Time-based tiebreaker** | When scores tie, needs objective resolution | Low | PR merge timestamp or commit timestamp. Document this clearly in rules. |

## Differentiators

Features that set this challenge apart. Not expected, but add significant value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Live leaderboard updates during event** | Creates energy/excitement at in-person workshop | Medium | GitHub Actions updates README on every scored PR. Auto-commit from bot account. Participants see updates in real-time if watching repo. |
| **Solution diversity metrics** | Shows ecosystem breadth (quantum vs classical approaches) | Low | Tag PRs or submissions as "QAOA", "VQE", "Classical-SA", "Classical-IP". Leaderboard shows approach distribution. |
| **Energy trajectory visualization** | Participants see if they're improving across attempts | Medium | Store submission history per participant. Graph energy vs attempt number. Could be static chart generator or external dashboard. |
| **Automated feasibility warnings** | Flag infeasible solutions without disqualifying them | Low | CI detects `sum(x) != K`, posts warning: "Infeasible — constraint penalty applied". Helps participants debug. |
| **Best submission per participant** | Multiple PRs allowed, only best score counts | Medium | Leaderboard logic: group by participant, select min energy. Encourages experimentation. |
| **PR template with approach description** | Participants document what method they used | Low | `.github/PULL_REQUEST_TEMPLATE.md` asks: "Approach (QAOA/VQE/Classical):", "Key parameters:", "Insights:". Creates knowledge sharing. |
| **Comparison to theoretical optimum** | Shows gap between achieved score and known lower bound | High | Requires solving to optimality (branch-and-bound or IP solver). Could run offline and display gap % in leaderboard. Adds research depth. |

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Complex web dashboard** | Over-engineering for a time-boxed challenge. High maintenance burden. | Use README leaderboard + GitHub's native PR interface. Participants are technical — CLI/GitHub UI is natural. |
| **Real-time collaborative scoring** | Unnecessary complexity. This isn't a live CTF. | Async submissions via PR. Post-event submissions welcome. No need for WebSocket infrastructure. |
| **User authentication system** | GitHub already provides identity. Don't recreate it. | Use GitHub username from PR author. Free, reliable, no password management. |
| **Submission size limits beyond JSON** | Adds validation complexity. Format is already constrained. | JSON schema validation is sufficient. No need to check file size — a 20-element array is tiny. |
| **Email notifications** | GitHub already does this via PR mentions and Actions results. | Use GitHub's native notification system. No external email service needed. |
| **Custom submission portal** | Participants expect GitHub workflow. Portal breaks that flow. | PR submission is the portal. Fits technical audience perfectly. |
| **Participant-visible test cases** | This is optimization, not algorithm validation. Full data must be public for reproducibility. | Instance.json is public. Energy function is deterministic. No hidden test cases. |
| **Multiple problem instances** | Adds comparison complexity. Single instance keeps it focused. | One canonical instance for the entire challenge. Simplifies leaderboard logic. |
| **Manual approval before scoring** | Defeats purpose of automation. Creates bottleneck. | Auto-score all PRs immediately. Spam/abuse unlikely in technical community challenge. |

## Feature Dependencies

```
Submission Validation (JSON schema check)
  └─> Automated Scoring (calculate energy)
      └─> PR Comment with Score
          └─> Leaderboard Update
              └─> README Auto-Commit (or manual update)

Baseline Solution
  └─> Energy Benchmark (participants know target to beat)

PR Template
  └─> Approach Metadata (tags for solution diversity)
```

**Critical path:** Validation → Scoring → Comment. Without this, challenge is not self-service.

**Optional path:** Scoring → Leaderboard automation. Could be semi-automated (manual README edit from CI logs) if full automation proves complex.

## MVP Recommendation

For a functional challenge (prioritize for phases 1-2):

1. **PR-based JSON validation** — Gate 1: Is submission structurally valid?
2. **Automated energy scoring** — Gate 2: What's the score?
3. **PR comment with results** — Gate 3: Participant sees their score immediately
4. **Manual leaderboard update** — Organizer updates README from CI logs after event or daily
5. **Clear error messages** — When validation fails, output is actionable

Defer to post-MVP or "nice to have":

- **Automated leaderboard updates** — Medium complexity, high maintenance. Can launch without it.
- **Energy trajectory visualization** — Cool but non-essential. Participants can track own attempts in git history.
- **Solution diversity metrics** — Interesting for post-event analysis, not critical for participant flow.
- **Theoretical optimum comparison** — Research-grade feature. Run after challenge to publish results.

## Implementation Notes

### Submission Flow (Table Stakes)

```
1. Participant forks repo
2. Writes solver (QAOA, classical, etc.)
3. Generates submission JSON: {"x": [0,1,0,...]}
4. Commits to branch, opens PR to main repo
5. GitHub Actions triggers on PR open/update
   a. Validate JSON schema
   b. Load instance.json
   c. Run evaluate.py --score submission.json
   d. Post result as PR comment
6. Participant sees score in seconds
7. Organizer merges valid PRs (or auto-merge with bot)
8. Leaderboard reflects best scores
```

### Leaderboard Update Strategy (Differentiator)

**Option A: Fully automated (Medium complexity)**
- GitHub Actions writes leaderboard table to README on every merge
- Requires bot account with repo write access
- Workflow: Fetch all merged PRs → Parse scores from PR comments → Sort → Render markdown table → Commit to README

**Option B: Semi-automated (Low complexity)**
- GitHub Actions logs scores to JSON artifact
- Organizer runs script to generate leaderboard: `python scripts/update_leaderboard.py`
- Simpler, less magic, acceptable for time-boxed challenge

**Recommendation for MVP:** Start with Option B. Upgrade to Option A if challenge runs long-term.

### Validation Robustness (Table Stakes)

Common submission errors to catch:

- Missing "x" key → Error: "Submission must contain key 'x'"
- Wrong array length → Error: "Array 'x' must have length 20, got {len}"
- Non-binary values → Error: "Array 'x' must contain only 0 or 1, found {val}"
- Invalid JSON syntax → Error: "Failed to parse JSON: {exception}"
- File not found at expected path → Error: "No submission JSON found at {path}"

Error messages must be clear and immediate (GitHub Actions output + PR comment).

## Participant Experience Expectations

Based on research into [coding challenge onboarding](https://geeksforgeeks.org/coding-contest-experience) and [PR-based workflows](https://rewind.com/blog/best-practices-for-reviewing-pull-requests-in-github/):

**What participants expect:**
- Clone repo, run scripts locally to verify solution before submitting (scripts/evaluate.py supports this)
- Submit via familiar git workflow (fork/PR, not custom portal)
- See results within seconds (not hours)
- Multiple attempts allowed without penalty (except for tiebreaker)
- Clear rules about scoring, feasibility, and ranking

**What frustrates participants:**
- Ambiguous submission format → Prevented by JSON schema validation + example
- Delayed feedback → Prevented by GitHub Actions auto-scoring
- Unclear ranking → Prevented by public leaderboard
- Black-box evaluation → Prevented by public instance.json + deterministic energy function

## Sources

- [How to automate testing in a pull request](https://graphite.com/guides/how-to-automate-testing-in-pull-request) — PR-based validation best practices
- [Validating Pull Requests on GitHub](https://hubverse-org.github.io/hubValidations/articles/validate-pr.html) — GitHub Actions validation patterns
- [Essential Pull Request Checklist](https://www.pullchecklist.com/posts/pull-request-checklist-github) — PR workflow expectations
- [Coding Contest Experience](https://geeksforgeeks.org/coding-contest-experience) — Participant onboarding and expectations
- [Coding Competitions Overview](https://fastercapital.com/content/Community-challenges-or-contests--Coding-Competitions--Code-to-Success--The-Thrill-of-Coding-Competitions.html) — Community dynamics
- [Automated Assessment in Mobile Programming Courses](https://arxiv.org/html/2504.04230v1) — GitHub Classroom + Actions for automated evaluation
- [Codabench Platform](https://www.codabench.org/) — Modern benchmark platform (automated scoring, leaderboards, code submission)
- [Competitive Programming (Wikipedia)](https://en.wikipedia.org/wiki/Competitive_programming) — Contest structure and judging systems
