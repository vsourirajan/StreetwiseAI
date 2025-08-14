from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

from citybrain.retrieval.parser import parse_scenario_query
from citybrain.retrieval.zoning_search import search_zoning_chunks
from citybrain.retrieval.geospatial import (
    get_zoning_districts_in_area, 
    get_traffic_counts_in_area,
    create_manhattan_broadway_bounds
)

logger = logging.getLogger(__name__)


def build_scenario_packet(query: str) -> Dict[str, Any]:
    """Build a comprehensive scenario packet for LLM analysis.
    
    This function implements the gigacontext retrieval layer by:
    1. Parsing the user query to understand what data is needed
    2. Retrieving relevant zoning text chunks via semantic search
    3. Getting relevant zoning districts and traffic data for the area
    4. Assembling everything into a condensed packet for the LLM
    """
    logger.info(f"Building scenario packet for query: {query}")
    
    # Step 1: Parse the query to understand what we need
    parsed = parse_scenario_query(query)
    logger.info(f"Parsed query components: {parsed}")
    
    # Step 2: Get relevant zoning text chunks via semantic search
    logger.info("Searching for relevant zoning text chunks...")
    zoning_chunks = search_zoning_chunks(query, top_k=5)
    logger.info(f"Found {len(zoning_chunks)} relevant zoning chunks")
    
    # Step 3: Get zoning districts and traffic data for the area
    logger.info("Getting geospatial data for the area...")
    
    # For the Broadway pedestrianization example, use Manhattan bounds
    area_bounds = create_manhattan_broadway_bounds()
    logger.info(f"Using area bounds: {area_bounds}")
    
    # Get zoning districts in the area
    zoning_districts = get_zoning_districts_in_area(area_bounds)
    logger.info(f"Found {len(zoning_districts)} zoning districts in area")
    
    # Get traffic counts in the area
    traffic_counts = get_traffic_counts_in_area(area_bounds)
    logger.info(f"Found {len(traffic_counts)} traffic count locations in area")
    
    # Step 4: Assemble the scenario packet
    scenario_packet = {
        "query": query,
        "parsed_components": parsed,
        "area_of_interest": {
            "bounds": area_bounds,
            "description": "Broadway corridor from 14th to 34th Street, Manhattan"
        },
        "zoning_information": {
            "relevant_text_chunks": zoning_chunks,
            "affected_zoning_districts": zoning_districts,
            "total_chunks_found": len(zoning_chunks),
            "total_districts_in_area": len(zoning_districts)
        },
        "traffic_information": {
            "traffic_count_locations": traffic_counts,
            "total_locations_in_area": len(traffic_counts)
        },
        "data_summary": {
            "total_data_points": len(zoning_chunks) + len(zoning_districts) + len(traffic_counts),
            "data_types": ["zoning_text", "zoning_districts", "traffic_counts"],
            "geographic_scope": "Manhattan Broadway corridor (14th-34th Streets)"
        }
    }
    
    logger.info(f"✓ Built scenario packet with {scenario_packet['data_summary']['total_data_points']} data points")
    
    return scenario_packet