# Plan 01-02 Summary

**Status:** completed
**Duration:** 4 minutes

## What was done
- Created pytest validation suite with 11 tests covering instance.json structure, locked parameters, mathematical properties (symmetry, positive semi-definiteness, reasonable ranges), ticker consistency, SHA256 hash integrity, and JSON determinism
- Updated requirements.txt with pytest>=7.0 and scipy>=1.11
- Documented LF-normalized SHA256 hash (`a3cbbd1d9e0125813e1026b39078ed8cc62ffb504238a476673cd7a58c0642dc`) in README.md Instance Data section
- Marked Getting Started steps 2 and 3 as optional since instance.json is pre-committed
- Updated Repo Structure in README to reflect instance.json at root and new tests/ directory

## Artifacts produced
- `tests/test_instance.py` -- 11 pytest tests validating instance.json integrity
- `requirements.txt` -- added pytest>=7.0 and scipy>=1.11
- `README.md` -- added Instance Data section with SHA256 hash, updated Getting Started and Repo Structure

## Verification
- All 11 tests pass: `pytest tests/test_instance.py -v` (11 passed in 0.10s)
- SHA256 hash verified cross-platform: LF-normalized hash matches on Windows (CRLF checkout) and Linux/macOS (LF checkout)
- Hash integrity test confirms README hash matches instance.json file hash
- JSON deterministic test confirms round-trip through json.dumps(sort_keys=True) produces identical content

## Commits
- `11e000a` test(01-02): add pytest validation suite for instance.json
- `a82befa` docs(01-02): document SHA256 hash in README and fix hash regex

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Cross-platform line-ending normalization**
- **Found during:** Task 1 (test_json_deterministic failure)
- **Issue:** instance.json has CRLF line endings on Windows checkout, but json.dumps produces LF. SHA256 hashes differ across platforms.
- **Fix:** Both hash tests (test_hash_integrity and test_json_deterministic) normalize file bytes to LF before hashing. README documents the LF-normalized hash with a Python cross-platform verification command.
- **Files modified:** tests/test_instance.py
- **Impact:** Tests now pass identically on Windows and Linux/macOS

**2. [Rule 1 - Bug] Hash regex required re.DOTALL flag**
- **Found during:** Task 2 (test_hash_integrity failure)
- **Issue:** The regex `[Ss][Hh][Aa]256.*?([a-f0-9]{64})` did not match because the SHA256 label and the actual hash value are on different lines in the README.
- **Fix:** Added `re.DOTALL` flag to allow `.` to match newlines
- **Files modified:** tests/test_instance.py
- **Commit:** a82befa

**3. [Rule 2 - Missing Critical] SHA256 hash corrected to LF-normalized value**
- **Found during:** Task 2
- **Issue:** Plan specified SHA256 `a2418653...` which was computed from CRLF file bytes (Windows-specific). This hash would fail on Linux/macOS where git checks out with LF.
- **Fix:** Used LF-normalized hash `a3cbbd1d...` instead, matching git's internal storage. Added Python cross-platform verification command to README.
- **Files modified:** README.md

## Notes
- The plan specified SHA256 hash `a2418653e39fbad30bba7d1f046bad84ea7a1acbb4ed2b6af9473289f0a7f689` but this was the Windows CRLF hash. The correct cross-platform (LF-normalized) hash is `a3cbbd1d9e0125813e1026b39078ed8cc62ffb504238a476673cd7a58c0642dc`. All tests and README use the LF-normalized hash.
- Updated Repo Structure in README (not in original plan) to accurately reflect instance.json location at root instead of data/ and to include the new tests/ directory.
