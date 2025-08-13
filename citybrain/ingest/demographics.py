from pathlib import Path
from typing import Dict, List
import zipfile
import io

import geopandas as gpd  # type: ignore
import pandas as pd  # type: ignore
import requests

from citybrain.config import DATA_DIR, NYC_COUNTY_FIPS, STATE_FIPS_NY, CENSUS_API_KEY

ACS_ENDPOINT = "https://api.census.gov/data/2022/acs/acs5"
ACS_VARS = {
    "B01003_001E": "total_pop",
    "B19013_001E": "median_hh_income", 
    "B08201_001E": "commuters_total",
}


def _fetch_tiger_tracts(out_dir: Path) -> gpd.GeoDataFrame:
    # New York state code 36
    url = "https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_36_tract.zip"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(out_dir)
    shp = next(p for p in out_dir.glob("tl_2022_36_tract.shp"))
    gdf = gpd.read_file(shp)
    return gdf


def _fetch_acs_for_counties(county_fips: List[str]) -> pd.DataFrame:
    var_list = ",".join(["NAME", "state", "county", "tract", *ACS_VARS.keys()])
    params = {
        "get": var_list,
        "for": "tract:*",
        "in": f"state:{STATE_FIPS_NY} county:{' '.join(county_fips)}",
    }
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY
    resp = requests.get(ACS_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    cols = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=cols)
    # Coerce numeric vars
    for var, alias in ACS_VARS.items():
        df[alias] = pd.to_numeric(df[var], errors="coerce")
    df["geoid"] = (
        df["state"].astype(str) + df["county"].astype(str).str.zfill(3) + df["tract"].astype(str).str.zfill(6)
    )
    return df[
        [
            "geoid",
            "NAME",
            *[alias for alias in ACS_VARS.values()],
        ]
    ]


def download_demographics(out_dir: Path | None = None) -> Path:
    out_dir = out_dir or DATA_DIR / "demographics"
    out_dir.mkdir(parents=True, exist_ok=True)

    tiger_dir = out_dir / "tiger"
    tiger_dir.mkdir(parents=True, exist_ok=True)
    tracts = _fetch_tiger_tracts(tiger_dir)

    nyc_tracts = tracts[tracts["COUNTYFP"].isin(list(NYC_COUNTY_FIPS.keys()))].copy()
    nyc_tracts["geoid"] = nyc_tracts["GEOID"].astype(str)

    acs = _fetch_acs_for_counties(list(NYC_COUNTY_FIPS.keys()))
    gdf = nyc_tracts.merge(acs, on="geoid", how="left")

    gdf.to_file(out_dir / "nyc_tracts_acs.parquet", driver="Parquet")
    gdf.to_file(out_dir / "nyc_tracts_acs.geojson", driver="GeoJSON")
    return out_dir