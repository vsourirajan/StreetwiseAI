from pathlib import Path
import osmnx as ox  # type: ignore
import geopandas as gpd  # type: ignore

from citybrain.config import DATA_DIR, OSM_PLACE_NAME


def download_osm_drive_network(out_dir: Path | None = None, place_name: str | None = None) -> Path:
    out_dir = out_dir or DATA_DIR / "osm"
    out_dir.mkdir(parents=True, exist_ok=True)
    place = place_name or OSM_PLACE_NAME

    G = ox.graph_from_place(place, network_type="drive")

    graphml_path = out_dir / "drive.graphml"
    ox.save_graphml(G, graphml_path)

    nodes, edges = ox.graph_to_gdfs(G)
    nodes.to_file(out_dir / "nodes.parquet", driver="Parquet")
    edges.to_file(out_dir / "edges.parquet", driver="Parquet")

    # Also write GeoJSON for quick visualization
    edges.to_file(out_dir / "edges.geojson", driver="GeoJSON")
    return graphml_path