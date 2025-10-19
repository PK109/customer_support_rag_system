#!/usr/bin/env bash
export URL="https://dl.mitsubishielectric.com/dl/fa/document/manual/robot/bfp-a3447/bfp-a3447q.pdf"
export FNAME="bfp-a3447q.pdf"
export COLLECTION="my_qdrant_collection"
export QDRANT_URL="http://localhost:6333"
export TOKEN_LIMIT=300

make run-all