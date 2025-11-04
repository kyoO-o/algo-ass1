# graph/algorithms/dfs.py
from typing import List, Tuple, Dict, Optional, Iterable
from ..road_graph import RoadGraph

def dfs_all_paths(graph: RoadGraph,
                  start: int,
                  goal: int,
                  max_paths: int = 10,
                  max_depth: int = 20000,
                  max_expanded: int = 200000) -> List[List[int]]:
    """
    Итератив DFS – simple path хайна. Зорилт руу ойр хөршүүдийг түрүүлж шалгана.
    """
    paths: List[List[int]] = []
    if start == goal:
        return [[start]]

    goal_lon, goal_lat = graph.nodes[goal]

    def neighbor_iter(u: int) -> Iterable:
        nbrs = graph.adj.get(u, [])
        return iter(sorted(
            nbrs,
            key=lambda e: (graph.nodes[e.target][0] - goal_lon) ** 2 +
                          (graph.nodes[e.target][1] - goal_lat) ** 2
        ))

    path: List[int] = [start]
    stack: List[Tuple[int, Iterable]] = [(start, neighbor_iter(start))]
    visited = set(path)
    expanded = 0

    while stack:
        u, it = stack[-1]

        if u == goal:
            paths.append(path.copy())
            if len(paths) >= max_paths:
                return paths
            stack.pop()
            visited.remove(u)
            path.pop()
            continue

        try:
            edge = next(it)
            v = edge.target
            if v in visited:
                continue
            if len(path) >= max_depth:
                continue

            visited.add(v)
            path.append(v)
            stack.append((v, neighbor_iter(v)))

            expanded += 1
            if expanded >= max_expanded:
                break

        except StopIteration:
            stack.pop()
            visited.remove(u)
            path.pop()

    return paths
