"""
Module to handle embedding generation.
"""

import io
import json
import logging
import pickle
import sys

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from clients.database_connector import DatabaseConnector


class Embedder:
    """
    Class to handle embedding generation.
    """

    def __init__(
        self,
        model: str,
        embedding_field: str,
        overflow_strategy: str = "truncate",
        embedding_instruction: str = "",
        max_batch_size: int = 50,
        compute_near_neighbours: bool = True,
        near_neighbour_count: int = 5,
    ):
        logging.info("Embedder initialising.")
        self.model_string = model
        self.model = None
        try:
            self.model = SentenceTransformer(self.model_string, local_files_only=True)
        except Exception as e:
            if "couldn't find them in the cached files" in str(e):
                logging.info(
                    "Embedder could not file model %s locally.", self.model_string
                )
            else:
                logging.critical(
                    "Embedder failed to check model. Exception: %s, %s",
                    type(e).__name__,
                    str(e),
                )
                raise e
        self.embedding_field = embedding_field
        self.overflow_strategy = overflow_strategy
        self.embedding_instruction = embedding_instruction
        self.log_buffer = io.StringIO()
        self.max_batch_size = max_batch_size
        self.compute_near_neighbours = compute_near_neighbours
        self.near_neighbour_count = near_neighbour_count
        logging.info("Embedder initialised.")

    def __embed(self, documents):
        """
        Method to generate embeddings for a list of
        documents.
        """
        embeddings = self.model.encode(documents)
        return embeddings

    def __compute_nearest_neighbours(self, database_connector):
        logging.info("Embedder computing nearest neighbours.")
        
        database_connector.create_nearest_neighbours_column()
        embeddings_dict = database_connector.get_embeddings()
        
        ids = list(embeddings_dict.keys())
        embeddings_list = [embeddings_dict[id_val] for id_val in ids]
        embeddings_array = np.array(embeddings_list).astype('float32')
        
        dimension = embeddings_array.shape[1]
        index = faiss.IndexFlatIP(dimension)
        
        faiss.normalize_L2(embeddings_array)
        index.add(embeddings_array)
        
        k = self.near_neighbour_count + 1
        distances, indices = index.search(embeddings_array, k)
        
        updates = []
        for i, id_val in enumerate(ids):
            neighbour_indices = indices[i][1:]
            neighbour_ids = [ids[idx] for idx in neighbour_indices]
            updates.append({
                "_id": id_val,
                "neighbours": json.dumps(neighbour_ids)
            })
        
        database_connector.write_nearest_neighbours(updates)
        logging.info("Embedder finished computing nearest neighbours.")

    def iterate_database(self, database_filename):
        """
        Method to iterate over the database and
        generate embeddings for the specified field for
        every document.
        """
        logging.info("Embedder iterating over database.")
        database_connector = DatabaseConnector(database_filename)
        storage_field = database_connector.create_field_to_store_embeddings(
            self.embedding_field
        )

        while True:
            rows = database_connector.get_unenriched_documents(
                storage_field, self.max_batch_size
            )
            if not rows:
                logging.info("Embedder finished iterating over database.")
                break
            documents = [row[self.embedding_field] for row in rows]
            ids = [row["_id"] for row in rows]
            embeddings = self.__embed(documents)
            for i, row in enumerate(rows):
                row[storage_field] = pickle.dumps(embeddings[i])
            database_connector.write_embedded_documents(rows, storage_field)
            logging.info("Embedder wrote enriched documents to database.")
        
        if self.compute_near_neighbours:
            self.__compute_nearest_neighbours(database_connector)
        
        logging.info("Embedder finished iterating over database.")

    def download_model(self):
        """
        Method to download the model while capturing
        stdout logs onto self.log_buffer. This method
        is intended to be called in a FastAPI background task.
        """
        st_logger = logging.getLogger("sentence_transformers")
        hf_logger = logging.getLogger("huggingface_hub")

        st_original_handlers = st_logger.handlers[:]
        hf_original_handlers = hf_logger.handlers[:]

        handler = logging.StreamHandler(self.log_buffer)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        )

        st_logger.handlers = [handler]
        st_logger.setLevel(logging.INFO)

        hf_logger.handlers = [handler]
        hf_logger.setLevel(logging.INFO)

        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = self.log_buffer
        sys.stderr = self.log_buffer

        try:
            self.log_buffer.flush()
            self.model = SentenceTransformer(self.model_string)
            self.log_buffer.flush()
            self.log_buffer.write("Model downloaded successfully.\n")
        except Exception as e:
            self.log_buffer.write(f"Error: {str(e)}\n")
            self.log_buffer.flush()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            st_logger.handlers = st_original_handlers
            hf_logger.handlers = hf_original_handlers