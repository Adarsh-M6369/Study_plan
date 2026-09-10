import sys
import os

# Ensure both root and frontend directory are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
frontend_dir = os.path.abspath(os.path.dirname(__file__))
for path in [root_dir, frontend_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

import streamlit as st

try:
    from frontend.auth import render_auth_sidebar, init_auth_session
    from frontend.utils.api_client import StudyGuideApiClient
    from frontend.components.upload_tab import render_upload_tab
    from frontend.components.study_pack_view import render_study_pack_view
    from frontend.components.quiz_view import render_quiz_view
    from frontend.components.download_buttons import render_download_buttons
except ImportError:
    from auth import render_auth_sidebar, init_auth_session
    from utils.api_client import StudyGuideApiClient
    from components.upload_tab import render_upload_tab
    from components.study_pack_view import render_study_pack_view
    from components.quiz_view import render_quiz_view
    from components.download_buttons import render_download_buttons

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="AI Study Guide Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session & Auth
init_auth_session()
api_client = StudyGuideApiClient()

# Custom CSS for Dark Theme with Light Blue Accent Aesthetics
st.markdown("""
<style>
    /* Global app styling */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #38bdf8;
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #111827;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        font-weight: 600;
        color: #94a3b8;
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #38bdf8;
        background-color: rgba(56, 189, 248, 0.08);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    /* Glass card containers */
    .card-panel {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
    }
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7, #38bdf8);
        border: none;
        color: #0b0f19;
        font-weight: 700;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Sidebar
    st.sidebar.title("🎓 Study Guide AI")
    render_auth_sidebar()

    # Backend Health Indicator in Sidebar
    health = api_client.check_health()
    if health.get("status") == "healthy":
        st.sidebar.success("🟢 Backend Connected (Port 8000)")
    else:
        st.sidebar.warning(f"🟡 Backend Offline/Unavailable: {health.get('error', 'Check server')}")

    # App Header
    st.markdown('<div class="main-header">🎓 AI Study Guide & Exam Prep Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Transform lecture notes into comprehensive study packs: 20 MCQs, short Q&As, roadmaps, summaries & Anki flashcards.</div>', unsafe_allow_html=True)

    # State stores
    if "current_study_pack" not in st.session_state:
        st.session_state.current_study_pack = None

    # Tabs definition
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 1. Ingest Notes",
        "⚙️ 2. Configure & Generate",
        "📖 3. Study Pack View",
        "🧠 4. Interactive Quiz",
        "💾 5. Export Center"
    ])

    # Tab 1: Upload / Ingestion
    with tab1:
        render_upload_tab(api_client)

    # Tab 2: Difficulty selection and Generation Trigger
    with tab2:
        st.markdown("## ⚙️ Configure Study Guide Generation")
        st.markdown("Select your target academic difficulty tier and trigger the LangGraph generation pipeline.")

        col1, col2 = st.columns([1, 1], gap="medium")

        with col1:
            difficulty = st.selectbox(
                "🎯 Select Academic Difficulty",
                options=["Beginner", "Intermediate", "Advanced"],
                index=1,
                help=(
                    "Beginner: Foundational recall & analogies.\n"
                    "Intermediate: Application, synthesis & multi-step analysis.\n"
                    "Advanced: Edge cases, rigorous mechanisms & challenging distractors."
                )
            )

            topic = st.text_input(
                "Focus Topic / Title",
                value=st.session_state.get("active_doc_title", "Lecture Study Guide"),
                placeholder="e.g. Distributed Consensus Protocols"
            )

        with col2:
            custom_instructions = st.text_area(
                "Custom Prompt / Focus Areas (Optional)",
                placeholder="e.g. Focus heavily on algorithm step complexity, Raft state transitions, and leader election scenarios.",
                height=125
            )

        st.write("")
        if st.button("✨ Run LangGraph Study Pack Pipeline", type="primary", use_container_width=True):
            with st.spinner("Executing LangGraph (Retrieval -> Reasoner -> MCP Tool -> Synthesis -> Validation)..."):
                token = st.session_state.get("user_token")
                success, result = api_client.generate_study_pack(
                    topic=topic,
                    difficulty=difficulty,
                    custom_instructions=custom_instructions,
                    token=token
                )
                if success:
                    st.session_state.current_study_pack = result
                    st.session_state.quiz_answers = {}
                    st.session_state.submitted_quiz = False
                    st.success(f"🎉 Generated full study pack for **{topic}**! Check **Tab 3**, **Tab 4**, and **Tab 5**.")
                    st.balloons()
                else:
                    st.error(f"❌ Generation failed: {result.get('error')}")

    # Tab 3: Study Pack View
    with tab3:
        render_study_pack_view(st.session_state.current_study_pack)

    # Tab 4: Interactive Practice Quiz (20 MCQs)
    with tab4:
        mcqs = st.session_state.current_study_pack.get("mcqs", []) if st.session_state.current_study_pack else []
        render_quiz_view(mcqs)

    # Tab 5: Download Center
    with tab5:
        render_download_buttons(st.session_state.current_study_pack, api_client)


if __name__ == "__main__":
    main()
