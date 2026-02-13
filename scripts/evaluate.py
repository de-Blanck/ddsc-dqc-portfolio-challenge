#!/usr/bin/env python3
"""
Evaluation script for the DDSC x DQC Quantum Portfolio Challenge.

Builds the QUBO instance from historical price data and scores submissions.

Usage:
    # Generate instance
    python scripts/evaluate.py --K 5 --lambda_ 0.5 --penalty_A 10.0 --start 2023-01-01 --end 2025-12-31

    # Score a submission
    python scripts/evaluate.py --score submissions/example_submission.json
"""
import argparse
import json
import os
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass
class Instance:
    tickers: List[str]
    mu: np.ndarray          # shape (N,)
    sigma: np.ndarray       # shape (N,N)
    K: int
    lam: float
    penalty_A: float


def load_stooq_csv(path: str) -> pd.DataFrame:
    """
    Stooq CSV commonly has columns: Date, Open, High, Low, Close, Volume.
    We only need Date + Close.
    """
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("date")
    close_col = cols.get("close") or cols.get("zamkniecie")
    if date_col is None or close_col is None:
        raise ValueError(f"Unexpected columns in {path}: {df.columns.tolist()}")
    df = df[[date_col, close_col]].rename(columns={date_col: "Date", close_col: "Close"})
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna()
    return df


def compute_log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices).diff().dropna()


def build_instance(
    price_dir: str,
    tickers: List[str],
    K: int,
    lam: float,
    penalty_A: float,
    start_date: str = None,
    end_date: str = None,
) -> Instance:
    rets = []
    kept = []
    for t in tickers:
        path = os.path.join(price_dir, f"{t}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing price file: {path}")
        df = load_stooq_csv(path)
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
        r = compute_log_returns(df["Close"]).rename(t)
        rets.append(r)
        kept.append(t)

    R = pd.concat(rets, axis=1).dropna(how="any")
    if len(R) < 200:
        raise ValueError(
            f"Too few aligned return rows ({len(R)}). "
            "Expand date range or reduce tickers."
        )

    mu = R.mean().values.astype(float)
    sigma = R.cov().values.astype(float)

    return Instance(tickers=kept, mu=mu, sigma=sigma, K=K, lam=lam, penalty_A=penalty_A)


def energy(x: np.ndarray, inst: Instance) -> float:
    """Compute QUBO energy E(x) = -mu^T x + lam x^T Sigma x + A(sum(x)-K)^2."""
    x = x.astype(float)
    term_ret = -float(inst.mu @ x)
    term_risk = float(inst.lam * (x.T @ inst.sigma @ x))
    term_pen = float(inst.penalty_A * (x.sum() - inst.K) ** 2)
    return term_ret + term_risk + term_pen


def parse_submission(path: str, N: int) -> np.ndarray:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    x = obj.get("x")
    if x is None:
        raise ValueError("Submission JSON must contain key 'x'.")
    if isinstance(x, str):
        x = [int(ch) for ch in x.strip()]
    x = np.array(x, dtype=int).reshape(-1)
    if len(x) != N:
        raise ValueError(f"'x' must have length {N}, got {len(x)}.")
    if not np.all((x == 0) | (x == 1)):
        raise ValueError("All entries in 'x' must be 0/1.")
    return x


def write_instance_json(inst: Instance, out_path: str) -> None:
    payload = {
        "tickers": inst.tickers,
        "K": inst.K,
        "lambda": inst.lam,
        "penalty_A": inst.penalty_A,
        "mu": inst.mu.tolist(),
        "sigma": inst.sigma.tolist(),
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser(
        description="DDSC x DQC Quantum Portfolio Challenge — instance builder & scorer"
    )
    ap.add_argument("--price_dir", default="data/prices",
                    help="Folder containing per-ticker CSVs.")
    ap.add_argument("--tickers", default="data/tickers.txt",
                    help="Tickers list file (one per line).")
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--lambda_", type=float, default=0.5)
    ap.add_argument("--penalty_A", type=float, default=10.0)
    ap.add_argument("--start", default=None, help="YYYY-MM-DD")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD")
    ap.add_argument("--emit_instance", default="data/instance.json",
                    help="Write instance JSON here.")
    ap.add_argument("--score", default=None,
                    help="Path to submission.json to score.")
    args = ap.parse_args()

    with open(args.tickers, "r", encoding="utf-8") as f:
        tickers = [
            ln.strip().lower()
            for ln in f
            if ln.strip() and not ln.strip().startswith("#")
        ]

    inst = build_instance(
        price_dir=args.price_dir,
        tickers=tickers,
        K=args.K,
        lam=args.lambda_,
        penalty_A=args.penalty_A,
        start_date=args.start,
        end_date=args.end,
    )

    write_instance_json(inst, args.emit_instance)
    print(f"Wrote instance to {args.emit_instance} (N={len(inst.tickers)}, K={inst.K})")

    if args.score:
        x = parse_submission(args.score, N=len(inst.tickers))
        e = energy(x, inst)
        feasible = int(x.sum() == inst.K)
        result = {
            "energy": e,
            "feasible": bool(feasible),
            "cardinality": int(x.sum()),
            "K": inst.K,
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
