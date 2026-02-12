# Phase 1: Data Foundation - Research

**Researched:** 2026-02-12
**Domain:** Financial data validation and integrity verification (Python)
**Confidence:** HIGH

## Summary

Phase 1 focuses on creating a validated, frozen instance.json file containing pre-computed mu (mean returns) and Sigma (covariance matrix) from historical stock price data. The data must be validated against quality issues, frozen for reproducibility, and committed with a SHA256 hash for integrity verification.

The standard approach combines pandas for data processing, hashlib for integrity verification, and pytest for validation tests. Financial time series data requires careful handling of missing values, outlier detection, and validation that the covariance matrix is positive semi-definite. The key challenge is detecting and addressing Stooq data quality issues (missing adjusted close, potential deviations up to 11%) before freezing the data.

JSON serialization must be deterministic (sorted keys) to ensure consistent hash values. The existing evaluate.py script provides the foundation for instance generation, but needs augmentation with comprehensive validation checks and integrity verification.

**Primary recommendation:** Build validation layer on top of existing evaluate.py, implement pytest-based quality checks, and add SHA256 hash computation with canonical JSON serialization.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | >=1.26 | Array operations, linear algebra | Industry standard for numerical computing, already in repo |
| pandas | >=2.1 | Time series handling, data alignment | Best-in-class for financial data with built-in missing data handling |
| hashlib | stdlib (3.11+) | SHA256 hash computation | Python standard library, optimized file_digest() in 3.11+ |
| json | stdlib | JSON serialization | Standard library, supports sort_keys for deterministic output |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=7.0 | Data validation testing | Already standard in Python ecosystem, gold standard for testing |
| requests | >=2.31 | HTTP downloads | Already in repo for Stooq downloads |
| scipy | >=1.11 | Eigenvalue checks for matrix validation | Cholesky decomposition for positive semi-definite validation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| json stdlib | orjson | orjson is 3x faster but adds dependency; stdlib sufficient for one-time instance generation |
| pytest | unittest | unittest is stdlib but pytest has better fixtures and parametrization for data validation |
| jsonschema | manual validation | jsonschema adds dependency but provides clearer schema documentation; manual validation acceptable for fixed schema |

**Installation:**
```bash
pip install pytest>=7.0 scipy>=1.11
# numpy, pandas, requests already in requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
├── download_stooq.py      # Existing: downloads price CSVs
├── evaluate.py            # Existing: builds instance, scores submissions
├── validate_instance.py   # New: validation checks before freezing
└── baseline_sa.py         # Existing: simulated annealing baseline

tests/
├── test_data_quality.py   # Data validation tests
└── test_instance.py       # Instance.json integrity tests

data/
├── tickers.txt            # Existing: 20 tickers
├── prices/                # Downloaded CSVs
└── instance.json          # Frozen instance with mu, Sigma

README.md                  # Updated with SHA256 hash
```

### Pattern 1: Separation of Download, Validation, and Freezing
**What:** Three-stage pipeline: download → validate → freeze
**When to use:** Always for reproducible data pipelines
**Example:**
```python
# Stage 1: Download (existing download_stooq.py)
# Stage 2: Validate (new validate_instance.py)
def validate_data_quality(price_dir, tickers, start_date, end_date):
    """Run all quality checks before building instance"""
    check_missing_data()
    check_outliers()
    check_date_coverage()
    check_covariance_matrix()

# Stage 3: Freeze (augmented evaluate.py)
def freeze_instance(instance, output_path):
    """Write instance with deterministic JSON and compute hash"""
    write_canonical_json(instance, output_path)
    hash_value = compute_sha256(output_path)
    return hash_value
```

### Pattern 2: Canonical JSON Serialization
**What:** Deterministic JSON output with sorted keys for consistent hashing
**When to use:** Always when computing cryptographic hashes of JSON files
**Example:**
```python
# Source: Python json stdlib documentation
import json

def write_canonical_json(data, path):
    """Write JSON with sorted keys for deterministic output"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f,
                  indent=2,           # Human-readable
                  sort_keys=True,     # Deterministic ordering
                  ensure_ascii=False) # Preserve unicode
```

### Pattern 3: File-Based SHA256 Hashing
**What:** Efficient hash computation using hashlib.file_digest() (Python 3.11+)
**When to use:** Computing checksums for integrity verification
**Example:**
```python
# Source: https://docs.python.org/3/library/hashlib.html
import hashlib

def compute_sha256(file_path):
    """Compute SHA256 hash of file efficiently"""
    with open(file_path, 'rb') as f:
        digest = hashlib.file_digest(f, 'sha256')
    return digest.hexdigest()

# For Python <3.11, use chunked reading:
def compute_sha256_legacy(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### Pattern 4: Pytest Fixtures for Data Validation
**What:** Use pytest fixtures to load data once and run multiple validation tests
**When to use:** Testing data quality across multiple dimensions
**Example:**
```python
# Source: pytest documentation patterns
import pytest
import pandas as pd

@pytest.fixture(scope='module')
def price_data(price_dir, tickers):
    """Load all price data once for validation tests"""
    return {t: load_stooq_csv(f"{price_dir}/{t}.csv")
            for t in tickers}

def test_date_coverage(price_data):
    """Verify all tickers cover required date range"""
    for ticker, df in price_data.items():
        assert df.index.min() <= pd.Timestamp('2023-01-01')
        assert df.index.max() >= pd.Timestamp('2025-12-31')

def test_no_extreme_outliers(price_data):
    """Check for data quality issues (>10% deviations)"""
    for ticker, df in price_data.items():
        returns = df['Close'].pct_change().dropna()
        # Flag daily returns > 20% as suspicious
        outliers = returns[returns.abs() > 0.20]
        assert len(outliers) < len(returns) * 0.01  # <1% outliers
```

### Anti-Patterns to Avoid
- **Generating instance without validation:** Always validate data quality before freezing; Stooq has known quality issues
- **Computing hash of in-memory object:** Hash the actual file bytes, not the Python object (serialization may differ)
- **Non-deterministic JSON:** Without sort_keys=True, dictionary key order is undefined, leading to different hashes
- **Ignoring missing data implications:** pandas.cov() with missing data is unbiased but not guaranteed positive semi-definite

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA256 file hashing | Manual chunked reading loop | hashlib.file_digest() (Py 3.11+) | Optimized, bypasses Python I/O layer, handles edge cases |
| Covariance matrix validation | Manual eigenvalue computation | scipy.linalg.cholesky() | Cholesky decomposition is fastest way to check positive definite |
| Missing data in time series | Custom forward-fill logic | pandas dropna() or fillna() | Handles edge cases, index alignment, maintains data integrity |
| JSON schema validation | Manual field checks | jsonschema library (if adding) | Handles nested structures, provides clear error messages |
| Outlier detection | Z-score thresholds | Proven statistical methods (IQR, MAD) | Robust to distribution assumptions |

**Key insight:** Financial data validation has well-established patterns. Custom solutions miss edge cases (e.g., non-positive-definite matrices from insufficient data, timezone issues, corporate actions).

## Common Pitfalls

### Pitfall 1: Stooq Data Quality Issues
**What goes wrong:** Stooq data has up to 11% deviations from reference sources, missing adjusted close prices, and lacks corporate action adjustments (splits/dividends).
**Why it happens:** Stooq is a free data source with limited quality assurance and no split/dividend adjustments.
**How to avoid:**
- Implement validation checks for extreme daily returns (>20% suspicious)
- Check for missing data in date range
- Consider spot-checking critical tickers against another source
- Document known limitations in README
**Warning signs:**
- Unusually high volatility in computed Sigma
- Negative or near-zero eigenvalues in covariance matrix
- Large gaps in date coverage

### Pitfall 2: Non-Deterministic JSON Serialization
**What goes wrong:** Hashing the same data produces different SHA256 values across runs.
**Why it happens:** Python dicts have undefined iteration order without explicit sorting.
**How to avoid:** Always use `json.dump(data, f, sort_keys=True)` when writing files for hashing.
**Warning signs:**
- CI fails with "hash mismatch" on identical data
- Different hash values when regenerating instance

### Pitfall 3: Non-Positive-Definite Covariance Matrix
**What goes wrong:** Covariance matrix has negative eigenvalues or isn't invertible, breaking optimization algorithms.
**Why it happens:** Insufficient data points relative to number of assets (N=20 requires ~200+ observations), or high multicollinearity.
**Source:** [pandas DataFrame.cov() documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html) warns "returned covariance matrix will be an unbiased estimate but not guaranteed to be positive semi-definite."
**How to avoid:**
- Ensure sufficient aligned return observations (200+ for N=20)
- Validate with `scipy.linalg.cholesky(Sigma)` (raises LinAlgError if not positive definite)
- Check eigenvalues: `np.linalg.eigvalsh(Sigma)` should all be >= 0
**Warning signs:**
- Cholesky decomposition fails
- Minimum eigenvalue < -1e-10 (beyond machine precision)

### Pitfall 4: Missing Data Handling in Aligned Returns
**What goes wrong:** Different tickers have different trading calendars (holidays, halts), leading to misaligned returns.
**Why it happens:** Stooq data is international, US tickers may have different date availability.
**How to avoid:** Use `pd.concat(axis=1).dropna(how='any')` to align on common dates only (existing evaluate.py does this correctly).
**Warning signs:**
- Very few aligned observations (<200) after dropna
- Covariance matrix estimation warnings

### Pitfall 5: Float Precision in JSON Serialization
**What goes wrong:** NumPy arrays serialize with excessive precision or scientific notation, making JSON hard to read.
**Why it happens:** NumPy defaults to maximum precision for float64.
**How to avoid:**
- Convert with `.tolist()` for standard Python float representation
- Consider rounding to reasonable precision (e.g., 8 decimal places for financial data)
- Avoid orjson or custom encoders that change precision unexpectedly
**Warning signs:**
- JSON files are enormous (>10MB for 20x20 matrix)
- Values like 1.23456789012345678e-10 appear

## Code Examples

Verified patterns from official sources:

### Computing SHA256 Hash (Python 3.11+)
```python
# Source: https://docs.python.org/3/library/hashlib.html
import hashlib

def compute_instance_hash(instance_path):
    """Compute SHA256 hash of instance.json for integrity verification"""
    with open(instance_path, 'rb') as f:
        digest = hashlib.file_digest(f, 'sha256')
    return digest.hexdigest()

# Usage:
hash_value = compute_instance_hash('data/instance.json')
print(f"SHA256: {hash_value}")
```

### Validating Covariance Matrix is Positive Semi-Definite
```python
# Source: Financial data validation best practices
import numpy as np
from scipy import linalg

def validate_covariance_matrix(sigma):
    """
    Check if covariance matrix is positive semi-definite.
    Returns True if valid, raises ValueError with details if invalid.
    """
    # Check symmetry
    if not np.allclose(sigma, sigma.T):
        raise ValueError("Covariance matrix is not symmetric")

    # Check positive semi-definite via eigenvalues
    eigenvalues = np.linalg.eigvalsh(sigma)
    min_eigenvalue = eigenvalues.min()

    # Allow small negative values due to numerical precision
    if min_eigenvalue < -1e-10:
        raise ValueError(
            f"Covariance matrix has negative eigenvalue: {min_eigenvalue}"
        )

    # Try Cholesky decomposition (faster, fails if not positive definite)
    try:
        linalg.cholesky(sigma, lower=True)
    except linalg.LinAlgError:
        # Matrix is positive semi-definite but not positive definite
        # This is acceptable (means some assets are perfectly correlated)
        pass

    return True
```

### Canonical JSON Writing
```python
# Source: Python json stdlib, RFC 8785 (JCS) principles
import json
import os

def write_instance_json(instance, output_path):
    """
    Write instance to JSON with deterministic formatting for hashing.

    Args:
        instance: dict with keys: tickers, K, lambda, penalty_A, mu, sigma
        output_path: path to write instance.json

    Returns:
        SHA256 hash of written file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    # Write with sorted keys for deterministic output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(instance, f,
                  indent=2,           # Human-readable formatting
                  sort_keys=True,     # Deterministic key ordering
                  ensure_ascii=False) # Preserve unicode if present

    # Compute hash of written file
    import hashlib
    with open(output_path, 'rb') as f:
        digest = hashlib.file_digest(f, 'sha256')

    return digest.hexdigest()
```

### Pytest Data Quality Tests
```python
# Source: pytest documentation, MLOps data validation patterns
import pytest
import pandas as pd
import numpy as np

def test_instance_schema(instance_json_path):
    """Verify instance.json has required fields and structure"""
    with open(instance_json_path) as f:
        data = json.load(f)

    # Check required fields
    required = ['tickers', 'K', 'lambda', 'penalty_A', 'mu', 'sigma']
    for field in required:
        assert field in data, f"Missing required field: {field}"

    # Check dimensions
    N = len(data['tickers'])
    assert N == 20, f"Expected 20 tickers, got {N}"
    assert len(data['mu']) == N, f"mu vector has wrong length"
    assert len(data['sigma']) == N, f"sigma matrix has wrong row count"
    for row in data['sigma']:
        assert len(row) == N, f"sigma matrix has wrong column count"

    # Check parameter values
    assert data['K'] == 5
    assert data['lambda'] == 0.5
    assert data['penalty_A'] == 10.0

def test_date_coverage(price_dir, tickers):
    """Verify all tickers cover date range 2023-01-01 to 2025-12-31"""
    start = pd.Timestamp('2023-01-01')
    end = pd.Timestamp('2025-12-31')

    for ticker in tickers:
        df = load_stooq_csv(f"{price_dir}/{ticker}.csv")
        assert df.index.min() <= start, f"{ticker}: data starts too late"
        assert df.index.max() >= end, f"{ticker}: data ends too early"

def test_no_extreme_outliers(price_dir, tickers):
    """Flag suspicious daily returns (>20%) that may indicate data errors"""
    for ticker in tickers:
        df = load_stooq_csv(f"{price_dir}/{ticker}.csv")
        returns = df['Close'].pct_change().dropna()

        # Flag extreme returns (>20% daily move)
        extreme = returns[returns.abs() > 0.20]

        # Allow small number of extreme events (crashes, splits)
        # but flag if >1% of days have extreme moves
        assert len(extreme) / len(returns) < 0.01, \
            f"{ticker}: {len(extreme)} extreme returns (>20%), may indicate data error"

def test_sufficient_aligned_observations():
    """Verify enough aligned observations for robust covariance estimation"""
    # Rule of thumb: need ~10x observations per asset
    # For N=20, want 200+ observations
    instance = load_instance('data/instance.json')
    # This would need to be checked during instance generation
    # Storing observation count in instance.json metadata would help
    pass

def test_hash_integrity():
    """Verify instance.json hash matches documented value"""
    computed_hash = compute_instance_hash('data/instance.json')

    # Read documented hash from README
    with open('README.md') as f:
        readme = f.read()

    # Extract hash (assumes format: SHA256: <hash>)
    import re
    match = re.search(r'SHA256:\s*([a-f0-9]{64})', readme)
    assert match, "README.md missing SHA256 hash"

    documented_hash = match.group(1)
    assert computed_hash == documented_hash, \
        f"Hash mismatch: computed {computed_hash}, README has {documented_hash}"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual JSON key sorting | sort_keys=True parameter | Always standard | Ensures deterministic JSON for hashing |
| Chunked hash reading | hashlib.file_digest() | Python 3.11 (2022) | Faster, bypasses I/O layer |
| unittest | pytest | ~2015+ | Better fixtures, parametrization, clearer assertions |
| Custom JSON schema checks | jsonschema library | Mature since 2013 | Clearer validation, better errors |
| Manual missing data handling | pandas dropna/fillna | Always standard | Handles edge cases, preserves types |

**Deprecated/outdated:**
- `hashlib.md5()` for integrity checks: Use SHA256 (MD5 is cryptographically broken)
- `np.matrix` type: Use `np.ndarray` (np.matrix deprecated in NumPy 1.20+)
- Python <3.10: Current best practice is Python 3.11+ for file_digest() optimization

## Open Questions

Things that couldn't be fully resolved:

1. **Exact validation threshold for "acceptable" data deviation**
   - What we know: Research mentions "up to 11% deviations" from reference sources
   - What's unclear: Is this 11% acceptable, or should data be rejected/corrected?
   - Recommendation: Document as known limitation, implement warning (not error) for >10% daily returns, proceed with Stooq data since parameters are locked

2. **Missing adjusted close prices from Stooq**
   - What we know: Stooq doesn't provide split/dividend-adjusted prices
   - What's unclear: Does Stooq's "Close" column have any adjustments, or is it raw?
   - Recommendation: Use Stooq "Close" as-is (existing evaluate.py does this), document assumption that corporate actions during 2023-2025 are minimal for these large-cap stocks

3. **Optimal observation count for N=20, K=5**
   - What we know: Rule of thumb is ~10x observations per asset (200+ for N=20)
   - What's unclear: Exact minimum for acceptable covariance matrix stability
   - Recommendation: Verify >200 aligned observations after dropna, store observation count in instance.json metadata

4. **Python version compatibility (hashlib.file_digest)**
   - What we know: file_digest() added in Python 3.11 (Oct 2022)
   - What's unclear: Should code support Python <3.11?
   - Recommendation: Check requirements.txt Python version, provide fallback chunked reading if needed

## Sources

### Primary (HIGH confidence)
- [Python hashlib documentation](https://docs.python.org/3/library/hashlib.html) - SHA256 hashing, file_digest() method
- [pandas.DataFrame.cov() documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html) - Covariance computation, missing data handling
- [jsonschema validation documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/) - JSON schema validation patterns
- Existing repository code (evaluate.py, download_stooq.py) - Current implementation patterns

### Secondary (MEDIUM confidence)
- [Financial data validation best practices (Cube Software)](https://www.cubesoftware.com/blog/data-validation-best-practices) - Validation principles for finance
- [An Introduction to Stooq Pricing Data (QuantStart)](https://www.quantstart.com/articles/an-introduction-to-stooq-pricing-data/) - Stooq data source characteristics
- [Building a Lightweight Data Validation Framework with PyTest (Medium)](https://medium.com/@husein2709/building-a-lightweight-data-validation-framework-with-pytest-and-github-actions-b9995c7f9556) - pytest patterns for data validation
- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) - Canonical JSON principles
- [Data Validation in Python Using Pandas (CodeSignal)](https://codesignal.com/learn/courses/data-cleaning-and-validation-for-machine-learning/lessons/data-validation-in-python-using-pandas) - Pandas validation patterns
- [Covariance Matrix Positive Semi-Definite validation (Statistical Proofs)](https://statproofbook.github.io/P/covmat-psd.html) - Mathematical foundation
- [Handling Missing Data in Financial Time Series (HackerNoon)](https://hackernoon.com/dealing-with-missing-data-in-financial-time-series-recipes-and-pitfalls) - Missing data strategies

### Tertiary (LOW confidence)
- WebSearch results on Stooq data quality (2026) - Community reports of quality issues
- WebSearch results on anomaly detection in stock data (2026) - Outlier detection approaches

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries are mature, well-documented, and already in use
- Architecture: HIGH - Patterns verified against official documentation and existing codebase
- Pitfalls: HIGH - Based on official pandas documentation warnings and financial data validation literature
- Stooq data quality: MEDIUM - Based on community reports and QuantStart analysis, not official Stooq documentation

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days - stable domain, Python stdlib and mature libraries change slowly)
