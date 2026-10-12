# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Load the synthetic data into the raw volume
# MAGIC
# MAGIC The schema and volume are **not** created here. They are infrastructure, so they're
# MAGIC defined in `databricks.yml` and created with `databricks bundle deploy -t dev`.
# MAGIC This notebook only handles data: it unpacks the uploaded zip.
# MAGIC
# MAGIC **Before running:**
# MAGIC 1. Deploy the bundle (creates `<catalog>.<schema>` and the volume `raw`).
# MAGIC 2. In Catalog Explorer, open the `raw` volume, create a folder named `upload`, and upload
# MAGIC    `claims_lakehouse_data.zip` there.
# MAGIC
# MAGIC Then run all cells. Notebook `01_drip_feed` copies payor files into `landing/` month by month.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Catalog")
dbutils.widgets.text("schema", "claims_lakehouse", "Schema")
dbutils.widgets.text("volume", "raw", "Volume")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
volume = dbutils.widgets.get("volume")
vol_path = f"/Volumes/{catalog}/{schema}/{volume}"

# Fail fast with a clear message if the bundle hasn't been deployed yet.
try:
    volumes = [r.volume_name for r in spark.sql(f"SHOW VOLUMES IN {catalog}.{schema}").collect()]
except Exception:
    volumes = []
assert volume in volumes, f"Volume {catalog}.{schema}.{volume} not found. Run `databricks bundle deploy -t dev` first."
print(f"Found {vol_path}")

# COMMAND ----------

import os
import zipfile

zip_path = f"{vol_path}/upload/claims_lakehouse_data.zip"
staging = f"{vol_path}/staging"

assert os.path.exists(zip_path), f"Upload the zip to {zip_path} first."

with zipfile.ZipFile(zip_path) as z:
    z.extractall(staging)

dbutils.fs.mkdirs(f"{vol_path}/landing/claims")
dbutils.fs.mkdirs(f"{vol_path}/landing/claims_transactions")

for root in ["reference", "clinical", "backfill", "feeds"]:
    p = f"{staging}/claims_lakehouse_data/{root}"
    n = sum(len(files) for _, _, files in os.walk(p))
    print(f"{root:10s} {n:4d} files")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What's in staging
# MAGIC
# MAGIC | Folder | Contents | Use it for |
# MAGIC |---|---|---|
# MAGIC | `reference/` | patients, payers, payer_transitions (eligibility history), providers, organizations | Dimensions; SCD Type 2 eligibility |
# MAGIC | `clinical/` | encounters, conditions, procedures, medications | Diagnoses and procedures for claims |
# MAGIC | `backfill/` | claims and transactions before Jan 2024, one file per payor | Initial historical load |
# MAGIC | `feeds/` | claims and transactions from Jan 2024, one file per payor per month | Streaming ingestion with Auto Loader |
# MAGIC
# MAGIC Payors: Medicare, Medicaid, Dual Eligible, Humana, UnitedHealthcare, Blue Cross Blue Shield, Aetna, Cigna, Anthem, plus self-pay.
