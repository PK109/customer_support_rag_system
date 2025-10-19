# Setup and Run Instructions

This document explains how to set up a reproducible local environment for the Customer Support RAG System, including Qdrant, Python dependencies, and the secrets file format.

Prerequisites
- Linux, macOS, or Windows WSL with Docker (for Qdrant) and Python 3.10+, for testing GH Codespaces are convenient.  
- pip or virtualenv for Python package management

1) Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Secrets file (`.streamlit/secrets.toml`)

Create `.streamlit/secrets.toml` (or point `SECRETS_PATH` to another file) as a copy of `secrets.example.toml`. Edit a file to provide credentials for used services.

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml

```

3) Run Qdrant locally (via Docker)

You can run Qdrant quickly with Docker. There is only one service working in Docker, making `docker-compose` file useless. Make action is prepared:
``` bash
make run-qdrant
```
Yet, keep in mind that operation can be performed automatically, when it is required by pipeline.


4) Example ingestion run using Makefile
All the ingestion steps can be done via Makefile.

```bash
# download
make download-file URL=https://link.to/sample.pdf
# convert to matched content JSON
make convert-pdf FNAME=sample.pdf
# chunk into token-limited passages
make chunk-file FNAME=sample.pdf
# create embeddings and upsert to Qdrant (collection must be specified)
make embed-file FNAME=sample.pdf COLLECTION=my_collection_name
```

Or run the combined flow (download + convert + chunk + embed):

```bash
make run-all URL=https://link.to/sample.pdf FNAME=sample.pdf COLLECTION=my_collection_name
```
Ready-to-use makefile script is available in `run_makefile.sh` file.

5) Run Streamlit UI, Qdrant is also required.

```bash
make run-qdrant
python3 -m streamlit run src/streamlit_app/rag_app.py

```

6) Troubleshooting notes

- PDF extraction fails: `pymupdf` depends on a MuPDF binary. If you see crashes or segmentation faults, try reinstalling `pymupdf` using the recommended versions in `requirements.txt`. 
- PDFs are complex files. Its conversion to markdown is not a straightforward operation. Therefore, some errors might occur during conversion. Manual intervention might be useful for complex documents. 
- Qdrant not reachable: ensure Docker is running and the container exposes port `6333`. Check logs with `docker compose logs qdrant`.  
- Model downloads are slow: SentenceTransformer models are cached under `models/` by default. For CI, pre-download models into `models/` or mount a cached models directory.  

7) Evaluation and adding monitoring

- The repo includes `Search.search_with_history` which appends search records to the configured `history_storage` file. You can use this file for building a simple dashboard and monitor the output, aligned with query provided.
- To evaluate retrieval, create a small labeled dataset of queries and ground-truth document IDs. Run `searcher.rrf_search` and compute metrics like precision and MRR.  
