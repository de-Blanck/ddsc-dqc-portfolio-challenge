# DDSC x DQC Quantum Portfolio Challenge

## What This Is

A production-ready quantum computing challenge for the Danish Data Science Community (DDSC) and Danish Quantum Community (DQC). Participants solve a mean-variance portfolio selection problem formulated as a QUBO, using either quantum methods (QAOA, VQE) or classical heuristics. The repo is the single source of truth — participants clone it, build solutions, submit via GitHub PR, get auto-scored by CI, and see their ranking on a leaderboard in the README.

## Core Value

A participant can go from cloning the repo to seeing their score on a leaderboard with zero human intervention.

## Requirements

### Validated

- ✓ QUBO formulation for mean-variance portfolio selection — existing
- ✓ Evaluation script (evaluate.py) computes energy from submission JSON — existing
- ✓ Data download script (download_stooq.py) fetches Stooq price CSVs — existing
- ✓ Simulated annealing baseline (baseline_sa.py) — existing
- ✓ README with full problem brief, math, and setup instructions — existing
- ✓ 20 US equity tickers defined — existing
- ✓ Example submission JSON format — existing
- ✓ Public GitHub repo at de-Blanck/ddsc-dqc-portfolio-challenge — existing

### Active

- [ ] End-to-end pipeline works (download → instance → baseline → score)
- [ ] GitHub Actions workflow auto-scores PR submissions
- [ ] CI posts score as PR comment
- [ ] Leaderboard in README tracks rankings
- [ ] Leaderboard updates automatically (or semi-automatically) from scored PRs
- [ ] Instance data (instance.json) committed so participants don't need to build it
- [ ] Participant experience validated (clone → solve → submit → score → leaderboard)

### Out of Scope

- Workshop content (slides, QAOA tutorial) — lives in separate .docx outside the repo
- Web-based scoring page — using GitHub Actions instead
- Real quantum hardware access — simulator-only challenge
- Mobile/non-technical participant flow — audience knows git and Python
- Prize management / event logistics — handled by DDSC and DQC separately

## Context

- **Organizations:** DDSC (Danish Data Science Community) and DQC (Danish Quantum Community), both Danish NGOs
- **Audience:** Students, researchers, professionals. Technical — comfortable with git, Python, and command line
- **Event format:** Workshop + challenge at a venue (e.g., CPH Fintech). Workshop covers QAOA theory and hands-on. Challenge is introduced at the event but stays open after — async participation welcome
- **Distribution:** Links from DQC website and DDSC Slack point to the GitHub repo
- **Data source:** Stooq (free, no API key). 20 US equities, 3 years daily data (2023-01-01 to 2025-12-31)
- **Existing code:** Evaluation pipeline, data downloader, SA baseline all written but untested against real data

## Constraints

- **Data source**: Stooq free tier — no API key, but may rate-limit heavy downloads
- **CI costs**: GitHub Actions free tier for public repos — must keep workflow lightweight
- **Submission format**: JSON with key "x" containing length-20 bitstring — locked, participants build to this spec
- **Parameters**: N=20, K=5, lambda=0.5, A=10.0 — locked for the challenge instance

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GitHub Actions for auto-scoring | Always-on, no server costs, fits technical audience | — Pending |
| Leaderboard in README | Simple, visible, no extra infrastructure | — Pending |
| PR-based submissions | Natural git workflow, creates audit trail, CI hooks available | — Pending |
| Stooq for price data | Free, no API key, widely used for prototyping | — Pending |
| Challenge stays open post-event | Allows async participation, broader reach | — Pending |

---
*Last updated: 2026-02-12 after initialization*
