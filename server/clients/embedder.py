"""
Module to handle embedding generation.
"""

import io
import logging
import pickle
import sys

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
        max_batch_size: int = 1,
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
        logging.info("Embedder initialised.")

    def __embed(self, documents):
        """
        Method to generate embeddings for a list of
        documents.
        """
        embeddings = self.model.encode(documents)
        return embeddings

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
