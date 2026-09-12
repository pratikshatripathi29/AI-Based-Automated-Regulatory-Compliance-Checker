# Rule matching and semantic similarity analysis against compliance standards.

from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util

# ==============================================================================
# CONFIGURABLE SIMILARITY THRESHOLDS
# ==============================================================================
# Cosine similarity produces a score from 0.0 (completely different) to 1.0 (identical meaning).
# You can adjust these thresholds below to make the compliance checking stricter or more lenient:
COMPLIANT_THRESHOLD = 0.55       # Scores > 0.55 are classified as "Compliant"
AMBIGUOUS_THRESHOLD = 0.35       # Scores between 0.35 and 0.55 are classified as "Weak/Ambiguous"
                                 # Scores < 0.35 are classified as "Missing"


# ==============================================================================
# MACHINE LEARNING CONCEPTS EXPLAINED FOR BEGINNERS
# ==============================================================================
# 1. WHAT IS AN EMBEDDING?
#    Computers do not understand the conceptual meaning of words—they only see sequences of
#    characters. An "embedding" is a way of translating a sentence into a long list of numbers
#    (called a mathematical vector, here with 384 dimensions).
#    A machine learning model reads the text and assigns coordinates in a high-dimensional space.
#    Crucially, sentences that mean similar things end up close to each other in this space,
#    even if they use completely different words!
#    For example:
#      - "We delete your personal data upon request."
#      - "Users have the right to request erasure of their records."
#    These two sentences share few identical words, but their embeddings will be nearly identical
#    in direction because their semantic meaning is the same.
#
# 2. WHAT DOES COSINE SIMILARITY MEASURE?
#    Cosine similarity measures the angle between two embedding vectors in mathematical space:
#      - A score of 1.0 means the two vectors point in the exact same direction (identical meaning).
#      - A score of 0.0 means the vectors are perpendicular / completely unrelated.
#      - In text matching, scores typically range from ~0.10 (unrelated topic) to ~0.85+ (near paraphrase).
#
# 3. WHY USE THRESHOLDS INSTEAD OF EXACT KEYWORD MATCHING?
#    Legal documents and privacy policies are written by many different lawyers, each using their
#    own unique phrasing, structure, and vocabulary. If we used traditional keyword matching
#    (e.g., searching for "Article 17 right to be forgotten"), we would fail to detect policies
#    that fulfill the legal requirement using terms like "request account and data deletion".
#    By using semantic embeddings with similarity thresholds, we can determine:
#      - "Compliant": The policy contains a clause with strong semantic correspondence.
#      - "Weak/Ambiguous": The policy touches on the topic, but might be vague or incomplete.
#      - "Missing": No clause in the document discusses this requirement adequately.
# ==============================================================================

# Global cache for the embedding model using Streamlit's @st.cache_resource
try:
    import streamlit as st
    cache_decorator = st.cache_resource
except ImportError:
    def cache_decorator(fn):
        return fn


@cache_decorator
def get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Loads and caches the SentenceTransformer model in memory.
    Using @st.cache_resource avoids re-downloading or re-initializing the model on every Streamlit rerun.
    """
    return SentenceTransformer(model_name)


def check_compliance(
    document_clauses: List[str],
    rules: List[Dict[str, Any]],
    model: Any = None
) -> List[Dict[str, Any]]:
    """
    Evaluates document clauses against a set of compliance rules using semantic embeddings.

    Parameters:
        document_clauses (List[str]): List of segmented sentences/clauses from the uploaded document.
        rules (List[Dict[str, Any]]): List of rule dictionaries loaded from gdpr_rules.json.
        model (Any, optional): Pre-loaded SentenceTransformer instance. If None, uses cached get_model().

    Returns:
        List[Dict[str, Any]]: A list of result dictionaries, one per rule, containing:
            - rule_id
            - article
            - title
            - requirement
            - severity
            - status ("Compliant", "Weak/Ambiguous", or "Missing")
            - best_matching_clause (the document clause with highest similarity)
            - similarity_score (float score rounded to 4 decimals)
    """
    results = []

    # If there are no rules to check, return an empty list
    if not rules:
        return results

    # If the document has no valid clauses (e.g. empty document or unreadable text),
    # all rules are marked as "Missing" with 0.0 similarity.
    if not document_clauses:
        for rule in rules:
            results.append({
                "rule_id": rule.get("rule_id", ""),
                "article": rule.get("article", ""),
                "title": rule.get("title", ""),
                "requirement": rule.get("requirement", ""),
                "severity": rule.get("severity", ""),
                "status": "Missing",
                "best_matching_clause": "",
                "similarity_score": 0.0
            })
        return results

    # Step 1: Load the sentence embedding model ("all-MiniLM-L6-v2") if not provided
    if model is None:
        model = get_model()

    # Step 2: Convert every document clause into an embedding vector
    clause_embeddings = model.encode(document_clauses, convert_to_tensor=True)

    # Step 3: Convert every rule's "requirement" text into an embedding vector
    rule_requirements = [rule.get("requirement", "") for rule in rules]
    rule_embeddings = model.encode(rule_requirements, convert_to_tensor=True)

    # Step 4: Compute cosine similarity matrix between all rules and all document clauses
    # util.cos_sim returns a 2D tensor of shape [num_rules, num_clauses]
    similarity_matrix = util.cos_sim(rule_embeddings, clause_embeddings)

    # Step 5 & 6: For each rule, find the best matching clause and classify status
    for i, rule in enumerate(rules):
        rule_scores = similarity_matrix[i]

        # Find the index of the highest similarity score
        best_clause_idx = int(rule_scores.argmax().item())
        best_score = float(rule_scores[best_clause_idx].item())
        best_clause = document_clauses[best_clause_idx]

        # Classify based on configurable thresholds
        if best_score > COMPLIANT_THRESHOLD:
            status = "Compliant"
        elif best_score >= AMBIGUOUS_THRESHOLD:
            status = "Weak/Ambiguous"
        else:
            status = "Missing"

        results.append({
            "rule_id": rule.get("rule_id", ""),
            "article": rule.get("article", ""),
            "title": rule.get("title", ""),
            "requirement": rule.get("requirement", ""),
            "severity": rule.get("severity", ""),
            "status": status,
            "best_matching_clause": best_clause,
            "similarity_score": round(best_score, 4)
        })

    return results
