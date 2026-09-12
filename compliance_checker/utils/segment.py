# Document segmentation and clause chunking utilities.

import re
from typing import List


def segment_text(text: str) -> List[str]:
    """
    Splits a document text string into a list of clauses/sentences.

    Splitting is performed on sentence boundaries (. ! ?) and paragraph breaks.
    Very short fragments (under 5 words) are filtered out to eliminate noise such
    as page numbers, isolated section codes, or stray punctuation.

    Parameters:
        text (str): The raw text extracted from a document.

    Returns:
        List[str]: A list of clean, meaningful clauses (each having 5 or more words).
    """
    if not text or not isinstance(text, str):
        return []

    # Normalize line endings
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split on sentence boundaries (period, exclamation, or question mark followed by whitespace)
    # or line/paragraph breaks (\n+)
    raw_clauses = re.split(r'(?<=[.!?])\s+|\n+', normalized_text)

    cleaned_clauses = []
    for clause in raw_clauses:
        # Collapse multiple whitespace characters into single spaces and trim
        clause_clean = " ".join(clause.split()).strip()

        # Count words in the clause
        words = clause_clean.split()

        # Filter out very short fragments under 5 words (e.g., page numbers, titles, noise)
        if len(words) >= 5:
            cleaned_clauses.append(clause_clean)

    return cleaned_clauses
