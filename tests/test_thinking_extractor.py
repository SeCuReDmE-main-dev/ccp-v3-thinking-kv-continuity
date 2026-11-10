"""Unit tests for CCP v3.0 Thinking Extractor & Window 6 Relay Builder."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ccp_v3.thinking_extractor import build_execution_relay_prompt, extract_thinking_handoff


def test_extract_thinking_handoff_and_relay_prompt(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    full_transcript = tmp_path / "transcript_full.jsonl"
    plan_file = tmp_path / "implementation_plan.md"
    plan_file.write_text("# Plan\n", encoding="utf-8")

    steps_compact = [
        {
            "step_index": 1,
            "type": "USER_INPUT",
            "content": "Plan the glymphatic 3-day wake-up",
        },
        {
            "step_index": 2,
            "type": "PLANNER_RESPONSE",
            "thinking": "Truncated preview...",
            "truncated_fields": ["thinking"],
        },
    ]
    steps_full = [
        steps_compact[0],
        {
            "step_index": 2,
            "type": "PLANNER_RESPONSE",
            "thinking": (
                "- Piège mécanique résolu : dans morning_flash_reconciler.py:4638, reconsolidation_pending écrasait days_idle < 3.\n"
                "- Interdit de faire git add . sur la branche 01-morning-kickoff pour éviter d'embarquer les autres fils.\n"
                "- Vérifier pytest -q et contrôler le SHA-256 de runtime_mode.json avant clôture.\n"
            ),
        },
    ]
    transcript.write_text("\n".join(json.dumps(s) for s in steps_compact) + "\n", encoding="utf-8")
    full_transcript.write_text("\n".join(json.dumps(s) for s in steps_full) + "\n", encoding="utf-8")

    handoff = extract_thinking_handoff(transcript, full_transcript)
    assert handoff["schema_version"] == "ccp.v3.0"
    assert handoff["planner_steps_analyzed"] == 1
    w6 = handoff["window_6_thinking_handoff"]
    assert any("morning_flash_reconciler.py" in t for t in w6["resolved_traps"])
    assert any("git add ." in r for r in w6["rejected_branches"])
    assert any("pytest" in g for g in w6["verification_gates"])

    relay_txt = build_execution_relay_prompt("e4ea1fa6-86a7-40fa-ad6b-5aa13f31122a", plan_file, handoff)
    assert "FENÊTRE 6 CCP v3 : THINKING_HANDOFF" in relay_txt
    assert "PURGE KV BÉNÉFIQUE ACTIVÉE" in relay_txt
    assert "e4ea1fa6-86a7-40fa-ad6b-5aa13f31122a" in relay_txt
