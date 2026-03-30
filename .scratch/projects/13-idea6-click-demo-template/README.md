# 13-idea6-click-demo-template

Template project directory for implementing Idea #6 with the modern `remora-test` multi-demo structure.

## What Was Created

- New demo package scaffold:
  - `demo/01-click-instant-local-knowledge-graph-boot/`
- Demo manifest/config/checks for isolated clone + wipeable workspace semantics.
- Copied Idea #6 planning artifacts from project 09 into this directory.

## Files Copied From `09-git-clone-knowledge-graph-demo`

- `ASSUMPTIONS.md`
- `CONTEXT.md`
- `DECISIONS.md`
- `DEMO_IDEAS.md`
- `IDEA_6_IMPLEMENTATION_GUIDE.md`
- `IDEA_6_INSTANT_LOCAL_KNOWLEDGE_GRAPH_BOOT_OVERVIEW.md`
- `ISSUES.md`
- `PLAN.md`
- `PROGRESS.md`
- `REPO_DEMO_ANALYSIS.md`

## Notes

- This template intentionally uses a dedicated clone dir and workspace root:
  - clone: `demo/01-click-instant-local-knowledge-graph-boot/repo/pallets-click`
  - workspace: `.remora-01-click-knowledge-graph-boot`
- The new demo uses `port: 8081` to avoid colliding with demo `00_repo_baseline`.
