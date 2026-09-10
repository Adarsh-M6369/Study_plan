import streamlit as st
from typing import List, Dict, Any


def render_quiz_view(mcqs: List[Dict[str, Any]]):
    """
    Renders Tab 4: Interactive practice quiz rendering 20 MCQs with instant feedback toggles.
    """
    if not mcqs:
        st.info("ℹ️ No MCQs generated yet. Generate a study pack in **Tab 2** to take the practice quiz.")
        return

    st.markdown("## 🧠 Interactive Practice Quiz (20 MCQs)")
    st.markdown("Test your mastery with active recall. Select your answers and get instant feedback with explanations.")

    # Init quiz state
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "submitted_quiz" not in st.session_state:
        st.session_state.submitted_quiz = False

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        instant_mode = st.toggle("⚡ Instant Validation Mode", value=True, help="Show explanations and answer correctness immediately upon selection.")
    with col_ctrl2:
        if st.button("🔄 Reset Quiz Answers", use_container_width=True):
            st.session_state.quiz_answers = {}
            st.session_state.submitted_quiz = False
            st.rerun()

    st.write("")

    score = 0
    answered_count = len(st.session_state.quiz_answers)

    for idx, mcq in enumerate(mcqs):
        q_id = mcq.get("id", idx + 1)
        q_text = mcq.get("question", "")
        options = mcq.get("options", [])
        correct_ans = mcq.get("correct_answer", "A")
        explanation = mcq.get("explanation", "")

        user_choice = st.session_state.quiz_answers.get(q_id)
        is_correct = (user_choice == correct_ans)
        if is_correct:
            score += 1

        with st.container():
            st.markdown(f"#### Question {q_id} of {len(mcqs)}")
            st.markdown(f"**{q_text}**")

            # Format options for radio
            option_labels = [f"{opt.get('label')}) {opt.get('text')}" for opt in options]
            option_keys = [opt.get('label') for opt in options]

            # Current index
            curr_idx = option_keys.index(user_choice) if user_choice in option_keys else None

            selected_str = st.radio(
                label=f"Options for Q{q_id}",
                options=option_labels,
                index=curr_idx,
                key=f"mcq_{q_id}",
                label_visibility="collapsed"
            )

            # Extract selected letter
            if selected_str:
                selected_letter = selected_str.split(")")[0].strip()
                if st.session_state.quiz_answers.get(q_id) != selected_letter:
                    st.session_state.quiz_answers[q_id] = selected_letter
                    if instant_mode:
                        st.rerun()

            # Feedback
            if user_choice and (instant_mode or st.session_state.submitted_quiz):
                if is_correct:
                    st.success(f"✅ **Correct!** (Selected {user_choice})")
                else:
                    st.error(f"❌ **Incorrect.** You selected **{user_choice}**, but the correct answer is **{correct_ans}**.")

                with st.expander("💡 View Detailed Explanation", expanded=instant_mode):
                    st.write(explanation)

            st.markdown("---")

    # Score Summary Banner
    st.markdown("### 📊 Quiz Performance Summary")
    pct = (score / len(mcqs)) * 100 if mcqs else 0
    st.progress(score / len(mcqs) if mcqs else 0)
    st.metric(
        label="Final Score",
        value=f"{score} / {len(mcqs)} ({pct:.1f}%)",
        delta=f"{answered_count} / {len(mcqs)} Questions Answered"
    )

    if not st.session_state.submitted_quiz and not instant_mode:
        if st.button("🏁 Submit All Answers for Grading", type="primary", use_container_width=True):
            st.session_state.submitted_quiz = True
            st.rerun()
