#!/usr/bin/env python3
"""
Download historical daily prices from Stooq for all tickers in the ticker list.

Usage:
    python scripts/download_stooq.py
    python scripts/download_stooq.py --tickers data/tickers.txt --out data/prices
"""
import argparse
import os
import time

import requests


def main():
    ap = argparse.ArgumentParser(description="Download Stooq price CSVs")
    ap.add_argument("--tickers", default="data/tickers.txt")
    ap.add_argument("--out", default="data/prices")
    ap.add_argument("--sleep", type=float, default=0.5,
                    help="Seconds between requests (be polite to Stooq)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with open(args.tickers, "r", encoding="utf-8") as f:
        tickers = [
            ln.strip().lower()
            for ln in f
            if ln.strip() and not ln.strip().startswith("#")
        ]

    print(f"Downloading {len(tickers)} tickers to {args.out}/")
    for i, t in enumerate(tickers, 1):
        url = f"https://stooq.com/q/d/l/?s={t}&i=d"
        path = os.path.join(args.out, f"{t}.csv")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(path, "wb") as w:
                w.write(r.content)
            print(f"  [{i}/{len(tickers)}] {t} -> {path}")
        except requests.RequestException as e:
            print(f"  [{i}/{len(tickers)}] {t} FAILED: {e}")
        time.sleep(args.sleep)

    print("Done.")


if __name__ == "__main__":
    main()
