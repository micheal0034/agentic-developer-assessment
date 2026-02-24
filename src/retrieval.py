"""RAG retrieval pipeline for IT runbook search.

Runbooks are pre-chunked and embedded offline. At query time, the query
is embedded and compared against stored chunk embeddings using cosine
similarity. Results above the similarity threshold are returned, sorted
by relevance.
"""

import math
from dataclasses import dataclass


@dataclass
class RunbookChunk:
    """A single chunk from a runbook document."""

    chunk_id: str
    source_doc: str
    category: str
    content: str
    embedding: list  # pre-computed embedding vector


# ---------------------------------------------------------------
# Pre-chunked runbook database
# Chunks created with a 200-char window and 50-char overlap
# ---------------------------------------------------------------

RUNBOOK_CHUNKS = [
    # --- Network ---
    RunbookChunk(
        chunk_id="net-001-a",
        source_doc="VPN Troubleshooting Guide",
        category="network",
        content=(
            "VPN Connection Issues — General Steps:\n"
            "1. Verify VPN client version is up to date\n"
            "2. Check firewall rules on the endpoint\n"
            "3. Restart network adapter via Device Manager"
        ),
        embedding=[0.92, 0.12, 0.04, 0.02, 0.88, 0.15, 0.06, 0.03],
    ),
    RunbookChunk(
        chunk_id="net-001-b",
        source_doc="VPN Troubleshooting Guide",
        category="network",
        content=(
            "VPN Connection Issues — Error Codes:\n"
            "4. Flush DNS: run ipconfig /flushdns\n"
            "5. Error 619: port 1723 is blocked — check router\n"
            "   settings and contact the network infrastructure team"
        ),
        embedding=[0.85, 0.10, 0.06, 0.03, 0.80, 0.12, 0.08, 0.05],
    ),
    RunbookChunk(
        chunk_id="net-002",
        source_doc="DNS Resolution Playbook",
        category="network",
        content=(
            "DNS Resolution Failures:\n"
            "1. Run nslookup to verify resolution\n"
            "2. Check /etc/hosts for stale entries\n"
            "3. Verify DNS server configuration in network settings\n"
            "4. Clear DNS cache and retry"
        ),
        embedding=[0.78, 0.08, 0.05, 0.04, 0.72, 0.10, 0.07, 0.06],
    ),
    # --- Software ---
    RunbookChunk(
        chunk_id="sw-001",
        source_doc="Office 365 Troubleshooting",
        category="software",
        content=(
            "Excel / Office Application Crashes:\n"
            "1. Clear application cache from %AppData%\n"
            "2. Reinstall via Software Center\n"
            "3. Check RAM usage — Excel needs 2 GB free for large files\n"
            "4. Disable COM add-ins and test again"
        ),
        embedding=[0.08, 0.91, 0.05, 0.03, 0.10, 0.87, 0.07, 0.04],
    ),
    RunbookChunk(
        chunk_id="sw-002",
        source_doc="General Software Issues",
        category="software",
        content=(
            "Software Installation Failures:\n"
            "1. Verify sufficient disk space (> 5 GB free)\n"
            "2. Run installer as administrator\n"
            "3. Check Windows Installer service is running\n"
            "4. Clear temp files from %TEMP% and retry"
        ),
        embedding=[0.06, 0.84, 0.08, 0.04, 0.08, 0.80, 0.10, 0.06],
    ),
    # --- Hardware ---
    RunbookChunk(
        chunk_id="hw-001",
        source_doc="Hardware Diagnostics Guide",
        category="hardware",
        content=(
            "Hardware Diagnostic Procedures:\n"
            "1. Run built-in hardware diagnostics (F12 on boot)\n"
            "2. Update device drivers via Device Manager\n"
            "3. Check for overheating — clean vents and verify fan operation"
        ),
        embedding=[0.04, 0.06, 0.93, 0.03, 0.05, 0.08, 0.90, 0.04],
    ),
    # --- Access ---
    RunbookChunk(
        chunk_id="acc-001",
        source_doc="Access Management Procedures",
        category="access",
        content=(
            "Password and Account Issues:\n"
            "1. Reset password via Active Directory Users and Computers\n"
            "2. Check group policy with gpresult /r\n"
            "3. Verify account is not locked out in AD"
        ),
        embedding=[0.03, 0.05, 0.02, 0.94, 0.04, 0.06, 0.03, 0.91],
    ),
    RunbookChunk(
        chunk_id="acc-002",
        source_doc="SaaS Application Access",
        category="access",
        content=(
            "SaaS Access Provisioning:\n"
            "1. Verify license is assigned in the application admin console\n"
            "2. Check SSO configuration in Okta\n"
            "3. Confirm user is in the correct AD group"
        ),
        embedding=[0.04, 0.07, 0.03, 0.90, 0.05, 0.08, 0.04, 0.87],
    ),
]


# Pre-computed query embeddings for common ticket patterns.
# In production, these would be generated at query time by an embedding model.
QUERY_EMBEDDINGS = {
    "vpn connection error": [0.89, 0.10, 0.05, 0.03, 0.85, 0.12, 0.07, 0.04],
    "salesforce access": [0.05, 0.08, 0.03, 0.88, 0.06, 0.09, 0.04, 0.85],
    "excel crash add-in": [0.07, 0.88, 0.06, 0.04, 0.09, 0.85, 0.08, 0.05],
}


def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def embed_query(query_text):
    """Embed a query string for similarity search.

    Uses pre-computed embeddings for known patterns. For unknown queries,
    generates a category-weighted embedding based on keyword presence.
    """
    query_lower = query_text.lower().strip()

    # Check for a pre-computed embedding
    for pattern, embedding in QUERY_EMBEDDINGS.items():
        if pattern in query_lower or query_lower in pattern:
            return embedding

    # Fallback: category keyword weighting
    categories = ["network", "software", "hardware", "access"]
    base = [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
    for i, cat in enumerate(categories):
        if cat in query_lower:
            base[i] = 0.85
            base[i + 4] = 0.80
    return base


def retrieve_chunks(query_text, top_k=3, similarity_threshold=0.85):
    """Retrieve the most relevant runbook chunks for a query.

    Args:
        query_text: The search query
        top_k: Maximum number of chunks to return
        similarity_threshold: Minimum cosine similarity to include a result

    Returns:
        List of (chunk, score) tuples sorted by relevance
    """
    query_embedding = embed_query(query_text)

    scored = []
    for chunk in RUNBOOK_CHUNKS:
        score = cosine_similarity(query_embedding, chunk.embedding)
        if score >= similarity_threshold:
            scored.append((chunk, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def format_results(chunks_with_scores):
    """Format retrieved chunks as a plain text string for the model."""
    if not chunks_with_scores:
        return "No matching runbook found. Escalate to L2 support."

    parts = []
    for chunk, score in chunks_with_scores:
        parts.append(chunk.content)
    return "\n---\n".join(parts)
