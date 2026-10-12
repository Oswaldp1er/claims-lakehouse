# Roadmap

Each milestone maps to a week in the 90-day plan. Check items off as they're merged.

## Milestone 0: Setup (Oct 19–25, 2026)
- [ ] Databricks Free Edition workspace created
- [x] Repo created on GitHub
- [ ] Repo connected to Databricks (Git folder)
- [ ] Databricks CLI installed; bundle deployed (schema + raw volume as code)
- [ ] Synthetic data uploaded; notebook 00 run successfully
- [ ] First month delivered with notebook 01

## Milestone 1: Streaming bronze → silver (Oct 26 – Nov 1)
- [ ] Auto Loader (`cloudFiles`) ingests `landing/claims` and `landing/claims_transactions` into bronze Delta tables, with file name and ingest time columns
- [ ] Checkpoints and `trigger(availableNow=True)`; re-running causes no duplicates
- [ ] Silver claims built with an idempotent `MERGE` (latest version of each claim wins)
- [ ] Simulated late-arriving and corrected claims handled correctly

## Milestone 2: dbt gold layer (Nov 2–8)
- [ ] dbt-databricks project: `fct_claims`, `dim_member`, `dim_provider`, `dim_payer`, `dim_date`
- [ ] SCD Type 2 member eligibility from `payer_transitions` (dbt snapshot)
- [ ] Tests (unique, not_null, relationships) and generated docs

## Milestone 3: Declarative pipeline (Nov 23–29)
- [ ] One pipeline rebuilt in Lakeflow Declarative Pipelines (DLT) with expectations (warn / drop / fail)
- [ ] Short write-up: DLT vs. jobs + notebooks vs. dbt

## Milestone 4: Terraform and Data Vault (Nov 30 – Dec 6)
- [ ] Terraform (Databricks provider) manages schema, volume, grants and one job
- [ ] Data Vault model for one subject area (hub_member, hub_claim, link_claim_member, satellites)

## Milestone 5: Architecture decision records (Dec 7–13)
- [ ] ADR-0001 and ADR-0002 written (see `docs/adr/0000-template.md`)

## Milestone 6: Data for AI (Dec 14–20)
- [ ] Member risk feature table in Unity Catalog
- [ ] Simple model tracked in MLflow
- [ ] Column masks and lineage for sensitive fields
