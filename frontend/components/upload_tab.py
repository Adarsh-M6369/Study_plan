import streamlit as st
import io
import re
import pypdf
try:
    from frontend.utils.api_client import StudyGuideApiClient
except ImportError:
    from utils.api_client import StudyGuideApiClient


def render_upload_tab(api_client: StudyGuideApiClient):
    """
    Renders Tab 1: Lecture PDF upload (with page count validation) and raw text/syllabus paste area.
    """
    st.markdown("## 📥 Ingest Lecture Material")
    st.markdown("Upload your lecture notes, slides, or textbook excerpts to build a custom AI study guide.")

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown("### 📄 Option A: Upload Lecture PDF")
        st.caption("Strict 150-page limit enforced per document upload.")

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a PDF lecture deck (maximum 150 pages)."
        )

        doc_title = st.text_input("Document Title (Optional)", placeholder="e.g. Distributed Systems Lecture 4")

        if uploaded_file is not None:
            # Client-side fast check
            try:
                reader = pypdf.PdfReader(io.BytesIO(uploaded_file.getvalue()))
                pages_count = len(reader.pages)
                if pages_count > 150:
                    st.error(f"❌ Document contains **{pages_count} pages**. It exceeds the strict **150-page limit**. Please trim the file before uploading.")
                else:
                    st.success(f"✓ PDF verified: **{pages_count} pages** (within 150-page limit).")
            except Exception as e:
                st.warning(f"Could not pre-verify pages locally: {e}")

            if st.button("🚀 Ingest PDF Document", type="primary", use_container_width=True):
                with st.spinner("Parsing pages, cleaning text, and indexing into vector store..."):
                    token = st.session_state.get("user_token")
                    success, res = api_client.upload_document(
                        file_bytes=uploaded_file.getvalue(),
                        filename=uploaded_file.name,
                        title=doc_title or uploaded_file.name,
                        token=token
                    )
                    if success:
                        st.balloons()
                        st.success(f"✅ {res.get('message', 'Indexed successfully!')}")
                        st.session_state["active_doc_id"] = res.get("document_id")

                        # Format title cleanly for user display
                        raw_t = res.get("title", "Lecture Notes")
                        cleaned_t = re.sub(r"(?i)\.pdf$", "", raw_t)
                        cleaned_t = re.sub(r"https?://\S+|www\.\S+", "", cleaned_t)
                        cleaned_t = re.sub(r"(?i)\b\w+\.(in|com|org|net)\b", "", cleaned_t)
                        cleaned_t = cleaned_t.replace("_", " ").replace("-", " ")
                        cleaned_t = " ".join([w for w in cleaned_t.split() if w.strip()]).strip()
                        st.session_state["active_doc_title"] = cleaned_t or "Lesson Study Guide"
                    else:
                        st.error(f"❌ Upload failed: {res.get('error')}")

    with col2:
        st.markdown("### 📝 Option B: Paste Raw Text / Syllabus")
        st.caption("Paste excerpts, lecture transcripts, or topic notes directly.")

        raw_text = st.text_area(
            "Lecture Text / Syllabus",
            height=250,
            placeholder="Paste syllabus topics, lecture transcript, or study summary here..."
        )
        text_title = st.text_input("Topic / Section Title", placeholder="e.g. Quantum Computing Algorithms")

        if st.button("📥 Ingest Raw Text", use_container_width=True):
            if not raw_text.strip():
                st.warning("Please enter some text before submitting.")
            else:
                with st.spinner("Chunking and indexing text into vector store..."):
                    token = st.session_state.get("user_token")
                    success, res = api_client.upload_document(
                        raw_text=raw_text,
                        title=text_title or "Pasted Notes",
                        token=token
                    )
                    if success:
                        st.success(f"✅ {res.get('message', 'Text indexed!')}")
                        st.session_state["active_doc_id"] = res.get("document_id")
                        st.session_state["active_doc_title"] = res.get("title")
                    else:
                        st.error(f"❌ Failed: {res.get('error')}")
