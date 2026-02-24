# IT Helpdesk Triage Agent - Assessment Answers

## Q1: Design Choices - Architecture
Sharing `conversation_history` across tickets in `main.py` is appropriate for this batch-triage workflow. The approach allows the model to carry forward prior classification context and improve consistency across sequential tickets in the same run. For this use case, preserving shared history is a deliberate state-management choice.

## Q2: Trace the State
If the model emits two `tool_use` blocks in one assistant turn, `triage_ticket` executes only the first one.

Reason:
- The code uses `next(b for b in response.content if b.type == "tool_use")`, which returns only the first matching block.
- It appends the full assistant response (`response.content`) to `conversation_history`.
- It appends one user `tool_result` tied to that first `tool_use.id`.
- Then it calls `messages.create()` again.

So the appended sequence is:
1. User ticket message (already appended before first model call)
2. Assistant message containing both `tool_use` blocks
3. User message containing one `tool_result` for the first `tool_use`

The transcript still contains the full assistant content, and the loop intentionally handles one tool execution per cycle.

## Q3: Predict the Failure Mode
In this implementation style, naive `len()`-based pruning with `del history_list[:-MAX_HISTORY_MESSAGES]` does not inherently force a hard API rejection. Pruning can reduce context quality and may orphan related blocks, but this request pattern can still proceed because the API can ignore malformed or unmatched portions. So the practical impact here is degraded coherence/grounding risk, not guaranteed hard failure.

## Q4: What happens with THIS input?
Ticket:
> "My laptop screen keeps flickering when I connect it to the docking station. Can someone replace the dock?"

Trace through `retrieval.py`:
- `embed_query()` checks precomputed patterns:
  - `"vpn connection error"`
  - `"salesforce access"`
  - `"excel crash add-in"`
- None match this ticket.
- Fallback then checks category keywords (`network`, `software`, `hardware`, `access`) in the raw query.
- None of those literal words appear in the ticket, so it returns the unchanged uniform base embedding `[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]`.
- `retrieve_chunks()` computes cosine similarity for each runbook chunk, but all scores are below `similarity_threshold = 0.85`.
- Therefore no chunks pass filtering.

Exact runbook chunks included in `format_results` output: **None**.

Resulting tool output text:
`No matching runbook found. Escalate to L2 support.`

## Q5: Fix evaluation
Proposed fix: increase `top_k` from 3 to 10.

This is not effective as the primary fix in this setup. Retrieval first filters by `similarity_threshold`; only then does `top_k` limit survivors. So if the relevant chunk is excluded before slicing, increasing `top_k` alone does not recover it.

Actual root cause in `retrieval.py`: retrieval behavior is dominated by embedding/fallback and threshold interaction for the query form, rather than by a too-small `top_k` alone.

Better approach:
- Improve retrieval recall for error-code queries (for example, explicit handling for numeric error codes).
- Tune threshold logic so relevant code-specific chunks are not filtered out prematurely.
- Keep `top_k` as a secondary ranking control after candidate quality is improved.
