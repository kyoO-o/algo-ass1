# road_graph.py
"""
Улаанбаатарын замын сүлжээг shapefile-с уншиж граф үүсгээд
BFS, DFS, Dijkstra алгоритмуудыг ажиллуулдаг энгийн класс.
NetworkX, OSMnx ашиглаагүй.
"""

from collections import deque
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString


@dataclass
class Edge:
    target: int
    weight: float


@dataclass
class RoadGraph:
    # node_id -> (lon, lat)
    nodes: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    # node_id -> List[Edge]
    adj: Dict[int, List[Edge]] = field(default_factory=dict)

    @classmethod
    def from_shapefile(cls, shp_path: str) -> "RoadGraph":
        """
        OpenStreetMap -ын gis_osm_roads_free_1.shp -г уншаад
        автомашинаар явах боломжтой замаас граф үүсгэнэ.
        """
        gdf = gpd.read_file(shp_path)

        graph = cls()
        coord_to_id: Dict[Tuple[float, float], int] = {}

        def get_node_id(lon: float, lat: float) -> int:
            key = (round(lon, 6), round(lat, 6))  # ойролцоо цэгүүдийг нэгтгэх
            if key not in coord_to_id:
                nid = len(coord_to_id)
                coord_to_id[key] = nid
                graph.nodes[nid] = (lon, lat)
                graph.adj[nid] = []
            return coord_to_id[key]

        for _, row in gdf.iterrows():
            geom = row.geometry

            # Зарим баганууд нэртэй/үгүй байж болох тул .get ашиглая
            access = row.get("access", None)
            fclass = row.get("fclass", None)
            oneway = row.get("oneway", "no")

            # Машин орохгүй, явган зам г.м-г алгасна
            if access in ("no", "private"):
                continue
            if fclass in ("footway", "path", "track", "pedestrian",
                          "steps", "cycleway"):
                continue
            if geom is None:
                continue

            # MultiLineString байж болно
            if isinstance(geom, LineString):
                lines = [geom]
            elif isinstance(geom, MultiLineString):
                lines = list(geom)
            else:
                continue

            for line in lines:
                coords = list(line.coords)
                # polyline – олон цэгтэй, сегмент болгонд ирмэг үүсгэнэ
                for i in range(len(coords) - 1):
                    lon1, lat1 = coords[i]
                    lon2, lat2 = coords[i + 1]

                    u = get_node_id(lon1, lat1)
                    v = get_node_id(lon2, lat2)

                    # Жин: энд геометрийн уртыг градусаар шууд авлаа (жижиг талбай учраас OK).
                    # Жин бодит болгохыг хүсвэл тусдаа to_crs(epsg=3857) хийж, сегментын уртыг метрээр тооцоорой.
                    seg_len = line.length / (len(coords) - 1)

                    graph.add_edge(u, v, seg_len, oneway=str(oneway))

        return graph

    def add_edge(self, u: int, v: int, w: float, oneway: str = "no") -> None:
        self.adj[u].append(Edge(target=v, weight=w))
        # oneway != yes бол 2 чигтэй гэж үзнэ
        if oneway.lower() not in ("yes", "1", "true"):
            self.adj[v].append(Edge(target=u, weight=w))

    def nearest_node(self, lon: float, lat: float) -> int:
        """
        Өгөгдсөн (lon, lat)-д хамгийн ойр node_id-ийг хайна.
        (Энгийн O(N) хайлт – оюутны даалгаварт хангалттай.)
        """
        best_id = -1
        best_dist = float("inf")
        for nid, (n_lon, n_lat) in self.nodes.items():
            d = (n_lon - lon) ** 2 + (n_lat - lat) ** 2
            if d < best_dist:
                best_dist = d
                best_id = nid
        return best_id


# ----------------- Алгоритмууд -----------------

def bfs_shortest_hops(graph: RoadGraph, start: int, goal: int) -> List[int]:
    """
    BFS – хамгийн цөөн алхамтай зам (edge-ийн тоо хамгийн бага).
    Жин харгалзахгүй.
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

    # path reconstruct
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def dfs_all_paths(graph: RoadGraph,
                  start: int,
                  goal: int,
                  max_paths: int = 10,
                  max_depth: int = 20000,
                  max_expanded: int = 200000) -> List[List[int]]:
    """
    Итератив DFS – боломжит simple path-уудыг хайна (циклийг зайлсхийхээр visited=path).
    Рекурс ашиглахгүй тул RecursionError гарахгүй.
    max_paths: хэдэн зам олмогц зогсох
    max_depth: замын уртын дээд хязгаар (аюулгүйн таслагч)
    max_expanded: тэлсэн зангилааны дээд хязгаар (аюулгүйн таслагч)
    """
    paths: List[List[int]] = []
    if start == goal:
        return [[start]]

    # path = [start], stack дээр (node, iterator) хэлбэртэй хадгална
    path: List[int] = [start]
    stack: List[Tuple[int, iter]] = [(start, iter(graph.adj.get(start, [])))]
    visited = set(path)  # зөвхөн path дахь цэгүүдийг 'зочилсон' гэж тооцно
    expanded = 0

    while stack:
        u, it = stack[-1]

        # Зорилтот цэгт хүрсэн үед: замыг бүртгээд нэг алхам ухарна
        if u == goal:
            paths.append(path.copy())
            if len(paths) >= max_paths:
                return paths
            # backtrack: одоогийн u-г буцааж ухрах
            stack.pop()
            visited.remove(u)
            path.pop()
            continue

        try:
            edge = next(it)
            v = edge.target

            # simple path хангах (циклийг таслах)
            if v in visited:
                continue

            # аюулгүйн уртын хязгаар
            if len(path) >= max_depth:
                continue

            # урагш ахих
            visited.add(v)
            path.append(v)
            stack.append((v, iter(graph.adj.get(v, []))))

            expanded += 1
            if expanded >= max_expanded:
                # Хэт том хайлтыг тасална – одоог хүртэл олдсон замуудыг буцаана
                break

        except StopIteration:
            # u-ийн бүх хөрш дууссан → backtrack
            stack.pop()
            visited.remove(u)
            path.pop()

    return paths



def dijkstra_shortest(graph: RoadGraph,
                      start: int,
                      goal: int) -> Tuple[List[int], float]:
    """
    Dijkstra – жинтэй граф дээрх хамгийн богино (жин хамгийн бага) зам.
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


# ----------------- Жижиг unit test -----------------

if __name__ == "__main__":
    # Жижиг test граф (гар аргаар)
    g = RoadGraph()
    # node-ууд
    g.nodes = {
        0: (0.0, 0.0),
        1: (1.0, 0.0),
        2: (2.0, 0.0),
        3: (1.0, 1.0),
    }
    g.adj = {0: [], 1: [], 2: [], 3: []}
    # A(0)-B(1)-C(2), B(1)-D(3)
    g.add_edge(0, 1, 1.0)
    g.add_edge(1, 2, 1.0)
    g.add_edge(1, 3, 1.0)

    print("BFS 0->2:", bfs_shortest_hops(g, 0, 2))
    print("Dijkstra 0->3:", dijkstra_shortest(g, 0, 3))
    print("DFS all paths 0->2:", dfs_all_paths(g, 0, 2, max_paths=5))
