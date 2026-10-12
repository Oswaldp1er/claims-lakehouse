# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Set up Unity Catalog objects and unpack the synthetic data
# MAGIC
# MAGIC Run this once after uploading `claims_lakehouse_data.zip`.
# MAGIC
# MAGIC 1. Creates a schema and a volume in Unity Catalog.
# MAGIC 2. Unzips the data into `staging/` inside the volume.
# MAGIC 3. Creates an empty `landing/` folder. This is where payor feed files "arrive";
# MAGIC    notebook `01_drip_feed` copies them in month by month for Auto Loader to pick up.
# MAGIC
# MAGIC **Before running:** in Catalog Explorer, open the volume created by the first cell
# MAGIC (`<catalog>.<schema>.raw`), create a folder named `upload`, and upload the zip there.
# MAGIC Run the first two cells, upload the zip, then run the rest.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Catalog")
dbutils.widgets.text("schema", "claims_lakehouse", "Schema")
dbutils.widgets.text("volume", "raw", "Volume")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
volume = dbutils.widgets.get("volume")
vol_path = f"/Volumes/{catalog}/{schema}/{volume}"
print(vol_path)

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema} COMMENT 'Claims lakehouse practice project (synthetic Synthea data, no PHI)'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume} COMMENT 'Raw files: uploads, staging, and landing zone for payor feeds'")
dbutils.fs.mkdirs(f"{vol_path}/upload")
print(f"Ready. Upload claims_lakehouse_data.zip to {vol_path}/upload/ then run the next cells.")

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
