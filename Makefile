PYTHON=python3
SRC_DIR=src/code
SCRIPTS_DIR=scripts
MODEL_NAME=all-mpnet-base-v2

.PHONY: all run-all clean dirs download-file convert-pdf chunk-file embed-file upsert

all: run-all

dirs:
	@mkdir -p data models

# Convenience target: operate on data/$(FNAME) using the same logic as run-all
download-file: dirs
	@if [ -z "$(URL)" ]; then echo "Please provide URL=<url> and FNAME=<filename.pdf>"; exit 1; fi
	@if [ -z "$(FNAME)" ]; then echo "Please provide FNAME=<filename.pdf>"; exit 1; fi
	@if [ -f "data/$(FNAME)" ]; then \
		echo "File data/$(FNAME) already exists, skipping download."; \
	else \
		echo "Downloading $(URL) -> data/$(FNAME)"; \
		wget -qO data/$(FNAME) "$(URL)"; \
	fi

convert-pdf: dirs
	@if [ -z "$(FNAME)" ]; then echo "Please provide FNAME=<filename.pdf> (file must be in data/)"; exit 1; fi
	@PDF_PATH="data/$(FNAME)"; \
	OUT_PATH="$${PDF_PATH%.pdf}_content.json"; \
	if [ -f "$$OUT_PATH" ]; then \
		echo "File $$OUT_PATH already exists, skipping PDF → Markdown conversion."; \
	else \
		echo "Converting $$PDF_PATH → $$OUT_PATH ; This might take a while..."; \
		$(PYTHON) -c "from src.code.pdf_to_md import PDFToMarkdown; p=PDFToMarkdown('$$PDF_PATH'); p.run(); print('Converted ->', p.output_filepath)"; \
	fi

chunk-file: dirs
	@if [ -z "$(FNAME)" ]; then echo "Please provide FNAME=<filename.pdf> (file must be in data/)"; exit 1; fi
	@PDF_PATH="data/$(FNAME)"; \
	INPUT_PATH="$${PDF_PATH%.pdf}_content.json"; \
	OUT_PATH="$${PDF_PATH%.pdf}_chunked.json"; \
	if [ -f "$$OUT_PATH" ]; then \
		echo "File $$OUT_PATH already exists, skipping chunking."; \
	else \
		echo "Chunking $$INPUT_PATH → $$OUT_PATH"; \
		$(PYTHON) -c "from src.code.chunking import TextChunker; c=TextChunker('sentence-transformers/$(MODEL_NAME)'); c.chunk_file('$$INPUT_PATH', '$$OUT_PATH')"; \
	fi

embed-file: dirs
	@if [ -z "$(FNAME)" ]; then echo "Please provide FNAME=<filename.pdf> (file must be in data/)"; exit 1; fi
	@if [ -z "$(COLLECTION)" ]; then echo "Please provide COLLECTION=<qdrant collection name>"; exit 1; fi
	@PDF_PATH="data/$(FNAME)"; \
	OUT_PATH="$${PDF_PATH%.pdf}_chunked.json"; \
	if [ ! -f "$$OUT_PATH" ]; then \
		echo "Chunked content $$OUT_PATH not found. Run 'make chunk-file FNAME=$(FNAME)' or ensure chunked JSON exists."; \
		exit 1; \
	fi
	@PDF_PATH="data/$(FNAME)"; \
	OUT_PATH="$${PDF_PATH%.pdf}_chunked.json"; \
	$(PYTHON) -c "from src.code.embedding import EmbeddingUploader; e=EmbeddingUploader(model_name='$(MODEL_NAME)', collection_name='$(COLLECTION)'); e.upload_hybrid_embeddings('$$OUT_PATH', qdrant_url='${QDRANT_URL:-http://localhost:6333}')"

# Create embeddings and upsert into Qdrant (expects CONTENT and COLLECTION)
upsert: embed-file

# Run full pipeline from a remote URL into qdrant collection
run-all: dirs
	@if [ -z "$(URL)" ]; then echo "Please provide URL and FNAME and COLLECTION (see README)"; exit 1; fi
	@if [ -z "$(FNAME)" ]; then echo "Please provide FNAME (filename to save as)"; exit 1; fi
	@if [ -z "$(COLLECTION)" ]; then echo "Please provide COLLECTION name"; exit 1; fi
	# download
	@if [ -f "data/$(FNAME)" ]; then \
		echo "File data/$(FNAME) already exists, skipping download."; \
	else \
		echo "Downloading $(URL) -> data/$(FNAME)"; \
		wget -qO data/$(FNAME) "$(URL)"; \
	fi
	# conversion to markdown 
	@PDF_PATH="data/$(FNAME)"; \
	OUT_PATH="$${PDF_PATH%.pdf}_content.json"; \
	if [ -f "$$OUT_PATH" ]; then \
		echo "File $$OUT_PATH already exists, skipping PDF → Markdown conversion."; \
	else \
		echo "Converting $$PDF_PATH → $$OUT_PATH ; This might take a while..."; \
		$(PYTHON) -c "from src.code.pdf_to_md import PDFToMarkdown; p=PDFToMarkdown('$$PDF_PATH'); p.run(); print('Converted ->', p.output_filepath)"; \
	fi
	# chunk
	@PDF_PATH="data/$(FNAME)"; \
	OUT_PATH="$${PDF_PATH%.pdf}_chunked.json"; \
	INPUT_PATH="$${PDF_PATH%.pdf}_content.json"; \
	if [ -f "$$OUT_PATH" ]; then \
		echo "File $$OUT_PATH already exists, skipping chunking."; \
	else \
		echo "Chunking $$INPUT_PATH → $$OUT_PATH"; \
		$(PYTHON) -c "from src.code.chunking import TextChunker; c=TextChunker('sentence-transformers/$(MODEL_NAME)'); c.chunk_file('$$INPUT_PATH', '$$OUT_PATH')"; \
	fi
	# embed & upsert points to collection
	@PDF_PATH="data/$(FNAME)"; \
	OUT_PATH="$${PDF_PATH%.pdf}_chunked.json"; \
	$(PYTHON) -c "from src.code.embedding import EmbeddingUploader; e=EmbeddingUploader(model_name='$(MODEL_NAME)', collection_name='$(COLLECTION)'); e.upload_hybrid_embeddings('$$OUT_PATH', qdrant_url='${QDRANT_URL}')"

clean:
	rm -rf data models
