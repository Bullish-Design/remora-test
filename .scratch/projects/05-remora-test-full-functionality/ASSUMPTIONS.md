# ASSUMPTIONS

1. This project tracks only remora-test changes; upstream remora-v2 changes are tracked separately.
2. The existing constrained mode was added for environment/runtime stability, not product intent.
3. Full-mode behavior should become the default local demo path.
4. Search and LSP may have external dependencies; tests/docs should make dependency failures explicit.
5. Existing unrelated working tree changes (for example `.grail/*`, `pyproject.toml`) are pre-existing and should not be reverted in this project.

