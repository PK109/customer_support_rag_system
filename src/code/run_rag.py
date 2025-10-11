#!/usr/bin/env python3
"""Simple runner for the RAG workflow.

This script initializes the model, qdrant client and LLM client, then
calls rag_workflow.rag(query). It is intentionally minimal — adjust
paths and collection names for your environment.
"""
import argparse
import os

from rag_workflow import rag



def main():
    parser = argparse.ArgumentParser(description="Run RAG workflow for a single query")
    parser.add_argument("--query", "-q", required=True, help="User query to run the RAG pipeline")
    parser.add_argument("--collection", "-c", default="bfp-a3447q", help="Qdrant collection name to query")
    parser.add_argument("--model_cache", default="./src/code/models", help="SentenceTransformer cache folder")
    parser.add_argument("--model_name", default="all-mpnet-base-v2", help="SentenceTransformer model name")
    parser.add_argument("--secrets", default="../../.streamlit/secrets.toml", help="Path to streamlit secrets toml for OpenAI key")
    args = parser.parse_args()

    # Run the pipeline
    print("Running RAG for query:", args.query)
    resp = rag(args.query, args.secrets, args.collection, verbose_search=True, verbose_prompt=False)
    print("\n---- RAG Response ----\n")
    print(resp)


if __name__ == "__main__":
    main()
