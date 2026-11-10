# CCP v3.0 — Context Continuity Protocol: Thinking Handoff & Beneficial KV-Cache Purge

**Author:** Jean-Sébastien Beaulieu ([ORCID: 0009-0007-2904-0443](https://orcid.org/0009-0007-2904-0443)) — SecuredMe Research Lab  
**Foundational Reference:** *HUMAN.md & Context Continuity Protocol* — [Zenodo DOI: 10.5281/zenodo.22699683](https://doi.org/10.5281/zenodo.22699683)  
**Status:** Public Reference Specification & Extractor (`v3.0.0`)

---

## 1. Why CCP v3.0? The Cross-Model Handoff & Thinking Budget Paradox

When orchestrating multi-hour engineering sessions across heterogeneous frontier models:
1. **Lowering the thinking effort of a frontier planner (`Carbon High/Medium -> Carbon Low/Min`) is a FinOps anti-pattern:** the heavy model still consumes high per-token rates while losing the multi-turn reasoning depth required for complex code architecture, forcing a second expensive pass at `Medium`.
2. **Switching from a frontier planner (`Carbon Medium / Argon Medium`) to a high-speed execution model (`Gemini Flash 3.8 Max`) triggers a full KV-Cache invalidation**, because KV tensors are physically bound to model weights $(W_Q, W_K, W_V)$ and layer geometry.
3. **Prior `PLANNER_RESPONSE.thinking` blocks are never re-sent in raw chat history.** Without a structured handoff, the incoming execution model receives the surface `implementation_plan.md` but loses the subtle edge-case deductions, rejected dead-ends, and invariant constraints discovered during the planner's deep reasoning phase.

**CCP v3.0 turns this physical KV-Cache reset into a Beneficial KV Purge:**
- It strips 100% of exploratory noise from the planning phase (`DeepSearch` dead-ends, `/grill-me` Q&A iterations, draft revisions).
- It distills the planner's `thinking` chain-of-thought into **Window 6 (`THINKING_HANDOFF`)**, giving the execution model (`Gemini Flash 3.8 Max`) a clean, deterministic prompt with zero reasoning re-computation.

---

## 2. The 4-Phase Multi-Model Pipeline

| Phase | Cognitive Role | Target Model Tier | Token / KV Profile |
| :--- | :--- | :--- | :--- |
| **Phase 1 — DeepSearch & Scouting** | Codebase exploration, AST mapping, log harvesting | Lightweight Fast Model (`Flash`) | High read volume, disposable context |
| **Phase 2 — Architectural Brainstorming** | Trade-off analysis, `/grill-me` Socratic alignment | Frontier Planner (`Carbon / Argon Medium`) | Deep reasoning, high `thinking` density |
| **Phase 3 — Deterministic Planning** | Authoring `implementation_plan.md` + `THINKING_HANDOFF` | Frontier Planner (`Carbon / Argon Medium`) | Crystallizes all invariants & edge cases |
| **Phase 4 — Surgical Execution** | Step-by-step code & test implementation (`0 stub`) | High-Speed Executor (`Gemini Flash 3.8 Max`) | **Beneficial KV Purge** + Window 6 Relay |

---

## 3. The 6 Hermetic Windows of a CCP v3.0 Capsule

```text
+-----------------------------------------------------------------------+
|  CCP v3.0 HERMETIC CAPSULE (6 WINDOWS)                                |
+-----------------------------------------------------------------------+
|  [Window 1] IDENTITY_LINEAGE      Thread UUID, Genesis CID, Paternity |
|  [Window 2] IMMUTABLE_INVARIANTS  [SEALED] rules, SHA-256 locks       |
|  [Window 3] GROUND_TRUTH_T        Verified files on disk & tests (T)  |
|  [Window 4] OPEN_HORIZON_I        Explicit backlog & 4-month debt (I) |
|  [Window 5] EXECUTION_CONTRACT    Approved implementation_plan.md URI |
|  [Window 6] THINKING_HANDOFF      Distilled CoT from Planner thinking |
+-----------------------------------------------------------------------+
```

### Window 6 (`THINKING_HANDOFF`) Structure
Extracted deterministically from `transcript.jsonl` / `transcript_full.jsonl` (`PLANNER_RESPONSE.thinking`):
- **`resolved_traps`**: Subtle mechanical traps, line-level hazards, and edge cases solved during the planner's reasoning.
- **`rejected_branches`**: Architectural dead-ends explicitly ruled out (so the executor never re-explores them).
- **`verification_gates`**: Exact commands, SHA-256 invariants, and unit test assertions required before completion.

---

## 4. Quickstart

```bash
pytest tests/ -q
python -m src.ccp_v3.thinking_extractor --transcript path/to/transcript.jsonl --plan path/to/implementation_plan.md
```
