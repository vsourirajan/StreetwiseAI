import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

PATTERNS = [
    # Existing ones
    re.compile(r"(?P<action>pedestrianiz\w+)\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+from\s+(?P<start>[^,]+?)\s+to\s+(?P<end>[^,]+?)(?:\s+in\s+(?P<city>[^.]+))?$", re.IGNORECASE),
    re.compile(r"add\s+(?P<feature>bike lane|bus lane)\s+(?:along|on)\s+(?P<street>[A-Za-z0-9 .'-]+?)(?:\s+in\s+(?P<city>[^.]+))?$", re.IGNORECASE),

    # Street closures
    re.compile(r"close\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+(?:between|from)\s+(?P<start>[^,]+?)\s+(?:and|to)\s+(?P<end>[^,]+?)(?:\s+in\s+(?P<city>[^.]+))?$", re.IGNORECASE),
    re.compile(r"shut\s+down\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+(?:between|from)\s+(?P<start>[^,]+?)\s+(?:and|to)\s+(?P<end>[^,]+?)(?:\s+in\s+(?P<city>[^.]+))?$", re.IGNORECASE),

    # New lanes/features
    re.compile(r"install\s+(?P<feature>protected bike lane|bus rapid transit)\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+?)$", re.IGNORECASE),
    re.compile(r"convert\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+into\s+(?P<feature>shared street|bike boulevard)$", re.IGNORECASE),
    re.compile(r"add\s+(?P<num>\d+)\s+way\s+(?P<feature>bike path|bus lane)\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"create\s+(?P<feature>pedestrian plaza|parklet)\s+(?:at|on)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Speed limit changes
    re.compile(r"reduce\s+speed\s+limit\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+to\s+(?P<limit>\d+)\s*mph$", re.IGNORECASE),
    re.compile(r"increase\s+speed\s+limit\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+to\s+(?P<limit>\d+)\s*mph$", re.IGNORECASE),

    # Traffic direction changes
    re.compile(r"make\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+(?P<direction>one[- ]way|two[- ]way)$", re.IGNORECASE),
    re.compile(r"change\s+traffic\s+flow\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+to\s+(?P<direction>one[- ]way|two[- ]way)$", re.IGNORECASE),

    # Transit changes
    re.compile(r"add\s+(?P<mode>subway station|train stop)\s+(?:at|near)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"remove\s+(?P<mode>bus stop|subway station)\s+(?:at|near)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"extend\s+(?P<mode>bus route|subway line)\s+(?P<name>[A-Za-z0-9 .'-]+?)\s+to\s+(?P<destination>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Road expansions/reductions
    re.compile(r"widen\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+by\s+(?P<lanes>\d+)\s+lanes$", re.IGNORECASE),
    re.compile(r"narrow\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+by\s+(?P<lanes>\d+)\s+lanes$", re.IGNORECASE),
    re.compile(r"reduce\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+to\s+(?P<lanes>\d+)\s+lanes$", re.IGNORECASE),

    # Pedestrian/bike infrastructure
    re.compile(r"build\s+(?P<feature>bike path|walking trail)\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"connect\s+(?P<feature1>bike path|trail)\s+to\s+(?P<feature2>bike path|trail)\s+(?:via|through)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Parking changes
    re.compile(r"remove\s+(?P<num>\d+)\s+parking\s+spaces\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"add\s+(?P<num>\d+)\s+parking\s+spaces\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Crosswalks/signals
    re.compile(r"add\s+(?P<feature>crosswalk|pedestrian signal)\s+(?:at|on)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"remove\s+(?P<feature>crosswalk|pedestrian signal)\s+(?:at|on)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Environmental
    re.compile(r"plant\s+(?P<num>\d+)\s+trees\s+(?:along|on)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"add\s+(?P<feature>green roof|rain garden)\s+(?:to|at)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"install\s+(?P<feature>solar panels|charging stations)\s+(?:along|on|at)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Bridges/tunnels
    re.compile(r"close\s+(?P<feature>bridge|tunnel)\s+(?P<name>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"open\s+(?P<feature>bridge|tunnel)\s+(?P<name>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Tolling/congestion pricing
    re.compile(r"introduce\s+(?P<feature>toll|congestion charge)\s+(?:on|for)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"remove\s+(?P<feature>toll|congestion charge)\s+(?:on|for)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Lighting/safety
    re.compile(r"install\s+(?P<num>\d+)\s+streetlights\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"remove\s+(?P<num>\d+)\s+streetlights\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Lane conversions
    re.compile(r"convert\s+(?P<num>\d+)\s+lanes\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+to\s+(?P<feature>bike lanes|bus lanes|parking)$", re.IGNORECASE),
    re.compile(r"repurpose\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+lanes\s+for\s+(?P<feature>bike traffic|bus traffic)$", re.IGNORECASE),

    # Roundabouts/intersections
    re.compile(r"add\s+(?P<feature>roundabout|traffic circle)\s+(?:at|on)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"remove\s+(?P<feature>roundabout|traffic circle)\s+(?:at|on)\s+(?P<location>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Misc planning
    re.compile(r"build\s+(?P<feature>pedestrian bridge|overpass)\s+(?:at|over)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"demolish\s+(?P<feature>overpass|bridge)\s+(?P<name>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"restrict\s+truck\s+access\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),
    re.compile(r"allow\s+truck\s+access\s+(?:on|along)\s+(?P<street>[A-Za-z0-9 .'-]+)$", re.IGNORECASE),

    # Zoning/land use
    re.compile(r"current\s+(?P<subject>zoning|land use)\s+(?:rules|restrictions|regulations)\s+(?:for|in)\s+(?P<area>[^?]+)", re.IGNORECASE),
    re.compile(r"(?:list|show)\s+(?P<type>zones|districts)\s+(?:in|for)\s+(?P<area>[^?]+)", re.IGNORECASE),
    re.compile(r"what\s+(?:is|are)\s+(?P<area>[^?]+)\s+(?P<subject>zone classification|zone type)", re.IGNORECASE),

    re.compile(r"(?:list|show)\s+(?P<feature>bike lanes|bus lanes|pedestrian zones)\s+(?:in|within)\s+(?P<area>[^?]+)", re.IGNORECASE),
    re.compile(r"status\s+of\s+(?P<project>[^?]+)\s+(?:project|initiative)", re.IGNORECASE),
    re.compile(r"where\s+(?:are|is)\s+(?P<feature>bike lanes|bus lanes|pedestrian plazas)\s+(?:in|within)\s+(?P<area>[^?]+)", re.IGNORECASE),
    re.compile(r"(?:list|show)\s+(?P<type>projects|changes)\s+(?:in|for)\s+(?P<area>[^?]+)\s+since\s+(?P<year>\d{4})", re.IGNORECASE),
    re.compile(r"(?:what|which)\s+(?P<feature>roads|streets)\s+were\s+(?P<action>closed|pedestrianized|modified)\s+in\s+(?P<year>\d{4})", re.IGNORECASE),
    re.compile(r"(?:find|locate)\s+(?P<feature>[^?]+)\s+near\s+(?P<location>[^?]+)", re.IGNORECASE),
    re.compile(r"(?:what|which)\s+(?P<feature>roads|zones)\s+are\s+adjacent\s+to\s+(?P<landmark>[^?]+)", re.IGNORECASE),
    re.compile(r"(?:what|which)\s+(?P<subject>laws|policies|guidelines)\s+(?:apply to|govern)\s+(?P<topic>[^?]+)", re.IGNORECASE),
    re.compile(r"(?:give me|list)\s+the\s+(?P<subject>rules|restrictions)\s+(?:about|for)\s+(?P<topic>[^?]+)", re.IGNORECASE),
]


def normalize(text: str) -> str:
    return " ".join(text.strip().split())


def parse_scenario_query(query: str) -> Dict:
    logger.info("Parsing scenario query")
    q = normalize(query)
    result: Dict = {
        "raw": query,
        "action": None,
        "street": None,
        "from_cross": None,
        "to_cross": None,
        "city": None,
        "feature": None,
    }
    for idx, pat in enumerate(PATTERNS, start=1):
        m = pat.search(q)
        if m:
            logger.debug(f"Pattern {idx} matched: {pat.pattern}")
            gd = {k: (normalize(v) if v else v) for k, v in m.groupdict().items()}
            if "action" in gd and gd["action"]:
                result["action"] = gd["action"].lower()
            if gd.get("feature"):
                result["action"] = gd["feature"].lower()
                result["feature"] = gd["feature"].lower()
            result["street"] = gd.get("street")
            result["from_cross"] = gd.get("start")
            result["to_cross"] = gd.get("end")
            result["city"] = gd.get("city") or "New York, NY"
            break
    if not result["city"]:
        result["city"] = "New York, NY"
    logger.info(
        "Parsed: action=%s street=%s from=%s to=%s city=%s",
        result.get("action"), result.get("street"), result.get("from_cross"), result.get("to_cross"), result.get("city"),
    )
    return result