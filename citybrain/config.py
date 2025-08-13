import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "citybrain-zoning")
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY", "")

NYC_ZONING_SOCRATA_DATASET_ID = os.getenv("NYC_ZONING_SOCRATA_DATASET_ID", "")
NYC_TRAFFIC_SOCRATA_DATASET_ID = os.getenv("NYC_TRAFFIC_SOCRATA_DATASET_ID", "")

OSM_PLACE_NAME = os.getenv("OSM_PLACE_NAME", "Manhattan, New York, USA")

# NYC County FIPS codes for ACS/TIGER joins
NYC_COUNTY_FIPS = {
    "005": "Bronx",
    "047": "Kings",
    "061": "New York",
    "081": "Queens",
    "085": "Richmond",
}

STATE_FIPS_NY = "36"