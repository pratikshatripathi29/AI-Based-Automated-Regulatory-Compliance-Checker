# AI-Based Automated Compliance Checker
http://regulatory-compliance-checker-pt.streamlit.app/
An AI-powered tool that scans a document (privacy policy, contract, SOP, etc.) and checks it against a set of regulatory requirements — clause by clause — flagging what's compliant, what's weak, and what's missing, along with an overall compliance score and a downloadable report.

This prototype is configured for GDPR compliance checking but is built so the rule base can be swapped for another regulation (HIPAA, AML/KYC, GMP) with minimal changes.

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Usage](#usage)
- [Rule Base](#rule-base)
- [Configuration](#configuration)
- [Testing & Evaluation](#testing--evaluation)
- [Limitations & Future Work](#limitations--future-work)
- [License](#license)

---

## Problem Statement
Regulated industries (finance, healthcare, pharma, data privacy) must ensure that internal documents, contracts, and policies satisfy legal requirements. Manual compliance review is slow, expensive, and error-prone, especially as regulations change and document volume grows. This project automates a first-pass compliance review using natural language processing, so a compliance officer can quickly see which requirements are addressed and which need attention, rather than reading every document line by line from scratch.

---

## How It Works
1. **Upload a document** (`.pdf`, `.docx`, or `.txt`).
2. The app **extracts the raw text** from the file.
3. The text is **split into clauses** (sentences and paragraph breaks).
4. Each clause is **compared against a list of regulatory requirements using sentence embeddings** — a technique that captures the meaning of text, not just keywords, so a clause can match a rule even if it uses different wording.
5. Each rule is marked **Compliant**, **Weak/Ambiguous**, or **Missing** based on how closely the best-matching clause aligns with it.
6. Results are shown as a **color-coded table with an overall weighted compliance score**, and can be **downloaded as a PDF report**.

---

## Architecture

```
Uploaded Document (PDF / DOCX / TXT)
            │
            ▼
 Text Extraction (PyPDF2 / python-docx)
            │
            ▼
 Clause Segmentation (regex-based sentence splitting)
            │
            ▼
 Rule Base (rules/gdpr_rules.json)
            │
            ▼
 Matching Engine (Sentence-BERT embeddings + cosine similarity)
            │
            ▼
 Classification (Compliant / Weak-Ambiguous / Missing)
            │
            ▼
 Scoring (severity-weighted compliance %)
            │
            ▼
 Streamlit UI + Downloadable PDF Report
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| **Frontend / App framework** | Streamlit |
| **Language** | Python 3.10+ |
| **Document parsing** | PyPDF2, python-docx |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) |
| **Similarity scoring** | scikit-learn / PyTorch (cosine similarity) |
| **Data handling** | pandas, numpy |
| **Report generation** | fpdf2 |
| **Optional AI explanations** | Anthropic API |

---

## Project Structure

```
compliance_checker/
│
├── app.py                 # Main Streamlit application (entry point)
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
│
├── rules/
│   └── gdpr_rules.json    # Regulatory rule base (editable JSON)
│
├── utils/
│   ├── __init__.py
│   ├── extract_text.py    # Reads text out of PDF/DOCX/TXT files
│   ├── segment.py         # Splits document text into clauses
│   ├── rules_loader.py    # Loads the rule base JSON
│   ├── matcher.py         # Embedding-based compliance matching engine
│   ├── report.py          # Compliance scoring + PDF report generation
│   └── llm_explainer.py   # (Optional) AI-generated plain-English explanations
│
└── sample_docs/
    └── sample_privacy_policy.txt # Example document for demos/testing
```

---

## Installation

### Prerequisites
Python 3.10 or higher installed on your machine.

1. **Clone or download this project folder**, then open a terminal inside it:
   ```bash
   cd compliance_checker
   ```

2. **Create a virtual environment** (keeps this project's packages separate from everything else on your machine):
   ```bash
   python -m venv venv
   ```

3. **Activate it**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **Mac/Linux**:
     ```bash
     source venv/bin/activate
     ```
   *You'll know it worked when your terminal prompt shows `(venv)` at the start.*

4. **Install all required packages**:
   ```bash
   pip install -r requirements.txt
   ```
   *The first install may take a few minutes since `sentence-transformers` pulls in a machine learning backend.*

5. *(Optional, for Stage 9 AI explanations only)* **Set your Anthropic API key as an environment variable**:
   - **Windows**:
     ```cmd
     set ANTHROPIC_API_KEY=your-key-here
     ```
   - **Mac/Linux**:
     ```bash
     export ANTHROPIC_API_KEY=your-key-here
     ```
   *The app runs fully without this — it just skips the AI-generated explanations and shows similarity scores instead.*

---

## Running the App

With the virtual environment activated:
```bash
streamlit run app.py
```

This prints a local URL (usually `http://localhost:8501`) and should open automatically in your browser. If not, copy the URL into your browser manually.

- To stop the app, go back to the terminal and press `Ctrl+C`.
- Next time you want to run it, you only need to reactivate the virtual environment (Step 3 above) and run `streamlit run app.py` again — no need to reinstall packages unless `requirements.txt` changes.

---

## Usage
1. Open the app in your browser.
2. Upload a document using the file uploader, or use one of the built-in sample documents from the sidebar.
3. Click **"Run Compliance Check"**.
4. Review the results:
   - **Overall weighted compliance score** at the top.
   - **A color-coded table**: green = Compliant, yellow = Weak/Ambiguous, red = Missing.
   - **Expand any row** to see the exact document clause the AI matched against that rule, and its similarity score.
5. Click **"Download Report (PDF)"** to save a summary you can share or submit.

---

## Rule Base

Rules live in `rules/gdpr_rules.json` as a list of objects:
```json
{
  "rule_id": "GDPR_Art17",
  "article": "Article 17",
  "title": "Right to Erasure",
  "requirement": "The document must describe the individual's right to request the deletion or removal of their personal data without undue delay.",
  "severity": "high"
}
```

To adapt this project to a different regulation (HIPAA, AML, GMP, etc.), replace this file with a new set of rules in the same format — no other code changes are required.

---

## Configuration

Similarity thresholds that decide Compliant / Weak / Missing status live at the top of `utils/matcher.py`:
```python
COMPLIANT_THRESHOLD = 0.55
AMBIGUOUS_THRESHOLD = 0.35
```

- **Raise these** to make the checker stricter.
- **Lower them** to make it more lenient.
- Severity weights used in scoring live in `utils/report.py`.

---

## Testing & Evaluation

To evaluate accuracy:
1. Collect several real or written test documents (a mix of compliant and non-compliant).
2. Manually review each one yourself and note which rules you believe are satisfied — this is your "ground truth."
3. Run each document through the app and compare its output to your manual assessment.
4. Report the match rate (e.g., *"the system agreed with manual review on X out of Y rule checks across test documents"*) as an accuracy measure in your project report.

---

## Limitations & Future Work
- **Semantic similarity, not legal reasoning**: The matching engine detects whether a clause addresses a topic, not whether it is legally sufficient. A clause can score "Compliant" while still being legally weak.
- **Rule base is a simplified starting point**: The included GDPR rules are illustrative, not exhaustive or lawyer-reviewed. A production system would need rules validated by legal experts.
- **No OCR support yet**: Scanned (image-only) PDFs won't extract text correctly; a future version could add OCR (e.g., `pytesseract`).
- **Single regulation at a time**: The current design checks against one rule base per run; a future version could support multi-regulation checks in one pass.
- **Threshold tuning**: Similarity thresholds are fixed constants; a future version could calibrate them against a labeled dataset for better accuracy.
- **LLM explanations are optional and API-dependent**: They require an internet connection and API key, and incur a small per-call cost.

---

## License
This is an academic/prototype project. Add your preferred license here (e.g., MIT) if you plan to share the code publicly.
