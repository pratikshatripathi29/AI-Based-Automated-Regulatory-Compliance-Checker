# Compliance report generation and scoring summary utilities.

from typing import List, Dict, Any
from fpdf import FPDF

# Severity weights: High severity misses hurt the compliance score more than low severity misses
SEVERITY_WEIGHTS = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0
}

# Status score multipliers:
# Compliant = 100% of the rule's points
# Weak/Ambiguous = 50% partial credit
# Missing = 0% credit
STATUS_MULTIPLIERS = {
    "Compliant": 1.0,
    "Weak/Ambiguous": 0.5,
    "Missing": 0.0
}


def generate_score(results: List[Dict[str, Any]]) -> float:
    """
    Calculates an overall compliance percentage (0.0 to 100.0), weighted by rule severity.

    High severity requirements (weight: 3.0) impact the score more heavily than medium (2.0)
    or low (1.0) requirements. Full points are awarded for Compliant, 50% for Weak/Ambiguous,
    and 0% for Missing.

    Parameters:
        results (List[Dict[str, Any]]): List of compliance result dictionaries.

    Returns:
        float: The weighted compliance percentage rounded to 1 decimal place.
    """
    if not results:
        return 0.0

    total_possible = 0.0
    earned_points = 0.0

    for item in results:
        severity = str(item.get("severity", "medium")).lower()
        weight = SEVERITY_WEIGHTS.get(severity, 2.0)

        status = item.get("status", "Missing")
        multiplier = STATUS_MULTIPLIERS.get(status, 0.0)

        total_possible += weight
        earned_points += (weight * multiplier)

    if total_possible == 0.0:
        return 0.0

    score_percentage = (earned_points / total_possible) * 100.0
    return round(score_percentage, 1)


def generate_pdf_report(results: List[Dict[str, Any]], score: float) -> bytes:
    """
    Generates a clean, single-page PDF report summarizing GDPR compliance results.

    Parameters:
        results (List[Dict[str, Any]]): The list of evaluated rule result dictionaries.
        score (float): The overall weighted compliance score percentage.

    Returns:
        bytes: Binary PDF file data suitable for direct download.
    """
    # Create an A4 portrait PDF document with 12mm margins
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Document Header Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "AI Compliance Checker", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 7, "GDPR Regulatory Compliance Audit Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Score Summary Banner Box
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    banner_y = pdf.get_y()
    pdf.rect(12, banner_y, 186, 16, style="FD")
    pdf.set_xy(12, banner_y + 3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, f"Overall Compliance Score: {score:.1f}% (Weighted by Severity)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(7)

    # Table Column Headers
    # Total width = 106 + 42 + 38 = 186mm (matches 186mm printable width)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(226, 232, 240)
    pdf.set_text_color(15, 23, 42)
    pdf.set_draw_color(203, 213, 225)
    pdf.cell(106, 9, "  Rule Title", border=1, fill=True)
    pdf.cell(42, 9, "Status", border=1, fill=True, align="C")
    pdf.cell(38, 9, "Severity", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    # Table Data Rows
    pdf.set_font("Helvetica", "", 9)
    for rule in results:
        title = rule.get("title", "Unknown Rule")
        status = rule.get("status", "Missing")
        severity = str(rule.get("severity", "medium")).upper()

        # Rule Title Cell
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(15, 23, 42)
        # Truncate title if extremely long to fit cleanly
        display_title = title if len(title) <= 52 else title[:49] + "..."
        pdf.cell(106, 8, f"  {display_title}", border=1)

        # Status Cell (Color-coded)
        if status == "Compliant":
            pdf.set_fill_color(220, 252, 231)   # Soft green
            pdf.set_text_color(22, 101, 52)      # Dark green text
        elif status == "Weak/Ambiguous":
            pdf.set_fill_color(254, 249, 195)   # Soft yellow
            pdf.set_text_color(133, 77, 14)      # Dark yellow text
        else:
            pdf.set_fill_color(254, 226, 226)   # Soft red
            pdf.set_text_color(153, 27, 27)      # Dark red text

        pdf.cell(42, 8, status, border=1, fill=True, align="C")

        # Severity Cell
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(38, 8, severity, border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    # Return raw PDF bytes
    return bytes(pdf.output())
