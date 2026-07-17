import streamlit as st

from src.utils import create_results_csv


def render_finished_page():
    st.title("Draft complete!")

    results = create_results_csv(st.session_state.drafts)

    st.caption("Final draft results")
    st.dataframe(results, hide_index=True, use_container_width=True)

    st.download_button(
        label="Download results to .csv",
        data=results.to_csv(index=False),
        file_name="draft_results.csv",
        mime="text/csv"
    )

    st.divider()

    if st.button("Start new draft", type="primary"):
        st.session_state.clear()
        st.rerun()
