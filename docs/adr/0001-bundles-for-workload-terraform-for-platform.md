# ADR-0001: Bundles for workload objects, Terraform for the platform

**Status:** Accepted
**Date:** 2026-10-11

## Context
The project needs Unity Catalog objects (a schema and a raw volume now; jobs and pipelines later). The first version created them inside a setup notebook with `CREATE ... IF NOT EXISTS`. That works, but nothing records what should exist, there's no review step before changes, no way to detect drift, and infrastructure is mixed with data loading.

There are two kinds of resources with different owners and change rates:
- **Platform:** workspace, catalogs, storage credentials and external locations, groups and permissions, compute policies, Key Vault and secret scopes. Owned by a platform team; changes rarely.
- **Workload:** the schema, volumes, jobs and pipelines for one data product. Owned by the data team; changes with the code.

## Options considered
1. **Notebook SQL (`CREATE IF NOT EXISTS`):** simplest; no state, no review, no drift detection.
2. **Terraform for everything:** one tool; but every pipeline change becomes an infrastructure change in a separate repo, which slows the data team.
3. **Terraform for platform, Declarative Automation Bundles for workload:** each layer is managed as code by the team that owns it, deployed from its own repo.

## Decision
Option 3. Workload objects live in `databricks.yml` in this repo and are deployed with `databricks bundle deploy`. Platform resources live in the separate `claims-lakehouse-infra` Terraform repo.

## Consequences
- Pipelines and the objects they need are versioned and deployed together.
- The setup notebook only loads data.
- Two tools to learn and keep in step. The boundary must be clear: the bundle never creates catalogs or grants platform-level access.
- `bundle destroy` deletes the schema and volume, including their data. Use it deliberately.

## Results (fill in later)
