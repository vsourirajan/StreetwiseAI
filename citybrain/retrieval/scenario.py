from __future__ import annotations

from typing import Dict, Any
import logging

from citybrain.retrieval.parser import parse_scenario_query
from citybrain.retrieval.zoning_search import search_zoning_chunks
from citybrain.retrieval.geospatial import select_traffic_counts

logger = logging.getLogger(__name__)


def build_scenario_packet(query: str) -> Dict[str, Any]:
    logger.info("Building scenario packet")

    # Step 1: Parse query
    parsed = parse_scenario_query(query)

    # Step 2: Geospatial context (if we have enough info)
    geo = None
    traffic = None

    if parsed.get("street") and parsed.get("from_cross") and parsed.get("to_cross"):
        logger.info("Basic geospatial info available, but OSM routing not implemented")
        # For now, just create basic coordinates without OSM routing
        # In a real implementation, you'd need to implement geocoding and routing
        geo = {
            "start_point": {"lat": 40.7378, "lon": -73.9914},  # Placeholder coordinates
            "end_point": {"lat": 40.7505, "lon": -73.9876},    # Placeholder coordinates
            "route_buffer": None,  # Would need OSM data to create this
        }
        # Note: traffic selection requires a buffer geometry, so this won't work without OSM
        logger.warning("Traffic selection requires OSM routing; skipping for now")
    else:
        logger.warning("Insufficient geospatial info in parsed query; skipping corridor/traffic")

    # Step 3: Zoning semantic search
    logger.info("Retrieving zoning references via semantic search")
    zoning = search_zoning_chunks(query, top_k=10)

    packet: Dict[str, Any] = {
        "query": query,
        "parsed": parsed,
        "zoning_references": zoning,
        "geospatial": geo,
        "traffic": traffic,
        "notes": [
            "This packet is a condensed context for LLM reasoning. Geometries are simplified for payload size.",
            "OSM routing functionality has been removed; geospatial data is limited.",
        ],
    }
    logger.info("Scenario packet built successfully")
    return packet