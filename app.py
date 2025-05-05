import streamlit as st
import os
import json
import time
import tempfile
import re
from typing import Dict, List
import tomli
import openai
import docx2txt
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# === LOAD ENVIRONMENT VARIABLES ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Load configuration from config.toml
#@st.cache_resource
def load_config():
    with open("config.toml", "rb") as f:
        return tomli.load(f)

config = load_config()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Directory to store segmented templates
SEGMENT_DIR = config.get("paths", {}).get("segment_dir", "./segments")
os.makedirs(SEGMENT_DIR, exist_ok=True)

# ---------------- Utility Functions ----------------
def display_hint(message: str):
    """Show an expandable hint to help the user."""
    with st.expander("Hint"):
        st.info(message)

def save_segment_to_json(filename: str, data: Dict):
    """Save segmentation dictionary to a JSON file."""
    with open(os.path.join(SEGMENT_DIR, filename), 'w') as f:
        json.dump(data, f, indent=4)

def load_segment_json(filename: str) -> Dict:
    """Load a JSON segmentation file."""
    with open(os.path.join(SEGMENT_DIR, filename), 'r') as f:
        return json.load(f)

def list_segment_files() -> List[str]:
    """List all available segmentation templates."""
    return [f for f in os.listdir(SEGMENT_DIR) if f.endswith(".json")]

def read_uploaded_file(file) -> str:
    """Extract text from TXT, DOCX, or PDF."""
    suffix = file.name.lower().split(".")[-1]
    if suffix == "txt":
        return file.read().decode("utf-8")
    elif suffix == "docx":
        temp_path = os.path.join(tempfile.gettempdir(), file.name)
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())
        return docx2txt.process(temp_path)
    elif suffix == "pdf":
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        return ""

# ---------------- Segmentation Functions ----------------
def segment_document(text: str) -> Dict:
    """Simple segmentation based on headers (e.g., numbered or titled sections)."""
    segments = {}
    current_section = "Header"
    segments[current_section] = []
    for line in text.splitlines():
        if re.match(r"^\s*\d+\.", line.strip()) or re.match(r"^[A-Z][A-Za-z\s]+:$", line.strip()):
            current_section = line.strip()
            segments[current_section] = []
        segments[current_section].append(line)
    return {k: "\n".join(v) for k, v in segments.items()}

# ---------------- Comparison Functions ----------------
def compare_segments(template: Dict, filled: Dict) -> Dict:
    """Compare two segmented documents using OpenAI's GPT-4 for semantic analysis, status classification, and remediation."""
    comparison = {}
    for section, content in template.items():
        filled_content = filled.get(section, "")
        if not filled_content.strip():
            status = "Missing"
            reason = "This section is missing in the filled document."
            remediation = "Please provide content for this section."
            match_percent = 0
        elif filled_content.strip() == content.strip():
            status = "Sufficient"
            reason = "This section is sufficiently filled and matches the template."
            remediation = "None needed."
            match_percent = 100
        else:
            prompt = (
                "You are a document comparison expert. "
                "Compare the following two sections and classify the filled section as one of: "
                "'Sufficient', 'Lacking Information', or 'Other Issue'. "
                "Then, explain your reasoning in 1-2 sentences. "
                "If the status is not 'Sufficient', provide a specific remediation suggestion for how to improve the filled section. "
                "Finally, estimate a match percentage (0-100) for how well the filled section aligns with the template, "
                "where 100 means a perfect match and 0 means no alignment at all. "
                "Respond in this format:\n"
                "Status: <Sufficient/Lacking Information/Other Issue>\n"
                "Reason: <your explanation>\n"
                "Remediation: <your suggestion or 'None needed'>\n"
                "Match Percentage: <number between 0 and 100>\n\n"
                f"Template:\n{content}\n\nFilled:\n{filled_content}"
            )
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a document comparison expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            analysis_full = response.choices[0].message.content
            lines = analysis_full.splitlines()
            status, reason, remediation, match_percent = "Other Issue", "", "", 0
            for line in lines:
                if line.lower().startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                elif line.lower().startswith("reason:"):
                    reason = line.split(":", 1)[1].strip()
                elif line.lower().startswith("remediation:"):
                    remediation = line.split(":", 1)[1].strip()
                elif line.lower().startswith("match percentage:"):
                    try:
                        match_percent = int(line.split(":", 1)[1].strip().replace('%',''))
                    except:
                        match_percent = 0
            if not remediation:
                remediation = "None provided."
        comparison[section] = {
            "template": content,
            "filled": filled_content,
            "status": status,
            "analysis": reason,
            "remediation": remediation,
            "match_percent": match_percent
        }
    return comparison

def status_icon(status):
    status = status.lower()
    if status == "sufficient":
        return "✅"
    elif status == "missing":
        return "❌"
    elif status == "lacking information":
        return "⚠️"
    else:
        return "❓"

# ---------------- Main App ----------------
st.title("Document Segmentation & Comparison Tool")
st.markdown("Use this tool to segment documents and compare filled forms against templates.")

# Segment selection
st.subheader("Step 1: Choose Template")
option = st.radio("Select an option:", ["Use existing segmentation", "Upload new document for segmentation"])

segment_data = {}

if option == "Use existing segmentation":
    template_options = list_segment_files()
    st.write(f"SEGMENT_DIR: {SEGMENT_DIR}")
    st.write(f"Files in SEGMENT_DIR: {os.listdir(SEGMENT_DIR)}")
    st.write(f"JSON files found: {template_options}")
    selected = st.selectbox("Choose a segmentation template:", template_options)
    if selected:
        with st.spinner("Loading segmentation template..."):
            time.sleep(1)
            segment_data = load_segment_json(selected)
        st.success("Template loaded.")

elif option == "Upload new document for segmentation":
    uploaded_file = st.file_uploader("Upload a document (TXT, DOCX, PDF)", type=["txt", "docx", "pdf"], key="template")
    if uploaded_file:
        text = read_uploaded_file(uploaded_file)
        display_hint("Document sections should be clearly marked with numbered headings or colons (e.g., '1. Introduction' or 'Conclusion:').")
        if st.button("Segment Document"):
            with st.spinner("Segmenting document..."):
                for percent in range(0, 101, 20):
                    time.sleep(0.2)
                    st.progress(percent)
                st.session_state.segment_data = segment_document(text)
                st.session_state.segmentation_complete = True
        # Show segmentation complete and text input if segmentation is done
        if st.session_state.get("segmentation_complete"):
            st.success("Segmentation complete!")
            segment_data = st.session_state.get("segment_data", {})
            json_name = st.text_input(
                "Enter a name to save this segmentation (e.g., template1.json):",
                key="save_filename"
            )
            # Removed debug information for cleaner UI
            if json_name and json_name.strip():
                if st.button("Save Segmentation", key="save_button"):
                    try:
                        save_segment_to_json(json_name, segment_data)
                        st.success(f"Segmentation saved as {json_name}!")
                        st.session_state.segmentation_complete = False  # Reset after save
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error saving file: {str(e)}")
            else:
                st.info("Please enter a filename to save the segmentation")

# Show segmented output
if segment_data:
    st.subheader("Segmented Document Preview")
    for section, content in segment_data.items():
        with st.expander(section):
            st.text_area("", content, height=150, key=section)

# Comparison Section
st.subheader("Step 2: Upload Filled Document for Comparison")
filled_file = st.file_uploader("Upload filled document (TXT, DOCX, PDF)", type=["txt", "docx", "pdf"], key="filled")
if filled_file and segment_data:
    filled_text = read_uploaded_file(filled_file)
    if st.button("Compare to Template"):
        with st.spinner("Segmenting and comparing filled document..."):
            filled_segments = segment_document(filled_text)
            st.session_state.comparison = compare_segments(segment_data, filled_segments)
            time.sleep(1)
        st.success("Comparison complete.")

# Always display results and download button if comparison exists in session state
if "comparison" in st.session_state:
    comparison = st.session_state.comparison
    if comparison:
        st.subheader("Comparison Results")
        filter_options = ["Missing", "Lacking Information", "Sufficient", "Other Issue"]
        selected_filters = st.multiselect(
            "Filter by status (leave empty to show all)", filter_options
        )
        for section, result in comparison.items():
            if not selected_filters or result['status'].lower() in [f.lower() for f in selected_filters]:
                icon = status_icon(result['status'])
                with st.expander(f"{icon} {section} - {result['status']} ({result['match_percent']}%)"):
                    st.text_area("Template:", result['template'], height=100, key=section+"_t")
                    st.text_area("Filled:", result['filled'], height=100, key=section+"_f")
                    st.text_area("Remediation:", result['remediation'], height=80, key=section+"_r")
    else:
        st.success("All sections match exactly.")

    # --- Always show the download button ---
    json_bytes = json.dumps(comparison, indent=4).encode('utf-8')
    st.download_button(
        label="Download Comparison Results as JSON",
        data=json_bytes,
        file_name="comparison_results.json",
        mime="application/json"
    )

st.markdown("---")
st.caption("Developed with simplicity and best practices. Configured using config.toml.")
