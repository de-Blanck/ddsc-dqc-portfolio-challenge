# Roadmap: DDSC x DQC Quantum Portfolio Challenge

## Overview

This project establishes a zero-friction quantum challenge where participants clone the repo, submit solutions via PR, and see their score on a leaderboard with zero human intervention. The roadmap prioritizes security-first automation, starting with validated data and secure CI architecture, then building scoring automation, participant feedback, and finally the public leaderboard.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Foundation** - Validated instance data committed to repo
- [ ] **Phase 2: Automated Scoring** - Secure CI scores submissions automatically
- [ ] **Phase 3: PR Feedback** - Scores posted as PR comments
- [ ] **Phase 4: Public Leaderboard** - README leaderboard auto-updates

## Phase Details

### Phase 1: Data Foundation
**Goal**: Instance data is validated, frozen, and committed so participants can start solving immediately
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01
**Success Criteria** (what must be TRUE):
  1. instance.json exists in repo root with mu vector, Sigma matrix, and locked parameters (N=20, K=5, lambda=0.5, A=10.0)
  2. Data covers date range 2023-01-01 to 2025-12-31 for 20 US equity tickers
  3. Stooq data has been validated against reference source (no >10% deviations)
  4. SHA256 hash of instance.json is documented in README for integrity verification
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Download price data, fix deterministic JSON, validate, generate frozen instance.json
- [ ] 01-02-PLAN.md — Create pytest validation suite and document SHA256 hash in README

### Phase 2: Automated Scoring
**Goal**: Untrusted PR submissions are scored automatically using secure two-workflow pattern
**Depends on**: Phase 1 (needs instance.json to score against)
**Requirements**: CISC-01, CISC-03
**Success Criteria** (what must be TRUE):
  1. Pull request from fork triggers scoring workflow with read-only permissions
  2. Workflow validates submission JSON schema (key "x", length-20 bitstring)
  3. evaluate.py computes energy, feasibility, and cardinality from submission
  4. Score results uploaded as workflow artifact for downstream consumption
  5. PR template prompts participant for approach type (QAOA/VQE/Classical) and notes
  6. All third-party GitHub Actions pinned to commit SHAs (not mutable tags)
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: PR Feedback
**Goal**: Participants see their scores immediately via PR comments without reading workflow logs
**Depends on**: Phase 2 (needs scoring artifact)
**Requirements**: CISC-02
**Success Criteria** (what must be TRUE):
  1. Second workflow (workflow_run trigger) downloads scoring artifact from Phase 2
  2. PR comment posted automatically showing energy, feasibility status, and cardinality
  3. Comment is sticky (updates on new pushes instead of creating spam)
  4. Failed submissions receive helpful error messages in PR comment
  5. Workflow runs in trusted context (base branch) and never executes PR code
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Public Leaderboard
**Goal**: Top submissions visible in README leaderboard, updated automatically on merge
**Depends on**: Phase 3 (needs scoring + commenting infrastructure)
**Requirements**: LEAD-01, LEAD-02, LEAD-03
**Success Criteria** (what must be TRUE):
  1. Merged PRs trigger leaderboard update workflow
  2. data/leaderboard.json stores full submission log (append-only)
  3. README top 10 table rebuilt from leaderboard.json (sorted by energy, lowest first)
  4. Multiple submissions per participant allowed, only best score shown in leaderboard
  5. Ties broken by submission timestamp (PR creation time)
  6. Concurrency controls prevent race conditions during simultaneous PR merges
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation | 0/2 | Planned | - |
| 2. Automated Scoring | 0/2 | Not started | - |
| 3. PR Feedback | 0/1 | Not started | - |
| 4. Public Leaderboard | 0/2 | Not started | - |
