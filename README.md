# StreetwiseAI

Minimal scaffolding for the "City Brain" NYC urban planning simulator.

## Quickstart

1. Create a virtualenv and install deps:
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:
```
cp .env.example .env
# Fill in API keys and dataset IDs as needed
```

3. Run ingestion locally (no Modal):
```
python scripts/local_ingest.py
```

4. Or run via Modal:
```
modal run citybrain/modal_app.py::ingest_data
```
