---
rfc: 0003
title: Optional actor attribution for decisions and universe selections
status: Draft # Draft | Active | Accepted | Rejected | Superseded
authors:
  - Your Name (@github-handle) # TODO: fill in before opening the PR
created: 2026-07-30
tracking-issue: # link to the GitHub issue opened in Step 1
superseded-by:
---

## Context

An `astra.yaml` records *what* was decided and *why* (options, `default`,
`rationale`), and its constraint model relates options to one another with
`requires` and `incompatible_with`. A universe (`universes/*.yaml`) records one
complete selection: for each decision, which option was chosen. Neither layer
records any of the *who*: no field names who put an option on the table, who
ruled it out, who selected an option for a universe, or who reviewed that pick.

That gap matters now that agents co-author analyses. When an agent proposes an
outlier rule and a human rejects it, when a human catches a data-leakage
mistake an agent introduced, or when an agent assembles a candidate universe
that a human then signs off on, the record keeps the surviving *state* but
loses the *attribution* — precisely the information a reader needs to judge
accountability and to reproduce the reasoning. In today's records, a choice a
researcher examined and ruled on is indistinguishable from a default nobody
looked at.

**Relationship to RFC-0002's removal of `authors`.**
[RFC-0002](0002-decouple-reports.md) removed `Analysis.authors` and deferred
attribution, on the grounds that *document authorship* cannot be applied
coherently until ASTRA defines identity, reuse, and citation semantics for
individual elements — extending a prior analysis makes an author list
undefined. This proposal is a different, narrower thing: **decision
attribution**, not document authorship. An attribution here is anchored to a
concrete element of *this* file ("actor X ruled out option Y"), so it does not
inherit the reuse incoherence: when an analysis is extended, prior judgments
keep their attributions and new judgments get their own. It stakes no claim on
authorship, ownership, or citation of the work — that remains deferred exactly
as RFC-0002 left it.

Looking outward before inventing inward, two established standards already
cover this ground and this proposal reuses them rather than reinventing:

- **CRediT** (Contributor Roles Taxonomy, credit.niso.org) — the 14-role
  vocabulary journals already use for contribution statements.
- **ORCID** (orcid.org) — the primary persistent researcher identifier. It is
  the *default* human id, but not everyone has one and a person is
  referenceable through several schemes; the schema therefore groups ORCID
  with sibling scholarly ids (arXiv, OpenAlex, Wikidata, Google Scholar) in a
  small `ResearcherId` record rather than pinning a single `orcid` scalar.

A companion non-normative document, the **Attribution Rubric**, tells a working
scientist how to apply these fields honestly; it travels with this RFC but adds
no requirements to the schema.

## Proposal

Add an **optional, additive** actor layer spanning both places where a "who"
is meaningful — the *options* of an analysis and the *selections* of a
universe. Nothing here is required; an `astra.yaml` (and its universes) with
no actor fields stays valid and unchanged in meaning.

**1. An `actors:` registry on Analysis.** A map of actor id to actor record.
Humans carry a **`ResearcherId`** — a small record grouping one or more
scholarly identifiers (`orcid`, `arxiv`, `openalex`, `wikidata`,
`google_scholar`; any subset, at least one present), with ORCID the default;
agents are identified by `model` + `harness` + `version` (the harness is the
software wrapper running the model). The test is that *"which actor,
exactly?"* stays answerable years later — which is precisely why a person is
not pinned to a single id scheme. The same registry serves both the
analysis-level and the universe-level attribution below.

Because `Analysis` is self-similar, `actors` may be declared at any level;
attribution references resolve **upward through ancestor scopes**, the same
downward-only direction decisions flow, so the common case is one registry at
the root. Universe attributions resolve against the analysis tree's
registries.

**2. One attribution value, reused everywhere.** Every attribution field takes
the same value: *either* an actor id (shorthand) *or* an object
`{actor, role}` whose `role` is drawn from the actor-type-keyed vocabulary of
§5 (a CRediT-subset term or a flagged agent extension). No field grows a
parallel `*_role` slot — the role lives as a sub-key inside the value.

**3. Two optional attribution fields on the `Option` object:**

| Field | Value | Meaning |
|-------|-------|---------|
| `proposed_by` | actor id, or `{actor, role}` | Who put this option on the table. |
| `excluded_by` | actor id, or `{actor, role}` | Who ruled this option out. Pairs with the **existing** `excluded` / `excluded_reason` fields, and is only legal on an option marked `excluded: true`. |

**4. Two optional attribution fields on the `DecisionSelection` object** (the
per-decision choice inside a universe):

| Field | Value | Meaning |
|-------|-------|---------|
| `selected_by` | actor id, or `{actor, role}` | Who chose this option for this universe. |
| `reviewed_by` | actor id, or `{actor, role}` | Who reviewed the selection — typically a human signing off on an agent's pick. |

To carry these on a selection without breaking existing universes, the
universe `decisions:` map accepts **either** form:

- the existing **shorthand** — `decision_id: option_id` (no attribution), or
- an **object** — `option_id:` plus the optional `selected_by` /
  `reviewed_by` fields.

This holds for the `decisions` map on `Universe` *and* on `UniverseNode` (the
per-sub-analysis node), and is achieved with an explicit union on the slot —
see *Concrete schema changes* for why relying on LinkML's compact-dict
behaviour is not enough.

**5. A role vocabulary, split by actor type.** The `role` sub-key draws on a
curated subset of CRediT terms that can attach to a single decision or
selection, plus explicitly **flagged extension roles** where CRediT has no
home. Rather than one flat list, the vocabulary is **two enums keyed to the
actor's `type`** — which encodes the rubric's accountability boundary directly
in the schema instead of leaving it to guidance:

| `HumanRole` (a human actor may hold) | `AgentRole` (an agent actor may hold) |
|---|---|
| `conceptualization` *(human-owned)* | — |
| `methodology` | `methodology` |
| `data_curation` | `data_curation` |
| `software` | `software` |
| `formal_analysis` | `formal_analysis` |
| `validation` | `validation` |
| `supervision` *(human-owned)* | — |
| `planner` *(extension)* | `planner` *(extension)* |
| `executor` *(extension)* | `executor` *(extension)* |
| `researcher` *(extension)* | `researcher` *(extension)* |

The split has a single constraint: `conceptualization` and `supervision` are
**human-only** (a human frames the decision and signs off — and, per the
boundary, is always the *resolver*). Every other role is **open to both**
actor types — the five shared CRediT terms and all three extensions
(`planner`, `executor`, `researcher`), the last three naming work CRediT has
no term for. So `AgentRole` is exactly `HumanRole` minus those two human-only
terms. Validation MUST reject an `{actor, role}` whose `role` is not in the
enum for that actor's `type` — in practice, an agent tagged
`conceptualization` or `supervision`. Each role list is a **closed enum**
(resolved — see "Roles" under *Questions or objections* below). The full
definitions live in the rubric. In the reference implementation the two enums
and every exclusion are derived from a single role→allowed-types table, so the
lists cannot drift apart.

**Corrections use existing fields, not a new structure.** A mistake that was
caught and replaced is recorded the way ASTRA already records a discarded
option: the mistaken option carries `excluded: true` + `excluded_reason`, and
the attribution names *who caught it* via
`excluded_by: {actor: <human>, role: validation}`. ASTRA continues to record
final **state**; the *history* of how that state was reached stays in the
capture layer (e.g. TRACE). This RFC deliberately proposes **no**
`corrections:` object and **no** new option-to-option relation beyond the
existing `requires` / `incompatible_with`.

**Enforcement split.** Following the spec's established division of labor:
the schema carries the vocabulary and every *structural* constraint (the
enums, the id patterns, the union shapes), and its `type`-keyed rules compile
into the published JSON Schema, where astra-spec's own test suite enforces
them. The generated Pydantic models do not compile LinkML rules or class-level
`any_of`, so **astra-tools' semantic layer is the runtime enforcement point**
for everything conditional or cross-referential: registry membership of every
attribution, role-legality for the actor's `type`, `excluded_by` ⇒
`excluded: true`, human/agent field consistency, and the at-least-one-id rule
on `ResearcherId`. This is the same split the spec already uses for
`excluded` / `excluded_reason` and the `from:`-alias rules.

Plain-language summary: *let an analysis optionally say who proposed and who
excluded each option, and let a universe optionally say who selected and who
reviewed each choice — with, if wanted, the role of each contribution (a
CRediT term or a flagged agent extension) — without changing anything about
how decisions or selections themselves are recorded.*

## Examples

**Analysis level** — the registry plus attributions that exercise all three
role classes: a human *framing* a decision (`conceptualization`, human-only),
an agent *proposing* an option it retrieved (`researcher`, an extension open
to both), and a rejected proposal the human ruled out (`methodology` /
`validation`, shared). Each attribution is a single `{actor, role}` value:

```yaml
actors:                              # NEW top-level key (optional)
  jane:
    type: human
    identifiers:                     # NEW: ResearcherId — grouped scholarly ids, not a lone orcid
      orcid: "0009-0000-0000-0000"   # any subset; at least one present
  assistant:
    type: agent
    model: claude-opus-5
    harness: claude-code
    version: "2026-07"

decisions:
  outlier_handling:
    label: "Outlier handling"
    rationale: "Whether flagged extreme rows stay in the training data."
    default: keep_all
    options:
      keep_all:
        label: "Keep all 150 rows"
        proposed_by: {actor: jane, role: conceptualization}   # NEW: human-only role — framing the "trust the curated data" stance
      drop_iqr:
        label: "Drop the 12 rows flagged by the 1.5 IQR rule"
        proposed_by: {actor: assistant, role: methodology}    # NEW
        excluded: true                                        # existing field
        excluded_reason: >-                                   # existing field
          The rows are real biological variation, not measurement error.
        excluded_by: {actor: jane, role: validation}          # NEW
  model:
    label: "Classifier"
    default: random_forest
    options:
      random_forest:
        label: "Random forest"
        proposed_by: {actor: jane, role: methodology}         # NEW
      svm:
        label: "SVM (RBF kernel)"
        proposed_by: {actor: assistant, role: researcher}     # NEW: `researcher` extension (open to both) — agent surfaced it from prior Iris baselines
```

The shorthand stays valid for anyone who does not want roles:

```yaml
        proposed_by: assistant   # bare actor id — the origin form, still accepted
```

A **corrected mistake** with no new machinery — the data-leakage catch is just
an excluded option whose exclusion is attributed to a `validation`
contribution:

```yaml
  scaling:
    label: "Feature scaling"
    default: standard_after_split
    options:
      standard_after_split:
        label: "StandardScaler, fit on the training split only"
        proposed_by: {actor: jane, role: methodology}         # NEW
      standard_before_split:
        label: "StandardScaler, fit on the FULL dataset before the split"
        proposed_by: {actor: assistant, role: methodology}    # NEW
        excluded: true                                        # existing field — how a corrected mistake is recorded
        excluded_reason: >-                                   # existing field
          Data leakage: fitting before the train/test split let test-set
          statistics contaminate the training features (0.97 -> 0.94 after refit).
        excluded_by: {actor: jane, role: validation}          # NEW — the actor who caught it
```

**Universe level** — a selection where an agent picked the model and a human
signed off, alongside a plain-shorthand selection that carries no attribution.
The `{actor, role}` value and the `actors:` registry are the same as above:

```yaml
id: baseline
description: Default configuration using standard practices.
decisions:
  scaling:                                             # object form (NEW)
    option_id: standard_after_split
    selected_by: {actor: jane, role: methodology}      # NEW
  model:
    option_id: random_forest
    selected_by: {actor: assistant, role: methodology} # NEW: the agent proposed the pick ...
    reviewed_by: {actor: jane, role: validation}       # NEW: ... and a human signed off
  outlier_handling: keep_all                           # shorthand still valid (no attribution)
```

Before/after for a reader: today the option blocks lose *who proposed* / *who
excluded* and the universe selections are bare `decision: option`; after,
those facts (and their roles) are recoverable, every other field is
byte-for-byte unchanged, and any selection can keep the untouched shorthand.

Every `role` above is legal for its actor's `type` — `assistant` (an agent)
with `methodology`, `jane` with `validation`, and so on. The type split is
what makes the following *invalid*, caught by validation rather than by
convention:

```yaml
proposed_by: {actor: assistant, role: conceptualization}  # REJECTED — conceptualization is human-only
reviewed_by: {actor: assistant, role: supervision}        # REJECTED — supervision is human-only
proposed_by: {actor: assistant, role: executor}           # OK — executor is open to both types
```

## Implementation implications & migration

- **`src/astra/schema/`** (LinkML, schema id `https://w3id.org/astra/analysis`):
  add an optional `actors` map to the `Analysis` class; add an `Actor` class
  (with `human` / `agent` variants, expressed via `type`-keyed validation
  rules rather than subclassing) and a small `Attribution` class
  `{actor, role}` — both live in a **new `actor.yaml` module** imported by
  `analysis.yaml` *and* `universe.yaml`, because `Attribution` is shared by
  `Option` and `DecisionSelection` and `universe.yaml` cannot import
  `analysis.yaml` without a cycle (`analysis` already imports `universe`).
  Resulting import DAG: `actor ← universe ← analysis` and `actor ← analysis`.
  - The `human` variant carries a `ResearcherId` class (slots `orcid`,
    `arxiv`, `openalex`, `wikidata`, `google_scholar` — each optional, with a
    declared at-least-one constraint) instead of a bare `orcid` scalar; the
    `agent` variant keeps `model` + `harness` + `version`. Each id slot may
    pin its own `pattern` (e.g. the ORCID shape — no checksum).
  - On the `Option` class, add optional slots `proposed_by` and `excluded_by`,
    each with range `union(string, Attribution)` (the string is the actor-id
    shorthand).
  - On the `DecisionSelection` class, add optional slots `selected_by` and
    `reviewed_by` with the same `union(string, Attribution)` range, and give
    the `decisions` slot on **both** `Universe` and `UniverseNode` an explicit
    `union(string, DecisionSelection)` value form.
  - **No parallel `*_role` slots** anywhere — the role lives inside the value.
  - Define two role enums, `HumanRole` and `AgentRole`. They differ only in
    the two human-only terms: `conceptualization` and `supervision` are in
    `HumanRole` only; every other role — the five shared CRediT terms plus all
    three extensions (`planner`, `executor`, `researcher`) — is in both. The
    `Attribution.role` slot is validated against the enum matching the
    referenced actor's `type`; because a slot's legal range depends on another
    object's `type`, this is expressed as `any_of` the two enums with the
    type-narrowing enforced by `astra-tools`.
- **Why the explicit union on `decisions` matters.** Today's shorthand
  (`decision_id: option_id`) exists because `DecisionSelection` is a LinkML
  "simple dict" class (identifier + exactly one required slot), which the
  generators special-case into `dict[str, Union[str, DecisionSelection]]`.
  Adding `selected_by` / `reviewed_by` removes that special case, and the
  generated models silently drop the scalar arm — breaking every existing
  universe file. Declaring `any_of: [string, DecisionSelection]` on the slot
  restores the union explicitly. (Verified against the generators; this is
  the one place where "additive" requires an explicit act to stay additive.)
- **Generated datamodels**: regenerate from the schema; all new slots
  optional. Tooling must parse both universe forms (scalar shorthand and
  object), injecting the map key as `decision_id` for the object form.
- **`astra-tools` / validation** (the runtime enforcement point — see
  *Enforcement split*): accept both the scalar and object forms; validate that
  the actor id (scalar, or the object's `actor`) references an id in an
  `actors:` registry in scope, that any `role` is legal for that actor's
  `type`, that `excluded_by` only appears on options marked `excluded: true`,
  that human/agent actors carry only their variant's fields, and that a
  present `identifiers` record is non-empty. Absence of any actor field is
  valid.
- **Docs**: add the actor fields to the Option, Analysis, and
  DecisionSelection field references; ship the Attribution Rubric as
  non-normative guidance.
- **Compatibility & bump**: backward compatible — every existing `astra.yaml`
  and universe file remains valid and unchanged in meaning, and no existing
  field changes shape (the universe `decisions` slot *gains* an accepted
  object form without dropping the scalar). Under the versioning policy this
  is a **minor** bump *provided* the union is implemented; requiring the
  object form instead would make it a **major** bump, which the union is
  designed to avoid. No migration is required.
- **Reference implementation**: the actor-layer branches of the `astra-spec`
  and `astra-tools` forks accompanying this RFC, from which the examples above
  are taken. <!-- TODO: link the fork branches -->

## Questions or objections

- **Union vs. required object for universe selections.** Keeping the scalar
  shorthand avoids churn in every existing universe, but two shapes for one
  field cost tooling complexity. Worth it? *(Open.)*
- **Does `reviewed_by` presuppose an agent `selected_by`?** Human review is
  most meaningful over an agent's pick, but a human reviewing another human's
  pick is also valid. Should the schema constrain this, or leave it to the
  rubric? *(Open.)*
- **Roles: closed enum or free string?** A closed CRediT-subset enum is safer
  for tooling; a free string is more flexible for domains with unusual
  contributions. *(Resolved — **closed enum**. Validation rejects any role
  outside the referenced actor-type's enum; both enums and every exclusion are
  derived from a single role→allowed-types table in the reference
  implementation so the lists cannot drift.)*
- **`ResearcherId`: named slots or a scheme/value list?** Named slots
  (`orcid`, `arxiv`, `openalex`, `wikidata`, `google_scholar`) are
  self-documenting and let each id carry its own validation `pattern`, but
  adding a new scheme means a schema edit. A generic
  `identifiers: [{scheme, value}]` list (scheme drawn from an enum) is
  open-ended and linked-data-native, at the cost of weaker per-scheme
  validation. The RFC currently proposes named slots. *(Open.)*
- **Extension roles in-spec or rubric-only?** `planner` / `executor` /
  `researcher` have no CRediT equivalent. *(Resolved — in-spec: enumerated as
  extension roles and open to both actor types; the two role enums are closed,
  per "Roles" above.)*
- **Accountability boundary.** The rubric holds that agents may *propose* and
  *execute* any role but a human must be the *resolver* and hold final
  responsibility. *(Partly resolved — the schema now enforces the one hard
  type constraint: `conceptualization` and `supervision` are human-only.
  Still open, and left to the rubric: the "resolver is human" rule itself,
  which the `{actor, role}` shape does not encode — no attribution field
  currently names a resolver.)*

## Appendix — CRediT coverage

ASTRA's role vocabulary (Proposal §5) is a deliberate *subset* of CRediT: it
keeps only the terms that attach to a **single decision**, and adds three
extension roles for work CRediT has no term for. This table records the full
mapping so the subset is auditable — including the roles intentionally left
out. "May be held by" repeats the actor-type split from §5.

| CRediT role | In ASTRA? | ASTRA `role` | May be held by | Kept / not — why |
|---|:--:|---|---|---|
| Conceptualization | ✓ | `conceptualization` | human | frames the decision — human-owned |
| Data curation | ✓ | `data_curation` | human, agent | selects or vouches for the data |
| Formal analysis | ✓ | `formal_analysis` | human, agent | runs the analysis, computes the result |
| Funding acquisition | — | — | — | analysis-level; never attaches to a single decision |
| Investigation | — | — | — | data generation/collection is upstream; at decision level it collapses into `data_curation` |
| Methodology | ✓ | `methodology` | human, agent | proposes an option / designs the method |
| Project administration | — | — | — | analysis-level coordination, not a decision |
| Resources | — | — | — | provisioning compute/materials, not a decision |
| Software | ✓ | `software` | human, agent | writes or maintains the recipe code |
| Supervision | ✓ | `supervision` | human | oversees the work, final sign-off — human-owned |
| Validation | ✓ | `validation` | human, agent | checks, rules out an option, catches an error |
| Visualization | — | — | — | output-level, not a decision |
| Writing – original draft | — | — | — | paper-level, not a decision |
| Writing – review & editing | — | — | — | edits the rationale prose, not the decision itself |

Three **extension roles** have no CRediT term (flagged as extensions); all
three are open to both actor types:

| ASTRA `role` | May be held by | Meaning |
|---|---|---|
| `planner` | human, agent | decomposes the task, sequences sub-analyses |
| `executor` | human, agent | runs code or tools, returns results |
| `researcher` | human, agent | retrieves prior work, assembles evidence / context |

**Coverage: 7 of CRediT's 14 roles are used** (2 human-only, 5 shared), plus
3 extension roles, all open to both actor types. The other 7 CRediT roles do
not attach to a single decision and are intentionally not used.

## References

- [RFC-0002 — Decouple analysis reports from astra.yaml](0002-decouple-reports.md),
  in particular the *Authorship — deferred* resolution this proposal is scoped
  against.
- CRediT — Contributor Roles Taxonomy, https://credit.niso.org
- ORCID — https://orcid.org
- Sibling researcher identifiers grouped by `ResearcherId` — arXiv author id
  (https://arxiv.org/a), OpenAlex (https://openalex.org), Wikidata
  (https://www.wikidata.org), Google Scholar profiles
  (https://scholar.google.com/citations)
- W3C PROV-O (https://www.w3.org/TR/prov-o/) — agents, software agents, and
  attribution relations; the conceptual frame this proposal instantiates
  minimally.
- The Attribution Rubric — non-normative companion travelling with this RFC.
- TRACE — the decision-capture layer that retains correction/revision history.
