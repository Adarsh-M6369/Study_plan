import streamlit as st
import os


def init_auth_session():
    """Initializes authentication session state variables in Streamlit."""
    if "user_token" not in st.session_state:
        st.session_state.user_token = os.getenv("DEMO_USER_TOKEN", "dev-token-default")
    if "user_id" not in st.session_state:
        st.session_state.user_id = "student_user_1"
    if "user_email" not in st.session_state:
        st.session_state.user_email = "student@studyguide.ai"
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Alex Scholar"


def render_auth_sidebar():
    """Renders user authentication controls and Clerk token status in the sidebar."""
    init_auth_session()

    st.sidebar.markdown("### 👤 User Profile & Clerk Auth")
    st.sidebar.info(f"**Logged in as:** {st.session_state.user_name}\n\n**Email:** `{st.session_state.user_email}`")

    with st.sidebar.expander("🔑 Clerk / JWT Token Settings"):
        custom_token = st.text_input(
            "Bearer Token",
            value=st.session_state.user_token,
            type="password",
            help="Provide Clerk JWT token for authenticated multi-tenant isolation."
        )
        if custom_token != st.session_state.user_token:
            st.session_state.user_token = custom_token
            st.success("Updated auth token!")

        custom_user_id = st.text_input(
            "User ID",
            value=st.session_state.user_id,
            help="Tenant identifier for partitioned Chroma vector storage."
        )
        if custom_user_id != st.session_state.user_id:
            st.session_state.user_id = custom_user_id
            st.success("Updated user tenant ID!")
