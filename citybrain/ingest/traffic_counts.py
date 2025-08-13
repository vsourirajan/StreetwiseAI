import logging
from pathlib import Path
import requests
import geopandas as gpd  # type: ignore
import pandas as pd

from citybrain.config import DATA_DIR, NYC_TRAFFIC_SOCRATA_DATASET_ID


def _check_parquet_support():
    """Check if Parquet format is supported and log the status."""
    logger = logging.getLogger(__name__)
    
    try:
        # Test pandas Parquet support
        test_df = pd.DataFrame({'test': [1, 2, 3]})
        test_df.to_parquet('/tmp/test.parquet')
        logger.info("✓ Pandas Parquet support available")
        return True
    except Exception as e:
        logger.warning(f"✗ Pandas Parquet support not available: {e}")
        return False
    
    try:
        # Test geopandas Parquet support
        test_gdf = gpd.GeoDataFrame({'test': [1, 2, 3]})
        test_gdf.to_file('/tmp/test.parquet', driver="Parquet")
        logger.info("✓ GeoPandas Parquet support available")
        return True
    except Exception as e:
        logger.warning(f"✗ GeoPandas Parquet support not available: {e}")
        return False


def download_traffic_counts(out_dir: Path | None = None) -> Path:
    logger = logging.getLogger(__name__)
    out_dir = out_dir or DATA_DIR / "traffic"
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting NYC traffic counts download to {out_dir}")

    if not NYC_TRAFFIC_SOCRATA_DATASET_ID:
        note = out_dir / "README.txt"
        note.write_text(
            "NYC_TRAFFIC_SOCRATA_DATASET_ID not set. Skipping traffic counts download.\n"
            "Find dataset ID on NYC Open Data for 'Traffic Volume Counts' and set in .env.\n"
        )
        logger.warning("NYC_TRAFFIC_SOCRATA_DATASET_ID not set - skipping traffic counts download")
        logger.info(f"Note written to: {note}")
        return out_dir

    url = f"https://data.cityofnewyork.us/resource/{NYC_TRAFFIC_SOCRATA_DATASET_ID}.geojson?$limit=500000"
    logger.info(f"Downloading from NYC Open Data: {url}")
    
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        logger.info(f"Download successful: {len(resp.content):,} bytes")
    except Exception as e:
        logger.error(f"Failed to download traffic counts: {e}")
        raise

    geojson_path = out_dir / "traffic_counts.geojson"
    geojson_path.write_bytes(resp.content)
    logger.info(f"GeoJSON saved to: {geojson_path}")

    try:
        logger.info("Converting to Parquet format...")
        gdf = gpd.read_file(geojson_path)
        logger.info(f"Loaded {len(gdf)} traffic count locations")
        
        # Try to coerce numeric counts if present
        for col in ["volume", "aadt", "hourly_volume"]:
            if col in gdf.columns:
                gdf[col] = gdf[col].apply(lambda x: float(x) if x not in [None, "", "nan"] else None)
                logger.debug(f"Normalized numeric column: {col}")
        
        # Check Parquet support before attempting conversion
        parquet_supported = _check_parquet_support()
        
        if parquet_supported:
            try:
                parquet_path = out_dir / "traffic_counts.parquet"
                gdf.to_file(parquet_path, driver="Parquet")
                logger.info(f"✓ Parquet saved to: {parquet_path}")
            except Exception as e:
                logger.warning(f"GeoPandas Parquet conversion failed: {e}")
                # Try pandas fallback
                try:
                    parquet_path = out_dir / "traffic_counts.parquet"
                    # Convert to pandas DataFrame and save
                    df = pd.DataFrame(gdf.drop(columns='geometry'))
                    df.to_parquet(parquet_path)
                    logger.info(f"✓ Parquet saved using pandas fallback: {parquet_path}")
                except Exception as pandas_e:
                    logger.warning(f"Pandas Parquet fallback also failed: {pandas_e}")
                    parquet_supported = False
        else:
            logger.warning("Parquet format not supported, skipping conversion")
        
        # Always try to save as CSV as a reliable fallback
        try:
            csv_path = out_dir / "traffic_counts.csv"
            # Convert to pandas DataFrame and save as CSV
            df = pd.DataFrame(gdf.drop(columns='geometry'))
            df.to_csv(csv_path, index=False)
            logger.info(f"✓ CSV saved to: {csv_path}")
        except Exception as csv_e:
            logger.warning(f"CSV conversion failed: {csv_e}")
        
        # Log some basic stats
        logger.info(f"Traffic counts summary:")
        logger.info(f"  Total locations: {len(gdf)}")
        logger.info(f"  Geometry type: {gdf.geometry.geom_type.unique()}")
        
        # Log available columns
        logger.info(f"  Available columns: {list(gdf.columns)}")
        
        # Log some sample data if available
        if "volume" in gdf.columns:
            non_null_volumes = gdf[gdf["volume"].notna()]
            if len(non_null_volumes) > 0:
                logger.info(f"  Volume range: {non_null_volumes['volume'].min():.0f} - {non_null_volumes['volume'].max():.0f}")
        
        # Show coordinate system info
        if gdf.crs:
            logger.info(f"  Coordinate system: {gdf.crs}")
        
        # Show sample records
        logger.info("Sample records:")
        for i, row in gdf.head(3).iterrows():
            sample_data = {k: v for k, v in row.items() if k != 'geometry'}
            logger.info(f"  Record {i}: {sample_data}")
        
    except Exception as e:
        logger.error(f"Error processing traffic counts: {e}")
        logger.exception("Full error details:")
        # Even if processing fails, we still have the GeoJSON file
        logger.info("GeoJSON file is still available for use")
    
    return geojson_path