"""
population_policy.py — Step 6: OpenEvolve Asymmetric Island Migration Strategy

Role:
    Implements the directed, one-way source→sink island migration hook for
    the OpenEvolve evolutionary search. Enforces the asymmetric gene flow
    topology specified in the Step 6 design:
        - Island 0 (Core Conformal Branch): Source — mathematical purity preserved
        - Island 1 (Experimental Radical Branch): Sink — receives Core breakthroughs

Gate Stage:    Step 6 (OpenEvolve Evaluator & Fitness Engine)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md Section 5
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

Inputs:
    snapshot (PopulationSnapshot) — immutable frozen view of all island programs
    and their metrics at the point of migration trigger.

Outputs:
    list[MigrationMove] — directed migration instructions consumed by
    openevolve.database.migrate_programs().

AGENTS.md Compliance:
    Rule #2 — No hardcoded metrics; Island 0 elite selected via live combined_score
    Rule #3 — Module executed by openevolve within ./.venv runtime
    Rule #4 — Self-documenting header, inline logic comments
    Rule #5 — Uses openevolve.population types directly; no custom reimplementation
"""

from openevolve.population import MigrationMove, PopulationSnapshot, PopulationStrategy


# ─────────────────────────────────────────────────────────────────────────────
# DIRECTED SOURCE→SINK MIGRATION FUNCTION
# Implements the asymmetric gene flow hook consumed by OpenEvolve's database
# via PopulationStrategy.migrate. Called every `migration_interval` generations.
# ─────────────────────────────────────────────────────────────────────────────


def directed_source_sink_migration(snapshot: PopulationSnapshot) -> list[MigrationMove]:
    """
    Enforces asymmetric one-way gene flow across 3 specialized branches:
        Island 0 (Core Conformal Branch) → Island 1 (Continuous Complexity Radical)
        Island 0 (Core Conformal Branch) → Island 2 (InferLine-Conformal Hybrid Radical)
        Island 1 & Island 2 → Island 0: STRICTLY FORBIDDEN

    Rationale:
        The Core branch evolves mathematically grounded conformal policies with
        strict Adaptive Conformal Inference (ACI) semantics.
        Island 1 explores continuous complexity dynamic factors (dp_fast/dt, acceleration).
        Island 2 builds on InferLine's proven traffic envelope foundation to ensure discovered
        policies are never worse than InferLine on trivial jobs, but strictly superior on complexity shocks.

        One-way migration ensures that Core breakthroughs (validated by Stage 3
        authoritative evaluation) seed both radical branches, while radical
        explorations can never corrupt the Core's mathematically sound lineage.

    Selection Rule:
        Migrate the single highest-fitness program from Island 0 into Island 1 and Island 2.
        Fitness is read from the live `combined_score` metric (the primary MAP-Elites
        ranking signal) to avoid stale or hardcoded thresholds.

    Args:
        snapshot: Immutable frozen view of all island programs. Do NOT mutate.

    Returns:
        list[MigrationMove]: Zero or one migration move. Zero moves are returned
        if Island 0 is empty (during the seed bootstrap phase).
    """
    moves: list[MigrationMove] = []

    # ── Identify Island 0 programs ────────────────────────────────────────────
    # snapshot.islands is a tuple of frozensets (one per island index).
    # Guard against the bootstrap case where Island 0 may not yet have programs.
    if not snapshot.islands or len(snapshot.islands) == 0:
        return moves
    island_0_pids = list(snapshot.islands[0])
    if not island_0_pids:
        # No programs available on Island 0 yet — skip this migration trigger.
        return moves

    # ── Select the Elite Core Program by combined_score ──────────────────────
    # combined_score is the primary fitness signal used by OpenEvolve's MAP-Elites
    # archive. Fall back to -inf if a program has no score (newly bootstrapped seed).
    best_p0_id = max(
        island_0_pids,
        key=lambda pid: snapshot.programs[pid].metrics.get("combined_score", float("-inf")),
    )

    # ── Emit One-Way Migration Moves to Island 1 & Island 2 ─────────────────
    # MigrationMove(program_id, target_island) instructs database.migrate_programs()
    # to copy the Core elite into both radical branches' candidate pools:
    #   - Island 1: Continuous Complexity Dynamic Radical
    #   - Island 2: InferLine-Conformal Hybrid Radical
    # Island 0 is NEVER listed as a target — preserving Core mathematical purity.
    if len(snapshot.islands) > 1:
        moves.append(MigrationMove(program_id=best_p0_id, target_island=1))
    if len(snapshot.islands) > 2:
        moves.append(MigrationMove(program_id=best_p0_id, target_island=2))

    return moves


# ─────────────────────────────────────────────────────────────────────────────
# POPULATION STRATEGY REGISTRATION
# Wraps the migration function into a PopulationStrategy object, which is
# passed to openevolve.OpenEvolve() in the run_evolution.py launcher.
# ─────────────────────────────────────────────────────────────────────────────

custom_population_strategy = PopulationStrategy(
    migrate=directed_source_sink_migration,
    # All other optional hooks (admit, replace_cell, archive, evict, migration_due)
    # are left as None — OpenEvolve defaults handle them appropriately.
)
