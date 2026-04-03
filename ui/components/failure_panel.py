"""Failure inspection panel for the internal Streamlit UI shell."""

from __future__ import annotations

import streamlit as st

from ui.mock_data import FailureCase
from ui.state import set_selected_error


def render_failure_panel(failure_cases: list[FailureCase]) -> None:
    st.subheader("Failure Inspection")
    st.caption("Compact diagnostic review for placeholder error cases.")

    selected_index = st.selectbox(
        "Selected error case",
        options=list(range(len(failure_cases))),
        index=st.session_state.selected_error_index,
        format_func=lambda index: failure_cases[index].selector_label(),
    )
    if selected_index != st.session_state.selected_error_index:
        set_selected_error(selected_index)

    selected_case = failure_cases[st.session_state.selected_error_index]
    metric_columns = st.columns(4, gap="small")
    metric_columns[0].metric("Code", selected_case.code)
    metric_columns[1].metric("Frame", f"{selected_case.frame_index:04d}")
    metric_columns[2].metric("Severity", selected_case.severity)
    metric_columns[3].metric("Owner", selected_case.owner)

    with st.container(border=True):
        st.markdown(f"**{selected_case.title}**")
        detail_columns = st.columns(2, gap="large")
        detail_columns[0].write(f"Summary: {selected_case.summary}")
        detail_columns[0].write(f"Suspected Cause: {selected_case.suspected_cause}")
        detail_columns[1].write(f"Recommended Check: {selected_case.recommended_check}")
        detail_columns[1].write("Scope: placeholder diagnostics only.")

    with st.expander("Failure Case Table", expanded=False):
        st.dataframe(
            [case.to_row() for case in failure_cases],
            width="stretch",
            hide_index=True,
        )
