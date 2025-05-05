# Document Segmentation & Comparison Tool

**Author:** Arash Geramifard

## Overview
This Streamlit application allows users to:
- Upload and segment documents (TXT, DOCX, PDF) into logical sections.
- Save and reuse segmentation templates.
- Upload filled documents and compare them against templates using OpenAI GPT-4 for semantic analysis.
- Get actionable feedback, remediation suggestions, and a match percentage for each section.
- Filter comparison results by status (e.g., Missing, Lacking Information, Sufficient, Other Issue).
- Download the comparison results as a JSON file.

## Features
- **Document Segmentation:** Automatically splits documents into sections based on headers or numbering.
- **Template Management:** Save and reuse segmentation templates for future comparisons.
- **AI-Powered Comparison:** Uses GPT-4 to analyze filled documents, providing status, reasoning, remediation, and match percentage for each section.
- **Visual Status Icons:** Quickly identify section status with icons (✅ Sufficient, ❌ Missing, ⚠️ Lacking Information, ❓ Other Issue).
- **Filtering:** Filter results by one or more statuses for focused review.
- **Downloadable Results:** Export comparison results as a JSON file for record-keeping or further analysis.

## How to Use
1. **Install Requirements:**
   - Install Python 3.8+
   - Install dependencies: `pip install -r requirements.txt`
   - Set your OpenAI API key in a `.env` file: `OPENAI_API_KEY=your-key-here`

2. **Run the App:**
   - Start the app with: `streamlit run app.py`

3. **Segment a Document:**
   - Choose "Upload new document for segmentation" and upload a TXT, DOCX, or PDF file.
   - Click "Segment Document" to split the document into sections.
   - Enter a filename and save the segmentation as a template.

4. **Compare a Filled Document:**
   - Choose "Use existing segmentation" and select a template.
   - Upload a filled document (same format as the template).
   - Click "Compare to Template" to analyze the filled document.
   - Review the results, filter by status, and download the JSON report if needed.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

*Developed by Arash Geramifard with simplicity and best practices.* 
