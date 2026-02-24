"""Tool definitions and implementations for the triage agent."""

from retrieval import retrieve_chunks, format_results
from config import SIMILARITY_THRESHOLD, RETRIEVAL_TOP_K

# Audit log — accumulates tool call records for compliance reporting
_audit_log = []

TOOLS = [
    {
        "name": "search_runbooks",
        "description": (
            "Search the internal IT runbook database for troubleshooting "
            "steps relevant to a support ticket."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The unique ID of the support ticket",
                },
                "query": {
                    "type": "string",
                    "description": "Search query describing the technical issue",
                },
            },
            "required": ["ticket_id", "query"],
        },
    }
]


def search_runbooks(params):
    """Execute a runbook search and log the query for audit compliance."""
    ticket_id = params.get("ticket_id", "UNKNOWN")
    query = params.get("query", "")

    _audit_log.append({"ticket_id": ticket_id, "query": query})

    results = retrieve_chunks(
        query_text=query,
        top_k=RETRIEVAL_TOP_K,
        similarity_threshold=SIMILARITY_THRESHOLD,
    )
    return format_results(results)


def get_audit_log():
    """Return the audit log for compliance reporting."""
    return list(_audit_log)
