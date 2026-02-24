# IT Helpdesk Triage Agent — Assessment

## Overview

You have been handed an IT helpdesk triage agent built by a junior developer. The agent is composed of 7 files in the `candidate/` directory.

The agent's goal is to:
1. Accept a raw support ticket
2. Call `search_runbooks` to retrieve relevant troubleshooting steps using a RAG pipeline
3. Classify the ticket into a structured output (category, priority, team, summary)
4. Process multiple tickets in a batch session

Your task is to answer the questions stated below in the deliverables section.

**You do not need to run the code to complete this assessment.** All questions can be answered by reading the provided files and tracing the logic.

---

## Deliverables

Create a file named `solution.md` and provide your responses to the 5 questions below. 

### Q1: Design Choices — Architecture
In `main.py`, the developer deliberately shares `conversation_history` across tickets "so the model can learn classification patterns."
- **Evaluate this design choice.** Is it appropriate for this specific use case?


### Q2: Trace the State 
In `agent.py`, the `triage_ticket` function has a loop to handle `tool_use` requests.
- Read through the loop. What happens if the LLM emits a response containing **two** `tool_use` blocks in the same turn? 
- Trace exactly what messages get appended to `conversation_history` in that scenario.Is there any information lost?

### Q3: Predict the Failure Mode 
To manage context growth, the developer added `_prune_history` to keep only the last `MAX_HISTORY_MESSAGES` (10) messages in the list using slice deletion (`del history_list[:-10]`).
- Even assuming the list mutation is correct, explain why applying naive `len()`-based pruning to an agentic conversation history will eventually cause a hard API rejection on a subsequent `messages.create()` call. 


### Q4: What happens with THIS input? 
A user submits the following ticket:
> "My laptop screen keeps flickering when I connect it to the docking station. Can someone replace the dock?"

- Trace this query through `retrieval.py`. 
- Exactly which runbook chunks will be included in the `format_results` output? (List the `chunk_id`s or write "None").
- Explain *why* you got that result, referencing the specific embedding fallback logic and the `similarity_threshold`.

### Q5: Fix evaluation 
The developer notices that for ticket TKT-001 ("error code 619"), the model classifies the ticket correctly but recommends generic VPN steps instead of the specific fix for 619. 
The developer proposes the following "fix" to the RAG pipeline in `retrieval.py`:
> *"Let's increase `top_k` from 3 to 10 so the model gets all possible VPN troubleshooting steps."*

- Is this fix effective?
- What is the *actual* root cause in `retrieval.py` for why the 619 fix was missed?
- Do you think there's a better way to handle this? If yes, explain your approach concisely.

---


**Expected Time Taken: 60 Minutes**

---

## Submission Process

To submit your assessment, please follow these steps:

1. **Fork this repository**
   - Create a fork of this repository to your personal GitHub account. Add a new `answers.md` file along with any modified code if you choose to fix the issues (fixing the code is optional; answering the questions is required).

2. **Raise a Pull Request**
   - Create a Pull Request from your personal fork back to this repository.

3. **Include Required Documentation**
   - Refer to your specific assessment file for the documentation requirements.

4. **MANDATORY: Include name in the PR**
   - Add your name, email id and the Job Title you appliead for to the PR description so we can identify you


