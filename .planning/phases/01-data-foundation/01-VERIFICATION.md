---
phase: 01-data-foundation
verified: 2026-02-13T12:00:00Z
status: passed
score: 6/6 must-haves verified
must_haves:
  truths:
    - "instance.json exists at repo root with correct schema (20 tickers, K=5, lambda=0.5, penalty_A=10.0, 20-element mu, 20x20 sigma)"
    - "Covariance matrix is symmetric and positive semi-definite"
    - "evaluate.py uses sort_keys=True for deterministic JSON"
    - "SHA256 hash documented in README matches actual instance.json hash"
    - "pytest validation suite (11 tests) all pass"
    - "requirements.txt includes pytest>=7.0 and scipy>=1.11"
  artifacts:
    - path: "instance.json"
      provides: "Frozen QUBO instance data"
    - path: "scripts/evaluate.py"
      provides: "Instance builder and submission scorer"
    - path: "tests/test_instance.py"
      provides: "11-test validation suite"
    - path: "requirements.txt"
      provides: "Python dependency specification"
    - path: "README.md"
      provides: "SHA256 hash documentation and challenge instructions"
    - path: "data/tickers.txt"
      provides: "20 ticker symbols referenced by instance.json"
  key_links:
    - from: "tests/test_instance.py"
      to: "instance.json"
      via: "json.load at REPO_ROOT / instance.json"
    - from: "tests/test_instance.py"
      to: "README.md"
      via: "regex extraction of SHA256 hash"
    - from: "tests/test_instance.py"
      to: "data/tickers.txt"
      via: "tickers_path read in test_tickers_match"
    - from: "scripts/evaluate.py"
      to: "instance.json"
      via: "write_instance_json with sort_keys=True"
---

# Phase 1: Data Foundation Verification Report

**Phase Goal:** Instance data is validated, frozen, and committed so participants can start solving immediately
**Verified:** 2026-02-13T12:00:00Z
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | instance.json exists at repo root with correct schema (20 tickers, K=5, lambda=0.5, penalty_A=10.0, 20-element mu, 20x20 sigma) | VERIFIED | File exists, keys sorted [K, lambda, mu, penalty_A, sigma, tickers], N=20 tickers, mu length=20, sigma 20x20, K=5, lambda=0.5, penalty_A=10.0 |
| 2 | Covariance matrix is symmetric and positive semi-definite | VERIFIED | Symmetry max diff = 0.00e+00, min eigenvalue = 3.48e-05 (> -1e-10), all diagonal entries positive (min = 8.63e-05) |
| 3 | evaluate.py uses sort_keys=True for deterministic JSON | VERIFIED | Line 130: json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False). Round-trip test confirms: reserialized hash matches file hash exactly. |
| 4 | SHA256 hash documented in README matches actual instance.json hash | VERIFIED | README documents a3cbbd1d...c0642dc. LF-normalized file hash matches exactly. |
| 5 | pytest validation suite (11 tests) all pass | VERIFIED | pytest tests/test_instance.py -v -- 11 passed in 0.08s. Tests cover: existence, required fields, dimensions, locked parameters, ticker match, sigma symmetry, sigma PSD, mu range, sigma diagonal, hash integrity, JSON determinism. |
| 6 | requirements.txt includes pytest>=7.0 and scipy>=1.11 | VERIFIED | File contains pytest>=7.0 (line 4) and scipy>=1.11 (line 5), plus numpy>=1.26, pandas>=2.1, requests>=2.31. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| instance.json | Frozen QUBO instance with mu, sigma, parameters | VERIFIED (exists, 457+ lines, sorted keys, wired to tests) | 20 tickers, K=5, lambda=0.5, penalty_A=10.0, 20-element mu, 20x20 sigma |
| scripts/evaluate.py | Instance builder + submission scorer with sort_keys=True | VERIFIED (exists, 187 lines, has sort_keys=True, has exports) | Full implementation: load_stooq_csv, compute_log_returns, build_instance, energy, parse_submission, write_instance_json |
| tests/test_instance.py | 11-test pytest validation suite | VERIFIED (exists, 191 lines, 11 test functions, imports instance.json) | Covers structure, parameters, math properties, integrity |
| requirements.txt | pytest>=7.0 and scipy>=1.11 | VERIFIED (exists, 5 lines, both present) | Also includes numpy, pandas, requests |
| README.md | SHA256 hash section + challenge documentation | VERIFIED (exists, 271 lines, hash present, instructions complete) | Full challenge docs: problem brief, getting started, scoring rules, repo structure |
| data/tickers.txt | 20 ticker symbols | VERIFIED (exists, 20 lines, matches instance.json tickers) | aapl.us through dis.us |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| tests/test_instance.py | instance.json | json.load(INSTANCE_PATH) in fixture | WIRED | Fixture loads instance.json; all 10 data tests use this fixture |
| tests/test_instance.py | README.md | re.search SHA256 hash regex with re.DOTALL | WIRED | test_hash_integrity extracts hash from README and compares to file hash |
| tests/test_instance.py | data/tickers.txt | tickers_path.read_text() in test_tickers_match | WIRED | Reads tickers.txt and asserts match with instance.json tickers |
| scripts/evaluate.py | instance.json | write_instance_json() with json.dump(sort_keys=True) | WIRED | Line 130 writes deterministic JSON; instance.json was generated by this function |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| DATA-01: Instance.json committed to repo with pre-computed mu, Sigma, and parameters (N=20, K=5, lambda=0.5, A=10.0, date range 2023-01-01 to 2025-12-31) | SATISFIED | None |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | No anti-patterns detected in any project source files |

No TODO, FIXME, placeholder, stub, or empty implementation patterns found in any .py, .json, .md, or .txt files within the project source tree.

### Human Verification Required

No items require human verification for this phase. All truths are structurally verifiable:

- Schema correctness: verified programmatically via JSON parsing
- Mathematical properties: verified via numpy eigenvalue computation
- Hash integrity: verified via SHA256 comparison
- Test suite: executed and all 11 pass
- Dependencies: verified via file content inspection

### SUMMARY Cross-Reference

The following SUMMARY claims were independently verified against the actual codebase:

| Claim (from SUMMARYs) | Verified? | Notes |
|------------------------|-----------|-------|
| 751 aligned return observations | N/A | Cannot verify without re-downloading price data; not required for phase goal |
| sort_keys=True in evaluate.py | YES | Confirmed at line 130 |
| SHA256 hash a3cbbd1d... | YES | Matches actual file hash |
| 11 pytest tests all pass | YES | 11 passed in 0.08s |
| Cross-platform LF normalization | YES | Both test_hash_integrity and test_json_deterministic normalize CRLF to LF before hashing |
| Sigma symmetric and PSD | YES | max diff=0.00e+00, min eigenvalue=3.48e-05 |
| SUMMARY 01-01 SHA256 a2418653... | STALE | This was the CRLF hash; replaced by LF-normalized hash a3cbbd1d... in SUMMARY 01-02. Not a concern. |

### Gaps Summary

No gaps found. All 6 observable truths are verified. All 6 required artifacts pass existence, substantive, and wiring checks. All 4 key links are confirmed wired. The single mapped requirement (DATA-01) is satisfied. No anti-patterns detected.

Phase 1 goal -- Instance data is validated, frozen, and committed so participants can start solving immediately -- is fully achieved.

---

_Verified: 2026-02-13T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
