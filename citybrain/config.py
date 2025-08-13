import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "citybrain-zoning")

# Optional: Census API Key (for demographics data)
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY", "")

# NYC Open Data Socrata Dataset IDs
NYC_ZONING_SOCRATA_DATASET_ID = os.getenv("NYC_ZONING_SOCRATA_DATASET_ID", "")
NYC_TRAFFIC_SOCRATA_DATASET_ID = os.getenv("NYC_TRAFFIC_SOCRATA_DATASET_ID", "")

# OSM place to download network for (use small area during development)
OSM_PLACE_NAME = os.getenv("OSM_PLACE_NAME", "Manhattan, New York, USA")

# Optional: Hugging Face embedding model
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# NYC County FIPS codes for ACS/TIGER joins
NYC_COUNTY_FIPS = {
    "005": "Bronx",
    "047": "Kings",
    "061": "New York",
    "081": "Queens",
    "085": "Richmond",
}

STATE_FIPS_NY = "36"