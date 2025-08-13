import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

PATTERNS = [
    re.compile(r"(?P<action>pedestrianiz\w+)\s+(?P<street>[A-Za-z0-9 .'-]+?)\s+from\s+(?P<start>[^,]+?)\s+to\s+(?P<end>[^,]+?)(?:\s+in\s+(?P<city>[^.]+))?$", re.IGNORECASE),
    re.compile(r"add\s+(?P<feature>bike lane|bus lane)\s+(?:along|on)\s+(?P<street>[A-Za-z0-9 .'-]+?)(?:\s+in\s+(?P<city>[^.]+))?$", re.IGNORECASE),
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