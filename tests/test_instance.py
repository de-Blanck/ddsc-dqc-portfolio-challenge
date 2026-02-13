"""Validation tests for instance.json integrity.

Ensures the frozen challenge instance has correct structure, parameters,
mathematical properties, and matches the documented SHA256 hash.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).parent.parent
INSTANCE_PATH = REPO_ROOT / "instance.json"


@pytest.fixture(scope="module")
def instance():
    """Load instance.json as a Python dict."""
    with open(INSTANCE_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------


def test_instance_exists():
    """instance.json must exist at the repository root."""
    assert INSTANCE_PATH.exists(), (
        f"instance.json not found at {INSTANCE_PATH}"
    )


def test_required_fields(instance):
    """instance.json must contain all required top-level keys."""
    required = {"tickers", "K", "lambda", "penalty_A", "mu", "sigma"}
    missing = required - set(instance.keys())
    assert not missing, f"Missing required fields: {missing}"


def test_dimensions(instance):
    """All arrays must have consistent N=20 dimensions."""
    n = 20
    assert len(instance["tickers"]) == n, (
        f"Expected {n} tickers, got {len(instance['tickers'])}"
    )
    assert len(instance["mu"]) == n, (
        f"Expected {n} mu values, got {len(instance['mu'])}"
    )
    assert len(instance["sigma"]) == n, (
        f"Expected {n} sigma rows, got {len(instance['sigma'])}"
    )
    for i, row in enumerate(instance["sigma"]):
        assert len(row) == n, (
            f"Sigma row {i} has {len(row)} columns, expected {n}"
        )


# ---------------------------------------------------------------------------
# Parameter tests
# ---------------------------------------------------------------------------


def test_locked_parameters(instance):
    """Challenge parameters must match the locked values."""
    assert instance["K"] == 5, f"K must be 5, got {instance['K']}"
    assert instance["lambda"] == 0.5, (
        f"lambda must be 0.5, got {instance['lambda']}"
    )
    assert instance["penalty_A"] == 10.0, (
        f"penalty_A must be 10.0, got {instance['penalty_A']}"
    )


def test_tickers_match(instance):
    """Tickers in instance.json must match data/tickers.txt."""
    tickers_path = REPO_ROOT / "data" / "tickers.txt"
    assert tickers_path.exists(), f"tickers.txt not found at {tickers_path}"

    expected = [
        line.strip().lower()
        for line in tickers_path.read_text().splitlines()
        if line.strip()
    ]
    actual = [t.strip().lower() for t in instance["tickers"]]
    assert actual == expected, (
        f"Ticker mismatch.\n  Expected: {expected}\n  Actual:   {actual}"
    )


# ---------------------------------------------------------------------------
# Mathematical property tests
# ---------------------------------------------------------------------------


def test_sigma_symmetric(instance):
    """Covariance matrix Sigma must be symmetric."""
    sigma = np.array(instance["sigma"])
    assert np.allclose(sigma, sigma.T), (
        "Sigma is not symmetric: max diff = "
        f"{np.max(np.abs(sigma - sigma.T)):.2e}"
    )


def test_sigma_positive_semidefinite(instance):
    """Covariance matrix Sigma must be positive semi-definite."""
    sigma = np.array(instance["sigma"])
    eigenvalues = np.linalg.eigvalsh(sigma)
    min_eig = eigenvalues.min()
    assert min_eig >= -1e-10, (
        f"Sigma is not positive semi-definite: "
        f"smallest eigenvalue = {min_eig:.2e}"
    )


def test_mu_reasonable_range(instance):
    """Mean return values must be within a reasonable daily range."""
    mu = np.array(instance["mu"])
    assert np.all((-1.0 <= mu) & (mu <= 1.0)), (
        f"mu values outside [-1.0, 1.0]: "
        f"min={mu.min():.6f}, max={mu.max():.6f}"
    )


def test_sigma_diagonal_positive(instance):
    """Variance (diagonal of Sigma) must be strictly positive."""
    sigma = np.array(instance["sigma"])
    diag = np.diag(sigma)
    assert np.all(diag > 0), (
        f"Sigma has non-positive diagonal entries: "
        f"min diagonal = {diag.min():.2e}"
    )


# ---------------------------------------------------------------------------
# Integrity tests
# ---------------------------------------------------------------------------


def test_hash_integrity(instance):
    """SHA256 of instance.json must match the hash documented in README.md.

    Uses LF-normalized bytes so the hash is identical on Windows (CRLF
    checkout) and Linux/macOS (LF checkout).
    """
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists(), f"README.md not found at {readme_path}"

    readme_text = readme_path.read_text()
    match = re.search(r"[Ss][Hh][Aa]256.*?([a-f0-9]{64})", readme_text, re.DOTALL)
    assert match, "No SHA256 hash found in README.md"

    expected_hash = match.group(1)
    # Normalize to LF for cross-platform consistency
    file_bytes = INSTANCE_PATH.read_bytes().replace(b"\r\n", b"\n")
    actual_hash = hashlib.sha256(file_bytes).hexdigest()
    assert actual_hash == expected_hash, (
        f"SHA256 mismatch!\n"
        f"  README says: {expected_hash}\n"
        f"  File hash:   {actual_hash}"
    )


def test_json_deterministic(instance):
    """Re-serializing instance.json with sort_keys=True must produce identical content.

    Compares with normalized (LF) line endings so the test passes regardless
    of whether git checks out the file with CRLF (Windows) or LF (Unix).
    """
    file_bytes = INSTANCE_PATH.read_bytes()
    # Normalize to LF for cross-platform comparison
    file_normalized = file_bytes.replace(b"\r\n", b"\n")
    file_hash = hashlib.sha256(file_normalized).hexdigest()

    with open(INSTANCE_PATH) as f:
        data = json.load(f)

    reserialized = json.dumps(data, indent=2, sort_keys=True) + "\n"
    reserialized_hash = hashlib.sha256(reserialized.encode()).hexdigest()

    assert reserialized_hash == file_hash, (
        f"JSON is not deterministic!\n"
        f"  File hash:         {file_hash}\n"
        f"  Reserialized hash: {reserialized_hash}\n"
        f"  The file was likely not written with sort_keys=True"
    )
