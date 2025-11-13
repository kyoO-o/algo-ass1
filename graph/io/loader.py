from typing import Dict, Tuple, List
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from ..road_graph import RoadGraph

def load_graph_from_shapefile(shp_path: str,
                              reproject_to_meters: bool = False) -> RoadGraph:
    gdf = gpd.read_file(shp_path)
    if reproject_to_meters:
        gdf = gdf.to_crs(epsg=3857)

    graph = RoadGraph()
    coord_to_id: Dict[Tuple[float, float], int] = {}

    def get_node_id(lon: float, lat: float) -> int:
        key = (round(lon, 6), round(lat, 6))
        if key not in coord_to_id:
            nid = len(coord_to_id)
            coord_to_id[key] = nid
            graph.add_node(nid, lon, lat)
        return coord_to_id[key]

    for _, row in gdf.iterrows():
        geom = row.geometry
        access = row.get("access", None)
        fclass = row.get("fclass", None)
        oneway = row.get("oneway", "no")

        if access in ("no", "private"):
            continue
        if fclass in ("footway", "path", "track", "pedestrian", "steps", "cycleway"):
            continue
        if geom is None:
            continue

        if isinstance(geom, LineString):
            lines = [geom]
        elif isinstance(geom, MultiLineString):
            lines = list(geom)
        else:
            continue

        for line in lines:
            coords = list(line.coords)
            if len(coords) < 2:
                continue
            if reproject_to_meters:
                seg_len = line.length / (len(coords) - 1)
            else:
                seg_len = line.length / (len(coords) - 1)

            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                u = get_node_id(x1, y1)
                v = get_node_id(x2, y2)
                graph.add_edge(u, v, seg_len, oneway=str(oneway))

    return graph
