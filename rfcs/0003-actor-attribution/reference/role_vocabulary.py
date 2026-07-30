"""Reference implementation of the RFC-0003 role vocabulary.

Normative shape for the astra-tools side: one closed ``Role`` enum (the
schema's vocabulary) and one per-role allow-table, ``ROLE_ALLOWED_TYPES``,
as the single source of truth for the actor-type split. Both per-type
lists and every exclusion are *derived* from the table — nothing else is
hand-maintained, which is what stops the human and agent lists from
drifting apart. Guardrails live in ``test_role_vocabulary.py``.

Run the guardrails:  python -m pytest rfcs/0003-actor-attribution/reference/
"""

from __future__ import annotations

from enum import Enum

HUMAN = "human"
AGENT = "agent"


class Role(str, Enum):
    """The single closed role vocabulary (CRediT subset + extensions)."""

    CONCEPTUALIZATION = "conceptualization"  # human-only
    METHODOLOGY = "methodology"
    DATA_CURATION = "data_curation"
    SOFTWARE = "software"
    FORMAL_ANALYSIS = "formal_analysis"
    VALIDATION = "validation"
    SUPERVISION = "supervision"  # human-only
    PLANNER = "planner"  # extension
    EXECUTOR = "executor"  # extension
    RESEARCHER = "researcher"  # extension


# The one source of truth: which actor types may hold each role.
ROLE_ALLOWED_TYPES: dict[Role, frozenset[str]] = {
    Role.CONCEPTUALIZATION: frozenset({HUMAN}),
    Role.METHODOLOGY: frozenset({HUMAN, AGENT}),
    Role.DATA_CURATION: frozenset({HUMAN, AGENT}),
    Role.SOFTWARE: frozenset({HUMAN, AGENT}),
    Role.FORMAL_ANALYSIS: frozenset({HUMAN, AGENT}),
    Role.VALIDATION: frozenset({HUMAN, AGENT}),
    Role.SUPERVISION: frozenset({HUMAN}),
    Role.PLANNER: frozenset({HUMAN, AGENT}),
    Role.EXECUTOR: frozenset({HUMAN, AGENT}),
    Role.RESEARCHER: frozenset({HUMAN, AGENT}),
}

# Derived views — never hand-maintained.
HUMAN_ROLES: frozenset[Role] = frozenset(
    r for r, types in ROLE_ALLOWED_TYPES.items() if HUMAN in types
)
AGENT_ROLES: frozenset[Role] = frozenset(
    r for r, types in ROLE_ALLOWED_TYPES.items() if AGENT in types
)
HUMAN_ONLY_ROLES: frozenset[Role] = HUMAN_ROLES - AGENT_ROLES


def role_allowed(role: Role | str, actor_type: str) -> bool:
    """Whether ``actor_type`` ('human' | 'agent') may hold ``role``."""
    return actor_type in ROLE_ALLOWED_TYPES[Role(role)]
