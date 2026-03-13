#!/usr/bin/env python3
"""
debate_orchestrator_generic.py — Generic debate orchestrator
Coordinates the full debate lifecycle: init, evidence, rounds, synthesis.
Uses provider-agnostic tool names; runtime adapter maps to actual tools.
"""

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Options:
    topic: str
    rounds: int = 3
    output_format: str = "full_report"
    language: str = "bilingual"
    domain: str = "general"
    depth: str = "standard"
    mode: str = "balanced"
    speculation: str = "moderate"
    evidence_refresh: str = "hybrid"
    focus: list[str] = field(default_factory=list)
    allow_fallback: bool = True
    min_evidence: int = 10
    source_retries: int = 2
    min_args: int = 2
    min_rebuttals: int = 1
    step_timeout_sec: int = 300

    @classmethod
    def from_config(cls, config_path: str) -> "Options":
        with open(config_path) as f:
            cfg = json.load(f)
        depth_evidence = {"quick": 5, "standard": 10, "deep": 15}
        depth_args = {"quick": 2, "standard": 2, "deep": 3}
        depth = cfg.get("depth", "standard")
        return cls(
            topic=cfg["topic"],
            rounds=cfg.get("round_count", cfg.get("rounds", 3)),
            output_format=cfg.get("output_format", "full_report"),
            language=cfg.get("language", "bilingual"),
            domain=cfg.get("domain", "general"),
            depth=depth,
            mode=cfg.get("mode", "balanced"),
            speculation=cfg.get("speculation_level", "moderate"),
            evidence_refresh=cfg.get("evidence_refresh", "hybrid"),
            focus=cfg.get("focus_areas", []),
            min_evidence=depth_evidence.get(depth, 10),
            min_args=depth_args.get(depth, 2),
        )


@dataclass
class StepResult:
    step_id: str
    success: bool
    error_type: str = ""
    reason: str = ""
    exit_code: Optional[int] = None


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_script(script: str, args: list[str], cwd: str) -> subprocess.CompletedProcess:
    script_dir = Path(__file__).parent
    script_path = script_dir / script
    result = subprocess.run(
        ["bash", str(script_path)] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Script {script} failed: {result.stderr}", file=sys.stderr)
    return result


def append_audit(workspace: str, action: str, details: dict):
    audit_file = os.path.join(workspace, "logs", "audit_trail.jsonl")
    entry = json.dumps({
        "timestamp": timestamp(),
        "action": action,
        "details": details,
    })
    run_script("append-audit.sh", [audit_file, entry], workspace)


def validate_json(filepath: str, schema_type: str) -> bool:
    result = run_script("validate-json.sh", [filepath, schema_type], os.path.dirname(filepath))
    return result.returncode == 0


def validate_debate_report(filepath: str) -> bool:
    result = run_script("validate-debate-report.sh", [filepath], os.path.dirname(filepath))
    return result.returncode == 0


def read_json(filepath: str):
    with open(filepath) as f:
        return json.load(f)


def write_json(filepath: str, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_config(workspace: str, updates: dict):
    config_path = os.path.join(workspace, "config.json")
    config = read_json(config_path)
    config.update(updates)
    config["updated_at"] = timestamp()
    write_json(config_path, config)


# --- Runtime Adapter ---

MODEL_MAP = {
    "claude": {"fast": "sonnet", "balanced": "sonnet", "deep": "opus"},
    "codex": {"fast": "gpt-4o-mini", "balanced": "gpt-4o", "deep": "o1"},
}


def tier_to_model(tier: str, runtime: str) -> str:
    """Map generic tier name to provider-specific model name."""
    return MODEL_MAP.get(runtime, {}).get(tier, tier)


def detect_runtime() -> str:
    """Detect which agent runtime is available. Priority: env override > codex > claude."""
    forced = os.environ.get("DEBATER_RUNTIME", "").strip().lower()
    if forced in {"codex", "claude"}:
        return forced

    for cmd, name in [("codex", "codex"), ("claude", "claude")]:
        if shutil.which(cmd):
            return name
    return "none"


_RUNTIME: Optional[str] = None


def get_runtime() -> str:
    """Cached runtime detection."""
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = detect_runtime()
        print(f"[{timestamp()}] Detected runtime: {_RUNTIME}")
    return _RUNTIME


def dispatch_agent(step_id: str, prompt: str, model_tier: str = "balanced",
                   timeout_sec: int = 300) -> StepResult:
    """
    Execute a step via the detected agent runtime.

    Claude Code  → claude -p <prompt> --model <model>
    Codex        → codex exec <prompt>
    None         → ERROR, returns failure result
    """
    runtime = get_runtime()
    print(f"[{timestamp()}] Executing step: {step_id} (model: {model_tier}, runtime: {runtime})")
    print(f"[{timestamp()}] Prompt length: {len(prompt)} chars")

    model = tier_to_model(model_tier, runtime)

    if runtime == "claude":
        cmd = [
            "claude", "-p", prompt,
            "--model", model,
        ]
    elif runtime == "codex":
        cmd = [
            "codex", "exec",
            "--sandbox", "workspace-write",
            "--color", "never",
            prompt,
        ]
    else:
        msg = "No agent runtime found (need 'claude' or 'codex' in PATH)"
        print(f"[{timestamp()}] ERROR: {msg}", file=sys.stderr)
        return StepResult(step_id=step_id, success=False, error_type="runtime_missing", reason=msg)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if result.returncode != 0:
            print(f"[{timestamp()}] Step {step_id} exited with code {result.returncode}", file=sys.stderr)
            if stderr:
                print(f"[{timestamp()}] stderr: {stderr[:500]}", file=sys.stderr)
            return StepResult(
                step_id=step_id,
                success=False,
                error_type="nonzero_exit",
                reason=(stderr[:500] or "subprocess returned non-zero exit"),
                exit_code=result.returncode,
            )

        success = f"DONE:{step_id}" in stdout
        if success:
            print(f"[{timestamp()}] Step {step_id} completed successfully")
        else:
            print(f"[{timestamp()}] Step {step_id} finished (no DONE marker, exit code {result.returncode})")
            # Runtime may succeed without explicit marker.
            success = result.returncode == 0

        return StepResult(step_id=step_id, success=success, exit_code=result.returncode)

    except subprocess.TimeoutExpired:
        print(f"[{timestamp()}] Step {step_id} TIMED OUT after {timeout_sec}s", file=sys.stderr)
        return StepResult(
            step_id=step_id,
            success=False,
            error_type="timeout",
            reason=f"Step timed out after {timeout_sec}s",
        )
    except FileNotFoundError:
        msg = f"Runtime '{runtime}' not found in PATH"
        print(f"[{timestamp()}] ERROR: {msg}", file=sys.stderr)
        return StepResult(step_id=step_id, success=False, error_type="runtime_missing", reason=msg)


def parallel_exec(tasks: list[tuple[str, str, str, int]]) -> dict[str, StepResult]:
    """
    Execute multiple dispatch_agent tasks in parallel.
    Each task: (step_id, prompt, model_tier, timeout_sec)
    Returns: {step_id: StepResult}
    """
    results: dict[str, StepResult] = {}
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {
            executor.submit(dispatch_agent, sid, prompt, tier, timeout): sid
            for sid, prompt, tier, timeout in tasks
        }
        for future in as_completed(futures):
            sid = futures[future]
            try:
                results[sid] = future.result()
            except Exception as e:
                print(f"[{timestamp()}] Step {sid} raised exception: {e}", file=sys.stderr)
                results[sid] = StepResult(
                    step_id=sid,
                    success=False,
                    error_type="exception",
                    reason=str(e),
                )
    return results


def fail_step(workspace: str, status: str, stage: str, result: StepResult):
    """Record a hard failure and raise to stop orchestration."""
    details = {
        "step_id": result.step_id,
        "stage": stage,
        "error_type": result.error_type or "failed",
        "reason": result.reason,
        "exit_code": result.exit_code,
        "status": status,
    }
    append_audit(workspace, "step_failed", details)
    update_config(workspace, {"status": status})
    raise RuntimeError(f"{result.step_id} failed at {stage}: {result.error_type} {result.reason}")


def require_step(workspace: str, status: str, stage: str, result: StepResult):
    if result.success:
        return
    fail_step(workspace, status, stage, result)


def merge_new_evidence(workspace: str, round_num: int):
    """Merge new_evidence from Pro/Con turns into evidence_store."""
    evidence_path = os.path.join(workspace, "evidence", "evidence_store.json")
    evidence_store = read_json(evidence_path)

    existing_keys = {(e.get("url", ""), e.get("hash", "")) for e in evidence_store}

    for side in ["pro", "con"]:
        turn_path = os.path.join(workspace, "rounds", f"round_{round_num}", f"{side}_turn.json")
        if not os.path.exists(turn_path):
            continue
        turn = read_json(turn_path)
        new_evidence = turn.get("new_evidence", [])
        added = 0
        for item in new_evidence:
            key = (item.get("url", ""), item.get("hash", ""))
            if key not in existing_keys:
                item["discovered_by"] = side
                item["discovered_at_round"] = round_num
                evidence_store.append(item)
                existing_keys.add(key)
                added += 1
        if added > 0:
            print(f"[{timestamp()}] Merged {added} new evidence items from {side}")

    write_json(evidence_path, evidence_store)
    append_audit(workspace, "evidence_merged_from_turn", {
        "round": round_num,
        "total_items": len(evidence_store),
    })


def report_backup_path(workspace: str) -> str:
    return os.path.join(workspace, "reports", "debate_report.pre_final_synthesis.bak.md")


def run_debate(workspace: str, opts: Options):
    """Run the full debate orchestration flow."""
    print(f"[{timestamp()}] Starting debate: {opts.topic}")
    print(f"[{timestamp()}] Rounds: {opts.rounds}, Depth: {opts.depth}, Mode: {opts.mode}")

    # Phase 1: Initialization
    print(f"\n{'='*60}")
    print("PHASE 1: INITIALIZATION")
    print(f"{'='*60}")

    # Step 1a: Source Ingest (broad)
    depth_queries = {"quick": 3, "standard": 5, "deep": 8}
    num_queries = depth_queries.get(opts.depth, 5)
    ingest0 = dispatch_agent(
        "source_ingest_round_0",
        f"Execute source-ingest.md: topic={opts.topic}, mode=broad, round=0, "
        f"depth={opts.depth}, num_queries={num_queries}. "
        f"Workspace: {workspace}",
        model_tier="balanced",
        timeout_sec=opts.step_timeout_sec,
    )
    require_step(workspace, "failed_initialization", "phase1_source_ingest", ingest0)

    # Step 1b: Freshness Check
    freshness0 = dispatch_agent(
        "freshness_check_0",
        f"Execute freshness-check.md: workspace={workspace}",
        model_tier="balanced",
        timeout_sec=opts.step_timeout_sec,
    )
    require_step(workspace, "failed_initialization", "phase1_freshness", freshness0)

    # Step 1c: Verify minimum evidence
    evidence_path = os.path.join(workspace, "evidence", "evidence_store.json")
    if os.path.exists(evidence_path):
        evidence = read_json(evidence_path)
        if len(evidence) < opts.min_evidence:
            print(f"[{timestamp()}] Warning: Only {len(evidence)} evidence items "
                  f"(minimum: {opts.min_evidence}). Retrying ingest...")
            for retry in range(opts.source_retries):
                retry_res = dispatch_agent(
                    f"source_ingest_retry_{retry+1}",
                    f"Execute source-ingest.md: topic={opts.topic}, mode=broad, round=0, "
                    f"broaden keywords. Workspace: {workspace}",
                    model_tier="balanced",
                    timeout_sec=opts.step_timeout_sec,
                )
                require_step(workspace, "failed_initialization", "phase1_source_ingest_retry", retry_res)
                evidence = read_json(evidence_path)
                if len(evidence) >= opts.min_evidence:
                    break

        if len(evidence) < opts.min_evidence:
            insufficient = StepResult(
                step_id="source_ingest_min_evidence_gate",
                success=False,
                error_type="insufficient_evidence",
                reason=f"evidence count {len(evidence)} < minimum {opts.min_evidence}",
            )
            fail_step(workspace, "failed_initialization", "phase1_min_evidence", insufficient)

    update_config(workspace, {"status": "evidence_gathered"})
    append_audit(workspace, "evidence_added", {"round": 0, "mode": "broad"})

    # Phase 2: Debate Rounds
    for round_num in range(1, opts.rounds + 1):
        failed_status = f"failed_round_{round_num}"

        print(f"\n{'='*60}")
        print(f"PHASE 2: ROUND {round_num}/{opts.rounds}")
        print(f"{'='*60}")

        append_audit(workspace, "round_started", {"round": round_num})
        update_config(workspace, {"current_round": round_num, "status": "in_progress"})

        # Step 2a: Per-round evidence refresh
        needs_refresh = (
            opts.evidence_refresh == "per_round" or
            (opts.evidence_refresh == "hybrid" and round_num > 1)
        )
        if needs_refresh:
            print(f"[{timestamp()}] Per-round evidence refresh for round {round_num}")
            prev_ruling_path = os.path.join(
                workspace, "rounds", f"round_{round_num-1}", "judge_ruling.json"
            )
            search_focus = ""
            if os.path.exists(prev_ruling_path):
                ruling = read_json(prev_ruling_path)
                mrps = ruling.get("mandatory_response_points", [])
                flags = ruling.get("causal_validity_flags", [])
                search_focus = json.dumps({"mrps": mrps, "flags": flags})

            refresh_ingest = dispatch_agent(
                f"source_ingest_round_{round_num}",
                f"Execute source-ingest.md: topic={opts.topic}, mode=focused, "
                f"round={round_num}, search_focus={search_focus}. Workspace: {workspace}",
                model_tier="balanced",
                timeout_sec=opts.step_timeout_sec,
            )
            require_step(workspace, failed_status, "phase2_per_round_ingest", refresh_ingest)

            refresh_freshness = dispatch_agent(
                f"freshness_check_round_{round_num}",
                f"Execute freshness-check.md: workspace={workspace}",
                model_tier="balanced",
                timeout_sec=opts.step_timeout_sec,
            )
            require_step(workspace, failed_status, "phase2_per_round_freshness", refresh_freshness)

            append_audit(workspace, "per_round_evidence_ingest", {"round": round_num})

        # Step 2b: Parallel Pro + Con
        print(f"[{timestamp()}] Launching Pro and Con in parallel")
        prev_round_context = ""
        if round_num > 1:
            prev_round_context = (
                f"Read round {round_num-1} data: "
                f"rounds/round_{round_num-1}/pro_turn.json, "
                f"rounds/round_{round_num-1}/con_turn.json, "
                f"rounds/round_{round_num-1}/judge_ruling.json"
            )

        pro_prompt = (
            f"Execute debate-turn.md: side=pro, round={round_num}, topic={opts.topic}, "
            f"mode={opts.mode}, speculation={opts.speculation}, depth={opts.depth}. "
            f"{prev_round_context}. Workspace: {workspace}"
        )
        con_prompt = (
            f"Execute debate-turn.md: side=con, round={round_num}, topic={opts.topic}, "
            f"mode={opts.mode}, speculation={opts.speculation}, depth={opts.depth}. "
            f"{prev_round_context}. Workspace: {workspace}"
        )

        parallel_results = parallel_exec([
            (f"debate_turn_pro_round_{round_num}", pro_prompt, "balanced", opts.step_timeout_sec),
            (f"debate_turn_con_round_{round_num}", con_prompt, "balanced", opts.step_timeout_sec),
        ])

        for side in ["pro", "con"]:
            sid = f"debate_turn_{side}_round_{round_num}"
            require_step(workspace, failed_status, "phase2_debate_turn", parallel_results[sid])

        # Step 2c: Validate outputs
        print(f"[{timestamp()}] Validating turn outputs")
        for side in ["pro", "con"]:
            turn_path = os.path.join(workspace, "rounds", f"round_{round_num}", f"{side}_turn.json")
            if not os.path.exists(turn_path):
                missing_turn = StepResult(
                    step_id=f"validate_{side}_turn_round_{round_num}",
                    success=False,
                    error_type="missing_output",
                    reason=f"Missing turn file: {turn_path}",
                )
                fail_step(workspace, failed_status, "phase2_validate_turn_output", missing_turn)

            if not validate_json(turn_path, f"{side}_turn"):
                print(f"[{timestamp()}] Validation failed for {side}_turn, retrying...")
                validated = False
                for retry in range(2):
                    retry_fix = dispatch_agent(
                        f"debate_turn_{side}_round_{round_num}_retry_{retry+1}",
                        f"Re-execute debate-turn.md: fix JSON validation errors. "
                        f"side={side}, round={round_num}. Workspace: {workspace}",
                        model_tier="balanced",
                        timeout_sec=opts.step_timeout_sec,
                    )
                    if retry_fix.success and validate_json(turn_path, f"{side}_turn"):
                        validated = True
                        break
                if not validated:
                    invalid_turn = StepResult(
                        step_id=f"validate_{side}_turn_round_{round_num}",
                        success=False,
                        error_type="json_validation_failed",
                        reason=f"{side}_turn.json failed schema validation after retries",
                    )
                    fail_step(workspace, failed_status, "phase2_validate_turn_output", invalid_turn)

        append_audit(workspace, "pro_turn_complete", {"round": round_num})
        append_audit(workspace, "con_turn_complete", {"round": round_num})

        # Step 2d: Judge audit
        print(f"[{timestamp()}] Judge audit for round {round_num}")
        judge_result = dispatch_agent(
            f"judge_audit_round_{round_num}",
            f"Execute judge-audit.md: round={round_num}. Workspace: {workspace}",
            model_tier="deep",
            timeout_sec=opts.step_timeout_sec,
        )
        require_step(workspace, failed_status, "phase2_judge_audit", judge_result)

        judge_path = os.path.join(workspace, "rounds", f"round_{round_num}", "judge_ruling.json")
        if not os.path.exists(judge_path):
            missing_judge = StepResult(
                step_id=f"validate_judge_ruling_round_{round_num}",
                success=False,
                error_type="missing_output",
                reason=f"Missing judge ruling file: {judge_path}",
            )
            fail_step(workspace, failed_status, "phase2_validate_judge_output", missing_judge)

        if not validate_json(judge_path, "judge_ruling"):
            invalid_judge = StepResult(
                step_id=f"validate_judge_ruling_round_{round_num}",
                success=False,
                error_type="json_validation_failed",
                reason="judge_ruling.json failed schema validation",
            )
            fail_step(workspace, failed_status, "phase2_validate_judge_output", invalid_judge)

        append_audit(workspace, "judge_ruling_complete", {"round": round_num})

        # Step 2e: Post-round processing
        print(f"[{timestamp()}] Post-round processing")
        claim_update = dispatch_agent(
            f"claim_ledger_update_round_{round_num}",
            f"Execute claim-ledger-update.md: round={round_num}. Workspace: {workspace}",
            model_tier="balanced",
            timeout_sec=opts.step_timeout_sec,
        )
        require_step(workspace, failed_status, "phase2_claim_ledger_update", claim_update)

        merge_new_evidence(workspace, round_num)

        update_config(workspace, {
            "current_round": round_num,
            "status": f"round_{round_num}_complete",
        })

    # Phase 3: Final Output
    print(f"\n{'='*60}")
    print("PHASE 3: FINAL OUTPUT")
    print(f"{'='*60}")

    debate_report_path = os.path.join(workspace, "reports", "debate_report.md")
    report_json_path = os.path.join(workspace, "reports", "final_report.json")
    backup_path = report_backup_path(workspace)

    if os.path.exists(debate_report_path):
        shutil.copyfile(debate_report_path, backup_path)

    final_timeout = max(opts.step_timeout_sec, 900)
    final_res = dispatch_agent(
        "final_synthesis",
        f"Execute final-synthesis.md: workspace={workspace}",
        model_tier="deep",
        timeout_sec=final_timeout,
    )
    require_step(workspace, "failed_final_synthesis", "phase3_final_synthesis", final_res)

    if not os.path.exists(report_json_path):
        missing_json = StepResult(
            step_id="validate_final_report",
            success=False,
            error_type="missing_output",
            reason=f"Missing final_report.json at {report_json_path}",
        )
        fail_step(workspace, "failed_report_validation", "phase3_validate_final_report", missing_json)

    if not validate_json(report_json_path, "final_report"):
        invalid_json = StepResult(
            step_id="validate_final_report",
            success=False,
            error_type="json_validation_failed",
            reason="final_report.json failed schema validation",
        )
        fail_step(workspace, "failed_report_validation", "phase3_validate_final_report", invalid_json)

    if not os.path.exists(debate_report_path):
        missing_md = StepResult(
            step_id="validate_debate_report",
            success=False,
            error_type="missing_output",
            reason=f"Missing debate_report.md at {debate_report_path}",
        )
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, debate_report_path)
        fail_step(workspace, "failed_report_validation", "phase3_validate_debate_report", missing_md)

    if not validate_debate_report(debate_report_path):
        invalid_md = StepResult(
            step_id="validate_debate_report",
            success=False,
            error_type="report_validation_failed",
            reason="debate_report.md failed Section 8 format validation",
        )
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, debate_report_path)
        fail_step(workspace, "failed_report_validation", "phase3_validate_debate_report", invalid_md)

    if os.path.exists(backup_path):
        os.remove(backup_path)

    update_config(workspace, {"status": "complete"})
    append_audit(workspace, "report_generated", {"workspace": workspace})

    print(f"\n[{timestamp()}] Debate complete!")
    print(f"  Report: {debate_report_path}")
    print(f"  JSON:   {report_json_path}")


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <workspace_dir> <config_or_topic> [rounds]")
        sys.exit(1)

    workspace = os.path.abspath(sys.argv[1])
    config_or_topic = sys.argv[2]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    if os.path.isfile(config_or_topic):
        opts = Options.from_config(config_or_topic)
    else:
        # Initialize workspace
        run_script("init-workspace.sh", [workspace, config_or_topic, str(rounds)], ".")
        opts = Options(topic=config_or_topic, rounds=rounds)

    try:
        run_debate(workspace, opts)
    except RuntimeError as e:
        print(f"[{timestamp()}] Debate failed: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
