"""The finite-state machine that owns every workflow transition.

Code controls the workflow (INV-03). A model can neither select a state nor request one:
the only entry point is :func:`assert_transition`, which accepts a declared edge and
rejects everything else with a critical event.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import (
    CASE_STATE_STAGE,
    ORDERED_CASE_STATES,
    TERMINAL_CASE_STATES,
    CaseState,
)
from app.domain.errors import IllegalTransitionError
from app.domain.reason_codes import STATE_FAILURE_REASON, ReasonCode

#: The last automated processing state before the case waits for a human.
LAST_PROCESSING_STATE = CaseState.PACKET_PRE_ISSUANCE_AUDIT

#: States from which a mandatory stop may route directly to ``CANNOT_PROCEED``.
STOPPABLE_STATES: frozenset[CaseState] = frozenset(
    state
    for state in ORDERED_CASE_STATES
    if CASE_STATE_STAGE[state] <= CASE_STATE_STAGE[CaseState.CLOSED_DECISION_SUPPORT_RECORD]
    and state is not CaseState.CLOSED_DECISION_SUPPORT_RECORD
)


def _sequential_edges() -> set[tuple[CaseState, CaseState]]:
    edges: set[tuple[CaseState, CaseState]] = set()
    for index in range(len(ORDERED_CASE_STATES) - 1):
        edges.add((ORDERED_CASE_STATES[index], ORDERED_CASE_STATES[index + 1]))
    return edges


#: Every legal edge. Anything absent here is an illegal transition.
DECLARED_TRANSITIONS: frozenset[tuple[CaseState, CaseState]] = frozenset(
    _sequential_edges()
    | {(state, CaseState.CANNOT_PROCEED) for state in STOPPABLE_STATES}
    | {
        # Reviewer authority or separation of duties failed: return to waiting.
        (CaseState.REVIEWER_AUTHORITY_AND_SOD, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW),
        # Disposition could not bind (missing rationale, stale packet hash): stay waiting.
        (CaseState.DISPOSITION_BINDING, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW),
        # A return-for-clarification disposition is recorded and the packet stays open.
        (CaseState.DISPOSITION_CLOSURE_AUDIT, CaseState.AWAITING_AUTHORIZED_HUMAN_REVIEW),
    }
)


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    case_id: str
    from_state: CaseState
    to_state: CaseState
    reason_code: ReasonCode | None = None


def is_declared(from_state: CaseState, to_state: CaseState) -> bool:
    return (from_state, to_state) in DECLARED_TRANSITIONS


def assert_transition(case_id: str, from_state: CaseState, to_state: CaseState) -> None:
    """Raise :class:`IllegalTransitionError` unless the edge is declared.

    This blocks skips, reorders and replays: a state can only advance along a declared
    edge, and terminal states have no outbound edge at all.
    """
    if from_state in TERMINAL_CASE_STATES:
        raise IllegalTransitionError(case_id=case_id, from_state=from_state, to_state=to_state)
    if not is_declared(from_state, to_state):
        raise IllegalTransitionError(case_id=case_id, from_state=from_state, to_state=to_state)


def next_state(current: CaseState) -> CaseState:
    """The next state in the ordered workflow."""
    stage = CASE_STATE_STAGE.get(current)
    if stage is None or stage + 1 >= len(ORDERED_CASE_STATES):
        raise IllegalTransitionError(case_id="", from_state=current, to_state=None)
    return ORDERED_CASE_STATES[stage + 1]


def failure_reason_for(state: CaseState) -> ReasonCode:
    """The reason code produced when ``state`` fails its pass condition."""
    return STATE_FAILURE_REASON.get(state, ReasonCode.DETERMINISTIC_GOVERNANCE_FAILURE)


def transition_table() -> list[dict[str, object]]:
    """Machine-readable transition table for documentation and admin inspection."""
    rows: list[dict[str, object]] = []
    for state in ORDERED_CASE_STATES:
        successors = sorted(
            to_state.value for (frm, to_state) in DECLARED_TRANSITIONS if frm is state
        )
        rows.append(
            {
                "stage": CASE_STATE_STAGE[state],
                "state": state.value,
                "permitted_next_states": successors,
                "failure_reason_code": failure_reason_for(state).value,
                "terminal": state in TERMINAL_CASE_STATES,
            }
        )
    rows.append(
        {
            "stage": None,
            "state": CaseState.CANNOT_PROCEED.value,
            "permitted_next_states": [],
            "failure_reason_code": None,
            "terminal": True,
        }
    )
    return rows
