"""Response parsing for structured triage output."""

import re

DEFAULT_VALUES = {
    "category": "other",
    "priority": "medium",
    "assigned_team": "L1",
    "summary": "Unable to parse model response",
}


def parse_triage_response(raw_text):
    """Parse the model's structured response into a dict.

    Uses regex to extract labelled fields. Falls back to defaults
    for any field the model doesn't include.
    """
    result = {}

    for field in ["CATEGORY", "PRIORITY", "ASSIGNED_TEAM", "SUMMARY"]:
        match = re.search(rf"{field}:\s*(.+)", raw_text)
        if match:
            result[field.lower()] = match.group(1).strip()
        else:
            result[field.lower()] = DEFAULT_VALUES[field.lower()]

    return result
