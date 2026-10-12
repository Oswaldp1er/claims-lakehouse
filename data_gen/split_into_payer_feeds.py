"""
Turn Synthea CSV output into a "multi-payor feed" layout for lakehouse practice.

Real claims platforms receive files from many payors on a schedule. This script
simulates that: claims and claim transactions are split by payer and by service
month, so you can drip-feed them into a landing folder and ingest them with
Databricks Auto Loader (Structured Streaming).

Output layout (under --out):
  reference/   patients, payers, payer_transitions, providers, organizations
  clinical/    encounters, conditions, procedures, medications
  backfill/    claims and claim transactions before --feed-start (one file per payer)
  feeds/       claims and claim transactions from --feed-start on, one file per payer per month
                 feeds/claims/<payer>/claims_<payer>_<YYYYMM>.csv
                 feeds/claims_transactions/<payer>/claims_transactions_<payer>_<YYYYMM>.csv

Usage:
  python split_into_payer_feeds.py --src <synthea output/csv> --out <data dir> [--feed-start 2024-01]
"""
import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

REFERENCE = ["patients", "payers", "payer_transitions", "providers", "organizations"]
CLINICAL = ["encounters", "conditions", "procedures", "medications"]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Synthea output/csv folder")
    ap.add_argument("--out", required=True, help="Destination data folder")
    ap.add_argument("--feed-start", default="2024-01", help="First month delivered as monthly feeds (YYYY-MM)")
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    feed_start = pd.Period(args.feed_start, freq="M")

    for group, names in (("reference", REFERENCE), ("clinical", CLINICAL)):
        (out / group).mkdir(parents=True, exist_ok=True)
        for n in names:
            shutil.copy2(src / f"{n}.csv", out / group / f"{n}.csv")

    payers = pd.read_csv(src / "payers.csv", usecols=["Id", "NAME"])
    payer_slug = dict(zip(payers["Id"], payers["NAME"].map(slug)))

    # Claims with no primary insurance are self-pay (patient responsibility).
    claims = pd.read_csv(src / "claims.csv", dtype=str)
    claims["_payer"] = claims["PRIMARYPATIENTINSURANCEID"].map(payer_slug).fillna("self_pay")
    claims["_month"] = pd.to_datetime(claims["SERVICEDATE"], utc=True).dt.tz_localize(None).dt.to_period("M")

    tx = pd.read_csv(src / "claims_transactions.csv", dtype=str)
    tx = tx.merge(claims[["Id", "_payer", "_month"]], left_on="CLAIMID", right_on="Id", how="left", suffixes=("", "_claim"))
    tx = tx.drop(columns=["Id"])
    tx["_payer"] = tx["_payer"].fillna("self_pay")

    for name, df in (("claims", claims), ("claims_transactions", tx)):
        cols = [c for c in df.columns if not c.startswith("_")]
        hist = df[df["_month"] < feed_start]
        feed = df[df["_month"] >= feed_start]
        for payer, g in hist.groupby("_payer"):
            p = out / "backfill" / name / payer
            p.mkdir(parents=True, exist_ok=True)
            g[cols].to_csv(p / f"{name}_{payer}_before_{feed_start.strftime('%Y%m')}.csv", index=False)
        for (payer, month), g in feed.groupby(["_payer", "_month"]):
            p = out / "feeds" / name / payer
            p.mkdir(parents=True, exist_ok=True)
            g[cols].to_csv(p / f"{name}_{payer}_{month.strftime('%Y%m')}.csv", index=False)

    n_feed = len(list((out / "feeds").rglob("*.csv")))
    print(f"claims: {len(claims):,}  transactions: {len(tx):,}  payers: {claims['_payer'].nunique()}  monthly feed files: {n_feed}")
    print(claims.groupby("_payer").size().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
