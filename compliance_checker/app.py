# Streamlit web application entry point for AI Compliance Checker.

import sys
import os
import pandas as pd
import streamlit as st

# Ensure the app's directory is in the Python search path so local modules in 'utils/' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom pipeline modules
from utils.extract_text import extract_text
from utils.segment import segment_text
from utils.rules_loader import load_rules
from utils.matcher import check_compliance, get_model
from utils.report import generate_score, generate_pdf_report


# ==============================================================================
# PRE-WRITTEN DEMO SAMPLE TEXTS
# ==============================================================================
# Sample 1: A well-drafted policy explicitly covering GDPR requirements (High score)
SAMPLE_COMPLIANT_POLICY = """Comprehensive Privacy Policy & Data Protection Notice
Last Updated: January 2026

1. Lawful Basis and Purpose Limitation:
We collect and process your personal information strictly for specified, explicit, and legitimate purposes relating to account management and service delivery. Our lawful basis for processing personal data relies upon your explicit consent and our legitimate business interests under GDPR Article 6.

2. Consent and Withdrawal:
Consent is freely given, specific, and informed. You have the absolute right to withdraw your consent to data processing at any time by updating your privacy preferences in your account settings or contacting our privacy office.

3. Data Minimization:
We ensure that personal data collected is adequate, relevant, and strictly limited to what is necessary for our stated processing purposes.

4. Data Subject Rights (Access & Erasure):
Individuals have the right to request access to and obtain copies of their personal data. Furthermore, data subjects have the right to request the prompt erasure and deletion of their personal data without undue delay under the right to be forgotten.

5. Data Retention Period:
Personal data is retained only for as long as necessary to fulfill the specified operational purposes, or for a maximum duration of 24 months following account closure, after which it is permanently and securely deleted.

6. Data Breach Notification:
In the event of a personal data breach that risks individual rights and freedoms, we maintain incident response procedures to notify supervisory authorities and affected individuals within 72 hours.

7. Cross-Border Transfers:
Where personal data is transferred outside the European Economic Area (EEA), we ensure adequate safeguards are implemented, specifically utilizing European Commission Standard Contractual Clauses (SCCs).

8. Data Protection Officer (DPO):
If you have questions regarding this policy or wish to exercise your rights, please contact our designated Data Protection Officer (DPO) at dpo@complianceguard-ai.com.
"""

# Sample 2: A vague, evasive terms text missing core GDPR requirements (Low score)
SAMPLE_NON_COMPLIANT_POLICY = """General Website Terms & Browsing Policy

Welcome to our website. By accessing or browsing our pages and using our web services, you agree to our general terms and privacy practices.

We collect some information about you from time to time, such as your browser type, device information, click activity, and whatever personal details you enter when filling out online forms. We use this information to make our website work better, analyze traffic patterns, show relevant advertising, and grow our business operations.

We may share your information with our affiliates, third-party marketing partners, and contractors whenever we consider it useful or necessary. We keep your information in our systems for as long as we deem appropriate for company purposes.

We try our best to protect our servers from unauthorized access. We reserve the right to alter or update these terms at any time without advance notice to visitors.
"""


# ==============================================================================
# MODEL CACHING WITH @st.cache_resource
# ==============================================================================
# WHAT IS CACHING AND WHY DOES IT MATTER FOR PERFORMANCE?
# In Streamlit, every user interaction (uploading a file, clicking a button, or toggling
# a tab) triggers a complete rerun of the entire Python script.
# Loading a deep-learning model like "all-MiniLM-L6-v2" involves reading ~80MB of neural network
# weights from disk, setting up PyTorch tensors, and preparing GPU/CPU execution pipelines.
# Without caching, this heavy setup would occur on EVERY interaction, causing 3–8 seconds
# of latency and consuming unnecessary CPU/RAM.
# The '@st.cache_resource' decorator tells Streamlit to run this function once, store the
# initialized model in memory as a global singleton, and return the same cached instance
# on all subsequent reruns instantly.
# ==============================================================================
@st.cache_resource
def load_embedding_model():
    """
    Loads and caches the SentenceTransformer model in memory.
    """
    return get_model("all-MiniLM-L6-v2")


# st.set_page_config() configures page metadata and layout.
st.set_page_config(
    page_title="AI-Based Automated Compliance Checker",
    page_icon="🛡️",
    layout="wide"
)


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "active_text" not in st.session_state:
    st.session_state["active_text"] = ""
if "active_doc_name" not in st.session_state:
    st.session_state["active_doc_name"] = ""
if "compliance_results" not in st.session_state:
    st.session_state["compliance_results"] = None
if "last_uploaded_name" not in st.session_state:
    st.session_state["last_uploaded_name"] = None


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.title("🛡️ AI Compliance Checker")
    st.caption("Automated GDPR Regulatory Evaluation")
    st.divider()

    st.markdown("### 📋 How It Works")
    st.markdown(
        """
        1. **Ingest Document**: Upload a `.pdf`, `.docx`, or `.txt` policy, or load a pre-written demo sample.
        2. **Semantic Matching**: Sentence-Transformers converts clauses into 384-dimensional embeddings and matches them against 10 GDPR requirements using cosine similarity.
        3. **Audit & Report**: Inspect severity-weighted compliance scores, examine AI reasoning, and download a summary PDF report.
        """
    )
    st.divider()

    st.markdown("### 🧪 Quick Demo Samples")
    st.caption("Test the analysis pipeline instantly without uploading a file:")

    if st.button("🟢 Load Compliant Policy", use_container_width=True, help="Loads a comprehensive policy explicitly addressing GDPR articles."):
        st.session_state["active_text"] = SAMPLE_COMPLIANT_POLICY
        st.session_state["active_doc_name"] = "Sample_Compliant_Policy.txt"
        st.session_state["compliance_results"] = None
        st.toast("Loaded Compliant Sample Policy!", icon="🟢")

    if st.button("🔴 Load Non-Compliant Policy", use_container_width=True, help="Loads a vague, evasive terms document missing core GDPR mandates."):
        st.session_state["active_text"] = SAMPLE_NON_COMPLIANT_POLICY
        st.session_state["active_doc_name"] = "Sample_Non_Compliant_Policy.txt"
        st.session_state["compliance_results"] = None
        st.toast("Loaded Non-Compliant Sample Policy!", icon="🔴")

    st.divider()
    st.info(
        "⚠️ **Disclaimer:** This application is an automated educational prototype. "
        "It does not constitute formal legal advice or regulatory certification."
    )


# ==============================================================================
# MAIN PAGE HEADER
# ==============================================================================
st.title("AI-Based Automated Compliance Checker")
st.markdown(
    """
    Evaluate privacy policies and legal agreements against **General Data Protection Regulation (GDPR)** requirements 
    to detect compliance gaps using semantic AI sentence embeddings.
    """
)

# Organize UI into 3 primary tabs
tab1, tab2, tab3 = st.tabs([
    "📄 Upload & Extracted Text",
    "📊 Compliance Results",
    "⚖️ About the Rules"
])


# ==============================================================================
# TAB 1: UPLOAD & EXTRACTED TEXT
# ==============================================================================
with tab1:
    st.subheader("Document Input")
    st.markdown("Upload your own legal agreement, or use the demo buttons in the sidebar.")

    uploaded_file = st.file_uploader(
        label="Select a document (.pdf, .docx, .txt):",
        type=["pdf", "docx", "txt"],
        help="Supported file formats: PDF, Microsoft Word (DOCX), and Plain Text (TXT)"
    )

    # Handle file upload change
    if uploaded_file is not None:
        if st.session_state["last_uploaded_name"] != uploaded_file.name:
            extracted = extract_text(uploaded_file)
            st.session_state["active_text"] = extracted
            st.session_state["active_doc_name"] = uploaded_file.name
            st.session_state["last_uploaded_name"] = uploaded_file.name
            st.session_state["compliance_results"] = None

    # Status banner for currently active document
    if st.session_state["active_text"]:
        st.success(f"**Active Document:** `{st.session_state['active_doc_name']}` ({len(st.session_state['active_text'].split()):,} words)")

        # Expandable preview of active text
        with st.expander("📄 View Active Document Text", expanded=st.session_state["compliance_results"] is None):
            st.text_area(
                label="Extracted Text Preview",
                value=st.session_state["active_text"],
                height=320,
                disabled=True
            )

        # Trigger Compliance Analysis
        if st.button("🚀 Run Compliance Check", type="primary"):
            with st.spinner("Analyzing document against GDPR requirements..."):
                model = load_embedding_model()
                clauses = segment_text(st.session_state["active_text"])
                rules = load_rules()
                results = check_compliance(clauses, rules, model=model)
                st.session_state["compliance_results"] = results

            st.success("✅ Analysis complete! Check the **Compliance Results** tab to review your audit score and findings.")
    else:
        st.info("💡 Upload a document above or click one of the **Quick Demo Samples** in the left sidebar to get started.")


# ==============================================================================
# TAB 2: COMPLIANCE RESULTS
# ==============================================================================
with tab2:
    if st.session_state["compliance_results"] is None:
        st.info("ℹ️ No audit results available yet. Please select or upload a document in the **Upload & Extracted Text** tab and click **Run Compliance Check**.")
    else:
        results = st.session_state["compliance_results"]
        results_df = pd.DataFrame(results)

        # Calculate severity-weighted compliance percentage
        overall_score = generate_score(results)

        # Calculate counts
        total_rules = len(results)
        compliant_count = sum(1 for r in results if r["status"] == "Compliant")
        missing_count = sum(1 for r in results if r["status"] == "Missing")
        ambiguous_count = sum(1 for r in results if r["status"] == "Weak/Ambiguous")

        st.subheader("Audit Executive Summary")

        # Top row: Overall weighted score + Progress bar
        score_col, progress_col = st.columns([1, 2])
        with score_col:
            st.metric(
                label="Overall Compliance Score",
                value=f"{overall_score:.1f}%",
                help="Weighted by severity: High (3x), Medium (2x), Low (1x). High severity omissions carry the largest penalty."
            )
        with progress_col:
            st.write("")
            if overall_score >= 80.0:
                badge = "🟢 Strong Compliance"
            elif overall_score >= 50.0:
                badge = "🟡 Moderate Compliance Risk"
            else:
                badge = "🔴 Critical Non-Compliance"
            st.write(f"**Compliance Status:** {badge}")
            st.progress(overall_score / 100.0)

        # Second row: 3 Summary Metrics + Download button
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        col1.metric("Total Rules Checked", total_rules)
        col2.metric("Compliant", compliant_count, delta=f"{(compliant_count/total_rules)*100:.0f}%" if total_rules else None)
        col3.metric("Missing", missing_count, delta=f"-{missing_count}" if missing_count else None, delta_color="inverse")
        with col4:
            st.write("")
            st.write("")
            pdf_bytes = generate_pdf_report(results, overall_score)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"GDPR_Compliance_Report_{st.session_state['active_doc_name']}.pdf",
                mime="application/pdf",
                help="Download a clean, single-page summary PDF of this audit."
            )

        st.divider()
        st.subheader("Findings by Regulation")

        # Color-coding style helper for the status column
        def highlight_status(val):
            if val == "Compliant":
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            elif val == "Weak/Ambiguous":
                return "background-color: #fff3cd; color: #856404; font-weight: bold;"
            elif val == "Missing":
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            return ""

        display_columns = ["rule_id", "article", "title", "severity", "status", "similarity_score"]
        display_df = results_df[display_columns].copy()

        apply_styler = getattr(display_df.style, "map", getattr(display_df.style, "applymap", None))
        styled_df = apply_styler(highlight_status, subset=["status"])

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.subheader("AI Reasoning & Clause Verification")
        st.caption("Inspect the exact clause selected by the model and see how the status was derived:")

        for res in results:
            status = res["status"]
            icon = "✅" if status == "Compliant" else ("⚠️" if status == "Weak/Ambiguous" else "❌")
            expander_title = f"{icon} [{res['rule_id']}] {res['article']}: {res['title']} — {status} (Score: {res['similarity_score']:.4f})"

            with st.expander(expander_title, expanded=False):
                st.markdown(f"**GDPR Requirement:** {res['requirement']}")
                st.markdown(f"**Severity:** `{res['severity'].upper()}` | **Similarity Score:** `{res['similarity_score']:.4f}`")

                if res["best_matching_clause"]:
                    st.markdown("**Best Matching Clause in Document:**")
                    st.info(f"\"{res['best_matching_clause']}\"")
                else:
                    st.warning("No relevant clause found in document.")

                if status == "Compliant":
                    st.success(
                        "💡 **AI Reasoning:** The document clause has a high semantic similarity score (> 0.55) "
                        "to this statutory requirement, indicating clear and adequate compliance."
                    )
                elif status == "Weak/Ambiguous":
                    st.warning(
                        "💡 **AI Reasoning:** The clause produced a moderate similarity score (0.35 - 0.55). "
                        "The document mentions related concepts, but the language may be vague, indirect, "
                        "or incomplete relative to GDPR standards."
                    )
                else:
                    st.error(
                        "💡 **AI Reasoning:** The highest similarity score is below 0.35. "
                        "No clause in the document adequately discusses this legal obligation, "
                        "indicating a potential compliance gap."
                    )


# ==============================================================================
# TAB 3: ABOUT THE RULES
# ==============================================================================
with tab3:
    st.subheader("GDPR Regulatory Rule Base")
    st.markdown(
        """
        The compliance engine audits documents against **10 core requirements** drawn directly 
        from the **European Union General Data Protection Regulation (GDPR)**.
        """
    )

    rules = load_rules()
    if rules:
        rules_df = pd.DataFrame(rules)[["rule_id", "article", "title", "severity", "requirement"]]
        st.dataframe(
            rules_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.subheader("Evaluation Methodology")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### ⚖️ Severity Weighting")
        st.markdown(
            """
            Missed requirements impact the overall compliance score based on legal risk:
            - **High Severity (3x Weight)**: Core legal prerequisites such as Lawful Basis (Art. 6), Consent (Art. 7), Right to Erasure (Art. 17), and Breach Notification (Art. 33).
            - **Medium Severity (2x Weight)**: Operational safeguards like Data Minimization (Art. 5), Retention (Art. 13), and Transfer Safeguards (Art. 44).
            - **Low Severity (1x Weight)**: Contact details such as Data Protection Officer info (Art. 37).
            """
        )

    with col_b:
        st.markdown("#### 📐 Similarity Thresholds")
        st.markdown(
            """
            Semantic matching uses cosine similarity against sentence embeddings:
            - **Compliant (Score > 0.55)**: Full points awarded (100%). Strong semantic coverage.
            - **Weak / Ambiguous (Score 0.35 – 0.55)**: Half points awarded (50%). Topic mentioned but vague or incomplete.
            - **Missing (Score < 0.35)**: Zero points awarded (0%). No adequate coverage detected.
            """
        )


# ==============================================================================
# FOOTER
# ==============================================================================
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #64748b; font-size: 0.85rem; padding: 15px 0 5px 0;'>
        <strong>AI Compliance Checker</strong> | Developed with Streamlit, Sentence-Transformers & FPDF2 | Automated Regulatory Audit Prototype
    </div>
    """,
    unsafe_allow_html=True
)
