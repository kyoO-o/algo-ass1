# graph/road_graph.py
from typing import Dict, Tuple, List
from .models import Edge

class RoadGraph:
    """
    Node ба ирмэгийн энгийн граф.
    nodes: node_id -> (lon, lat)
    adj:   node_id -> List[Edge]
    """
    def __init__(self) -> None:
        self.nodes: Dict[int, Tuple[float, float]] = {}
        self.adj: Dict[int, List[Edge]] = {}

    def add_node(self, nid: int, lon: float, lat: float) -> None:
        if nid not in self.nodes:
            self.nodes[nid] = (lon, lat)
            self.adj[nid] = []

    def add_edge(self, u: int, v: int, w: float, oneway: str = "no") -> None:
        """
        OSM-н oneway-ийн утгыг зөв тайлбарлана.
        yes/true/1  -> зөвхөн u->v
        -1/reverse  -> зөвхөн v->u
        бусад        -> хоёр чиг
        """
        ow = (oneway or "no").strip().lower()
        if ow in ("yes", "1", "true"):
            self.adj[u].append(Edge(target=v, weight=w))
        elif ow in ("-1", "reverse"):
            self.adj[v].append(Edge(target=u, weight=w))
        else:
            self.adj[u].append(Edge(target=v, weight=w))
            self.adj[v].append(Edge(target=u, weight=w))

    def nearest_node(self, lon: float, lat: float) -> int:
        """
        (lon, lat)-д хамгийн ойр node_id.
        """
        best_id = -1
        best_dist = float("inf")
        for nid, (n_lon, n_lat) in self.nodes.items():
            d = (n_lon - lon) ** 2 + (n_lat - lat) ** 2
            if d < best_dist:
                best_dist = d
                best_id = nid
        return best_id
