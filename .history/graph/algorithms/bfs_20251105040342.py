# graph/algorithms/bfs.py
from collections import deque
from typing import Dict, List, Optional
from ..road_graph import RoadGraph

def bfs_shortest_hops(graph: RoadGraph, start: int, goal: int) -> List[int]:
    """
    Хамгийн цөөн алхамтай зам (edge тоо хамгийн бага).
    """
    queue = deque([start])
    parent: Dict[int, Optional[int]] = {start: None}

    while queue:
        u = queue.popleft()
        if u == goal:
            break
        for edge in graph.adj.get(u, []):
            v = edge.target
            if v not in parent:
                parent[v] = u
                queue.append(v)

    if goal not in parent:
        return []

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path
