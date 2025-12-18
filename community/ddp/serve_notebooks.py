#!/usr/bin/env python3
"""
Serve all marimo notebooks from the current directory.
Run this script to start a marimo server that serves all notebooks.
"""

import marimo
from pathlib import Path

# Get the current directory (where this script is located)
current_dir = Path(__file__).parent

# Create the ASGI application using the builder pattern
# Need to call .build() to get the actual ASGI app
app = (
    marimo.create_asgi_app()
    .with_dynamic_directory(path="/", directory=str(current_dir))
    .build()
)

if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is required to run this server.")
        print("Install it with: pip install uvicorn")
        exit(1)
    
    print(f"Serving marimo notebooks from: {current_dir}")
    print("Notebooks will be available at: http://localhost:8000/{notebook-name}")
    print("For example: http://localhost:8000/home for home.py")
    print("Press Ctrl+C to stop the server\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
