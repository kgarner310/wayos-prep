"""Risk Theme Graph expansion service.

Provides query-time graph expansion to discover related risk themes,
coverages, question categories, and departments using denormalized
edges in the risk_theme_edges table.
"""

import logging

from sqlalchemy.orm import Session

from app.models.models import RiskTheme, RiskThemeEdge

logger = logging.getLogger(__name__)

# Minimum edge weight to include in expansion
MIN_EXPANSION_WEIGHT = 0.30

# Maximum expansion depth (1 = direct neighbors only)
MAX_DEPTH = 2

# Maximum expanded nodes per query
MAX_EXPANDED_NODES = 20


def expand_risk_graph(
    db: Session,
    seed_values: list[str],
    depth: int = 1,
    min_weight: float = MIN_EXPANSION_WEIGHT,
) -> dict:
    """Expand seed values through the denormalized risk graph.

    Args:
        db: Database session.
        seed_values: List of node values to expand from (e.g., industry names,
                     department names, risk themes, account traits).
        depth: How many hops to traverse (1 = direct neighbors).
        min_weight: Minimum edge weight to follow.

    Returns:
        dict with keys:
            - expanded_themes: list of dicts with name, node_type, weight, path
            - expanded_coverages: list of coverage names discovered
            - expanded_risk_themes: list of risk_theme names discovered
            - expanded_question_categories: list of question_category names discovered
            - seed_count: number of seed values matched
            - expansion_hops: actual depth used
    """
    depth = min(depth, MAX_DEPTH)

    if not seed_values:
        return _empty_result()

    seed_set = set(v.lower() for v in seed_values)

    # Track visited: node_value -> (weight, node_type, path)
    visited = {}
    for sv in seed_set:
        visited[sv] = (1.0, "seed", [sv])

    frontier = list(seed_set)

    for hop in range(depth):
        if not frontier:
            break

        # Get forward edges: from_node_value IN frontier
        edges = (
            db.query(RiskThemeEdge)
            .filter(
                RiskThemeEdge.from_node_value.in_(frontier),
                RiskThemeEdge.weight >= min_weight,
            )
            .all()
        )

        next_frontier = []
        for edge in edges:
            target = edge.to_node_value
            parent_weight = visited.get(edge.from_node_value, (1.0, "seed", []))[0]
            propagated_weight = float(edge.weight) * parent_weight
            parent_path = visited.get(edge.from_node_value, (1.0, "seed", ["?"]))[2]
            new_path = parent_path + [f"--{edge.edge_type}-->", target]

            if target in seed_set:
                # Don't re-expand seed nodes
                continue

            if target in visited:
                # Already visited — keep higher weight
                if propagated_weight > visited[target][0]:
                    visited[target] = (propagated_weight, edge.to_node_type, new_path)
            else:
                visited[target] = (propagated_weight, edge.to_node_type, new_path)
                next_frontier.append(target)

        # Also check reverse edges (to_node_value IN frontier)
        reverse_edges = (
            db.query(RiskThemeEdge)
            .filter(
                RiskThemeEdge.to_node_value.in_(frontier),
                RiskThemeEdge.weight >= min_weight,
            )
            .all()
        )

        for edge in reverse_edges:
            target = edge.from_node_value
            parent_weight = visited.get(edge.to_node_value, (1.0, "seed", []))[0]
            propagated_weight = float(edge.weight) * parent_weight
            parent_path = visited.get(edge.to_node_value, (1.0, "seed", ["?"]))[2]
            new_path = [target, f"--{edge.edge_type}-->"] + parent_path

            if target in seed_set:
                continue

            if target in visited:
                if propagated_weight > visited[target][0]:
                    visited[target] = (propagated_weight, edge.from_node_type, new_path)
            else:
                visited[target] = (propagated_weight, edge.from_node_type, new_path)
                next_frontier.append(target)

        frontier = next_frontier

    # Build result from non-seed visited nodes
    expanded = []
    expanded_coverages = []
    expanded_risk_themes = []
    expanded_question_categories = []

    for value, (weight, node_type, path) in visited.items():
        if value in seed_set:
            continue

        expanded.append({
            "name": value,
            "node_type": node_type,
            "display_label": value.replace("_", " ").title(),
            "weight": round(weight, 4),
            "path": path,
        })

        if node_type == "coverage":
            expanded_coverages.append(value)
        elif node_type == "risk_theme":
            expanded_risk_themes.append(value)
        elif node_type == "question_category":
            expanded_question_categories.append(value)

    # Sort by weight descending, limit
    expanded.sort(key=lambda x: x["weight"], reverse=True)
    expanded = expanded[:MAX_EXPANDED_NODES]

    # Look up display labels from risk_themes table for top results
    top_names = [e["name"] for e in expanded]
    if top_names:
        nodes = db.query(RiskTheme).filter(RiskTheme.name.in_(top_names)).all()
        label_map = {n.name: n.display_label for n in nodes if n.display_label}
        for e in expanded:
            if e["name"] in label_map:
                e["display_label"] = label_map[e["name"]]

    return {
        "expanded_themes": expanded,
        "expanded_coverages": expanded_coverages,
        "expanded_risk_themes": expanded_risk_themes,
        "expanded_question_categories": expanded_question_categories,
        "seed_count": len(seed_set),
        "expansion_hops": depth,
    }


def get_expansion_seeds(
    industry: str,
    state: str,
    entity_type: str | None = None,
    public_entity_type: str | None = None,
    department: str | None = None,
    account_traits: list[str] | None = None,
) -> list[str]:
    """Build the list of seed values from query parameters."""
    seeds = [industry.lower()]

    if entity_type:
        seeds.append(entity_type.lower())
    if public_entity_type:
        seeds.append(public_entity_type.lower())
    if department:
        seeds.append(department.lower())
    if account_traits:
        seeds.extend(t.lower() for t in account_traits)

    return seeds


def _empty_result() -> dict:
    return {
        "expanded_themes": [],
        "expanded_coverages": [],
        "expanded_risk_themes": [],
        "expanded_question_categories": [],
        "seed_count": 0,
        "expansion_hops": 0,
    }
