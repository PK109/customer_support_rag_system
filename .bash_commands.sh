#!/bin/bash
# command for running qdrant in docker
alias qdrant-run="docker run -p 6333:6333 -p 6334:6334 -v \"$(pwd)/qdrant_storage:/qdrant/storage:z\" qdrant/qdrant"
# expand PATH to include local python bin and user local bin
PATH="/usr/local/python/3.12.1/bin:$HOME/.local/bin:${PATH}"