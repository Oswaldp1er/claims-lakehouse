# ADR-0002: Resource ownership model (platform vs. project)

**Status:** Accepted
**Date:** 2026-10-11

## Context
Several projects will run on the same Databricks platform. Some objects are used by only one project; others (catalogs, audit tables, landing zones, conformed reference data) are used by many. If two deployments declare the same object, they conflict, and retiring one project can delete data another project depends on.

## Decision
Every object has exactly **one owner**, and only the owner declares it. Everyone else references it by name (through a variable) and gets access through Unity Catalog grants.

### Decision tree: who owns an object?
1. **Is it infrastructure or governance?** (workspace, catalogs, storage credentials, external locations, groups, compute policies, Key Vault / secret scopes)
   → **Platform** (Terraform, `claims-lakehouse-infra`)
2. **Is it shared by several projects and not produced by any single one of them?** (audit schema, shared landing zone, common reference data)
   → **Platform** (Terraform)
3. **Is it produced by one project, even if others read it?** (e.g., `silver_claims`, `dim_member`)
   → **That project's bundle.** Publish it as a data product: a stable table or view, a documented contract (columns, freshness, quality), and read grants for consumers.
4. **Is it used only inside one project?** (staging tables, checkpoints, intermediate results)
   → **That project's bundle**, not granted to anyone else.

### Deployment order
1. **Platform:** infrastructure, catalogs, shared schemas, common objects, access.
2. **Projects:** their own schemas, tables, volumes, jobs and pipelines, including tables that feed other processes.
3. **Promotion:** when a project-owned object becomes shared, move ownership to the platform. **Adopt it; don't recreate it.** The platform runs `terraform import`, and the project runs `databricks bundle deployment unbind` before removing the object from its `databricks.yml`.

## Consequences
- **Retiring a project is a decision, not a side effect.** By default, `bundle destroy`, or removing a resource from `databricks.yml` and deploying, **deletes the object and its data**. Before retiring a project, check lineage and audit logs for consumers, then retire or transfer each object it owns.
- Consumers depend on published interfaces, not internals, so producers can change internals safely. Breaking changes get a new version with an overlap period.
- Ownership is visible: every object has a group owner and required tags (`domain`, `team`, `data_product`, `criticality`), and Unity Catalog lineage and system tables give the cross-project view.
- **Rule to choose and apply consistently:** this project lets projects own their own schemas. Some organizations have the platform create all schemas for tighter governance. Either works if applied consistently.
