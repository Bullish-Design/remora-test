# DECISIONS

1. Use source-and-doc-grounded review as primary evidence base.
- Rationale: Runtime command validation in this session hit dependency import limits (`aiosqlite`) in the active shell context.
- Impact: Report emphasizes concrete file-level evidence and explicit capability mapping instead of runtime re-benchmarking.

2. Treat prior `DEMO_REPORT.md` as historical, not authoritative.
- Rationale: remora-v2 has evolved and current naming/contracts in source/tests indicate potential drift from prior conclusions.
- Impact: Report calls out stale-risk explicitly and avoids inheriting older claims as fact.

3. Refactoring guide uses custom local bundle names (`demo-*`) instead of overriding default bundle names.
- Rationale: avoids merge-order ambiguity when both local and default bundles exist in `bundle_search_paths`.
- Impact: intern implementation is simpler, more deterministic, and easier to debug.
