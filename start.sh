#!/bin/bash
echo "Starting FastAPI Backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "Starting Streamlit Frontend..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
