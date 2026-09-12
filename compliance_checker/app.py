# Streamlit web application entry point for AI Compliance Checker.

import sys
import os
import streamlit as st

# Ensure the app's directory is in the Python search path so local modules in 'utils/' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom text extraction helper from utils/extract_text.py
from utils.extract_text import extract_text

# st.set_page_config() configures page metadata and layout.
# Note: This MUST be the very first Streamlit command called in your app.
# - page_title: Sets the title shown in the browser tab.
# - page_icon: Sets the icon/favicon shown in the browser tab (can be an emoji).
# - layout="wide": Expands the app to use the full browser window width.
st.set_page_config(
    page_title="AI-Based Automated Compliance Checker",
    page_icon="🛡️",
    layout="wide"
)

# st.title() displays a large, top-level header on the page.
st.title("AI-Based Automated Compliance Checker")

# st.markdown() renders formatted Markdown text.
# Here we provide a short overview explaining what the tool does.
st.markdown(
    """
    This tool automatically evaluates uploaded documents (such as privacy policies 
    and legal agreements) against **General Data Protection Regulation (GDPR)** requirements 
    to help identify compliance gaps and risk areas.
    """
)

# st.divider() renders a subtle horizontal rule to separate sections cleanly.
st.divider()

# st.file_uploader() renders a file upload box that accepts drag-and-drop or file browsing.
# - label: The text prompt displayed above the upload area.
# - type: A list of allowed file extension strings (e.g., ["pdf", "docx", "txt"]).
uploaded_file = st.file_uploader(
    label="Upload a document for GDPR compliance verification",
    type=["pdf", "docx", "txt"],
    help="Supported file formats: PDF, DOCX, and TXT"
)

# Check if a file has been uploaded by the user
if uploaded_file is not None:
    # st.success() displays a green success message box.
    st.success("File uploaded successfully!")

    # Format file size in kilobytes (KB) for readability
    file_size_kb = uploaded_file.size / 1024

    # st.subheader() displays a secondary heading.
    st.subheader("File Information")

    # st.info() displays an informative callout box.
    # uploaded_file.name provides the original filename.
    # uploaded_file.size provides the size in bytes.
    st.info(
        f"**Filename:** {uploaded_file.name}\n\n"
        f"**File Size:** {uploaded_file.size:,} bytes ({file_size_kb:.2f} KB)"
    )

    # Call extract_text() to parse the document content based on its file extension
    extracted_text = extract_text(uploaded_file)

    # st.expander() creates a collapsible container that users can toggle open or closed.
    # It keeps the interface clean while allowing users to inspect the full extracted text.
    with st.expander("📄 View Extracted Document Text", expanded=False):
        if extracted_text.strip():
            # st.text_area() displays multi-line text inside a scrollable box.
            # - label: Heading for the text area widget.
            # - value: The extracted string content.
            # - height: Height in pixels.
            # - disabled=True: Makes it read-only so the user can verify without editing.
            st.text_area(
                label="Extracted Content",
                value=extracted_text,
                height=350,
                disabled=True
            )
        else:
            # st.warning() displays a yellow warning box when no text was found
            st.warning("⚠️ No text could be extracted from this document, or the file is empty.")


