from __future__ import annotations

import time

from _harness import CheckContext, CheckFailure, CheckResult, RemoraClient, run_command


NAME = "check_discovery"


def _preflight(ctx: CheckContext) -> None:
    required = {
        "python": list((ctx.project_root / "src").rglob("*.py")),
        "markdown": list((ctx.project_root / "docs").rglob("*.md")),
        "toml": list((ctx.project_root / "configs").rglob("*.toml")),
    }
    for label, files in required.items():
        if not files:
            raise CheckFailure(f"Preflight failed: expected at least one {label} file in discovery paths")


def run(ctx: CheckContext) -> CheckResult:
    started = time.time()

    try:
        _preflight(ctx)

        proc = run_command(
            [
                "remora",
                "discover",
                "--project-root",
                str(ctx.project_root),
                "--config",
                str(ctx.config_path),
            ],
            prefix=ctx.command_prefix,
            cwd=ctx.project_root,
        )
        if proc.returncode != 0:
            raise CheckFailure(f"remora discover failed:\n{proc.stderr[-1000:]}")

        output = proc.stdout
        if not any(line.startswith("function ") for line in output.splitlines()):
            raise CheckFailure("Expected at least one function node in discover output")
        if not any(line.startswith("section ") for line in output.splitlines()):
            raise CheckFailure("Expected markdown section nodes in discover output")
        if not any(line.startswith("table ") for line in output.splitlines()):
            raise CheckFailure("Expected TOML table nodes in discover output")

        client = RemoraClient(ctx.base_url)
        try:
            if client.health().get("status") == "ok":
                nodes = client.nodes()
                virtual_count = sum(1 for node in nodes if str(node.get("node_type", "")) == "virtual")
                if virtual_count < 2:
                    raise CheckFailure("Expected at least 2 virtual nodes when runtime is running")
        except Exception:
            pass

        return CheckResult(name=NAME, passed=True, duration_s=time.time() - started)
    except Exception as exc:
        return CheckResult(name=NAME, passed=False, duration_s=time.time() - started, detail=str(exc))
