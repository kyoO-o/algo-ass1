import logging, json, time
from rich.logging import RichHandler
from rich.traceback import install as rich_traceback_install
from flask import Flask, request, jsonify, render_template, g

# --- Rich tracebacks (өнгө, context) ---
rich_traceback_install(show_locals=False, width=120)

# --- Rich logger ---
LOG_LEVEL = logging.INFO
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(message)s",
    datefmt="[%H:%M:%S]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)
logger = logging.getLogger("uv-logger")

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# FIRST create app here ↓↓↓
app = Flask(__name__)
app.logger.setLevel("INFO")

# NOW add before/after decorators ↓↓↓
@app.before_request
def _start_timer():
    g._t0 = time.perf_counter()

@app.after_request
def _log_request(resp):
    try:
        dur_ms = (time.perf_counter() - getattr(g, "_t0", time.perf_counter())) * 1000
        method = request.method
        path = request.path
        status = resp.status_code
        q = request.query_string.decode() if request.query_string else ""
        if status >= 500:
            status_str = f"[bold red]{status}[/]"
        elif status >= 400:
            status_str = f"[yellow]{status}[/]"
        else:
            status_str = f"[green]{status}[/]"

        meta = {}
        if path == "/api/path" and resp.is_json:
            try:
                data = resp.get_json()
                if isinstance(data, dict):
                    meta = {
                        "alg": data.get("algorithm"),
                        "nodes": len(data.get("nodes", [])),
                        "weight": data.get("total_weight"),
                    }
            except:
                pass

        logger.info(
            f"[bold cyan]{method}[/] {path}"
            + (f"?{q}" if q else "")
            + f"  → {status_str}  ({dur_ms:.1f} ms)"
            + (f"  {json.dumps({k:v for k,v in meta.items() if v is not None})}" if meta else "")
        )
    except:
        pass
    return resp


from graph import (
    RoadGraph,
    bfs_shortest_hops,
    dfs_all_paths,
    dijkstra_shortest,
)
from graph.io.loader import load_graph_from_shapefile

SHAPEFILE_PATH = "data/gis_osm_roads_free_1.shp"
UB_CENTER = (47.918, 106.917)

app = Flask(__name__)
app.logger.setLevel("INFO")

app.logger.info("Shapefile-с граф үүсгэж байна...")
# Хэрэв илүү бодит урт (метр) хэрэгтэй бол reproject_to_meters=True болгож болно
GRAPH: RoadGraph = load_graph_from_shapefile(SHAPEFILE_PATH, reproject_to_meters=False)
app.logger.info(f"Граф үүссэн. node={len(GRAPH.nodes)}")

@app.route("/")
def index():
    return render_template("index.html",
                           center_lat=UB_CENTER[0],
                           center_lon=UB_CENTER[1])

@app.route("/api/path")
def api_path():
    try:
        alg = request.args.get("alg", "dijkstra").lower()
        start_lon = float(request.args["start_lon"])
        start_lat = float(request.args["start_lat"])
        end_lon = float(request.args["end_lon"])
        end_lat = float(request.args["end_lat"])
    except (KeyError, ValueError):
        return jsonify({"error": "Параметр буруу байна."}), 400

    start_node = GRAPH.nearest_node(start_lon, start_lat)
    end_node = GRAPH.nearest_node(end_lon, end_lat)

    if start_node == -1 or end_node == -1:
        return jsonify({"error": "Ойролцоо зангилаа олдсонгүй."}), 404

    if alg == "bfs":
        node_path = bfs_shortest_hops(GRAPH, start_node, end_node)
        total_weight = None
    elif alg == "dfs":
        max_paths = int(request.args.get("max_paths", 1))
        max_depth = int(request.args.get("max_depth", 20000))
        max_expanded = int(request.args.get("max_expanded", 1000000))
        paths = dfs_all_paths(GRAPH, start_node, end_node,
                              max_paths=max_paths,
                              max_depth=max_depth,
                              max_expanded=max_expanded)
        node_path = paths[0] if paths else []
        total_weight = None
    else:  # dijkstra
        node_path, total_weight = dijkstra_shortest(GRAPH, start_node, end_node)

    if not node_path:
        app.logger.info(f"No path ({alg}): start={start_node}, end={end_node}")
        return jsonify({"error": "Зам олдсонгүй."}), 404

    coords = [{"lon": GRAPH.nodes[nid][0], "lat": GRAPH.nodes[nid][1]} for nid in node_path]
    return jsonify({
        "algorithm": alg,
        "nodes": node_path,
        "coords": coords,
        "total_weight": total_weight,
    })
if __name__ == "__main__":
    app.run(debug=True)
