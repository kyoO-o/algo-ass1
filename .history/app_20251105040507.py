# app.py
from flask import Flask, request, jsonify, render_template
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
