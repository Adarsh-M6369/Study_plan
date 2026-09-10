import streamlit as st
from typing import Dict, Any
try:
    from frontend.utils.api_client import StudyGuideApiClient
except ImportError:
    from utils.api_client import StudyGuideApiClient


def render_download_buttons(pack: Dict[str, Any], api_client: StudyGuideApiClient):
    """
    Renders Tab 5: Download center featuring side-by-side buttons for ReportLab PDF & Anki CSV.
    """
    st.markdown("## 💾 Export & Download Center")
    st.markdown("Export your study guide and practice materials for offline learning and spaced repetition tools.")

    if not pack:
        st.info("ℹ️ No study pack available for export. Generate a study pack first in **Tab 2**.")
        return

    st.write("")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### 📄 Multi-Page Study Pack PDF")
        st.caption("Professionally styled PDF compiled using ReportLab with roadmap, glossary table, notes, and 20 MCQs.")

        if st.button("🔄 Prepare PDF Download", key="prep_pdf", use_container_width=True):
            with st.spinner("Compiling PDF with ReportLab..."):
                success, data = api_client.export_pdf(pack)
                if success:
                    st.session_state["pdf_bytes"] = data
                    st.success("PDF ready for download!")
                else:
                    st.error(f"Failed to generate PDF: {data}")

        if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"]:
            title_slug = pack.get("title", "StudyPack").replace(" ", "_")[:30]
            st.download_button(
                label="📥 Download Study Pack (PDF)",
                data=st.session_state["pdf_bytes"],
                file_name=f"{title_slug}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

    with col2:
        st.markdown("### 🗂️ Anki & Quizlet Flashcards CSV")
        st.caption("Two-column HTML formatted CSV with questions & options on the front, and answers with explanations on the back.")

        if st.button("🔄 Prepare Flashcards CSV", key="prep_csv", use_container_width=True):
            with st.spinner("Formatting 20 MCQs for Anki / Quizlet..."):
                mcqs = pack.get("mcqs", [])
                success, data = api_client.export_csv(mcqs)
                if success:
                    st.session_state["csv_bytes"] = data
                    st.success("Anki CSV ready for download!")
                else:
                    st.error(f"Failed to generate CSV: {data}")

        if "csv_bytes" in st.session_state and st.session_state["csv_bytes"]:
            st.download_button(
                label="📥 Download Anki Flashcards (CSV)",
                data=st.session_state["csv_bytes"],
                file_name="Anki_Quizlet_Flashcards.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

    st.divider()
    st.markdown("#### 💡 How to Import into Anki:")
    st.markdown("""
    1. Open the **Anki Desktop** application.
    2. Click **File -> Import...** and select the downloaded `.csv` file.
    3. Ensure **Allow HTML in fields** is checked.
    4. Map Field 1 to **Front** and Field 2 to **Back**.
    5. Click **Import** and start studying with active recall!
    """)
