# Shadowpuppet

Shadowpuppet is a GUI tool for visualising semantic scatter plots. Semantic scatter plots represent data with more aligned meaning as points that are closer on a graph. Graphs are produced by representing textual data in a high-dimensional space using sentence embeddings then projecting back down onto a 2d plot using PaCMAP. This technique results in context-aware visualisations of unstructured datasets. Shadowpuppet facilitates graph creation and exploration by executing queries against a local sqlite database to highlight points.

## Installation

Shadowpuppet is available as a Tauri binary for Windows, MacOS and Linux under the releases section. The binary contains the entire application in a single exectuable file for ease of use. Databases created will be created in a `./databases` directory in the same location the exectuable runs from. 

Tauri can also be deployed via a Python FastAPI server serving a statically compiled Svelte5 web application. The steps for serving the application require `npm` and `pip/python3` and are:

1. install frontend dependencies with `npm install` from `./frontend`
2. build the frontend files with `npm run build` from `./frontend`
3. install server dependencies with `pip install -r requirements.txt` from `./server`, using a virtual environment if you prefer
4. run the server using `python3 server.py` from `./server`
