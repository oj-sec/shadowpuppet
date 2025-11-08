import hashlib
import io
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager

import pandas as pd
import uvicorn
from fastapi import (
    BackgroundTasks,
    Cookie,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.staticfiles import StaticFiles

from clients.database_connector import DatabaseConnector, DatabaseCreator
from clients.dimension_reducer import DimensionReducer
from clients.embedder import Embedder

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def is_bundled():
    """
    Check if the server is running in a bundle.
    """
    return getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")


def get_resource_path(relative_path: str) -> str:
    """
    Get the resource path for a file in the bundle.
    """
    if is_bundled():
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


clients = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    clients["database_creator"] = DatabaseCreator()
    clients["database_connector"] = None
    clients["embedder"] = None
    clients["dimension_reducer"] = None
    logging.info("Shadowpuppet server initialised.")
    yield
    clients.clear()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)


@app.get("/shutdown")
async def shutdown():
    """
    Remote interface to shut down the server.
    """
    pid = os.getpid()

    def kill_process():
        if sys.platform == "win32":
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)

    import threading

    threading.Timer(0.5, kill_process).start()
    return {"message": "Server shutting down"}


@app.post("/api/visualise/categorical-query")
async def categorical_query(
    request: Request,
):
    """
    Route to return buckets based on on unique values of
    a field up to a maximum number of buckets.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    data = await request.json()
    try:
        return clients["database_connector"].categorical_query(
            data["field"],
            data["buckets"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error completing query: {type(e).__name__}: {str(e)}")


@app.post("/api/visualise/sequential-query")
async def sequential_query(
    request: Request,
):
    """
    Route to return a specified number of buckets of point
    indexes based on a specified sequential field.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    data = await request.json()
    try:
        return clients["database_connector"].sequential_query(
            data["field"],
            data["buckets"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error completing query: {type(e).__name__}: {str(e)}")


@app.post("/api/visualise/simple-query")
async def query(
    request: Request,
):
    """
    Route to execute a simple query
    and return matching ids.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    data = await request.json()
    try:
        return clients["database_connector"].simple_query(
            data["field"],
            data["query"],
            data["operator"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error completing query: {type(e).__name__}: {str(e)}")


@app.post("/api/visualise/get-point")
async def get_point(request: Request):
    """
    Route to get data associated with a point.
    """
    data = await request.json()
    return clients["database_connector"].get_data_by_id(data["id"])


@app.post("/api/visualise/get-column-values")
async def get_column_values(request: Request):
    """
    Route to get all values of a specified column, keyed by _id.
    Expects JSON payload: { "column": "column_name" }
    """
    data = await request.json()
    return clients["database_connector"].get_column_values_by_id(data["column"])


@app.get("/api/visualise/get-coordinates")
async def get_coordinates():
    """
    Route to get the coordinates of points.
    """
    return {
        "coordinates": clients["dimension_reducer"].map_vectors,
    }


@app.get("/api/visualise/list-databases")
async def list_databases():
    """
    Route to list all databases in the databases
    directory.
    """
    databases = clients["database_creator"].list_databases()
    selectedDatabase = (
        clients["database_connector"].database_filename
        if clients["database_connector"]
        else None
    )
    return {"databases": databases, "selectedDatabase": selectedDatabase}


@app.get("/api/embeddings/check-progress")
async def check_progress():
    """
    Route to check the progress of the embedding
    generation.
    """
    storage_field = clients["embedder"].embedding_field + "_embedding"
    return {
        "completedDocuments": clients[
            "database_connector"
        ].get_completed_document_count(storage_field),
        "nearNeighbourComplete": clients[
            "database_connector"
        ].is_nearest_neighbours_complete(),
    }


@app.post("/api/embedding/queue-embeddings")
async def queue_embeddings(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Route to start embedding generation in a
    background task.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    if not clients["embedder"]:
        raise HTTPException(status_code=400, detail="No embedding model loaded.")

    logging.info("Queueing embedding generation.")
    background_tasks.add_task(
        clients["embedder"].iterate_database,
        clients["database_connector"].database_filename,
    )
    logging.info("Embedding generation queued.")
    return {
        "status": "success",
    }


@app.post("/api/dimension-reduction/run")
async def run_dimension_reduction(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Route to start dimension reduction in a
    background task.
    """
    if not clients["dimension_reducer"]:
        raise HTTPException(status_code=400, detail="No dimension reducer loaded.")
    logging.info("Queueing dimension reduction.")
    background_tasks.add_task(
        clients["dimension_reducer"].reduce_dimensions,
        clients["database_connector"].database_filename,
    )
    logging.info("Dimension reduction queued.")
    return {
        "status": "success",
    }


@app.get("/api/dimension-reduction/check-progress")
async def check_dimension_reduction():
    """
    Route to check the progress of the dimension
    reduction.
    """
    if clients["dimension_reducer"].map_vectors is None:
        return {
            "status": "processing",
        }
    else:
        return {
            "status": "success",
            "mapVectors": clients["dimension_reducer"].map_vectors,
        }


@app.post("/api/dimension-reduction/configure")
async def configure_dimension_reduction(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Route to configure the dimension reduction model.
    """
    data = await request.json()
    clients["dimension_reducer"] = None
    clients["dimension_reducer"] = DimensionReducer(
        n_neighbours=data["nNeighbours"] if data["nNeighbours"] != 0 else None,
        MN_ratio=data["nearNeighbourRatio"],
        FP_ratio=data["farNeighbourRatio"],
        init=data["initialisationMethod"],
    )
    return {
        "status": "success",
    }


@app.post("/api/embeddings/configure")
async def configure_embeddings(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Route to configure the embedding model.
    """
    data = await request.json()
    clients["embedder"] = None
    clients["embedder"] = Embedder(
        model=data["embeddingModel"],
        overflow_strategy=data["overflowStrategy"],
        embedding_instruction=data["embeddingInstruction"],
        embedding_field=data["selectedColumn"],
    )
    if not clients["embedder"].model:
        background_tasks.add_task(clients["embedder"].download_model)
        return {
            "status": "pending",
            "message": "model downloading",
            "logs": clients["embedder"].log_buffer.getvalue(),
        }
    return {"status": "success", "message": "model loaded"}


@app.get("/api/embeddings/check-download")
async def check_download():
    """
    Route to check the progress of the embedding
    model download.
    """
    return {
        "model": clients["embedder"].model_string,
        "modelObject": str(clients["embedder"].model),
        "logs": clients["embedder"].log_buffer.getvalue(),
    }


@app.get("/api/database/health")
async def check_database():
    """
    Route to check if a database is loaded.
    """
    if not clients["database_connector"]:
        return {"loaded": False}
    if not clients["database_connector"].database_filename:
        return {"loaded": False}
    return {"loaded": True, "name": clients["database_connector"].database_filename}


@app.get("/api/database/preview")
async def preview_database():
    """
    Route to preview the first 10 rows of
    the current database.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    return clients["database_connector"].preview_data()


@app.get("/api/database/columns")
async def get_columns():
    """
    Route to get the columns of the current database.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    return clients["database_connector"].get_columns()


@app.get("/api/database/total-documents")
async def get_total_documents():
    """
    Route to get the total number of documents
    in the current database.
    """
    if not clients["database_connector"]:
        raise HTTPException(status_code=400, detail="No database loaded.")
    return {"totalDocuments": clients["database_connector"].get_total_documents()}


@app.post("/api/database/select-database")
async def select_database(request: Request):
    """
    Route to select a database from the databases
    directory.
    """
    data = await request.json()
    database_name = data["database"]
    clients["database_connector"] = None
    clients["database_connector"] = DatabaseConnector(database_name)
    return {"status": "success"}


@app.post("/api/database/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Route to upload a file and read it into a
    sqlite3 database.
    """
    filename = file.filename.lower()
    if not (
        filename.endswith(".csv")
        or filename.endswith(".json")
        or filename.endswith(".ndjson")
    ):
        raise HTTPException(
            status_code=400, detail="File must be .csv, .json, or .ndjson"
        )
    file_bytes = await file.read()
    file_string = file_bytes.decode("utf-8")
    file_io = io.StringIO(file_string)

    if filename.endswith(".csv"):
        df = pd.read_csv(file_io)
    elif filename.endswith(".json"):
        df = pd.read_json(file_io)
    elif filename.endswith(".ndjson"):
        df = pd.read_json(file_io, lines=True)

    data_list = df.to_dict(orient="records")
    database_file = clients["database_creator"].create_new_database(filename, data_list)
    clients["database_connector"] = DatabaseConnector(database_file)


frontend_path = get_resource_path(os.path.join("frontend", "build"))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
