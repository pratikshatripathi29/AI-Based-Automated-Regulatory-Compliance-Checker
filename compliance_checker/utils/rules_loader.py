# Rules loading utility for AI Compliance Checker.

import json
import os
from typing import List, Dict, Any

# Why store rules in JSON instead of hardcoding them in Python?
# 1. Non-Technical Accessibility: Storing rules in an external JSON file allows legal
#    specialists, compliance officers, and non-programmers to view, adjust, or write new
#    rules without needing to touch or understand Python code.
# 2. Extensibility and Modular Architecture: Separating data from application logic means
#    we can easily swap out or add new regulations (such as CCPA, HIPAA, or ISO 27001)
#    simply by supplying another JSON file, without altering any processing algorithms.
# 3. Portability and Schema Validation: JSON is an industry-standard, language-agnostic
#    data exchange format that can easily be validated, updated via external APIs, or
#    managed across different platforms.


def load_rules(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Loads compliance rules from a JSON file into a Python list of dictionaries.

    Parameters:
        filepath (str, optional): The path to the rules JSON file.
            If None, automatically resolves the default path to 'rules/gdpr_rules.json'.

    Returns:
        List[Dict[str, Any]]: List of rule dictionaries containing rule_id, article,
                              title, requirement, and severity.
    """
    if filepath is None:
        # Resolve the default rules path relative to this file's location:
        # utils/ -> ../rules/gdpr_rules.json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "rules", "gdpr_rules.json")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            rules = json.load(f)
            return rules
    except FileNotFoundError:
        print(f"Error: Rules file not found at '{filepath}'")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON rules file '{filepath}': {e}")
        return []
