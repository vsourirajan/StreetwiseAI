import sys
import argparse
import logging
from pathlib import Path

import orjson

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.retrieval.scenario import build_scenario_packet


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def summarize(packet: dict) -> str:
    parsed = packet.get("parsed", {})
    zoning = packet.get("zoning_references", [])
    traffic = packet.get("traffic", {}) or {}
    geo = packet.get("geospatial", {})

    lines = []
    lines.append(f"Query: {packet.get('query')}")
    lines.append(
        f"Parsed: action={parsed.get('action')}, street={parsed.get('street')}, from={parsed.get('from_cross')}, to={parsed.get('to_cross')}, city={parsed.get('city')}"
    )
    
    # Full zoning references
    lines.append(f"\nZoning References ({len(zoning)} matches):")
    for i, ref in enumerate(zoning):
        lines.append(f"\n--- Zoning Reference {i+1} ---")
        lines.append(f"ID: {ref.get('id')}")
        lines.append(f"Score: {ref.get('score', 'N/A')}")
        lines.append(f"Metadata: {ref.get('metadata', {})}")
        lines.append(f"Full Text:\n{ref.get('text', 'No text available')}")
    
    # Full geospatial data
    if geo:
        lines.append(f"\nGeospatial Data:")
        lines.append(f"Start Point: {geo.get('start_point', {})}")
        lines.append(f"End Point: {geo.get('end_point', {})}")
        lines.append(f"Route Buffer: {geo.get('route_buffer', 'None')}")
    
    # Full traffic data
    if traffic:
        lines.append(f"\nTraffic Data:")
        lines.append(f"Count: {traffic.get('count', 0)}")
        lines.append(f"Summary: {traffic.get('summary', {})}")
        if traffic.get('locations'):
            try:
                import json
                locations = json.loads(traffic['locations'])
                lines.append(f"Locations: {json.dumps(locations, indent=2)}")
            except:
                lines.append(f"Locations: {traffic['locations']}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Test the Gigacontext scenario packet builder")
    parser.add_argument(
        "--query",
        type=str,
        default="Pedestrianize Broadway from 14th to 34th in NYC",
        help="Scenario query to parse and retrieve context for",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="Optional path to write the full scenario packet as JSON",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        packet = build_scenario_packet(args.query)
    except Exception as e:
        print(f"Error building scenario packet: {e}")
        sys.exit(1)

    print(summarize(packet))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(orjson.dumps(packet))
        print(f"\nWrote full packet to: {out_path}")


if __name__ == "__main__":
    main()