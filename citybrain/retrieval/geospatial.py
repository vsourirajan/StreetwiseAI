from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import logging

import geopandas as gpd  # type: ignore
import pandas as pd  # type: ignore
from shapely.geometry import Point, LineString  # type: ignore

from citybrain.config import DATA_DIR

logger = logging.getLogger(__name__)

TRAFFIC_DIR = DATA_DIR / "traffic"


@dataclass
class Corridor:
    start_point: Tuple[float, float]  # (lat, lon)
    end_point: Tuple[float, float]
    route_edges: gpd.GeoDataFrame
    route_line: LineString
    buffer_geom: object  # shapely geometry


def select_traffic_counts(buffer_geom) -> Dict:
    logger.info("Selecting traffic counts within buffer")
    geojson_path = TRAFFIC_DIR / "traffic_counts.geojson"
    if not geojson_path.exists():
        logger.warning("Traffic counts file not found: %s", geojson_path)
        return {"count": 0, "locations": [], "summary": {}}
    gdf = gpd.read_file(geojson_path)
    # Ensure CRS
    if gdf.crs is None:
        gdf.set_crs(4326, inplace=True)
    within = gdf[gdf.geometry.within(buffer_geom)]
    summary = {"num_points": int(len(within))}
    for col in ["volume", "aadt", "hourly_volume"]:
        if col in within.columns:
            s = within[col].dropna()
            if len(s) > 0:
                summary[col] = {
                    "min": float(s.min()),
                    "max": float(s.max()),
                    "mean": float(s.mean()),
                }
    logger.info("Selected %d traffic points", len(within))
    return {
        "count": int(len(within)),
        "locations": within.head(200).to_json(),  # cap for payload
        "summary": summary,
    }