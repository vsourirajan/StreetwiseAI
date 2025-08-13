import json
import logging
import zipfile
import tempfile
from pathlib import Path
import requests
import geopandas as gpd  # type: ignore

from citybrain.config import DATA_DIR, NYC_ZONING_SOCRATA_DATASET_ID


def _check_gdal_drivers():
    """Check available GDAL drivers for debugging."""
    try:
        import fiona
        drivers = fiona.supported_drivers
        logger = logging.getLogger(__name__)
        logger.info(f"Available GDAL drivers: {list(drivers.keys())}")
        
        # Check specifically for FileGDB support
        if 'FileGDB' in drivers:
            logger.info("✓ FileGDB driver available")
        else:
            logger.warning("✗ FileGDB driver not available")
            
        if 'OpenFileGDB' in drivers:
            logger.info("✓ OpenFileGDB driver available")
        else:
            logger.warning("✗ OpenFileGDB driver not available")
            
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not check GDAL drivers: {e}")


def download_zoning_shapes(out_dir: Path | None = None) -> Path:
    logger = logging.getLogger(__name__)
    out_dir = out_dir or DATA_DIR / "zoning"
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting NYC zoning shapes download to {out_dir}")
    
    # Debug: Show what dataset ID we're using
    logger.info(f"Using dataset ID: {NYC_ZONING_SOCRATA_DATASET_ID}")
    
    # Check GDAL drivers for debugging
    _check_gdal_drivers()
    
    if not NYC_ZONING_SOCRATA_DATASET_ID:
        # Write a note and skip
        note = out_dir / "README.txt"
        note.write_text(
            "NYC_ZONING_SOCRATA_DATASET_ID not set. Skipping zoning shapes download.\n"
            "Find dataset ID on NYC Open Data for 'Zoning Districts' and set in .env.\n"
            "Expected: mm69-vrje for the Zoning GIS Data Geodatabase\n"
        )
        logger.warning("NYC_ZONING_SOCRATA_DATASET_ID not set - skipping zoning shapes download")
        logger.info(f"Note written to: {note}")
        return out_dir

    # For geodatabase files, we need to download the zip file first
    # The dataset ID mm69-vrje contains a File Geodatabase (.gdb)
    zip_url = f"https://data.cityofnewyork.us/download/{NYC_ZONING_SOCRATA_DATASET_ID}/application/zip"
    logger.info(f"Downloading ESRI File Geodatabase from NYC Open Data: {zip_url}")
    
    try:
        resp = requests.get(zip_url, timeout=120)  # Longer timeout for larger files
        resp.raise_for_status()
        logger.info(f"Download successful: {len(resp.content):,} bytes")
    except Exception as e:
        logger.error(f"Failed to download zoning geodatabase: {e}")
        logger.error(f"URL attempted: {zip_url}")
        logger.error(f"Dataset ID from config: {NYC_ZONING_SOCRATA_DATASET_ID}")
        raise

    # Save the zip file
    zip_path = out_dir / "zoning_geodatabase.zip"
    zip_path.write_bytes(resp.content)
    logger.info(f"ZIP file saved to: {zip_path}")

    # Extract the geodatabase
    logger.info("Extracting geodatabase files...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(out_dir)
        
        # Find the .gdb directory
        gdb_dirs = list(out_dir.glob("*.gdb"))
        if not gdb_dirs:
            logger.warning("No .gdb directory found in extracted files")
            logger.info("Available files:")
            for item in out_dir.iterdir():
                logger.info(f"  {item.name}")
            return out_dir
        
        gdb_dir = gdb_dirs[0]
        logger.info(f"Found geodatabase: {gdb_dir}")
        
        # Try multiple approaches to read the geodatabase
        gdf = None
        main_feature_class = None
        
        # Method 1: Try using fiona to discover layers (most robust)
        try:
            import fiona  # type: ignore
            logger.info("Method 1: Using fiona to discover feature classes...")
            
            # List all layers in the geodatabase
            layers = fiona.listlayers(str(gdb_dir))
            logger.info(f"Available layers: {layers}")
            
            # Filter for feature classes (exclude system tables)
            feature_classes = []
            for layer in layers:
                # Skip system tables that typically start with these prefixes
                if not any(layer.lower().startswith(prefix) for prefix in ['gdb_', 'cat_', 'sys_', 'tbl_']):
                    feature_classes.append(layer)
            
            logger.info(f"Feature classes found: {feature_classes}")
            
            if feature_classes:
                # Try to identify the main zoning districts feature class
                preferred_names = ['ZoningDistricts', 'Zoning', 'Districts', 'Zoning_Districts', 'ZoningDist']
                
                for name in preferred_names:
                    if name in feature_classes:
                        main_feature_class = name
                        break
                
                # If no preferred name found, use the first feature class
                if not main_feature_class:
                    main_feature_class = feature_classes[0]
                
                logger.info(f"Selected feature class: {main_feature_class}")
                
                # Try to read with geopandas
                try:
                    gdf = gpd.read_file(str(gdb_dir), layer=main_feature_class)
                    logger.info(f"✓ Successfully loaded {len(gdf)} features using fiona + geopandas")
                except Exception as e:
                    logger.warning(f"geopandas.read_file failed: {e}")
                    # Try direct fiona reading as fallback
                    try:
                        with fiona.open(str(gdb_dir), layer=main_feature_class) as src:
                            features = list(src)
                            logger.info(f"✓ Successfully read {len(features)} features using fiona directly")
                            # Convert to GeoDataFrame
                            gdf = gpd.GeoDataFrame.from_features(features)
                    except Exception as fiona_e:
                        logger.warning(f"Direct fiona reading also failed: {fiona_e}")
            
        except ImportError:
            logger.warning("fiona not available, trying alternative methods...")
        except Exception as e:
            logger.warning(f"fiona method failed: {e}")
        
        # Method 2: Try direct geopandas reading (fallback)
        if gdf is None:
            logger.info("Method 2: Trying direct geopandas reading...")
            try:
                gdf = gpd.read_file(str(gdb_dir))
                logger.info(f"✓ Successfully loaded {len(gdf)} features using direct geopandas")
                main_feature_class = "default"
            except Exception as e:
                logger.warning(f"Direct geopandas reading failed: {e}")
        
        # Method 3: Try reading specific file types within the geodatabase
        if gdf is None:
            logger.info("Method 3: Trying to find and read specific files...")
            try:
                # Look for .shp files that might have been extracted
                shp_files = list(out_dir.glob("**/*.shp"))
                if shp_files:
                    logger.info(f"Found shapefiles: {[f.name for f in shp_files]}")
                    gdf = gpd.read_file(str(shp_files[0]))
                    logger.info(f"✓ Successfully loaded {len(gdf)} features from shapefile")
                    main_feature_class = shp_files[0].stem
                else:
                    logger.warning("No shapefiles found")
            except Exception as e:
                logger.warning(f"Shapefile reading failed: {e}")
        
        # Method 4: Try alternative geodatabase drivers
        if gdf is None:
            logger.info("Method 4: Trying alternative geodatabase drivers...")
            try:
                # Try with explicit driver specification
                gdf = gpd.read_file(str(gdb_dir), driver="OpenFileGDB")
                logger.info(f"✓ Successfully loaded {len(gdf)} features using OpenFileGDB driver")
                main_feature_class = "OpenFileGDB_default"
            except Exception as e:
                logger.warning(f"OpenFileGDB driver failed: {e}")
                
                try:
                    gdf = gpd.read_file(str(gdb_dir), driver="FileGDB")
                    logger.info(f"✓ Successfully loaded {len(gdf)} features using FileGDB driver")
                    main_feature_class = "FileGDB_default"
                except Exception as e2:
                    logger.warning(f"FileGDB driver also failed: {e2}")
        
        # Process the data if we successfully loaded it
        if gdf is not None and len(gdf) > 0:
            logger.info(f"Processing {len(gdf)} zoning districts from {main_feature_class}")
            
            # Log the schema
            logger.info(f"Schema: {list(gdf.columns)}")
            
            # Normalize columns if present (check both lowercase and uppercase variants)
            for col in ["zonedist", "zonedist1", "zonedist2", "zone_type", "ZONEDIST", "ZONEDIST1", "ZONEDIST2"]:
                if col in gdf.columns:
                    gdf[col] = gdf[col].astype(str)
                    logger.debug(f"Normalized column: {col}")
            
            # Check Parquet support before attempting conversion
            parquet_supported = _check_parquet_support()
            
            # Save as multiple formats for flexibility
            if parquet_supported:
                try:
                    parquet_path = out_dir / "zoning_districts.parquet"
                    gdf.to_file(parquet_path, driver="Parquet")
                    logger.info(f"✓ Parquet saved to: {parquet_path}")
                except Exception as e:
                    logger.warning(f"GeoPandas Parquet conversion failed: {e}")
                    # Try pandas fallback
                    try:
                        parquet_path = out_dir / "zoning_districts.parquet"
                        # Convert to pandas DataFrame and save
                        df = pd.DataFrame(gdf.drop(columns='geometry'))
                        df.to_parquet(parquet_path)
                        logger.info(f"✓ Parquet saved using pandas fallback: {parquet_path}")
                    except Exception as pandas_e:
                        logger.warning(f"Pandas Parquet fallback also failed: {pandas_e}")
                        parquet_supported = False
            else:
                logger.warning("Parquet format not supported, skipping conversion")
            
            try:
                geojson_path = out_dir / "zoning_districts.geojson"
                gdf.to_file(geojson_path, driver="GeoJSON")
                logger.info(f"✓ GeoJSON saved to: {geojson_path}")
            except Exception as e:
                logger.warning(f"Could not save as GeoJSON: {e}")
            
            # Always try to save as CSV as a reliable fallback
            try:
                csv_path = out_dir / "zoning_districts.csv"
                # Convert to pandas DataFrame and save as CSV
                df = pd.DataFrame(gdf.drop(columns='geometry'))
                df.to_csv(csv_path, index=False)
                logger.info(f"✓ CSV saved to: {csv_path}")
            except Exception as csv_e:
                logger.warning(f"CSV conversion failed: {csv_e}")
            
            # Log some basic stats
            logger.info(f"Zoning districts summary:")
            logger.info(f"  Total districts: {len(gdf)}")
            logger.info(f"  Geometry type: {gdf.geometry.geom_type.unique()}")
            logger.info(f"  Available columns: {list(gdf.columns)}")
            
            # Show some sample zone types if available
            zone_col = None
            for col in ["zonedist", "ZONEDIST", "zone_type", "ZONE_TYPE"]:
                if col in gdf.columns:
                    zone_col = col
                    break
            
            if zone_col:
                zone_counts = gdf[zone_col].value_counts().head()
                logger.info(f"  Primary zone types: {zone_counts.to_dict()}")
            
            # Show coordinate system info
            if gdf.crs:
                logger.info(f"  Coordinate system: {gdf.crs}")
            
            # Show sample data
            logger.info("Sample records:")
            for i, row in gdf.head(3).iterrows():
                sample_data = {k: v for k, v in row.items() if k != 'geometry'}
                logger.info(f"  Record {i}: {sample_data}")
            
        else:
            logger.error("Failed to load any zoning data from the geodatabase")
            logger.info("Available files in output directory:")
            for item in out_dir.iterdir():
                logger.info(f"  {item.name}")
            
    except Exception as e:
        logger.error(f"Error processing geodatabase: {e}")
        logger.exception("Full error details:")
        # Even if processing fails, we still have the raw files
        logger.info("Raw geodatabase files are available in the output directory")
    
    # Clean up the zip file to save space
    try:
        zip_path.unlink()
        logger.info("Cleaned up temporary ZIP file")
    except Exception as e:
        logger.warning(f"Could not clean up ZIP file: {e}")
    
    return out_dir