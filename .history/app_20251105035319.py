# app.py
"""
Flask backend:
- /       -> Leaflet map UI (templates/index.html)
- /api/path -> start/end цэгүүдээс зам тооцож JSON болгож буцаана.
"""

from flask import Flask, request, jsonify, render_template
from road_graph import (
    RoadGraph,
    bfs_shortest_hops,
    dfs_all_paths,
    dijkstra_shortest,
)

# ----------------- Тохиргоо -----------------
SHAPEFILE_PATH = "data/gis_osm_roads_free_1.shp"  # замын shapefile-ийн замаа энд заа
UB_CENTER = (47.918, 106.917)  # УБ төв (lat, lon) – front-end-д ашиглана


app = Flask(__name__)

print("Shapefile-с граф үүсгэж байна...")
GRAPH = RoadGraph.from_shapefile(SHAPEFILE_PATH)
print(f"Граф үүссэн. Нийт node: {len(GRAPH.nodes)}")


@app.route("/")
def index():
    # UB_CENTER-ийг template рүү дамжуулна
    return render_template(
        "index.html",
        center_lat=UB_CENTER[0],
        center_lon=UB_CENTER[1],
    )


@app.route("/api/path")
def api_path():
    """
    GET /api/path?alg=dijkstra&start_lon=..&start_lat=..&end_lon=..&end_lat=..
    """
    try:
        alg = request.args.get("alg", "dijkstra").lower()
        start_lon = float(request.args["start_lon"])
        start_lat = float(request.args["start_lat"])
        end_lon = float(request.args["end_lon"])
        end_lat = float(request.args["end_lat"])
    except (KeyError, ValueError):
        return jsonify({"error": "Параметр буруу байна."}), 400

    # Map дээрх цэгийг графын хамгийн ойр node-д хөрвүүлнэ
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
        paths = dfs_all_paths(GRAPH, start_node, end_node,
                            max_paths=max_paths, max_depth=max_depth)

        node_path = paths[0] if paths else []
        total_weight = None
    else:  # dijkstra
        node_path, total_weight = dijkstra_shortest(GRAPH, start_node, end_node)

    if not node_path:
        return jsonify({"error": "Зам олдсонгүй."}), 404

    coords = []
    for nid in node_path:
        lon, lat = GRAPH.nodes[nid]
        coords.append({"lon": lon, "lat": lat})

    return jsonify(
        {
            "algorithm": alg,
            "nodes": node_path,
            "coords": coords,
            "total_weight": total_weight,
        }
    )


if __name__ == "__main__":
    # Хөгжүүлэлтийн горим
    app.run(debug=True)
