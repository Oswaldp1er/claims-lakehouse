# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Drip-feed payor files into the landing zone
# MAGIC
# MAGIC Simulates payors delivering monthly files. Each run copies the **next N months**
# MAGIC of claim and transaction files (all payors) from `staging/.../feeds/` into `landing/`.
# MAGIC Run it, then run your Auto Loader pipeline, and repeat. That is how you practice
# MAGIC incremental ingestion, checkpoints and idempotent `MERGE`.
# MAGIC
# MAGIC Set `reset = yes` to empty the landing zone and start over (also clear your checkpoints).

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Catalog")
dbutils.widgets.text("schema", "claims_lakehouse", "Schema")
dbutils.widgets.text("volume", "raw", "Volume")
dbutils.widgets.text("months", "1", "Months to deliver")
dbutils.widgets.dropdown("reset", "no", ["no", "yes"], "Reset landing zone")

vol_path = f"/Volumes/{dbutils.widgets.get('catalog')}/{dbutils.widgets.get('schema')}/{dbutils.widgets.get('volume')}"
months_to_deliver = int(dbutils.widgets.get("months"))
feeds = f"{vol_path}/staging/claims_lakehouse_data/feeds"
landing = f"{vol_path}/landing"

# COMMAND ----------

import os
import re
import shutil

if dbutils.widgets.get("reset") == "yes":
    for d in ["claims", "claims_transactions"]:
        shutil.rmtree(f"{landing}/{d}", ignore_errors=True)
        os.makedirs(f"{landing}/{d}", exist_ok=True)
    print("Landing zone emptied.")


def all_files(root):
    """{(dataset, payer, yyyymm): path} for every feed file under root."""
    out = {}
    for dataset in ["claims", "claims_transactions"]:
        base = f"{root}/{dataset}"
        if not os.path.exists(base):
            continue
        for payer in os.listdir(base):
            for f in os.listdir(f"{base}/{payer}"):
                m = re.search(r"_(\d{6})\.csv$", f)
                if m:
                    out[(dataset, payer, m.group(1))] = f"{base}/{payer}/{f}"
    return out


available = all_files(feeds)
delivered = all_files(landing)
delivered_months = {k[2] for k in delivered}
pending_months = sorted({k[2] for k in available} - delivered_months)
to_deliver = pending_months[:months_to_deliver]

copied = 0
for (dataset, payer, month), path in sorted(available.items()):
    if month in to_deliver:
        dest_dir = f"{landing}/{dataset}/{payer}"
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy(path, dest_dir)
        copied += 1

print(f"Delivered months: {to_deliver or 'none (all months already delivered)'}")
print(f"Files copied: {copied}. Months still pending: {len(pending_months) - len(to_deliver)}")
