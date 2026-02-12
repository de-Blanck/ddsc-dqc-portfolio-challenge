#!/usr/bin/env python3
"""
Simulated annealing baseline for the DDSC x DQC Quantum Portfolio Challenge.

Operates on the QUBO energy function. Maintains feasibility by swapping
a selected asset (1) with an unselected asset (0) at each step.

Usage:
    python scripts/baseline_sa.py
    python scripts/baseline_sa.py --instance data/instance.json --iterations 50000 --output submissions/sa_submission.json
"""
import argparse
import json
import math
import random

import numpy as np


def load_instance(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def energy(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray,
           K: int, lam: float, penalty_A: float) -> float:
    """Compute QUBO energy E(x) = -mu^T x + lam x^T Sigma x + A(sum(x)-K)^2."""
    xf = x.astype(float)
    return -float(mu @ xf) + lam * float(xf @ sigma @ xf) + penalty_A * (xf.sum() - K) ** 2


def simulated_annealing(
    mu: np.ndarray,
    sigma: np.ndarray,
    K: int,
    lam: float,
    penalty_A: float,
    iterations: int = 50000,
    T_start: float = 1.0,
    T_end: float = 1e-4,
    seed: int = 42,
) -> tuple:
    rng = random.Random(seed)
    N = len(mu)

    # Start with a random feasible solution: exactly K ones
    indices = list(range(N))
    rng.shuffle(indices)
    x = np.zeros(N, dtype=int)
    for i in indices[:K]:
        x[i] = 1

    best_x = x.copy()
    best_e = energy(x, mu, sigma, K, lam, penalty_A)
    current_e = best_e

    cooling_rate = (T_end / T_start) ** (1.0 / iterations)
    T = T_start

    ones = [i for i in range(N) if x[i] == 1]
    zeros = [i for i in range(N) if x[i] == 0]

    for step in range(iterations):
        # Swap: turn off one selected asset, turn on one unselected asset
        i_on = rng.choice(ones)
        i_off = rng.choice(zeros)

        x[i_on] = 0
        x[i_off] = 1

        new_e = energy(x, mu, sigma, K, lam, penalty_A)
        delta = new_e - current_e

        if delta < 0 or rng.random() < math.exp(-delta / max(T, 1e-12)):
            # Accept
            current_e = new_e
            ones.remove(i_on)
            ones.append(i_off)
            zeros.remove(i_off)
            zeros.append(i_on)
            if current_e < best_e:
                best_e = current_e
                best_x = x.copy()
        else:
            # Reject — revert
            x[i_on] = 1
            x[i_off] = 0

        T *= cooling_rate

    return best_x, best_e


def main():
    ap = argparse.ArgumentParser(
        description="Simulated annealing baseline for quantum portfolio challenge"
    )
    ap.add_argument("--instance", default="data/instance.json",
                    help="Path to instance JSON (from evaluate.py)")
    ap.add_argument("--iterations", type=int, default=50000)
    ap.add_argument("--T_start", type=float, default=1.0)
    ap.add_argument("--T_end", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", default="submissions/sa_submission.json")
    args = ap.parse_args()

    inst = load_instance(args.instance)
    mu = np.array(inst["mu"])
    sigma = np.array(inst["sigma"])
    K = inst["K"]
    lam = inst["lambda"]
    penalty_A = inst["penalty_A"]
    N = len(mu)

    print(f"Instance: N={N}, K={K}, lambda={lam}, penalty_A={penalty_A}")
    print(f"Running SA: {args.iterations} iterations, T={args.T_start}->{args.T_end}, seed={args.seed}")

    best_x, best_e = simulated_annealing(
        mu=mu, sigma=sigma, K=K, lam=lam, penalty_A=penalty_A,
        iterations=args.iterations,
        T_start=args.T_start, T_end=args.T_end, seed=args.seed,
    )

    selected = [inst["tickers"][i] for i in range(N) if best_x[i] == 1]
    print(f"\nBest energy: {best_e:.6f}")
    print(f"Selected assets ({len(selected)}): {', '.join(selected)}")
    print(f"Feasible: {int(best_x.sum()) == K}")

    submission = {"x": best_x.tolist()}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2)
    print(f"Submission written to {args.output}")


if __name__ == "__main__":
    main()
