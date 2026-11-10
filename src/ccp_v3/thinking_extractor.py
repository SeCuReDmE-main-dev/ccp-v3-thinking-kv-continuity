"""
CCP v3.0 — Deterministic Thinking Extractor & Cross-Model Relay Prompt Builder.

Extracts `PLANNER_RESPONSE.thinking` blocks from Antigravity JSONL transcripts
(`transcript.jsonl` / `transcript_full.jsonl`) and builds Window 6 (`THINKING_HANDOFF`)
so a faster execution model (e.g., Gemini Flash 3.8 Max) inherits the frontier
planner's reasoning without re-computing or losing subtle architectural traps.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def extract_thinking_handoff(
    transcript_path: Path,
    full_transcript_path: Path | None = None,
    max_items_per_section: int = 8,
) -> dict[str, Any]:
    """
    Parses a JSONL transcript, resolves truncated `thinking` fields from
    `transcript_full.jsonl` when available, and distills Window 6 (`THINKING_HANDOFF`).
    """
    if not transcript_path.is_file():
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    full_lines_by_step: dict[int, dict[str, Any]] = {}
    if full_transcript_path and full_transcript_path.is_file():
        for raw_line in full_transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                obj = json.loads(raw_line)
                step_idx = obj.get("step_index")
                if isinstance(step_idx, int):
                    full_lines_by_step[step_idx] = obj
            except json.JSONDecodeError:
                continue

    thinking_blocks: list[str] = []
    for raw_line in transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            step = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if step.get("type") != "PLANNER_RESPONSE":
            continue
        truncated = step.get("truncated_fields") or []
        step_idx = step.get("step_index")
        if "thinking" in truncated and isinstance(step_idx, int) and step_idx in full_lines_by_step:
            thinking_txt = str(full_lines_by_step[step_idx].get("thinking") or "").strip()
        else:
            thinking_txt = str(step.get("thinking") or "").strip()
        if thinking_txt:
            thinking_blocks.append(thinking_txt)

    resolved_traps: list[str] = []
    rejected_branches: list[str] = []
    verification_gates: list[str] = []

    trap_re = re.compile(r"\b(pi[eè]ge|trap|edge[- ]case|attention|hazard|fix|garde-fou|invariant)\b", re.IGNORECASE)
    reject_re = re.compile(r"\b(never|jamais|interdit|do not|ne pas|reject|avoid|au lieu de)\b", re.IGNORECASE)
    verify_re = re.compile(r"\b(pytest|pyflakes|sha-?256|assert|verify|test_|v[eé]rifier)\b", re.IGNORECASE)

    for block in thinking_blocks:
        for line in block.splitlines():
            clean = re.sub(r"^[\s\-\*\d\.]+", "", line).strip()
            if len(clean) < 20 or len(clean) > 320:
                continue
            if trap_re.search(clean) and clean not in resolved_traps and len(resolved_traps) < max_items_per_section:
                resolved_traps.append(clean)
            if reject_re.search(clean) and clean not in rejected_branches and len(rejected_branches) < max_items_per_section:
                rejected_branches.append(clean)
            if verify_re.search(clean) and clean not in verification_gates and len(verification_gates) < max_items_per_section:
                verification_gates.append(clean)

    return {
        "schema_version": "ccp.v3.0",
        "planner_steps_analyzed": len(thinking_blocks),
        "window_6_thinking_handoff": {
            "resolved_traps": resolved_traps,
            "rejected_branches": rejected_branches,
            "verification_gates": verification_gates,
        },
    }


def build_execution_relay_prompt(
    conversation_id: str,
    plan_path: Path,
    handoff_data: dict[str, Any],
    source_model: str = "Carbon Medium",
    target_model: str = "Gemini Flash 3.8 Max",
) -> str:
    """Formats the ready-to-paste CCP v3.0 relay prompt including Window 6 (`THINKING_HANDOFF`)."""
    w6 = handoff_data.get("window_6_thinking_handoff") or {}
    traps = "\n".join(f"  - {item}" for item in (w6.get("resolved_traps") or ["None recorded"]))
    rejected = "\n".join(f"  - {item}" for item in (w6.get("rejected_branches") or ["None recorded"]))
    gates = "\n".join(f"  - {item}" for item in (w6.get("verification_gates") or ["None recorded"]))

    return (
        f"[RELAIS D'EXÉCUTION CCP v3.0 — {source_model.upper()} -> {target_model.upper()} | PURGE KV BÉNÉFIQUE ACTIVÉE]\n\n"
        f"Tu prends le relais d'exécution chirurgicale dans le fil `{conversation_id}` après approbation du plan `{plan_path}`.\n"
        f"Lis ce plan une seule fois et exécute-le à la lettre (0 stub, 0 pass silencieux).\n\n"
        f"=== FENÊTRE 6 CCP v3 : THINKING_HANDOFF DISTILLÉ DE {source_model.upper()} ===\n"
        f"1. Pièges mécaniques résolus ({len(w6.get('resolved_traps') or [])}) :\n{traps}\n"
        f"2. Branches rejetées / Interdictions ({len(w6.get('rejected_branches') or [])}) :\n{rejected}\n"
        f"3. Portes de vérification obligatoires ({len(w6.get('verification_gates') or [])}) :\n{gates}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CCP v3.0 Thinking Extractor")
    parser.add_argument("--transcript", required=True, type=Path, help="Path to transcript.jsonl")
    parser.add_argument("--full-transcript", required=False, type=Path, help="Optional path to transcript_full.jsonl")
    parser.add_argument("--plan", required=True, type=Path, help="Path to approved implementation_plan.md")
    parser.add_argument("--cid", default="active-thread", help="Conversation UUID")
    args = parser.parse_args()

    handoff = extract_thinking_handoff(args.transcript, args.full_transcript)
    print(build_execution_relay_prompt(args.cid, args.plan, handoff))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
