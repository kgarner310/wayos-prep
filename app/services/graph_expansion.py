"""Risk Theme Graph expansion service.

Provides query-time graph expansion to discover related risk themes,
coverages, and departments from the risk_themes / risk_theme_edges tables.
"""

import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.models import RiskTheme, RiskThemeEdge

logger = logging.getLogger(__name__)

# Minimum edge weight to include in expansion
MIN_EXPANSION_WEIGHT = 0.30

# Maximum expansion depth (1 = direct neighbors only)
MAX_DEPTH = 2

# Maximum expanded nodes per query
MAX_EXPANDED_NODES = 15


def expand_risk_graph(
    db: Session,
    seed_themes: list[str],
    depth: int = 1,
    min_weight: float = MIN_EXPANSION_WEIGHT,
) -> dict:
    """Expand seed themes through the risk graph.

    Args:
        db: Database session.
        seed_themes: List of theme names to expand from (e.g., risk_theme values,
                     industry names, department names).
        depth: How many hops to traverse (1 = direct neighbors, 2 = neighbors of neighbors).
        min_weight: Minimum edge weight to follow.

    Returns:
        dict with keys:
            - expanded_themes: list of dicts with name, node_type, weight, path
            - expanded_coverages: list of coverage names discovered
            - expanded_risk_themes: list of risk_theme names discovered
            - seed_count: number of seed nodes found in graph
            - expansion_hops: actual depth used
    """
    depth = min(depth, MAX_DEPTH)

    # Look up seed nodes
    seed_nodes = (
        db.query(RiskTheme)
        .filter(RiskTheme.name.in_(seed_themes))
        .all()
    )

    if not seed_nodes:
        return _empty_result()

    seed_ids = {n.id for n in seed_nodes}
    seed_names = {n.name for n in seed_nodes}

    # BFS expansion
    visited = {}  # theme_id -> (weight, path)
    for node in seed_nodes:
        visited[node.id] = (1.0, [node.name])

    frontier = list(seed_ids)

    for hop in range(depth):
        if not frontier:
            break

        # Get all edges from frontier nodes
        edges = (
            db.query(RiskThemeEdge)
            .filter(
                RiskThemeEdge.from_theme_id.in_(frontier),
                RiskThemeEdge.weight >= min_weight,
            )
            .all()
        )

        next_frontier = []
        for edge in edges:
            if edge.to_theme_id in visited and edge.to_theme_id not in seed_ids:
                # Already visited via a different path — keep the higher weight
                existing_weight = visited[edge.to_theme_id][0]
                new_weight = float(edge.weight) * visited[edge.from_theme_id][0]
                if new_weight > existing_weight:
                    parent_path = visited[edge.from_theme_id][1]
                    visited[edge.to_theme_id] = (new_weight, parent_path + [f"--{edge.edge_type}-->"])
                continue

            if edge.to_theme_id not in visited:
                parent_weight = visited[edge.from_theme_id][0]
                propagated_weight = float(edge.weight) * parent_weight
                parent_path = visited[edge.from_theme_id][1]

                # Load the target node
                target = db.query(RiskTheme).filter(RiskTheme.id == edge.to_theme_id).first()
                if target:
                    visited[edge.to_theme_id] = (
                        propagated_weight,
                        parent_path + [f"--{edge.edge_type}-->", target.name],
                    )
                    next_frontier.append(edge.to_theme_id)

        frontier = next_frontier

    # Also traverse reverse edges (to_theme_id -> from_theme_id)
    frontier_rev = list(seed_ids)
    for hop in range(depth):
        if not frontier_rev:
            break

        reverse_edges = (
            db.query(RiskThemeEdge)
            .filter(
                RiskThemeEdge.to_theme_id.in_(frontier_rev),
                RiskThemeEdge.weight >= min_weight,
            )
            .all()
        )

        next_frontier_rev = []
        for edge in reverse_edges:
            if edge.from_theme_id not in visited:
                parent_weight = visited.get(edge.to_theme_id, (1.0, []))[0]
                propagated_weight = float(edge.weight) * parent_weight
                parent_path = visited.get(edge.to_theme_id, (1.0, ["?"]))[1]

                target = db.query(RiskTheme).filter(RiskTheme.id == edge.from_theme_id).first()
                if target:
                    visited[edge.from_theme_id] = (
                        propagated_weight,
                        [target.name, f"--{edge.edge_type}-->"] + parent_path,
                    )
                    next_frontier_rev.append(edge.from_theme_id)

        frontier_rev = next_frontier_rev

    # Build result
    expanded = []
    expanded_coverages = []
    expanded_risk_themes = []

    # Load all visited nodes
    all_theme_ids = [tid for tid in visited if tid not in seed_ids]
    if all_theme_ids:
        nodes = db.query(RiskTheme).filter(RiskTheme.id.in_(all_theme_ids)).all()
        node_map = {n.id: n for n in nodes}

        for tid in all_theme_ids:
            node = node_map.get(tid)
            if not node:
                continue
            weight, path = visited[tid]
            expanded.append({
                "name": node.name,
                "node_type": node.node_type,
                "display_label": node.display_label or node.name.replace("_", " ").title(),
                "weight": round(weight, 4),
                "path": path,
            })

            if node.node_type == "coverage":
                expanded_coverages.append(node.name)
            elif node.node_type == "risk_theme":
                expanded_risk_themes.append(node.name)

    # Sort by weight descending, limit
    expanded.sort(key=lambda x: x["weight"], reverse=True)
    expanded = expanded[:MAX_EXPANDED_NODES]

    return {
        "expanded_themes": expanded,
        "expanded_coverages": expanded_coverages,
        "expanded_risk_themes": expanded_risk_themes,
        "seed_count": len(seed_nodes),
        "expansion_hops": depth,
    }


def get_expansion_seeds(
    industry: str,
    state: str,
    entity_type: str | None = None,
    public_entity_type: str | None = None,
    department: str | None = None,
) -> list[str]:
    """Build the list of seed theme names from query parameters."""
    seeds = [industry.lower()]

    if entity_type:
        seeds.append(entity_type.lower())
    if public_entity_type:
        seeds.append(public_entity_type.lower())
    if department:
        seeds.append(department.lower())

    return seeds


def _empty_result() -> dict:
    return {
        "expanded_themes": [],
        "expanded_coverages": [],
        "expanded_risk_themes": [],
        "seed_count": 0,
        "expansion_hops": 0,
    }
