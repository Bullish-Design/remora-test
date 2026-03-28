from __future__ import annotations

import subprocess
import time

from _harness import CheckContext, CheckFailure, CheckResult, run_command


NAME = "check_lsp_startup"


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()
    timeout_s = 8.0
    require_lsp = ctx.require_lsp_bridge

    try:
        from remora.core.model.config import load_config

        config = load_config(ctx.config_path)
        db_path = ctx.project_root / config.infra.workspace_root / "remora.db"
        if not db_path.exists():
            raise CheckFailure(
                f"LSP startup precheck failed: remora database not found at {db_path}. "
                "Run runtime at least once before LSP checks."
            )

        try:
            proc = run_command(
                [
                    "remora",
                    "lsp",
                    "--project-root",
                    str(ctx.project_root),
                    "--config",
                    str(ctx.config_path),
                ],
                prefix=ctx.command_prefix,
                timeout_s=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name=NAME,
                passed=True,
                duration_s=time.time() - started,
                detail=f"LSP server startup appears healthy (process remained running for {int(timeout_s)}s).",
            )

        merged_log = f"{proc.stdout}\n{proc.stderr}"
        if proc.returncode == 0 and "Starting standalone LSP server on stdin/stdout" in merged_log:
            return CheckResult(
                name=NAME,
                passed=True,
                duration_s=time.time() - started,
                detail="LSP server startup appears healthy (server started and exited cleanly on stdin EOF).",
            )

        if "LSP support requires pygls" in merged_log:
            if require_lsp:
                raise CheckFailure("Detected missing LSP dependency (pygls) in strict mode")
            return CheckResult(
                name=NAME,
                passed=True,
                skipped=True,
                skip_reason="LSP dependency missing (pygls)",
                duration_s=time.time() - started,
            )

        raise CheckFailure(
            f"LSP startup check failed with exit code {proc.returncode}. Last log lines:\n{merged_log[-1200:]}"
        )
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
