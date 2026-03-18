NO SUBAGENTS: This project is executed directly without using the Task tool.

# 00-example-repo-setup plan

## Goal
Populate this project directory with the standard tracking files, then set up `/home/andrew/Documents/Projects/remora-test` so it is ready to run the remora-v2 demo.

## Steps
1. Create required project template files (`PLAN.md`, `PROGRESS.md`, `CONTEXT.md`, `DECISIONS.md`, `ASSUMPTIONS.md`, `ISSUES.md`).
2. Align repository config with the setup guide (especially `remora.yaml` and `.gitignore`).
3. Run devenv-based dependency sync and remora verification commands.
4. Add a demo smoke-test helper script from the guide.
5. Confirm runtime startup behavior with a bounded run.

## Acceptance criteria
- Standard project template files exist in this project folder.
- `remora.yaml` uses runtime-compatible bundle mapping.
- `.gitignore` ignores `.remora/`.
- `devenv shell -- uv sync --extra dev` succeeds.
- `devenv shell -- remora discover --project-root .` succeeds.
- `remora start` can boot and expose core web APIs during a bounded smoke run.

NO SUBAGENTS: Never use the Task tool for this project.
