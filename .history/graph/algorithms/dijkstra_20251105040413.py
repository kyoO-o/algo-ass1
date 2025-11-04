# graph/algorithms/dijkstra.py
import heapq
from typing import Dict, List, Optional, Tuple
from ..road_graph import RoadGraph

def dijkstra_shortest(graph: RoadGraph,
                      start: int,
                      goal: int) -> Tuple[List[int], float]:
    """
    Жинтэй граф дээрх хамгийн богино (жин хамгийн бага) зам.
    """
    dist: Dict[int, float] = {nid: float("inf") for nid in graph.nodes}
    parent: Dict[int, Optional[int]] = {nid: None for nid in graph.nodes}

    dist[start] = 0.0
    pq: List[Tuple[float, int]] = [(0.0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == goal:
            break
        for edge in graph.adj.get(u, []):
            v = edge.target
            nd = d + edge.weight
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))

    if dist[goal] == float("inf"):
        return [], float("inf")

    path = []
    cur: Optional[int] = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path, dist[goal]
