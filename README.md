# DDSC x DQC Quantum Portfolio Challenge

A quantum computing challenge by [Danish Data Science Community (DDSC)](https://ddsc.io) and [Danish Quantum Community (DQC)](https://dqc.dk) exploring whether quantum optimization (QAOA) can outperform classical heuristics on a real-world financial problem.

**No quantum hardware required.** Simulators welcome. Classical solutions welcome. The point is to compare.

---

## Problem Brief: Quantum Mean-Variance Portfolio Selection

### Goal

Given historical price data for **N = 20** assets, select exactly **K = 5** assets to maximize a risk-adjusted return objective. Participants may solve using quantum methods (e.g., QAOA on a simulator) or classical methods. Submissions are evaluated by the achieved objective value — lower energy is better.

### Background

Mean-variance portfolio optimization (Markowitz, 1952) is a natural fit for quantum optimization because the objective is quadratic in binary decision variables. By encoding asset selection as a QUBO (Quadratic Unconstrained Binary Optimization), the problem maps directly onto quantum annealing hardware and variational quantum algorithms like QAOA.

### Mathematical Formulation

**Input data** (computed from historical daily prices):

- Daily log returns: `r(t,i) = ln(P(t,i) / P(t-1,i))`
- Mean return vector: `mu` (length N)
- Covariance matrix: `Sigma` (N x N)

**Decision variables:**

```
x_i in {0, 1},  i = 1..N     (1 = select asset i, 0 = skip)
```

**Cardinality constraint:**

```
sum(x_i) = K
```

**Objective (maximize risk-adjusted return):**

```
maximize:  mu^T x  -  lambda * x^T Sigma x
```

Where `lambda` is the risk aversion parameter (provided).

**QUBO form (minimize energy):**

To cast this as a minimization problem suitable for quantum solvers:

```
minimize E(x) = -mu^T x  +  lambda * x^T Sigma x  +  A * (sum(x_i) - K)^2
```

Where:
- `lambda = 0.5` (risk aversion — balances return vs. risk)
- `A = 10.0` (penalty coefficient — enforces the cardinality constraint)
- `K = 5` (number of assets to select)

The penalty term `A * (sum(x) - K)^2` equals zero for feasible solutions (exactly K assets selected) and grows quadratically for violations. `A` is set large enough that violating the constraint always costs more than any gain from the objective.

### What to Submit

A JSON file with a single key `"x"` containing a length-20 list of 0/1 values:

```json
{ "x": [0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0] }
```

Each position corresponds to the ticker at the same index in `data/tickers.txt`.

### Scoring

- **Primary score:** `E(x)` — lower is better
- **Feasibility:** If `sum(x) != K`, the penalty term inflates your score automatically. You are **not** disqualified — you just get a worse score.
- **Tiebreaker:** If two submissions have equal energy, the one submitted first wins.

### Assets

20 liquid US equities (3 years of daily data, 2023-01-01 to 2025-12-31):

| # | Ticker | Company |
|---|--------|---------|
| 0 | AAPL | Apple |
| 1 | MSFT | Microsoft |
| 2 | AMZN | Amazon |
| 3 | GOOG | Alphabet |
| 4 | NVDA | NVIDIA |
| 5 | META | Meta Platforms |
| 6 | BRK-B | Berkshire Hathaway |
| 7 | JPM | JPMorgan Chase |
| 8 | XOM | Exxon Mobil |
| 9 | UNH | UnitedHealth |
| 10 | V | Visa |
| 11 | AVGO | Broadcom |
| 12 | TSLA | Tesla |
| 13 | COST | Costco |
| 14 | PEP | PepsiCo |
| 15 | KO | Coca-Cola |
| 16 | MCD | McDonald's |
| 17 | NFLX | Netflix |
| 18 | ORCL | Oracle |
| 19 | DIS | Disney |

### Parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| N | 20 | Number of assets |
| K | 5 | Assets to select |
| lambda | 0.5 | Risk aversion |
| A | 10.0 | Constraint penalty |

### Instance Data

The file `instance.json` is pre-committed in the repository root and contains the mean return vector (`mu`), covariance matrix (`sigma`), ticker list, and all QUBO parameters. This is the single source of truth for the challenge -- all submissions are scored against it.

**SHA256 checksum (LF-normalized):**

```
a3cbbd1d9e0125813e1026b39078ed8cc62ffb504238a476673cd7a58c0642dc
```

Verify your copy is unmodified:

```bash
# Linux / macOS
shasum -a 256 instance.json

# Windows (PowerShell)
(Get-FileHash instance.json -Algorithm SHA256).Hash.ToLower()

# Python (cross-platform, normalizes line endings)
python -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('instance.json').read_bytes().replace(b'\r\n', b'\n')).hexdigest())"
```

---

## Getting Started

### 1. Clone and set up

```bash
git clone https://github.com/de-Blanck/ddsc-dqc-portfolio-challenge.git
cd ddsc-dqc-portfolio-challenge

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Download price data (Optional)

> **Note:** `instance.json` is already committed in the repo. You only need to download price data if you want to regenerate it yourself or explore the raw data.

```bash
python scripts/download_stooq.py
```

This downloads daily CSVs from [Stooq](https://stooq.com) (free, no API key) into `data/prices/`. Takes about 10 seconds.

### 3. Generate the challenge instance (Optional)

> **Note:** Skip this step -- `instance.json` is already committed with the frozen challenge data. Only run this if you downloaded price data in step 2 and want to verify the instance generation.

```bash
python scripts/evaluate.py --K 5 --lambda_ 0.5 --penalty_A 10.0 --start 2023-01-01 --end 2025-12-31
```

This reads the price CSVs, computes `mu` and `Sigma`, and writes `data/instance.json`. This file contains everything you need to solve the QUBO — no need to touch the raw price data again.

### 4. Score a submission

```bash
python scripts/evaluate.py --score submissions/example_submission.json
```

Output:

```json
{
  "energy": -0.000123,
  "feasible": true,
  "cardinality": 5,
  "K": 5
}
```

### 5. Run the classical baseline (simulated annealing)

```bash
python scripts/baseline_sa.py
```

This runs 50,000 iterations of simulated annealing on the QUBO and writes the result to `submissions/sa_submission.json`. Use this as your benchmark to beat.

You can tune SA parameters:

```bash
python scripts/baseline_sa.py --iterations 100000 --T_start 2.0 --T_end 1e-5 --seed 123
```

Then score it:

```bash
python scripts/evaluate.py --score submissions/sa_submission.json
```

---

## Approaches You Might Try

### Quantum (the point of the challenge)

- **QAOA** (Quantum Approximate Optimization Algorithm) via Qiskit, Cirq, or PennyLane
- **VQE** (Variational Quantum Eigensolver) with a QUBO Hamiltonian
- **Quantum Annealing** simulation (e.g., D-Wave Ocean SDK with SimulatedAnnealingSampler)
- **Grover Adaptive Search** for constrained optimization

### Classical (the baseline to beat)

- Simulated annealing (provided)
- Greedy heuristic (select top-K by Sharpe ratio, then local search)
- Branch and bound / integer programming (e.g., Gurobi, CPLEX, OR-Tools)
- Genetic algorithms

---

## Repo Structure

```
ddsc-dqc-portfolio-challenge/
  README.md               # This file
  LICENSE                  # MIT
  requirements.txt         # Python dependencies
  instance.json            # Frozen QUBO instance (mu, Sigma, parameters)
  data/
    tickers.txt            # 20 ticker symbols
    prices/                # Downloaded CSVs (not committed)
  scripts/
    download_stooq.py      # Fetch price data from Stooq
    evaluate.py            # Build instance + score submissions
    baseline_sa.py         # Simulated annealing baseline
  tests/
    test_instance.py       # Validation tests for instance.json
  submissions/
    example_submission.json
```

---

## Data Source

Historical prices are downloaded from [Stooq](https://stooq.com), a free financial data provider. No API key required. The download script fetches daily OHLCV data for each ticker.

**Note:** Stooq data is for educational and research purposes. If you encounter rate limiting, increase the `--sleep` parameter in the download script.

---

## License

MIT. See [LICENSE](LICENSE).

---

*A [DDSC](https://ddsc.io) x [DQC](https://dqc.dk) initiative.*
