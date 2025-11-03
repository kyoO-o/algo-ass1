from fastapi import FastAPI
from pydantic import BaseModel
from collections import deque
import networkx as nx
import heapq
import time, tracemalloc

app = FastAPI()

# Sample Graph
G = nx.Graph()
edges = [
    ('A', 'B', 1),
    ('A', 'C', 2),
    ('B', 'D', 4),
    ('C', 'D', 1),
    ('B', 'E', 2),
    ('D', 'E', 1)
]
for u, v, w in edges:
    G.add_edge(u, v, weight=w)

class PathRequest(BaseModel):
    start: str
    goal: str

# ---------------- BFS ----------------
def bfs_shortest_steps(graph, start, goal):
    queue = deque([[start]])
    visited = set()
    all_paths = []

    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == goal:
            all_paths.append(path)
        if node not in visited:
            visited.add(node)
            for neighbor in graph.neighbors(node):
                if neighbor not in path:
                    queue.append(path + [neighbor])
    min_steps_path = min(all_paths, key=len)
    return all_paths, min_steps_path

# ---------------- DFS ----------------
def dfs_all_paths(graph, start, goal, path=[]):
    path = path + [start]
    if start == goal:
        return [path]
    paths = []
    for neighbor in graph.neighbors(start):
        if neighbor not in path:
            new_paths = dfs_all_paths(graph, neighbor, goal, path)
            paths.extend(new_paths)
    return paths

# ---------------- Dijkstra ----------------
def dijkstra_shortest_path(graph, start, goal):
    queue = [(0, start, [start])]
    visited = set()
    all_paths = []

    while queue:
        cost, node, path = heapq.heappop(queue)
        if node == goal:
            all_paths.append((path, cost))
        if node not in visited:
            visited.add(node)
            for neighbor in graph.neighbors(node):
                w = graph[node][neighbor]['weight']
                heapq.heappush(queue, (cost + w, neighbor, path + [neighbor]))
    min_path, min_cost = min(all_paths, key=lambda x: x[1])
    return all_paths, min_path

# ---------------- API ----------------
@app.post("/bfs")
def api_bfs(req: PathRequest):
    tracemalloc.start()
    t0 = time.time()
    all_paths, min_steps = bfs_shortest_steps(G, req.start, req.goal)
    t1 = time.time()
    mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"all_paths": all_paths, "min_steps": min_steps, "runtime": t1-t0, "memory": mem[1]}

@app.post("/dfs")
def api_dfs(req: PathRequest):
    tracemalloc.start()
    t0 = time.time()
    all_paths = dfs_all_paths(G, req.start, req.goal)
    t1 = time.time()
    mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    min_steps = min(all_paths, key=len)
    return {"all_paths": all_paths, "min_steps": min_steps, "runtime": t1-t0, "memory": mem[1]}

@app.post("/dijkstra")
def api_dijkstra(req: PathRequest):
    tracemalloc.start()
    t0 = time.time()
    all_paths, min_path = dijkstra_shortest_path(G, req.start, req.goal)
    t1 = time.time()
    mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"all_paths": [p for p,_ in all_paths], "min_path": min_path, "runtime": t1-t0, "memory": mem[1]}
