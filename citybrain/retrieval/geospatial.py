from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path
import logging
import json

import geopandas as gpd  # type: ignore
import pandas as pd  # type: ignore
from shapely.geometry import Point, LineString, Polygon  # type: ignore
from shapely.ops import unary_union

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


def load_zoning_districts() -> Optional[gpd.GeoDataFrame]:
    """Load zoning districts from GeoJSON file."""
    try:
        zoning_path = DATA_DIR / "zoning" / "zoning_districts.geojson"
        if not zoning_path.exists():
            logger.warning(f"Zoning districts file not found: {zoning_path}")
            return None
        
        logger.info(f"Loading zoning districts from {zoning_path}")
        gdf = gpd.read_file(zoning_path)
        logger.info(f"Loaded {len(gdf)} zoning districts")
        logger.info(f"Columns: {list(gdf.columns)}")
        logger.info(f"Sample districts: {gdf.head(3).to_dict('records')}")
        
        return gdf
    except Exception as e:
        logger.error(f"Error loading zoning districts: {e}")
        return None


def load_traffic_counts() -> Optional[gpd.GeoDataFrame]:
    """Load traffic counts from GeoJSON file."""
    try:
        traffic_path = DATA_DIR / "traffic" / "traffic_counts.geojson"
        if not traffic_path.exists():
            logger.warning(f"Traffic counts file not found: {traffic_path}")
            return None
        
        logger.info(f"Loading traffic counts from {traffic_path}")
        gdf = gpd.read_file(traffic_path)
        logger.info(f"Loaded {len(gdf)} traffic count locations")
        logger.info(f"Columns: {list(gdf.columns)}")
        logger.info(f"Sample traffic data: {gdf.head(3).to_dict('records')}")
        
        return gdf
    except Exception as e:
        logger.error(f"Error loading traffic counts: {e}")
        return None


def get_zoning_districts_in_area(area_bounds: Dict[str, float]) -> List[Dict[str, Any]]:
    """Get zoning districts that intersect with the given area bounds.
    
    Args:
        area_bounds: Dict with 'min_lat', 'max_lat', 'min_lon', 'max_lon'
    
    Returns:
        List of zoning district data (without geometry for JSON serialization)
    """
    gdf = load_zoning_districts()
    if gdf is None:
        return []
    
    try:
        # Create a bounding box polygon
        bbox = Polygon([
            (area_bounds['min_lon'], area_bounds['min_lat']),
            (area_bounds['max_lon'], area_bounds['min_lat']),
            (area_bounds['max_lon'], area_bounds['max_lat']),
            (area_bounds['min_lon'], area_bounds['max_lat']),
            (area_bounds['min_lon'], area_bounds['min_lat'])
        ])
        
        # Find intersecting districts
        intersecting = gdf[gdf.intersects(bbox)]
        logger.info(f"Found {len(intersecting)} zoning districts in area")
        
        # Convert to serializable format (drop geometry, keep other columns)
        districts_data = []
        for idx, row in intersecting.iterrows():
            district_info = row.drop('geometry').to_dict()
            districts_data.append(district_info)
        
        return districts_data
        
    except Exception as e:
        logger.error(f"Error finding zoning districts in area: {e}")
        return []


def get_traffic_counts_in_area(area_bounds: Dict[str, float]) -> List[Dict[str, Any]]:
    """Get traffic count locations that fall within the given area bounds.
    
    Args:
        area_bounds: Dict with 'min_lat', 'max_lat', 'min_lon', 'max_lon'
    
    Returns:
        List of traffic count data (without geometry for JSON serialization)
    """
    #gdf = load_traffic_counts()
    gdf = None
    if gdf is None:
        return []
    
    try:
        # Create a bounding box polygon
        bbox = Polygon([
            (area_bounds['min_lat'], area_bounds['min_lon']),
            (area_bounds['max_lat'], area_bounds['min_lon']),
            (area_bounds['max_lat'], area_bounds['max_lon']),
            (area_bounds['min_lat'], area_bounds['max_lon']),
            (area_bounds['min_lat'], area_bounds['min_lon'])
        ])
        
        # Find points within the bounding box
        within = gdf[gdf.within(bbox)]
        logger.info(f"Found {len(within)} traffic count locations in area")
        
        # Convert to serializable format (drop geometry, keep other columns)
        traffic_data = []
        for idx, row in within.iterrows():
            traffic_info = row.drop('geometry').to_dict()
            traffic_data.append(traffic_info)
        
        return traffic_data
        
    except Exception as e:
        logger.error(f"Error finding traffic counts in area: {e}")
        return []


def create_manhattan_broadway_bounds() -> Dict[str, float]:
    """Create bounding box for Broadway from 14th to 34th Street in Manhattan."""
    # Broadway runs roughly north-south in Manhattan
    # 14th Street is around 40.7378°N, 34th Street is around 40.7505°N
    # Broadway is roughly between 5th Ave (-73.9914°W) and 6th Ave (-73.9876°W)
    # Add some buffer for nearby areas
    return {
        'min_lat': 40.7300,  # Slightly south of 14th
        'max_lat': 40.7550,  # Slightly north of 34th
        'min_lon': -73.9950,  # Slightly west of Broadway
        'max_lon': -73.9850,  # Slightly east of Broadway
    }