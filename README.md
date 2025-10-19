# Customer Support RAG System

A reproducible RAG (Retrieval-Augmented Generation) pipeline for customer support manuals. The project converts PDFs into a searchable knowledge base (Qdrant) and exposes a Streamlit chat interface for retrieval + LLM answer generation.

This repository contains a lightweight, modular pipeline that covers:
- PDF → Markdown extraction (`PDFToMarkdown`)  
- Chunking into token-limited passages (`TextChunker`)  
- Embedding and hybrid upload to Qdrant (`EmbeddingUploader`). Step uses Docker to run qdrant engine, when required.
- Hybrid retrieval / re-ranking (`Search.rrf_search`) and query refinement (`refine_query`) used by the RAG workflow  
- A small Streamlit-based chat UI for interacting with the collection

## Why this project
- Enables rapid ingestion of vendor manuals into a retrieval system for question answering.
- Demonstrates hybrid retrieval (vector + sparse/BM25) and re-ranking to improve result quality.

## Repository layout (relevant files)
- `src/code/` – implementation of the pipeline (pdf_to_md, chunking, embedding, search, prompts, rag_workflow, etc.)
- `Makefile` – high-level convenience targets to run the pipeline end-to-end or as well as single steps, used mainly because using Airflow, combined with all dependencies here was too much for GH codespaces :D
- `src/experiments` - the folder where all the features where developed in Jupyter environment
- `src/streamlit_app/` – Streamlit UI for interactive chat
- `requirements.txt` – Python dependencies used by the project

## Quick summary of the ingestion orchestration
1. Download PDF (Makefile: `download-file`)  
2. Convert PDF → matched markdown/JSON content (`convert-pdf`)  
3. Chunk content into token-limited passages (`chunk-file`)  
4. Create embeddings and upsert to Qdrant (hybrid support) (`embed-file` / `upsert`)  
5. Run end-to-end pipeline (`run-all` runs steps 1–4 automatically)

## Key implementation notes (what improves retrieval quality)
- Query rewriting: `rag_workflow.refine_query` generates multiple reformulations of the user's query (default 3 queries in total). Those are used to broaden coverage and find the best candidate documents.  
- Hybrid upload: `EmbeddingUploader.upload_hybrid_embeddings` writes both dense vectors and a BM25-style sparse document representation to Qdrant.
- Re-ranking: `Search.rrf_search` combines neural and sparse (BM25) prefetches and uses RRF fusion from Qdrant to produce a final ranked set of results.  

## Makefile targets (convenience)
- `make download-file URL=<url> FNAME=<filename.pdf>` — download a PDF into `data/`.
- `make convert-pdf FNAME=<filename.pdf>` — convert `data/<FNAME>` into `*_content.json` using `PDFToMarkdown`.
- `make chunk-file FNAME=<filename.pdf>` — chunk the `*_content.json` into `*_chunked.json`.
- `make embed-file FNAME=<filename.pdf> COLLECTION=<qdrant_collection>` — create embeddings and upload to Qdrant collection (hybrid upload). Requires Qdrant running.
- `make run-all URL=<url> FNAME=<filename.pdf> COLLECTION=<collection>` — runs the whole flow (download, convert, chunk, embed) end-to-end.
- `make clean` — remove `data/` and `models/` folders
- `make run-qdrant` — starts Qdrant in Docker with expected setup for this application - handled automatically by another targets

> Note: use `run_makefile.sh` script to handle entire pipeline in a simple, convenient way

## Running the Streamlit UI
1. Ensure Qdrant and embeddings exist for the collection you want to query.  
2. Provide credentials in `.streamlit/secrets.toml` (see `setup.md` for exact format).  
3. Launch:

```bash
pip install -r requirements.txt
streamlit run streamlit_app/main.py
```

## Conversion Notes:
PDF files are hard to manipulate. Conversion steps for this application consists:
- Obtaining the TOC of document (PDF is required to have TOC)
- Converting the file to markdown text, using `pymupdf4llm`. Basic cleaning manipulation.
- Splitting markdown into chapters, using `regex`.
- Combining TOC with content related to chapter.  

Some documents might be incorrectly interpreted and converted. For the best results, manual intervention might be required.
While chunking, document is validated for missing chapters. Manual modification can improve final results.

## Evaluation & monitoring notes
- Retrieval flow: the repo uses both a knowledge base (Qdrant) and an LLM in the RAG pipeline.  
- Retrieval evaluation: hybrid search + RRF re-ranking are available; considering  a small automated evaluation script to compare different approaches (e.g., dense-only vs hybrid) for a future improvement 
- LLM evaluation: not currently automated; the workflow supports experimenting with different prompts via `src/code/prompts.yaml`.  
- Monitoring: the code appends simple search records (query + result scores) to a history file when `Search.search_with_history` is used — you can wire that into a dashboard for monitoring.

## Reproducibility
- Dependencies are listed in `requirements.txt`. Run `pip install -r requirements.txt` in a Python 3.12+ virtual environment.  
- The `Makefile` provides reproducible commands for the ingestion flow.  
- For full reproducibility, start Qdrant locally (see `setup.md`) and populate a collection with `make embed-file`.

