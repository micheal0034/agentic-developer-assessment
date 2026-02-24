"""Configuration for the IT Helpdesk Triage Agent."""

import anthropic

client = anthropic.Anthropic()

# Model settings
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024

# Conversation management
# Keep the last N messages when pruning history to manage context growth.
MAX_HISTORY_MESSAGES = 10

# RAG retrieval settings
SIMILARITY_THRESHOLD = 0.85
RETRIEVAL_TOP_K = 3
