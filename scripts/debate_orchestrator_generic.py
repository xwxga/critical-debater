#!/usr/bin/env python3
"""Generic debate orchestrator for Codex runtime.

Runs a real multi-phase debate workflow (source-ingest -> rounds -> synthesis)
with strict JSON validation and optional fallback policy.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / ".agents/skills/_shared/references/data-contracts.md"
def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s[:max_len] or "debate-topic").strip("-")


def run_cmd(
    cmd: list[str], *, capture: bool = False, timeout_sec: int | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=capture,
        timeout=timeout_sec,
        check=False,
    )


def require_ok(result: subprocess.CompletedProcess[str], context: str) -> None:
    if result.returncode == 0:
        return
    detail = (result.stderr or result.stdout or "").strip()
    raise RuntimeError(f"{context} failed (exit={result.returncode}): {detail[-1000:]}")


@dataclass
class Options:
    topic: str
    rounds: int
    output_format: str
    language: str
    domain: str
    depth: str
    mode: str
    speculation: str
    focus: list[str]
    allow_fallback: bool
    min_evidence: int
    source_retries: int
    min_args: int
    min_rebuttals: int
    codex_model: str | None
    workspace: str | None
    step_timeout_sec: int


class DebateOrchestrator:
    def __init__(self, opts: Options) -> None:
        self.opts = opts
        self.workspace = self._resolve_workspace(opts.workspace)
        self.logs_dir = self.workspace / "logs"
        self.audit_file = self.logs_dir / "audit_trail.jsonl"
        self.config_file = self.workspace / "config.json"
        self.evidence_file = self.workspace / "evidence/evidence_store.json"
        self.claim_ledger_file = self.workspace / "claims/claim_ledger.json"
        self.final_report_file = self.workspace / "reports/final_report.json"
        self.debate_report_file = self.workspace / "reports/debate_report.md"
        self.run_log_file = self.logs_dir / "orchestrator_run.log"

    def _resolve_workspace(self, requested: str | None) -> Path:
        if requested:
            return (ROOT / requested).resolve()
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        ws = ROOT / "debates" / f"{slugify(self.opts.topic)}-{ts}"
        return ws.resolve()

    def append_audit(self, action: str, details: dict) -> None:
        line = json.dumps(
            {"timestamp": now_iso(), "action": action, "details": details},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = run_cmd(["bash", "scripts/append-audit.sh", str(self.audit_file), line], capture=True)
        require_ok(result, f"append_audit({action})")

    def write_config(self, status: str, current_round: int | None = None) -> None:
        with self.config_file.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg.update(
            {
                "rounds": self.opts.rounds,
                "round_count": self.opts.rounds,
                "pro_model": "balanced",
                "con_model": "balanced",
                "judge_model": "deep",
                "domain": self.opts.domain,
                "depth": self.opts.depth,
                "evidence_scope": "mixed",
                "output_format": self.opts.output_format,
                "speculation_level": self.opts.speculation,
                "language": self.opts.language,
                "focus_areas": self.opts.focus,
                "mode": self.opts.mode,
                "status": status,
                "updated_at": now_iso(),
            }
        )
        if current_round is not None:
            cfg["current_round"] = current_round
        with self.config_file.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def init_workspace(self) -> None:
        self.workspace.parent.mkdir(parents=True, exist_ok=True)
        result = run_cmd(
            [
                "bash",
                "scripts/init-workspace.sh",
                str(self.workspace),
                self.opts.topic,
                str(self.opts.rounds),
            ],
            capture=True,
        )
        require_ok(result, "init-workspace")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.run_log_file.write_text("", encoding="utf-8")
        self.write_config(status="initialized", current_round=0)

    def codex_exec(self, step_id: str, prompt: str) -> None:
        cmd = ["codex", "exec", "-C", str(ROOT)]
        if self.opts.codex_model:
            cmd.extend(["--model", self.opts.codex_model])
        cmd.append(prompt)
        print(f"[orchestrator] step={step_id}", flush=True)
        try:
            result = run_cmd(cmd, capture=True, timeout_sec=self.opts.step_timeout_sec)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"step {step_id} timed out after {self.opts.step_timeout_sec}s")
        output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")

        step_log = self.logs_dir / f"{step_id}.codex.log"
        step_log.write_text(output, encoding="utf-8", errors="replace")
        with self.run_log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n===== {step_id} =====\n")
            f.write(output)
            if output and not output.endswith("\n"):
                f.write("\n")

        if result.returncode != 0:
            tail = output[-1200:].strip()
            raise RuntimeError(f"step {step_id} failed (exit={result.returncode}). tail:\n{tail}")

        marker = f"DONE:{step_id}"
        if marker not in output:
            tail = output[-1200:].strip()
            raise RuntimeError(f"step {step_id} missing completion marker `{marker}`. tail:\n{tail}")

        if not self.opts.allow_fallback:
            if re.search(r"(?m)^ERROR:CAPABILITY_UNAVAILABLE\s*$", output):
                raise RuntimeError(f"step {step_id} reported capability unavailable in strict mode")

    def validate_json(self, path: Path, schema: str) -> None:
        result = run_cmd(["bash", "scripts/validate-json.sh", str(path), schema], capture=True)
        require_ok(result, f"validate-json {schema} @ {path}")

    def check_long_output(self, round_idx: int) -> None:
        pro_path = self.workspace / f"rounds/round_{round_idx}/pro_turn.json"
        con_path = self.workspace / f"rounds/round_{round_idx}/con_turn.json"

        with pro_path.open("r", encoding="utf-8") as f:
            pro = json.load(f)
        with con_path.open("r", encoding="utf-8") as f:
            con = json.load(f)

        checks = [
            ("pro.arguments", len(pro.get("arguments", [])), self.opts.min_args),
            ("con.arguments", len(con.get("arguments", [])), self.opts.min_args),
            ("pro.rebuttals", len(pro.get("rebuttals", [])), self.opts.min_rebuttals),
            ("con.rebuttals", len(con.get("rebuttals", [])), self.opts.min_rebuttals),
        ]
        failed = [f"{name}={actual} < {minimum}" for name, actual, minimum in checks if actual < minimum]
        if failed:
            raise RuntimeError(f"round {round_idx} long-output gate failed: {', '.join(failed)}")

    def _strict_line(self) -> str:
        if self.opts.allow_fallback:
            return (
                "Fallback is allowed only when capability is unavailable, and you MUST log "
                "a concrete reason plus fallback_level in your output notes."
            )
        return (
            "Fallback is NOT allowed. If capability is unavailable, print exactly "
            "ERROR:CAPABILITY_UNAVAILABLE and stop this step."
        )

    def _safe_evidence_count(self) -> int:
        if not self.evidence_file.exists():
            return 0
        try:
            with self.evidence_file.open("r", encoding="utf-8") as f:
                evidence = json.load(f)
            if isinstance(evidence, list):
                return len(evidence)
        except Exception:
            return 0
        return 0

    def _build_source_ingest_prompt(self, attempt: int, existing_count: int) -> str:
        append_line = (
            "If evidence_store.json already has items, keep them and append new unique items "
            "(dedupe by url+hash), then rewrite the merged array."
            if existing_count > 0
            else "Write a fresh evidence array."
        )
        return dedent(
            f"""
            Execute skill workflow: source-ingest + freshness-check.

            Topic: {self.opts.topic}
            Workspace: {self.workspace}
            Contract reference: {CONTRACT_PATH}
            Attempt: {attempt}
            Existing evidence count: {existing_count}

            Rules:
            - Real execution only, no fabricated sources.
            - Collect at least {self.opts.min_evidence} evidence items from diverse source types if possible.
            - Prioritize fast completion: search-first collection is acceptable; deep fetch is optional.
            - {append_line}
            - Each evidence item must include:
              evidence_id, source_type, url, publisher, published_at, retrieved_at,
              snippet, hash, credibility_tier, freshness_status, evidence_track,
              social_credibility_flag, verification_priority, corroboration_status.
            - Use ISO-8601 UTC timestamps.
            - Write JSON array to: {self.evidence_file}
            - Update {self.config_file} status to "evidence_gathered".
            - Do not write any files outside this workspace.
            - {self._strict_line()}

            Return one line at end: DONE:source-ingest-attempt-{attempt}
            """
        ).strip()

    def run_source_ingest(self) -> None:
        max_attempts = self.opts.source_retries + 1
        last_error: RuntimeError | None = None

        for attempt in range(1, max_attempts + 1):
            step_id = f"source-ingest-attempt-{attempt}"
            existing_count = self._safe_evidence_count()
            prompt = self._build_source_ingest_prompt(attempt, existing_count)

            try:
                self.codex_exec(step_id, prompt)
                self.validate_json(self.evidence_file, "evidence_item")
            except RuntimeError as exc:
                last_error = exc
                self.append_audit(
                    "source_ingest_attempt_failed",
                    {
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "error": str(exc),
                        "evidence_count": self._safe_evidence_count(),
                    },
                )
                if attempt < max_attempts:
                    continue
                break

            count = self._safe_evidence_count()
            if count >= self.opts.min_evidence:
                self.write_config(status="evidence_gathered", current_round=0)
                self.append_audit(
                    "evidence_ingested",
                    {
                        "count": count,
                        "allow_fallback": self.opts.allow_fallback,
                        "min_evidence": self.opts.min_evidence,
                        "attempts_used": attempt,
                    },
                )
                return

            self.append_audit(
                "source_ingest_attempt_insufficient",
                {
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "count": count,
                    "target": self.opts.min_evidence,
                },
            )

        final_count = self._safe_evidence_count()
        if not self.opts.allow_fallback:
            raise RuntimeError(
                f"source-ingest remained below min_evidence after retries: count={final_count}, "
                f"target={self.opts.min_evidence}, retries={self.opts.source_retries}"
            )

        if last_error is not None:
            self.append_audit(
                "source_ingest_degraded",
                {"reason": str(last_error), "count": final_count, "target": self.opts.min_evidence},
            )
        self.write_config(status="evidence_gathered", current_round=0)
        self.append_audit(
            "evidence_ingested",
            {
                "count": final_count,
                "allow_fallback": self.opts.allow_fallback,
                "min_evidence": self.opts.min_evidence,
                "attempts_used": max_attempts,
            },
        )

    def run_round(self, round_idx: int) -> None:
        round_dir = self.workspace / f"rounds/round_{round_idx}"
        pro_file = round_dir / "pro_turn.json"
        con_file = round_dir / "con_turn.json"
        judge_file = round_dir / "judge_ruling.json"

        prev_context = ""
        if round_idx > 1:
            prev_context = dedent(
                f"""
                Previous context:
                - prior con turn: {self.workspace}/rounds/round_{round_idx - 1}/con_turn.json
                - prior judge ruling: {self.workspace}/rounds/round_{round_idx - 1}/judge_ruling.json
                """
            )

        pro_prompt = dedent(
            f"""
            Execute skill workflow: debate-turn (PRO side).

            Topic: {self.opts.topic}
            Round: {round_idx}
            Mode: {self.opts.mode}
            Workspace files:
            - config: {self.config_file}
            - evidence: {self.evidence_file}
            - claim ledger: {self.claim_ledger_file}
            {prev_context}

            Write valid DebateTurn JSON to: {pro_file}

            Hard constraints:
            - side must be "pro"
            - arguments length >= {self.opts.min_args}
            - rebuttals length >= {self.opts.min_rebuttals}
            - each argument must include non-empty reasoning_chain with all 5 fields
            - each argument must include claim_id using pattern clm_{round_idx}_pro_<index>
            - include mandatory_responses array (can be empty)
            - include historical_wisdom and speculative_scenarios blocks
            - {self._strict_line()}

            Return one line at end: DONE:pro-round-{round_idx}
            """
        ).strip()
        self.codex_exec(f"pro-round-{round_idx}", pro_prompt)
        self.validate_json(pro_file, "pro_turn")

        con_prompt = dedent(
            f"""
            Execute skill workflow: debate-turn (CON side).

            Topic: {self.opts.topic}
            Round: {round_idx}
            Mode: {self.opts.mode}
            Workspace files:
            - config: {self.config_file}
            - evidence: {self.evidence_file}
            - claim ledger: {self.claim_ledger_file}
            - pro turn (same round): {pro_file}
            {prev_context}

            Write valid DebateTurn JSON to: {con_file}

            Hard constraints:
            - side must be "con"
            - arguments length >= {self.opts.min_args}
            - rebuttals length >= {self.opts.min_rebuttals}
            - each argument must include non-empty reasoning_chain with all 5 fields
            - each argument must include claim_id using pattern clm_{round_idx}_con_<index>
            - include mandatory_responses array (can be empty)
            - include historical_wisdom and speculative_scenarios blocks
            - {self._strict_line()}

            Return one line at end: DONE:con-round-{round_idx}
            """
        ).strip()
        self.codex_exec(f"con-round-{round_idx}", con_prompt)
        self.validate_json(con_file, "con_turn")

        judge_prompt = dedent(
            f"""
            Execute skill workflow: judge-audit + evidence-verify.

            Topic: {self.opts.topic}
            Round: {round_idx}
            Workspace files:
            - pro turn: {pro_file}
            - con turn: {con_file}
            - evidence: {self.evidence_file}
            - claim ledger: {self.claim_ledger_file}

            Write valid JudgeRuling JSON to: {judge_file}

            Hard constraints:
            - include round, verification_results, mandatory_response_points, round_summary
            - verify at least {max(2, self.opts.min_args)} claims
            - use claim_id values from pro/con arguments when possible
            - severity labels must be from allowed schema values
            - {self._strict_line()}

            Return one line at end: DONE:judge-round-{round_idx}
            """
        ).strip()
        self.codex_exec(f"judge-round-{round_idx}", judge_prompt)
        self.validate_json(judge_file, "judge_ruling")

        ledger_prompt = dedent(
            f"""
            Execute skill workflow: claim-ledger-update.

            Topic: {self.opts.topic}
            Round: {round_idx}
            Inputs:
            - existing claim ledger: {self.claim_ledger_file}
            - pro turn: {pro_file}
            - con turn: {con_file}
            - judge ruling: {judge_file}

            Task:
            - Upsert claims from pro/con arguments into ClaimItem array.
            - Required fields per item:
              claim_id, round, speaker, claim_type, claim_text, evidence_ids, status,
              last_verified_at, judge_note, mandatory_response, conflict_details.
            - Use status from judge verification where available, else keep "unverified".
            - Keep file as JSON array and preserve older round claims.
            - {self._strict_line()}

            Write output to: {self.claim_ledger_file}
            Return one line at end: DONE:ledger-round-{round_idx}
            """
        ).strip()
        self.codex_exec(f"ledger-round-{round_idx}", ledger_prompt)
        self.validate_json(self.claim_ledger_file, "claim_item")

        self.check_long_output(round_idx)
        self.write_config(status=f"round_{round_idx}_complete", current_round=round_idx)
        self.append_audit(
            "round_complete",
            {
                "round": round_idx,
                "files": {
                    "pro": str(pro_file),
                    "con": str(con_file),
                    "judge": str(judge_file),
                },
            },
        )

    def run_final_synthesis(self) -> None:
        prompt = dedent(
            f"""
            Execute skill workflow: final-synthesis.

            Topic: {self.opts.topic}
            Rounds: {self.opts.rounds}
            Output format: {self.opts.output_format}
            Language: {self.opts.language}
            Workspace: {self.workspace}
            Contract reference: {CONTRACT_PATH}

            Inputs:
            - config: {self.config_file}
            - evidence: {self.evidence_file}
            - claim ledger: {self.claim_ledger_file}
            - rounds directory: {self.workspace}/rounds

            Outputs to write:
            - {self.final_report_file}
            - {self.debate_report_file}

            Hard constraints:
            - final_report.json must include required keys:
              topic, total_rounds, generated_at, report_path, verified_facts,
              probable_conclusions, contested_points, to_verify, scenario_outlook, watchlist_24h.
            - report_path value must be exactly "reports/debate_report.md"
            - Provide substantive content, not placeholders.
            - {self._strict_line()}

            Return one line at end: DONE:final-synthesis
            """
        ).strip()
        self.codex_exec("final-synthesis", prompt)
        self.validate_json(self.final_report_file, "final_report")
        if not self.debate_report_file.exists():
            raise RuntimeError(f"missing required markdown report: {self.debate_report_file}")
        if self.debate_report_file.stat().st_size == 0:
            raise RuntimeError(f"markdown report is empty: {self.debate_report_file}")
        self.write_config(status="complete", current_round=self.opts.rounds)
        self.append_audit(
            "report_generated",
            {
                "final_report": str(self.final_report_file),
                "debate_report": str(self.debate_report_file),
            },
        )

    def run(self) -> None:
        print(f"[orchestrator] workspace={self.workspace}")
        self.init_workspace()
        self.append_audit(
            "orchestrator_started",
            {
                "topic": self.opts.topic,
                "rounds": self.opts.rounds,
                "allow_fallback": self.opts.allow_fallback,
                "min_evidence": self.opts.min_evidence,
                "source_retries": self.opts.source_retries,
                "min_args": self.opts.min_args,
                "min_rebuttals": self.opts.min_rebuttals,
            },
        )

        self.run_source_ingest()
        self.write_config(status="in_progress", current_round=0)

        for round_idx in range(1, self.opts.rounds + 1):
            self.run_round(round_idx)

        self.run_final_synthesis()
        self.append_audit("orchestrator_finished", {"status": "pass"})
        print(f"WORKSPACE={self.workspace.relative_to(ROOT)}")
        print("CHECKS=PASS")


def parse_focus(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_args() -> Options:
    parser = argparse.ArgumentParser(description="Run generic multi-phase debate orchestrator")
    parser.add_argument("topic", help="Debate topic")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output", dest="output_format", default="full_report")
    parser.add_argument("--language", default="bilingual")
    parser.add_argument("--domain", default="auto")
    parser.add_argument("--depth", default="standard")
    parser.add_argument("--mode", default="balanced")
    parser.add_argument("--speculation", default="moderate")
    parser.add_argument("--focus", default="")
    parser.add_argument("--allow-fallback", action="store_true")
    parser.add_argument("--min-evidence", type=int, default=8)
    parser.add_argument("--source-retries", type=int, default=2)
    parser.add_argument("--min-args", type=int, default=3)
    parser.add_argument("--min-rebuttals", type=int, default=2)
    parser.add_argument("--codex-model", default=None)
    parser.add_argument("--workspace", default=None, help="Optional workspace path relative to repo root")
    parser.add_argument("--step-timeout-sec", type=int, default=300)
    ns = parser.parse_args()

    if ns.rounds < 1:
        raise SystemExit("--rounds must be >= 1")
    if ns.min_evidence < 1:
        raise SystemExit("--min-evidence must be >= 1")
    if ns.source_retries < 0:
        raise SystemExit("--source-retries must be >= 0")
    if ns.min_args < 1:
        raise SystemExit("--min-args must be >= 1")
    if ns.min_rebuttals < 0:
        raise SystemExit("--min-rebuttals must be >= 0")
    if ns.step_timeout_sec < 30:
        raise SystemExit("--step-timeout-sec must be >= 30")

    return Options(
        topic=ns.topic,
        rounds=ns.rounds,
        output_format=ns.output_format,
        language=ns.language,
        domain=ns.domain,
        depth=ns.depth,
        mode=ns.mode,
        speculation=ns.speculation,
        focus=parse_focus(ns.focus),
        allow_fallback=bool(ns.allow_fallback),
        min_evidence=ns.min_evidence,
        source_retries=ns.source_retries,
        min_args=ns.min_args,
        min_rebuttals=ns.min_rebuttals,
        codex_model=ns.codex_model,
        workspace=ns.workspace,
        step_timeout_sec=ns.step_timeout_sec,
    )


def main() -> int:
    try:
        opts = parse_args()
        DebateOrchestrator(opts).run()
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
