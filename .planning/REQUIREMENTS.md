# Requirements: DDSC x DQC Quantum Portfolio Challenge

**Defined:** 2026-02-12
**Core Value:** A participant can go from cloning the repo to seeing their score on a leaderboard with zero human intervention.

## v1 Requirements

### Data

- [x] **DATA-01**: Instance.json committed to repo with pre-computed mu, Sigma, and parameters (N=20, K=5, lambda=0.5, A=10.0, date range 2023-01-01 to 2025-12-31)

### CI Scoring

- [ ] **CISC-01**: GitHub Actions scores PR submissions automatically using secure two-workflow pattern (pull_request + workflow_run)
- [ ] **CISC-02**: Score posted as sticky PR comment showing energy, feasibility, and cardinality
- [ ] **CISC-03**: PR template asks participants for approach type (QAOA/VQE/Classical) and notes

### Leaderboard

- [ ] **LEAD-01**: README leaderboard auto-updates when PRs are merged
- [ ] **LEAD-02**: Multiple submissions per participant allowed, only best score shown
- [ ] **LEAD-03**: Leaderboard sorted by energy (lowest first), with tiebreaker on submission timestamp

## v2 Requirements

### Participant Experience

- **PEXP-01**: Actionable error messages when submission JSON is invalid
- **PEXP-02**: Solution diversity metrics (quantum vs classical breakdown)
- **PEXP-03**: Energy trajectory visualization per participant

### Data Quality

- **DATQ-01**: Cross-validate Stooq data against secondary source
- **DATQ-02**: SHA256 hash of instance.json for integrity verification

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web dashboard / custom portal | GitHub-native is sufficient for technical audience |
| User authentication system | GitHub identity via PR author |
| Email notifications | GitHub's native notification system |
| Multiple problem instances | Single instance keeps it focused |
| Manual approval before scoring | Defeats automation purpose |
| Real-time collaborative scoring | Not a live CTF, async is fine |
| Theoretical optimum comparison | Research-grade, post-challenge analysis |
| Workshop content / slides | Lives in separate .docx outside repo |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Done |
| CISC-01 | Phase 2 | Pending |
| CISC-02 | Phase 3 | Pending |
| CISC-03 | Phase 2 | Pending |
| LEAD-01 | Phase 4 | Pending |
| LEAD-02 | Phase 4 | Pending |
| LEAD-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after roadmap creation*
