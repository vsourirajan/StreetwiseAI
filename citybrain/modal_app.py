import modal
from pathlib import Path

image = (
    modal.Image.debian_slim()
    .apt_install("curl")
    .pip_install(
        [
            "modal>=0.62.0",
            "osmnx==1.7.1",
            "networkx>=3.2.1",
            "geopandas>=0.14.3",
            "shapely>=2.0.3",
            "pyogrio>=0.7.2",
            "pandas>=2.2.2",
            "requests>=2.32.3",
            "beautifulsoup4>=4.12.3",
            "tiktoken>=0.7.0",
            "openai>=1.40.0",
            "python-dotenv>=1.0.1",
            "folium>=0.16.0",
            "rapidfuzz>=3.9.6",
            "pdfminer.six>=20240706",
            "orjson>=3.10.7",
        ]
    )
)

app = modal.App("citybrain-ingest")


@app.function(image=image, timeout=900)
def ingest_data():
    from citybrain.ingest.zoning_text import download_zoning_text, chunk_and_write_embeddings_corpus
    from citybrain.ingest.zoning_shapes import download_zoning_shapes
    # from citybrain.ingest.osm_network import download_osm_drive_network
    from citybrain.ingest.traffic_counts import download_traffic_counts
    # from citybrain.ingest.demographics import download_demographics

    # Execute sequentially; can parallelize later with async
    print("Downloading zoning text...")
    download_zoning_text()
    chunk_and_write_embeddings_corpus()

    print("Downloading zoning shapes...")
    download_zoning_shapes()

    print("Downloading OSM network...")
    download_osm_drive_network()

    print("Downloading traffic counts...")
    download_traffic_counts()

    print("Downloading demographics...")
    download_demographics()

    print("Ingestion complete.")


if __name__ == "__main__":
    ingest_data.local()