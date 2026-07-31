"""Four consistency guardrails for the RFC-0004 role vocabulary."""

from role_vocabulary import (
    AGENT_ROLES,
    HUMAN_ONLY_ROLES,
    HUMAN_ROLES,
    ROLE_ALLOWED_TYPES,
    Role,
)


def test_table_covers_the_enum_exactly() -> None:
    """Every role — and only roles — appear in the allow-table."""
    assert set(ROLE_ALLOWED_TYPES) == set(Role)


def test_every_role_allows_at_least_one_type() -> None:
    """No role is orphaned: each is holdable by human, agent, or both."""
    assert all(types for types in ROLE_ALLOWED_TYPES.values())


def test_agent_list_is_human_list_minus_human_only() -> None:
    """The agent list is exactly the human list minus the human-only terms."""
    assert AGENT_ROLES == HUMAN_ROLES - HUMAN_ONLY_ROLES


def test_human_only_terms_are_exactly_the_boundary() -> None:
    """The accountability boundary: conceptualization and supervision only."""
    assert HUMAN_ONLY_ROLES == {Role.CONCEPTUALIZATION, Role.SUPERVISION}
