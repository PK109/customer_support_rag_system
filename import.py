# from src.code.embedding import EmbeddingUploader
# e=EmbeddingUploader(model_name='all-mpnet-base-v2', collection_name='my_qdrant_collection')
# e.run_reading('pdfs/bfp-a3606u.pdf')

from src.code.chunking import TextChunker
tc = TextChunker(model_name='sentence-transformers/all-mpnet-base-v2')
tc.chunk_file('pdfs/bfp-a3606u_content.json', 'pdfs/bfp-a3606u_chunked.json', token_limit=300)