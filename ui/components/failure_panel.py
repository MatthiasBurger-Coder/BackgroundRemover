"""Failure inspection panel for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FailureCase
from ui.state import set_selected_error


def render_failure_panel(failure_cases: list[FailureCase]) -> None:
    st.subheader("Failure Inspection")
    st.caption("Mock diagnostic cases for workflow review and future backend integration.")

    selection_column, detail_column = st.columns([1, 1.2], gap="large")

    with selection_column:
        selected_index = st.selectbox(
            "Selected error case",
            options=list(range(len(failure_cases))),
            index=st.session_state.selected_error_index,
            format_func=lambda index: failure_cases[index].selector_label(),
        )
        if selected_index != st.session_state.selected_error_index:
            set_selected_error(selected_index)

        st.dataframe(
            [case.to_row() for case in failure_cases],
            width="stretch",
            hide_index=True,
        )

    with detail_column:
        selected_case = failure_cases[st.session_state.selected_error_index]
        with st.container(border=True):
            st.markdown("**Selected Failure Detail**")
            st.write(f"Code: {selected_case.code}")
            st.write(f"Frame: {selected_case.frame_index:04d}")
            st.write(f"Severity: {selected_case.severity}")
            st.write(f"Title: {selected_case.title}")
            st.write(f"Summary: {selected_case.summary}")
            st.write(f"Suspected Cause: {selected_case.suspected_cause}")
            st.write(f"Recommended Check: {selected_case.recommended_check}")
            st.write(f"Owner: {selected_case.owner}")
