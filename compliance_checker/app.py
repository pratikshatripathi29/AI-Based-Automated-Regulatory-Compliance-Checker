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


# ==============================================================================
# MODEL CACHING WITH @st.cache_resource
# ==============================================================================
# WHAT IS CACHING AND WHY DOES IT MATTER FOR PERFORMANCE?
# In Streamlit, every user interaction (such as uploading a file, clicking a button,
# or toggling an expander) triggers a complete rerun of the entire Python script.
# Loading a deep-learning model like "all-MiniLM-L6-v2" involves reading ~80MB of neural network
# weights from disk, setting up PyTorch tensors, and preparing GPU/CPU execution pipelines.
# Without caching, this heavy setup would occur on EVERY button click, introducing 3–8 seconds
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
# Note: This MUST be the very first Streamlit command called in your app.
st.set_page_config(
    page_title="AI-Based Automated Compliance Checker",
    page_icon="🛡️",
    layout="wide"
)

# st.title() displays the prominent heading
st.title("AI-Based Automated Compliance Checker")

# st.markdown() displays an introductory overview
st.markdown(
    """
    This tool automatically evaluates uploaded documents (such as privacy policies 
    and legal agreements) against **General Data Protection Regulation (GDPR)** requirements 
    to help identify compliance gaps and risk areas using semantic AI embeddings.
    """
)

st.divider()

# st.file_uploader() allows users to select or drag-and-drop a document
uploaded_file = st.file_uploader(
    label="Upload a document for GDPR compliance verification",
    type=["pdf", "docx", "txt"],
    help="Supported file formats: PDF, DOCX, and TXT"
)

# Initialize Streamlit session state to preserve audit results across UI interactions
if "compliance_results" not in st.session_state:
    st.session_state["compliance_results"] = None
if "current_file_name" not in st.session_state:
    st.session_state["current_file_name"] = None

# Check if a file has been uploaded
if uploaded_file is not None:
    # If the user uploads a different file, reset previous analysis results
    if st.session_state["current_file_name"] != uploaded_file.name:
        st.session_state["compliance_results"] = None
        st.session_state["current_file_name"] = uploaded_file.name

    st.success("File uploaded successfully!")

    # Format and show file metadata
    file_size_kb = uploaded_file.size / 1024
    st.subheader("File Information")
    st.info(
        f"**Filename:** {uploaded_file.name}\n\n"
        f"**File Size:** {uploaded_file.size:,} bytes ({file_size_kb:.2f} KB)"
    )

    # Extract text from the uploaded document
    extracted_text = extract_text(uploaded_file)

    # Collapsible preview of extracted document content
    with st.expander("📄 View Extracted Document Text", expanded=False):
        if extracted_text.strip():
            st.text_area(
                label="Extracted Content",
                value=extracted_text,
                height=300,
                disabled=True
            )
        else:
            st.warning("⚠️ No readable text could be extracted from this document, or the file is empty.")

    # Action button to trigger the compliance audit
    if st.button("Run Compliance Check", type="primary"):
        if not extracted_text.strip():
            st.error("Cannot run compliance check: No readable text found in the uploaded file.")
        else:
            # st.spinner() provides visual feedback while the AI pipeline runs
            with st.spinner("Analyzing document against GDPR requirements..."):
                # 1. Retrieve the cached sentence embedding model
                model = load_embedding_model()

                # 2. Segment extracted document text into individual clauses
                clauses = segment_text(extracted_text)

                # 3. Load predefined GDPR compliance rules from JSON
                rules = load_rules()

                # 4. Perform semantic matching using sentence embeddings & cosine similarity
                compliance_results = check_compliance(clauses, rules, model=model)

                # Store results in session state to persist them across UI reruns
                st.session_state["compliance_results"] = compliance_results

    # If results are available in session state, display summary metrics and results
    if st.session_state["compliance_results"] is not None:
        results = st.session_state["compliance_results"]
        results_df = pd.DataFrame(results)

        # Calculate summary metrics
        total_rules = len(results)
        compliant_count = sum(1 for r in results if r["status"] == "Compliant")
        missing_count = sum(1 for r in results if r["status"] == "Missing")
        ambiguous_count = sum(1 for r in results if r["status"] == "Weak/Ambiguous")

        st.divider()
        st.subheader("Compliance Audit Summary")

        # Display three prominent summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rules Checked", total_rules)
        col2.metric("Compliant", compliant_count, delta=f"{(compliant_count/total_rules)*100:.0f}% Compliant" if total_rules else None)
        col3.metric("Missing", missing_count, delta=f"-{missing_count} Non-compliant" if missing_count else None, delta_color="inverse")

        st.divider()
        st.subheader("Compliance Results Table")

        # Color-coding style helper for the status column
        def highlight_status(val):
            if val == "Compliant":
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            elif val == "Weak/Ambiguous":
                return "background-color: #fff3cd; color: #856404; font-weight: bold;"
            elif val == "Missing":
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            return ""

        # Prepare table with selected columns for clean presentation
        display_columns = ["rule_id", "article", "title", "severity", "status", "similarity_score"]
        display_df = results_df[display_columns].copy()

        # Apply styling across pandas versions safely
        apply_styler = getattr(display_df.style, "map", getattr(display_df.style, "applymap", None))
        styled_df = apply_styler(highlight_status, subset=["status"])

        # Display interactive dataframe
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.subheader("AI Reasoning & Clause Verification")
        st.caption("Expand any rule below to review the best-matching document clause and see how the AI derived its status:")

        # Show an expander for each row explaining the AI's reasoning
        for res in results:
            status = res["status"]
            icon = "✅" if status == "Compliant" else ("⚠️" if status == "Weak/Ambiguous" else "❌")
            expander_title = f"{icon} [{res['rule_id']}] {res['article']}: {res['title']} — {status} (Score: {res['similarity_score']:.4f})"

            with st.expander(expander_title, expanded=False):
                st.markdown(f"**GDPR Requirement:** {res['requirement']}")
                st.markdown(f"**Severity:** `{res['severity'].upper()}` | **Similarity Score:** `{res['similarity_score']:.4f}`")

                if res["best_matching_clause"]:
                    st.markdown("**Best Matching Clause Found in Document:**")
                    st.info(f"\"{res['best_matching_clause']}\"")
                else:
                    st.warning("No relevant clause found in the document.")

                # Detailed explanation of how status was derived
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
