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

Information is effectively lost at execution time in that turn: the second `tool_use` is present in stored assistant content but has no matching `tool_result` appended in that iteration.

## Q3: Predict the Failure Mode
Naive message-count pruning can eventually cut across protocol-linked message structures (for example, keeping an assistant `tool_use` block but deleting its paired user `tool_result`, or vice versa). Once history is truncated by raw count rather than semantic boundaries, a later `messages.create()` can receive an invalid transcript with orphaned tool blocks and fail validation with a hard API error.

So even if the slice mutation itself is syntactically correct, the pruning strategy is unsafe for agentic histories because message validity depends on block pairing and sequence integrity, not just total list length.

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

This is not the primary fix for the observed miss. In `retrieve_chunks()`, chunks are filtered by `similarity_threshold` before `top_k` slicing. If the specific 619 chunk does not clear threshold for the actual query embedding, increasing `top_k` alone cannot recover it.

Actual root cause in `retrieval.py`: the query embedding path is brittle (`embed_query()` only matches a few literal patterns, else falls back to coarse keyword weighting), and that interacts with a strict threshold (`0.85`) that can drop relevant code-specific chunks before ranking.

Better approach:
- Improve retrieval recall for error-code queries (for example, explicit handling for numeric error codes).
- Tune thresholding so relevant code-specific chunks are not filtered out prematurely.
- Keep `top_k` as a secondary ranking control after candidate quality is improved.
